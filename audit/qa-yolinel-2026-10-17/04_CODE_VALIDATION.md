# 04 · Validación de código — Revisión QA 2026-10-17

**Documento**: evidencia de código (`archivo:línea`) para cada hallazgo de `01_SOURCE_FINDINGS.md`
**Fecha**: 2026-10-18 · **Baseline**: `83c9cd8` · **Método**: lectura dirigida del código (sin ejecución de SAP, sin escrituras)
**Spec**: `specs/008-qa-yolinel-findings-remediation/spec.md` · **Clasificación**: `02` · **Trazabilidad**: `03`

> Las líneas corresponden al baseline `83c9cd8`. Si el archivo cambia, la referencia se revalida antes de certificar.

---

## 1. Evidencia por hallazgo

### QA-001 · Cadena / unidad de negocio en maestros

| Elemento | Ubicación | Verificación |
|---|---|---|
| `Farm.company_id` (empresa, **no** unidad de negocio) | `backend/app/modules/masters/models.py:79` | La FK es a empresa; no existe `business_unit_id` en `Farm` |
| `Farm.farm_type` | `backend/app/modules/masters/models.py:83` | Clasifica el tipo de granja; **no** determina la cadena |
| `Hatchery` | `backend/app/modules/masters/models.py:110-113` | Planta de incubación con `location` texto; sin FK a unidad de negocio |
| `Lot.bird_type` | `backend/app/modules/masters/models.py:295` | **Fuente real** de la cadena del lote |
| Derivación de cadena / scope | `backend/app/modules/business_units/scope.py:45-69` | La unidad/alcance se resuelve desde la cadena del lote, no desde el maestro padre |
| Clasificación de Hatchery | `route_scope.py` | Hatchery ⇒ unidad única `hatchery` |

**Conclusión**: `ALREADY_COMPLIANT`. No procede añadir FK; procede documentar (FR-08/AC-08.7). Riesgo de “arreglarlo” añadiendo FK: contradice GA-REM-040 (granja con galpones de varias unidades).

### QA-002 · Baja de maestros = lógica

| Elemento | Ubicación | Verificación |
|---|---|---|
| Endpoint DELETE | `backend/app/modules/masters/router.py:69-81` | Llama al servicio de desactivación; no hay `session.delete()` |
| Servicio de baja | `backend/app/modules/masters/service.py:267-272` | `is_active = False` y commit; **no** borrado físico |
| Consecuencia | — | Sin referencias huérfanas ni error 500 por FK al eliminar un maestro en uso |

**Conclusión**: `ALREADY_COMPLIANT` en backend. La regresión es de **presentación**: rótulo «Eliminar», aviso «no se puede deshacer», listado sin Estado y fallo silencioso ⇒ FR-04.

### QA-003 · Identificación de vacunas/medicamentos/causas

| Elemento | Ubicación | Verificación |
|---|---|---|
| Modelos de sanidad | `masters/models.py` (vacunas, medicamentos, causas de mortalidad/descarte) | `name` obligatorio; **sin** constraint `unique` por empresa; sin `code` |
| Atributos descriptivos disponibles | mismos modelos | laboratorio, tipo, vía, principio activo, descripción existen pero no se listan correctamente (ver QA-013) |
| Fuentes de contrato | `docs/02` | ninguna exige código único |

**Conclusión**: `ALREADY_COMPLIANT` (identificación por nombre) + `UX_IMPROVEMENT` (columnas) + `OWNER_DECISION_REQUIRED` (unicidad, OD-QA2-01).

### QA-004 · Zona/área en planta de incubación

| Elemento | Ubicación | Verificación |
|---|---|---|
| `Hatchery.location` | `masters/models.py:110-113` | Texto libre; **no** hay `area_id` |
| `Farm.company_id` / `Farm.farm_type` | `masters/models.py:79, 83` | El modelo de granja es distinto; replicarlo no está justificado |
| Contrato de Área | GA-REM-039 | Área = estructura **organizativa**, no zona física |

**Conclusión**: `OWNER_DECISION_REQUIRED` (OD-QA2-02). No se implementa.

### QA-005 · Relación de maestros importados de SAP

| Elemento | Ubicación | Verificación |
|---|---|---|
| Staging inbound | `backend/app/modules/inbound/models.py:164-171` | Estructura de staging (objeto + payload/crudo); no es todavía referencia de dominio |
| Promoción (mapeo) | `backend/app/modules/inbound/promotion.py:109-116` | Resuelve `business_unit_code` para la entidad promovida |
| Promoción (solo PLANT) | `backend/app/modules/inbound/promotion.py:246-256` | `business_unit_code` se asigna **solo** cuando `entity_type == PLANT`; el resto queda sin unidad ⇒ mapeo **informativo** |
| Cadena del módulo | SPEC 005 | HANA READ ONLY → RAW → VALIDATION → MAPPING → STAGING → **promoción controlada** a `sap_references`; **14 objetos** |

**Conclusión**: `DOCUMENTATION_CLARIFICATION` (FR-08/AC-08.2). SAP real `PENDING 2026-10-20`.

### QA-006 · Origen de los lotes

| Elemento | Ubicación | Verificación |
|---|---|---|
| `lots.origin` / `activation_type` | modelo y servicio de lotes | `origin ∈ {NATIVE, MIGRATED}`; `activation_type` normal/manual |
| Inbound SAP | `inbound/*` | el inbound escribe referencias/staging; **no** crea lotes de dominio |

**Conclusión**: `DOCUMENTATION_CLARIFICATION` (FR-08/AC-08.3).

### QA-007 · La OC no se contrasta con la cadena del lote

| Elemento | Ubicación | Verificación |
|---|---|---|
| `validate_oc_limit` | `backend/app/modules/operations/validators.py:908-948` (aprox.) | Valida **empresa** de la OC y **cantidad acumulada** (BR-18). **No** consulta cadena ni mapping PLANT |
| Listado de referencias OC | `backend/app/modules/sap/service.py:153-163` | `list_references` filtra **solo por empresa**; no hay parámetro de cadena |
| Dato determinista disponible | `inbound/promotion.py:246-256` | `SapEntityMapping(entity_type=PLANT).business_unit_code` existe por centro (WERKS) |

**Conclusión**: `FUNCTIONAL_GAP` P1 ⇒ BR-23 mínimo (FR-01). La política «cadena desconocida ⇒ bloquear» no está decidida ⇒ `OWNER_DECISION_REQUIRED`.

### QA-008 · Autocompletado de Recepción de Aves

| Elemento | Ubicación | Verificación |
|---|---|---|
| Autocompletado actual | formulario de recepción de aves (FE) | referencia, cantidad declarada y proveedor (texto) desde la OC; granja/galpón/lote/transporte/fecha del usuario |
| Mapping de almacén | SAP-STO-01 (`LGORT`↔galpón) | `PENDING` |
| Mapping de planta | OD-24 / AOD-02 (`WERKS`↔granja) | `PENDING` (P-08) |

**Conclusión**: `OWNER_DECISION_REQUIRED` (OD-QA2-03) + documentar matriz (AC-08.6).

### QA-009 · Orden de los procesos (predecesores)

| Elemento | Ubicación | Verificación |
|---|---|---|
| Validadores de proceso | `validators.py` (BR-01..BR-04, R3/R4) | Solo **saldos** (saldo insuficiente), lote activo y fecha |
| Catálogo de predecesores | — (`grep` de predecesor en backend) | **No existe** catálogo ni validación de orden de procesos |
| Secuencia en UI | `frontend/src/data/processCatalog.ts` | La secuencia vive **solo** en frontend (orden de presentación, no regla de dominio) |
| Contrato | `docs/02` | No impone orden temporal explícito |

**Conclusión**: `FUNCTIONAL_GAP` (backend) + `OWNER_DECISION_REQUIRED` (OD-QA2-04). Se entrega matriz propuesta; **no** se implementa.

### QA-010 · Máquina de estados de operaciones

| Elemento | Ubicación | Verificación |
|---|---|---|
| Transiciones de revisión/aprobación | `backend/app/modules/review/service.py` | `submit/start/return/complete/approve/reject` con niveles (BR-14) |
| Corrección | `review/service.py` + corrección | corregible desde `registered/pending_review/in_review/returned/rejected`; `corrected→approved|rejected` |
| Reverso | servicio de reverso | `reverse` solo sobre `approved` con contrapartida aprobada ⇒ ambos `reversed` |
| Cancelación | servicio de operaciones | `cancel` desde todo salvo `approved/consolidated/sent_to_sap/sap_confirmed/reversed/cancelled` |

**Conclusión**: `DOCUMENTATION_CLARIFICATION` ⇒ `OPERATION_STATE_MACHINE.md` (FR-08/AC-08.1).

### QA-011 · Segregación de funciones

| Elemento | Ubicación | Verificación |
|---|---|---|
| Aplicación de exclusiones | `backend/app/modules/review/service.py:35-90` (aprox.) | Bloquea registrador, corrector y quien rechazó ⇒ **403 R-143**; el supervisor que revisó sí aprueba |
| Configuración | `ApprovalStep.require_segregation` (default `True`, por empresa) | Si es `False` no se aplican exclusiones |
| Cobertura | `backend/tests/**/test_segregation_r143` g01-g06, E2E `proceso-03` | Cubierto por tests |

**Conclusión**: `ALREADY_COMPLIANT` + `DOCUMENTATION_CLARIFICATION`. **Nota**: con la bandera `False` también se desactivan las exclusiones de corrector/rechazador — es **inferencia de lectura**; el Owner debe confirmar si es el comportamiento deseado.

### QA-012 · Padre en listados de galpones/incubadoras/nacedoras

| Elemento | Ubicación | Verificación |
|---|---|---|
| Listados hijos | vistas de maestros (galpones, incubadoras-equipo, nacedoras) | No hay columna con nombre de granja/planta; solo ids o nada |
| Modelo | `masters/models.py` | La relación padre existe, por lo que el dato es resoluble sin migración |

**Conclusión**: `UX_IMPROVEMENT` ⇒ FR-03.

### QA-013 · Columnas con claves i18n de botones

| Elemento | Ubicación | Verificación |
|---|---|---|
| Definiciones de columna de los maestros | `frontend/src/**/masters/*` + `MasterListPage.tsx` + `DataTable.tsx` | **20 de 42** columnas usan claves de acción (`common.edit` «Editar», `common.save` «Guardar») para campos reales |
| Campos afectados | — | `tax_id`, `country`, `code`, `location`, `capacity`, `plate`, `laboratory`, `category`, `order`, `description`, `sap_code` (y el resto hasta 20) |
| Efecto | — | La cabecera muestra «Editar»/«Guardar» mientras el contenido es un dato (país, código, capacidad…) |

**Conclusión**: `DEFECT` P1 ⇒ FR-02 + test guardián.

### QA-014 · Listados devuelven solo ids

| Elemento | Ubicación | Verificación |
|---|---|---|
| Contrato de lotes | `backend/app/modules/lots/schemas.py:77-86` | Expone ids (granja/galpón/etc.); **no** `farm_name` |
| Contrato de operaciones | `backend/app/modules/operations/schemas.py:269-279` | Expone ids; **no** `farm_name`/`hatchery_name` |
| Efecto en UI | Lotes, Historial, Mis pendientes, Centro de Revisión, Aprobaciones | El FE no puede pintar el nombre sin resolver catálogos o un join |

**Conclusión**: `UX_IMPROVEMENT` ⇒ FR-07 (nombre de padre en contrato de lectura + columna condicional).

### QA-015 · Filtros ya soportados pero no expuestos

| Elemento | Ubicación | Verificación |
|---|---|---|
| Filtros de operaciones | `backend/app/modules/operations/router.py:42-71` | Acepta `farm_id`, `date_from`, `date_to`, `status` |
| Filtros de lotes | `backend/app/modules/lots/router.py:23` | Acepta `farm_id`, `status` |
| Filtro por planta | — (`grep` de `hatchery_id`) | **No existe** en ningún endpoint |
| UI | vistas de Operaciones y Lotes | No expone esos parámetros |

**Conclusión**: `UX_IMPROVEMENT` (farm, coste bajo) + `FUNCTIONAL_GAP` (hatchery: requiere diseño de endpoint). Se implementa farm; se documenta hatchery.

### QA-016 · Fechas futuras

| Elemento | Ubicación | Verificación |
|---|---|---|
| Validación backend `event_date` | `backend/app/modules/operations/validators.py:951-976` (aprox.) | Rechaza fecha futura (BR-19 / R-30 / AC13) |
| Resto de campos de fecha | `start_date`, `activation_date`, `cutover_datetime` | Sin validación de futuro; RR-09 no lo exige |
| Frontend | `grep` de `max=` en `frontend/src` (inputs `type="date"`) | **Ningún** input operativo aplica `max`; el calendario ofrece días futuros y el error aparece tras enviar |

**Conclusión**: `ALREADY_COMPLIANT` (BE) + `UX_IMPROVEMENT` (`max=hoy`) + `OWNER_DECISION_REQUIRED` (fechas planificadas/cutover).

### QA-017 · REQUEST_LOOP en el Centro de Revisión

| Elemento | Ubicación | Verificación |
|---|---|---|
| `fetchEvents` | `frontend/src/**/review/ReviewCenter.tsx` | Definida en el cuerpo del componente (nueva identidad por render) y usada en `useEffect` |
| Dependencia `can` | `useCan` + `ReviewCenter.tsx` | `useCan` devuelve una **función recreada en cada render**; al ser dependencia del efecto, el efecto se re-ejecuta |
| Dependencia `toast` | `ReviewCenter.tsx` | El objeto `toast` (contexto/hook) también entra en dependencias → nueva ejecución |
| Bucle real | — | Cada `setState` (incluidos los que guardan la respuesta) provoca nuevo render → nueva identidad → nuevo fetch |
| `ApprovalPanel` | `frontend/src/**/review/ApprovalPanel.tsx` | No presenta el patrón; sirve de contraste (no cicla) |

**Conclusión**: `DEFECT` P1 ⇒ FR-05 + test de conteo de peticiones.

### QA-018 · Usuario y fecha de registro

| Elemento | Ubicación | Verificación |
|---|---|---|
| Campos existentes | modelo de operaciones | `created_by`/`created_at` (auditoría) existen |
| Contratos de lectura | `lots/schemas.py:77-86`, `operations/schemas.py:269-279` | No exponen explícitamente usuario de registro ni `created_at` en los esquemas citados |
| UI | Lotes, Historial, Mis pendientes, Revisión, Aprobaciones | Sin columnas «Registrado por» / «Fecha de registro»; solo fecha de evento |

**Conclusión**: `UX_IMPROVEMENT` ⇒ FR-07 (con QA-014).

---

## 2. Tabla resumen de evidencia

| QA | Archivo(s):línea | Tipo de hallazgo | Gravedad |
|---|---|---|---|
| QA-001 | `masters/models.py:79, 83, 110-113, 295`; `business_units/scope.py:45-69` | Modelo correcto (sin FK a BU) | — |
| QA-002 | `masters/router.py:69-81`; `masters/service.py:267-272` | Baja lógica confirmada | — (BE) / UX P2 |
| QA-003 | `masters/models.py` (sanidad) | `name` sin unique | P2 |
| QA-004 | `masters/models.py:110-113` | `location` texto, sin `area_id` | P2 (decisión) |
| QA-005 | `inbound/models.py:164-171`; `inbound/promotion.py:109-116, 246-256` | Promoción parcial (PLANT) | P2 (doc) |
| QA-006 | modelo/servicio de lotes; `inbound/*` | `origin` / `activation_type` | P3 (doc) |
| QA-007 | `validators.py:908-948`; `sap/service.py:153-163`; `promotion.py:246-256` | Sin validación de cadena | **P1** |
| QA-008 | formulario de recepción (FE); SAP-STO-01/AOD-02 `PENDING` | Autocompletado limitado | P2 (decisión) |
| QA-009 | `validators.py` (saldos); `processCatalog.ts` | Sin predecesores en BE | **P1** (decisión) |
| QA-010 | `review/service.py`; servicios de corrección/reverso/cancelación | Estados implementados | P2 (doc) |
| QA-011 | `review/service.py:35-90`; `test_segregation_r143` g01-g06; `proceso-03` | Segregación correcta | P3 (doc) |
| QA-012 | vistas de maestros hijos | Falta columna de padre | P2 |
| QA-013 | `MasterListPage.tsx`; `DataTable.tsx`; columnas de maestros | 20/42 claves de acción | **P1** |
| QA-014 | `lots/schemas.py:77-86`; `operations/schemas.py:269-279` | Solo ids | P2 |
| QA-015 | `operations/router.py:42-71`; `lots/router.py:23`; sin `hatchery_id` | Filtros BE listos, FE no | P2 |
| QA-016 | `validators.py:951-976`; FE sin `max=` | BE correcto, FE incompleto | P2 |
| QA-017 | `ReviewCenter.tsx` (deps `can`/`toast`); `ApprovalPanel` sin bucle | REQUEST_LOOP | **P1** |
| QA-018 | `lots/schemas.py:77-86`; `operations/schemas.py:269-279`; vistas | Sin usuario/fecha de registro | P2 |

---

## 3. Conclusiones de validación

1. **El backend no tiene errores de corrección en los hallazgos de maestros, segregación, fechas de evento ni workflow**: la baja es lógica, la segregación se aplica con 403 (R-143) y `event_date` rechaza futuro. Los “fallos” percibidos son de presentación y de documentación.
2. **Los dos defectos reales están en el frontend**: claves i18n de acción usadas como etiquetas de campo (QA-013) y dependencias inestables que producen el bucle de peticiones (QA-017). Ambos P1 y con test de regresión.
3. **El único hueco funcional que se cierra en esta ronda es QA-007**: BR-23 se implementa con un dato ya persistido (`SapEntityMapping(PLANT).business_unit_code`), sin consultar SAP y sin decidir política nueva, con `fail-open` explícito para cadena desconocida.
4. **QA-009 y QA-015 (hatchery) no se resuelven con código hoy**: requieren decisión Owner (QA-009) o contrato inexistente (`hatchery_id`).
5. **Ninguna evidencia de código contradice la clasificación**: no hay `QA_MISUNDERSTANDING`.

## 4. Límites de esta validación

- Lectura estática: no se ejecutaron pruebas en esta pasada (los tests RED/GREEN se ejecutan en las fases R…6 del `plan.md`).
- Las líneas citadas son del baseline `83c9cd8`; deben revalidarse tras cada commit de la ronda.
- No se contrastó con el PDF de QA (`PENDING`): si aparece una captura que muestre un comportamiento distinto, esta validación se reabre.
- No se inspeccionó ningún archivo de entorno ni se realizó ninguna llamada a SAP (ni real ni simulada) durante la validación.
