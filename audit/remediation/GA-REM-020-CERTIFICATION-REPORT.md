# GA-REM-020 — CERTIFICATION REPORT

| | |
|---|---|
| **GA-REM** | `GA-REM-020` — Validación de cobertura funcional contra la documentación del cliente |
| **Fecha** | 2026-09-03 |
| **Wave** | 1 |
| **Estado final** | **`CERTIFIED`** |

## Finding
**R-15** — El repositorio contiene 43 documentos funcionales del cliente que **nunca se habían usado para validar la implementación**. La auditoría los registró como «fuente disponible y no explotada formalmente». Una lectura parcial durante la revalidación ya había producido dos requisitos incumplidos, lo que sugería más huecos sin detectar.

## Source
| Nivel | Documento | Uso |
|---|---|---|
| 1 | `Bases Consideradas en el Desarrollo de la App Avicola.pdf` (13 pág.) | requisitos originales: datos diarios y KPI por etapa |
| 2 | `Recomendación central.pdf` (29 pág.) | arquitectura funcional, 17 reglas obligatorias, 11 estados, datos por proceso |
| 2 | `Control de Codificación de Procesos Avicolas PROTINAL.xlsx` | inventario de 30 procesos — lista de comprobación |
| 2 | `Sap y App Proceso Avícola Software primera version.pdf` (34 pág.) | contexto de negocio |
| 3 | Manuales Ross / Cobb | estándares técnicos de referencia |
| 4 | Capturas del sistema legacy | `NOT_VERIFIABLE` — imágenes sin texto |
| 5 | 30 formatos `AVI-*.xlsx` | **`RA-04` plantillas vacías** — no se infirió nada |

## Spec
`specs/remediation/GA-REM-020-FUNCTIONAL-COVERAGE-VALIDATION.md` — 7 AC, 4 tests.

## AC — verificación

| AC | Criterio | Resultado |
|---|---|---|
| AC01 | Matriz completa con estado y evidencia por elemento | ✅ **96 elementos** validados, cada uno con estado y evidencia (ruta y línea, o ausencia verificada) |
| AC02 | Los huecos generan hallazgos con destino | ✅ **10 hallazgos** (`R-13` … `R-22`), todos con severidad y spec destino |
| AC03 | Las coberturas positivas citan evidencia en el código | ✅ 57 `COVERED` con ruta y línea |
| AC04 | Cobertura de los procesos del cliente comprobada | ✅ 17 procesos PESADAS: 12 `COVERED`, 5 `PARTIAL`, **0 `ABSENT`**; 13 LIVIANAS `OUT_OF_SCOPE` |
| AC05 | La taxonomía del proyecto NO se modifica | ✅ 0 archivos de aplicación modificados; `processCatalog.ts` intacto; 0 identificadores `AVI-*` introducidos |
| AC06 | Los estándares técnicos se validan | ✅ 6 elementos: 5 `COVERED`, 1 `ABSENT` (`R-18`, curva de peso) |
| AC07 | Las discrepancias se escalan, no se resuelven | ✅ `RC-07` abierto (política de mortalidad frente a SAP); ninguna spec ni código modificados para resolverlo |

## Tests ejecutados

| ID | Verificación | Resultado |
|---|---|---|
| `T-020-01` | completitud de la matriz | 96 elementos con estado · **PASS** |
| `T-020-02` | sin cambios en código ni `processCatalog.ts` | `backend/app` 0 · `frontend/src` 0 · `alembic/versions` 0 · `processCatalog.ts` 0 · **PASS** |
| `T-020-03` | no se introdujeron identificadores `AVI-*` | 1 única aparición = placeholder preexistente en `LotFormPage.tsx:129`, sin cambios · **PASS** |
| `T-020-04` | cada hueco tiene hallazgo y destino | 10 hallazgos, 10 destinos · **PASS** |

**PASS 4 · FAIL 0**

## Resultados de la validación

```
COVERED ......... 57 (59 %)
PARTIAL ......... 25 (26 %)
ABSENT ..........  5 ( 5 %)
OUT_OF_SCOPE ....  6 ( 6 %) + 13 procesos LIVIANAS
NOT_VERIFIABLE ..  2 ( 2 %)
REQ_CONFLICT ....  1 ( 1 %)
```

### Conclusiones de negocio

1. **Ningún proceso de negocio del cliente está ausente.** Los 17 procesos PESADAS en alcance tienen cobertura funcional; los 5 parciales lo son por dos defectos ya identificados (P0-1 mortalidad, P0-11 trazabilidad), no por funcionalidad faltante.
2. **La app respeta las 6 prohibiciones arquitectónicas del cliente**: no crea órdenes de compra, materiales ni almacenes, no cambia costos, no ajusta inventario sin documento SAP y no cierra órdenes. No invade el ámbito mandante de SAP.
3. **El déficit dominante está en los KPI, no en la captura de datos.** 22 de 26 datos diarios exigidos están cubiertos; en cambio 12 de 18 KPI están `PARTIAL`: cinco implementados sin consumidor y siete derivables de datos ya capturados que nunca se calcularon.
4. **6 de las 17 reglas obligatorias del cliente son inaplicables** por no consumir maestros ni inventario de SAP. No son defectos independientes: son consecuencia de que la integración real no existe.
5. **La máquina de estados del proyecto se corresponde con los 11 estados operativos del cliente** en 9 de 11 casos directos.
6. **`SapPayload` ya declara los tres campos anti-duplicados** que el cliente exige (`external_transaction_id`, `source_system`, `sap_reference_item`) y **ninguno se puebla jamás** (`R-21`).

## Hallazgos producidos

| ID | Severidad | Destino |
|---|---|---|
| R-13 consumo de agua | P1 | `GA-REM-021` |
| R-14 tasa de eclosión | P1 | `GA-REM-022` |
| R-15 documentación sin validar | P1 | **cerrado por esta spec** |
| R-16 rotación de huevos incompleta | P2 | backlog |
| R-17 12 KPI parciales | P1 | `GA-REM-022` (ampliada) |
| R-18 sin curva de peso estándar | P2 | backlog |
| R-19 sin validación de unidad de medida | P3 | backlog |
| R-20 sin consumo de maestros SAP | P1 | `GA-REM-017` (`BLOCKED_EXTERNAL`) |
| R-21 identificadores SAP declarados y nunca poblados | P1 | `GA-REM-010` (ampliada) |
| R-22 sin bandera de riesgo manual | P2 | backlog |

## Nuevos requerimientos
`GA-REQ-057` agua · `GA-REQ-058` rotación de huevos · `GA-REQ-059` identificador de transacción externa · `GA-REQ-060` bandera de riesgo.

Criterio aplicado (§9 del encargo): **no se convirtió ninguna mención documental en requisito** sin evidencia de que el software debía soportarlo. Los manuales técnicos, el contexto de negocio y los formatos vacíos **no** generaron requerimientos.

## Reclasificación
`egg_storage`: de `IMPLEMENTED_WITHOUT_SPEC` a **`CLIENT_REQUIREMENT_PRESENT` + `SPEC_GAP`**, con trazabilidad a `Bases Consideradas p.8` y `Recomendación central §11`. **La implementación no se modifica**: es correcta.

## Requirement conflict abierto
`RC-07` — política de mortalidad frente a SAP: el cliente presenta tres políticas excluyentes y exige elegir una; no hay decisión registrada. Escalado, no resuelto.

## Regression
Ninguna. No se modificó código, esquema, configuración ni datos.

## Files
| Archivo | Acción |
|---|---|
| `audit/remediation/FUNCTIONAL_COVERAGE_MATRIX.md` | **creado** (311 líneas) |
| `specs/remediation/GA-REM-020-FUNCTIONAL-COVERAGE-VALIDATION.md` | spec previa |
| Código de aplicación | **sin cambios** |

## Evidence
- `audit/remediation/FUNCTIONAL_COVERAGE_MATRIX.md` — 96 elementos con evidencia
- Salidas de `T-020-01` … `T-020-04` reproducidas arriba
- Extracciones documentales: `pdftotext -layout` sobre 3 PDF; lector XLSX propio sobre 2 libros

## Final status
**`CERTIFIED`** — habilita el congelamiento del **Functional Baseline V1.1**.
