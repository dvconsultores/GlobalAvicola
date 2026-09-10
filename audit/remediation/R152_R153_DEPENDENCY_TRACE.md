# `R-152` → `R-153` · Traza de dependencia (`R152_R153_DEPENDENCY_TRACE`)

**WAVE B · tranche 12 · pre-flight** · 2026-09-10 · baseline `5e9bbee` · Progenitoras (`grandparent`) · regla de la tranche: **el mismo concepto de
producto no implica la misma regla de negocio; el soporte de Reproductoras no certifica Progenitoras; la concesión de Reproductoras no autoriza Progenitoras**.

## 1. Lectura exacta de los dos hallazgos

| Hallazgo | Título oficial (backlog) | P | Origen | Requisito gobernante | Spec | Proceso | Unidad |
|---|---|---|---|---|---|---|---|
| `R-152` | «`grandparent_import` sin estructura para el plan de importación (`docs/02 §3.4.1`): país, cantidades comprada/embarcada/recibida, mortalidad en traslado, cuarentena, adjuntos tipados» | **P2** | `H360A-02` (`GLOBAL_AVICOLA_MASTER_360_ADDENDUM…:49`: «`grandparent_import` es un `OperationalEvent` genérico: `sap_document_ref`, `supplier_id`, `extra_data` libre; sin país, cantidades comprada/embarcada/recibida, mortalidad en traslado, cuarentena; adjuntos solo vía `evidences` sin tipología … la importación no es validable ni conciliable con la OC internacional») | `docs/02 §3.4.1` (22 campos del plan) · `spec.md §4.4` («Plan de importación (PO SAP, proveedor internacional, docs sanitarios, aduana, cuarentena)»; `grandparent_import` «Registro inicial de importación con documentos») | **spec propia** (`WAVE_B §1` fila 11: «tipo sin esquema propio»; ningún `GA-REM` lo gobierna) → `GA-REM-042` | `P-01` Progenitoras — Cría (paso 1 de 12, `PROCESS-01-CERTIFICATION §2`, `PASS` como evento genérico con OC) | Progenitoras (`grandparent`), exclusivamente (`spec.md §4.4`; ausente en `§4.5-§4.8`) |
| `R-153` | «el lote de abuelas no se crea automáticamente al completar la importación» | **P3** | `H360A-03` («ninguna rama crea un lote al completar la importación; no implementado; doble captura manual») | `docs/02 §3.4.2` («Al completar la importación, se crea automáticamente el lote de abuelas. Vinculación: Lote → Granja → Galpón → Trazabilidad») · `spec.md §4.4` («Creación de lote de abuelas vinculado a granja/galpón», sin la palabra *automática*) · `docs/15 :237` («Creación de lote de abuelas: `POST /lots` ✅», manual) | spec propia | `P-01` (paso 0: hoy el lote se crea a mano **antes** del paso 1, porque `grandparent_import` exige `lot_id`: `LOT_OPTIONAL_EVENTS` = solo inspecciones) | Progenitoras |

Búsqueda mecánica (`R-152`, `R-153`, `grandparent_import`, `GRANDPARENT`, `Progenitoras`): el backend tiene el tipo (`EventType.GRANDPARENT_IMPORT`), el
catálogo (`ALL_EVENT_TYPES`), ninguna rama de servicio ni validador; el frontend tiene el caso del formulario con **cuatro** entradas libres en
`extra_data` (`origin_country`, `sanitary_cert`, `quarantine_days`, `import_doc`) más filas ♂/♀; el E2E `proceso-p01` registra la importación con
`sap_document_ref` y `extra_data: {supplier: 'Internacional'}`; ninguna prueba de backend registra una importación (solo el catálogo). Ningún KPI,
saldo ni linaje lee la importación (`PROGENITORAS_COVERAGE_MATRIX`: «evento documental; la población entra por `bird_reception`»).

## 2. Traza de dependencia (`§11`)

| Hallazgo | Requisito raíz | Capacidad de negocio | Proceso | Unidad | Modelo | Servicio | Ruta | Frontend | Depende de | Tipo | Por qué | ¿Ejecutable solo? | ¿Decisión? | AC | Prueba |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `R-152` | `docs/02 §3.4.1` · `spec.md §4.4` | registrar el plan de importación con sus datos, identidades y adjuntos tipados | `P-01` paso 1 | `grandparent` | `OperationalEvent` (`extra_data` JSONB, `sap_document_ref`, `supplier_id`, `transport_id`, `bird_movements`), `Evidence.evidence_type` (`String(50)`), `Lot` (`bird_type`, `genetic_line_id`) | `_apply_business_rules` · guarda de edición/corrección (`R-173`/`R-176`) · `upload_evidence` | `POST /operations` · `PUT /operations/{id}` · `POST /corrections` · `POST /operations/{id}/evidences` | `OperationFormPage` (caso `grandparent_import`), `OperationDetailPage` (plan + adjuntos tipados), i18n | nada | — | los datos, identidades y tipología caben en el modelo actual; el lote existe antes (contrato vigente, `P-01` certificado) | **sí** | **no** (§4) | `AC-R152-*` | `tests/test_grandparent_import.py` · vitest |
| `R-153` | `docs/02 §3.4.2` | crear el lote de abuelas al completar la importación, vinculado a granja/galpón, con trazabilidad | `P-01` paso 0 | `grandparent` | `Lot` (nuevo desde el evento), `OperationalEvent.lot_id` (hoy obligatorio) | `create_lot` (existente, manual) · ninguna rama automática | `POST /operations` (importación sin lote) → `Lot` | `LotFormPage` (manual hoy) | **`R-152`** | **`HARD_DATA_MODEL`** (los atributos del lote —granja/galpón, línea genética, fecha de inicio, sexo/cantidades— salen del plan estructurado que `R-152` define; sin plan no hay de dónde derivarlos) + **`HARD_FUNCTIONAL`** (invierte el orden vigente: hoy la importación **exige** un lote; la creación automática exige que la importación pueda registrarse sin lote y lo produzca) | ambas fuentes lo confirman: `H360A-03` («no implementado») y `LOT_OPTIONAL_EVENTS` | **no** antes de `R-152`; y **no** sin decisión (§4) | **sí: `AOD-25`** | — | — |

**Conclusión de dependencia**: `R-153` depende materialmente de `R-152` (`HARD_DATA_MODEL` + `HARD_FUNCTIONAL`) → el orden `R-152 → R-153` está
justificado por prueba, no por posición en el backlog. Además `R-153` no es ejecutable en esta tranche por falta de semántica (§4).

## 3. Significado exacto (respuesta al `§1` del prompt)

```
R-152 exact meaning ......... la importación de abuelas se registra como un evento genérico sin esquema: el plan de importación que docs/02 §3.4.1
                              enumera (22 campos) no se captura con tipo, no se valida (ninguna identidad entre comprada/embarcada/recibida/mortalidad
                              en traslado ni entre recibida y ♂/♀), no se concilia (país, proveedor, OC, fechas, cuarentena) y sus cinco clases de
                              adjuntos no se distinguen (`evidence_type` = photo|document por MIME). No es «activar Progenitoras»: la unidad ya existe,
                              está habilitada por empresa, concedida por usuario y certificada en acceso (GA-REM-040-G/H: AC-W05, AC-W15, AC-L02, AC-L14).
R-153 exact meaning ......... nada crea el lote de abuelas al «completar» la importación; el operador lo crea antes, a mano (POST /lots), y la importación
                              se registra sobre él (doble captura de granja/galpón/línea genética/fecha).
R-153 depends on R-152 ...... YES (HARD_DATA_MODEL + HARD_FUNCTIONAL)
```

## 4. Puerta de decisión de `R-153` (`§43`)

El repositorio **no define** (niveles 1-4): (a) qué es «completar la importación» — el registro del evento, su aprobación (`P-07`), la llegada
(`arrival_date`) o el fin de la cuarentena; (b) el **código** del lote creado automáticamente (`lot_code` es único y visible al usuario; ninguna
fuente da la regla) ni sus atributos derivados (fecha de inicio = ¿llegada?; sexo del lote); (c) si la importación **puebla** el lote (hoy la población
entra por `bird_reception`, `P-01` paso 4 certificado con `BR-18`; poblar desde la importación duplicaría la entrada o exigiría suprimir el paso 4); (d) la
convivencia con la creación manual (`POST /lots`, `docs/15`, `P-01` certificado) y con el contrato vigente «la importación exige lote». Las cuatro cambian el
comportamiento de negocio y la captura → **`OWNER_DECISION_REQUIRED` (`AOD-25`)**. Sin código para `R-153`.

## 5. Modo

```
R-152 ...... ACTIVE · GOBERNADO (docs/02 §3.4.1 · spec.md §4.4 · RR-12 como patrón de identidad intra-evento · GA-REM-040 para la cadena de acceso) · sin decisión · P2 · ejecutable
R-153 ...... ACTIVE · NO gobernado en lo implementación-crítico · OWNER_DECISION_REQUIRED (AOD-25) · P3 · no ejecutable · depende de R-152 (HARD)
modo ....... R152_ONLY
```
