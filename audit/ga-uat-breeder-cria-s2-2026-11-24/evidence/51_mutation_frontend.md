# Campaña de sensibilidad — Tanda 3 (frontend, 7 mutantes)

- Rama `develop`, HEAD `3073ff6`; el código de producción de los cinco ficheros mutados es idéntico
  al del commit `8366827` (`git diff --stat 8366827 -- <archivo>` vacío tras cada restauración).
- Suite de cada corrida (una sola vez por mutante), desde `frontend/`:

  `npx vitest run src/pages/review/__tests__/uatS2.correctionMaster.test.tsx src/pages/review/__tests__/uatS2.reviewFilters.test.tsx src/pages/review/__tests__/f4.lotFilterDebounce.test.tsx src/pages/operations/__tests__/uatS2.listLotLabel.test.tsx`

- Línea base sin mutar: **4 ficheros, 19 tests passed** (6,8 s). Ninguna corrida falló por
  infraestructura; todas las corridas terminaron en 7–14 s.
- Restauración tras cada mutante: `git restore --source=8366827 -- <archivo>` + `git diff --stat`
  vacío verificado antes del siguiente; `git status --short -- frontend` vacío al terminar.
- Abreviaturas: `CM` = `uatS2.correctionMaster.test.tsx`, `RF` = `uatS2.reviewFilters.test.tsx`,
  `F4D` = `f4.lotFilterDebounce.test.tsx`, `LL` = `uatS2.listLotLabel.test.tsx`
  (rutas bajo `frontend/src/pages/…`).

## Tanda 3 (F1–F4)

| Mutante | Archivo | Mutación | Resultado | Tests que lo detectan |
|---|---|---|---|---|
| F1 | `review/CorrectionForm.tsx` · input VALOR ORIGINAL (l.171) | `campoActual?.current_display ?? campoActual?.current_value ?? ''` → `campoActual?.current_value ?? ''` | **DETECTADO** (1 fallo) | `CM › C04 · el valor original de un maestro muestra el NOMBRE, no el id` (`expected '27' to be 'Avícola Norte'`) |
| F2 | `review/ReviewCenter.tsx` · `fetchEvents` (l.132) | `params.set('lot_code', lotCodeDebounced)` → `params.set('lot_id', lotCodeDebounced)` | **DETECTADO** (4 fallos) | `RF › REV-S2-UI-01 · teclear «L-0001» envía lot_code tras 400 ms y nunca lot_id`; `RF › REV-S2-UI-02 · un texto no numérico no muestra ningún aviso de formato`; `F4D › código no numérico ⇒ se consulta con lot_code tras el debounce, sin aviso de formato`; `F4D › tres caracteres seguidos ⇒ una sola petición extra (sin ráfaga)` |
| F3 | `review/ReviewCenter.tsx` · `fetchEvents` (l.124) | se comenta `if (rangoInvalido) return` | **DETECTADO** (1 fallo) | `RF › REV-S2-UI-03 · inicio > fin ⇒ no se consulta y aparece un único role="alert"` (`el rango inválido no se consulta: expected 1 to be +0`) |
| F4 | `operations/OperationListPage.tsx` · `lotCellLabel` (l.19) | `return ev.event_type === 'grandparent_import'` → `return true` | **DETECTADO** (1 fallo) | `LL › farm_inspection sin lote ⇒ «Sin lote (nivel granja)» (ni «Se creará al aprobar» ni «#null»)` |
| F5 | `approvals/ApprovalPanel.tsx` · consulta de pendientes (l.54) | `params.set('lot_code', lotCodeDebounced)` → `params.set('lot_id', lotCodeDebounced)` | **DETECTADO** (3 fallos) | `RF › REV-S2-UI-05 · ApprovalPanel envía lot_code a /approvals/pending`; `F4D › Aprobaciones · código no numérico ⇒ viaja lot_code tras el debounce y nunca lot_id`; `F4D › Aprobaciones · tres caracteres seguidos ⇒ una sola petición extra` |
| F6 | `review/ReviewDetail.tsx` · historial de correcciones (l.221) | `c.original_display ?? c.original_value` → `c.original_value` | **DETECTADO** (1 fallo) | `CM › C05 · campo de maestro: original_display → corrected_display` (`expected … to contain 'Avícola Norte'`) |
| F7 | `review/CorrectionForm.tsx` · JSX VALOR CORREGIDO (l.178) | condición `campoActual?.master` del `<select data-testid="correction-corrected-master">` → `false` | **DETECTADO** (3 fallos) | `CM › C04 · pide el catálogo del maestro y ofrece un select sin el registro actual`; `CM › C04 · guardar envía el id del registro elegido como string`; `CM › C04 · sin selección en un campo de maestro no envía y avisa con un único mensaje` |

## Conclusión

7/7 mutantes DETECTADOS (0 supervivientes). Detección mínima de 1 test (F1, F3, F4, F6) y máxima de
4 (F2). No se añadieron ni modificaron tests. Árbol de frontend limpio al cierre
(`git status --short -- frontend` vacío) y cada fichero restaurado a `8366827` antes del mutante siguiente.
