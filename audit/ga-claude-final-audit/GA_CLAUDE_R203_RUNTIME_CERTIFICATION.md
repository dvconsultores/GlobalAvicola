# GA-CLAUDE · R-203 — CERTIFICACIÓN (tenencia estructural en alta/edición de lotes)

Fecha: 2026-09-13 · Hallazgo **R-203** (P2 · bloquea cruce · GAP-06) · Paquete `specs/R-203/` · Clarificación **C-07** · Commits: C1 `fc8f193` · C2 (este tranche).

## 1 · Fases

| Fase | Estado | Evidencia |
|---|---|---|
| **C1 · RED** | ✅ | `red_c1.log` — **5F/7P**: galpón de otra empresa ⇒ 201; línea ajena ⇒ 201; línea+curva ajenas ⇒ 201 con curva aplicada; `PUT {house_id: B}` ⇒ 200; extensión del fichero de referencia de la clase (`ga06a_06`) rojo. Controles verdes (curva propia aplicada, alta legítima, área como referencia de la clase) |
| **C2 · Implementación** | ✅ | `green_c2_regresion.log` — **86/86** dirigidas (R-203 7 + área 6 + curvas + tenencia maestros + submovimientos + row scope); **suite completa conjunta `1278 passed / 0 failed / 49 skipped`** (`full_suite_c2.log`, 20:14); extensión de clase: RED genuino re-observado (`red_c1_area_extension.log`) |
| **C2s · Sensibilidad** | ✅ S1·S2 | **S1** (sin verificación de galpón): 2F — RED-01 y RED-04 caen (`mutations/S1_sin_galpon.log`); **S2** (sin verificación de línea): 2F — RED-02 y RED-03 caen (`mutations/S2_sin_linea.log`); mutaciones revertidas, C2 restaurado |
| **C3 · Runtime** | ⏸ **pendiente G-06** | Las sondas crean geometría ajena (empresa B) en runtime: requieren credenciales privilegiadas multiempresa — misma clase que R-199/202/201. Las sondas `R203-RT-01…06` quedan listas |

## 2 · Implementación

`lots/service.py` — misma clase y contrato que el área (`GA-FE-06-A`):
- **Alta**: `house_id` se verifica **por la granja** (el galpón cuelga de `Farm`); `genetic_line_id` por `verificar_catalogo_de_empresa` (nulo = compartida, `R-179`); la curva sigue la línea verificada + el chequeo de línea de curva existente.
- **Edición**: mismas verificaciones para cambio de `house_id`/`genetic_line_id` (solo cuando el valor cambia — semántica `OD-21`, como el área).
- Rechazo canónico (**C-07**): `400` + detalle neutro («Galpón no encontrado» / «Línea genética no encontrado») + `rule: "BR-07"` — el ajeno se comporta como inexistente, sin distinguirlo de «no existe».

## 3 · AC

| AC | Estado |
|---|---|
| AC-R203-01 (galpón ajeno ⇒ rechazo; cero filas) | ✅ RED-01 · **S1** |
| AC-R203-02 (línea ajena ⇒ rechazo; nula ⇒ 201) | ✅ RED-02 · **S2** |
| AC-R203-03 (curva de línea ajena ⇒ rechazo sin aplicar) | ✅ RED-03 · **S2** |
| AC-R203-04 (edición no cruza; propio ⇒ 200) | ✅ RED-04 · **S1** |
| AC-R203-05 (curva propia sigue aplicándose, control) | ✅ control verde (evaluación de curvas: `test_genetic_curves` en la suite) |
| AC-R203-06 (alta legítima intacta, control) | ✅ control verde + `test_lot_area_ownership` completo |
| AC-R203-07 (A/B cruzadas por las tres puertas) | ✅ fixture R-203 con empresas A y B |
| AC-R203-08 (sin migración/endpoint/permiso; diff `lots/service.py`) | ✅ diff |
| AC-R203-09 (inventario de control §12) | ✅ ejecutado al cierre sobre la BD de pruebas: **house=0 · line=0 · curve=0** filas cruzadas (consulta de solo lectura; resultado en §4) |
| AC-R203-10 (regresión de las cinco suites) | ✅ 86/86 dirigidas (incluye las cinco) · suite completa `1278/0/49` |

## 4 · Inventario de control (§12 de la spec)

Consulta de solo lectura sobre la BD de pruebas (tras la suite de cierre):

- `lots.house_id` fuera de su empresa (vía granja): **0**
- `lots.genetic_line_id` no nulo fuera de su empresa: **0**
- `lots.weight_curve_id` cuya línea es de otra empresa: **0**

Entorno con seeds; coincide con lo esperado.

## 5 · Veredicto

**R-203 = `CLOSED_TECHNICALLY`** — C1/C2/C2s completos con evidencia local; C3 runtime pendiente de **G-06**. Sin cambio para flujos legítimos; las referencias ajenas pasan de escribirse a rechazarse (corrección de cruce entre inquilinos).
