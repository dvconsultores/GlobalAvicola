# GA-CLAUDE · R-206 — CERTIFICACIÓN (vacíos del asistente: `''` ⇒ ausencia)

Fecha: 2026-09-14 · Hallazgo **R-206** (P2 · no bloquea) · Paquete `specs/R-206/` (compacto) · Commits: C1 `ce1ea7e` · C2 `da66344` · C2s `4fdd131`.

## 1 · Fases

| Fase | Estado | Evidencia |
|---|---|---|
| **C1 · RED** | ✅ | FE `evidence/red/vitest-r206.log` — **8F/8** (`limpiarVacios` inexistente; importación con cuarentena `''` viaja). BE `evidence/red/backend-r206.log` — **4F/2P** (tolerancia de `''` en opcionales de `PlanDeImportacion`; controles: fecha válida y requerido estricto) |
| **C2 · Implementación** | ✅ | `evidence/green/` — FE **17/17** (R-206 + serializadores); BE **35/35** (tolerancia + importaciones); `tsc` 0; FE completa **372/372**; `valueAsNumber` en 8 registros numéricos de `extra_data` · commit `da66344` |
| **C2s · Sensibilidad** | ✅ S1·S2 | S1 (serializador fuera de la cadena): 1F · S2 (validador BE apagado): 4F — `evidence/sensibilidad/` |
| **C3 · Runtime** | ⏸ pendiente | R206-RT-01/02 (importación con/sin fecha ⇒ 201; sonda API `''`) — ventana de deploy |

## 2 · Implementación

- `operationPayload.ts::limpiarVacios` — `''` ⇒ ausencia, **recursivo** (objetos/arrays), omite claves ausentes; compuesto con `limpiarNumerosNoFinitos` en el `preprocess` del esquema.
- `OperationFormPage.tsx` — `valueAsNumber` en los registros numéricos de `extra_data` (`transport_density`, `transport_temperature`, `transport_duration_min`, `incubation_day`, `fcr`; 8 sitios).
- `operations/schemas.py::PlanDeImportacion` — validador `mode="before"`: `''` en **opcionales** ⇒ `None` (defensa en profundidad, C-02=A); requeridos sin relajar.

## 3 · AC

| AC | Estado |
|---|---|
| AC-R206-01 (cuarentena en blanco ⇒ clave omitida) | ✅ jsdom · S1 |
| AC-R206-02 (fecha válida — control) | ✅ BE control |
| AC-R206-03 (numéricos canónicos) | ✅ unit + registros |
| AC-R206-04 (`sap_document_ref`/`vaccination_route` sin `''`) | ✅ unit (limpiarVacios) |
| AC-R206-05 (tolerancia BE opcionales) | ✅ BE 4/4 · S2 |
| AC-R206-06 (sin migración/endpoint/permiso) | ✅ diff FE+validador |
| AC-R206-07 (regresión serializadores/importaciones) | ✅ `f01d`/`f01.payloadContract`/importaciones verdes |

## 4 · Veredicto

**R-206 = `CLOSED_TECHNICALLY`** — el contrato canónico del asistente ya no lleva `''`; la importación con cuarentena en blanco guarda (201) por cualquier ruta. C3 runtime en ventana.
