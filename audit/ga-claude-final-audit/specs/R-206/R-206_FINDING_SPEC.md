# R-206 · FINDING + SPEC (COMPACTO) — VACÍOS DEL ASISTENTE: FECHA OPCIONAL `''` ⇒ 400; NUMÉRICOS DE `extra_data` COMO CADENAS; `''` PERSISTIDO

| Campo | Valor |
|---|---|
| **ID** | **R-206** · P2 · **no bloquea** (existe rodeo: rellenar el campo) · Estado `SPEC_READY` |
| **Origen** | B-11/B-26/B-37 + local `GP2-01a` · Registro G-17 · HEAD `c0b4afc` · 2026-09-13 |
| **GA-REM** | a asignar; sin migración/endpoint/permiso · **UAT: sí** (visible en importación) |

## 1 · Contexto y evidencia

- `OperationFormPage.tsx:1782` — «Cuarentena (fecha fin)» es `<input type=date>` **opcional**; en blanco viaja como `''` y `PlanDeImportacion` (`schemas.py:43`) la rechaza ⇒ **400 BR-22 «Input should be a valid date»** (repro local `GP2-01a-contrato-fecha-vacia: quarantine_end_date_enviado: ""`). El recorrido certificado rellenaba el campo (`scripts_e2e_f01_retry.mjs:176`), por eso no se vio.
- `:189-207` — `limpiarNumerosNoFinitos` convierte `NaN→undefined` en números; **no toca cadenas `''`**: numéricos de `extra_data` (p. ej. `transport_temperature:"22"`, `incubation_day:"18"`, `fcr:"2.000"`; B-26 con `OFP:947-973,1131-1157,1565,1708-1712`) viajan como cadenas.
- `''` persistido en lugar de ausente/null: `sap_document_ref:''`, `vaccination_route:''` (B-37, `OFP:1951,1962,566-567`).

## 2 · Causa raíz

El serializador del asistente limpia `NaN` pero no la clase «cadena vacía para opcional»; el backend tipado (fecha opcional) no tolera `''`.

## 3 · Comportamiento actual → esperado

| Caso | Hoy | Esperado |
|---|---|---|
| `quarantine_end_date` en blanco | `''` ⇒ 400 | campo omitido (undefined) ⇒ 201 |
| Numéricos de `extra_data` sin `valueAsNumber` | cadenas | número o ausente (canónico) |
| `sap_document_ref`/`vaccination_route` sin elegir | `''` | ausente (no `''`) |

## 4 · Secciones §47 (resumen)

- **Alcance**: `operationPayload.ts` (ampliar normalizador: `''`→`undefined` recursivamente para campos opcionales; números como número o ausente), `OperationFormPage.tsx` (puntos B-11/B-26/B-37); opcional: backend tolerante `''→None` **solo en campos opcionales** de `PlanDeImportacion` (defensa en profundidad, C-02).
- **Fuera**: limpieza de históricos; validación estricta de otros tipos.
- **FE**: serializador (testeable en unit puro).
- **BE** (si C-02=A): `schemas.py:23-44` tolerancia en opcionales — sin relajar requeridos.
- **Contrato**: el payload canónico omite vacíos; el backend sigue estricto.
- **Seguridad/tenant/BU/RBAC**: sin cambio. **Transacciones/Auditoría**: sin cambio.
- **i18n**: sin claves nuevas. **Móvil/escritorio**: sin cambio visual.
- **Migración/SAP**: ninguna / indirecto (importación de abuelas).
- **Compatibilidad**: clientes con `''` siguen fallando salvo que C-02=A lo tolere (documentado).
- **AC**: ver `R-206_AC_RED_E2E_UAT.md`. **Cierre**: AC verdes · RED · sin migración/endpoint/permiso.

## 5 · Dedup

R-189/F-01d cubrió `[{}]`/`NaN`; B-11/B-26/B-37 quedaron fuera (frontera declarada). **Nuevo** (registro G-17; familia R-189).

## 6 · Interdependencias

R-189/F-01 (serializador) · R-209 (`sap_document_ref`) · R-210 (mismo serializador) · R-190/R-205 (tranche del asistente, coordinar).
