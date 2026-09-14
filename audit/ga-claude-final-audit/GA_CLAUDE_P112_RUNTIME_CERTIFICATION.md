# GA-CLAUDE · CERTIFICACIÓN RUNTIME — P1-12 (REAPERTURA): UN PRODUCTOR POR ACCIÓN

Fecha: 2026-09-14 · Paquete: `specs/P1-12-REOPEN/` · GA-REM-043 (siguiente libre al autorizar) · HEAD de partida: `56d0fcb` (T7 cerrada).

## 1 · Ejecución por ciclos

| Ciclo | Commits | Resultado |
|---|---|---|
| **C1 · RED** | `d228eac` | Arnés con listener (`tests/audit_harness.py`) + `test_p112_audit_single_producer.py`: **BE 6F/13P** — `created`=2 (listener+helper), `review_started`=3, `approved`=2, `corrected` espuria=1; cierre/usuarios/evidencias/curvas/batch = 0 filas. C-01 registrada (híbrido determinista). |
| **C1b · RED extendido** | `ce363af` | `AC-P112-04` completo: activación manual y fase ⇒ 0 filas; **8F exactos** reproducidos. |
| **C2 · Implementación** | `0bbad13` + `0de63c2` | **Guarda de idempotencia compartida** listener↔helpers (`helpers.ya_emitida`/`marcar_emitida`; clave `(entidad, id, acción)` en `session.info`): un productor por acción en runtime **y** en contextos sin listener. Ruta `ApprovalAction` del listener **retirada** (las decisiones transitan el estado del evento; batch y contrapartida escriben su transición explícitamente). Mapa del listener: `pending_review→UPDATED`, `reversed→REVERSED`; la corrección rica (diff) la escribe la ruta `CorrectionLog`. Productores nuevos: cierre/activación/fase de lote, usuarios (alta/edición/baja, sin secretos), evidencias (subir/borrar), curvas (crear/activar), batch y contrapartida. **BE 8/8** · regresión **207/207** · arnés runtime añadido a `test_audit_coverage` y `test_edit_cancel_balance` (sus «exactamente 1» ahora son verdad en runtime). |
| **C2s · Sensibilidad** | `5940f6a` | S1 (guardas off): 2F — `created`=2 y `review_started`=2. S2 (sin productor de cierre): 1F. |
| **C3 · Runtime** | — | En ventana (familia G-06): recuento UI por acción en entorno desplegado. |

## 2 · Criterios de aceptación

| AC | Estado | Evidencia |
|---|---|---|
| AC-P112-01 alta ⇒ 1 `created` | ✅ | `test_p112_01` verde con listener; S1 lo rompe |
| AC-P112-02 `start/approve/return/reject` ⇒ 1 fila | ✅ | `test_p112_02` (3→1; espuria 0) |
| AC-P112-03 sin `corrected` espuria al aprobar | ✅ | ídem (tipo del `ApprovalAction` corregido y ruta retirada) |
| AC-P112-04 cierre/activación/fase ⇒ 1 fila con valores | ✅ | `test_p112_03/03b/03c`; S2 rompe el cierre |
| AC-P112-05 usuarios ⇒ 1 fila (sin secretos) | ✅ | `test_p112_04` (CREATED/UPDATED/DELETED en módulo `users`) |
| AC-P112-06 evidencias ⇒ 1 fila | ✅ | `test_p112_05` (producible ya en T8·R-198) |
| AC-P112-07 curvas ⇒ 1 fila | ✅ | `test_p112_05` (CREATED + UPDATED de activación) |
| AC-P112-08 batch/contrapartida ⇒ transición `pending_review` | ✅ | `test_p112_06` (UPDATED, `new_state=pending_review`) |
| AC-P112-09 suite con listener | ✅ | 8/8 + 207/207 con arnés; módulos de conteo migrados |
| AC-P112-10 GA-REM-032 reconciliado | ✅ | C-03=A: logout (ya cerrado, GA-REM-003 AC04); exportaciones cliente `NOT_APPLICABLE_CLIENT` |
| AC-P112-11 sin migración/endpoint/permiso | ✅ | `git diff --stat`: audit + módulos + tests |

## 3 · Límites declarados

- **C3 runtime** en ventana: el recuento «exactamente 1» ya es verdadero **bajo listener en tests** (fidelidad de runtime del arnés); la captura UI desplegada queda en la cola G-06.
- Los helpers se **conservan** para contextos sin listener (scripts/arnés); en runtime quedan inertes por la guarda — es la decisión C-01/C-02 registrada.
- Históricos con duplicados **no se limpian** (inmutabilidad, R-148): la corrección es hacia adelante.

## 4 · Veredicto

**P1-12 (REAPERTURA) = `CLOSED_TECHNICALLY`** — un productor por acción, cobertura completa de las siete acciones sin rastro, corrección sin fila espuria y prueba bajo listener en los módulos de conteo. **P-09 (auditoría) reparado técnicamente**; la captura runtime de UI queda en ventana.
