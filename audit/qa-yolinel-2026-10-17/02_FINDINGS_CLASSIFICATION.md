# 02 · Clasificación formal de hallazgos — Revisión QA 2026-10-17

**Documento**: clasificación de los 18 hallazgos de `01_SOURCE_FINDINGS.md`
**Fecha**: 2026-10-18 · **Baseline de código**: `83c9cd8` · **Spec asociada**: `specs/008-qa-yolinel-findings-remediation/spec.md`
**Carácter**: clasificación **técnica** derivada de contrato + código; no sustituye la certificación QA (PDF original `PENDING`)

Etiquetas usadas: `ALREADY_COMPLIANT` · `DEFECT` · `FUNCTIONAL_GAP` · `UX_IMPROVEMENT` · `DOCUMENTATION_CLARIFICATION` · `QA_MISUNDERSTANDING` · `OWNER_DECISION_REQUIRED`.
Un hallazgo puede acumular varias etiquetas.

---

## Tabla de clasificación

| ID | Observación QA (resumen) | Clasificación(es) | Justificación (contrato / código) | Acción | Prioridad |
|---|---|---|---|---|---|
| **QA-001** | ¿Granjas/Incubadoras están relacionadas con su Unidad de Negocio? | `ALREADY_COMPLIANT` + `DOCUMENTATION_CLARIFICATION` | **GA-REM-040**: una granja aloja galpones de varias unidades, por lo que **no existe FK** granja→unidad de negocio; la cadena se deriva de `lots.bird_type` mediante `business_units/scope.py:45-69`. Hatchery se clasifica como unidad única `hatchery` en `route_scope.py`. Ver `04_CODE_VALIDATION.md` (`masters/models.py:79, 83, 110-113, 295`) | Documentar el modelo y la derivación de cadena; sin cambio de código. Nota Owner: filtrar el listado de plantas de incubación por BU concedida es decisión **opcional** | — |
| **QA-002** | ¿Se puede eliminar un maestro en uso? Si viene de SAP no debería eliminarse | `ALREADY_COMPLIANT` (BE) + `UX_IMPROVEMENT` (FE) | El DELETE de los 20 maestros es **baja lógica** (`is_active=False`), nunca borrado físico: `masters/router.py:69-81`, `masters/service.py:267-272`. No hay referencias huérfanas ni 500. Defecto de experiencia: la UI dice «Eliminar», avisa «no se puede deshacer», el listado no distingue inactivos y un fallo del DELETE es silencioso | FE: «Desactivar/Reactivar», columna **Estado**, fila atenuada, toast de error (FR-04). Maestros SAP: por **OD-24** Empresas/Granjas serán espejo SAP de solo lectura cuando exista **P-08**; hoy no hay convergencia destructiva → documentar | P2 |
| **QA-003** | ¿Existe un campo único que identifique vacunas, medicamentos, causas de mortalidad y de descarte? | `ALREADY_COMPLIANT` + `UX_IMPROVEMENT` + `OWNER_DECISION_REQUIRED` | Se identifican por `name` (obligatorio, **no único por empresa**); ninguna fuente exige código único. UX: columnas descriptivas reales (laboratorio, tipo, vía; principio activo; descripción) con etiquetas correctas — hoy comparten el defecto de claves de botón (QA-013) | Mostrar columnas descriptivas con etiquetas propias (FR-02). Decisión Owner **OD-QA2-01**: ¿nombre único por empresa y/o código? | P2 |
| **QA-004** | ¿Las plantas/incubadoras manejan ZONA igual que las granjas? | `OWNER_DECISION_REQUIRED` | `Hatchery` tiene `location` (texto) y **no** `area_id` (`masters/models.py:110-113`). **GA-REM-039** define Área como estructura **organizativa**, no zona física; no aplica copiar `Farm` (`masters/models.py:79, 83`) | Decisión Owner **OD-QA2-02**; sin implementación en esta ronda | P2 |
| **QA-005** | Cómo se relacionan los maestros importados de SAP | `DOCUMENTATION_CLARIFICATION` | **SPEC 005**: HANA **READ ONLY** → RAW → VALIDATION → MAPPING → STAGING → **PROMOCIÓN CONTROLADA** a `sap_references`; **14 objetos**; `promotion.py:109-116, 246-256` promueve `business_unit_code` solo para `entity_type=PLANT`; `inbound/models.py:164-171`. El resto queda staging-only | Documentar la cadena y una sección para QA «Cómo Global Avícola recibe información de SAP» (FR-08/AC-08.2). SAP real **PENDING 2026-10-20** | P2 |
| **QA-006** | ¿Los lotes vienen de SAP? ¿Cuándo se crean directamente? | `DOCUMENTATION_CLARIFICATION` | `lots.origin`: `NATIVE` (alta manual, importación de abuelas) y `MIGRATED` (Cargas Iniciales / cutover, SPEC 006). **SAP inbound nunca crea lotes** (solo referencias). `activation_type` normal/manual | Documentar (FR-08/AC-08.3) | P3 |
| **QA-007** | No debería poder seleccionarse una OC de Engorde dentro de Reproductoras | `FUNCTIONAL_GAP` | `validate_oc_limit` (`validators.py:908-948`) solo valida **empresa** y **cantidad acumulada** (BR-18): no compara cadena. `/sap/references` (`sap/service.py:153-163`) filtra solo por empresa; el selector carga **todas** las OC. Dato determinista existente: `SapEntityMapping(entity_type=PLANT).business_unit_code` para el centro (WERKS) de las posiciones | Implementar **BR-23** mínimo (FR-01): cadena OC conocida ≠ `lots.bird_type` ⇒ 400; desconocida ⇒ permitir y mostrar «sin cadena»; conflicto entre centros ⇒ 400; selector FE filtrado. «Desconocida ⇒ bloquear» queda como decisión Owner | **P1** |
| **QA-008** | Al elegir una OC SAP todavía debe seleccionar granja, lote, etc. | `OWNER_DECISION_REQUIRED` + `DOCUMENTATION_CLARIFICATION` | Hoy la OC autocompleta **referencia**, **cantidad declarada** y **proveedor** (texto); granja/galpón/lote/transporte/fecha son del usuario. **SAP-STO-01** (LGORT↔galpón) y la clasificación de plantas (WERKS↔granja) están `PENDING` (**AOD-02**, **OD-24 P-08**) | Entregar matriz campo→`AUTO_POPULATED_EDITABLE`/`USER_REQUIRED`/`NOT_APPLICABLE`/`PENDING_MAPPING` (FR-08/AC-08.6). No autocompletar más hasta mapping aprobado (**OD-QA2-03**) | P2 |
| **QA-009** | ¿Se valida que los procesos se registren en orden? No debería registrarse alimento sin Recepción de Aves | `FUNCTIONAL_GAP` + `OWNER_DECISION_REQUIRED` | El backend **no tiene catálogo de predecesores**: solo reglas de saldo (BR-01..BR-04, R3/R4) y lote activo/fecha. La secuencia vive **solo** en `frontend/src/data/processCatalog.ts` (UI). `docs/02` no impone orden temporal | Entregar `PROCESS_PREDECESSOR_MATRIX` **propuesta** (precondición hoy / propuesta) y pedir **OD-QA2-04**. **No se implementa** en esta ronda | **P1** (decisión) |
| **QA-010** | ¿Desde qué estado pueden ocurrir rechazado, cancelado, reversado? | `DOCUMENTATION_CLARIFICATION` | Máquina de estados real verificada en `review/*`: `draft→registered`; `registered/returned/rejected→pending_review`; `pending_review→in_review`; `in_review→returned`; `in_review→corrected` (2+ niveles) o `→approved` (1 nivel); `corrected→approved|rejected` (BR-14, `review/service.py:35-90`); `approved→consolidated`; `cancel` desde todo salvo `approved/consolidated/sent_to_sap/sap_confirmed/reversed/cancelled`; `reverse` solo sobre `approved` con contrapartida aprobada ⇒ ambos `reversed`; corregible desde `registered/pending_review/in_review/returned/rejected` | Entregar `OPERATION_STATE_MACHINE.md` (FR-08/AC-08.1) | P2 |
| **QA-011** | ¿Cómo se configura y funciona la segregación de funciones? | `ALREADY_COMPLIANT` + `DOCUMENTATION_CLARIFICATION` | BR-14/**RR-03**: `ApprovalStep.require_segregation` (default `True`) por empresa; bloquea **registrador**, **corrector** y **quien rechazó** (**R-143**, 403) en `review/service.py:35-90`; el supervisor que revisó **sí** aprueba. Tests `test_segregation_r143` g01-g06 y E2E `proceso-03` | Documentar (FR-08/AC-08.4). Nota Owner: con la bandera en `False` se desactivan también las exclusiones de corrector/rechazador (inferencia de lectura de código; **confirmar**) | P3 |
| **QA-012** | Galpones, incubadoras (equipo) y nacedoras no identifican claramente el padre | `UX_IMPROVEMENT` | Los listados hijos no muestran el nombre del padre; el modelo sí tiene la relación (`masters/models.py`) | Añadir columna **Granja** / **Planta** por nombre (FR-03) | P2 |
| **QA-013** | Algunos maestros muestran una columna EDITAR cuyo contenido es otro atributo | **`DEFECT`** | **20 de 42** columnas reutilizan claves i18n de botones (`common.edit` «Editar», `common.save` «Guardar») para campos reales: `tax_id`, `country`, `code`, `location`, `capacity`, `plate`, `laboratory`, `category`, `order`, `description`, `sap_code` (definiciones de columna de los 20 maestros + `MasterListPage.tsx`/`DataTable.tsx`) | Claves i18n propias por campo + test guardián (FR-02) | **P1** |
| **QA-014** | Incluir Granja/Incubadora en Lotes, Historial, Mis Pendientes, Centro de Revisión y Aprobaciones | `UX_IMPROVEMENT` | Las APIs devuelven **solo ids**: `lots/schemas.py:77-86`, `operations/schemas.py:269-279` (no hay `farm_name`/`hatchery_name`) | Añadir nombre de padre al contrato de lectura + columna condicional (FR-07/AC-07.1-07.2) | P2 |
| **QA-015** | Agregar filtro por Granja / Incubadora | `UX_IMPROVEMENT` (farm) + `FUNCTIONAL_GAP` (hatchery) | `/operations` **ya acepta** `farm_id`/`date_from`/`date_to`/`status` (`operations/router.py:42-71`) y `/lots` `farm_id`/`status` (`lots/router.py:23`), pero la UI no los expone. **No existe `hatchery_id`** en ningún endpoint | Exponer filtro **Granja** en la UI (FR-07/AC-07.4). **Planta**: documentar como pendiente (AC-07.5) | P2 |
| **QA-016** | En campos sin fechas futuras permitidas el calendario aún las ofrece | `ALREADY_COMPLIANT` (BE `event_date`) + `UX_IMPROVEMENT` (FE) + `OWNER_DECISION_REQUIRED` (otras fechas) | BE: **BR-19** + **R-30/AC13** rechazan futuro en `event_date` (`validators.py:951-976`). FE: ningún `input type=date` operativo lleva `max=`. **RR-09** declara que ninguna fuente exige validar futuro en `start_date`/`activation_date`/`cutover_datetime` | FE `max=hoy` en `event_date` (FR-06) + inventario `FIELD/ROUTE/ALLOW_FUTURE`. Fechas planificadas/cutover: **OD-QA2-05** | P2 |
| **QA-017** | El Centro de Revisión busca constantemente (ejecución continua) | **`DEFECT`** | `ReviewCenter.tsx`: `fetchEvents` depende de `can` (función recreada por `useCan` en cada render) y del objeto `toast`; el `useEffect` se re-ejecuta tras cada `setState` ⇒ **REQUEST_LOOP** real. `ApprovalPanel` no cicla | Dependencias estables + test de conteo de peticiones (FR-05) | **P1** |
| **QA-018** | Mostrar Usuario y Fecha de creación en listados | `UX_IMPROVEMENT` | Los listados de operaciones/revisión no exponen ni muestran `created_by`/`created_at` | Columnas «Registrado por» y «Fecha de registro» distinguidas de la fecha del evento (FR-07/AC-07.3); se implementa junto con QA-014 | P2 |

---

## Conteos

| Clasificación | Total | Hallazgos |
|---|---|---|
| `ALREADY_COMPLIANT` | **5** | QA-001, QA-002, QA-003, QA-011, QA-016 (parcial) |
| `DEFECT` | **2** | QA-013, QA-017 |
| `FUNCTIONAL_GAP` | **3** | QA-007, QA-009, QA-015 (hatchery) |
| `UX_IMPROVEMENT` | **7** | QA-002, QA-003, QA-012, QA-014, QA-015, QA-016, QA-018 |
| `DOCUMENTATION_CLARIFICATION` | **6** | QA-001, QA-005, QA-006, QA-008, QA-010, QA-011 |
| `QA_MISUNDERSTANDING` | **0** | — |
| `OWNER_DECISION_REQUIRED` | **5** | QA-003 (unicidad), QA-004, QA-008, QA-009, QA-016 (fechas ≠ `event_date`) |

**Total de hallazgos clasificados**: **18 / 18** (QA-001 … QA-018). Los conteos **no son excluyentes** (un hallazgo puede llevar varias etiquetas) y por eso la suma por etiqueta (28) no coincide con 18.

### Distribución por prioridad

| Prioridad | Total | Hallazgos |
|---|---|---|
| **P1** | **4** | QA-007 (implementar BR-23), QA-009 (decisión), QA-013 (defecto UI), QA-017 (defecto UI) — QA-013/QA-017 son los dos `DEFECT` |
| P2 | 12 | QA-002, QA-003, QA-004, QA-005, QA-008, QA-010, QA-011, QA-012, QA-014, QA-015, QA-016, QA-018 |
| P3 | 1 | QA-006 |
| — | 1 | QA-001 (sin acción de código; documentación) |
| **Total** | **18** | — |

### Distribución por módulo revisado

| Módulo | Hallazgos |
|---|---|
| Maestros | QA-001, QA-002, QA-003, QA-004, QA-012, QA-013 |
| SAP | QA-005, QA-006 (lotes), QA-008 (OC) |
| Operativo | QA-007, QA-009, QA-014 (parcial), QA-015, QA-016, QA-018 (parcial) |
| Revisión / Aprobaciones | QA-010, QA-011, QA-014 (parcial), QA-017, QA-018 (parcial) |

---

## Lectura ejecutiva

1. **Ningún `QA_MISUNDERSTANDING`**: los 18 hallazgos son legítimos; seis apuntan a comportamiento correcto **mal explicado** (documentación, no código).
2. **Solo 2 defectos puros** (QA-013, QA-017) y ambos son P1 y de UI: se corrigen en esta ronda.
3. **3 huecos funcionales**: uno se cierra con regla mínima determinista (QA-007 → BR-23), uno requiere decisión (QA-009), y uno es de alcance de modelo de datos (QA-015/`hatchery_id`).
4. **5 decisiones del Owner** (OD-QA2-01…05) bloquean solo lo que exige política, no lo que exige contrato.
5. El backend en su núcleo (baja lógica, segregación, BR-18, BR-19, máquina de estados) **no requiere cambios de corrección**: requiere **documentación verificable**.
