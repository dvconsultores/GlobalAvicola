# R-210 · SPEC — UNIDAD ÚNICA DE PESO (GRAMOS) EN CAPTURA, ETIQUETA Y CONVERSIÓN

Fecha: 2026-09-13 · Hallazgo canónico: **R-210** (P2 · bloquea integridad) · HEAD `c0b4afc` · Origen B-12 · Registro G-22. Secciones §47.

## 1 · Contexto

El sistema opera pesos en **gramos** (curvas OD-06, evaluación, uniformidad CV, IPE). El asistente muestra etiquetas mixtas («(g)» i18n vs «(kg)» fallbacks) y `step="0.001"` heredado de la era kg. Sin una regla explícita, la captura puede entrar en kg.

## 2 · Evidencia

`R-210_FINDING.md §1`: `OperationFormPage.tsx:470,484,627,865,987,1703,1790`; fallbacks i18n; `GA_REM_021_B02…:19,45`; `operations/service.py:744-824`; `OperationDetailPage.tsx:221`.

## 3 · Causa raíz

Migración kg→g incompleta en controles (step/textos/fallbacks) sin prueba de unidad.

## 4 · Impacto de negocio

Pesajes erróneos por factor 1000 en peores casos; evaluación de curva y KPI de uniformidad incorrectos; decisiones de manejo y datos de crecimiento contaminados.

## 5 · Comportamiento actual

| Punto | Hoy |
|---|---|
| Etiqueta visible (i18n) | «Peso prom. (g)» |
| `step` del input | `0.001` (sugiere kg) |
| Fallbacks de código | «(kg)» |
| `lot_closure`/`grandparent_import` | textos «Peso final/… (kg)» |
| Sistema/curva/KPI | gramos |

## 6 · Comportamiento esperado

1. **Regla única**: captura en **gramos** (C-01 por defecto; confirmación del propietario registrada). Etiquetas y ayudas lo dicen explícitamente; `step` coherente (p. ej. `1`/`0.1` g o libre) — se eliminan textos «(kg)».
2. **Serialización**: el valor viaja tal cual (número en g); sin conversiones ocultas.
3. **Fallbacks/i18n**: clave única `operations.avgWeight` «Peso prom. (g)» / «Avg. weight (g)»; sin fallbacks kg.
4. **Detalle**: se mantiene en g (sin cambio) — coherencia con evaluación.
5. Si el propietario decidiera capturar en kg (C-01=B), la spec exige **conversión explícita** ×1000 en el serializador + etiqueta kg coherente y tests de conversión — no se mezcla.
6. Sin cambio backend (los validadores y curvas ya operan en g).

## 7 · Alcance

- `OperationFormPage.tsx` (todos los puntos de peso listados) + locales ES/EN.
- Tests: `frontend/.../__tests__/r210.weightUnit.test.tsx` (rótulos/step/serialización; rojo con step 0.001/fallback kg) + regresión `weightEvaluation` (backend control: un pesaje en g correcto evalúa `within/above` según curva).
- Sin migración/endpoint/permiso.

## 8 · Fuera de alcance

- Rango/curva (B02) y fórmulas KPI (Wave C).
- Unidades de otros campos (temperatura, kg de alimento — donde kg es correcto).
- Edición de eventos históricos.

## 9 · Impacto frontend

Etiquetas/step/fallbacks del peso en 6 bloques; sin rediseño.

## 10 · Impacto backend

Ninguno.

## 11 · Contrato frontend↔backend

`bird_movements[].avg_weight` sigue siendo número en g; sin cambio de esquema. El detalle/evaluación permanecen en g.

## 12 · Impacto en datos

Ninguno nuevo; se previenen capturas contaminadas. Históricos: inventario opcional (pesos fuera de rango plausible en g ⇒ posible kg capturado en el pasado reciente de pruebas, no producción real).

## 13 · Seguridad

Sin cambio.

## 14 · Inquilino · 15 · Unidad de negocio · 16 · RBAC

Sin cambio.

## 17 · Transacciones · 18 · Auditoría

Sin cambio.

## 19 · i18n

| Clave | ES | EN |
|---|---|---|
| `operations.avgWeight` (existente, consolidar) | Peso prom. (g) | Avg. weight (g) |
| `operations.weightFinal` (nueva si no existe) | Peso final prom. (g) | Final avg. weight (g) |

Sin «(kg)» en fallbacks; sin claves duplicadas.

## 20 · Escritorio · 21 · Móvil

Etiqueta y teclado (inputMode decimal) usables; verificación 390×844.

## 22 · Manejo de errores

Sin cambio (rangos BR-02 siguen en backend).

## 23 · Impacto de migración

Ninguna.

## 24 · Impacto SAP

Indirecto (peso de crecimiento como dato de origen). Sin llamadas.

## 25 · Compatibilidad hacia atrás

Clientes API: sin cambio (mismo campo numérico). Operadores: verán la unidad explícita (g).

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| AC-R210-01 | Etiquetas de peso (todos los bloques) dicen «(g)» en ES y EN; sin «(kg)» renderizado |
| AC-R210-02 | `step` coherente con gramos en los 6 puntos (no 0.001) |
| AC-R210-03 | Serialización: valor g viaja sin conversión; evaluación de curva lo interpreta en g (control backend) |
| AC-R210-04 | Fallbacks sin «(kg)» (lectura de locales y de códigos) |
| AC-R210-05 | Si C-01=B (kg): conversión explícita ×1000 documentada y probada (variante) |
| AC-R210-06 | Sin migración/endpoint/permiso |
| AC-R210-07 | Regresión: `f01.payloadContract`, `f01d.serializers`, `receptionFormContract`, vitest completa, tsc, build |
| AC-R210-08 | Confirmación C-01 del propietario registrada en el acta (unidad de captura) |

## 27 · Pruebas RED→GREEN

`§1` del diseño: `r210.weightUnit` (rótulo/step/serialización; rojo), control backend `test_r210_weight_evaluation_grams.py` (verde).

## 28 · E2E

`§2`: `R210-RT-01…03` (pesaje por UI ⇒ payload en g; evaluación dentro de curva; movil). Artefacto `evidence/r210/`.

## 29 · UAT

Mínima (C-01): el propietario confirma «el pesaje se captura en gramos». Caso práctico opcional: registrar un pesaje conocido (p. ej. 2150 g) y ver la evaluación dentro de banda.

## 30 · Criterios de cierre

RED válida · GREEN local · C-01 registrada · sensibilidad (S1: restaurar step 0.001+fallback kg ⇒ AC-01/02 rojas) · sin migración/endpoint/permiso · R-210 → `CLOSED` con GA-REM asignado.
