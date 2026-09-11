# GA-FE-07 · CHECKLIST (por AC — tarea, prueba, evidencia runtime, estado)

| AC | Tarea | Prueba | Evidencia runtime | Estado |
|---|---|---|---|---|
| AC01 | OD-21 registrada | doc | — | ✔ |
| AC02 | Principio general documentado sin implementación masiva | doc + diff | — | ✔ |
| AC03 | Alcance Área→Lote explícito | spec §6 | — | ✔ |
| AC04 | Referencias históricas válidas | test H1/H2 | E2E-05/06 | ○ |
| AC05 | Ningún FK histórico reescrito | test + fresh GET | E2E-05 | ○ |
| AC06 | Activa propia ALLOW | test alta | E2E-01 | ○ |
| AC07 | Inactiva propia DENY | test alta | E2E-03 | ○ |
| AC08 | Ajena activa DENY | test | E2E-10 | ○ |
| AC09 | Ajena inactiva DENY | test | E2E-10 | ○ |
| AC10 | Inexistente DENY | test | matriz | ○ |
| AC11 | NULL sin cambio | test | E2E-11 | ○ |
| AC12 | Update no relacionado histórica ALLOW | test H1 | E2E-06 | ○ |
| AC13 | Histórica preservada | test | E2E-05/06/07 | ○ |
| AC14 | Cambio a activa ALLOW | test H4 | E2E-07 | ○ |
| AC15 | Cambio a inactiva DENY | test H3/H5 | E2E-04/08 | ○ |
| AC16 | Cambio a ajena DENY | test | E2E-10 | ○ |
| AC17 | Mismo ID inactivo explícito sin falsa invalidación | test H2 | E2E-09 | ○ |
| AC18 | Inactiva ausente del selector nuevo | vitest | E2E-02 (desktop/móvil) | ○ |
| AC19 | Activa presente | vitest | E2E-01/02 | ○ |
| AC20 | Sin IDs crudos | vitest | capturas | ○ |
| AC21 | Display histórico no se rompe | — | fresh GET histórico | ○ |
| AC22 | Visibilidad admin intacta | — | regresión masters | ○ |
| AC23 | Móvil = desktop | — | E2E móvil | ○ |
| AC24/25 | ES/EN completas (sin copia nueva) | — | declaración | ○ |
| AC26 | Backend aplica la regla | test | E2E-03/04 | ○ |
| AC27 | UI no es única defensa | test directo | E2E-03 | ○ |
| AC28 | Tenencia intacta | tests área | E2E-10 | ○ |
| AC29–AC32 | BU/RBAC/global | tests | matriz regresión | ○ |
| AC33 | Sin falso éxito | vitest | E2E-12 (carrera) | ○ |
| AC34 | Denegación no persiste | test DB | búsqueda tras DENY | ○ |
| AC35 | Sin auditoría de éxito en DENY | test | auditoría | ○ |
| AC36 | Consola sin errores fatales | — | capturas + conteo | ○ |
| AC37 | Sin tormenta de fetch | — | conteo red | ○ |
| AC38–AC42 | Regresiones GA-FE-02..06 | vitest + runtime | muestreos | ○ |
| AC43 | R-182 sigue CLOSED | diff | — | ○ |
| AC44 | R-184 intacto | diff | — | ○ |
