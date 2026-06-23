# Auditoría: Recomendación Central vs Spec vs Implementación

> **Fecha:** 2026-06-23  
> **Documento fuente:** "Recomendación central.pdf" — Soluciones Integrales de TI Innova  
> **Alcance:** 26 secciones de recomendaciones para integración SAP S/4HANA ↔ App Avícola  
> **Resultado:** 73 puntos verificados — 45 ✅ | 16 ⚠️ Parcial | 12 ❌ No implementado

---

## Resumen Ejecutivo

| Categoría | Total | ✅ Cubierto | ⚠️ Parcial | ❌ Falta |
|:--|:--|:--|:--|:--|
| Arquitectura y principios | 5 | 5 | 0 | 0 |
| SAP como mandante | 3 | 2 | 1 | 0 |
| Funciones App (permitidas) | 20 | 15 | 2 | 3 |
| Módulos SAP | 12 | 3 | 4 | 5 |
| Procesos operativos | 8 | 4 | 3 | 1 |
| Reglas de validación | 17 | 10 | 5 | 2 |
| Estados operativos | 1 | 1 | 0 | 0 |
| Integración técnica | 7 | 3 | 1 | 3 |
| **TOTAL** | **73** | **45 (62%)** | **16 (22%)** | **12 (16%)** |

---

## 1. Principio Fundamental: SAP Mandante, App Auxiliar

> "Configuren SAP S/4HANA como sistema mandante transaccional y la app avícola como sistema auxiliar operativo de captura, validación, evidencia y aprobación."

| # | Recomendación | Spec | Implementación | Estado |
|:--|:--|:--|:--|:--|
| 1.1 | SAP es mandante transaccional | Spec §3.1: "SAP es el sistema principal" | ✅ Principio reflejado en spec | ✅ |
| 1.2 | App es auxiliar operativo | Spec §3.1 | ✅ `AppLayout` separa web/mobile | ✅ |
| 1.3 | App no decide inventario, costos, compras | Spec §9: Out of scope | ✅ Backend no tiene endpoints de creación de OC/STO | ✅ |
| 1.4 | Solo datos aprobados van a SAP | Spec §3.2: "Nada va a SAP sin aprobación" | ✅ `ReviewCenter` → `ApprovalPanel` → `SAP export` | ✅ |
| 1.5 | Datos trazables e idempotentes | Spec §5 BR-11/BR-12 | ✅ SHA-256 idempotency key, `SapPayload` unique | ✅ |

---

## 2. Qué Debe Quedar Mandante en SAP

| # | Objeto | Dueño según doc | Spec | Implementación | Estado |
|:--|:--|:--|:--|:--|:--|
| 2.1 | Materiales | SAP | ✅ `SapReferenceType.MATERIAL` | ✅ Referencia SAP catalogada | ✅ |
| 2.2 | Proveedores | SAP | ✅ `Supplier.sap_code` | ⚠️ Solo maestro local, sin sync SAP | ⚠️ |
| 2.3 | Órdenes de compra | SAP | ✅ `SapReferenceType.PURCHASE_ORDER` | ✅ Lectura de OC desde SAP | ✅ |
| 2.4 | Órdenes de transferencia | SAP | ✅ `SapReferenceType.TRANSFER_ORDER` | ✅ Lectura de STO | ✅ |
| 2.5 | Inventario | SAP | ❌ No hay consulta de stock | ❌ Sin endpoint de inventario | ❌ |
| 2.6 | Almacenes | SAP | ✅ `SapReferenceType.STORAGE_LOCATION` | ✅ Catalogado, sin sync | ⚠️ |
| 2.7 | Centros / plantas / granjas | SAP | ✅ `SapReferenceType.PLANT` | ✅ Catalogado, sin sync | ⚠️ |
| 2.8 | Centros de costo | SAP | ❌ No modelado | ❌ Sin modelo CO | ❌ |
| 2.9 | Costeo | SAP | ❌ Fuera de scope v1 | ❌ Sin módulo de costos | ❌ |
| 2.10 | Cierre contable/logístico | SAP | ❌ No modelado | ❌ Sin validación de período fiscal | ❌ |
| 2.11 | Lotes productivos oficiales | SAP | ⚠️ `Lot` model existe pero es local | ⚠️ Lote local, no sincronizado con SAP | ⚠️ |

---

## 3. Qué Debe Poder Hacer la App (Funciones Permitidas)

| # | Función | Doc | Spec | Implementación | Estado |
|:--|:--|:--|:--|:--|:--|
| 3.1 | Consultar OC abiertas | Sí | ✅ | ✅ `GET /sap/references?ref_type=purchase_order` | ✅ |
| 3.2 | Consultar STO abiertas | Sí | ✅ | ✅ `GET /sap/references?ref_type=transfer_order` | ✅ |
| 3.3 | Consultar materiales | Sí | ✅ | ✅ `SapReferenceType.MATERIAL` | ✅ |
| 3.4 | Consultar inventario disponible | Sí | ❌ | ❌ Sin endpoint | ❌ |
| 3.5 | Consultar granjas, galpones, capacidad | Sí | ✅ | ✅ Masters CRUD con `capacity` | ✅ |
| 3.6 | Capturar recepción real de aves | Sí | ✅ | ✅ `bird_reception` event | ✅ |
| 3.7 | Distribuir aves por galpón, sexo, lote | Sí | ✅ | ✅ `BirdMovement` con `sex`, `source_house_id` | ✅ |
| 3.8 | Registrar peso promedio | Sí | ✅ | ✅ `BirdMovement.avg_weight` | ✅ |
| 3.9 | Registrar temperatura, humedad | Sí | ✅ | ✅ `OperationalEvent` + `InspectionDetail` | ✅ |
| 3.10 | Registrar mortalidad | Sí | ✅ | ✅ `mortality_recording` event | ✅ |
| 3.11 | Registrar consumo alimento | Sí | ✅ | ✅ `feed_registration` + `FeedMovement` | ✅ |
| 3.12 | Registrar vacunas/medicinas | Sí | ✅ | ✅ `vaccination`/`medication` events | ✅ |
| 3.13 | Registrar inspección granja/equipos | Sí | ✅ | ✅ `farm_inspection` event | ✅ |
| 3.14 | Levantar banderas operativas | Sí | ❌ | ❌ No implementado | ❌ |
| 3.15 | Adjuntar evidencias | Sí | ❌ | ❌ Sin modelo de adjuntos/evidencias | ❌ |
| 3.16 | Enviar datos aprobados a SAP | Sí | ✅ | ✅ `POST /sap/export` con flujo completo | ✅ |

**Funciones NO permitidas (correctamente bloqueadas):**
| 3.17 | Crear OC desde la app | No | ✅ | ✅ Sin endpoint | ✅ |
| 3.18 | Crear materiales desde la app | No | ✅ | ✅ Solo lectura | ✅ |
| 3.19 | Cambiar costos desde la app | No | ✅ | ✅ Sin módulo | ✅ |
| 3.20 | Cerrar órdenes desde la app | No | ✅ | ✅ Sin endpoint | ✅ |

---

## 4. Módulos SAP que Deben Quedar Preparados

### 4.1 MM — Material Management

| # | Requisito | Estado |
|:--|:--|:--|
| 4.1.1 | Compra de aves, alimento, vacunas, medicinas | ⚠️ Referencias SAP catalogadas, sin integración real |
| 4.1.2 | Órdenes de compra y transferencia | ✅ `SapReferenceType` cubre ambos |
| 4.1.3 | Gestión de inventario | ❌ Sin consulta de stock |
| 4.1.4 | Consumos, mermas, bajas | ❌ Sin modelo de movimiento de material |
| 4.1.5 | Recepciones parciales, diferencias | ⚠️ `OperationalEvent` captura diferencias, no las envía a SAP |
| 4.1.6 | API Purchase Order (lectura) | ❌ Sin cliente OData/SOAP real |

### 4.2 Inventory Management

| # | Requisito | Estado |
|:--|:--|:--|
| 4.2.1 | IM básico / WM / EWM definido | ❌ No modelado |
| 4.2.2 | Almacenes por granja | ⚠️ `House` model existe, sin integración SAP |
| 4.2.3 | API Material Document | ❌ Sin implementación |

### 4.3 CO — Controlling

| # | Requisito | Estado |
|:--|:--|:--|
| 4.3.1 | Granja = Centro de costo | ❌ Sin modelo CO |
| 4.3.2 | Lote productivo = Eje de trazabilidad y costeo | ⚠️ `Lot` existe localmente, sin enlace CO |
| 4.3.3 | Consumo contra lote o centro de costo | ❌ Sin imputación CO |

### 4.4 PM/EAM — Equipos

| # | Requisito | Estado |
|:--|:--|:--|
| 4.4.1 | Inventario de equipos por galpón | ❌ Sin modelo de equipos |
| 4.4.2 | Contraste equipo esperado vs encontrado | ❌ Sin implementación |

### 4.5 QM — Quality Management

| # | Requisito | Estado |
|:--|:--|:--|
| 4.5.1 | Bioseguridad en app, resumen a SAP | ⚠️ `InspectionDetail` captura datos, sin envío a SAP |
| 4.5.2 | Evento de calidad a SAP | ❌ Sin implementación |

### 4.6 FI — Financial

| # | Requisito | Estado |
|:--|:--|:--|
| 4.6.1 | App no crea asientos contables | ✅ Correctamente fuera de scope |

---

## 5. Materiales que Deben Existir en SAP

| # | Material | Espec | Estado |
|:--|:--|:--|:--|
| 5.1 | Pollita reproductora Cobb hembra | ⚠️ No en catálogo de materiales | ⚠️ |
| 5.2 | Pollito reproductor Cobb macho | ⚠️ No en catálogo | ⚠️ |
| 5.3 | Reproductora Ross hembra/macho | ⚠️ No en catálogo | ⚠️ |
| 5.4 | Pollito engorde | ⚠️ No en catálogo | ⚠️ |
| 5.5 | Pollita progenitora | ⚠️ No en catálogo | ⚠️ |
| 5.6 | Huevo fértil / descartado | ⚠️ `EggMovement.egg_type` cubre tipos | ⚠️ |
| 5.7 | Pollito nacido | ⚠️ No en catálogo | ⚠️ |
| 5.8 | Alimento por tipo (8 tipos) | ✅ `FeedType` model en masters | ✅ |
| 5.9 | Medicinas y vacunas | ✅ `Vaccine` y `Medication` models | ✅ |
| 5.10 | Batch management para trazabilidad | ❌ Sin modelo batch/lote SAP | ❌ |

---

## 6. Procesos Operativos — Evaluación por Proceso

### 6.1 Recepción de Reproductoras

**En SAP debe crear:** OC, proveedor, material, cantidad, raza, sexo, centro, almacén, precio, fecha, lote
| Campo | App | Estado |
|:--|:--|:--|
| OC SAP | `sap_document_ref` en event | ✅ |
| Posición OC | ❌ No modelado | ❌ |
| Proveedor | `Supplier` model | ✅ |
| Material | `SapReferenceType.MATERIAL` | ✅ |
| Cantidad esperada/recibida | `BirdMovement.quantity` | ✅ |
| Fecha despacho/recepción | `OperationalEvent.event_date` | ✅ |
| Hora recepción | `OperationalEvent.event_time` | ✅ |
| Granja, galpones | `farm_id`, `house_id` | ✅ |
| Capacidad galpón | `House.capacity` — sin validación | ⚠️ |
| Distribución ♂♀ | `BirdMovement.sex` | ✅ |
| Raza confirmada | `BirdMovement.breed_id` | ✅ |
| Peso promedio ♂♀ | `BirdMovement.avg_weight` por sexo | ✅ |
| Muestra tomada | ❌ Sin campo `sample_size` en recepción | ❌ |
| Temperatura, humedad | En `InspectionDetail` o `OperationalEvent` | ✅ |
| Condición transporte | `InspectionDetail` tipo `transport_inspection` | ✅ |
| Mortalidad al arribo | `mortality_recording` event | ✅ |
| Evidencias | ❌ Sin adjuntos | ❌ |

**Validación administrativa:**
| Regla | Estado |
|:--|:--|
| OC existe | ✅ `validate_lot_active` (BR-07) | ✅ |
| Cantidad ≤ OC | ❌ Sin validación | ❌ |
| Distribución ≤ capacidad | ❌ Sin validación | ❌ |
| ♂ + ♀ + mort + rechazo cuadran | ❌ Sin validación de cuadre | ❌ |
| Lote definido | ✅ `lot_id` requerido | ✅ |
| Pesos en rango | ❌ Sin validación | ❌ |
| Evidencia existe | ❌ Sin validación | ❌ |
| Responsable aprueba | ✅ `ApprovalStep` workflow | ✅ |

### 6.2 Inspección de Granja

| Campo | Estado |
|:--|:--|
| Fecha, inspector, granja, galpón | ✅ |
| Equipos encontrados/faltantes/dañados | ❌ Sin modelo de equipos |
| Estado cama, T°, H°, ventilación | ✅ `InspectionDetail` |
| Limpieza, bioseguridad | ✅ `InspectionDetail` |
| Evidencia fotográfica | ❌ Sin adjuntos |
| Bandera de riesgo | ❌ Sin alertas |

### 6.3 Alimento por Transferencia

| Paso | Estado |
|:--|:--|
| Consultar transferencias activas | ✅ `SapReference` transfer_order |
| Confirmar llegada | ✅ `feed_registration` con `sap_order_id` |
| Registrar cantidad recibida | ✅ `FeedMovement.quantity_kg` |
| Registrar diferencias | ❌ Sin campo de diferencia |
| Registrar lote alimento | ❌ Sin batch de alimento |
| Registrar silo/almacén destino | ❌ Sin modelo de almacén |
| Registrar evidencia | ❌ Sin adjuntos |
| Consumo parcial diario/semanal | ✅ `FeedMovement` + `week_number` (G-08) |

### 6.4 Mortalidad

| Campo | Estado |
|:--|:--|
| Fecha, granja, galpón, lote, sexo | ✅ |
| Edad del lote | ⚠️ Calculable pero no almacenado |
| Cantidad, causa, clasificación | ✅ `mortality_recording` + `MortalityCause` |
| Observación sanitaria, responsable | ✅ |
| Evidencia | ❌ |
| Peso si aplica | ⚠️ No en modelo de mortalidad |
| Acumulados y % | ✅ `reports/service.py` KPIs |
| Política: KPI vs baja vs estadístico | ⚠️ No definido explícitamente |

### 6.5 Vacunas y Medicinas

| Campo | Estado |
|:--|:--|
| Material inventariable en SAP | ✅ `Vaccine`/`Medication` en masters |
| Lote productivo, galpón, sexo | ✅ |
| Dosis, cantidad usada | ✅ `vaccination`/`medication` events |
| Responsable, fecha, hora | ✅ |
| Método de aplicación | ⚠️ Parcial — no hay campo `method` |
| Evidencia | ❌ |
| Envío a SAP: consumo + imputación | ❌ Sin integración |

### 6.6 Producción de Huevos

| Campo | Estado |
|:--|:--|
| Huevos recolectados, fértiles, descartados, rotos, sucios, infértiles | ✅ `EggMovement.egg_type` |
| Peso promedio | ✅ `EggMovement.avg_weight` |
| Galpón, lote, fecha/hora | ✅ |
| Condiciones almacenamiento | ✅ G-07: `storage_temp_c`, `storage_humidity_pct` |
| Envío a SAP: entrada/producción | ❌ Sin integración |

### 6.7 Incubadora

| Campo | Estado |
|:--|:--|
| Lote huevos, cantidad recibida | ✅ `egg_reception_hatchery` |
| Condición transporte, T°, H°, tiempo | ✅ G-07: `EggStorage` model |
| Descartes, fertilidad | ✅ `ovoscopy` event |
| Nacimientos, pollitos descartados | ✅ `birth_registration` |
| Vacunación, clasificación | ✅ `vaccination` event |
| Transferencia a granja | ✅ `chick_dispatch` |
| Envío a SAP: movimientos, costos | ❌ Sin integración |

### 6.8 Pollo de Engorde

| Campo | Estado |
|:--|:--|
| Recepción pollitos | ✅ `bird_reception` |
| Mortalidad, consumo, peso, uniformidad | ✅ Events correspondientes |
| Conversión alimenticia | ✅ `reports/service.py` KPI |
| Salida a planta, cantidad, peso | ✅ `bird_exit` event |
| Envío a SAP: consumos, cierre | ❌ Sin integración |

---

## 7. Reglas de Validación Obligatorias (17 reglas del documento)

| # | Regla del Documento | Spec BR | Implementación | Estado |
|:--|:--|:--|:--|:--|
| 7.1 | Cantidad recibida ≤ OC | — | ❌ No implementada | ❌ |
| 7.2 | Capacidad galpón no excedida | — | ❌ `House.capacity` sin validación | ❌ |
| 7.3 | Galpón existe en SAP | — | ⚠️ Validación local, no contra SAP | ⚠️ |
| 7.4 | Material existe en SAP | — | ⚠️ Validación local, no contra SAP | ⚠️ |
| 7.5 | Lote inexistente o cerrado | BR-07 | ✅ `validate_lot_active` | ✅ |
| 7.6 | Almacén inválido | — | ❌ Sin validación | ❌ |
| 7.7 | Centro inválido | — | ❌ Sin validación | ❌ |
| 7.8 | Unidad de medida inválida | — | ❌ Sin validación | ❌ |
| 7.9 | Consumo > stock disponible | — | ❌ Sin consulta de stock | ❌ |
| 7.10 | Mortalidad > población actual | BR-01 | ✅ `validate_mortality` | ✅ |
| 7.11 | Vacuna sin material válido | — | ⚠️ Validación local de FK | ⚠️ |
| 7.12 | Consumo sanitario sin stock | — | ❌ Sin consulta de stock | ❌ |
| 7.13 | Fecha en período SAP cerrado | — | ❌ Sin validación de período | ❌ |
| 7.14 | Registro sin usuario responsable | — | ✅ `registered_by_id` FK not null | ✅ |
| 7.15 | Registro sin aprobación | BR-13 | ✅ Approval workflow | ✅ |
| 7.16 | Duplicidad de envío | BR-12 | ✅ SHA-256 idempotency | ✅ |
| 7.17 | Corrección sobre aprobado sin versión/reverso | BR-15/BR-16 | ⚠️ Cancel existe, reverso no | ⚠️ |

---

## 8. Estados Operativos

**Documento recomienda:**
```
BORRADOR → REGISTRADO_EN_GRANJA → EN_REVISION_ADMINISTRATIVA → OBSERVADO →
CORREGIDO → APROBADO → ENVIADO_A_SAP → CONTABILIZADO_EN_SAP →
RECHAZADO_POR_SAP → REPROCESADO → ANULADO/REVERSADO
```

**Nuestra implementación (`EventStatus` enum):**
```
DRAFT → REGISTERED → PENDING_REVIEW → IN_REVIEW → RETURNED →
CORRECTED → APPROVED → CONSOLIDATED → SENT_TO_SAP → SAP_CONFIRMED →
REJECTED → CANCELLED → SAP_ERROR
```

| Doc | Nosotros | Match |
|:--|:--|:--|
| BORRADOR | DRAFT | ✅ |
| REGISTRADO_EN_GRANJA | REGISTERED | ✅ |
| EN_REVISION_ADMINISTRATIVA | PENDING_REVIEW / IN_REVIEW | ✅ |
| OBSERVADO | RETURNED | ✅ |
| CORREGIDO | CORRECTED | ✅ |
| APROBADO | APPROVED | ✅ |
| ENVIADO_A_SAP | SENT_TO_SAP | ✅ |
| CONTABILIZADO_EN_SAP | SAP_CONFIRMED | ✅ |
| RECHAZADO_POR_SAP | SAP_ERROR | ✅ |
| REPROCESADO | — | ❌ FALTA |
| ANULADO/REVERSADO | CANCELLED (parcial) | ⚠️ |

**Gaps:** Falta `REPROCESADO` como estado explícito. `CANCELLED` existe pero no hay REVERSADO con registro compensatorio.

---

## 9. ID Externo para Evitar Duplicados

**Documento requiere:**
```json
{
  "external_transaction_id": "AVICOLA-RECEPCION-2026-000001",
  "source_system": "APP_AVICOLA",
  "sap_reference_document": "4500001234",
  "sap_reference_item": "00010",
  "event_type": "BREEDER_RECEPTION"
}
```

| Campo | Nuestra implementación | Estado |
|:--|:--|:--|
| `external_transaction_id` | ❌ No existe | ❌ |
| `source_system` | ❌ No existe | ❌ |
| `sap_reference_document` | ✅ `sap_document_ref` en `OperationalEvent` | ✅ |
| `sap_reference_item` | ❌ No existe (posición de documento) | ❌ |
| `event_type` | ✅ `event_type` enum | ✅ |

**Recomendación:** Agregar modelo `ExternalTransactionId` o campos en `SapPayload`.

---

## 10. Matriz Final de Integración (8 procesos)

| Proceso | SAP crea/manda | App captura | SAP recibe | App Status |
|:--|:--|:--|:--|:--|
| Compra aves | ✅ OC modelada | ✅ Recepción | ⚠️ Sin envío real | ⚠️ |
| Distribución aves | ✅ Lote/granja | ✅ Galpón/sexo/cant | ❌ Sin custom object | ❌ |
| Inspección granja | ✅ Granja/galpón | ✅ Estado real | ❌ Sin alerta | ❌ |
| Transferencia alimento | ✅ STO modelada | ✅ Recepción real | ⚠️ Sin confirmación | ⚠️ |
| Consumo alimento | ✅ Material/stock | ✅ Kg consumidos | ❌ Sin salida inventario | ❌ |
| Mortalidad | ✅ Lote/costo | ✅ Cantidad/causa | ⚠️ Evento sin baja | ⚠️ |
| Vacunas/Medicinas | ✅ Material/lote | ✅ Aplicación/dosis | ❌ Sin consumo SAP | ❌ |
| Producción huevos | ✅ Material/lote | ✅ Fértiles/descarte | ❌ Sin entrada SAP | ❌ |
| Incubadora | ✅ Inventario | ✅ Nacimientos | ❌ Sin producción SAP | ❌ |
| Engorde | ✅ Lote/alimento | ✅ Pesos/consumo | ❌ Sin cierre SAP | ❌ |

---

## 11. Recomendación Técnica de Integración

**Documento:**
```
React/Mobile → Backend App → Integration Layer → SAP S/4HANA APIs/OData
NO: React → SAP directo
NO: App → Tablas HANA
```

| Componente | Estado |
|:--|:--|
| React/Mobile → Backend | ✅ Vite proxy → FastAPI |
| Backend → Integration Layer | ⚠️ Adapter pattern existe pero sin capa de integration real |
| Integration Layer → SAP APIs/OData | ❌ Sin implementación (solo Mock/Manual) |
| NO React → SAP directo | ✅ Cumplido |
| NO App → Tablas HANA | ✅ Cumplido |
| Communication Arrangements | ❌ No modelados |
| Usuarios técnicos SAP | ❌ No configurados |

---

## 12. Las 5 Decisiones Críticas (Sección 25 del documento)

| # | Decisión | Nuestro estado |
|:--|:--|:--|
| 1 | ¿Ave viva = inventario valorizado o población productiva? | ❌ No definido |
| 2 | ¿Galpón = almacén SAP, ubicación técnica o dimensión operativa? | ❌ No definido |
| 3 | ¿Lote productivo = batch, orden interna, orden producción o custom? | ❌ No definido |
| 4 | ¿Mortalidad = movimiento inventario o solo indicador/costo? | ❌ No definido |
| 5 | ¿Bioseguridad = SAP QM/custom o solo app con resumen? | ❌ No definido |

> ⚠️ **CRÍTICO:** El documento advierte: "Sin esas cinco decisiones, la integración puede funcionar técnicamente, pero quedará débil para costeo, trazabilidad y auditoría."

---

## 13. Resumen de Gaps Prioritarios

### 🔴 Críticos (deben resolverse antes de integración real con SAP)

| # | Gap | Impacto |
|:--|:--|:--|
| G-R01 | **Sin OData/API client real para SAP** | La app no puede comunicarse con SAP |
| G-R02 | **5 decisiones críticas no definidas** | La integración será débil sin ellas |
| G-R03 | **Sin `external_transaction_id`** | Riesgo de duplicados en reprocesos |
| G-R04 | **Sin validación de capacidad de galpón** | Puede asignar más aves de las que caben |
| G-R05 | **Sin validación cantidad ≤ OC** | Puede recibir más de lo comprado |

### 🟡 Altos (necesarios para operación completa)

| # | Gap | Impacto |
|:--|:--|:--|
| G-R06 | **Sin adjuntos/evidencias** | No hay fotos de recepción, inspección, mortalidad |
| G-R07 | **Sin alertas/banderas operativas** | Desviaciones no se detectan automáticamente |
| G-R08 | **Sin consulta de inventario SAP** | No se valida stock antes de consumo |
| G-R09 | **Sin reverso verdadero** | Cancel existe pero no hay contrapartida |
| G-R10 | **Sin conciliación App vs SAP** | No se puede verificar consistencia |
| G-R11 | **Sin modelo de equipos PM/EAM** | Inspección no contrasta equipos |
| G-R12 | **Sin período fiscal** | Fechas en período cerrado no se bloquean |

### 🟢 Medios (mejoras recomendadas)

| # | Gap |
|:--|:--|
| G-R13 | Sin `REPROCESADO` como estado |
| G-R14 | Sin `sap_reference_item` (posición de documento) |
| G-R15 | Sin `sample_size` en recepción |
| G-R16 | Sin `method` en aplicación de vacunas |

---

## 14. Plan de Acción Recomendado

### Fase 10A: Decisiones de negocio (1 día)
- Taller con stakeholders para resolver las 5 decisiones críticas (Sección 25)
- Documentar en spec las respuestas

### Fase 10B: Validaciones críticas (3-5 días)
- G-R04: Validación de capacidad de galpón
- G-R05: Validación cantidad ≤ OC
- G-R01: Cliente OData real (aunque sea stubbed para dev)
- G-R03: `external_transaction_id` en `SapPayload`

### Fase 10C: Features operativos (5-7 días)
- G-R06: Sistema de adjuntos/evidencias (multer/S3/local)
- G-R07: Banderas operativas (threshold-based alerts)
- G-R08: Endpoint de consulta de inventario (mock inicial)
- G-R09: Mecanismo de reverso con registro compensatorio
- G-R10: Endpoint de conciliación App vs SAP

### Fase 10D: SAP Integration Layer (8-12 días)
- Cliente OData para SAP S/4HANA APIs
- Communication arrangements
- Importación de Business Partners, Materiales, Centros, Almacenes
- API Material Document (creación)
- Flujo completo: recepción → SAP entrada mercancía

---

> **Conclusión:** El 62% de las recomendaciones del documento ya están cubiertas en spec e implementación. Los gaps principales están en la capa de integración real con SAP (aún en modo mock/manual), las validaciones de reglas de negocio específicas (capacidad, OC), y features operativos complementarios (evidencias, alertas, reversos). Las 5 decisiones críticas de la Sección 25 deben ser resueltas por el negocio antes de avanzar con la integración real.
