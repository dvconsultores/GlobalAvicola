# 05 · Plan de corrección por hallazgo — Revisión QA 2026-10-17

**Documento**: estado real de cada hallazgo al cierre de la ronda de remediación
**Fecha**: 2026-10-18 · **Baseline de referencia**: `83c9cd8` · **Spec asociada**: `specs/008-qa-yolinel-findings-remediation/spec.md`
**Carácter**: estado de implementación verificado en código y en pruebas; no sustituye la certificación QA

Estados usados: `IMPLEMENTADO` · `DOCUMENTADO` · `OWNER_DECISION` · `FUNCTIONAL_GAP`.

---

## 1. Tabla de estado

| ID | Hallazgo (resumen) | Estado | Qué hay hoy | Evidencia / prueba |
|---|---|---|---|---|
| **QA-007** | Una OC de Engorde podía usarse en Reproductoras | **IMPLEMENTADO** (backend + frontend) | **BR-23**: cadena de la OC derivada del `business_unit_code` de sus centros; si es conocida y no coincide con la cadena del lote ⇒ `400`; si es **desconocida** se permite y se rotula «sin cadena»; conflicto entre centros ⇒ `400`. Selector de OC filtrado en el frontend | `backend/tests/test_br23_sap_reference_business_unit.py`, `frontend/src/pages/operations/__tests__/qaYolinel.sapOrderByUnit.test.tsx` |
| **QA-013** | Columnas de maestros con etiquetas de botón («Editar», «Guardar») | **IMPLEMENTADO** | Claves i18n propias por campo en los 20 maestros (42 columnas revisadas) + prueba guardiana que impide reutilizar claves de acción como cabecera de dato | `frontend/src/pages/masters/__tests__/qaYolinel.mastersList.test.tsx` |
| **QA-012** | Galpones, incubadoras (equipo) y nacedoras no muestran el padre | **IMPLEMENTADO** | Columna con el nombre del padre: **Granja** en galpones, **Planta** en equipos y nacedoras | `frontend/src/pages/masters/__tests__/qaYolinel.mastersList.test.tsx` |
| **QA-002** | «Eliminar» en maestros: la UI no distingue inactivos ni avisa de fallos | **IMPLEMENTADO** | Acción **Desactivar/Reactivar**, columna **Estado**, fila atenuada para inactivos y toast de error cuando la baja lógica falla. El backend ya era baja lógica (`is_active=False`), nunca borrado | `frontend/src/pages/masters/__tests__/qaYolinel.mastersList.test.tsx` |
| **QA-017** | Bucle de peticiones / re-render en las pantallas afectadas | **IMPLEMENTADO** | `useCan` estable (identidad de función memoizada) y dependencias corregidas en los efectos; sin bucles de recarga | `frontend/src/__tests__/qaYolinel.red.test.tsx` |
| **QA-016** | Fechas futuras aceptadas | **IMPLEMENTADO** (parcial: `event_date`) | `max=hoy` en el selector de la **fecha del evento** y en las fechas de **salida/llegada de la importación**. El resto de fechas queda como decisión Owner (ver §3) | `frontend/src/__tests__/qaYolinel.red.test.tsx` |
| **QA-014** | Granja/Incubadora ausentes en Lotes, Historial, Mis Pendientes, Centro de Revisión y Aprobaciones | **IMPLEMENTADO** | Contrato de lectura ampliado con `farm_name`, `lot_code` y `registered_by_name`; columnas **Lote / Granja / Fecha del evento / Registrado por / Fecha de registro** en Lotes, Historial, Mis pendientes, Centro de Revisión y Aprobaciones. La parte de **incubadora** queda declarada como brecha funcional en QA-015 (§3) | `backend/tests/test_qa_yolinel_list_enrichment.py` (3), `frontend/src/__tests__/qaYolinel.listColumns.test.tsx` (3), `frontend/src/pages/review/__tests__/qaYolinel.reviewColumns.test.tsx` (2) |
| **QA-015** | Filtro por Granja / Incubadora | **IMPLEMENTADO** (granja) + **FUNCTIONAL_GAP** (incubadora) | Filtro **Granja** expuesto en la UI sobre endpoints que ya lo aceptaban: **Lotes, Historial, Aprobaciones** y **Centro de Revisión** (que ya lo tenía). **No existe `hatchery_id`** en ningún endpoint: se documenta como brecha funcional, sin implementación en esta ronda | `backend/tests/test_qa_yolinel_list_enrichment.py` (3), `frontend/src/__tests__/qaYolinel.listColumns.test.tsx` (3), `frontend/src/pages/review/__tests__/qaYolinel.reviewColumns.test.tsx` (2) |
| **QA-018** | Listados pobres en Centro de Revisión y Aprobaciones | **IMPLEMENTADO** | Mismo enriquecimiento que QA-014 (`registered_by_name`, granja, código de lote) aplicado a esas dos colas, más **Fecha de registro** distinguida de la fecha del evento | `backend/tests/test_qa_yolinel_list_enrichment.py` (3), `frontend/src/__tests__/qaYolinel.listColumns.test.tsx` (3), `frontend/src/pages/review/__tests__/qaYolinel.reviewColumns.test.tsx` (2) |
| **QA-001** | ¿Granjas/Incubadoras relacionadas con su Unidad de Negocio? | **DOCUMENTADO** | No hay FK granja→unidad: una granja aloja galpones de varias unidades (`GA-REM-040`); la cadena se deriva del lote. Plantas de incubación = cadena `hatchery` | `LOT_ORIGIN_AND_MASTERS_FOR_QA.md` |
| **QA-005** | Cómo se relacionan los maestros importados de SAP | **DOCUMENTADO** | HANA **solo lectura** → RAW → VALIDACIÓN → MAPEO → STAGING → promoción controlada a referencias; 14 objetos | `SAP_PARA_QA.md` |
| **QA-006** | ¿Los lotes vienen de SAP? | **DOCUMENTADO** | `NATIVE` (alta manual / importación de abuelas) y `MIGRATED` (cargas iniciales). **SAP nunca crea lotes** | `LOT_ORIGIN_AND_MASTERS_FOR_QA.md` |
| **QA-010** | ¿Desde qué estado se rechaza, cancela o reversa? | **DOCUMENTADO** | Máquina de estados completa con las tres acciones y sus guardas | `OPERATION_STATE_MACHINE.md` |
| **QA-011** | Cómo se configura y funciona la segregación | **DOCUMENTADO** | **BR-14** / **RR-03**: configurable por paso (`require_segregation`, por defecto activo); bloquea registrador, corrector y quien rechazó | `LOT_ORIGIN_AND_MASTERS_FOR_QA.md` §5 |
| **QA-003** | ¿Campo único para vacunas, medicamentos, causas? (unicidad) | **OWNER_DECISION** (OD-QA2-01) | Hoy la identidad es el **nombre** (obligatorio, no único por empresa); ninguna fuente exige código único. Se corrigieron las columnas descriptivas (QA-013). Falta decidir si se exige unicidad y/o código | — |
| **QA-004** | ¿Las plantas/incubadoras manejan ZONA como las granjas? | **OWNER_DECISION** (OD-QA2-02) | La planta tiene `location` (texto) y no `area_id`; **GA-REM-039** define Área como estructura organizativa, no zona física. No se copia el modelo de granja sin decisión | — |
| **QA-008** | Al elegir una OC SAP aún hay que elegir granja, lote, etc. | **OWNER_DECISION** (OD-QA2-03) | La OC autocompleta referencia, cantidad declarada y proveedor; el resto son datos del usuario. Autocompletar más exige el mapping **SAP-STO-01** (LGORT↔galpón) y la clasificación WERKS↔granja, hoy `PENDING` (AOD-02 / OD-24 P-08) | — |
| **QA-009** | ¿Se valida el orden de los procesos? | **OWNER_DECISION** (OD-QA2-04) | El backend no tiene catálogo de predecesores; la secuencia vive solo en la UI. Se entrega matriz propuesta, sin implementar | `PROCESS_PREDECESSOR_MATRIX.md` |
| **QA-016 (otras fechas)** | Fechas distintas de la del evento | **OWNER_DECISION** | Solo la **fecha del evento** rechaza futuro; las fechas de inspección, parámetros de incubación y demás tienen semántica propia (algunas pueden ser planes a futuro). Decidir cuáles se limitan | — |

## 2. Pruebas RED → GREEN de referencia

| Ámbito | Archivo |
|---|---|
| BR-23 · cadena de la OC vs cadena del lote | `backend/tests/test_br23_sap_reference_business_unit.py` |
| Contrato de lectura enriquecido (granja, lote, registrador) | `backend/tests/test_qa_yolinel_list_enrichment.py` |
| Regresiones de UI (bucle, fechas, acciones) | `frontend/src/__tests__/qaYolinel.red.test.tsx` |
| Selector de OC filtrado por unidad | `frontend/src/pages/operations/__tests__/qaYolinel.sapOrderByUnit.test.tsx` |
| Maestros: etiquetas, padre, estado, desactivar | `frontend/src/pages/masters/__tests__/qaYolinel.mastersList.test.tsx` |

## 3. Pendiente de decisión Owner (no bloquea la entrega, sí la cierra)

| Decisión | Contenido | Efecto si no se decide |
|---|---|---|
| **OD-QA2-01** | ¿Nombre único por empresa y/o código en vacunas, medicamentos y causas? | Se mantiene la identidad por nombre; el riesgo de duplicados homónimos persiste |
| **OD-QA2-02** | Zona en plantas de incubación | Las plantas siguen clasificándose solo por ubicación (texto) |
| **OD-QA2-03** | Autocompletado adicional desde la OC | Granja/galpón/lote/transporte siguen siendo manuales |
| **OD-QA2-04** | Predecesores de proceso: ¿bloqueante o aviso? ¿qué severidad? | Se puede registrar un proceso fuera de orden; la UI avisa, el backend no impide |
| **QA-015 hatchery** | `hatchery_id` en endpoints y filtro en UI | No hay filtro por planta en ninguna pantalla (brecha funcional declarada) |
| **QA-003/004/008** | Ver filas `OWNER_DECISION` de §1 | Sin cambio de código |
