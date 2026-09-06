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
| 15 | **Reporte de estados** — pendientes, aprobados, rechazados, enviados | **ninguno** | no | **FAIL** — `R-87` |
| 16 | **Exportación Excel / PDF** | **ninguna** | no | **FAIL** — `R-88` |

```
16 pasos · PASS 8 · FAIL 7 · por verificar 1
```

## 3. Los dos huecos de la mitad B

```
R-87 · P2 · «Reporte de estados» (pendientes, aprobados, rechazados, enviados) es uno de los
            seis reportes de docs/02 §3.12.2 y no tiene productor.

R-88 · P1 · «Exportación Excel/PDF» es normativa en spec.md §4.12 y en docs/02 §3.12.2.
            No existe: ni endpoint, ni biblioteca declarada en pyproject.toml, ni superficie
            en la interfaz. El `POST /sap/export` es otra cosa —el envío del payload a SAP—.
```

`R-88` no es una corrección: es **desarrollo nuevo** que exige elegir biblioteca, formato,
contenido y filtros de cada informe exportable. Nada de eso está especificado.

## 4. Alcance de esta tanda

`GA-REM-022` cubre la mitad A y **solo** la mitad A: su título es «completitud de KPI» y sus
cinco criterios hablan de indicadores. **Ninguna spec vigente cubre `R-87` ni `R-88`.**

Por tanto:

```
AUTORIZADO POR SPEC   ·  mitad A — GA-REM-022, con enmienda para R-85 y R-86
NO AUTORIZADO         ·  mitad B — R-87 y R-88 carecen de spec, y R-88 es desarrollo nuevo
```

Se cierra la mitad A y se declara la B. **`P-15` no podrá certificarse en esta tanda**, y
decirlo por adelantado es más útil que descubrirlo al final.
