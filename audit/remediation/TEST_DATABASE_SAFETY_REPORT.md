# TEST DATABASE SAFETY REPORT

**Fecha** 2026-09-03 · **Wave** 1.5 · **Track** B · `GA-REM-014`

Este informe documenta cómo se aprovisionó una base de datos de pruebas aislada **sin
privilegios de administración y sin tocar producción**, y qué garantías impiden que la
suite alcance datos reales.

---

## 1. El problema de partida

La auditoría (Wave 0) se negó a ejecutar los 101 tests del backend porque el único
`DATABASE_URL` configurado apuntaba a un PostgreSQL en IP pública que, por todos los
indicios, sirve al entorno real — y la suite **escribe** eventos, correcciones,
aprobaciones y usuarios. No existía ninguna guarda que lo impidiera: bastaba ejecutar
`pytest` para escribir en producción.

`GA-REM-014` quedó en Wave 1 como `IMPLEMENTED · verificación parcial`, con `AC03` y `AC05`
en `BLOCKED_EXTERNAL`: la guarda existía y funcionaba, pero **no había ningún motor de base
de datos** en la máquina para demostrar el ciclo completo.

---

## 2. Restricción de privilegios y cómo se resolvió sin bypass

`sudo` exige contraseña en esta máquina Debian 12, de modo que
`apt install postgresql` no era posible. El encargo es explícito: *«Si requiere privilegios
que no están disponibles: NO intentar bypass. Registrar `BLOCKED_BY_PRIVILEGE`.»*

No se intentó ningún bypass. Tampoco se recurrió a la opción de crear una base separada
**dentro del servidor de producción**, expresamente desaconsejada.

La solución fue lateral y legítima: el paquete **`pgserver`** de PyPI empaqueta binarios de
**PostgreSQL 16.2** y ejecuta un servidor **en espacio de usuario**, sobre un socket Unix
bajo `$HOME`, sin root, sin systemd y sin modificar ninguna configuración global del
sistema.

```
PostgreSQL 16.2 on x86_64-pc-linux-gnu, compiled by gcc (GCC) 10.2.1
```

Es PostgreSQL real, no un sustituto: la misma versión mayor que producción, con los mismos
tipos, restricciones y comportamiento transaccional. Ejecutar la suite contra SQLite habría
sido más fácil y habría invalidado el resultado.

---

## 3. La instancia de pruebas

| Elemento | Valor |
|---|---|
| Motor | PostgreSQL 16.2 (`pgserver`, espacio de usuario) |
| `PGDATA` | `~/.local/share/global_avicola_test_pg` (59 MB) |
| Conexión | **socket Unix**, no TCP — sin puerto de red expuesto |
| Base | `global_avicola_test` |
| Rol | `global_avicola_test_user` |
| Gestor | `backend/scripts/test_db.py` — `start` · `dsn` · `reset` · `stop` · `status` |
| Persistencia | `pgserver.get_server(PGDATA, cleanup_mode=None)` |

La conexión por socket Unix es una garantía por sí misma: **la instancia de pruebas no es
alcanzable por red**, ni siquiera desde la propia máquina por TCP.

`test_db.py` incorpora su propia lista de bases prohibidas
(`avicolav2`, `avicola`, `globalavicola`, `postgres`) y rehúsa operar sobre cualquiera de
ellas, de modo que ni siquiera un uso equivocado del gestor puede alcanzar un nombre de
producción.

---

## 4. La guarda de entorno — cinco señales, fail-closed

`backend/tests/environment_guard.py` exige que **las cinco** señales sean afirmativas.
Cualquier ausencia, ambigüedad o contradicción aborta antes de abrir conexión alguna.

| # | Señal | Qué comprueba |
|---|---|---|
| 1 | `ENVIRONMENT` | no puede ser `production`, `prod`, `staging`, `pre` ni `preprod` |
| 2 | `GA_TEST_ENV=1` | marcador explícito: la ejecución debe declararse de forma consciente |
| 3 | `GA_TEST_DATABASE_URL` | el DSN de pruebas se declara **aparte**, nunca se hereda de `DATABASE_URL` |
| 4 | Nombre de la base | debe cumplir `^(test_|.*_test$)` y no estar en la lista prohibida |
| 5 | Sin colisión con la aplicación | el DSN de pruebas no puede coincidir con el que declara `backend/.env` |

La guarda actúa en `pytest_configure`, **antes de la recolección y antes de importar la
aplicación**. `--collect-only` queda exento porque no abre conexiones. Al abortar usa
`pytest.exit(..., returncode=3)`, un código distinguible de un fallo de test.

### 4.1 Corrección de un falso positivo (Wave 1.5)

La señal 5 comparaba originalmente el DSN de pruebas con la **variable de entorno**
`DATABASE_URL`. Pero el flujo legítimo —`run_tests.sh`— sobrescribe esa variable con el DSN
de pruebas justo después de validar. La guarda se veía a sí misma y abortaba:

```
La base de pruebas coincide exactamente con la base de la aplicación
```

Se corrigió leyendo el DSN declarado en el **fichero** `backend/.env`
(`_configured_app_database_url()`), que es la fuente estable de la configuración de la
aplicación y no la altera el propio proceso de pruebas. Se añadió el test de regresión
`test_no_hay_falso_positivo_al_sobrescribir_database_url`.

Merece registrarse: **el fallo fue de la guarda cerrando de más, no de menos.** Una guarda
fail-closed que se equivoca, se equivoca hacia el lado seguro.

---

## 5. Verificación — `T-014-01` … `T-014-06`

| ID | Verificación | Resultado |
|---|---|---|
| `T-014-01` | DSN apuntando a la base de producción (`avicolav2`) | **PASS** — `«La base 'avicolav2' está en la lista de bases prohibidas para pruebas»`, abortado sin abrir conexión |
| `T-014-02` | `ENVIRONMENT=production` | **PASS** — `«ENVIRONMENT='production' es un entorno no apto para pruebas»` |
| `T-014-03` | Sin el marcador `GA_TEST_ENV` | **PASS** — `«Falta el marcador explícito GA_TEST_ENV=1»` |
| `T-014-04` | Nombre de base sin patrón de prueba (`produccion_avicola`) | **PASS** — `«no cumple el patrón exigido»` |
| `T-014-05` | `--collect-only` exento | **PASS** — `101 tests collected`, sin abortar, sin conectar |
| `T-014-06` | Ciclo completo reproducible y determinista | **PASS** — `run_tests.sh` ejecuta crear → migrar → verificar → sembrar → `pytest`; dos ejecuciones consecutivas dan `26 failed · 74 passed · 1 skipped` idéntico |

Los **25 tests** de `tests/test_environment_guard.py` pasan (`25 passed in 0.21s`). Si
alguien debilita la guarda, fallan.

---

## 6. Verificación de esquema en cada ejecución

`run_tests.sh` no da por bueno el estado de la base. Antes de sembrar comprueba:

- la cadena Alembic tiene **exactamente un *head*** (`i9j0k1l2m3n4`);
- el *head* registrado en la base coincide con el del código;
- hay **48 tablas** (47 + `alembic_version`).

Cualquier discrepancia aborta. Esto convierte cada ejecución en una verificación implícita
de la integridad de las 21 migraciones.

---

## 7. Credenciales de prueba

| Garantía | Cómo se cumple |
|---|---|
| Locales y solo de prueba | `run_tests.sh` genera `JWT_SECRET_KEY` y las tres contraseñas con `secrets.token_urlsafe(18)` **en cada ejecución** |
| No reutilizan producción | no derivan de ningún valor de producción ni existen fuera del proceso |
| No se escriben en Git | viven en variables de entorno del proceso; ningún fichero versionado las contiene |
| No se imprimen | los resúmenes muestran `<oculta>`; este informe no contiene ninguna |

Los correos de las cuentas sembradas usan `@example.com` (RFC 2606). Se intentó primero
`.invalid` y `.test`, pero `EmailStr` de Pydantic rechaza los TLD reservados — comprobado
empíricamente.

---

## 8. Aislamiento respecto de terceros

Durante el aprovisionamiento se detectó en la máquina **otra instancia de PostgreSQL (18)
perteneciente a un proyecto distinto** (`-home-maria-Proyectos-kontrol`), corriendo desde
su propio directorio temporal. **No se tocó, no se conectó, no se detuvo ni se inspeccionó
su contenido.** Se deja constancia únicamente porque un `ps` lo muestra y su existencia
podría confundir a quien reproduzca este trabajo.

---

## 9. Estado de producción

**Intacta.** Durante toda la Wave 1 y la Wave 1.5:

- ninguna conexión abierta contra `64.225.104.69/avicolav2`;
- cada intento deliberado de apuntar ahí fue bloqueado por la guarda **antes** de conectar;
- ninguna migración, siembra ni escritura ejecutada fuera de `global_avicola_test`.

---

## 10. Estado final

`AC03` y `AC05`, que quedaron en `BLOCKED_EXTERNAL` en Wave 1, están **verificados**. El
bloqueo por privilegios se resolvió **sin bypass**: no se obtuvo root, no se modificó la
configuración del sistema y no se usó el servidor de producción.

**`GA-REM-014` → `CERTIFIED`.**
