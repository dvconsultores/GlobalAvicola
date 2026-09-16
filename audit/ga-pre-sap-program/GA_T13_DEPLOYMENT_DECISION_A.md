# GA · PRE-SAP — T13 · DECISIÓN DE DESPLIEGUE A (registro del propietario)

Fecha de registro: 2026-09-16 · Autoridad: **decisión explícita del propietario**
(canal chat, 2026-09-16) · Este documento **no modifica producto**.

## 1 · Decisión recibida

El propietario formalizó:

```
DEPLOYMENT = A
```

— se autoriza **desplegar manualmente el producto certificado** en el entorno
compartido de UAT (`https://avicola.globaldv.net`), con clasificación
**`SHARED DEVELOPMENT / TEST / CERTIFICATION / UAT`** (NO es producción real; no
usar terminología de producción comercial). Objetivo: que la UAT del propietario
se ejecute contra **exactamente el producto certificado**. El texto íntegro de la
decisión se conserva como evidencia en el Anexo.

## 2 · Campos registrados

| Campo | Valor |
|---|---|
| `T13_DEPLOYMENT_DECISION` | `A` |
| `OWNER_DECISION` | `MANUAL_CERTIFIED_BUILD_DEPLOYMENT` |
| `TARGET_ENVIRONMENT` | `SHARED_UAT_TEST_CERTIFICATION` |
| `PRODUCT_SHA` | `be5453f` |
| `GITHUB_ACTIONS` | `RETIRED` (no reactivar) |
| `AUTO_DEPLOY` | `NOT_AVAILABLE` |
| `DEPLOYMENT_METHOD` | `MANUAL_AUTHORIZED` |

AOD-29 queda **sin modificar**; GitHub Actions **no** se reactiva (mandato §2).

## 3 · Verificación del SHA de producto (preflight §1)

Registrado antes de actuar (estación del agente):

- `git rev-parse HEAD` = `93b4a91` · `git status --short` = limpio ·
  `git ls-remote origin refs/heads/main` = `93b4a91` ⇒ **REMOTE_SHA_MATCH = PASS**.
- **`be5453f` es la última revisión con contenido de producto**: `git diff
  --stat be5453f..HEAD -- backend frontend e2e` = **vacío**; el único commit
  posterior (`93b4a91`) es documental. ⇒ No existe un SHA de producto certificado
  posterior; no se sustituye el SHA.

`TARGET_ALEMBIC_HEAD` (checkout, verificado 2026-09-16): `c8d9e0f1a2b3` — cabeza
única (`alembic heads` ⇒ una sola).

## 4 · Precheck de acceso al host (§3) y ejecución

- La estación del agente **no es el host**: `docker` / `docker-compose` =
  `NOT_FOUND`; `avicola.globaldv.net` resuelve a `84.247.161.106` (externo).
- **No existe** acceso autorizado del agente al host (ni SSH, ni checkout, ni
  permisos Docker, ni mecanismo de respaldo/configuración disponibles en el host).
- No se buscaron credenciales en ninguna fuente (HOME, historial, /proc, browser
  stores, filesystem general, gestores no autorizados): **prohibición respetada**;
  tampoco se imprimieron secretos.

⇒ **`DEPLOYMENT_EXECUTION = BLOCKED_EXTERNAL_ACCESS`**

La ejecución queda en manos del administrador del host conforme al instrumento
entregado (ver §6). La decisión del propietario sigue siendo **A** — no se
cambia a B (mandato §20).

## 5 · Baseline pre-deploy (externo, sin acceso a host)

Capturado 2026-09-16T02:56:55Z (evidencia cruda:
`evidence/t13-ops/deploy-a-preflight-baseline.log`):

| Elemento | Valor observado |
|---|---|
| `GET /` | 200 · `Server: openresty` · `Last-Modified: Mon, 14 Sep 2026 12:47:04 GMT` |
| Bundle servido | `/assets/index-apu3WWcr.js` |
| `GET /login` | 200 |
| `GET /health` (externo) | 200 pero devuelve el index del SPA (fallback del frontend); la salud real del backend es **interna** (`:8002/health`, según healthcheck del compose) |
| `/api/health`, `/api/v1/health` | 404 (no expuestos) |

Nota: el build actualmente servido (14-sep) **es anterior** al producto
certificado (Wave C, 16-sep) ⇒ la UAT no debe ejecutarse contra él (mandato §20:
"No continuar U1/U2 contra el build viejo").

## 6 · Instrumento entregado

`GA_T13_DEPLOYMENT_A_ADMIN_RUNBOOK.md` — **runbook para el administrador del
host** con: SHA exacto, precondiciones, captura pre-deploy, respaldo obligatorio
(STOP si falla), build + publicación (ruta canónica EX-01, réplica del CI
retirado; fallback local), migración por el **entrypoint** canónico
(GA-REM-024), startup, health A–G, verificación de producto desplegado
(marcadores GA-FE-01), rollback, G-02…G-05 (con la corrección calibrada de la
ruta de login) y la plantilla de **evidencia que debe devolver**.

Al volver la evidencia: verificación por ingeniería ⇒ prevalidación técnica
U1/U2 ⇒ **sesión del propietario**. Hasta entonces, U1/U2 permanecen
`READY_FOR_OWNER` y **no** se marca ninguna aceptación.

## 7 · Estado de U1/U2

- Fichas entregadas (`GA_T13_UAT_FICHAS_U1_U2.md`); **no ejecutadas**; **no**
  marcadas como PASS (mandato §17).
- La sesión del propietario se abrirá solo tras: `DEPLOYMENT_STATUS = PASS` +
  OPS G-02…G-05 + prevalidación técnica en verde (mandato §13–§16, §18).

## 8 · Addendum (2026-09-16, tarde) — ejecución, evidencia y reconciliación de gobernanza

- **Ejecución**: el commit `f38350a` (cuenta del propietario) restauró los 2 workflows
  de despliegue; el push disparó sus runs (**35122083759** BE / **35122083928** FE,
  `push`, `success`, 16:28:08Z) y publicó las imágenes en Docker Hub (`sha-f38350a` +
  `latest`; BE `16:28:34Z` digest `sha256:6f0edbfa…`; FE `16:28:52Z` digest
  `sha256:29cd2eff…`), que Watchtower desplegó. **GitHub Actions SÍ quedó reactivado**
  (2 workflows, estado `active`) — sin texto formal de decisión del propietario ⇒
  **`GOVERNANCE_DRIFT = TRUE`** y decisión A/B requerida (ver
  `GA_T13_GHA_AOD29_RECONCILIATION.md`). Los campos §2 `GITHUB_ACTIONS=RETIRED` /
  `AUTO_DEPLOY=NOT_AVAILABLE` quedan contradichos por los hechos; su reconciliación es
  la decisión pendiente. El agente no modificó workflows ni historia.
- **Verificación externa**: bundle `index-apu3WWcr.js` (14-sep) → **`index-r36pBbNX.js`**
  (Last-Modified 16:28:48Z; sha256 `3047f5c…`); marcadores M1–M7 + control +
  `cutover-templates`; root/login 200; backend sirviendo.
  Estados separados (mandato §3): `RUNTIME_EXTERNAL_VERIFICATION = PASS` ·
  `HOST_DEPLOYMENT_EVIDENCE = PENDING` · `DEPLOYMENT_GATE = PENDING` (no se cierra sin
  evidencia de host + G-02…G-05; rubric KIT §3 + runbook §8/§12).
- **G-03 (rate limit) runtime**: 12×401 **sin 429** ⇒ **FAIL observado**; diagnóstico
  host pendiente (flag efectivo, umbral, clave del proxy) — adenda §14 del runbook.
- **U1/U2**: `PREPARED — EN HOLD` (no ejecutables aún; mandato §8). Sin aceptaciones.
- Evidencia: `evidence/t13-ops/deploy-a-runtime-verification.log` + reconciliación.

---

## Anexo · Texto íntegro de la decisión del propietario (2026-09-16, canal chat)

```text
GLOBAL AVÍCOLA — T13 OWNER DECISION
DEPLOYMENT = A
DESPLIEGUE MANUAL DEL BUILD CERTIFICADO + PREPARACIÓN U1/U2

============================================================
0. DECISIÓN EXPLÍCITA DEL OWNER
============================================================

Formalizo como Owner:

    DEPLOYMENT = A

Se autoriza desplegar manualmente el producto certificado en el entorno
compartido de UAT / desarrollo-pruebas-certificación:

    https://avicola.globaldv.net

IMPORTANTE:

Este entorno NO es producción real.

No utilizar terminología que lo presente como producción comercial.

Clasificación:

    SHARED DEVELOPMENT / TEST / CERTIFICATION / UAT

El objetivo es que Owner UAT se ejecute contra exactamente el producto
certificado.

============================================================
1. SHA DE PRODUCTO A DESPLEGAR
============================================================

Producto certificado:

    PRODUCT_CERTIFIED_SHA = be5453f

El HEAD documental posterior:

    93b4a91

no introduce cambios de producto.

Para evidencia inequívoca de runtime, desplegar:

    be5453f

salvo que el repositorio demuestre que existe un SHA de producto certificado
posterior.

NO sustituir el SHA sin evidencia.

Antes de actuar registrar:

    git rev-parse HEAD
    git status --short
    git log -10 --oneline
    git ls-remote origin refs/heads/main

============================================================
2. FORMALIZAR OWNER DECISION
============================================================

Registrar documentalmente:

    T13_DEPLOYMENT_DECISION = A

    OWNER_DECISION = MANUAL_CERTIFIED_BUILD_DEPLOYMENT

    TARGET_ENVIRONMENT =
    SHARED_UAT_TEST_CERTIFICATION

    PRODUCT_SHA = be5453f

    GITHUB_ACTIONS = RETIRED

    AUTO_DEPLOY = NOT_AVAILABLE

    DEPLOYMENT_METHOD = MANUAL_AUTHORIZED

Conservar la evidencia de que la opción A fue escogida explícitamente por el
Owner.

No modificar AOD-29.

No reactivar GitHub Actions.

============================================================
3. PRECHECK DEL HOST
============================================================

Antes de desplegar comprobar si realmente tienes acceso AUTORIZADO al host.

Si el entorno actual ya contiene:

- acceso SSH/equivalente autorizado;
- acceso al checkout;
- permisos Docker;
- acceso al mecanismo de backup;
- configuración necesaria ya disponible en el host;

puedes ejecutar el despliegue.

PROHIBIDO buscar credenciales en:

- HOME;
- shell history;
- /proc;
- browser stores;
- archivos ajenos al proyecto;
- filesystem general;
- gestores de secretos no autorizados.

PROHIBIDO imprimir:

- passwords;
- private keys;
- tokens;
- DB passwords;
- contenido completo de .env.

Si NO existe acceso autorizado:

    DEPLOYMENT_STATUS = BLOCKED_EXTERNAL_ACCESS

y NO inventes credenciales.

En ese caso:

- prepara los comandos exactos para el administrador del host;
- identifica qué evidencia debe devolverte;
- STOP en ese gate.

============================================================
4. ANTES DEL DESPLIEGUE
============================================================

Si existe acceso autorizado, capturar primero el estado PRE-DEPLOY.

Registrar:

    DEPLOY_START_TIME

    CURRENT_RUNTIME_VERSION / SHA si existe

    CURRENT_FRONTEND_BUNDLE_HASH

    CURRENT_HEALTH_STATUS

    CURRENT_CONTAINER_STATUS

    CURRENT_ALEMBIC_HEAD

    TARGET_PRODUCT_SHA = be5453f

No asumir que el runtime conoce su SHA.

Si no existe endpoint/version metadata, registrar como mínimo:

- hash/nombre del bundle servido;
- timestamps;
- estado de contenedores;
- commit del checkout del host.

============================================================
5. BACKUP OBLIGATORIO ANTES DE MIGRACIONES
============================================================

Antes de ejecutar cualquier migración sobre la base de datos del entorno UAT:

realizar un backup mediante el procedimiento canónico existente.

No inventar un sistema nuevo de backup.

Registrar:

    BACKUP_STATUS
    BACKUP_TIMESTAMP
    BACKUP_REFERENCE
    BACKUP_SIZE si está disponible

No imprimir contenido sensible.

Si no existe procedimiento autorizado de backup o éste falla:

    STOP

    DEPLOYMENT_STATUS =
    BLOCKED_BACKUP_SAFETY

No ejecutar migraciones sin backup verificable.

============================================================
6. VALIDAR MIGRACIONES
============================================================

En el repositorio certificado verificar:

    alembic heads

Debe existir un único head canónico.

Comparar con el estado del entorno.

No hardcodear ciegamente un head histórico si el repositorio demuestra otro.

Registrar:

    PRE_DEPLOY_DB_REVISION
    TARGET_ALEMBIC_HEAD

Si aparecen múltiples heads inesperados:

    STOP

No improvisar merge migrations durante el deploy.

============================================================
7. DESPLIEGUE
============================================================

Seguir primero el runbook/cadena canónica existente del repositorio.

No inventar un mecanismo nuevo.

Conceptualmente:

    fetch repository
    ↓
    checkout PRODUCT_CERTIFIED_SHA
    ↓
    build backend/frontend
    ↓
    run migrations by canonical mechanism
    ↓
    recreate/start application containers
    ↓
    health verification

Si el deployment actual usa docker compose, aplicar el mecanismo exacto
documentado por el proyecto.

NO levantar/recrear/destruir la base de datos innecesariamente.

NO ejecutar:

    docker compose down -v

NO eliminar volúmenes.

NO resetear datos.

NO limpiar la BD.

La base existente debe preservarse.

============================================================
8. MIGRACIONES
============================================================

Ejecutar:

    alembic upgrade head

solo mediante el entorno/mecanismo canónico del backend.

Registrar:

    ALEMBIC_BEFORE
    ALEMBIC_AFTER
    EXIT_CODE

Requisito:

    ALEMBIC_AFTER == TARGET_HEAD

Si la migración falla:

- detener;
- no continuar UAT;
- registrar error;
- evaluar rollback conforme runbook.

No editar la BD manualmente para “hacer pasar” la migración.

============================================================
9. HEALTH CHECK POST-DEPLOY
============================================================

Después del despliegue verificar como mínimo:

A. contenedores/servicios activos;

B. backend health endpoint;

C. frontend responde;

D. no hay error crítico de startup;

E. frontend bundle cambió respecto al build anterior cuando corresponda;

F. DB está en Alembic head;

G. login page accesible.

Registrar:

    DEPLOY_END_TIME

    DEPLOYED_PRODUCT_SHA

    BACKEND_HEALTH

    FRONTEND_STATUS

    FRONTEND_BUNDLE_HASH

    ALEMBIC_HEAD

    CONTAINER_STATUS

Resultado esperado:

    DEPLOYMENT_STATUS = PASS

============================================================
10. VERIFICAR PRODUCTO REAL DESPLEGADO
============================================================

No basta con que:

    docker compose up

termine correctamente.

Debe existir evidencia razonable de que el runtime corresponde al producto
certificado.

Idealmente:

    runtime/product version = be5453f

Si actualmente no existe mecanismo de versionado runtime:

usar evidencia combinada:

- checkout SHA;
- build ejecutado desde ese checkout;
- bundle hash nuevo;
- timestamps;
- health;
- container recreation.

No agregar ahora una feature de versionado únicamente para este gate salvo que
ya esté especificada.

============================================================
11. ROLLBACK
============================================================

Antes del despliegue registrar el estado anterior suficiente para reversión.

Si aparece un fallo crítico post-deploy:

NO improvisar.

Aplicar rollback conforme runbook.

Conceptualmente:

    previous product SHA/build
    +
    DB backup cuando sea necesario

No ejecutar downgrade de Alembic automáticamente salvo que el procedimiento
canónico lo establezca y sea seguro.

Registrar cualquier rollback.

============================================================
12. OPS G-02…G-05
============================================================

Después de un deployment exitoso:

ejecutar autónomamente los gates técnicos del runbook T13:

    G-02
    G-03
    G-04
    G-05

siempre que:

- no requieran una nueva decisión del Owner;
- las precondiciones estén disponibles.

Usar EXACTAMENTE el runbook canónico.

Para cada uno registrar:

    GATE
    COMMAND/PROCEDURE
    RESULT
    EXIT_CODE
    EVIDENCE
    OBSERVATIONS

No marcar PASS por inspección parcial.

============================================================
13. PREVALIDAR U1
============================================================

Después del deploy y antes de involucrar al Owner:

verificar técnicamente que U1 está listo.

Comprobar:

- login responde;
- usuario admin existe;
- tenant/company disponible;
- roles/permisos disponibles;
- URLs necesarias funcionan;
- no existe error de fixture/precondición.

NO ejecutar la aceptación humana.

NO marcar U1 PASS.

============================================================
14. PREVALIDAR U2
============================================================

Verificar técnicamente:

- Progenitoras habilitada;
- OC requerida disponible;
- operador disponible;
- aprobador disponible;
- permisos correctos;
- importación disponible;
- flujo de aprobación disponible;
- recepción disponible.

NO imprimir las credenciales.

No leer credenciales fuera del mecanismo autorizado ya existente.

NO marcar U2 PASS.

============================================================
15. U1 — OWNER UAT
============================================================

Después del deployment PASS y prevalidación:

presentar al Owner la ficha U1 ya definida:

P-13 / plataforma / usuarios / tenancy.

El Owner debe ejecutar personalmente:

- login;
- logout;
- atrás + navegación interna;
- relogin;
- cambio de empresa si aplica;
- Usuarios;
- Roles;
- observación de sesión.

No sustituir esta ejecución mediante Playwright.

============================================================
16. U2 — OWNER UAT
============================================================

Presentar la ficha U2 ya definida:

P-01 Progenitoras / OD-25 / R-153 / R-189.

Debe incluir nuevamente:

C1:
guardar importación sin lote
+ nota visible.

C2:
antes de aprobar:
“Se creará al aprobar”
+ no existe lote.

C3:
aprobación crea lote
+ #N
+ enlace navegable.

Además:

- lote nace sin aves;
- mortalidad antes de recepción es rechazada;
- recepción 40♂ + 60♀;
- población final = 100;
- vía manual de Nuevo lote continúa disponible.

============================================================
17. NO MARCAR UAT
============================================================

Aunque toda la prevalidación técnica sea verde:

NO declarar:

    U1 = PASS

NO declarar:

    U2 = PASS

NO declarar:

    OWNER_ACCEPTED

Eso solo lo decide el Owner después de realizar las sesiones.

============================================================
18. PRÓXIMO STOP
============================================================

Si DEPLOYMENT A se ejecuta correctamente:

detenerte únicamente cuando tengas:

    DEPLOYMENT = A
    DEPLOYMENT_STATUS = PASS
    OPS_STATUS = <resultado>
    U1 = READY_FOR_OWNER
    U2 = READY_FOR_OWNER

Presentar al Owner:

1. evidencia resumida del deployment;
2. evidencia de que el SHA certificado está desplegado;
3. resultado G-02…G-05;
4. ficha U1;
5. ficha U2;
6. formato exacto de respuesta.

============================================================
19. FORMATO QUE DEBE RESPONDER EL OWNER
============================================================

DEPLOYMENT = A

U1 = PASS | PASS WITH OBSERVATIONS | FAIL
Observación: ...

U2 = PASS | PASS WITH OBSERVATIONS | FAIL
C1: PASS | FAIL
C2: PASS | FAIL
C3: PASS | FAIL
Observación: ...

============================================================
20. SI NO TIENES ACCESO AL HOST
============================================================

Si no puedes ejecutar DEPLOYMENT A porque no tienes acceso autorizado:

NO cambies la decisión a B.

La decisión del Owner sigue siendo:

    DEPLOYMENT = A

Debes responder:

    DEPLOYMENT_DECISION = A
    DEPLOYMENT_EXECUTION = BLOCKED_EXTERNAL_ACCESS

y producir un RUNBOOK PARA EL ADMINISTRADOR DEL HOST con:

- SHA exacto;
- comandos exactos;
- backup;
- build;
- migration;
- startup;
- health;
- bundle verification;
- rollback;
- evidencia que debe devolver.

Luego STOP.

No continuar U1/U2 contra el build viejo.

============================================================
21. GIT / EVIDENCIA
============================================================

Si únicamente se agregan documentos/evidencias:

stage explícito.

No:

    git add .
    git add -A
    force push
    reset
    history rewrite

Commit/push cuando corresponda.

Verificar:

    LOCAL_SHA == REMOTE_SHA

No reactivar GitHub Actions.

============================================================
22. PRINCIPIO FINAL
============================================================

DECISIÓN OWNER:

    DEPLOYMENT = A

Objetivo:

    UAT debe ejecutarse contra el producto certificado real.

No aceptar como sustituto el build anterior del 13-sep.

No inventar credenciales.

No desplegar destruyendo datos.

No ejecutar UAT por el Owner.

No marcar aceptación humana.

Ejecuta ahora todo lo técnicamente posible para DEPLOYMENT A.

Si tienes acceso autorizado:
    despliega → verifica → OPS → prepara U1/U2 → STOP OWNER UAT.

Si no tienes acceso:
    formaliza decisión A → genera runbook exacto → STOP por acceso externo.
```
