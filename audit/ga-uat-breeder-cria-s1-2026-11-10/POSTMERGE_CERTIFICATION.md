# Certificación post-merge · Breeder Cría S1 (UAT)

- **Mandato:** `GA-UAT-BREEDER-CRIA-S1-POSTMERGE-UAT`
- **HEAD certificado:** `23d6e39` == `origin/main`
- **Estado de entrada:** `TECHNICALLY_CERTIFIED_WITH_NON_BLOCKING_OBSERVATIONS`
- **`OWNER_UAT_READY`:** `NO` (ver §3)
- **`OWNER_ACCEPTED`:** `NO`
- **Evidencia:** `audit/ga-uat-breeder-cria-s1-2026-11-10/evidence/`

## 1. Qué introdujo el PR #1

Base: commit `01c42a2` + merge `457d807`. Alcance estrictamente de arranque/despliegue:

| Archivo | Cambio |
|---|---|
| `backend/scripts/bootstrap_first_superuser.py` | alta idempotente del primer superusuario |
| `bootstrap-first-superuser.sh` | envoltura de ejecución |
| `Dockerfile` | añade `COPY scripts/ scripts/` |
| `backend/tests/test_first_superuser_bootstrap.py` | 9 tests del script |
| `docker-compose.develop.yml` | entorno de desarrollo; selecciona las imágenes `:develop` |
| `create-pr.sh` | utilidad de PR |
| spec GA-REM-043 | requisito del bootstrap |

**No toca producto.** No modifica rutas ni código de la aplicación y el arranque no cambia: `grep -rn 'bootstrap' backend/app` no devuelve coincidencias (el script vive en `backend/scripts/` y se invoca a mano). Verificado además:

- **Regresión de autoridad P19-4:** `is_super_admin` es `true` solo en `test_admin`; `false` en operador, aprobador y usuario nuevo.
- Operador sobre `/roles` → **403**.
- El `openapi` no expone ningún endpoint con `bootstrap`.

## 2. Certificación del HEAD final (`23d6e39`)

| Ámbito | Resultado | Log |
|---|---|---|
| Backend completo | **1888 passed · 0 failed · 52 skipped** (+9 tests del PR #1) | `60_postmerge_backend_full.log` |
| Frontend `vitest` | 121 archivos · **703 passed** | `61_postmerge_frontend_vitest.log` |
| `tsc -b` | rc 0 | `62_postmerge_tsc.log` |
| `vite build` | rc 0 · bundle `index-C14hqVc0.js` | `63_postmerge_build.log` |
| E2E P18A–P18D | verdes | `evidence/` |
| E2E P19A–P19C | verdes | `evidence/` |
| E2E completa en serie (`--workers=1`) | **199 passed · 0 failed · 0 skipped** | `65_postmerge_e2e_full_serial.log` |

`POST_MERGE_BACKEND = PASS` · `POST_MERGE_FRONTEND = PASS` · `POST_MERGE_TSC = PASS` · `POST_MERGE_BUILD = PASS` · `POST_MERGE_P18 = PASS` · `POST_MERGE_FULL_E2E = PASS`

## 3. Paridad de despliegue = **FAIL**

El runtime de UAT `https://avicola.globaldv.net` sirve el frontend `assets/index-D-PzEPNO.js` con `Last-Modified: Tue, 17 Nov 2026 23:02:26 GMT`. Ese bundle **no contiene ninguno** de los marcadores de esta entrega:

`lots-no-units` · `toast-container` · `pending-classification` · `reject-reason` · `lot-filter-hint` · `operation-filter-lot-code`

El bundle local del HEAD (`index-C14hqVc0.js`) **sí** los contiene todos.

Causa: `docker-compose.develop.yml` (introducido por el PR #1) selecciona las imágenes `:develop`. Los workflows de GitHub muestran:

- `Docker Push — Frontend (dev)` publicó el **2026-11-17 23:03Z** desde la rama `develop` (`7ff5451`).
- El push de `main` (`23d6e39`, **2026-11-18 05:48Z**) publica `:latest` — workflows Backend/Frontend de `main` completados con éxito — y **no** el tag `:develop`.
- La rama `develop` (`7610ece`) **no contiene** la SPEC 015.

**Conclusión:** el servidor de UAT ejecuta la imagen `develop` anterior; hasta actualizar `develop` (o apuntar el servidor a `:latest`) el UAT manual **no probaría este código**.

No se actualizó `develop` ni se tocó el servidor: la acción de despliegue queda reservada a la **Owner**.

No se dispone de las credenciales de `qa.admin` / `qa.pruebas.unidades` y **no se imprimió ningún secreto**; el UAT focalizado se ejecutó en el entorno aislado E2E con usuarios equivalentes.

## 4. UAT focalizado (entorno aislado, HEAD final)

| Caso | Resultado | Evidencia |
|---|---|---|
| UAT-01 · BU | **PASS** | P18C: pestañas solo de las unidades concedidas; URL directa sin datos; API 404/IDOR; sin unidades → aviso |
| UAT-02 · corrección 2.0 → 2.5 | **PASS** | P18A: original 2.0, corregido 2.5 con motivo; auditoría `corrected`/`review_started`/`updated`/`created`; persiste tras aprobar; historial sin nombre crudo |
| UAT-03 · inspección | **PASS** | P18A: B1 derivada y visible; B2 multicadena → pendiente visible en bandeja con nombres |

| UAT-04 · reportes | **PASS** | P18D: pantalla, PDF y Excel descargados; «Volver» al detalle; Producción y Mortalidad abren `/reports` sin error |
| UAT-05 · obligatorios | **PASS** | P19-1: pesaje, vacunación, medicación y alimento vacíos → 0 POST + mensaje; con dato mínimo 201; salida sin transporte 201 |
| UAT-05 · agua | **PASS** → `WATER_UAT=PASS` | P19-2: vacío y 0 bloqueados sin POST; 120.5 → 201; aparece en Historial filtrando por código; detalle con código y litros; sin texto crudo ni 422 crudos |

`WATER_UAT=PASS` cierra **`S1-WATER`** (el `UAT_EVIDENCE_INSUFFICIENT` del ciclo anterior).

- **O-2:** ningún recorrido mostró un `422` crudo.
- **`CORRECTABLE_FIELDS_SECURITY=PASS`** (P19-3): sin token 401; usuario sin `corrections:read` 403; autorizado 200; evento de otra unidad 404; inexistente 404; admin de otra empresa 404; misma empresa 200.

## 5. O-8 investigada

La hipótesis de saldo/cutover **no aplica**. El fallo es `P-17-G · operator` con `/cutover`:

1. Tras `P-16`, `habilitarCutoverEnRoles` (`test-support/cutover.ts`) añade `cutover:*` a **todos** los roles y no los restaura.
2. `test_operator` es `view_type='mobile'`.
3. `/cutover` está bajo `WebOnlyRoute`: la UI redirige al menú a un perfil móvil, mientras la API autoriza por permiso → **API 200 y UI redirigida** = falsa inconsistencia **del test**.

Reproducido en el baseline `7ff5451` (`24_e2e_baseline_p16_p17d_pair.log`) y en el árbol actual (`23_e2e_p16_p17d_pair.log`).

**Clasificación:** defecto de TEST/FIXTURE (**P3**), sin impacto en operación, saldo ni integridad (no toca balances). El producto es correcto por diseño: un perfil móvil no tiene pantallas solo-web.

**Corregido:** P-17-G ahora conoce el perfil (`/me.view_type`) y marca `/cutover` como `soloWeb`; pasa tras P-16 y la suite completa en serie queda verde.

**Disposición:** O-8 **CERRADA** (fix de test). El saldo se valida por TOTAL (**D4**) y las pruebas de saldo (P18B parte 3 y `test_uat_s1_inspection_trace` D4) siguen verdes.

## 6. O-3 — reclasificada como `FUNCTIONAL GAP`

Respuestas verificadas (P19-5a / P19C):

- **O3-A: SÍ.** Una inspección de granja sin lote nace **pendiente** cuando la granja no tiene lotes, cuando tiene lotes de cadenas distintas o cuando la cadena no es efectiva para el actor.
- **O3-B: SÍ.** `/operations/pending-classification` (enlace desde Historial) la lista con nombres de granja y galpón.
- **O3-C: PARCIAL.** Un texto general explica por qué (cadena no inequívoca), pero **no** dice qué granja ni qué lotes causan la ambigüedad.

- **O3-D: NO.** La pantalla no tiene ningún control para clasificar (0 acciones; evidencia `e2e_p19c`).
- **O3-E: NO, ni siquiera por API.** `POST /operations/{id}/classify` existe (permiso `masters:update`) pero exige `company_business_unit_id`, un id interno que **ninguna API expone**: `GET /business-units` devuelve solo `code, name_key, is_enabled` (la omisión del id en `HabilitacionRead` es deliberada, por seguridad). Un cliente real no puede resolver un pendiente sin acceso a la base.

**Nota de corrección:** el cierre del ciclo anterior describía O-3 como «solo por API»; es impreciso: **tampoco es utilizable por API** sin conocer ese id.

**Clasificación:** `FUNCTIONAL GAP` · `OWNER_DECISION_REQUIRED`.

**Recomendación:** si un pendiente puede producirse legítimamente en operación, debe poder resolverse desde la UI: pantalla de pendientes con selector de unidad **por CÓDIGO** (el servidor resuelve la habilitación de la empresa), motivo obligatorio, permiso `masters:update` (o `operations:classify` nuevo), auditoría en el rastro P-09 y bloqueo de reclasificación según GA-REM-040 §11.6. No se implementa en este ciclo porque requiere definir el workflow.

## 7. O-9

`.github/workflows` solo contiene los `docker-push-*` (no ejecutan E2E), por lo que el **CI oficial no se ve afectado**. La inestabilidad con 2 workers es deuda del arnés local: ejecutar con `--workers=1`.

## 8. Observaciones individuales

- **O-1 (P3):** el detalle de evento no publica `id` por fila de submovimiento. No bloquea (las correcciones usan `row_id` de `correctable-fields`). Backlog: publicar `id` en el detalle (aditivo).
- **O-2 (P3):** los `422` de pydantic salen en inglés desde la API. No bloquea: la UI los traduce y ningún recorrido UAT los expone. Backlog: manejador global de validación en español.
- **O-3:** ver §6.

- **O-4 (P2):** las correcciones de campos de catálogo (causa, vacuna, medicamento, proveedor…) se hacen por código numérico, sin selector. No bloquea (corregir peso/cantidad/fecha/observaciones funciona); requiere decisión de UX. Backlog.
- **O-5 (test):** `test_approver` sembrado no tiene `review:read`; dato de pruebas, no de producto.
- **O-6 (P3):** `POST /operations` sobre un lote de otra unidad responde 400 «Lote no encontrado» (anti-enumeración, comportamiento previo a esta spec). No bloquea.
- **O-7:** CERRADA por `WATER_UAT=PASS`.

## 9. Estado

- `POST_MERGE_CODE = CERTIFIED`
- `FINAL_HEAD_TECHNICALLY_CERTIFIED = NO` — bloqueado por la **paridad de despliegue** (§3) y por la decisión Owner de **O-3** (§6)
- `OWNER_UAT_READY = NO` hasta actualizar el servidor
- `OWNER_ACCEPTED = NO`

## 10. Adenda — despliegue ejecutado tras la decisión de la Owner

Decisión Owner (2026-11-18): avanzar `develop` a `main`. `develop` (7610ece, commit de Andres «fix» que cambia solo `backend/scripts/bootstrap_first_superuser.py` y `create-pr.sh`) no era ancestro de `main`, así que no era posible un fast-forward: se hizo un merge no-ff de `main` (043324b) sobre el tip de `develop` y se pusheó a `develop` (7610ece..ebc4350); el árbol resultante solo difiere de `main` en esos dos scripts (código de aplicación idéntico). Los workflows `Docker Push — Backend (dev)` y `Frontend (dev)` para ebc4350 terminaron con éxito (2026-11-18 14:20Z).

Verificación del runtime tras el despliegue (sin credenciales; solo lecturas públicas): el index de https://avicola.globaldv.net pasó de `assets/index-D-PzEPNO.js` (Last-Modified 2026-11-17 23:02Z) a `assets/index-BT7-4mmE.js` (Last-Modified 2026-11-18 05:47:20Z, coincidente con la imagen construida desde `main` 23d6e39 entre 05:46Z y 05:48Z); el bundle nuevo CONTIENE los marcadores de esta entrega (`lots-no-units`, `toast-container`, `pending-classification`, `reject-reason`, `lot-filter-hint`, `operation-filter-lot-code`, `correctable-fields`, «Valor no válido en»); en la API, `GET /api/v1/corrections/events/1/correctable-fields` y `GET /api/v1/operations/pending-classification` responden 401 (la ruta existe) frente al 404 de una ruta inexistente. El código de aplicación es idéntico en 23d6e39, 043324b y ebc4350 (`git diff --stat 23d6e39 043324b -- backend/app frontend/src` vacío).

Resultado: `DEPLOYMENT_PARITY = PARTIAL` — la presencia funcional de la entrega en frontend y backend está demostrada por marcadores, pero el SHA exacto desplegado NO es demostrable porque la aplicación no expone un marcador de versión (recomendación: endpoint/etiqueta de build con el SHA). Por el criterio estricto, `FINAL_HEAD_TECHNICALLY_CERTIFIED = NO` hasta demostrar el SHA; `OWNER_UAT_READY = YES` condicionado (el runtime contiene todos los entregables); `OWNER_ACCEPTED = NO`.

Observación nueva **O-10** (ajena a esta spec): en el árbol de `develop` el test `backend/tests/test_first_superuser_bootstrap.py::test_t_043_02_second_run_is_idempotent_and_does_not_rotate_password` falla («El correo reservado del bootstrap ya pertenece a otro usuario; se rehúsa sobrescribirlo»): el commit 7610ece cambió el script sin actualizar su test; ya fallaba en `develop` antes de este merge; el CI oficial no ejecuta tests; se informa a su autor. Decisión Owner O-3 (2026-11-18): resolver desde la UI por código de unidad (spec delta + implementación en un ciclo propio, aún NO implementado).

