# GA-FE-05 · CHECKLIST (AC ↔ tarea ↔ test ↔ evidencia)

Sin AC huérfano. Estados: ☐ pendiente · ✅ cumplido.

## Contrato
| AC | Descripción | Tarea | Test/instrumento | Evidencia | Estado |
|---|---|---|---|---|---|
| R181-AC01 | Contrato backend documentado | T1 | reconciliación §2 | doc | ✅ |
| R181-AC02 | Gap frontend documentado | T2 | reconciliación §3–4 | doc | ✅ |
| R181-AC03 | Permiso canónico `operations:create` | T2/T8 | vitest permisos | test + spec §11 | ✅ |
| R181-AC04 | Contexto de empresa respetado | T8/T21 | vitest + E2E-02 | runtime | ✅ |
| R181-AC05 | CBU OFF bloquea | T21 | E2E-02 | runtime | ✅ |
| R181-AC06 | User BU/global respetados | T19–T21 | vitest + E2E-01/03 | runtime | ✅ |
| R181-AC07 | Backend autoridad final | T21/T24 | API directa | runtime | ✅ |

## Submit
| R181-AC08 | Descubrible por UI normal | T11 | vitest CTA + E2E-01 | captura | ✅ |
| R181-AC09 | Una mutación por acción | T11/T25 | vitest doble clic + E2E-09 | red | ✅ |
| R181-AC10 | Refresh verdad backend | T13 | vitest refetch + E2E-01 | red | ✅ |
| R181-AC11 | Estado correcto tras éxito | T13 | vitest + E2E-01 | runtime | ✅ |
| R181-AC12 | CTA desaparece tras éxito | T13 | vitest + E2E-01 | captura | ✅ |
| R181-AC13 | Sin éxito falso | T14 | vitest fallo + E2E-10 | runtime | ✅ |
| R181-AC14 | Refresh preserva estado | T13 | E2E-01 | runtime | ✅ |
| R181-AC15 | Relogin preserva estado | T13 | E2E-01 | runtime | ✅ |

## Resubmit
| R181-AC16 | `returned/rejected` exponen reenvío (OD-17) | T12 | vitest + E2E-06/07 | runtime | ✅ |
| R181-AC17 | Sin reenvío antes de corrección cuando el contrato lo exige | T12 | análisis (no exigido para `returned`; `corrected` sin CTA) | spec C09 | ✅ |
| R181-AC18 | Reenvío autorizado funciona | T12 | E2E-07 | runtime | ✅ |
| R181-AC19 | Estado resultante correcto | T12 | E2E-07 | runtime | ✅ |
| R181-AC20 | Persistencia refresh/relogin | T12 | E2E-07 | runtime | ✅ |
| R181-AC21 | Final inmutable sin reenvío | T19 | vitest + E2E-08 | runtime | ✅ |

## Negativos
| R181-AC22 | CBU OFF ⇒ oculto/denegado | T19 | E2E-02 | runtime | ✅ |
| R181-AC23 | Sin User BU ⇒ oculto/denegado | T19 | vitest + E2E-03 | runtime | ✅ |
| R181-AC24 | Sin RBAC ⇒ oculto/denegado | T19 | vitest + E2E-04 | runtime | ✅ |
| R181-AC25 | No autorizado ⇒ oculto/denegado | T19 | vitest + E2E-04 | runtime | ✅ |
| R181-AC26 | Estado inválido ⇒ oculto/denegado | T19 | vitest + E2E-05 | runtime | ✅ |
| R181-AC27 | API directa no elude | T21/T24 | E2E-02–05 API | runtime | ✅ |
| R181-AC28 | Global no elude CBU OFF | T21 | E2E-02 variante global | runtime | ✅ |

## Calidad
| R181-AC29 | Desktop usable | T15 | E2E desktop | captura | ✅ |
| R181-AC30 | Móvil usable | T16 | E2E móvil | captura | ✅ |
| R181-AC31 | ES completo | T17 | runtime ES | captura | ✅ |
| R181-AC32 | EN completo | T17 | runtime EN | captura | ✅ |
| R181-AC33 | Sin claves crudas | T17 | revisión + runtime | captura | ✅ |
| R181-AC34 | Sin mutación duplicada | T25 | E2E-09 | red | ✅ |
| R181-AC35 | Sin flash de permiso | T18 | vitest (fail-closed) + runtime | test | ✅ |
| R181-AC36 | Sin error fatal de consola | T22 | runtime consola | log | ✅ |
| R181-AC37 | Auditoría correcta | T21 | audit API | runtime | ✅ |
| R181-AC38 | Regresión GA-FE-02 | T27 | suite + spots | test | ✅ |
| R181-AC39 | Regresión GA-FE-03 | T27 | suite + spots | test | ✅ |
| R181-AC40 | Regresión GA-FE-04 | T27 | GA-FE-04 22/22 + spots | test | ✅ |
