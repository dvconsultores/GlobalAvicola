# 🥚 INFORME INTEGRAL — PROCESOS INCUBADORA (Hatchery)

**Fecha:** 2026-06-29  
**Equipo:** Especialista Incubación + Manual de Manejo + TI + SAP  
**Objetivo:** Evaluar completitud del sistema para manejo y registro de Incubadora e integración SAP

---

## INFORME 1 — PROCESOS DE INCUBADORA

### 9 operaciones — Estado actual

| # | Operación | SearchSelect | SAP | Estado |
|---|-----------|-------------|-----|--------|
| 1 | **Inspección de Incubadora** | ❌ Máquina (incubadora/nacedora) nativo | — | 🟡 PENDIENTE SearchSelect |
| 2 | **Recepción de Huevos** | ❌ Granja y transporte nativos | 🟡 SIN orden transferencia SAP | 🟡 PENDIENTE SearchSelect + SAP |
| 3 | **Clasificación de Huevos Recibidos** | N/A | — | ✅ COMPLETO |
| 4 | **Inspección de Transporte** | Transporte ✅ | — | ✅ COMPLETO |
| 5 | **Carga de Incubación** | ❌ Incubadora nativa | — | 🟡 PENDIENTE SearchSelect |
| 6 | **Ovoscopía** | N/A (numérico) | — | ✅ COMPLETO |
| 7 | **Transferencia a Nacedora** | ❌ Nacedora nativa | — | 🟡 PENDIENTE SearchSelect |
| 8 | **Registro de Nacimiento** | Vacuna ✅ | — | ✅ COMPLETO |
| 9 | **Despacho de Pollitos** | ❌ Granja y transporte nativos | 🟡 SIN SAP | 🟡 PENDIENTE SearchSelect + SAP |

---

## INFORME 2 — INTEGRACIÓN SAP EN INCUBADORA

### 2A. Flujo SAP ideal (huevos → pollitos)

```
Producción                    Incubadora                      Destino
──────────                    ──────────                      ──────
egg_dispatch ──────────────► egg_reception_hatchery
(transfer_order)              (debe referenciar la
                              misma transfer_order)
                              
                              incubation_load
                              ovoscopy
                              transfer_to_hatcher
                              birth_registration
                              chick_dispatch ──────────────► Granja engorde
                                                            (purchase_order
                                                             o transfer_order)
```

### 2B. Gaps SAP detectados

| Operación | Gap | Tipo SAP recomendado |
|-----------|-----|---------------------|
| `egg_reception_hatchery` | No tiene selector de orden SAP | `transfer_order` — debe referenciar la misma orden del `egg_dispatch` |
| `chick_dispatch` | No tiene selector de orden SAP | `purchase_order` o `transfer_order` — los pollitos se despachan con orden |

### 2C. Backend SAP (compartido)

| Capacidad | Estado |
|-----------|--------|
| Import/Export/Consolidate/Retry | ✅ |
| Multi-compañía | ✅ |
| `company.sap_config` | 🟡 Adapter pendiente |

---

## GAPS DETECTADOS — RESUMEN

### 🟡 SearchSelect pendientes (4 operaciones)

| Operación | Catálogo | Tipo |
|-----------|----------|------|
| `hatchery_inspection` | Incubadoras + Nacedoras | `sel()` nativo |
| `egg_reception_hatchery` | Granjas + Transportes | `sel()` nativo |
| `incubation_load` | Incubadoras | `sel()` nativo |
| `transfer_to_hatcher` | Nacedoras | `sel()` nativo |
| `chick_dispatch` | Granjas + Transportes | `sel()` nativo |

### 🔴 SAP pendientes (2 operaciones)

| Operación | Tipo SAP | Prioridad |
|-----------|---------|-----------|
| `egg_reception_hatchery` | `transfer_order` | Alta — es la contraparte de `egg_dispatch` |
| `chick_dispatch` | `purchase_order` | Alta — despacho de pollitos con orden |

---

## COMPARATIVA CON PROGENITORAS Y REPRODUCTORAS

| Etapa | Operaciones | SearchSelect | SAP integrado | Completitud |
|-------|------------|-------------|---------------|-------------|
| Progenitoras | 25 | 100% ✅ | 5 ops ✅ | 100% |
| Reproductoras | 24 | 100% ✅ | 4 ops ✅ | 100% |
| **Incubadora** | **9** | **5/9 🟡** | **0/2 🔴** | **~55%** |

---

## VEREDICTO

**Incubadora está al ~55%.** Las 5 operaciones que comparten catálogos con Progenitoras/Reproductoras (mortalidad, descarte, etc.) ya están al 100%. Pero 5 operaciones específicas de incubadora aún usan `<select>` nativo: inspección de máquinas, recepción de huevos, carga, transferencia a nacedora y despacho de pollitos. Adicionalmente, 2 operaciones críticas no tienen integración SAP: la recepción de huevos (debe referenciar la orden de traslado del despacho) y el despacho de pollitos (debe referenciar la orden de compra/traslado). Se recomienda corregir estos 7 gaps para alcanzar el 100%.

---

*Informe generado por evaluación multidisciplinaria: Especialista Incubación + Manual de Manejo + TI + SAP.*
