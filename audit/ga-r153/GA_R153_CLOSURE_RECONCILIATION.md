# GA-R153 · RECONCILIACIÓN DE CIERRE (spec → contrato → evidencia)

Fecha: 2026-09-12 · Spec: `GA_R153_AUTOMATIC_GRANDPARENT_LOT_SPEC.md` (AC01–AC57) + **AC58/59** (derivación por tipo, añadidos en C2b).

| AC | Qué exige | Evidencia | Estado |
|---|---|---|---|
| 01–03 | Decisión formalizada (OD-25 = B), sin migración, vía manual preservada | `GA_OD_25_…DECISION.md` · C1 | ✅ |
| 04–05 | Registrar importación sin lote (API y UI) | Suite AC04/05 · E2E-01 · nota UI | ✅ |
| 06–08 | Aprobar ⇒ exactamente 1 lote | Suite AC06-08 · E2E-04 | ✅ |
| 09–11 | Código `L-GP-{año}-{nn}` por empresa/año | Suite AC09/10 · runtime 01→…→09 | ✅ |
| 12–15 | Mapeo de campos (granja/galpón del evento; genética/área/curva NULL; sexo del plan) | Suite AC12-14 · `LOT_FIELD_MAPPING` · E2E-05 | ✅ |
| 16–22 | Aprobar NO puebla; recepción sí (una vez) | Suite AC16-21 · E2E-06 bracketing · E2E-12/13 | ✅ |
| 23–27 | Doble aprobación sin duplicar; legado sin duplicar | Suite AC23/26/27 · E2E-18/19 | ✅ |
| 28–32 | Devolución sin lote; fallo del lote revierte la aprobación | Suite AC28/29/31/32 | ✅ |
| 33–35 | Regresión de lotes (cierre/activación) intacta | Suites existentes (CI) | ✅ (CI) |
| 36–43 | UI: lote opcional + nota + enlace/pendiente + i18n | Vitest 3/3 · 295/295 · capturas UI | ✅ |
| 44–49 | Guardas de unidad/tenant (403; BU OFF cerrado; ajena invisible) | Suite AC45/46/59 · E2E-AC45 | ✅ |
| 50–57 | No regresión global (BR-17/18/20/22, R-130, P-07) | Suites CI vecinas · build/vitest 295 | ✅ (CI declarada) |
| **58** | Sin lote y sin clasificar ⇒ visible a `grandparent`, fuera de la bandeja | Suite AC58 · runtime (84→200) | ✅ |
| **59** | La derivación **no** abre alcance a otras cadenas | Suite AC59 | ✅ (CI) |

**Diferidos declarados**: ejecución local PG (CI) · concurrencia multi-proceso runtime (misma primitiva que `R-130`; cubierta en CI).
