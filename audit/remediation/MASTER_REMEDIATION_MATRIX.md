# MATRIZ MAESTRA DE REMEDIACIÓN

Documento vivo. Se actualiza tras el cierre de cada `GA-REM`.

**Última actualización:** 2026-09-04 (cierre de **Wave 3**) · **Commit base:** `bfccdfb`

---

## 1. Matriz

| GA-REM | Problema | Prior. | Dependencias | Spec | Implementación | Tests | E2E | Estado |
|---|---|---|---|---|---|---|---|---|
| `001` | Constitución sin ratificar | P0 | — | ✅ | ✅ | ✅ 6/6 | n/a | **`CERTIFIED`** |
| `020` | Documentación del cliente sin usar para validar (R-15) | P1 | 001 | ✅ | ✅ | ✅ 4/4 | n/a | **`CERTIFIED`** |
| `014` | Sin entorno de test aislado | P0 | 001 | ✅ | ✅ | ✅ 6/6 + 25 | n/a | **`CERTIFIED`** |
| `004` | Credenciales públicas · rate limit off | P0 | 001 | ✅ | ✅ | ✅ | n/a | **`CERTIFIED`** |
| `009` | Evidencias se pierden en cada despliegue | P0 | 001 | ✅ | ✅ | ✅ | ⬜ | **`CERTIFIED`** |
| `010` | SAP simulado marca `sent_to_sap` | P0 | 001 | ✅ | ✅ | ✅ | ⬜ | **`CERTIFIED`** |
| `011` | 18 desajustes de contrato · 5 pantallas caídas | P0 | 001, 014 | ✅ | ✅ 10/18 | ✅ | ⬜ | **`PARTIALLY CERTIFIED`** |
| `013` | CI nunca ejecutado | P1 | 001, 014 | ✅ | ✅ | ✅ 8/8 | n/a | **`CERTIFIED`** |
| `005` | Mortalidad → 500 · `R-38`…`R-41` | P0 | 001, 014, 023 | ✅ *(enmendada)* | ✅ | ✅ 16/16 | ⬜ | **`CERTIFIED`** |
| `002` | RBAC no aplicado · `R-36` `R-44` `R-48` | P0 | 001, 014, **024** | ✅ | ✅ | ✅ 21+35 | ⬜ | **`CERTIFIED`** |
| `003` | Refresh degrada la identidad · **`R-43`** el refresco nunca funcionó | P0 | 001, 014 | ✅ | ✅ | ✅ | ⬜ | **`CERTIFIED`** |
| `007` | BR-14 eludible · `R-23` | P0 | 001, 002, 014 | ✅ | ✅ | ✅ | ⬜ | **`CERTIFIED`** |
| `012` | Cambio de contraseña inoperante (`P0-13`) | P0 | 001, 002, 003, 014 | ✅ | ✅ | ✅ 11/11 | ⬜ | **`CERTIFIED`** |
| `006` | Correcciones no aplican el valor (`P0-2`) | P0 | 001, 011, 014 | ✅ | ✅ | ✅ 18/18 | ⬜ | **`CERTIFIED`** |
| `008` | Trazabilidad auto-referencial | P0 | 001, 011, 014 | ✅ | ✅ | ✅ 4/4 | ⬜ | **`CERTIFIED`** — `RC-04` resuelto (`RR-04`) |
| `015` | 101 tests nunca ejecutados · addendum **`R-28`** | P1 | 014 | ✅ | ✅ | ✅ 5/5 + 7/7 | n/a | **`CERTIFIED`** |
| `021` | Consumo de agua no capturado (R-13) | P1 | 001 | ✅ | ⬜ | ⬜ | ⬜ | `SPEC_READY` — Wave 2 |
| `022` | KPI incompletos (R-14, R-17) | P1 | 001, 011 | ✅ | ⬜ | ⬜ | ⬜ | `SPEC_READY` — Wave 2 |
| `016` | 0 procesos certificados | P1 | 7 specs | ⚠ draft | ⬜ | ⬜ | ⬜ | `SPEC_DRAFT` |
| `018` | Trazabilidad metodológica perdida | P1 | 001 | ✅ | ⬜ | n/a | n/a | `SPEC_READY` |
| `017` | Sin integración SAP real | P1 | externo | ⚠ prelim | ⬜ | ⬜ | ⬜ | **`BLOCKED_EXTERNAL`** |
| **`023`** | `P0-14` 14 columnas descartadas · `R-26` 7 reglas devuelven 500 · `R-27` `R-30` `R-32` `R-34` | **P0** | 001, 014 | ✅ | ✅ | ✅ 33/33 | ⬜ | **`CERTIFIED`** |
| **`024`** | **`GA-TD-013`** el despliegue no ejecutaba migraciones | **P0** | — | ✅ | ✅ | ✅ 4 escenarios de arranque real | n/a | **`CERTIFIED`** |
| `019` | Deuda P2/P3 + hallazgos de W1, W1.5, W2 y W2.5 | P2 | Fases A–G | ✅ | ⬜ | n/a | n/a | `DEFERRED` |

⚠ = bloqueada por un `REQUIREMENT_CONFLICT` pendiente de decisión. **Tras Wave 1.5 no queda ninguna.**

`RC-01`, `RC-02`, `RC-03` y `RC-05` resueltos por evidencia; `RC-07` acotado a `GA-REM-017`.
Detalle → `REQUIREMENT_CONFLICT_RESOLUTION.md`.

## 2. Marcador de métricas

Se actualiza tras cada cierre. **No se espera al final del programa para volver a medir.**

| Métrica | Baseline | W1 | W1.5 | W2 | W2.5 | W2.75 | **Wave 3** | Objetivo |
|---|---|---|---|---|---|---|---|---|
| Requerimientos vigentes | 56 | 60 (baseline V1.1) | 60 | 60 | 60 | 60 | 60 | 60 |
| Requerimientos E2E completos | 12 / 56 | 12 / 60 | 12 / 60 | **12 / 60** *(sin cambio: E2E no ejecutado)* | 12 / 60 *(sin cambio: E2E no ejecutado)* | 12 / 60 *(sin cambio: E2E no ejecutado)* | **21 / 60** | ≥ 30 |
| **Cobertura funcional E2E** | 21,4 % | 20,0 % | 20,0 % | **20,0 %** *(no se aumenta sin certificación real)* | 20,0 % *(no se aumenta sin certificación real)* | 20,0 % *(no se aumenta sin certificación real)* | **35 %** | ≥ 50 % |
| Procesos certificados | 0 / 15 | 0 / 15 | 0 / 15 | **0 / 15** | 0 / 15 | 0 / 15 | **1 / 15** *(+3 de 9 pasos del orden)* | ≥ 3 |
| Tests backend PASS | 0 (nunca ejecutados) | 0 | 74 / 101 | 211 / 211 | **229 / 229** + **35 / 35** (actualización) | **253 / 253** + 35 + 14 | **265 / 265** | 100 % |
| Tests backend existentes | 76 | 100 | 101 | 211 | **264** (229 + 35) | **302** | 302 | — |
| Tests frontend PASS | 61 / 61 | 61 / 61 | 61 / 61 | **61 / 61** | 61 / 61 | 61 / 61 | 61 / 61 | mantener |
| Tests E2E PASS | 0 | 0 | 0 | **0** *(no ejecutados por encargo)* | 0 *(no ejecutados por encargo)* | 0 *(no ejecutados por encargo)* | **21 / 21** | > 0 |
| **Bloqueadores P0 abiertos** | 12 | 8 | 10 | 0 | **0** | 0 | 0 | 0 |
| Riesgos P1 abiertos | 16 | 13 | 16 | 4 | **3** *(`R-42`, `R-45`, `R-47`)* | 3 *(`R-42`, `R-45`, `R-47`)* | 3 *(`R-42`, `R-45`, `R-47`)* | ≤ 4 |
| Desajustes de contrato FE↔BE | 13 (18 al inventariar) | 8 | 8 | **8** | 8 | 8 | 8 | 0 |
| Pantallas caídas | 5 | 0 | 0 | **0** | 0 | 0 | 0 | 0 |
| Endpoints con PUT de maestros | 4 / 12 | 12 / 12 | 12 / 12 | 12 / 12 | 12 / 12 | 12 / 12 | 12 / 12 | 12 |
| Operaciones OpenAPI | 168 | 176 | 176 | **178** (+ cambio de contraseña) | 178 (+ cambio de contraseña) | 178 (+ cambio de contraseña) | 178 (+ cambio de contraseña) | — |
| Deriva de esquema | 0 | 0 | 0 | 0 | **0** tablas · **0** columnas · **0** enums | 0 tablas · 0 columnas · 0 enums | 0 tablas · 0 columnas · 0 enums | 0 |
| Paridad i18n | 865 = 865 | 865 = 865 | 865 = 865 | **866 = 866** | 866 = 866 | 866 = 866 | 866 = 866 | mantener |
| `TODO` en el backend | 1 | 0 | 0 | **0** | 0 | 0 | 0 | 0 |
| Deuda Spec Development | 16 | 14 | 13 | **9** | 9 | 9 | 9 | ≤ 4 |
| Quality gates ejecutándose | no | sí — 8/8 | sí — 8/8 | **sí — 8/8** | sí — 8/8 | sí — 8/8 | sí — 8/8 | sí |
| **Rutas con autorización declarada** | 0 / 78 | 0 / 78 | 0 / 78 | 177 / 177 | **177 / 177** | **177 / 177** | 177 / 177 | 100 % |
| **Camino de actualización certificado** | no | no | no | no | **sí** | **sí, en arranque real** | sí, en arranque real | sí |
| **Migraciones aplicadas en el despliegue** | **no** | no | no | no | **sí** (`GA-REM-024`) | **sí, certificado en runtime** | sí, certificado en runtime | sí |
| Madurez | NIVEL 3 | NIVEL 3 | NIVEL 3 | NIVEL 3 | **NIVEL 3** *(NIVEL 4 exige E2E certificado)* | NIVEL 3 *(NIVEL 4 exige E2E certificado)* | **NIVEL 4 — OPERATIONAL BETA** | NIVEL 4 |


---

## 3. Nota sobre el aumento de P0 tras Wave 1.5

Los bloqueadores P0 subieron de 8 a 10 y los riesgos P1 de 13 a 16. **Esto no es un
retroceso.** `P0-13`, `P0-14`, `R-23`, `R-26` y `R-28` no se crearon en esta Wave: ya
estaban en el producto. Se hicieron visibles porque, por primera vez, la suite backend se
ejecuta contra una base de datos real y porque se persiguió cada `RC` hasta su evidencia.

Un programa de remediación honesto sube su recuento de defectos cuando mejora su capacidad
de detección. El indicador sano no es «P0 bajando siempre», sino «P0 conocidos, trazados y
con spec de destino»: **10 / 10**.

---

## 4. `GA-REM-029` · Contrato de cierre de lote (2026-09-05)

| Hallazgo | Sev. | Estado |
|---|:--:|---|
| `R-73` · `POST /lots/{id}/close` respondía 500 siempre | P1 | **`CERTIFIED`** |
| `R-74` · `BR-05` colgaba del evento `lot_closure`, que no cierra el lote | P1 | **`CERTIFIED`** |
| `R-75` · `end_date` a medianoche local → el cierre se releía con la fecha de ayer | P1 | **`CERTIFIED`** |

El endpoint es el único punto del backend que asigna `status = "closed"`, así que ningún
lote pudo cerrarse nunca hasta ahora.

**No certificó ningún proceso.** El frente se eligió con evidencia y la propia matriz de
alcance ya avisaba: `R-73` tenía fan-out 1. `P-06` sigue `PARTIAL` por `GA-TD-014` y
`GA-REQ-037`. Sirve de recordatorio de que cerrar un defecto real y certificar un proceso
son cosas distintas.

Evidencia: `R-73-LOT-CLOSE-CERTIFICATION.md` · `R73_CLOSE_LOT_CONTRACT_MATRIX.md`.


---

## 5. `GA-REM-030` · `GA-REM-031` · `P-10` certificado (2026-09-05)

| Hallazgo | Sev. | Estado |
|---|:--:|---|
| `R-60` · los vínculos de trazabilidad no comprobaban pertenencia ni existencia | P2 | **`CERTIFIED`** |
| `R-78` · el vínculo no se creaba desde la recepción: en el orden natural no se creaba ninguno | **P1** | **`CERTIFIED`** |
| `R-79` · la evidencia de `GA-REM-008 AC01` no podía fallar | P2 | **`CERTIFIED`** |
| `R-80` · el día de negocio es local y `created_at` es UTC | P2 | abierto |

```
P-10 = CERTIFIED        CERTIFIED 6 / 15        PARTIAL 9 / 15
```

La cadena de causas es la lección del tramo: una afirmación que no podía fallar dejó pasar un
defecto de dominio, y ese defecto mantuvo un proceso en `PARTIAL` sin que ninguna matriz lo
mostrara. De ahí la enmienda F de `GA-REM-016`: la validez de la evidencia alcanza a toda
prueba invocada como tal, la escribiera quien la escribiera.


---

## 6. `GA-REM-032` · `P-09` certificado (2026-09-06)

| Hallazgo | Sev. | Estado |
|---|:--:|---|
| `R-81` · seis de once módulos sin un solo registro de auditoría | **P1** | **`CERTIFIED`** |
| `R-82` · la vista aparentaba filtrar y no filtraba | **P1** | **`CERTIFIED`** |
| `R-84` · el filtro de fecha devolvía 500 | **P1** | **`CERTIFIED`** |
| `R-83` · una acción sin empresa no puede auditarse | P2 | abierto |

```
P-09 = CERTIFIED        CERTIFIED 7 / 15        PARTIAL 8 / 15
```

Dos correcciones de medición que conviene conservar: las acciones emitidas eran **12**, no 6;
y **21 valores de enum no son 21 requisitos** — dos quedan fuera por no tener superficie que
auditar, y decirlo es más honesto que completarlas por estética.


---

## 7. `GA-REM-022` enmienda A · `P-15` certificado (2026-09-06)

| Hallazgo | Sev. | Estado |
|---|:--:|---|
| `R-14` · la tasa de eclosión devolvía texto en un campo numérico | **P1** | **`CERTIFIED`** |
| `R-85` · tres cocientes de incubadora con denominadores distintos, fundidos en uno | P2 | **`CERTIFIED`** |
| `R-86` · «Fertilidad» normativa y sin productor | P2 | **`CERTIFIED`** |
| ~~`R-87`~~ · ~~reporte de estados ausente~~ | — | **RETIRADO** |
| ~~`R-88`~~ · ~~exportación ausente~~ | — | **RETIRADO** |

```
P-15 = CERTIFIED        CERTIFIED 8 / 15        PARTIAL 7 / 15
```

Dos lecciones del tramo. La primera: **21 valores de enum no son 21 requisitos**, y de los
cuatro KPI «huérfanos» solo dos los exigía el cliente. La segunda es propia y menos cómoda:
registré dos hallazgos —`R-87` y `R-88`— buscando **solo en el backend**, y los dos estaban
implementados en el cliente. Retirados y anotados, no borrados.
