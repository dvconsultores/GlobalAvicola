# PANELES Y KPI FRENTE A LA UNIDAD DE NEGOCIO

Auditoría del 2026-09-07 · 2 paneles · 16 endpoints de reporte · **solo lectura**

---

## 1. La fuga que no se tapa escondiendo pantallas

Un agregado no necesita mostrar una fila para revelarla. Si la mortalidad total de la empresa
incluye Incubadora, un usuario de Reproductoras que conozca la suya **deduce la de Incubadora
por diferencia**. Es la clase de fuga que sobrevive a cualquier filtro de listado.

## 2. La matriz

| KPI/Card | Source Data | Unidad | Currently Filtered by Company | Needs User Module Scope | Leakage Risk |
|---|---|---|:--:|:--:|:--:|
| `GET /dashboard/admin` | eventos, lotes, aprobaciones | **las cuatro** | sí | **sí** | **P1** |
| `GET /dashboard/mobile` | pendientes del usuario | derivable | sí | **sí** | **P1** |
| `/reports/kpis` | agregador | las cuatro | sí | **sí** | **P1** |
| `/reports/kpis/mortality` | `bird_movements` | las cuatro | sí | **sí** | **P1** |
| `/reports/kpis/feed-conversion` | `feed_movements` | las cuatro | sí | **sí** | **P1** |
| `/reports/kpis/afcr` | ídem | las cuatro | sí | **sí** | **P1** |
| `/reports/kpis/egg-production` | `egg_movements` | Progenitoras · Reproductoras | sí | **sí** | **P1** |
| `/reports/kpis/hatchery` | `hatchery_params` | **Incubadora** | sí | **sí** | **P1** |
| `/reports/kpis/animal-welfare` | inspecciones | las cuatro | sí | **sí** | **P2** |
| `/reports/kpis/production-index` | mixto | las cuatro | sí | **sí** | **P2** |
| `/reports/kpis/transfer-efficiency` | movimientos | **cruza unidades** | sí | **decisión** | **P1** |
| `/reports/kpis/vaccination-efficiency` | vacunación | las cuatro | sí | **sí** | **P2** |
| `/reports/kpi/ipe/{lot_id}` | por lote | derivable | sí | **sí** | **P1** |
| `/reports/kpi/weight-uniformity/{lot_id}` | por lote | derivable | sí | **sí** | **P1** |
| `/reports/lot/{lot_id}` | por lote | derivable | sí | **sí** | **P1** |
| `/reports/sap-comparison` | consolidado | las cuatro | sí | **decisión** | **P2** |

```
auditados ......... 16
seguros por unidad .. 0
con riesgo de fuga . 16
```

## 3. `P-15`, dicho con precisión

`P-15` está **funcionalmente certificado** y sigue estándolo: sus trece indicadores normativos
calculan lo que `docs/02 §3.12.1` exige. Lo que ninguno hace es acotar por unidad de negocio,
porque hasta hoy el requisito no existía.

Respuesta a la pregunta de `§33` del encargo:

```
¿Puede alguien con acceso solo a Reproductoras inferir datos de Incubadora?

SÍ, hoy, por dos vías:
  · directamente, porque `/reports/kpis/hatchery` responde y es de Incubadora
  · indirectamente, porque los agregados totales incluyen las cuatro
```

## 4. Los dos que además necesitan decisión

`transfer-efficiency` mide precisamente el **paso entre unidades**. Filtrarlo por una sola lo
haría incalculable. Es un indicador que, por naturaleza, o cruza o no existe.

`sap-comparison` contrasta lo enviado con lo registrado, y la consolidación agrupa las cuatro.

Ninguno se resuelve con un filtro: los dos necesitan que el propietario diga qué debe ver quien
tiene una sola unidad.
