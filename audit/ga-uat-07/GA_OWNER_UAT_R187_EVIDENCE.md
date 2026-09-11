# GA-UAT-07 · R-187 — EVIDENCIA DEL UAT DEL PROPIETARIO

Separación explícita: **A-C = prueba de ingeniería (no sustituye la aceptación)** · **D-F = juicio del propietario (PENDIENTE hasta su respuesta)** · **G = limpieza (tras la decisión)**.

## A · Precondiciones técnicas

| Ítem | Estado |
|---|---|
| Baseline | `cb412c3` == remoto · worktree limpio |
| Producto desde certificación | **SIN CAMBIOS** (`git diff f755baa..HEAD -- backend/app frontend/` = vacío) |
| Backend certificado | `f755baa` (RATIFIED_IMPLEMENTED) · Frontend `index-BUthrUt9.js` |
| Runtime | health 200 |
| Smoke | TypeScript **PASS** · build **PASS** · Vitest **280/280** · backend targeted **2 passed** (matemática R-187 + ruteo OD-16) |

## B · Fixture del UAT

| Ítem | Valor |
|---|---|
| Operador | `ra187uat` (rol 71 «R187 UAT», permisos normales de consulta; usuario 141; concesión broiler 201; login verificado 200) |
| Lote primario | **54 · `L-R187-DET`** — 19 d · 1000 aves · viabilidad 95 % · peso 2000 g · FCR 3 → **IPE esperado 333.3 · 🟢 Excelente** |
| Apoyo | 56 · `L-R187-MID` (**282.7 · 🟡 Bueno**) · 55 LOW (**241.1 · 🔴 Regular**) · legado 11 (5.6, contexto) |
| Ventana | BU broiler habilitada temporalmente para el UAT (se restaura a OFF al cierre) |

## C · Reference walkthrough (medición; NO reemplaza la aceptación)

| Medición | Resultado |
|---|---|
| Lot detail | **PASS** |
| IPE card visible | **YES** |
| IPE | **333.3** |
| Clasificación | **🟢 «Excelente»** |
| Valor de escala antigua presente | **NO** |
| HTTP 500 | **0** |
| NaN / Infinity | **0 / 0** |
| Lot Report | **PASS** (mismo 333.3; contexto verificado: «IPE Índice Europeo de Producción 333.3 🟢 Excelente») |
| Detail/report consistency | **MATCH (333.3 == 333.3)** |
| Refresh | **PASS** (333.3) |
| Relogin | **PASS** (333.3) |
| Móvil 390×844 | **PASS** (333.3 · 🟢 · overflow 0) |
| Fatal console (`pageerror`) | **0** (los errores de consola son 403 de widgets opcionales sin permiso del operador mínimo; fail-silent) |
| Banda media (apoyo) | **282.7 · 🟡 Bueno** |

Raw: `evidence/walkthrough-uat.json` · `evidence/setup-uat.json`.

## D · Casos del propietario

| UAT-01 | UAT-02 | UAT-03 | UAT-04 | UAT-05 | UAT-06 |
|---|---|---|---|---|---|
| **PENDIENTE** | **PENDIENTE** | **PENDIENTE** | **PENDIENTE** | **PENDIENTE** | **PENDIENTE** |

## E · Observaciones del propietario

**PENDIENTE** — ver `GA_OWNER_UAT_R187_OBSERVATIONS.md` (incluye notas técnicas pre-registradas N-1…N-3, no bloqueantes).

## F · Decisión del propietario

**PENDIENTE** — opciones válidas: A) ACEPTO R-187 · B) ACEPTO R-187 CON OBSERVACIONES · C) RECHAZO R-187 — CORREGIR.
*(No se registra aceptación ficticia; este campo se completa solo con la respuesta explícita.)*

## G · Limpieza (tras la decisión)

Plan: revocar concesión · baja lógica del operador (141) · desactivar rol (71) · restaurar **BU broiler OFF (4×OFF)** · destruir credenciales `~/ga_uat07_credentials.txt` y temporales · preservar todo `audit/`, evidencia R-187, decisión OD-22, R-184/R-186 y aceptaciones previas · ningún usuario humano modificado.
**Estado: PENDIENTE hasta la decisión.**
