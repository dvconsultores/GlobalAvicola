# GA-REM-022 — COMPLETITUD DE KPI

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-022` · **Tipo** `FUNCTIONAL GAP SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P1** · **Estado** `SPEC_READY` |
| **Dependencias** | `GA-REM-001` · `GA-REM-011` (4 KPI son endpoints huérfanos) |
| **Hallazgos** | **R-14** (nuevo, no estaba en la auditoría) · `audit/06 §P-15` (4 endpoints huérfanos) |

## Problema
Dos defectos distintos sobre los KPI:

1. **La Tasa de Eclosión devuelve un texto en lugar de un número**, pese a que los datos necesarios ya existen en el sistema.
2. **Cuatro endpoints de KPI no tienen ningún consumidor** en el frontend.

## Evidencia

### Defecto 1 — Tasa de Eclosión
```python
# backend/app/reports/service.py:145-147
return {
    "total_chicks_born": born,
    "hatchability_pct": "N/A (requiere datos de carga de incubación)",
    "note": "Para hatchability completa se necesitan datos de huevos cargados en incubadoras",
}
```
La afirmación del comentario **es falsa**: los datos existen.
- `HatcheryParams.quantity_loaded` almacena los huevos cargados (`operations/models.py:207`).
- `get_hatchery_egg_balance` ya los suma (`validators.py:97-105`).

El cliente exige este KPI explícitamente: *«Indicadores Calculables: 1. Tasa de Eclosión»* para Incubadora, y *«Tasa de Fertilidad»* para Reproductora Producción y para el traslado de huevo fértil.

### Defecto 2 — KPI huérfanos
| Endpoint | Consumidor |
|---|---|
| `GET /reports/kpis/animal-welfare` | ninguno |
| `GET /reports/kpis/production-index` | ninguno |
| `GET /reports/kpis/transfer-efficiency` | ninguno |
| `GET /reports/kpis/vaccination-efficiency` | ninguno |

Los cuatro están **implementados** en `reports/service.py`. Los dos últimos corresponden a KPI que el cliente exige (*«Eficiencia de Vacunación»*, *«Eficiencia de Traslado»*).

## Comportamiento esperado
Todos los KPI que el cliente exige se calculan con valor numérico y son accesibles desde la interfaz.

## Alcance
1. Implementar el cálculo real de la Tasa de Eclosión con los datos existentes.
2. Contrastar la lista de KPI exigidos por el cliente contra los implementados y los expuestos.
3. Exponer en la interfaz los KPI implementados y huérfanos que el cliente exige.
4. Revisar el criterio de estado: hoy los KPI solo cuentan eventos ya aprobados, lo que hace que sean cero hasta que se aprueban. Documentarlo o exponerlo en la interfaz.

## KPI exigidos por el cliente vs implementación
| KPI exigido | Etapa | Implementado | Expuesto en UI |
|---|---|---|---|
| Tasa de Fertilidad | Reproductora Producción · Traslado HF | parcial (`egg-production`) | sí |
| Porcentaje de Huevos Infértiles | Reproductora Producción | por confirmar | por confirmar |
| Porcentaje de Huevos Descartados | Reproductora Producción | por confirmar | por confirmar |
| Peso Promedio de los Huevos | Reproductora Producción | sí | sí |
| Consumo de Alimento por Huevo | Reproductora Producción | por confirmar | por confirmar |
| Tasa de Mortalidad | todas | sí | sí |
| **Tasa de Eclosión** | Incubadora | **devuelve texto** | sí, vacío |
| Tasa de Mortalidad de Pollitos | Incubadora | por confirmar | por confirmar |
| **Eficiencia de Vacunación** | Incubadora | **sí, huérfano** | **no** |
| Porcentaje de Pollitos Sanos | Incubadora | por confirmar | por confirmar |
| **Eficiencia de Traslado** | Incubadora · Traslado HF | **sí, huérfano** | **no** |
| Conversión Alimenticia | Engorde | sí | sí |

## Base de datos afectada
Ninguna prevista: los datos existen.

## Acceptance Criteria
**AC01 — La Tasa de Eclosión es un número**
```
Given un lote de incubadora con carga de incubación y nacimiento registrados
When  se consulta GET /api/v1/reports/kpis/hatchery
Then  hatchability_pct es un valor numérico
And   equivale a nacidos viables dividido entre huevos cargados, en porcentaje
```
**AC02 — Sin datos suficientes se informa con claridad**
```
Given un lote sin carga de incubación registrada
When  se consulta el KPI
Then  se devuelve un valor nulo con un indicador explícito de dato insuficiente
And   no un texto en español embebido en un campo numérico
```
**AC03 — Los KPI exigidos están expuestos**
```
Given los KPI que el cliente exige y que están implementados
When  se abre la pantalla de reportes del lote
Then  todos son visibles
```
**AC04 — Contraste documentado**
```
Given la lista de KPI del documento del cliente
When  se contrasta con la implementación
Then  cada KPI tiene estado: implementado y expuesto · implementado y huérfano · no implementado
```
**AC05 — El criterio de estado es explícito**
```
Given que los KPI solo consideran eventos aprobados
When  un usuario consulta un lote con eventos aún no aprobados
Then  la interfaz lo indica, en lugar de mostrar cero sin explicación
```

## Riesgos
| Riesgo | Mitigación |
|---|---|
| El cálculo de eclosión se hace con un denominador equivocado | AC01 fija la fórmula; se valida con datos de prueba derivados del cliente |
| Exponer KPI huérfanos sin validar su cálculo | cada KPI expuesto requiere test con datos conocidos |

## Definition of Done
- [ ] AC01–AC05 verificados · [ ] Contraste completo documentado · [ ] Tests con datos conocidos por KPI expuesto · [ ] Certification report
