# GA-FE-05 · EVIDENCIA RED (pre-implementación)

Fecha: 2026-09-11 · Generación: bundle `index-B66tpdeW.js` (producto `de40d36`, pre-GA-FE-05)
Actor: `ga05-c` (id 109 · rol 46 «GA-FE05 TEST OPERATOR»: dashboard:read · lots:read · operations:read+create · concesión broiler)
Ventana: broiler ON (solo fixtures).

## 1 · RED automatizado — `src/pages/operations/__tests__/gaFe05.submitGates.test.tsx`

Resultado: **6 fallas objetivo | 4 controles** (10 casos).

| Caso | Tipo | Resultado | Detalle |
|---|---|---|---|
| registered + permiso + unidad ⇒ «Enviar a revisión» | objetivo | **FAIL** | `AssertionError: expected null not to be null` — no existe CTA |
| un clic ⇒ 1 mutación + GET fresco + CTA desaparece | objetivo | **FAIL** | CTA inexistente (no hay punto de acción) |
| returned ⇒ «Reenviar a revisión» | objetivo | **FAIL** | CTA inexistente |
| rejected ⇒ «Reenviar» (OD-17.a) | objetivo | **FAIL** | CTA inexistente |
| doble clic ⇒ 1 mutación | objetivo | **FAIL** | sin botón que probar |
| fallo 403 ⇒ sin éxito falso + reconciliación | objetivo | **FAIL** | sin flujo |
| pending_review ⇒ sin CTA | control | PASS (vacuo hoy) | página renderiza; sin CTA (correcto tras fix también) |
| approved ⇒ sin CTA | control | PASS (vacuo hoy) | íd. |
| sin operations:create ⇒ sin CTA | control | PASS (vacuo hoy) | íd. |
| cero unidades ⇒ sin CTA | control | PASS (vacuo hoy) | íd. |

Los 4 controles pasan hoy «vacuos» (no hay CTA en absoluto); tras la implementación pasan por la lógica real de visibilidad.

## 2 · RED runtime (pre-fix, producción)

| Evidencia | Medición |
|---|---|
| Operación **44** (`registered`) abierta como C en `/operations/44` | `Enviar/Reenviar/Submit/Resubmit` = **0 botones** · chip muestra `registered` **crudo** | 
| Captura | `evidence/red/RED_operation_44_registered_no_submit_cta.png` |
| Operación **45** (`pending_review`) — control | 0 CTA (correcto) · `evidence/red/RED_operation_45_pending_no_cta.png` |

Además, la viabilidad del backend quedó probada en el propio flujo de fixtures: `POST /operations/45/submit` (API, actor C) ⇒ **200** `pending_review` — el backend funciona y la UI no lo expone (la esencia del hallazgo R-181).

## 3 · Conclusión RED

El gap es exactamente el declarado: **servicio existente con 0 llamadores**; ninguna pantalla ofrece el acto explícito; el estado se muestra crudo. RED válido para implementar (FINDING → … → RED → IMPLEMENT).
