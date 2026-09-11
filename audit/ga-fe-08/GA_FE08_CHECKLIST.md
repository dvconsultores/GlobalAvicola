# GA-FE-08 · CHECKLIST (AC → tarea → test → evidencia → estado)

Fecha: 2026-09-11 · Estados: ✅ PASS · ⏳ pendiente · ▶ en curso.

| AC | Tarea | Test | Evidencia runtime | Estado |
|---|---|---|---|---|
| FE08-AC01 descubrible por navegación normal | T02 | `gaFe08.lotsNav` (op descubre) | E2E-01/C01 | ⏳ |
| FE08-AC02 sin URL directa | T02 | idem | E2E-01/C01-C02 | ⏳ |
| FE08-AC03 usa la ruta existente | T01 | contrato `to==='/lots'` único | E2E-01 click → `/lots` | ⏳ |
| FE08-AC04 sin ruta duplicada | T01 | unicidad | reconciliación | ⏳ |
| FE08-AC05 estado activo | T01 | `isPathActive` | E2E-02 (contenedor resaltado) | ⏳ |
| FE08-AC06 solo con contexto de empresa | T02 | matriz global sin contexto | E2E-04/10 | ⏳ |
| FE08-AC07 BU OFF oculta | T02 | matriz BU OFF | E2E-04/C05 | ⏳ |
| FE08-AC08 sin BU de usuario oculta | T02 | matriz sin unidades | E2E-06 | ⏳ |
| FE08-AC09 histórico OD-23 oculto | T02 | matriz histórica | E2E-05/C06 | ⏳ |
| FE08-AC10 concesión fresca muestra | T02 | matriz fresca | E2E-05/C07 | ⏳ |
| FE08-AC11 sin RBAC oculta | T02 | matriz sin permiso | E2E-07/C08 | ⏳ |
| FE08-AC12 zero-BU sin entrada | T02 | fixture Z | E2E-08 | ⏳ |
| FE08-AC13 Access Admin sin Lotes | T02 | fixture B | E2E-09/C09 | ⏳ |
| FE08-AC14 global no bypassa BU OFF | T02 | fixture E-all-off | E2E-04 (spot global) | ⏳ |
| FE08-AC15 deep link autorizado | T02 | matriz | E2E-01 (URL directa) | ⏳ |
| FE08-AC16 sin autoridad falla cerrado | T02 | matriz | E2E-06/07 (denegación visual/vacío) | ⏳ |
| FE08-AC17 nav ≠ autoridad | — | frontera (contrato ruta intacto) | reconciliación | ⏳ |
| FE08-AC18 sin datos ajenos | — | — | E2E-10 | ⏳ |
| FE08-AC19 desktop hub | T03 | vista web | E2E-01/C01 | ⏳ |
| FE08-AC20 móvil hub | T03 | vista mobile | E2E-03/C03-C04 | ⏳ |
| FE08-AC21/22 ES/EN | T04 | paridad `nav.lots` | E2E (ETIQUETA ES/EN) | ⏳ |
| FE08-AC23 sin hardcode | T04 | reuso de clave | evidencia | ⏳ |
| FE08-AC24 sin overflow | — | — | E2E-03 (0) | ⏳ |
| FE08-AC25 consola 0 | — | — | E2E (0 fatales) | ⏳ |
| FE08-AC26 orden coherente | T01 | orden del hub | C01 | ⏳ |
| FE08-AC27…37 regresiones | T05/T06 | suites + spots | evidencia de regresión | ⏳ |
