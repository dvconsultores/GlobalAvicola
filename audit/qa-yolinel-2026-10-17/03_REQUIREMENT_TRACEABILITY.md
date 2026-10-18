# 03 · Trazabilidad de requisitos — Revisión QA 2026-10-17

**Documento**: trazabilidad de cada hallazgo a su fuente contractual y conclusión (`CUBIERTO` / `HUECO` / `DECISIÓN`)
**Fecha**: 2026-10-18 · **Baseline de código**: `83c9cd8`
**Spec**: `specs/008-qa-yolinel-findings-remediation/spec.md` · **Clasificación**: `02_FINDINGS_CLASSIFICATION.md` · **Código**: `04_CODE_VALIDATION.md`

Convención de conclusión:

| Conclusión | Significado |
|---|---|
| `CUBIERTO` | El contrato define la regla y el código la implementa (o el modelo la hace imposible). Solo falta explicarla |
| `HUECO` | El contrato no define nada y el código no implementa; requiere diseño + implementación |
| `DECISIÓN` | El contrato no define (o define de forma ambigua) y la política es del Owner |

---

## Tabla de trazabilidad

| ID | Fuente contractual | Qué dice la fuente | Qué hace el código | Conclusión |
|---|---|---|---|---|
| **QA-001** | **GA-REM-040** (acceso por unidad de negocio) · `docs/02` (modelo de granjas/galpones/lotes) · `SPEC 005 data-model` (`business_unit_code` **informativo**) | Una granja aloja galpones de **varias** unidades; la unidad no se fija por granja sino por **cadena del lote**. `business_unit_code` en referencias SAP es informativo, no una FK de dominio | `business_units/scope.py:45-69` deriva la cadena de `lots.bird_type`; `route_scope.py` clasifica Hatchery como unidad única `hatchery`; no hay columna BU en `Farm`/`Hatchery` (`masters/models.py:79, 83, 110-113`) | **CUBIERTO** (documentar) |
| **QA-002** | **OD-24** (Empresas/Granjas espejo SAP de solo lectura cuando exista **P-08**) · `docs/02` (maestros y baja lógica) | Los maestros no se borran: se desactivan. Los que provienen de SAP serán espejo de solo lectura cuando P-08 exista | DELETE ⇒ `is_active=False` (`masters/router.py:69-81`, `masters/service.py:267-272`); no hay borrado físico ni huérfanos | **CUBIERTO** en BE · **HUECO** de UX (rótulo/estado/error) ⇒ FR-04 |
| **QA-003** | `docs/02` (maestros de sanidad: vacunas, medicamentos, causas) · `SPEC 005` (catálogos SAP) | No se exige **código único**; la identificación es por nombre descriptivo. Ninguna fuente define unicidad | Modelos con `name` obligatorio y **sin unique** por empresa; atributos descriptivos existen (laboratorio, tipo, vía, principio activo, descripción) | **CUBIERTO** (identificación por nombre) · **DECISIÓN** OD-QA2-01 (unicidad/código) · **HUECO** de UX de columnas ⇒ FR-02 |
| **QA-004** | **GA-REM-039** (Área = estructura **organizativa**) · `docs/02` (plantas de incubación) | Área organize la empresa; **no** es una zona física de planta. No se replica el modelo de granja en incubación | `Hatchery.location` es texto libre (`masters/models.py:110-113`); no hay `area_id`; `Farm` sí tiene `farm_type`/`company_id` (`:79, :83`) | **DECISIÓN** OD-QA2-02 |
| **QA-005** | **SPEC 005** (HANA read-only inbound) · `docs/12` (arquitectura de integración) · `SPEC 005 data-model` | Cadena **HANA READ ONLY → RAW → VALIDATION → MAPPING → STAGING → PROMOCIÓN CONTROLADA** a `sap_references`; **14 objetos**; solo una parte se promueve, el resto queda staging-only; `business_unit_code` se promueve para `PLANT` | `inbound/models.py:164-171` (staging), `promotion.py:109-116, 246-256` (promoción con `business_unit_code` solo en `PLANT`) | **CUBIERTO** (documentar la cadena y el alcance de la promoción) |
| **QA-006** | `docs/02` (origen de lote) · **SPEC 006** (Cargas Iniciales / cutover) · **SPEC 005** (inbound solo referencias) | Lotes `NATIVE` (alta manual, importación de abuelas) o `MIGRATED` (Cargas Iniciales/cutover). El inbound SAP **no crea lotes**, solo referencias | `lots.origin` en el modelo de lotes; `activation_type` normal/manual; el flujo inbound no escribe en `lots` | **CUBIERTO** (documentar) |
| **QA-007** | `docs/02` (recepción de aves / OC SAP) · **BR-18** (límite de OC) · **SPEC 005 data-model** (`SapEntityMapping` PLANT→`business_unit_code`) · **GA-REM-040** | La OC debe corresponder a la cadena del lote. La fuente **no dice explícitamente** que la OC determine la cadena, pero existe el dato determinista centro(WERKS)→unidad vía mapping PLANT | `validate_oc_limit` (`validators.py:908-948`) valida **empresa + cantidad acumulada** y **no** cadena; `/sap/references` (`sap/service.py:153-163`) filtra solo por empresa | **HUECO** ⇒ implementar **BR-23** (regla mínima, FR-01) · política «desconocida ⇒ bloquear» = **DECISIÓN** |
| **QA-008** | `docs/02` (recepción de aves: campos obligatorios) · **SAP-STO-01** (`LGORT`↔galpón) `PENDING` · **OD-24 / AOD-02** (clasificación WERKS↔granja `PENDING`) | Solo referencia, cantidad y proveedor pueden derivarse de la OC mientras no exista mapping aprobado de almacén/planta | Autocompletado limitado a referencia/cantidad declarada/proveedor (texto); granja/galpón/lote/transporte/fecha son del usuario | **DECISIÓN** OD-QA2-03 · documentar matriz (AC-08.6) |
| **QA-009** | `docs/02` (procesos operativos; **no** impone orden temporal explícito) · `docs/12` (**R3/R4**, **BR-01..BR-04** reglas de saldo) | El contrato regula **saldos** y estado del lote, no una secuencia de predecesores | No existe catálogo de predecesores en backend; `frontend/src/data/processCatalog.ts` contiene la secuencia solo como UI; validadores aplican saldo, lote activo y fecha | **HUECO** (backend) · **DECISIÓN** OD-QA2-04 → matriz propuesta, sin implementar |
| **QA-010** | **BR-14** (aprobación por niveles) · `docs/12` (workflow de revisión) | Define transiciones de revisión/aprobación, corrección y reverso con contrapartida | Implementado en `review/service.py` (aprobación, corrección, cancelación, reverso); la máquina no está documentada en `docs/` | **CUBIERTO** (documentar `OPERATION_STATE_MACHINE.md`) |
| **QA-011** | **RR-03** / **R-143** (segregación de funciones) · **BR-14** · `docs/12` | `require_segregation` configurable por empresa; se excluye a registrador, corrector y a quien rechazó; el supervisor que revisó puede aprobar | `review/service.py:35-90` aplica las exclusiones y responde 403 (R-143); tests `test_segregation_r143` g01-g06 y E2E `proceso-03` | **CUBIERTO** (documentar) · nota: `require_segregation=False` también desactiva exclusiones de corrector/rechazador (**inferencia**, confirmar) |
| **QA-012** | `docs/02` (jerarquía Granja→Galpón; Planta→Incubadora/Nacedora) | Existe relación padre-hijo entre granja/galpón y planta/incubadora/nacedora | Relación en el modelo; el listado no muestra el nombre del padre | **HUECO** de UX ⇒ FR-03 |
| **QA-013** | `docs/02` (columnas de cada maestro) · estándar i18n del proyecto (`common.*` = acciones) | Cada campo debe mostrarse con su nombre; las claves `common.*` son de acción | 20 de 42 columnas usan `common.edit`/`common.save` para campos de datos | **HUECO** (defecto de implementación) ⇒ FR-02, P1 |
| **QA-014** | `docs/02` (listados con granja/planta) · **GA-REM-040** (contexto de unidad por lote) | El usuario debe poder ubicar el registro por granja/planta | Contratos de lectura devuelven solo ids (`lots/schemas.py:77-86`, `operations/schemas.py:269-279`) | **HUECO** de UX/contrato ⇒ FR-07 |
| **QA-015** | `docs/02` (filtros de listados) · **GA-REM-040** | Filtrar por granja es esperable; filtrar por planta de incubación requeriría modelo/consulta no definida | `/operations` acepta `farm_id/date_from/date_to/status` (`operations/router.py:42-71`); `/lots` `farm_id/status` (`lots/router.py:23`); **no existe** `hatchery_id` | **HUECO** de UI (farm, fácil) · **HUECO** funcional (hatchery, sin contrato) ⇒ documentar |
| **QA-016** | **BR-19** · **GA-REM-023 R-30 / AC13** (fecha de evento no futura) · **RR-09** (ninguna fuente exige validar futuro en fechas planificadas) | `event_date` no puede ser futura; `start_date`/`activation_date`/`cutover_datetime` no tienen exigencia de validación | Backend rechaza futuro solo en `event_date` (`validators.py:951-976`); ningún form FE aplica `max=` | **CUBIERTO** en BE · **HUECO** de UX (`max=hoy`) · **DECISIÓN** OD-QA2-05 (fechas planificadas) |
| **QA-017** | `docs/12` (uso de recursos / comportamiento de UI) · estándar React del proyecto (dependencias de efectos estables) | La UI no debe generar peticiones en bucle | `ReviewCenter.tsx` depende de `can` (recreado por `useCan` en cada render) y de `toast` ⇒ `useEffect` re-ejecutado por cada `setState` | **HUECO** (defecto de implementación) ⇒ FR-05, P1 |
| **QA-018** | `docs/12` (auditoría y trazabilidad de registros) · `docs/02` (listados operativos) | Todo registro debe ser atribuible a un usuario y a un instante de creación, distinguible de la fecha del evento | `created_by`/`created_at` existen en el modelo, no se exponen ni se muestran en esos listados | **HUECO** de UX/contrato ⇒ FR-07 |

---

## Resumen por conclusión

| Conclusión | Total | Hallazgos |
|---|---|---|
| `CUBIERTO` | **5** | QA-001, QA-005, QA-006, QA-010, QA-011 (comportamiento correcto; falta explicarlo) |
| `HUECO` | **11** | QA-002 (UX), QA-003 (UX), QA-007 (BE), QA-009 (BE), QA-012, QA-013, QA-014, QA-015, QA-016 (UX), QA-017, QA-018 |
| `DECISIÓN` | **5** | QA-003 (unicidad), QA-004, QA-008, QA-009 (política de predecesor desconocido), QA-016 (fechas planificadas/cutover) |
| `QA_MISUNDERSTANDING` | **0** | — |
| **Hallazgos únicos** | **18** | 5 + 11 + 5 = 21 lecturas con solapamiento (5 hallazgos son `HUECO` y `DECISIÓN` a la vez o lo combinan: QA-003, QA-007, QA-009, QA-016) |

> Las conclusiones se combinan igual que las etiquetas: un hallazgo puede ser `CUBIERTO` en backend y `HUECO` en frontend (QA-002, QA-003, QA-016), o `HUECO` + `DECISIÓN` (QA-007 política, QA-009 política).

## Fuentes contractuales citadas (inventario)

| Fuente | Uso en esta trazabilidad |
|---|---|
| **GA-REM-040** | Acceso por unidad de negocio; una granja con galpones de varias unidades; cadena derivada de `lots.bird_type` (QA-001, QA-007, QA-014, QA-015) |
| **GA-REM-039** | Área como estructura organizativa, no zona física (QA-004) |
| **GA-REM-023 R-30 / AC13** | Fecha de evento no futura (QA-016) |
| **RR-09** | Ninguna fuente exige validar futuro en fechas planificadas (QA-016) |
| **RR-03 / R-143** | Segregación de funciones y su bloqueo 403 (QA-011) |
| **BR-14** | Aprobación por niveles, corrección y reverso (QA-010, QA-011) |
| **BR-18** | Límite de OC por empresa y cantidad acumulada (QA-007) |
| **BR-19** | Fecha de evento no futura en backend (QA-016) |
| **SPEC 005 / data-model** | Cadena HANA→RAW→VALIDATION→MAPPING→STAGING→promoción; 14 objetos; `SapEntityMapping(PLANT).business_unit_code` **informativo** (QA-001, QA-005, QA-007) |
| **SPEC 006** | `lots.origin=MIGRATED` por Cargas Iniciales/cutover (QA-006) |
| **SPEC 007** | Dataset QA de referencia para pruebas de esta ronda (contexto de pruebas) |
| **OD-24 / AOD-02** | Espejo SAP de solo lectura (P-08) y clasificación de plantas `PENDING` (QA-002, QA-008) |
| **SAP-STO-01** | `LGORT`↔galpón `PENDING` (QA-008) |
| **`docs/02`** | Reglas de negocio, modelo de maestros, recepción de aves, procesos operativos (todos) |
| **`docs/12`** | Arquitectura, reglas R1/R2/R3/R4, workflow y uso de recursos (QA-009, QA-010, QA-017, QA-018) |

## Notas de contraste pendiente

1. El PDF «REVISION GENERAL DE SISTEMA GLOBAL AVICOLA - 17-10-2026.pdf» **no está disponible**; las citas de `docs/02` y `docs/12` son de contrato vigente, no de las capturas QA. Si al contrastar el PDF aparece una regla no documentada, esta tabla debe reabrirse.
2. `business_unit_code` de `SPEC 005 data-model` se usa aquí en su carácter **informativo**: no crea autoridad de dominio sobre la cadena del lote (eso sigue siendo `lots.bird_type`).
3. La conclusión `DECISIÓN` no equivale a ambigüedad del contrato: son políticas que el contrato deja explícitamente al Owner.
