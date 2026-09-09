# MATRIZ DE SISTEMA DE REGISTRO Y AUTORIDAD

**Auditoría 360°** · 2026-09-09 · base `7310adb` · **AUDIT ONLY**

Principio del encargo y de la Recomendación central §0: **Global Avícola no es un ERP paralelo.**
SAP S/4HANA es mandante transaccional; la app captura, valida, evidencia, aprueba, traza,
calcula KPI, prepara eventos y concilia. Esta matriz recorre **cada recurso** y contesta:
quién es dueño según la fuente de mayor nivel, qué hace la app hoy, y si eso es correcto,
placeholder aceptable, desviación o decisión pendiente.

Clasificaciones: `SAP_MANDANTE` · `APP_MANDANTE` · `ESPEJO_LECTURA` (copia importada, solo consulta)
· `LOCAL_PLACEHOLDER` (maestro local que SAP sustituirá; `SAP_DEFERRED`) · `DESVIACIÓN` (la app
decide algo que no le corresponde) · `OWNER_DECISION_REQUIRED`.

---

## 1. Maestros

| Recurso | Dueño (fuente) | En la app (`7310adb`) | Clave externa | Quién lo edita hoy | Clasificación | Hallazgo |
|---|---|---|---|---|---|---|
| Materiales — alimento | SAP MM (Rec. §1, §5, §15) | `feed_types` (`company_id, name, code, presentation`) | `code` texto libre, opcional | `masters:create/update/delete` | `LOCAL_PLACEHOLDER` **sin vínculo** a `sap_references.MATERIAL` | `H360-S01` |
| Materiales — vacunas | SAP MM | `vaccines` (`laboratory, vaccine_type, standard_dosage:String, application_route`) | **ninguna** | ídem | `LOCAL_PLACEHOLDER` sin clave | `H360-S01` |
| Materiales — medicinas | SAP MM | `medications` (`laboratory, presentation`) | **ninguna** | ídem | `LOCAL_PLACEHOLDER` sin clave | `H360-S01` |
| Materiales — aves por raza/sexo, huevo fértil, pollito nacido (Rec. §5) | SAP MM | no existen como material; la app usa `genetic_lines`/`breeds` + `sex` | — | — | `SAP_DEFERRED` (mapeo evento→material inexistente) | `H360-S02` |
| Proveedores | SAP Business Partner (Rec. §15) | `suppliers.sap_code` opcional **y** `sap_references.VENDOR` importable | `sap_code` | `masters:*` | **doble representación** sin regla de precedencia | `H360-S03` |
| Órdenes de compra / transferencia | SAP MM (Rec. §1, §8) | `sap_references` (`PURCHASE_ORDER`, `TRANSFER_ORDER`, `quantity`) importadas por `POST /sap/references/import` (CSV/JSON manual) | `sap_code` | `sap:send_sap` (importa) | `ESPEJO_LECTURA` ✓ | OC validada en recepción (`BR-18`); **OT no validada** en `feed_registration` (`sap_document_ref` texto libre) → `H360-S04` |
| Inventario / stock | SAP IM/EWM | inexistente; sin validación consumo ≤ stock (Rec. §17) | — | — | `SAP_DEFERRED` correcto (la app no decide inventario) | consulta de inventario disponible (Rec. §2) ausente |
| Almacenes / silos | SAP | sin modelo; `sap_references.STORAGE_LOCATION` importable pero **ningún evento lo referencia** | — | — | `SAP_DEFERRED` | alimento sin silo/almacén destino (Rec. §8) |
| Sociedad / empresa | SAP (Rec. §4 «Empresa → Sociedad SAP») | `companies` (`name, tax_id, country, currency, sap_config, approval_levels`) | **ninguna** (sin código de sociedad) | `masters:*` sobre `CONTROL_GLOBAL` (`OD-14`) | `OWNER_DECISION_REQUIRED` (`R-124`) | `AOD-06` |
| Centro / planta / granja | SAP (Rec. §1, §15 «Granjas → Maestro SAP») **vs** `docs/02 §3.2.1` local | `farms` (`code` opcional, `farm_type`) | `code` texto libre | `masters:*` | `REQUIREMENT_CONFLICT` · `R-124` | `AOD-06` |
| Galpón y capacidad | SAP PM/EAM/custom (Rec. §15) | `houses.capacity` local; `BR-17` valida contra ella | ninguna | `masters:*` | `LOCAL_PLACEHOLDER` con decisión pendiente (Rec. §25.2) | `AOD-02` |
| Incubadoras / nacedoras / plantas de incubación | SAP PM/EAM | `hatcheries`, `incubators`, `hatchers` (capacidad local) | ninguna | `masters:*` | `LOCAL_PLACEHOLDER` | — |
| Equipos por galpón | SAP PM/EAM (Rec. §3.4) | inexistente; inspección con `parameter/value` libre | — | — | `SAP_DEFERRED` | G-R11 vigente |
| Centros de costo / objetos CO | SAP CO | `sap_references.COST_CENTER` importable, **sin uso** en eventos ni payload; `areas` son áreas funcionales (`GA-REM-039`), no centros de costo | — | — | `SAP_DEFERRED` | payload sin objeto de costo → `H360-S08` |
| Lote productivo oficial | SAP CO/custom (Rec. §3.3 «eje de trazabilidad y costeo», §15, §25.3) | `lots` (`lot_code` único local, `bird_type, sex, status, activation_type`) **sin ninguna columna `sap_*`**; `sap_references.SAP_BATCH` importable sin FK | **ninguna** | `lots:*` | `LOCAL_PLACEHOLDER` **sin clave externa** — la app antigua sí tenía «Id SAP» (PDF Sap y App p.16) | `H360-S05` · `AOD-03` |
| Líneas genéticas / razas / curvas de peso | app (no aparece en Rec. §1; Rec. §5 las modela como clasificación de material) | `genetic_lines`, `breeds`, `genetic_weight_curves(+points)` | — | `masters:*` | `APP_MANDANTE` con referencia de dominio | ✓ |
| Fases productivas | app | `productive_phases` (`CORE`) | — | `masters:*` | `APP_MANDANTE` | ✓ |
| Causas de mortalidad / descarte, tipos de corrección, motivos de rechazo, transportes, plantas de beneficio | app (catálogos operativos) | tablas locales por empresa | — | `masters:*` | `APP_MANDANTE` | ✓ · plantas de beneficio podrían ser Centro SAP (decisión no urgente) |
| Períodos abiertos | SAP FI/CO (Rec. §15) | `BR-19`: 90 días fijos en código (`validators.py:485-497`) | — | — | `LOCAL_PLACEHOLDER` **hard-coded** | `H360-S06` |
| Usuarios autorizados | Rec. §15: SAP/IAM · `docs/02`: local | `users`, `roles`, `permissions`, `user_business_units` locales (`OD-13`, `OD-15`) | — | `users:*`, `business_units:*` | `REQUIREMENT_CONFLICT` | `AOD-07` |

## 2. Transacciones y documentos

| Recurso | Dueño | En la app | Clasificación | Hallazgo |
|---|---|---|---|---|
| Documento de material, entrada/salida de mercancía, verificación de factura, asientos | SAP (Rec. §3.6 «FI no recibe nada directo») | no existen; la app no crea documentos ni asientos | `SAP_MANDANTE` respetado ✓ | — |
| Reversos / anulaciones de documentos SAP | SAP (Rec. §1, §21) | `reversals` tabla sin servicio/ruta; `cancel` solo pre-aprobación | `SAP_MANDANTE` — pero `BR-16` (ajuste post-SAP mediante reverso) **no tiene mecanismo en la app** | `H360-P05` |
| Cierre contable / logístico / de períodos | SAP | ninguno ✓ | `SAP_MANDANTE` | — |
| Cierre / liquidación del lote | SAP «cerrar lotes» (Rec. §21) · app «datos de cierre» (Rec. §13) | `POST /lots/{id}/close`: `status=closed`, resumen (mortalidad, alimento, huevos, eventos), `BR-05`, `R7` | **cierre operativo local**, no declarado como distinto de la liquidación SAP | `AOD-08` |
| Costeo / valoración | SAP CO | ninguno ✓ | `SAP_MANDANTE` | — |
| Evento operativo (captura) | **app** (Rec. §2, §21) | `operational_events` + movimientos; 26 tipos; 13 estados | `APP_MANDANTE` ✓ | — |
| Validación operativa | app (Rec. §17) | `BR-01…BR-19` parciales; ver `OPERATIONAL_PROCESS_STATE_AND_CLOSURE_MATRIX §4` | `APP_MANDANTE` parcial | `H360-P01`, `H360-B01…B03` |
| Evidencia | app (+DMS opcional) | `evidences` + volumen `avicola-media` | `APP_MANDANTE` ✓ | obligatoriedad sin regla → `H360-B04` |
| Aprobación administrativa | app | `review/*`, `approvals/*`, `approval_steps`, `BR-14` configurable (`RC-03`) | `APP_MANDANTE` ✓ | — |
| Trazabilidad operativa y auditoría | app | `audit_logs` (listeners), `egg_batches`, `chick_batches` | `APP_MANDANTE` ✓ | inmutabilidad solo de aplicación → `H360-D04` |
| KPI | app | `reports/*`, `dashboard/*` | `APP_MANDANTE` con **defectos de fórmula** | `KPI_FORMULA_AND_DATA_SOURCE_MATRIX` |
| Envío a SAP (preparación) | app prepara; SAP recibe | `consolidated_movements` → `sap_payloads` → adaptador manual/mock | `APP_MANDANTE` de la **preparación**; entrega `BLOCKED_EXTERNAL` (`P-08`, `GA-REM-017`) | `SAP_INTEGRATION_READINESS_AUDIT` |
| Conciliación app ↔ SAP | app (Rec. §24, §26) | `GET /reports/sap-comparison` clasifica eventos propios por estado; no lee SAP | `SAP_DEFERRED` | G-R10 vigente |

## 3. Semántica de los tres objetos que más se confunden

| Objeto | Qué es en la app | Qué es en SAP (Rec.) | Regla vigente | Riesgo si no se declara |
|---|---|---|---|---|
| **Empresa** | inquilino (`company_id` en 44 de 54 tablas; `TENANT_RESOURCE_CLASSIFICATION.md`) y unidad de control global (`OD-14`) | Sociedad | `OD-11`, `OD-14` | crear empresas en la app sin código de sociedad impide cualquier conciliación futura |
| **Granja** | maestro local por empresa, con `farm_type` y galpones | Centro o atributo operativo «según tamaño» (Rec. §4) | ninguna sobre origen → `R-124` | granjas locales y centros SAP con nombres distintos → eventos inatribuibles |
| **Lote** | agregado central local: `lot_code` único global, `bird_type`, `sex`, `status`, fases, saldo de apertura | lote productivo oficial: batch / orden interna / orden de producción / custom (Rec. §25.3, **decisión pendiente**) | ninguna | «cada recepción de aves debe terminar asociada a un lote productivo oficial en SAP» (Rec. §3.3) es hoy **imposible**: el lote no guarda identificador SAP |

## 4. Funciones prohibidas por la Recomendación §2 — comprobación

| Prohibido a la app | ¿La app lo hace? | Evidencia |
|---|---|---|
| Crear OC | No — solo importa referencias | `sap/router.py`: no hay creación de OC |
| Crear materiales | **Sí, localmente** (`feed_types`, `vaccines`, `medications` con `masters:create`) | son placeholders; la desviación nace si se consideran maestro definitivo → `H360-S01` |
| Crear almacenes | No (no hay modelo) | — |
| Cambiar costos | No | — |
| Ajustar inventario sin documento SAP | No (no hay inventario) | — |
| Cerrar órdenes | No (`OD-04`: sin cierre automático de OC) | `validators.py` docstring de `validate_oc_limit` |
| Modificar datos aprobados sin reverso | **Parcialmente posible**: `POST /operations/{id}/cancel` rechaza `APPROVED, CONSOLIDATED, SENT_TO_SAP` pero **no** `SAP_CONFIRMED` ni `SAP_ERROR` (`operations/service.py:923`) | latente: esos estados son inalcanzables hasta `GA-REM-017` → `H360-P04` |

## 5. Veredicto

La app **respeta** el principio en lo financiero-logístico (no crea documentos, no toca
inventario, no costea, no cierra períodos). **No lo respeta todavía** en la capa de identidad
de maestros: materiales, lote productivo, granja y sociedad viven sin identificador SAP, de modo
que la frase «enviar a SAP solo datos aprobados, trazables e idempotentes» se cumple en
*aprobados* e *idempotentes* y falla en *trazables hacia SAP*. Eso es lo que convierte a
`AOD-01…06` en decisiones previas a cualquier `WAVE D`.
