# CERTIFICACIÓN LOCAL — GA-UAT-BREEDER-CRIA-S2-O23-NULL-TO-MASTER

Residual posterior a `GA-UAT-BREEDER-CRIA-S2-OWNER-DECISIONS` (`SESSION2 = CERTIFIED`). Spec: `specs/020-uat-breeder-cria-s2/spec.md` §7 (`NULL_TO_MASTER_CORRECTION`, `AC-O23-01..08`).
Baseline `develop` = `963f536`; `main` = `1587073` (sin tocar). Rama: `develop`. Sin PR, sin cambios en `main`, sin despliegue a producción. No reabre la Sesión 2 ni cambia `OD-S2-01..07`.

## 1. Causa raíz

`CorrectionService.campos_corregibles_de_evento` descartaba todo campo del evento con valor `NULL` salvo `observations` (`SIEMPRE_OFRECIDOS`): la corregibilidad dependía del **valor** y no de la **metadata** del campo. El formulario ya construía el selector a partir de `master` sin mirar el valor, pero nunca recibía el campo. En el servidor, `POST /corrections` no bloqueaba `NULL → id`, aunque tampoco acotaba el maestro al tipo de evento ni exigía maestro activo (`OD-21`).

Hipótesis descartadas: el frontend no condicionaba el selector al valor original; `MAESTROS_CORREGIBLES` ya daba el catálogo por campo, sin depender del valor; la escritura no exigía una FK previa; `_nombre_de_maestro` devuelve `None` para `NULL` sin error.

## 2. Contrato implementado

| Dirección | Resultado |
|---|---|
| A · `NULL → maestro válido` (activo, de la empresa o compartido, campo que aplica al tipo) | ALLOW (201) |
| B · `maestro A → maestro B` | ALLOW (201) |
| C · `maestro → NULL` | según el contrato vigente del campo: proveedor, transporte y destinos admiten vaciarse; vacuna, medicamento y causas, no (`RR-21`, `RR-32`) |
| D · `NULL → maestro` inexistente / de otra empresa | DENY 400 «no encontrado» (`BR-07`, sin nombrar al ajeno) |
| D · `NULL → maestro` inactivo (y también `A → B` inactivo) | DENY 400, `rule = OD-21` |
| `NULL → maestro` en un campo ajeno al tipo de evento | DENY 400 «no aplica a este tipo de evento» |

Metadata (`MAESTROS_POR_TIPO_DE_EVENTO`, extraída del formulario de alta):
- Recepción de aves → proveedor.
- Salida de aves → granja destino, planta destino y transporte.
- Despacho de huevo, recepción de huevo en incubadora e inspección de transporte → transporte.
- Nacimiento → vacuna.
- Despacho de pollitos → granja destino y transporte.
- Importación de progenitoras → proveedor y transporte.
- Mortalidad → causa de mortalidad.
- Descarte → causa de descarte.
- Vacunación → vacuna.
- Medicación → medicamento.

### Matriz de los 8 campos de maestro

| Campo | Catálogo | Tipos de evento | NULL original soportado |
|---|---|---|---|
| `supplier_id` | suppliers | recepción, importación | SÍ |
| `cause_id` | mortality-causes | mortalidad | SÍ |
| `cull_cause_id` | cull-causes | descarte | SÍ |
| `vaccine_id` | vaccines | vacunación, nacimiento | SÍ |
| `medication_id` | medications | medicación | SÍ |
| `destination_farm_id` | farms | salida de aves, despacho de pollitos | SÍ |
| `destination_plant_id` | processing-plants | salida de aves | SÍ |
| `transport_id` | transports | salida de aves, despacho de huevo, recepción de huevo en incubadora, inspección de transporte, despacho de pollitos, importación | SÍ |

La guarda de activo va **después** de la de empresa (`verificar_destino_de_edicion`), para que el maestro ajeno siga siendo «no encontrado» (`AC26`). Las reglas del campo (`RR-21`, `RR-31`, `RR-32`, `BR-07`, vínculo efectivo) se aplican igual que en `A → B`. La arquitectura no cambia: la corrección escribe el valor efectivo y `CorrectionLog` y la auditoría conservan `original_value = NULL` y `corrected_value = id` (`RR-01`). Sin migración.

## 3. UI

- Valor original vacío: «Sin valor» (`corrections.noValue`, es/en). Nunca `null`, `undefined`, `0` ni un campo en blanco.
- Selector de catálogo también con original `NULL`. Solo ofrece registros activos, con etiqueta `código — nombre` (`sap_code`, `code`, `plate`) o, si no hay código, el nombre. Nunca el id solo.
- Historial: «Proveedor: *Sin valor* → "Proveedor ABC"».
- Al guardar se vuelve al detalle, que se recarga.

## 4. Commits

- Implementación: `26522ad`. Incluye:
  - `backend/app/corrections/service.py`
  - `frontend/src/pages/review/{CorrectionForm,ReviewDetail}.tsx`
  - `frontend/src/utils/correctionFields.ts`
  - i18n es/en
  - tests backend, vitest y E2E
  - spec §7
- Certificación: este commit (evidencia, manual de usuario y estado de la spec).

## 5. Pruebas

| Suite | Resultado | Evidencia |
|---|---|---|
| Backend dirigidas `O23-B01..B10`, `B03b`, `B09b`, `S01` (14) + regresión de correcciones | 72 passed | `test_uat_s2_o23_null_to_master.py` |
| Vitest dirigidas `O23-F01..F07` (7) | 7 passed (directorio review: 47/47) | `uatS2o23.nullToMaster.test.tsx` |
| E2E dirigida `proceso-spec020c` (2) | 2 passed: UI completa con aprobación, recarga y re-login; negativos por API (otra empresa, inactivo) | `evidence/e2e_o23_dirigida.log` |
| Backend completa (pre-commit / post-mutación) | **2139 passed, 0 failed, 60 skipped** en ambas | `evidence/backend_full_*.log` |
| Vitest completa | pre-commit **820/820**; post-mutación 818 passed + 1 fallo **intermitente preexistente** (O-28) + 1 skipped condicional (SPEC 016) | `evidence/frontend_vitest_*.log`, `frontend_flaky_baseline_963f536.txt` |
| `tsc -b` / `vite build` | RC 0 / OK (ambas corridas) | `evidence/frontend_tsc_*.log`, `frontend_build_*.log` |
| E2E completa `--workers=1` | **241 passed** (pre-commit y post-mutación) | `evidence/e2e_full_*.log` |
| Mutación (después del commit `26522ad`, restauración con `git restore --source=26522ad`) | **11/11 muertos** (6 backend, 5 frontend) | `evidence/mutation/` |

Seguridad de `correctable-fields`:
- Sin token → 401.
- Sin permiso → 403 (test_t8 de S1, sigue en verde).
- Evento de otra empresa → 404 (fail closed, `O23-S01`).
- Inexistente → 404.
- Otra unidad de negocio: sin cambios, el alcance de `get_event` y `exigir_unidad_operativa` no se tocó (suite BU completa en verde).
- IDOR por payload: un maestro ajeno o inactivo da DENY en el servidor (`O23-B04`, `B03`, E2E-O23-02).

## 6. Observaciones

- **O-28 (nueva, no bloqueante, preexistente):** `gaFe02.userBuPanel` y `uatAdminRbac.userBuPanel` fallan de forma intermitente bajo la carga de la suite completa de vitest (un `getByText` síncrono tras una carga asíncrona). En la línea base `963f536`, sin O-23, fallan 3 de 3 corridas completas. Aislados pasan 3 de 3. O-23 no toca `src/pages/users`. No se relajó ningún test.
- `O-26` y `O-27` siguen como estaban (limitación documentada y requisito de datos de QA). `O-11`, `O-12`, `O-16` y `O-19` quedan fuera de alcance.
- La corrida E2E completa reescribe evidencia versionada de otras specs (capturas y JSON). Se restauró con `git restore` y no forma parte de este cambio.

## 7. Seguridad de la evidencia

Logs saneados (DSN, tokens y contraseñas). Escaneo de secretos de `audit/ga-uat-breeder-cria-s2-o23-2026-11-26/` limpio. Las coincidencias del escaneo en el spec E2E son referencias a `process.env.GA_TEST_*_PASSWORD`, no valores.

## 8. Decisión local

`O-23 = CLOSED` · `SESSION2 = CERTIFIED` · `OWNER_ACCEPTED = NO`. La paridad de runtime de UAT se verifica después del push a `develop`.
