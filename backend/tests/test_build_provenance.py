"""`SPEC 016 §B` — procedencia del build · `GET /api/v1/version`.

Pregunta que resuelve: **qué artefacto está sirviendo esta petición**. Un operador que
diagnostica un incidente necesita el `SHA` antes de tener sesión, porque la primera sospecha
suele ser el despliegue.

Lo que estas pruebas protegen, además del contenido:

    PUBLICA            la respuesta no exige sesión ni filtra nada por empresa
    ACOTADA            tres claves exactas; ni un campo de más
    NO INVENTADA       el `SHA` viene del `build-arg`, no de inspeccionar el disco
    DECLARADA          la exención de autorización y el alcance están escritos, no heredados
    REPRODUCIBLE       el `Dockerfile` inyecta lo que la ruta lee
"""
from __future__ import annotations

import pathlib

#: Raíz del backend, resuelta desde este archivo y no desde el directorio de ejecución.
RAIZ = pathlib.Path(__file__).resolve().parents[1]

#: Lo que la respuesta **jamás** puede contener, ni como clave ni dentro de un valor. La
#: lista es corta a propósito: son las formas en que una proyección descuidada filtraría
#: credenciales o rutas del servidor.
PROHIBIDO = ("password", "secret", "DATABASE", "postgres://", "/home/")


# ── VP-01 · lo inyectado es lo que se responde ───────────────────────────────

async def test_vp_01_la_respuesta_es_lo_inyectado_en_el_build(http_client, monkeypatch):
    """Sin sesión: `200`, y las tres cadenas tal cual se configuraron."""
    from app.config import settings

    monkeypatch.setattr(settings, "GA_GIT_SHA", "abc123def456")
    monkeypatch.setattr(settings, "GA_BUILD_TIME", "2026-11-18T12:00:00Z")
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    r = await http_client.get("/api/v1/version")

    assert r.status_code == 200, r.text
    assert r.json() == {
        "git_sha": "abc123def456",
        "build_time": "2026-11-18T12:00:00Z",
        "environment": "production",
    }, r.json()


# ── VP-02 · la proyección está acotada ───────────────────────────────────────

async def test_vp_02_ni_una_clave_de_mas_ni_un_secreto(http_client):
    """Tres claves exactas. Un `**settings` habría volcado credenciales a internet."""
    r = await http_client.get("/api/v1/version")

    assert r.status_code == 200, r.text
    assert set(r.json()) == {"git_sha", "build_time", "environment"}, r.json()

    texto = r.text
    filtrado = [aguja for aguja in PROHIBIDO if aguja in texto]
    assert filtrado == [], f"la respuesta filtra {filtrado}: {texto}"


# ── VP-04 · sin inyección, `unknown` — y no se pregunta al repositorio ───────

async def test_vp_04_sin_inyeccion_la_respuesta_es_unknown(http_client):
    """`unknown` es la respuesta honesta: fuera del contenedor no hay `build-arg` que leer.

    Además comprueba que el valor por defecto del modelo es `unknown` y no un `SHA` inventado:
    un default plausible sería peor que ninguno, porque parecería información.
    """
    from app.config import Settings, settings

    assert Settings.model_fields["GA_GIT_SHA"].default == "unknown"
    assert Settings.model_fields["GA_BUILD_TIME"].default == "unknown"
    # La suite no inyecta estas variables: si alguien las exporta, esta expectativa deja de
    # valer y el mensaje lo dice en lugar de fallar de forma opaca.
    assert settings.GA_GIT_SHA == "unknown", settings.GA_GIT_SHA
    assert settings.GA_BUILD_TIME == "unknown", settings.GA_BUILD_TIME

    r = await http_client.get("/api/v1/version")

    assert r.status_code == 200, r.text
    assert r.json()["git_sha"] == "unknown", r.json()
    assert r.json()["build_time"] == "unknown", r.json()


def test_vp_04_el_modulo_no_interroga_al_repositorio():
    """El `SHA` no se obtiene ejecutando nada: la imagen no lleva `.git`.

    Se comprueba sobre el fuente porque lo que hay que impedir es la reintroducción de la
    idea —inspeccionar el árbol en tiempo de petición—, no un fallo de comportamiento. Y de
    paso, que la ruta no pueda lanzar un proceso sea lo que sea que llegue por la red.
    """
    fuente = (RAIZ / "app" / "version.py").read_text(encoding="utf-8")

    assert "subprocess" not in fuente, "la ruta no debe lanzar procesos"
    assert "git rev-parse" not in fuente, "el SHA viene del build-arg, no del repositorio"


# ── VP-06 · la exención está declarada, no heredada ─────────────────────────

async def test_vp_06_la_ruta_es_publica_y_declarada(http_client):
    """Dos mitades de la misma decisión: la clasificación escrita y la respuesta sin token.

    Sin la primera, el arranque falla (`route_scope.verificar`); sin la segunda, el `PUBLICA`
    sería una etiqueta que no describe lo que ocurre.
    """
    from app.authorization_coverage import RUTAS_PUBLICAS
    from app.business_units.route_scope import RUTAS, Alcance

    alcance, unidad, motivo = RUTAS["/api/v1/version"]
    assert alcance is Alcance.PUBLICA, alcance
    assert unidad is None, "una ruta pública no puede exigir unidad de negocio"
    assert motivo.strip(), "la clasificación debe declarar su motivo"
    assert "/api/v1/version" in RUTAS_PUBLICAS, (
        "la exención de autorización tiene que estar declarada, no deducida")

    r = await http_client.get("/api/v1/version")  # deliberadamente sin `Authorization`
    assert r.status_code == 200, r.text


# ── VP-05a · el `Dockerfile` inyecta lo que la ruta lee ─────────────────────

def test_vp_05a_el_dockerfile_inyecta_el_sha_como_build_arg():
    """La ruta solo sirve de algo si el artefacto trae el dato.

    Se lee el `Dockerfile` real: es el contrato entre quien construye la imagen y quien la
    interroga después. Un `ARG` con valor por defecto `unknown` mantiene el build posible sin
    pasar argumentos; el `LABEL` deja la misma procedencia en la metadata de la imagen, donde
    la lee el registro sin arrancar el contenedor.
    """
    dockerfile = (RAIZ / "Dockerfile").read_text(encoding="utf-8")

    assert "ARG GIT_SHA" in dockerfile, "falta el ARG del commit"
    assert "ARG BUILD_TIME" in dockerfile, "falta el ARG de la fecha de build"
    assert "org.opencontainers.image.revision" in dockerfile, (
        "la imagen debe declarar su revisión también como label")
    assert "ENV GA_GIT_SHA=$GIT_SHA" in dockerfile, (
        "el ARG tiene que llegar al entorno que lee `Settings`")
