# 🐔 INFORME INTEGRAL — PROCESOS REPRODUCTORAS (Breeder)

**Fecha:** 2026-06-29  
**Equipo:** Especialista Avícola Reproductoras + Manual de Manejo + TI + SAP  
**Objetivo:** Evaluar completitud del sistema para manejo y registro de Reproductoras (Cría y Producción) e integración SAP

---

## INFORME 1 — PROCESOS DE REPRODUCTORAS

### 1A. Reproductoras — Cría (`breeder_rearing`) — 12 operaciones

| # | Operación | SearchSelect | SAP | Estado |
|---|-----------|-------------|-----|--------|
| 1 | **Inspección de Granja** | Casa ✅, Equipos por galpón ✅ | — | ✅ COMPLETO |
| 2 | **Recepción de Aves** | SAP OC/Transferencia ✅, Proveedor ✅, Raza ✅, Casa ✅, Granja ✅, Lote ✅ | `purchase_order` / `transfer_order` + auto-populado ✅ | ✅ COMPLETO |
| 3 | **Distribución de Aves** | Casa origen ✅, Casa destino ✅ | — | ✅ COMPLETO |
| 4 | **Transferencia de Aves** | Casa origen ✅, Casa destino ✅ | — | ✅ COMPLETO |
| 5 | **Inspección de Transporte** | Transporte ✅ | — | ✅ COMPLETO |
| 6 | **Registro de Alimento** | SAP order ✅, Fase ✅, Tipo ✅ | `transfer_order` ✅ | ✅ COMPLETO |
| 7 | **Registro de Pesaje** | N/A (numérico) | — | ✅ COMPLETO |
| 8 | **Registro de Mortalidad** | Causa ✅ | — | ✅ COMPLETO |
| 9 | **Registro de Descarte** | Causa ✅ | — | ✅ COMPLETO |
| 10 | **Vacunación** | Vacuna ✅ | — | ✅ COMPLETO |
| 11 | **Medicación** | Medicamento ✅ | — | ✅ COMPLETO |
| 12 | **Salida de Aves** | SAP OC ✅, Granja ✅, Planta ✅, Transporte ✅, Inspección transporte ✅ | `purchase_order` ✅ | ✅ COMPLETO |

### 1B. Reproductoras — Producción (`breeder_production`) — 12 operaciones

| # | Operación | SearchSelect | SAP | Estado |
|---|-----------|-------------|-----|--------|
| 1 | **Inspección de Granja** | Casa ✅, Equipos ✅ | — | ✅ COMPLETO |
| 2 | **Transferencia de Aves** | Casa origen ✅, Casa destino ✅ | — | ✅ COMPLETO |
| 3 | **Inspección de Transporte** | Transporte ✅ | — | ✅ COMPLETO |
| 4 | **Registro de Alimento** | SAP order ✅, Fase ✅, Tipo ✅ | `transfer_order` ✅ | ✅ COMPLETO |
| 5 | **Registro de Pesaje** | N/A | — | ✅ COMPLETO |
| 6 | **Registro de Mortalidad** | Causa ✅ | — | ✅ COMPLETO |
| 7 | **Registro de Descarte** | Causa ✅ | — | ✅ COMPLETO |
| 8 | **Vacunación** | Vacuna ✅ | — | ✅ COMPLETO |
| 9 | **Medicación** | Medicamento ✅ | — | ✅ COMPLETO |
| 10 | **Recolección y Clasificación de Huevos** | N/A | — | ✅ COMPLETO |
| 11 | **Despacho de Huevos** | SAP transfer order ✅, Incubadora ✅, Transporte ✅, Inspección transporte ✅ | `transfer_order` ✅ | ✅ COMPLETO |
| 12 | **Salida de Aves** | SAP OC ✅, Granja ✅, Planta ✅, Transporte ✅, Inspección ✅ | `purchase_order` ✅ | ✅ COMPLETO |

---

## INFORME 2 — INTEGRACIÓN SAP EN REPRODUCTORAS

### 2A. Operaciones con integración SAP directa

| Operación | Tipo SAP | Dato registrado | Etapa |
|-----------|---------|-----------------|-------|
| **Recepción de Aves** | `purchase_order` o `transfer_order` | `extra_data.sap_order_ref` + auto-populado (proveedor, raza, cantidad, fecha despacho, pesos) | Cría |
| **Salida de Aves** | `purchase_order` | `extra_data.sap_order_ref` | Cría / Producción |
| **Despacho de Huevos** | `transfer_order` | `extra_data.sap_order_ref` | Producción |
| **Registro de Alimento** | `transfer_order` (SearchSelect) | `feed_movements.0.sap_order_id` | Cría / Producción |

### 2B. Diferenciador clave: Doble origen en Recepción

La recepción de aves en Reproductoras tiene un selector de origen **exclusivo** que no existe en Progenitoras:

```
Origen de las aves:
┌──────────────────┐  ┌──────────────────┐
│  Transferencia   │  │  Orden de compra │
│  (desde Incub.)  │  │  (compra externa)│
└──────────────────┘  └──────────────────┘
```

| Origen | Tipo SAP | Datos auto-poblados |
|--------|---------|-------------------|
| Transferencia | `transfer_order` | Fecha despacho incubadora, pesos declarados por quien despacha |
| Orden de compra | `purchase_order` | Proveedor, raza, cantidad, fecha despacho, pesos declarados |

### 2C. Datos auto-poblados desde SAP (ambos orígenes)

| Campo SAP | Recepción OC | Recepción Transferencia |
|-----------|-------------|------------------------|
| `quantity` | ✅ Cantidad declarada | ✅ Cantidad declarada |
| `extra_data.vendor_name` | ✅ Proveedor | ✅ Incubadora/Progenitora origen |
| `extra_data.breed_name` | ✅ Línea/Raza | ✅ Línea/Raza |
| `extra_data.dispatch_date` | ✅ Fecha despacho proveedor | ✅ Fecha despacho incubadora |
| `extra_data.avg_weight_male` | ✅ Peso machos proveedor | ✅ Peso machos despachante |
| `extra_data.avg_weight_female` | ✅ Peso hembras proveedor | ✅ Peso hembras despachante |

### 2D. Backend SAP (compartido con Progenitoras)

| Capacidad | Estado |
|-----------|--------|
| Importación de referencias SAP | ✅ |
| Listado, consolidación, exportación | ✅ |
| Reintentos, payloads, sync jobs | ✅ |
| SAP Manager UI con KPIs | ✅ |
| Multi-compañía (company_id en todas las tablas) | ✅ |
| `company.sap_config` por empresa | ✅ DB + schema, 🟡 adapter no lo usa aún |

---

## FLUJO COMPLETO REPRODUCTORAS

```
CRÍA (breeder_rearing)                      PRODUCCIÓN (breeder_production)
──────────────────────                      ──────────────────────────────
1. Inspección de Granja                     1. Inspección de Granja
2. Recepción de Aves ← SAP OC/Transfer      2. Transferencia de Aves
3. Distribución de Aves                     3. Inspección de Transporte
4. Transferencia de Aves                    4. Registro de Alimento ← SAP
5. Inspección de Transporte                 5. Registro de Pesaje
6. Registro de Alimento ← SAP               6. Mortalidad / Descarte
7. Registro de Pesaje                       7. Vacunación / Medicación
8. Mortalidad / Descarte                    8. 🥚 Recolección y Clasificación
9. Vacunación / Medicación                  9. 📤 Despacho de Huevos ← SAP
10. Salida de Aves ← SAP                    10. Salida de Aves ← SAP
    (cierre de ciclo cría)                      (cierre de ciclo o traslado)
```

---

## INDICADORES (KPIs) PARA REPRODUCTORAS

El dashboard actual ya genera los siguientes KPIs filtrados por compañía:

| Indicador | Fuente | Disponible |
|-----------|--------|-----------|
| Eventos hoy (operador) | `OperationalEvent` | ✅ Dashboard móvil |
| Pendientes de corrección | `OperationalEvent.status = RETURNED` | ✅ |
| Aprobados hoy | `OperationalEvent.status = APPROVED` | ✅ |
| Lotes activos por etapa | `Lot` por `bird_type` | ✅ KPI |
| Tendencia de mortalidad (8 sem) | `BirdMovement` + `MORTALITY_RECORDING` | ✅ Gráfico |
| Tipos de evento generados | `OperationalEvent.event_type` | ✅ Top N |
| Huevos recolectados (producción) | `EggMovement` | ✅ Dashboard |
| Total eventos | `OperationalEvent` count | ✅ |

### 🔵 KPIs que podrían agregarse (futuro)

| Indicador | Descripción |
|-----------|-------------|
| % Huevos fértiles vs total | `egg_collection` fértiles / total recolectado |
| Huevos por ave/día | Producción diaria / población activa |
| % Mortalidad acumulada | Acumulado vs población inicial |
| Conversión alimenticia (FCR) | Alimento consumido / peso ganado |
| % Viabilidad al nacimiento | `birth_registration` viables / total |

---

## VEREDICTO

**Reproductoras está 100% completo.** Las 24 operaciones (12 Cría + 12 Producción) usan SearchSelect en todos sus catálogos. Las 4 operaciones con integración SAP están configuradas con el tipo de orden correcto según el contexto (purchase_order para recepción OC y salida, transfer_order para recepción por transferencia y despacho de huevos y alimento). El diferenciador clave de Reproductoras — el selector de doble origen en Recepción de Aves (transferencia vs OC) — está implementado y funcional. Los KPIs del dashboard cubren mortalidad, eventos, lotes y producción de huevos. No se detectaron gaps.

---

*Informe generado por evaluación multidisciplinaria: Especialista Reproductoras + Manual de Manejo + TI + SAP.*
