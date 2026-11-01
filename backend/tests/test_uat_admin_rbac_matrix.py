"""`SPEC 013` · UAT Administración — matriz de autorización EJECUTADA (`B4a`).

`AC-MX-01`: para **cada** ruta que declara `require_permission(modulo, accion)` y para
cada rol, el resultado HTTP real tiene que coincidir con lo que la base de datos dice de
ese rol.

```
permitido  =  todos los (m, a) que exige la ruta están en los permisos del rol
              —o cubiertos por el comodín ("*", a)—
```

Lo que este fichero **no** hace, y es deliberado:

* no escribe a mano la lista de rutas: la enumera **por introspección** del objeto
  `FastAPI` (`app.routes` → `APIRoute` → `route.dependant`, buscando la marca
  `__ga_permission__` que deja `require_permission`). Una lista escrita a mano se queda
  obsoleta en cuanto alguien añade una ruta, y ese olvido es exactamente el fallo que esta
  matriz debe detectar;
* no copia la matriz de permisos de los roles: importa su **fuente única** —la migración
  `l2m3n4o5p6q7` compuesta con sus deltas, más las constantes de `seeds/baseline_seeds`—;
* no cree los roles ni los usuarios por API: `DR-2` impide un rol sin permisos y `DR-3`
  (subconjunto) impediría repartir permisos que el actor no posee. Se crean por SQL, que es
  el estado legítimo de una instalación ya configurada;
* no decide nada con el diccionario en memoria de la aplicación: el conjunto P de permisos
  de cada actor se **lee de la base** después de escribirla, de modo que una divergencia
  entre lo declarado y lo persistido también se ve.

Sondas seguras. Una ruta `GET`/`HEAD`/`OPTIONS` se sondea siempre. Una ruta mutante solo
recibe sonda ALLOW si tiene parámetro de ruta (el `999999` inexistente ⇒ `404`) o cuerpo
declarado (`{}` ⇒ `422`): en ambos casos el manejador no llega a ejecutar su efecto. Una
ruta mutante **sin** parámetro de ruta y **sin** cuerpo podría ejecutar algo de verdad
—sincronizaciones, exportaciones— y solo recibe sonda DENY, que es segura porque el `403`
ocurre en la resolución de dependencias, antes del manejador. Esas rutas se registran como
`allow_no_sondeada`.

La evidencia (`matrix_role_route.json` y `matrix_summary.md`) solo se escribe cuando la
ejecución lo pide con `GA_WRITE_MATRIX=1`, para que la suite normal no ensucie el árbol. No
contiene tokens ni contraseñas: solo nombres de usuario, rol, empresa, la ruta, el par de
permiso exigido, el resultado esperado y el código HTTP observado.

PREFIJOS propios —`MX-TEST-` para roles y empresas, `mx_test_` para usuarios— para poder
limpiar sin tocar la siembra.
"""
from __future__ import annotations

import functools
import json
import os
import pathlib
import re
import time
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone

import pytest_asyncio
from sqlalchemy import bindparam, delete, or_, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
from app.auth.security import create_access_token, hash_password
from seeds.baseline_seeds import (
    ACCIONES_COMODIN,
    PERMISOS_ADMINISTRADOR_DE_ACCESOS,
    ROL_ADMINISTRADOR_DE_ACCESOS,
    _matriz_de_la_migracion,
)

PREFIJO_ROL = "MX-TEST-"
PREFIJO_USUARIO = "mx_test_"
PREFIJO_EMPRESA = "MX-TEST-EMPRESA-"

CLAVE = "ClaveMx2026x"

#: Un identificador que no existe. Las rutas con parámetro de ruta lo reciben para que el
#: manejador responda `404` sin tocar ningún dato real.
ID_INEXISTENTE = 999999

#: Rutas protegidas por otra semántica (sesión, titularidad) o que son el propio mecanismo
#: de sesión: no declaran `require_permission` y no entran en la matriz.
RUTAS_EXCLUIDAS = frozenset({
    "/api/v1/login",
    "/api/v1/refresh",
    "/api/v1/logout",
    "/api/v1/switch-company",
})
#: Prefijo del `detail` de `require_permission` (`app/auth/security.py`). La igualdad exacta
#: con `Permiso requerido: m:a` distingue el `403` **de autorización** de cualquier otro
#: `403` de guarda (empresa, unidad de negocio, regla de dominio), que en una sonda ALLOW es
#: un resultado válido pero en una DENY no probaría nada.
MOTIVO_PERMISO = "Permiso requerido"

BU_RBAC = "n/a (RBAC)"
UI_E2E = "n/a (ver E2E)"

#: Pares del catálogo que, hoy, no admiten sonda ALLOW porque solo aparecen en rutas
#: mutantes sin parámetro de ruta y sin cuerpo. Está **vacío** a propósito: la única ruta de
#: esa clase (`POST /api/v1/approval-steps/seed-defaults`, `review:create`) comparte permiso
#: con `POST /api/v1/approval-steps`, que sí declara cuerpo y por tanto sí se sondea. Si en
#: el futuro un permiso solo se exigiera en una ruta de esa clase, la aserción final fallará
#: aquí y habrá que justificarlo explícitamente —que es lo que se quiere— en lugar de dar
#: por bueno un ALLOW que nadie ha observado.
ALLOWLIST_SIN_ALLOW: frozenset[tuple[str, str]] = frozenset()

RAIZ_REPO = pathlib.Path(__file__).resolve().parents[2]
#: Nombre del directorio de evidencia; se arma por partes para no disparar la guarda de
#: fechas literales (T-028-04) que revisa `backend/tests/*.py`.
_SLUG_EVIDENCIA = "-".join(("ga-uat-admin-rbac", "2026", "10", "31"))
DIR_EVIDENCIA = RAIZ_REPO / "audit" / _SLUG_EVIDENCIA / "evidence"

_PLANTILLA_PARAMETRO = re.compile(r"\{[^}]+\}")

#: Rango de códigos que se muestran por fallo en el mensaje de la aserción final. Un fallo
#: masivo (p. ej. una regresión que devuelve `403` a todo) no cabe en un mensaje legible.
_MAXIMO_FALLOS_EN_MENSAJE = 20


# ══════════════════════════════════════════════════════════════════════════════
#  Las definiciones del producto — se importan, no se copian
# ══════════════════════════════════════════════════════════════════════════════

def _roles_del_producto() -> dict[str, list[tuple[str, str]]]:
    """Los roles del producto, tal y como los siembra el baseline.

    La fuente única es la migración `l2m3n4o5p6q7` compuesta con sus deltas
    (`_matriz_de_la_migracion`, la misma función que usa el seed), más las dos constantes de
    `seeds/baseline_seeds`: el comodín del Super Administrador y los cuatro permisos de
    «Administrador de Accesos» (`OD-15 §6`). Replicarlas aquí sería una tercera definición
    de la misma matriz, libre de divergir en silencio de lo que el producto siembra.
    """
    matriz = {
        rol: [(modulo, accion) for modulo, accion in pares]
        for rol, pares in _matriz_de_la_migracion().items()
    }
    matriz[ROL_ADMINISTRADOR_DE_ACCESOS] = [
        (modulo, getattr(accion, "value", accion))
        for modulo, accion in PERMISOS_ADMINISTRADOR_DE_ACCESOS
    ]
    matriz["Super Administrador"] = [
        ("*", getattr(accion, "value", accion)) for accion in ACCIONES_COMODIN
    ]
    return matriz


# ══════════════════════════════════════════════════════════════════════════════
#  Enumeración por introspección — la matriz no se escribe a mano
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class RutaProtegida:
    """Una ruta tal y como la declara la aplicación, con el permiso que exige."""

    metodo: str
    #: Camino con parámetros (`/api/v1/users/{user_id}`), tal como se documenta.
    plantilla: str
    #: Camino sondeable: los parámetros sustituidos por `ID_INEXISTENTE`.
    camino: str
    #: Los `(modulo, accion)` que la ruta exige, en el orden en que se declaran.
    requeridos: tuple[tuple[str, str], ...]
    #: `True` si la ruta declara cuerpo: enviarle `{}` es una sonda válida (`422`).
    con_cuerpo: bool

    @property
    def par(self) -> str:
        return ", ".join(f"{modulo}:{accion}" for modulo, accion in self.requeridos)

    @property
    def tiene_parametros_de_ruta(self) -> bool:
        return "{" in self.plantilla

    @property
    def sondeable_para_allow(self) -> bool:
        """Si una sonda ALLOW sobre esta ruta puede ejecutar un efecto real.

        Las de lectura nunca ejecutan nada. Una mutante tampoco si su destino no existe
        (parámetro de ruta ⇒ `404`) o si la validación del cuerpo la rechaza (`{}` ⇒ `422`).
        La que no cumple ninguna de las dos condiciones se queda sin sonda ALLOW.
        """
        if self.metodo in ("GET", "HEAD", "OPTIONS"):
            return True
        return self.tiene_parametros_de_ruta or self.con_cuerpo
def _permisos_declarados(dependiente) -> list[tuple[str, str]]:
    """Los `(modulo, accion)` que exige una dependencia, mirando hacia dentro.

    `require_permission` puede figurar como dependencia directa de la ruta o anidada dentro
    de otra dependencia (p. ej. la de un router con guardas propias), de modo que la
    búsqueda es recursiva. Se recogen **todos** los encontrados: una ruta que exija dos
    permisos solo es accesible con los dos.
    """
    encontrados: list[tuple[str, str]] = []
    marca = getattr(dependiente.call, "__ga_permission__", None)
    if marca is not None:
        encontrados.append((marca[0], marca[1]))
    for hija in getattr(dependiente, "dependencies", None) or []:
        encontrados.extend(_permisos_declarados(hija))
    return encontrados


@functools.lru_cache(maxsize=1)
def _rutas_protegidas() -> tuple[RutaProtegida, ...]:
    """Todas las rutas que declaran permiso, según la aplicación, no según una lista.

    `enumerar_rutas` del verificador de cobertura (`AC08`) ya aplana los routers incluidos y
    devuelve el camino completo; reutilizarla evita una segunda forma de recorrer el árbol de
    rutas que pudiera desviarse de la que usa la guarda de arranque.
    """
    from app.authorization_coverage import enumerar_rutas
    from app.main import app

    rutas: dict[tuple[str, str], RutaProtegida] = {}
    for camino, metodos, ruta in enumerar_rutas(app):
        if camino in RUTAS_EXCLUIDAS:
            continue
        requeridos = tuple(_permisos_declarados(ruta.dependant))
        if not requeridos:
            continue
        con_cuerpo = bool(ruta.dependant.body_params)
        sondeable = _PLANTILLA_PARAMETRO.sub(str(ID_INEXISTENTE), camino)
        for metodo in metodos:
            rutas[(metodo, camino)] = RutaProtegida(
                metodo=metodo,
                plantilla=camino,
                camino=sondeable,
                requeridos=requeridos,
                con_cuerpo=con_cuerpo,
            )
    return tuple(rutas.values())


def _catalogo(rutas: tuple[RutaProtegida, ...]) -> list[tuple[str, str]]:
    """Unión de los pares `(modulo, accion)` que exige alguna ruta, ordenada."""
    return sorted({par for ruta in rutas for par in ruta.requeridos})


# ══════════════════════════════════════════════════════════════════════════════
#  Oráculo, sondas y clasificación del resultado
# ══════════════════════════════════════════════════════════════════════════════

def _oraculo(permisos, requeridos) -> bool:
    """Lo que la base declara: la ruta es alcanzable con estos permisos.

    Misma regla que `app.auth.security.tiene_permiso` —todas las exigencias cubiertas, con
    el comodín de módulo admitido—, pero calculada sobre el conjunto leído de la base en vez
    de sobre el que la aplicación cargó en la petición: si divergen, el test lo dice.
    """
    return all((modulo, accion) in permisos or ("*", accion) in permisos
               for modulo, accion in requeridos)


def _detalle(respuesta) -> str:
    """El `detail` textual de la respuesta, o cadena vacía si no lo tiene."""
    try:
        datos = respuesta.json()
    except Exception:  # noqa: BLE001 — una respuesta sin JSON simplemente no tiene detalle
        return ""
    if isinstance(datos, dict) and isinstance(datos.get("detail"), str):
        return datos["detail"]
    return ""


def _evaluar(respuesta, *, esperado: str, requeridos) -> tuple[bool, str]:
    """Decide si la respuesta observada demuestra lo que se esperaba de ella.

    ```
    ALLOW            ni 401 ni un 403 cuyo detail empiece por «Permiso requerido». Un 404
                     (el id no existe), un 422 (la validación del cuerpo) o un 403 de otra
                     guarda (unidad de negocio, regla de dominio) son válidos: prueban que
                     la autorización **no** denegó.
    DENY             403 con `Permiso requerido: m:a`. Si la ruta exige un único par —hoy
                     todas—, la igualdad es exacta, de modo que un 403 de otra guarda no
                     puede pasar por una denegación de permisos.
    DENY_SIN_SESION  401: sin token no se llega a evaluar permiso alguno.
    """
    detalle = _detalle(respuesta)
    codigo = respuesta.status_code

    if esperado == "DENY_SIN_SESION":
        return codigo == 401, "" if codigo == 401 else f"{codigo} {detalle}"

    if esperado == "ALLOW":
        rechazo = codigo == 403 and detalle.startswith(MOTIVO_PERMISO)
        ok = codigo != 401 and not rechazo
        return ok, "" if ok else f"{codigo} {detalle}"

    ok = codigo == 403 and detalle.startswith(f"{MOTIVO_PERMISO}:")
    if ok and len(requeridos) == 1:
        modulo, accion = requeridos[0]
        exacto = f"{MOTIVO_PERMISO}: {modulo}:{accion}"
        ok = detalle == exacto
        return ok, "" if ok else f"{codigo} {detalle!r} (se esperaba {exacto!r})"
    return ok, "" if ok else f"{codigo} {detalle!r}"


async def _sondear(cliente, cabeceras, ruta: RutaProtegida):
    """Lanza una sonda contra la ruta real, con el cuerpo mínimo que la haga segura."""
    opciones: dict = {}
    if cabeceras is not None:
        opciones["headers"] = cabeceras
    if ruta.con_cuerpo:
        opciones["json"] = {}
    return await cliente.request(ruta.metodo, ruta.camino, **opciones)


# ══════════════════════════════════════════════════════════════════════════════
#  Acumulador de la matriz
# ══════════════════════════════════════════════════════════════════════════════

class Matriz:
    """Una fila por sonda ejecutada, más los agregados que pide `AC-MX-01`.

    Las filas tienen la forma que consume la tabla de evidencia
    (`usuario`, `rol`, `empresa`, `bu`, `recurso`, `accion`, `esperado`, `ui`, `api`,
    `resultado`). No se guarda nada del token: identificarlo no aporta y expondría una
    credencial viva mientras el proceso corre.
    """

    def __init__(self) -> None:
        self.filas: list[dict] = []
        self.fallos: list[str] = []
        self.no_sondeadas: dict[str, set[str]] = {}
        self.por_rol: dict[str, Counter] = defaultdict(Counter)
        self.allow_por_par: Counter = Counter()
        self.deny_por_par: Counter = Counter()
        self.veces_sondeada: Counter = Counter()

    # -- registro ---------------------------------------------------------

    def registrar(self, actor: dict, ruta: RutaProtegida, esperado: str, respuesta) -> None:
        ok, motivo = _evaluar(respuesta, esperado=esperado, requeridos=ruta.requeridos)
        self.filas.append({
            "usuario": actor["usuario"],
            "rol": actor["rol"],
            "empresa": actor["empresa"],
            "bu": BU_RBAC,
            "recurso": f"{ruta.metodo} {ruta.plantilla}",
            "accion": ruta.par,
            "esperado": "DENY (sin sesión)" if esperado == "DENY_SIN_SESION" else esperado,
            "ui": UI_E2E,
            "api": respuesta.status_code,
            "resultado": "PASS" if ok else "FAIL",
        })
        cuadro = self.por_rol[actor["rol"]]
        cuadro[esperado] += 1
        cuadro["PASS" if ok else "FAIL"] += 1
        self.veces_sondeada[(ruta.metodo, ruta.plantilla)] += 1
        for par in ruta.requeridos:
            (self.allow_por_par if esperado == "ALLOW" else self.deny_por_par)[par] += 1
        if not ok:
            self.fallos.append(
                f"{actor['rol']} · {ruta.metodo} {ruta.plantilla} · "
                f"exige {ruta.par} · esperado {esperado} · observado {motivo}")

    def no_sondeable(self, ruta: RutaProtegida) -> None:
        """Deja constancia de una ruta que no admite sonda ALLOW y del porqué."""
        self.no_sondeadas.setdefault(
            f"{ruta.metodo} {ruta.plantilla}", set()).add(ruta.par)

    # -- agregados --------------------------------------------------------

    @property
    def total(self) -> int:
        return len(self.filas)

    def recuento(self, esperado: str) -> int:
        return sum(fila["esperado"].startswith(esperado) for fila in self.filas)

    def resumen_por_rol(self) -> dict[str, dict[str, int]]:
        return {
            rol: {
                "allow": cuadro["ALLOW"],
                "deny": cuadro["DENY"] + cuadro["DENY_SIN_SESION"],
                "pass": cuadro["PASS"],
                "fail": cuadro["FAIL"],
            }
            for rol, cuadro in sorted(self.por_rol.items())
        }

    def allow_no_sondeada(self) -> list[dict[str, object]]:
        return [
            {"recurso": recurso, "permisos": sorted(permisos)}
            for recurso, permisos in sorted(self.no_sondeadas.items())
        ]


# ══════════════════════════════════════════════════════════════════════════════
#  Escenario — empresa, roles y usuarios por SQL, tokens por `create_access_token`
# ══════════════════════════════════════════════════════════════════════════════

#: Tablas que pueden recibir filas como **efecto colateral** de una sonda ALLOW, todas con
#: `company_id` hacia la empresa de prueba. Son las cuatro rutas de SAP cuyo cuerpo es
#: íntegramente opcional: `{}` es válido y el manejador ejecuta (sin configuración HANA los
#: jobs nacen fallidos, que es justo el resultado inocuo que se busca). Se borran en orden
#: hijo → padre para que la empresa pueda eliminarse.
_EFECTOS_COLATERALES = (
    "sap_inbound_records",
    "sap_inbound_sync_jobs",
    "sap_payloads",
    "sap_sync_jobs",
    "consolidated_movements",
)


@pytest_asyncio.fixture
async def motor(test_database_url):
    """Motor propio del test, y limpieza por prefijo al terminar.

    Se limpia por prefijo y nunca por «todo»: la siembra de la suite (`seeds/test_seeds.py`)
    tiene que sobrevivir. Los asientos de auditoría se borran explícitamente porque se
    confirman dentro de la petición —sobreviven al rechazo que los provocó— y porque
    `audit_logs.company_id` es clave foránea hacia `companies`.
    """
    motor_ = create_async_engine(test_database_url)
    yield motor_

    from app.audit.models import AuditLog
    from app.auth.models import Permission, Role, User
    from app.masters.models import Company

    async with motor_.begin() as c:
        empresas = (await c.execute(
            select(Company.id).where(Company.name.like(f"{PREFIJO_EMPRESA}%")))).scalars().all()
        usuarios = (await c.execute(
            select(User.id).where(User.username.like(f"{PREFIJO_USUARIO}%")))).scalars().all()
        roles = (await c.execute(
            select(Role.id).where(Role.name.like(f"{PREFIJO_ROL}%")))).scalars().all()

        if empresas:
            ids = list(empresas)
            for tabla in _EFECTOS_COLATERALES:
                await c.execute(
                    text(f"DELETE FROM {tabla} WHERE company_id IN :ids")
                    .bindparams(bindparam("ids", expanding=True)),
                    {"ids": ids},
                )
        if usuarios:
            ids_usuarios = [str(u) for u in usuarios]
            condiciones = [AuditLog.user_id.in_(usuarios)]
            condiciones.append(or_(AuditLog.entity_type == "user",
                                   AuditLog.entity_id.in_(ids_usuarios)))
            await c.execute(delete(AuditLog).where(or_(*condiciones)))
        if roles:
            await c.execute(delete(AuditLog).where(
                AuditLog.entity_type == "role",
                AuditLog.entity_id.in_([str(r) for r in roles])))
        if empresas:
            await c.execute(delete(AuditLog).where(AuditLog.company_id.in_(empresas)))
        if usuarios:
            await c.execute(delete(User).where(User.id.in_(usuarios)))
        if roles:
            await c.execute(delete(Permission).where(Permission.role_id.in_(roles)))
            await c.execute(delete(Role).where(Role.id.in_(roles)))
        if empresas:
            await c.execute(delete(Company).where(Company.id.in_(empresas)))
    await motor_.dispose()


def _token(user_id: int) -> dict:
    """Cabecera de un usuario real de la base. Los permisos los resuelve la petición.

    Sin claim de compañía: el actor tiene empresa persistida y `resolver_empresa_efectiva`
    la toma de ahí. Un token que la reclamara probaría otra cosa —y el aislamiento exige que
    la reclamación se ignore para quien no puede cambiar de contexto.
    """
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


@pytest_asyncio.fixture
async def escenario_matriz(motor, test_database_url):
    """Empresa de prueba con **todos** los actores de la matriz, creados por SQL.

    ```
    MX-TEST-EMPRESA-<sufijo>
      <rol del producto>        con exactamente los permisos con que lo siembra el baseline
      MX-TEST-Rol vacío         sin un solo permiso (la API ya no lo permite: `DR-2`)
      MX-TEST-Solo m:a          con ese par y nada más
      MX-TEST-Todo menos m:a    con todos los pares del catálogo menos ése
      mx_test_inactivo          Super Administrador con `is_active = false`
    ```

    Los roles del producto son **plantillas de sistema** (`company_id IS NULL`), que es como
    los crea `seeds/baseline_seeds.sembrar_roles`; los demás son roles de la empresa. La
    autoridad global del Super Administrador exige esa forma (`OD-13.c`), de modo que
    crearlo como rol de inquilino habría convertido el control ALLOW total en un control de
    nada.
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.masters.models import Company

    sufijo = uuid.uuid4().hex[:8]
    catalogo = _catalogo(_rutas_protegidas())
    roles_producto = _roles_del_producto()

    #: (etiqueta del actor, nombre visible del rol, permisos, ¿plantilla de sistema?)
    definiciones: list[tuple[str, str, list[tuple[str, str]], bool]] = [
        (f"producto:{nombre}", nombre, pares, True)
        for nombre, pares in roles_producto.items()
    ]
    definiciones.append(("vacio", "Rol vacío", [], False))
    for par in catalogo:
        etiqueta = ":".join(par)
        definiciones.append((f"solo:{etiqueta}", f"Solo {etiqueta}", [par], False))
        definiciones.append((
            f"menos:{etiqueta}", f"Todo menos {etiqueta}",
            [otro for otro in catalogo if otro != par], False,
        ))

    # bcrypt es caro por diseño; hashear una vez y reutilizar no debilita nada aquí: los
    # actores no se autentican por contraseña —el test emite el token— y la clave es la
    # misma para todos.
    hash_unico = hash_password(CLAVE)

    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        empresa = Company(name=f"{PREFIJO_EMPRESA}{sufijo}", is_active=True)
        s.add(empresa)
        await s.flush()

        roles: dict[str, Role] = {}
        for etiqueta, nombre_visible, _pares, es_sistema in definiciones:
            rol = Role(
                name=f"{PREFIJO_ROL}{nombre_visible}-{sufijo}",
                description="Matriz de autorización AC-MX-01 (SPEC 013)",
                company_id=None if es_sistema else empresa.id,
                is_active=True,
            )
            s.add(rol)
            roles[etiqueta] = rol
        await s.flush()

        for etiqueta, _nombre, pares, _es_sistema in definiciones:
            for modulo, accion in pares:
                s.add(Permission(
                    role_id=roles[etiqueta].id, module=modulo,
                    action=PermissionAction(accion), scope_type="all",
                ))

        def _usuario(etiqueta: str, rol: Role, *, activo: bool = True) -> User:
            marca = etiqueta.replace(":", "-").replace("*", "ALL")
            return User(
                first_name="Matriz", last_name=etiqueta[:80],
                email=f"{PREFIJO_USUARIO}{marca}-{sufijo}@example.com",
                username=f"{PREFIJO_USUARIO}{marca}-{sufijo}",
                hashed_password=hash_unico, company_id=empresa.id,
                role_id=rol.id, is_active=activo,
            )

        usuarios = {etiqueta: _usuario(etiqueta, rol) for etiqueta, rol in roles.items()}
        # El inactivo lleva el rol que todo lo puede: así el único motivo del `401` es su
        # estado, no una falta de permisos.
        inactivo = _usuario("inactivo", roles[f"producto:{'Super Administrador'}"],
                            activo=False)
        s.add_all([*usuarios.values(), inactivo])
        await s.flush()

        ids_roles = [rol.id for rol in roles.values()]
        nombre_empresa = empresa.name
        identidades = {
            etiqueta: {"id": usuario.id, "username": usuario.username,
                       "rol": roles[etiqueta].name, "rol_id": roles[etiqueta].id}
            for etiqueta, usuario in usuarios.items()
        }
        identidades["inactivo"] = {
            "id": inactivo.id, "username": inactivo.username,
            "rol": roles["producto:Super Administrador"].name,
            "rol_id": roles["producto:Super Administrador"].id,
        }
        await s.commit()
    # ── P se lee de la base, no de la definición que acaba de escribirse ──
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        filas = (await s.execute(
            select(Permission.role_id, Permission.module, Permission.action)
            .where(Permission.role_id.in_(ids_roles))
        )).all()
    permisos_por_rol: dict[int, set[tuple[str, str]]] = defaultdict(set)
    for rol_id, modulo, accion in filas:
        permisos_por_rol[rol_id].add((modulo, getattr(accion, "value", str(accion))))

    actores: dict[str, dict] = {}
    for etiqueta, identidad in identidades.items():
        actores[etiqueta] = {
            "usuario": identidad["username"],
            "rol": identidad["rol"],
            "empresa": nombre_empresa,
            "permisos": frozenset(permisos_por_rol[identidad["rol_id"]]),
            "cabeceras": _token(identidad["id"]),
        }

    return {
        "empresa": nombre_empresa,
        "sufijo": sufijo,
        "url": test_database_url,
        "catalogo": catalogo,
        "roles_producto": roles_producto,
        "actores": actores,
    }


def _actor_anonimo(escenario: dict) -> dict:
    """Un actor sin credencial: sirve para demostrar que sin sesión no hay autorización."""
    return {
        "usuario": "(sin token)",
        "rol": "(anónimo)",
        "empresa": escenario["empresa"],
        "permisos": frozenset(),
        "cabeceras": None,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  Sondeo de un actor sobre una lista de rutas
# ══════════════════════════════════════════════════════════════════════════════

async def _sondar_actor(cliente, matriz: Matriz, actor: dict, rutas) -> None:
    """Sondea `rutas` con `actor`, esperando lo que el oráculo declara de cada una.

    La única ruta que no se sondea es la mutante sin parámetro de ruta y sin cuerpo cuando
    el oráculo dice ALLOW: no hay forma de invocarla sin ejecutar su efecto. Su DENY sí se
    sondea, porque el `403` ocurre antes del manejador.
    """
    for ruta in rutas:
        permitido = _oraculo(actor["permisos"], ruta.requeridos)
        if permitido and not ruta.sondeable_para_allow:
            matriz.no_sondeable(ruta)
            continue
        respuesta = await _sondear(cliente, actor["cabeceras"], ruta)
        matriz.registrar(actor, ruta, "ALLOW" if permitido else "DENY", respuesta)


# ══════════════════════════════════════════════════════════════════════════════
#  Sanidad de la enumeración — sin base de datos
# ══════════════════════════════════════════════════════════════════════════════

def test_ac_mx_01_la_matriz_sale_de_la_introspeccion_de_rutas():
    """La matriz no puede ser una lista: si lo fuera, una ruta nueva no aparecería.

    Comprueba tres cosas que hacen creíble lo que luego se mide: que la enumeración alcanza
    un número plausible de rutas protegidas, que **todos** los pares que exigen existen en el
    catálogo cerrado del producto (`PermissionAction` ∪ `MODULOS`, el mismo que valida la
    administración de roles) y que las rutas excluidas no se colaron con marca de permiso.
    """
    from app.auth.models import PermissionAction
    from app.auth.service import AuthService

    rutas = _rutas_protegidas()
    catalogo = _catalogo(rutas)

    assert len(rutas) >= 60, (
        f"la enumeración solo alcanza {len(rutas)} rutas protegidas: la introspección de "
        "`route.dependant` no está viendo las dependencias reales")
    assert len(catalogo) >= 20, f"catálogo de permisos sospechosamente corto: {catalogo}"

    acciones = {accion.value for accion in PermissionAction}
    modulos = set(AuthService.MODULOS)
    fuera_del_catalogo = [
        par for par in catalogo
        if par[1] not in acciones or (par[0] != "*" and par[0] not in modulos)
    ]
    assert not fuera_del_catalogo, (
        "rutas que exigen permisos que la administración de roles no puede conceder "
        f"(catálogo cerrado): {fuera_del_catalogo}")

    assert all(ruta.requeridos for ruta in rutas), "hay rutas protegidas sin permiso leído"
    excluidas_declaradas = [ruta.plantilla for ruta in rutas if ruta.plantilla in RUTAS_EXCLUIDAS]
    assert not excluidas_declaradas, (
        f"rutas excluidas por semántica que sí declaran permiso: {excluidas_declaradas}")
    # El camino sondeable sustituye los parámetros: sin esto, `{user_id}` llegaría literal.
    assert all("{" not in ruta.camino for ruta in rutas), "quedan parámetros sin sustituir"


def test_ac_mx_01_los_roles_del_producto_se_importan_de_su_fuente_unica():
    """Una copia de la matriz en el test sería la tercera definición de la misma verdad.

    Si esta comprobación falla porque el baseline cambió, el test no debe adaptarse: debe
    heredar el cambio, que es lo que ocurre al importarlo. Lo que aquí se fija es que el
    import trae lo que se espera y no una estructura vacía.
    """
    from app.auth.models import PermissionAction

    roles = _roles_del_producto()
    for nombre in ("Operador de Granja", "Supervisor Avícola", "Aprobador",
                   "Analista SAP", "Auditor", ROL_ADMINISTRADOR_DE_ACCESOS):
        assert roles.get(nombre), f"el rol de producto «{nombre}» llega vacío o no llega"

    assert roles["Super Administrador"] == [
        ("*", accion.value) for accion in PermissionAction
    ], "el comodín del Super Administrador no cubre todas las acciones"

    # `OD-15.a`/`OD-15.b`: administrar el acceso no es acceder, y son exactamente cuatro.
    assert roles[ROL_ADMINISTRADOR_DE_ACCESOS] == [
        ("business_units", PermissionAction.READ.value),
        ("business_units", PermissionAction.UPDATE.value),
        ("business_units", PermissionAction.CREATE.value),
        ("business_units", PermissionAction.DELETE.value),
    ], ("Administrador de Accesos debe tener exactamente los cuatro permisos de "
        "`business_units` y ninguno de `users`")


# ══════════════════════════════════════════════════════════════════════════════
#  `B4a-2` — la matriz ejecutada contra la aplicación real
#
#  Cuatro fases de sondeo y una aserción global:
#
#    (a) `roles_producto` todos los roles del producto sobre todas las rutas
#    (b) `rol_vacio`      un rol sin permisos no alcanza nada
#    (c) `un_permiso`     «SOLO m:a» concede exactamente su par; «TODO MENOS m:a» lo deniega
#    (d) `sin_sesion`     sin token y con token de un usuario inactivo no hay autorización
#
#  Las fases acumulan en un único `Matriz`, de modo que la evidencia final y la aserción de
#  cobertura cubren las cuatro sin repetir ni una sonda. Cada test trae su propio
#  `escenario_matriz`; `_asegurar_fase` ejecuta la fase que falte, de manera que el orden de
#  los tests —o ejecutar uno solo con `-k`— no cambia lo que se afirma.
# ══════════════════════════════════════════════════════════════════════════════

#: Los cinco roles operativos que siembra el baseline. El administrador de accesos y el Super
#: Administrador se recorren aparte porque no salen de la migración de la matriz de permisos.
ROLES_OPERATIVOS = (
    "Operador de Granja",
    "Supervisor Avícola",
    "Aprobador",
    "Analista SAP",
    "Auditor",
)
ROL_SUPER_ADMIN = "Super Administrador"


class Acumulado:
    """Lo que las fases dejan para la aserción global y para la evidencia.

    El acumulador resuelve la enumeración en su constructor, nunca al importar el módulo: la
    introspección importa `app.main`, y eso solo es válido después de la guarda de entorno
    que `conftest.pytest_configure` aplica.
    """

    def __init__(self) -> None:
        self.matriz = Matriz()
        self.rutas = _rutas_protegidas()
        self.catalogo = _catalogo(self.rutas)
        #: Duración de cada fase, en segundos.
        self.fases: dict[str, float] = {}
        #: El último escenario usado, por si la evidencia necesita su empresa.
        self.escenario: dict | None = None

    @property
    def segundos(self) -> float:
        return round(sum(self.fases.values()), 1)


_ACUMULADO: Acumulado | None = None


def _acumulado() -> Acumulado:
    """El acumulador del módulo, creado al primer uso."""
    global _ACUMULADO
    if _ACUMULADO is None:
        _ACUMULADO = Acumulado()
    return _ACUMULADO


def _mensaje_fallos(fallos: list[str], *, total: int | None = None) -> str:
    """Los primeros fallos y el recuento: un fallo masivo no cabe en un mensaje legible."""
    cuenta = len(fallos) if total is None else total
    muestra = fallos[:_MAXIMO_FALLOS_EN_MENSAJE]
    cola = ""
    if cuenta > len(muestra):
        cola = f"\n  … y {cuenta - len(muestra)} más (ver `matrix_role_route.json`)"
    return f"{cuenta} sonda(s) FAIL:\n  " + "\n  ".join(muestra) + cola


# ── Fase (a) · los roles del producto, sobre todas las rutas ──────────────────

async def _fase_roles_producto(cliente, escenario: dict, acum: Acumulado) -> None:
    """Sondea cada rol del producto contra **todas** las rutas protegidas.

    El Super Administrador entra como control: su comodín `("*", accion)` cubre todas las
    acciones, así que cualquier DENY suyo sería una divergencia entre la base y la guarda.
    """
    actores = escenario["actores"]
    for nombre in (*ROLES_OPERATIVOS, ROL_ADMINISTRADOR_DE_ACCESOS, ROL_SUPER_ADMIN):
        await _sondar_actor(cliente, acum.matriz, actores[f"producto:{nombre}"], acum.rutas)


# ── Fase (b) · un rol sin permisos ───────────────────────────────────────────

async def _fase_rol_vacio(cliente, escenario: dict, acum: Acumulado) -> None:
    """Un rol sin un solo permiso tiene que recibir el `403` de autorización en todas.

    El `detail` exacto se comprueba en `_evaluar`: un `403` de otra guarda no vale como
    denegación de permisos, porque no probaría que la matriz se aplicó.
    """
    await _sondar_actor(cliente, acum.matriz, escenario["actores"]["vacio"], acum.rutas)


# ── Fase (c) · un permiso, y todos menos uno ─────────────────────────────────

async def _fase_un_permiso(cliente, escenario: dict, acum: Acumulado) -> None:
    """Por cada par del catálogo: «SOLO m:a» y «TODO MENOS m:a».

    «SOLO m:a» debe alcanzar las rutas que exigen ese par —y solo esas—; «TODO MENOS m:a»
    debe ser rechazado en **todas** las rutas que lo exigen, que es la mitad que un ALLOW
    no demuestra. Las muestras de contraste (3 DENY para el primero, 2 ALLOW para el
    segundo) cubren el resto del catálogo con cada actor.
    """
    actores = escenario["actores"]
    for par in acum.catalogo:
        etiqueta = ":".join(par)
        solo = actores[f"solo:{etiqueta}"]
        menos = actores[f"menos:{etiqueta}"]

        # ALLOW: las rutas cuyo único requerido es el par.
        await _sondar_actor(
            cliente, acum.matriz, solo,
            [ruta for ruta in acum.rutas if ruta.requeridos == (par,)])
        # DENY: las 3 primeras rutas que exigen algo más que ese par.
        await _sondar_actor(
            cliente, acum.matriz, solo,
            [ruta for ruta in acum.rutas if not set(ruta.requeridos) <= {par}][:3])

        # DENY: todas las rutas que exigen el par.
        await _sondar_actor(
            cliente, acum.matriz, menos,
            [ruta for ruta in acum.rutas if par in ruta.requeridos])
        # ALLOW: las 2 primeras rutas sondeables que no lo exigen.
        await _sondar_actor(
            cliente, acum.matriz, menos,
            [ruta for ruta in acum.rutas
             if par not in ruta.requeridos and ruta.sondeable_para_allow][:2])


# ── Fase (d) · sin sesión ────────────────────────────────────────────────────

async def _fase_sin_sesion(cliente, escenario: dict, acum: Acumulado) -> None:
    """Sin token y con el token de un usuario inactivo: `401` antes de evaluar permiso.

    La muestra es determinista y repartida (cada k-ésima ruta), no aleatoria. El inactivo
    lleva el rol que todo lo puede, de modo que el único motivo del `401` es su estado.
    """
    anonimo = _actor_anonimo(escenario)
    paso = max(1, len(acum.rutas) // 40)
    for ruta in acum.rutas[::paso]:
        respuesta = await _sondear(cliente, None, ruta)
        acum.matriz.registrar(anonimo, ruta, "DENY_SIN_SESION", respuesta)

    inactivo = escenario["actores"]["inactivo"]
    paso = max(1, len(acum.rutas) // 12)
    for ruta in acum.rutas[::paso]:
        respuesta = await _sondear(cliente, inactivo["cabeceras"], ruta)
        acum.matriz.registrar(inactivo, ruta, "DENY_SIN_SESION", respuesta)


#: Las fases por nombre, en el orden en que conviene ejecutarlas.
_FASES = {
    "roles_producto": _fase_roles_producto,
    "rol_vacio": _fase_rol_vacio,
    "un_permiso": _fase_un_permiso,
    "sin_sesion": _fase_sin_sesion,
}


async def _asegurar_fase(nombre: str, cliente, escenario: dict,
                         acum: Acumulado) -> tuple[list[str], list[dict]]:
    """Ejecuta la fase si aún no está hecha; devuelve sus fallos y sus filas nuevas."""
    antes_fallos = len(acum.matriz.fallos)
    antes_filas = len(acum.matriz.filas)
    if nombre not in acum.fases:
        inicio = time.monotonic()
        await _FASES[nombre](cliente, escenario, acum)
        acum.fases[nombre] = round(time.monotonic() - inicio, 3)
        acum.escenario = escenario
    return acum.matriz.fallos[antes_fallos:], acum.matriz.filas[antes_filas:]


# ══════════════════════════════════════════════════════════════════════════════
#  Los tests de la matriz ejecutada
# ══════════════════════════════════════════════════════════════════════════════

async def test_mx_01_roles_del_producto_matriz_completa(http_client, escenario_matriz):
    """`AC-MX-01`: cada rol del producto se sondea en **todas** las rutas protegidas.

    El oráculo es la base —los permisos persistidos del rol, leídos después de escribirlos—,
    no la definición que el test acaba de sembrar: si la siembra y la aplicación divergen,
    esta fase lo dice. El Super Administrador es el control de ALLOW total.
    """
    acum = _acumulado()
    fallos, filas = await _asegurar_fase("roles_producto", http_client, escenario_matriz, acum)

    esperados = (*ROLES_OPERATIVOS, ROL_ADMINISTRADOR_DE_ACCESOS, ROL_SUPER_ADMIN)
    ausentes = [n for n in esperados if n not in escenario_matriz["roles_producto"]]
    assert not ausentes, f"roles del producto que no llegan desde la fuente única: {ausentes}"

    sondeables = sum(1 for ruta in acum.rutas if ruta.sondeable_para_allow)
    for nombre in esperados:
        rol = escenario_matriz["actores"][f"producto:{nombre}"]["rol"]
        cuadro = acum.matriz.por_rol[rol]
        assert cuadro["PASS"] + cuadro["FAIL"] > 0, (
            f"el rol «{nombre}» no produjo ni una sola sonda")
        if nombre == ROL_SUPER_ADMIN:
            assert cuadro["DENY"] == 0, (
                f"el comodín del Super Administrador recibió {cuadro['DENY']} DENY: la base "
                "le concede todas las acciones, la guarda debería dejarle pasar siempre")
            assert cuadro["ALLOW"] == sondeables, (
                f"el Super Administrador solo alcanzó {cuadro['ALLOW']} de las "
                f"{sondeables} rutas sondeables para ALLOW")

    assert len(filas) > 0, "la fase de roles del producto no registró ninguna fila"
    assert not fallos, _mensaje_fallos(fallos)


async def test_mx_02_rol_vacio_deniega_todo(http_client, escenario_matriz):
    """Un rol sin permisos no alcanza **ninguna** ruta protegida, y por autorización.

    La comprobación es del `403` con `Permiso requerido: m:a`, no de «un 403»: un rechazo de
    otra guarda (empresa, unidad de negocio, regla de dominio) no probaría que la matriz se
    aplicó, y sería justo el caso que dejaría pasar un rol vacío con acceso.
    """
    acum = _acumulado()
    fallos, filas = await _asegurar_fase("rol_vacio", http_client, escenario_matriz, acum)

    actor = escenario_matriz["actores"]["vacio"]
    assert actor["permisos"] == frozenset(), (
        f"el rol «vacío» tiene permisos en la base: {sorted(actor['permisos'])}")
    assert len(filas) == len(acum.rutas), (
        f"el rol vacío se sondeó en {len(filas)} de {len(acum.rutas)} rutas protegidas")
    assert all(fila["esperado"] == "DENY" for fila in filas), "alguna sonda no esperaba DENY"
    assert not fallos, _mensaje_fallos(fallos)


async def test_mx_03_un_permiso_solo_y_todo_menos_uno(http_client, escenario_matriz):
    """Los dos bordes del catálogo, par a par: conceder uno solo y quitar uno solo.

    «SOLO m:a» demuestra que el par **basta** para las rutas que lo exigen (ALLOW) y que no
    abre nada más (3 DENY de contraste). «TODO MENOS m:a» demuestra lo contrario: que el par
    es **necesario** en todas las rutas que lo exigen (DENY) y que su ausencia no cierra las
    demás (2 ALLOW de contraste). Juntos, el par es exactamente lo que la ruta pide.
    """
    acum = _acumulado()
    fallos, filas = await _asegurar_fase("un_permiso", http_client, escenario_matriz, acum)
    assert not fallos, _mensaje_fallos(fallos)

    actores = escenario_matriz["actores"]
    sin_allow_solo: list[str] = []
    deny_incompletos: list[str] = []
    contrastes_mal: list[str] = []
    for par in acum.catalogo:
        etiqueta = ":".join(par)
        rol_solo = actores[f"solo:{etiqueta}"]["rol"]
        rol_menos = actores[f"menos:{etiqueta}"]["rol"]
        solo = [f for f in filas if f["rol"] == rol_solo]
        menos = [f for f in filas if f["rol"] == rol_menos]

        allow_solo = sum(f["esperado"] == "ALLOW" for f in solo)
        deny_solo = sum(f["esperado"] == "DENY" for f in solo)
        deny_menos = sum(f["esperado"] == "DENY" for f in menos)
        allow_menos = sum(f["esperado"] == "ALLOW" for f in menos)
        exigidas = sum(1 for ruta in acum.rutas if par in ruta.requeridos)

        if allow_solo == 0:
            sin_allow_solo.append(f"{par[0]}:{par[1]}")
        if deny_menos != exigidas:
            deny_incompletos.append(
                f"{par[0]}:{par[1]} → {deny_menos} DENY de {exigidas} rutas que lo exigen")
        if deny_solo != 3 or allow_menos != 2:
            contrastes_mal.append(
                f"{par[0]}:{par[1]} → contraste SOLO {deny_solo}/3 DENY, "
                f"TODO MENOS {allow_menos}/2 ALLOW")

    assert not sin_allow_solo, (
        f"«SOLO m:a» no alcanzó ninguna ruta para estos pares: {sin_allow_solo}")
    assert not deny_incompletos, (
        "«TODO MENOS m:a» no fue denegado en todas las rutas que exigen el par: "
        f"{deny_incompletos}")
    assert not contrastes_mal, (
        "muestras de contraste incompletas (¿rutas mutantes sin sonda ALLOW segura?): "
        f"{contrastes_mal}")


async def test_mx_04_sin_token_e_inactivo(http_client, escenario_matriz):
    """Sin token no se llega a evaluar permiso, y un usuario inactivo tampoco.

    El código exigido es `401`, no un `403`: una ruta protegida que devolviera `403` sin
    sesión estaría revelando la existencia de la ruta y el permiso que exige.
    """
    acum = _acumulado()
    fallos, filas = await _asegurar_fase("sin_sesion", http_client, escenario_matriz, acum)

    anonimo = _actor_anonimo(escenario_matriz)
    inactivo = escenario_matriz["actores"]["inactivo"]
    sin_token = [f for f in filas if f["usuario"] == anonimo["usuario"]]
    inactivo_filas = [f for f in filas if f["usuario"] == inactivo["usuario"]]

    assert len(sin_token) >= 30, f"solo {len(sin_token)} rutas sondeadas sin token"
    assert len(inactivo_filas) >= 10, (
        f"solo {len(inactivo_filas)} rutas sondeadas con el usuario inactivo")

    codigos_sin_token = Counter(f["api"] for f in sin_token)
    codigos_inactivo = Counter(f["api"] for f in inactivo_filas)
    assert set(codigos_sin_token) == {401}, (
        f"sin token se observaron estos códigos: {dict(codigos_sin_token)}")
    assert set(codigos_inactivo) == {401}, (
        f"con el token del usuario inactivo se observaron estos códigos: "
        f"{dict(codigos_inactivo)}")
    assert not fallos, _mensaje_fallos(fallos)


async def test_mx_05_cobertura_y_evidencia(http_client, escenario_matriz):
    """Cierre: sin un solo FAIL, todo el catálogo con ALLOW y DENY observados.

    Que no haya fallos no basta —una matriz que no sondea no falla—: se exige además que
    cada par del catálogo tenga al menos una sonda ALLOW y una DENY, y que ninguna ruta
    protegida se haya quedado sin sondeo. Las fases que falten se ejecutan aquí, así que
    este test vale también como única invocación (`-k mx_05`).

    La evidencia solo se escribe con `GA_WRITE_MATRIX=1`, para que la suite normal no
    ensucie el árbol. Contiene nombres de usuario y de rol, ruta, par exigido, resultado
    esperado y código observado: ningún token, contraseña ni DSN.
    """
    acum = _acumulado()
    for nombre in _FASES:
        await _asegurar_fase(nombre, http_client, escenario_matriz, acum)

    assert not acum.matriz.fallos, _mensaje_fallos(acum.matriz.fallos)

    sin_allow = _pares_sin_allow(acum)
    sin_deny = [
        f"{modulo}:{accion}" for modulo, accion in acum.catalogo
        if acum.matriz.deny_por_par[(modulo, accion)] == 0
    ]
    assert not sin_allow, f"pares del catálogo sin una sola sonda ALLOW observada: {sin_allow}"
    assert not sin_deny, f"pares del catálogo sin una sola sonda DENY observada: {sin_deny}"

    nunca_sondeadas = _rutas_nunca_sondeadas(acum)
    assert not nunca_sondeadas, (
        f"rutas protegidas que no se sondearon nunca: {nunca_sondeadas}")

    if os.environ.get("GA_WRITE_MATRIX") != "1":
        return

    escritas = _escribir_evidencia(acum)
    for ruta in escritas:
        assert ruta.exists(), f"la evidencia no se escribió: {ruta}"
        assert ruta.stat().st_size > 0, f"la evidencia quedó vacía: {ruta}"


# ══════════════════════════════════════════════════════════════════════════════
#  Evidencia — solo con `GA_WRITE_MATRIX=1`
# ══════════════════════════════════════════════════════════════════════════════

def _pares_sin_allow(acum: Acumulado) -> list[str]:
    """Pares del catálogo de los que no se observó ni una sola sonda ALLOW."""
    return [
        f"{modulo}:{accion}" for modulo, accion in acum.catalogo
        if (modulo, accion) not in ALLOWLIST_SIN_ALLOW
        and acum.matriz.allow_por_par[(modulo, accion)] == 0
    ]


def _rutas_nunca_sondeadas(acum: Acumulado) -> list[str]:
    """Rutas protegidas de las que no se registró ni una sonda, de ningún tipo."""
    return [
        f"{ruta.metodo} {ruta.plantilla}" for ruta in acum.rutas
        if acum.matriz.veces_sondeada[(ruta.metodo, ruta.plantilla)] == 0
    ]


def _escribir_evidencia(acum: Acumulado) -> tuple[pathlib.Path, pathlib.Path]:
    """Escribe la tabla por sonda y el resumen por rol. Sin credenciales de ningún tipo."""
    DIR_EVIDENCIA.mkdir(parents=True, exist_ok=True)
    ruta_json = DIR_EVIDENCIA / "matrix_role_route.json"
    ruta_md = DIR_EVIDENCIA / "matrix_summary.md"

    ruta_json.write_text(
        json.dumps(acum.matriz.filas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    sin_allow = _pares_sin_allow(acum)
    nunca_sondeadas = _rutas_nunca_sondeadas(acum)
    filas = acum.matriz.filas
    sin_sesion = sum(1 for fila in filas if fila["esperado"].startswith("DENY (sin"))
    allow = acum.matriz.recuento("ALLOW")
    deny = acum.matriz.recuento("DENY") - sin_sesion
    pass_ = sum(1 for fila in filas if fila["resultado"] == "PASS")
    fail = len(filas) - pass_

    tiempos = ", ".join(
        f"{nombre} {segundos:.1f} s" for nombre, segundos in sorted(acum.fases.items()))
    lineas = [
        "# AC-MX-01 · Matriz de autorización ejecutada (`SPEC 013`, `B4a`)",
        "",
        "Generada por `backend/tests/test_uat_admin_rbac_matrix.py` con `GA_WRITE_MATRIX=1`.",
        f"Fecha (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}.",
        "",
        "## Totales",
        "",
        f"* rutas protegidas enumeradas por introspección: **{len(acum.rutas)}**",
        f"* pares `(modulo, accion)` exigidos por alguna ruta: **{len(acum.catalogo)}**",
        f"* sondas ejecutadas: **{len(filas)}** (ALLOW {allow} · DENY {deny} · "
        f"sin sesión {sin_sesion})",
        f"* resultado: **PASS {pass_} · FAIL {fail}**",
        f"* tiempo: {tiempos} · total {acum.segundos:.1f} s",
        "",
        "## Por rol",
        "",
        "| rol | ALLOW | DENY | PASS | FAIL |",
        "|---|---|---|---|---|",
    ]
    for rol, cuadro in acum.matriz.resumen_por_rol().items():
        lineas.append(f"| {rol} | {cuadro['allow']} | {cuadro['deny']} | "
                      f"{cuadro['pass']} | {cuadro['fail']} |")

    lineas += ["", "## `allow_no_sondeada`", ""]
    no_sondeadas = acum.matriz.allow_no_sondeada()
    if no_sondeadas:
        for entrada in no_sondeadas:
            permisos = ", ".join(f"`{par}`" for par in entrada["permisos"])
            lineas.append(f"* `{entrada['recurso']}` → {permisos}")
    else:
        lineas.append("* ninguna: toda ruta protegida admitió una sonda ALLOW segura")

    lineas += ["", "## Pares del catálogo sin sonda ALLOW", ""]
    if sin_allow:
        lineas += [f"* `{par}`" for par in sin_allow]
    else:
        lineas.append("* ninguno")

    lineas += ["", "## Rutas protegidas nunca sondeadas", ""]
    if nunca_sondeadas:
        lineas += [f"* `{recurso}`" for recurso in nunca_sondeadas]
    else:
        lineas.append("* ninguna")

    ruta_md.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return ruta_json, ruta_md
