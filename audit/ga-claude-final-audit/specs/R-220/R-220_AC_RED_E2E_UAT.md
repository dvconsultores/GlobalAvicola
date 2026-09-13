# R-220 · AC · RED · E2E · UAT (COMPACTO)

HEAD `c0b4afc` · Artefactos bajo `specs/R-220/evidence/`.

## 1 · Criterios de aceptación (por lote)

| AC | Criterio | Verificación |
|---|---|---|
| AC-R220-A | Lote A: los ítems A1–A13/A15–A18 corregidos con unit o lectura dirigida; A14/A18 con test backend | units + salida |
| AC-R220-B | Lote B: B1–B10 verificados (navegación usable en `<1024px` y móvil; rutas huérfanas con entrada; responsive sin cortes) | E2E viewports 390/768/1280 |
| AC-R220-C | Lote C: sin enumerados crudos en las pantallas listadas; claves ES/EN presentes; sin fallbacks ES en EN | units de locales + capturas EN |
| AC-R220-D | Lote D: código muerto retirado o alineado; sin regresiones | grep + suites |
| AC-R220-05 | Sin migración/endpoint/permiso (salvo A14/A18 menor documentado) | revisión diff |
| AC-R220-06 | Regresión: vitest completa, tsc, build, `test_r26_error_contract` (A1750), `test_water*` (A14) | suites |

## 2 · Diseño RED (por ítem representativo)

- A1: unit de formateador de fechas (rojo: −1 día).
- A5: unit que muestra `rule` en un 400 (rojo).
- A7: unit de textos por tipo de notificación (rojo).
- B3/B5: unit/E2E de navegación con entrada visible (rojo).
- C1: unit de `t()` en los 8 puntos (rojo: crudos).
- D4: revisión de clases (no test).
Ejecución por lote; salidas a `evidence/red/<lote>/`.

## 3 · E2E

`R220-RT-A…D`: recorridos de humo por lote (capturas 390/1280; ES/EN donde aplique). Artefacto `evidence/r220/runtime-{red,c3}.json`.

## 4 · UAT

**No requerida** (residuales P3; sin impacto funcional de proceso). Verificación informativa conjunta si el propietario la pide (tour de móvil/EN).
