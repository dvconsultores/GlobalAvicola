# GA-FE-05 · ÍNDICE DE CAPTURAS

## RED pre-fix (`evidence/red/`, generación `index-B66tpdeW.js`)

| Archivo | Caso | Medición |
|---|---|---|
| `RED_operation_44_registered_no_submit_cta.png` | Operación 44 `registered` como C | 0 botones Enviar/Reenviar · chip `registered` crudo |
| `RED_operation_45_pending_no_cta.png` | Operación 45 `pending_review` | 0 CTA (control) |

## Certificación post-fix (`evidence/runtime/`, generación `index-WUv1-F9o.js`)

| Archivo | Caso | Resultado visible |
|---|---|---|
| `E2E01_before_submit_44.png` | C · 44 registrada | CTA «Enviar a revisión» visible |
| `E2E01_after_submit_44.png` | tras submit | chip «Enviado a Revisión» · CTA desaparecido |
| `E2E01_EN_submit_label.png` | 51 en inglés | «Submit for review» |
| `E2E01_mobile_before_52.png` / `E2E01_mobile_after_52.png` | móvil 390×844 | CTA ⇒ pendiente, sin desborde |
| `E2E09_after_doubleclick_48.png` | doble clic | una sola mutación; pendiente |
| `E2E10_failure_49.png` | fallo 403 | error visible; estado intacto; CTA de vuelta |
| `E2E05_pending_45_no_cta.png` | 45 pendiente | sin CTA |
| `E2E06_returned_46_resubmit_visible.png` | 46 devuelta | «Reenviar a revisión» + observación visible |
| `E2E07_after_resubmit_46.png` | tras reenvío | chip «Enviado a Revisión» |
| `E2E08_approved_47_no_cta.png` | 47 aprobada | sin CTA (inmutable) |
| `E2E03_Z_no_user_bu_49.png` | Z sin User BU | sin CTA |
| `E2E04_R2_no_rbac_49.png` | R2 sin RBAC | sin CTA (lectura sí) |
| `E2E04b_p_denied.png` / `E2E04b_d_denied.png` | P/D sin autoridad | «No tiene permiso» |
| `E2E02_cbu_off_C_49.png` / `E2E02_cbu_off_E_50.png` | CBU OFF (C y global) | sin CTA; lectura bloqueada (sin bypass global) |
