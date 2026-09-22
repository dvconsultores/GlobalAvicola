# Estrategia de Integración SAP S/4HANA — Global Avícola

> **Documento:** 10-sap-integration-strategy.md
> **Versión:** 1.1.0
> **Fecha:** 2026-06-23
> **Target:** SAP S/4HANA
>
> **ADDENDUM 2026-09-22 (SAP-SOAP-1)**: el mecanismo **inbound** acordado con Lider Pollo y su proveedor SAP es **SOAP (pull)**; la recomendación previa de **OData** queda `SUPERSEDED_BY_OWNER_AND_PROVIDER_DECISION` para inbound (historia preservada, no se borra). El contrato vigente vive en `audit/sap-soap/**` y `specs/003-sap-soap-inbound-contract/`. Direct HANA queda `RETIRED_AS_TARGET_ARCHITECTURE`.

---

## 1. PRINCIPIO RECTOR

**SAP S/4HANA es y seguirá siendo el sistema principal administrativo, contable y de inventario formal** (módulos MM, FI, CO, PP). Global Avícola es una capa auxiliar operativa que:

1. **Importa** datos maestros y documentos desde SAP (referencia)
2. **Captura** datos operativos en campo
3. **Valida, corrige y aprueba** los datos operativos
4. **Consolida** movimientos aprobados
5. **Envía** datos consolidados a SAP de forma controlada
6. **Audita** cada paso del proceso

**Ningún dato operativo llega a SAP sin pasar por revisión, corrección (si aplica) y aprobación.**

---

## 2. ARQUITECTURA DE INTEGRACIÓN (ADAPTER PATTERN)

```
┌──────────────────────────────────────────────┐
│           DOMINIO AVÍCOLA                     │
│  (Lotes, Eventos, Revisión, Aprobación)      │
│  NO CONOCE DETALLES DE SAP                    │
└──────────────────┬───────────────────────────┘
                   │ Depende de interfaz
┌──────────────────┴───────────────────────────┐
│       SAP INTEGRATION INTERFACE (ABC)          │
│  + import_masters_from_s4hana()                │
│  + import_documents_from_s4hana()              │
│  + export_consolidated_movements_to_s4hana()   │
│  + check_s4hana_connection()                   │
│  + get_odata_service_status()                  │
└──────────────────┬───────────────────────────┘
                   │ Implementaciones
     ┌─────────────┼─────────────┬──────────────┐
     ▼             ▼             ▼              ▼
┌─────────┐ ┌──────────┐ ┌─────────────┐ ┌────────────────┐
│ MANUAL  │ │ SFTP     │ │ OData S/4   │ │ SOAP / IDoc    │
│ (Mock)  │ │ CSV/JSON │ │ HANA (REC)  │ │ (Alternativo)  │
└─────────┘ └──────────┘ └─────────────┘ └────────────────┘
```

### Principios:
- El dominio avícola NUNCA importa/conoce clases concretas de SAP
- La interfaz de integración define qué operaciones existen
- Cada implementación concreta sabe CÓMO comunicarse con SAP
- Cambiar de un mecanismo a otro NO requiere tocar el dominio

---

## 3. DIRECCIONES DE INTEGRACIÓN

### 3.1 SAP → Global Avícola (IMPORT)

| Datos a importar | Frecuencia | Mecanismo inicial |
|---|---|---|
| Órdenes de Compra (Purchase Orders) | Bajo demanda / Diario | Manual (CSV/JSON upload) |
| Órdenes de Transferencia (Transfer Orders) | Bajo demanda | Manual |
| Centros (Plants) | Inicial + cambios | Manual |
| Almacenes (Storage Locations) | Inicial + cambios | Manual |
| Materiales (Material Masters) | Inicial + cambios | Manual |
| Proveedores (Vendors) | Inicial + cambios | Manual |
| Lotes SAP (Batches) | Bajo demanda | Manual |

### 3.2 Global Avícola → SAP (EXPORT)

| Datos a exportar | Frecuencia | Condición |
|---|---|---|
| Recepción de mercancía (Goods Receipt) | Tras aprobación | Movimientos de recepción de aves/alimento |
| Salida de mercancía (Goods Issue) | Tras aprobación | Movimientos de salida/transferencia |
| Transferencias entre centros | Tras aprobación | Movimientos entre granjas |
| Ajustes de inventario | Tras aprobación | Diferencias validadas |
| Consumo de material | Tras aprobación | Consumo de alimento, vacunas |

---

## 4. FLUJO DE DATOS GA → SAP

```
1. REGISTRO OPERATIVO
   ↓
2. ENVIADO A REVISIÓN
   ↓
3. REVISIÓN (Supervisor)
   ↓
4. CORRECCIÓN (si aplica, auditada)
   ↓
5. APROBACIÓN (Aprobador)
   ↓
6. CONSOLIDACIÓN
   - Agrupa movimientos aprobados por lote/período
   - Valida integridad (totales, referencias SAP)
   - Genera ConsolidatedMovement
   ↓
7. PREPARACIÓN DE PAYLOAD
   - Transforma ConsolidatedMovement → SapPayload
   - Genera idempotency_key (SHA-256)
   ↓
8. ENVÍO A SAP
   - Llama al adapter concreto
   - Registra intento en SapSyncJob
   ↓
9. RECEPCIÓN DE RESPUESTA
   ├── ÉXITO → SapPayload.status = CONFIRMED
   │         → SapResponse con ID de documento SAP
   └── ERROR → SapPayload.status = FAILED
             → SapResponse con código de error
             → Reintento automático (hasta 3 veces)
             → Notificación al analista SAP
```

---

## 5. IDEMPOTENCIA

**Problema:** Un movimiento no debe enviarse dos veces a SAP.

**Solución:**
1. Cada SapPayload tiene una `idempotency_key` única
2. La clave se genera como: `SHA-256(lot_id + event_type + event_date + sap_reference + consolidated_data)`
3. Antes de enviar, se verifica si ya existe un SapPayload con esa clave en estado CONFIRMED
4. Si existe → se omite el envío (ya fue procesado)
5. Si no existe → se envía normalmente

---

## 6. MANEJO DE ERRORES SAP

### 6.1 Códigos de error comunes

| Error | Causa probable | Acción |
|---|---|---|
| Documento duplicado | Ya existe en SAP | Marcar como CONFIRMED (idempotencia) |
| Material no encontrado | Código de material incorrecto | Notificar analista SAP |
| Centro no válido | Centro no existe o está bloqueado | Notificar analista SAP |
| Cantidad excede disponible | Stock insuficiente en SAP | Revisar diferencias de inventario |
| Error de conexión | SAP no disponible | Reintento automático |
| Error de autorización | Credenciales SAP inválidas | Notificar administrador |

### 6.2 Política de reintentos

- Máximo 3 reintentos
- Backoff exponencial: 1min, 5min, 15min
- Si falla el 3er intento → marcar como FAILED permanentemente
- Notificar al rol "Analista SAP"
- Intervención manual requerida

---

## 7. MODO INICIAL: MANUAL

Dado que no se ha confirmado conectividad directa con SAP:

1. **Importación:** El analista SAP descarga archivos desde SAP (CSV, Excel) y los carga en Global Avícola a través de una interfaz de importación.
2. **Exportación:** Global Avícola genera archivos (CSV, JSON, XML) con los movimientos consolidados. El analista SAP los descarga y los procesa en SAP.
3. **Referencias SAP:** Los códigos SAP (órdenes, materiales, centros) se ingresan manualmente o por importación de archivo.

### Interfaz de importación manual:
- Upload de archivo CSV/Excel con mapeo de columnas
- Vista previa de datos antes de importar
- Validación de datos (formatos, referencias existentes)
- Registro de auditoría de cada importación

### Interfaz de exportación manual:
- Selección de movimientos consolidados
- Generación de archivo en formato requerido
- Descarga
- Registro de auditoría de cada exportación

---

## 8. MECANISMOS DE INTEGRACIÓN CON SAP S/4HANA

SAP S/4HANA ofrece las siguientes vías de integración nativas. El diseño soporta todas sin cambios en el dominio:

| Mecanismo | Descripción | S/4HANA Nativo | Complejidad |
|---|---|---|---|
| **OData REST Services** | APIs RESTful estándar de S/4HANA (recomendado) | ✅ Sí | Baja |
| **SOAP Web Services** | Servicios web clásicos, aún soportados | ✅ Sí | Media |
| **IDoc (Intermediate Documents)** | Formato estándar de intercambio SAP | ✅ Sí | Media |
| **CDS Views** | Core Data Services para extracción de datos | ✅ Sí | Media |
| **SAP API Business Hub** | Catálogo oficial de APIs pre-construidas | ✅ Sí | Baja |
| **SAP Cloud Connector** | Túnel seguro para entornos cloud SAP | ✅ Sí | Media |
| **Archivo plano (SFTP)** | CSV/JSON vía SFTP | ✅ Sí | Baja |

**Mecanismo recomendado para S/4HANA:** OData REST Services + SAP API Business Hub.

**Modo inicial:** Manual (archivos CSV/JSON) hasta que los servicios OData de SAP estén expuestos y probados.

---

## 9. ENTIDADES DE INTEGRACIÓN

| Entidad | Propósito |
|---|---|
| **SapReference** | Referencia a cualquier objeto SAP (orden, centro, material, etc.) |
| **SapSyncJob** | Trabajo de sincronización (lote de importación o exportación) |
| **SapPayload** | Payload individual para envío a SAP |
| **SapResponse** | Respuesta de SAP a un payload |
| **SapIntegrationAdapter** | Interfaz abstracta (ABC en Python) |
| **ManualSapAdapter** | Implementación concreta para modo manual |
| **RestSapAdapter** | Implementación concreta para API REST (futuro) |

---

## 10. SEGURIDAD EN INTEGRACIÓN

1. Credenciales SAP NUNCA en código → variables de entorno / secrets manager
2. Comunicación encriptada (HTTPS/TLS) para API
3. SFTP con clave privada para archivos
4. Payloads de SAP almacenados con acceso restringido (solo rol SAP)
5. Auditoría de cada envío/importación
6. Validación de datos antes de enviar a SAP
7. No exponer errores de SAP con detalles sensibles al frontend

---

## 11. PRUEBAS DE INTEGRACIÓN

1. **Mock SAP:** Adaptador mock que simula respuestas SAP
2. **Tests de idempotencia:** Verificar que no se envían duplicados
3. **Tests de reintento:** Simular fallos y verificar reintentos
4. **Tests de consolidación:** Verificar agrupación correcta
5. **Tests de payload:** Validar formato correcto según especificación SAP
6. **Tests de errores:** Simular cada tipo de error SAP

---

## 12. CRITERIOS DE ACEPTACIÓN SAP

- [ ] Se pueden importar referencias SAP manualmente
- [ ] Los movimientos aprobados se consolidan correctamente
- [ ] Se genera payload para SAP con formato correcto
- [ ] La idempotencia evita envíos duplicados
- [ ] Los errores de SAP se registran y notifican
- [ ] Se puede cambiar el mecanismo de integración sin modificar el dominio
- [ ] Cada envío queda auditado
- [ ] Los reintentos funcionan con backoff exponencial
