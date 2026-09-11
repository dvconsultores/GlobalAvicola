# GA-UAT-08 · R-188 / BU-D10 / OD-23 — EVIDENCIA DEL UAT

Separación explícita: **A-C = prueba de ingeniería (no sustituye la aceptación)** · **D-F = juicio del propietario (PENDIENTE)** · **G = limpieza (tras la decisión)**.

## A · Precondiciones técnicas

| Ítem | Estado |
|---|---|
| Baseline | `7762e4e` == remoto · worktree limpio · producto sin cambios de comportamiento desde la generación certificada `399751c` (único diff posterior: docstring C3b ya incluido en la certificación) |
| Backend certificado | C3 `bee33f5` + C3b `399751c` · Frontend `index-BUthrUt9.js` |
| Runtime | health 200 |
| Smoke | TypeScript **PASS** · build **PASS** · Vitest **280/280** · backend targeted **1 passed** (ruteo OD-16; suite R-188 PG: skip local declarado) |

## B · Actores y estado del UAT

| Ítem | Valor |
|---|---|
| Operador | `uat188op` (usuario 146; rol 92: ver lotes + ver reportes) — concesión fresca inicial 201; `/me` effective=[broiler] |
| Access Administrator | `uat188adm` (usuario 147; rol 93: 4 permisos de administración de acceso) — `/me` **[] / []** (sin acceso productivo propio) |
| Empresa / BU | Empresa 1 · **Engorde (broiler)** — estado inicial del UAT: **ON** (restaurado al cierre) |
| Concesión fresca del regrant | realizada por la **UI real** (Acceso por unidad → Engorde → botón *Conceder*) |

## C · Reference walkthrough (medición; no reemplaza la aceptación)

| Medición | Resultado |
|---|---|
| Inicial BU ON + concesión | IPE **333.3** · nav `/lots` **visible** · sin error · C01 |
| Tras apagar BU (sesión viva) | IPE **ausente** · nav **oculta** · sin error · C02 · móvil C08 (nav 0, overflow 0) |
| Tras re-encender SIN regrant | IPE **sigue ausente** · nav **sigue oculta** · C03 ⇒ **caso central OD-23 PASS** |
| Regrant por UI (Access Admin) | fila «No concedida» → clic *Conceder* → «Concedida» · `/me` effective=[broiler] · C04/C04b |
| Tras regrant (operador, refresh normal) | nav **restaurada** · IPE **333.3** · reporte **333.3** · C05/C06 |
| Móvil con acceso | IPE 333.3 · overflow 0 · sin error · C07 |
| Consola (páginas y errores) | **0** (sin `pageerror` ni errores de consola) |
| Datos ajenos | **0** |

Raw: `evidence/walkthrough-uat.json` · `evidence/setup-uat.json`.

## D · Casos del propietario

| UAT-01 | UAT-02 | UAT-03 | UAT-04 | UAT-05 |
|---|---|---|---|---|
| **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |

## E · Observaciones del propietario

**Sin observaciones** — decisión A (ver `GA_OWNER_UAT_R188_OBSERVATIONS.md`; notas N-1…N-3 informativas).

## F · Decisión del propietario

**A) ACEPTO R-188 / BU-D10 / OD-23** — registrada en `GA_OWNER_ACCEPTANCE_R188_BU_D10_RECORD.md` (fecha 2026-09-11).

## G · Limpieza (ejecutada tras la decisión)

Ejecutada y verificada: concesión del operador revocada (200) · bajas lógicas de usuarios 146/147 (204/204) · roles 92/93 desactivados (200/200) · **BU Engorde OFF — catálogo 4×OFF** · admin operativo (200) · credenciales y temporales destruidos.
Raw: `evidence/cleanup-uat.json`.
