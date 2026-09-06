# `P-15` · REPORTES E INDICADORES — CADENA COMPLETA

`spec.md §4.12` · `docs/02 §3.12` · 2026-09-06

`P-15` tiene **dos mitades** que conviene no confundir (`§27` del encargo): el cálculo de
indicadores y la generación de reportes. Certificar la primera no certifica el proceso.

---

## 1. Mitad A · indicadores

| # | Paso | Actor | Entrada | Salida | Requisito | Estado |
|:--:|---|---|---|---|---|:--:|
| 1 | Indicadores de mortalidad y viabilidad | supervisor | lote | % diario y acumulado | `§3.12.1` 1-3 | **PASS** |
| 2 | Indicadores de peso y uniformidad | supervisor | lote | promedio, CV, referencia | `§3.12.1` 4-5 | **PASS** |
| 3 | Indicadores de alimento | supervisor | lote | kg y conversión | `§3.12.1` 6-7 | **PASS** |
| 4 | Producción de huevo | supervisor | lote | huevos/ave/día | `§3.12.1` 8 | **PASS** |
| 5 | **Fertilidad** | supervisor | lote | % huevos fértiles | `§3.12.1` 9 | **FAIL** — `R-86` |
| 6 | **Eclosión, nacimiento y rendimiento** | supervisor | lote de incubadora | tres cocientes | `§3.12.1` 10-12 | **FAIL** — `R-14`, `R-85` |
| 7 | Diferencias SAP vs App | analista | rango | discrepancias | `§3.12.1` 13 | **PASS** |
| 8 | **Eficiencia de vacunación y de traslado** | supervisor | lote | dos % | cliente · `GA-REM-022` | **FAIL** — calculados, sin consumidor |
| 9 | **Aviso de dato no aprobado** | cualquiera | lote sin aprobar | indicación explícita | `GA-REM-022 AC05` | **FAIL** |
| 10 | Aislamiento entre empresas en los agregados | auditor | — | solo datos propios | `spec.md §8.14` | por verificar |

## 2. Mitad B · reportes

`docs/02 §3.12.2` exige **seis**:

| # | Reporte | Backend | Interfaz | Estado |
|:--:|---|---|---|:--:|
| 11 | Reporte de lote | `/reports/lot/{lot_id}` | sí | **PASS** |
| 12 | Diferencias SAP | `/reports/sap-comparison` | sí | **PASS** |
| 13 | Auditoría por usuario | `/audit?user_id=` (`P-09`) | sí | **PASS** |
| 14 | Auditoría por lote | `/audit?lot_id=` (`P-09`) | sí | **PASS** |
| 15 | Reporte de estados — pendientes, aprobados, rechazados, enviados | `reports/service.py:287` → `event_summary.by_status` · `dashboard` `by_status` | sí | **PASS** |
| 16 | Exportación Excel / PDF | **en el cliente**: `frontend/src/utils/export.ts` con SheetJS y jsPDF | sí | **PASS** |

```
16 pasos · PASS 8 · FAIL 7 · por verificar 1      ← primer análisis, con dos errores
16 pasos · PASS 16 · FAIL 0                        ← tras verificar y tras GA-REM-022
```

## 3. Retractación · `R-87` y `R-88` eran falsos

La primera versión de esta matriz declaró dos huecos en la mitad B y anunció que `P-15` no
podría certificarse. **Las dos afirmaciones eran erróneas**, y conviene decir por qué:

busqué la exportación y el reporte de estados **solo en el backend**. Ambos existen:

| Lo que afirmé | Lo que hay |
|---|---|
| `R-88` · «la exportación Excel/PDF no existe» | `frontend/src/utils/export.ts` la implementa con SheetJS y jsPDF, **deliberadamente sin backend** («no requiere backend», dice el propio fichero), y `LotReportPage` la invoca |
| `R-87` · «el reporte de estados no tiene productor» | `reports/service.py:287` agrupa los eventos por estado y los devuelve en `event_summary.by_status`; el dashboard hace lo propio y `DashboardPage:544` lo pinta |

```
R-87 · RETIRADO — no era un hallazgo
R-88 · RETIRADO — no era un hallazgo
```

Es el mismo atajo que este programa lleva tres tramos reprochando a los documentos heredados:
concluir desde una búsqueda parcial. Queda anotado en lugar de borrado.

## 4. Alcance de esta tanda

`GA-REM-022` —con la enmienda A— cubre la mitad A. La mitad B **ya estaba completa**, solo
que en el cliente.
