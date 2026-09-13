# R-210 · FINDING — UNIDAD DE PESO: CAPTURA CON RESTOS «KG» FRENTE A SISTEMA/CURVA/KPI EN GRAMOS

| Campo | Valor |
|---|---|
| **ID canónico** | **R-210** (asignado en `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §0`; máximo previo R-189) |
| **Título** | Los campos de peso del asistente conservan `step="0.001"` y textos/fallbacks «(kg)» mientras el sistema, las curvas (OD-06) y la evaluación/KPI operan en **gramos**: riesgo de captura en kg interpretada como g (curva y uniformidad erróneas) |
| **Severidad** | **P2** (integridad de pesos/curva; **severidad a reevaluar** — la etiqueta renderizada i18n es «Peso prom. (g)» y el defecto remanente son `step`/fallbacks; se mantiene P2 hasta confirmar la unidad de captura con el propietario, C-01) |
| **Clase** | `REQUEST_CONTRACT` (unit mismatch) / `DATA_INTEGRITY` |
| **Proceso** | P-03/P-06 (pesaje), transferencia/salida/importación (peso en filas), P-15 (uniformidad/IPE) |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` (== `origin/main`) |
| **Familia** | B-12 (informe B); `GA-REM-021 B02` (`GA_REM_021_B02_WEIGHT_RANGE_MATRIX.md:19,45`); GA-REM-037; `OperationDetailPage.tsx:221` |
| **Paquete** | `audit/ga-claude-final-audit/specs/R-210/` (completo, 6 ficheros) |
| **GA-REM** | a asignar al autorizar; siguiente libre GA-REM-043 |
| **Bloquea SAP** | **SÍ** (integridad de pesos/curva; pesos alimentan uniformidad/IPE y datos de origen) |
| **UAT del propietario** | sí, mínima: confirmación de la unidad de captura (g) en el pesaje (C-01) |

## 1 · Evidencia

### 1.1 Código (verificado en HEAD)

- `frontend/src/pages/operations/OperationFormPage.tsx:470,484` — etiqueta de filas «(kg)» con `step="0.001"`; usos en `weight_recording` (`:627`), `bird_transfer` (`:865`), `bird_exit` (`:987`), `lot_closure` (`:1703`), `grandparent_import` (`:1790`).
- `operations.avgWeight` (JSON ES) = «Peso prom. (g)» **con fallback «Peso prom. (kg)»** en el código; `OperationListPage`/`Detail` y la matriz B02 usan gramos.
- Sistema en gramos: `GA_REM_021_B02_WEIGHT_RANGE_MATRIX.md:19,45`; evaluación de curva (`masters/curves.py`; `operations/service.py:744-824`); uniformity/IPE sobre `avg_weight` (gramos).
- `OperationDetailPage.tsx:221` — detalle presentado en g.

### 1.2 Lectura reconciliada (FORM_CONTRACT §5.1 nota)

Con la etiqueta i18n verificada «(g)», el defecto renderizado se reduce a: `step="0.001"` (sugiere kg), fallbacks «(kg)» en código/i18n residual y textos «Peso final prom. (kg)». El riesgo real es de **captura**: un operador puede ingresar kg (p. ej. 2.15) creyendo kg mientras el sistema espera g (2150) ⇒ evaluación `below_standard` y KPI erróneos.

## 2 · Causa raíz

Migración parcial de kg→g (GA-REM-037): sistema y curvas migraron; los controles del asistente conservaron `step` y textos heredados; sin prueba que fije la unidad de captura.

## 3 · Impacto

- Pesajes capturados en kg interpretados como g ⇒ curva/alerta de peso y uniformidad/CV erróneos; IPE contaminado.
- Inconsistencia interna de etiquetas (g en unos sitios, kg en fallbacks).

## 4 · Dedup realizada (§48)

| Registro | Resultado |
|---|---|
| R-001…R-189 | GA-REM-037/B02 documentan el rango en gramos; B-12 queda como defecto de formulario sin hallazgo propio. |
| Informes B/F | B-12 (líneas) + F (fallbacks/step) concuerdan; F propone reevaluar severidad. |

Conclusión: **nuevo**; ID asignado **R-210**.

## 5 · Propietario sugerido

Frontend (asistente) + confirmación de dominio (unidad de captura). Regresión de evaluación de curva (backend).

## 6 · Bloquea SAP y por qué

**SÍ** por integridad: pesos incorrectos se propagan a uniformidad/IPE (y a reportes de crecimiento de P-08). Corrección pequeña, impacto de dato alto.

## 7 · Interdependencias

- **C-01** con el propietario (unidad de captura): por defecto **gramos** (alineado con curvas/KPI).
- **R-206** (serializador de opcionales): misma tranche de asistente; el normalizador aplica a los mismos campos.
- **E-24/R-214** (KPI sin filtro de estado): familia KPI; fuera de aquí.
