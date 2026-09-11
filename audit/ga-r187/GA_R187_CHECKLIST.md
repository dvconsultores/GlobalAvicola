# GA-R187 · CHECKLIST (AC → tarea → test → evidencia runtime → estado)

Cobertura completa R187-AC01…AC52 (sin AC huérfano). Estados: [x] hecho · [ ] pendiente.

## Gobierno
| AC | Tarea | Test | Evidencia runtime | Estado |
|---|---|---|---|---|
| AC01 | T01 | Revisión doc (spec §2) | — | [x] |
| AC02 | T01 | Revisión doc (reconciliation §1) | — | [x] |
| AC03 | T02 | Revisión doc (reconciliation §2) | — | [x] |
| AC04 | T02 | Revisión doc (spec §5) | — | [x] |
| AC05 | T03 | `GA_R187_UNIT_TRACE.md` §1-4 + suite aserciones de unidad | prefijo-ipe (404 gobernado) + committed R-184 (100.0/95.0) | [x] |

## Fórmula
| AC | Tarea | Test | Evidencia runtime | Estado |
|---|---|---|---|---|
| AC06 | T10 (impl) | `test_r187_…det_od22` (assert 333.3; ≠33333.3) | E2E-01/02 | [ ] |
| AC07 | T10 | idem + matemática independiente | E2E-01 | [ ] |
| AC08 | T10 | diff de implementación (solo `* 100` retirado) | — | [ ] |
| AC09 | T10 | determinista (viab 95.0) | E2E-01 | [ ] |
| AC10 | T10 | determinista (ganancia 105.26) | E2E-01 | [ ] |
| AC11 | T10 | determinista (fcr 3.0) | E2E-01 | [ ] |
| AC12 | T10 | controles de fecha | E2E-06 | [ ] |

## Bandas
| AC | Tarea | Test | Evidencia runtime | Estado |
|---|---|---|---|---|
| AC13 | T11 | diffs vacíos en bandas + tests | E2E-03/04/05 | [ ] |
| AC14 | T11 | diffs vacíos en i18n | E2E-07 screenshots | [ ] |
| AC15 | T11 | `test_…frontera_250` (250.0 🟡 / 249.9 🔴) | E2E-04b (fixture 250.0) | [ ] |
| AC16 | T11 | `test_…frontera_300` (300.0 🟢) | E2E-04c (fixture 300.0) | [ ] |
| AC17 | T11 | grep umbrales (solo 300/250 existentes) | — | [ ] |
| AC18 | T11 | revisión doc (BAND_TRACE §7) | E2E-07/08 consistencia | [ ] |

## Fecha
| AC | Tarea | Test | Evidencia runtime | Estado |
|---|---|---|---|---|
| AC19 | T12 | control fechas suite | E2E-06 + lote 11 age 110 | [ ] |
| AC20 | T12 | idem (sin TypeError) | E2E-06 | [ ] |
| AC21 | T12 | idem (±1 día) | E2E-06 | [ ] |
| AC22 | T12 | mismo día → 1 / ipe 0 | E2E-06 variante | [ ] |
| AC23 | T12 | sin fecha → 30 / ipe 0 | E2E-06 variante (si hay lote legado) | [ ] |

## Resultado
| AC | Tarea | Test | Evidencia runtime | Estado |
|---|---|---|---|---|
| AC24 | T13 | determinista == independiente | E2E-01 | [ ] |
| AC25 | T13 | cálculo a mano en doc+suite | — | [ ] |
| AC26 | T13 | redondeo 1d (aserción exacta) | E2E-01 (5.6 / 333.3) | [ ] |
| AC27 | T13 | guardas NaN | E2E (sin NaN) | [ ] |
| AC28 | T13 | guardas Infinity | E2E (sin Infinity) | [ ] |
| AC29 | T13 | cero/faltante controlado (fcr 0 ⇒ 0.0) | E2E lotes 33/35 (ipe 0.0) | [ ] |

## UI
| AC | Tarea | Test | Evidencia runtime | Estado |
|---|---|---|---|---|
| AC30 | T20 | — | E2E-07 (tarjeta IPE nuevo valor) | [ ] |
| AC31 | T20 | — | E2E-08 (reporte mismo valor) | [ ] |
| AC32 | T20 | — | E2E-07/08 clasificación nueva correcta | [ ] |
| AC33 | T20 | — | E2E-09 refresco | [ ] |
| AC34 | T20 | — | E2E-09 relogin | [ ] |
| AC35 | T20 | — | E2E-10 móvil 390×844 | [ ] |
| AC36 | T20 | — | E2E-07/08 sin error crudo | [ ] |

## Seguridad
| AC | Tarea | Test | Evidencia runtime | Estado |
|---|---|---|---|---|
| AC37 | T21 | suite seguridad (ajeno 404) | E2E-11 | [ ] |
| AC38 | T21 | — | E2E-12 (BU OFF) | [ ] |
| AC39 | T21 | suite (sin concesión 404) | E2E-13 | [ ] |
| AC40 | T21 | suite (sin RBAC 403) | E2E-14 | [ ] |
| AC41 | T21 | — | E2E-12 global + BU OFF | [ ] |
| AC42 | T21 | — | E2E-11/12 sin fuga | [ ] |

## Regresión
| AC | Tarea | Test | Evidencia runtime | Estado |
|---|---|---|---|---|
| AC43 | T22 | suite R-184 (técnica) | E2E R-184 (200 en todo lote) | [ ] |
| AC44 | T22 | suite R-184 | E2E-06 | [ ] |
| AC45 | T22 | suite R-184 ajustada* | E2E-02 (5.6 == OD-22, NO 556.6) | [ ] |
| AC46 | T23 | suite R-186 | E2E G-05 (5.1 estable) | [ ] |
| AC47 | T23 | spot GA-FE-07 | spot área inactiva (400 si aplica) | [ ] |
| AC48 | T23 | Vitest | spot UI operaciones | [ ] |
| AC49 | T23 | Vitest | — | [ ] |
| AC50 | T23 | Vitest | spot GA-FE-07 | [ ] |
| AC51 | T23 | — | sin tocar (doc) | [ ] |
| AC52 | T23 | — | sin tocar (doc) | [ ] |

\* §31: la suite R-184 **actualiza su aserción numérica al valor OD-22** (mismos insumos crudos ⇒ 333.3, cálculo independiente), conservando sus invariantes técnicos (200, fechas, esquema, seguridad); el `33333.3` del régimen anterior queda como comentario histórico, no como aserción. Los documentos históricos `audit/ga-r184/**` no se reescriben. (Registrado en `GA_R187_RED_EVIDENCE.md` §5.)

## Cierre
| AC | Tarea | Test | Evidencia | Estado |
|---|---|---|---|---|
| (cobertura) | T30 | `GA_R187_CLOSURE_RECONCILIATION.md` | todo lo anterior + git | [ ] |
