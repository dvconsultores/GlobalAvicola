# GA-FE-07 · TAREAS

| ID | Finding | Cláusula OD-21 | Sección spec | AC | Ficheros | Test | Evidencia runtime | Dependencia | Estado |
|---|---|---|---|---|---|---|---|---|---|
| T01 | R-185 | 1–2 | §10 alta | AC07 | `lots/service.py` (create) | `test_lot_area_eligibility.py` | E2E-03 | validador extendido | ○ |
| T02 | R-185 | 3 | §11 edición | AC15 | `lots/service.py` (update, detección cambio) | íd. (H3/H5) | E2E-04/08 | T01 | ○ |
| T03 | R-185 | 4–6,8 | §9/§11 | AC12/13/17 | `lots/service.py` (sin regla cuando no hay cambio) | íd. (H1/H2) | E2E-05/06/09 | T02 | ○ |
| T04 | R-185 | 9 | §11 | AC14/16 | `lots/service.py` + `tenancy.py` (`exigir_activo`) | íd. (H4, ajena) | E2E-07/10 | T02 | ○ |
| T05 | R-185 | 3 | §12 | AC18/19/20 | `LotFormPage.tsx` (filtro selector) | `gaFe07.inactiveAreaEligibility.test.tsx` | E2E-02/24 | — | ○ |
| T06 | R-185 | 11 | §16 | AC15 | `tenancy.py` mensaje «Área inactiva» | tests contrato | E2E-03/04 | T01 | ○ |
| T07 | R-185 | 12 | §12/§22 | AC22 | (no tocar MasterListPage) | — | regresión masters | — | ○ |
| T08 | R-185 | — | §19 | AC38–42 | (diff aislado) | vitest completo | muestreos | T01–T05 | ○ |
| T09 | R-185 | — | §23 | AC01–44 | docs | — | — | T01–T08 | ○ |
