# MATRIZ DE COBERTURA — PROGENITORAS (`grandparent`)

**Addendum Master 360 · WAVE A0-P** · 2026-09-09 · base `7ee72a1` · **sin código**

Regla: **Progenitoras ≠ Reproductoras**; nada se da por cubierto por parecerse a `breeder`.
Fuente de requisito: `spec.md §4.4` (15 `event_type`), `docs/02 §3.4` (plan de importación y
creación automática del lote), `GA-REM-040 §2`, `OD-16`. Ross/Cobb y el PDF «Sap y App» son
referencia de dominio, no requisito. Estados: `COMPLETE` · `PARTIAL` · `MISSING` · `BLOCKED` ·
`NOT_APPLICABLE` · `OWNER_DECISION_REQUIRED`.

Rastro temporal: `BirdTypeEnum.GRANDPARENT` existe desde el commit inicial `3c93440` (2026-06-23);
`HATCHERY` se añadió en `d3f37f8` (2026-06-24). `spec.md §4.4` y `docs/02 §3.4` lo gobiernan desde
la redacción inicial; `docs/15:20` lo marca como «NUEVO» respecto de la app anterior. `docs/03:124`
sigue listando **tres** valores (`GRANDPARENT, BREEDER, BROILER`) — deriva documental (`H360A-07`).

| Requisito | Fuente | Modelo | Backend | API | Frontend | KPI | Test | E2E | Evidencia | Estado |
|---|---|---|---|---|---|---|---|---|---|---|
| Plan de importación (OC SAP, proveedor internacional, país, línea genética, sexo, cantidades comprada/embarcada/recibida, mortalidad en traslado, 5 adjuntos, fechas, transporte, cuarentena, inspección inicial) | `docs/02 §3.4.1` · `spec §4.4` `grandparent_import` | `EventType.GRANDPARENT_IMPORT`; evento genérico: `sap_document_ref`, `supplier_id`, `extra_data` JSON, `evidences` | sin rama propia (`operations/service.py` no lo distingue) | `POST /operations` | `OperationFormPage` (tipo listado) | n/a | `test_full_workflow_audit` | `proceso-p01` paso 1 (`sap_document_ref` + `extra_data.supplier`) | `PROCESS-01` paso 1 PASS | **`PARTIAL`** — campos de `docs/02 §3.4.1` sin estructura ni validación → `H360A-02` |
| Creación automática del lote de abuelas al completar la importación | `docs/02 §3.4.2` | — | no existe (el lote se crea por `POST /lots`) | — | `LotFormPage` manual | n/a | — | p01 crea el lote a mano | — | **`MISSING`** → `H360A-03` |
| Recepción de aves (cantidad, sexo, peso) con control de OC y capacidad | `spec §4.4` | `bird_reception` + `bird_movements(sex, quantity, avg_weight)`; `BR-17`, `BR-18` | `validate_house_capacity`, `validate_oc_limit` | `POST /operations` | ídem | — | `test_purchase_order_limit`, `test_business_units` | p01 «OD-04 entregas parciales» | `PROCESS-01` pasos 3-4 | `COMPLETE` |
| Cría (rearing) | `spec §4.4` · etapa `grandparent_rearing` | `lot_phases`; `processCatalog` etapa | genérico | genérico | `navigationConfig gp_rearing`, `PoultryStagePage` | — | — | p01 «cadena completa» | `PROCESS-01` 12/12 | `COMPLETE` |
| Población (saldo nunca negativo) | invariante · `BR-01` | `get_current_bird_balance`: `bird_reception`/`birth_registration` entran; `grandparent_import` **no** entra (documental) | `validate_mortality` solo | — | — | — | `test_bird_balance*` | p01 | — | **`PARTIAL`** — descarte y salida sin validar (`H360-P01`); la importación como evento documental es coherente con p01, que puebla con `bird_reception` |
| Macho / hembra | `spec §4.4` | `bird_movements.sex`, `Lot.sex` | ✓ | ✓ | ✓ | — | ✓ | p01 usa `mixed` | — | `COMPLETE` (evidencia E2E solo con `mixed` → nota) |
| Asignación a galpones | `spec §4.4` `bird_distribution` | `target_house_id`, `BR-17` | ✓ | ✓ | ✓ | — | ✓ | p01 paso 5 | `PROCESS-01` | `COMPLETE` |
| Pesajes semanales (♂/♀, semana) | `spec §4.4` | `weight_recording`, `sample_size`, `week_number` | ✓ | ✓ | ✓ | uniformidad, IPE | ✓ | p01 paso 7 | `PROCESS-01` | `COMPLETE` |
| Pesos objetivo | `spec §4.12` (vs estándar) · `GA-REM-037` | `genetic_weight_curves` por línea genética (no por unidad) | `weight-evaluation`, alerta `weight_deviation` | ✓ | `WeightCurvesPage` | ✓ | `test_weight_curve*` | p03 curvas UI (reproductoras) | `GA-REM-037` | `COMPLETE` (genérico; el requisito no exige curva específica de progenitoras) |
| Uniformidad | `spec §4.12` | CV entre pesajes | `get_kpi_weight_uniformity` | ✓ | `ReportsPage` | ✓ | ✓ | — | — | `PARTIAL` — definición abierta (`AOD-10.d`) |
| Clasificación de aves / condición corporal / recuperación | ninguna fuente de nivel 1-4 | — | — | — | — | — | — | — | — | `NOT_APPLICABLE` (no se inventa requisito desde manuales) |
| Alimento | `spec §4.4` | `feed_registration`, `quantity_kg`, `week_number` | ✓ | ✓ | ✓ | FCR (`H360-K01`) | ✓ | p01 paso 6 | `PROCESS-01` | `COMPLETE` según spec; huecos del cliente (`H360-B03`) son transversales |
| Agua | `Bases` p.2 (cría) | — | — | — | — | — | — | — | — | **`MISSING`** — `R-13` / `GA-REM-021` (`H360-B05`), aplica a esta unidad |
| Mortalidad | `spec §4.4` | `mortality_recording`, `cause_id`, `sex` | `BR-01` | ✓ | ✓ | % (`H360-K02`) | `GA-REM-005` | p01 paso 8 | `PROCESS-01` | `COMPLETE` (captura) · KPI `PARTIAL` |
| Descarte | `spec §4.4` `cull_recording` | `cull_cause_id` | **sin validación de saldo** | ✓ | ✓ | — | — | p01 paso 9 | `PROCESS-01` | `PARTIAL` (`H360-P01`) |
| Vacunación / medicación | `spec §4.4` | `vaccine_id`, ruta, lote, dosis; `medication_id`, días | ✓ | ✓ | ✓ | vacunación (`H360-K03`, aplica a incubadora) | ✓ | p01 pasos 10-11 | `PROCESS-01` | `COMPLETE` |
| Salud y ambiente | `spec §4.4` `farm_inspection`, `transport_inspection` | `inspection_details`, alertas T°/H° | ✓ | ✓ | ✓ | bienestar (`H360-K05`) | ✓ | p01 pasos 2-3 | `PROCESS-01` | `COMPLETE` (umbrales fijos: `H360-B07`) |
| Traslados entre galpones | `bird_transfer` (`RC-02` neutro) | ✓ | ✓ | ✓ | ✓ | — | ✓ | — | — | `COMPLETE` |
| Transición de fase (cría → producción) | `spec §4.9` (fases) · etapas `grandparent_rearing/production` | `lot_phases`, `POST /lots/{id}/phases` | ✓ | ✓ | `processCatalog` 2 etapas | — | `test_lots*` | **ninguna E2E de progenitoras la recorre** | — | `PARTIAL` (evidencia) → `H360A-08` |
| Producción de huevo (recolección, clasificación, despacho a reproductoras) | `spec §4.4` `egg_collection/classification/dispatch` | `egg_movements`, `BR-02` | ✓ | ✓ | `gp_production` | fertilidad (`AOD-10.a`) | ✓ | `proceso-p02` 9 casos | `PROCESS-02` `CERTIFIED` | `COMPLETE` |
| Trazabilidad hacia reproductoras | `spec §4.4`, `§4.9` | `egg_batches.generation='grandparent'`; `handoff.FLUJOS` (`grandparent`→`hatchery`; `hatchery`→`breeder`) | ✓ | `POST /lots/egg-batches` | `TraceabilityTree` | — | `test_traceability*`, `test_handoff*` | `proceso-p10` | `PROCESS-10` | `COMPLETE` |
| Salida definitiva | `spec §4.4` `bird_exit` | `destination_*` | **sin validación de saldo** | ✓ | ✓ | — | — | p01 paso 12 | `PROCESS-01` | `PARTIAL` (`H360-P01`) |
| Cierre operativo del lote | `BR-05`, `GA-REM-029/036` | `POST /lots/{id}/close` | ✓ | ✓ | `LotDetailPage` | — | `test_lot_closure` | **no en p01** (termina en `bird_exit`) | — | `PARTIAL` (evidencia E2E) → `H360A-08` |
| KPI aplicables | `spec §4.12` · `Bases` (sin sección propia de progenitoras) | genéricos por lote | `reports/*` | ✓ | `ReportsPage` | mortalidad, FCR, uniformidad, IPE, huevo | `P-15` | p15 | `PROCESS-15` | `PARTIAL` — defectos genéricos `H360-K01/K02` |
| Revisión, corrección, aprobación | `P-07` | genérico | ✓ | ✓ | ✓ | — | ✓ | `proceso-03` | `PROCESS_CERTIFICATION_MATRIX` | `COMPLETE` (transversal) |
| Traza SAP futura (lote productivo oficial, materiales por raza/sexo) | Recomendación §3.3, §5, §25.3 | `sap_document_ref` en eventos; **`lots` sin id SAP** | — | — | — | — | — | — | — | `BLOCKED` → `H360-S05` / `AOD-03` |
| Acceso por unidad de negocio | `GA-REM-040`, `OD-16` | `business_units.code='grandparent'`; clasificación por `bird_type`; `route_scope` | `unidades_efectivas` | fase 7/8 | `navigationConfig` estático (asume las cuatro) | — | 7 archivos de test la mencionan | 3 E2E la usan | fases 1-8 | `PARTIAL` — plataforma sí; certificación de acceso por proceso `PENDIENTE` (`0/15`); interfaz no lee la sesión (`H360A-01`) |
| Interfaz (menú, etapas, formulario de lote) | `docs/02 §7`, `GA-REM-040 §14.3` | — | — | — | `navigationConfig` (2 etapas), `processCatalog`, `LotFormPage.BIRD_TYPES`, `PoultryHubPage`, `thermalCurves` (comparte cría con `breeder`) | — | vitest no la cubre | p03 UI curvas (no progenitoras) | — | `PARTIAL` — presente y estática; sin prueba de interfaz propia |

## Recuento

```
COMPLETE ............ 14
PARTIAL ............. 11   (población/descarte/salida · uniformidad · fase · cierre · KPI · acceso · UI · importación)
MISSING .............  2   (creación automática del lote · agua)
BLOCKED .............  1   (traza SAP)
NOT_APPLICABLE ......  1   (clasificación / condición corporal / recuperación: sin fuente)
OWNER_DECISION ......  0   propios (los abiertos son transversales: AOD-03, AOD-10)
```

**Conclusión.** Progenitoras está **definida** (spec y `docs/02`), **implementada** en su cadena
de cría y producción (`P-01` 12/12, `P-02` 9/9, `P-10`) y **disponible** en producto y en el
catálogo de unidades. Sus huecos propios son dos (`H360A-02` importación sin estructura,
`H360A-03` lote automático) y una carencia de evidencia (`H360A-08` fase y cierre sin E2E). El
resto de sus `PARTIAL` son defectos transversales ya registrados en la Master 360. Ninguno es P0.
