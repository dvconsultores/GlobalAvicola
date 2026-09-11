# GA-UAT-03 · EVIDENCIA — GA-FE-05 (envío/reenvío a revisión)

Fecha: 2026-09-11 · Generación: **`index-WUv1-F9o.js`** (producto `005a252`; sin cambios) · Baseline canónico: `a28b2a1`
Runtime: https://avicola.globaldv.net · health 200.

## A · PRECONDICIONES DE INGENIERÍA

| Gate | Resultado |
|---|---|
| TypeScript | 0 |
| Build | PASS |
| Vitest completo | **273/273** (35 archivos) |
| GA-FE-05 dirigida | **10/10** |
| GA-FE-05 técnica | FUNCTIONALLY_CERTIFIED (R-181 CLOSED) — evidencia en `audit/ga-fe-05/` |

**Fixtures** (oficiales, sintéticos): operador `uat03-operador` (rol 50) + revisor `uat03-revisor` (rol 51) · ventana `broiler` ON · concesiones para ambos · lote 11 (L-BO-2026-05).

**Operaciones de prueba** (todas por flujo oficial, sin SQL):

| Nº visible | Estado | Uso |
|---|---|---|
| #53 | registrada | UAT-01/02 (enviar) |
| #54 | enviada (pending_review) | UAT-03 |
| #55 | devuelta (con motivo) | UAT-04/05 (reenviar) |
| #56 | aprobada | UAT-06 |
| #57 | enviada en carrera | UAT-07 (demostración de fallo) |
| #58 | registrada | UAT-08 móvil (enviar) |
| #59 | devuelta | UAT-08 móvil (reenviar) |
| #60 | registrada | UAT-09 (inglés) |

## B · EJECUCIÓN DE REFERENCIA (capturas del equipo, sin mutar fixtures del propietario)

| Captura | Medición |
|---|---|
| `c01_registered_submit_cta.png` | chip «Registrado» + 1 botón «Enviar a revisión» |
| `c02_pending_no_cta.png` | chip «Enviado a Revisión» + **0** botones |
| `c03_returned_reason_resubmit.png` | chip «Devuelto» + **motivo visible** + 1 «Reenviar a revisión» |
| `c04_approved_final_no_cta.png` | chip «Aprobado» + **0** botones |
| `c05_mobile_registered_submit.png` | 390×844: CTA visible, sin desborde |
| `c06_mobile_returned_resubmit.png` | 390×844: CTA reenviar visible, sin desborde |
| `c07_en_submit_label.png` | «Submit for review» + «Registered», sin claves crudas |
| `c08_failure_race_error_and_reconcile.png` | fallo controlado: error visible, **sin éxito falso**, estado reconciliado a «Enviado a Revisión», CTA desaparecido |

Detalle UAT-07 (carrera): operador abre #57 (botón visible) → la operación es enviada en
segundo plano (misma persona, otra sesión) → el clic del operador recibe la negativa canónica
del servidor → aviso de error + recarga automática del estado real. Sin exposición técnica.

## C · CASOS DEL PROPIETARIO

Ejecución (si el propietario corre la app) o revisión del paquete: ver `GA_OWNER_UAT_GA_FE_05_GUIDE.md`.
Credenciales efímeras: `~/ga_uat_03_credentials.txt` (fuera del repositorio; se destruyen al cierre).

## D · OBSERVACIONES DEL PROPIETARIO

**PENDIENTE** — registro vacío hasta la sesión (`GA_OWNER_UAT_GA_FE_05_OBSERVATIONS.md`).

## E · DECISIÓN DEL PROPIETARIO

**PENDIENTE** — no se rellena antes de la respuesta explícita.

## F · LÍMITES

- No se reabre ingeniería; no se implementa nada durante la sesión (§2/§23 del encargo).
- R-182 intacto; BU-D10 no se decide aquí; sin nuevas tranches.
