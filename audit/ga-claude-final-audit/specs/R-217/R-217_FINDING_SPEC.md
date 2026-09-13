# R-217 · FINDING + SPEC (COMPACTO) — `SapManagerPage`: ESTADOS INEXISTENTES, SIN REFETCH NI REINTENTO

| Campo | Valor |
|---|---|
| **ID** | **R-217** · P2 · **no bloquea ahora** (SÍ para la fase SAP) · Estado `SPEC_READY` |
| **Origen** | C#10/C#22/C#24 (informe C); B-27 (DTO muerto) · Registro G-29 · HEAD `c0b4afc` · 2026-09-13 |
| **GA-REM** | a asignar; sin migración · UAT: no (fase SAP; informativa) |

## 1 · Contexto y evidencia

`SapManagerPage.tsx:70-72,191-291` filtra por `'pending'|'draft'|'sent'|'error'` mientras el backend produce `prepared/sending/confirmed/failed/retrying` (`sap/models.py:40-52`) ⇒ «Pendientes» y «Errores» siempre 0; los `failed` nunca se ven; jobs `failed` reciben variante `pending`. Sin refetch tras consolidar/exportar (`:51-67`) ⇒ KPIs/pestañas viejos hasta F5. Sin UI para `/sap/retry` (`sapService.retry` sin llamador) ni para `/sap/references/import` (DTO muerto con `entries` vs `references`, B-27); `delivers_to_sap`/`mode` ignorados (un adaptador simulado parece «conectado»).

## 2 · Causa raíz

Vocabulario FE obsoleto respecto al modelo; sin relectura tras mutación; capacidades (retry/import/errores) sin superficie.

## 3 · Comportamiento actual → esperado

| Aspecto | Hoy | Esperado |
|---|---|---|
| Estados | vocabulario inventado | `prepared/sending/confirmed/failed/retrying` (valores) + jobs `pending/in_progress/completed/failed` |
| Pendientes/Errores | 0 siempre | recuentos reales; `failed` visible |
| Tras consolidar/exportar | sin refetch | KPIs y listas refrescadas; toast con resultado |
| Retry | sin UI | acción de reintento (gate `sap:send_sap`) para `failed` |
| Importación de referencias | servicio muerto (`entries`) | corregir DTO o retirar el método muerto (C-02) |
| Conexión | «conectado» simulado | mostrar `delivers_to_sap/mode` (manual/simulado explícito) |

## 4 · Secciones §47 (resumen)

- **Alcance FE**: `SapManagerPage.tsx`, `sap.service.ts` (tipos/estados; retry; import si C-02=A); i18n de estados.
- **Fuera**: backend SAP real (GA-REM-017/P-08); `R-201` (seguridad de contexto, paquete propio); re-proceso.
- **Contrato**: mismos endpoints; el FE consume los valores reales; sin cambios de esquema.
- **Seguridad**: gates `sap:read`/`sap:send_sap` (ya existen en backend).
- **Migración/SAP**: ninguna / es preparación de la fase.
- **AC/cierre**: ver `R-217_AC_RED_E2E_UAT.md`.

## 5 · Dedup

C#10/C#22/C#24 + B-27 + R-112 (response_model) — el hallazgo de UI no tenía paquete. **Nuevo** (G-29; fase SAP).

## 6 · Interdependencias

R-201 (contexto SAP; el panel con autoridad global sin contexto verá ∅ — correcto) · GA-REM-010 (modo manual) · R-112.
