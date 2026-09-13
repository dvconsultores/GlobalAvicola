# R-193 · DISEÑO RED · E2E RUNTIME · UAT

## 1 · Pruebas RED — `backend/tests/test_r193_oc_limit_after_reversal.py`

Fixture `escenario_oc` (función): empresa de semillas (`seeded_ids`), `SapReference {ref_type:'purchase_order', sap_code:'R193-OC-<uuid>', quantity:1000, company_id}` insertada como en `test_purchase_order_receipt.py` (teardown por prefijo `R193-`), lote `broiler` `R193-LOTE-<uuid>` con `farm_id`/`house_id` de semillas (capacidad ≥ 1000). Actores: `auth_headers` (Super Admin: registra, aprueba flujo con `cabecera_de_rol('approver')`, solicita reverso) y `cabecera_de_rol('approver')` (aprueba la contrapartida: BR-14 exige ≠ solicitante). Helpers: `_recepcion(cab, n, oc)` ⇒ `POST /operations {event_type:'bird_reception', lot_id, farm_id, house_id, sap_document_ref: oc, bird_movements:[{sex:'mixed', quantity:n, house_id}], event_date: hoy}`; `_aprobar(id)` ⇒ submit/start/complete; `_reverso(id)` ⇒ `POST /reversals {event_id:id, reason:'R193 prueba'}` + aprobación de la contrapartida (patrón `test_internal_reversal.py:226-253`).

| Test | Pasos | Aserto que falla en HEAD (observado) |
|---|---|---|
| `test_r193_01_tras_un_reverso_efectivo_la_oc_recupera_su_capacidad` | A=400 aprobada · `_reverso(A)` ⇒ A y A' `reversed` (control) · B=400 | `assert rB.status_code == 201` — HEAD: **400**, `rule=='BR-18'`, `detail` contiene «ya recibidas: 800» |
| `test_r193_02_el_reverso_pendiente_no_libera_la_oc` | A=400 aprobada · solicitud de reverso **sin aprobar** · B=700 ⇒ esperado 400 (`ya recibidas: 400`) [control, verde] · aprobar contrapartida · B=700 | segundo `assert == 201` — HEAD: **400** (`ya recibidas: 800`) |
| `test_r193_03_la_contrapartida_rechazada_no_cuenta` | A=400 aprobada · solicitud · `POST /review/start` + `POST /review/return` o `approvals/reject` de la contrapartida (queda `returned`/`rejected`, no efectiva) · B=600 ⇒ 201 (A cuenta 400; contrapartida no) · B2=1 ⇒ 400 (`ya recibidas: 1000`) | en HEAD: la contrapartida `rejected` **cuenta** (no está `CANCELLED` y es `BIRD_RECEPTION` con la misma OC) ⇒ B=600 devuelve **400** (`ya recibidas: 800`) — rojo. Variante empresa B: `SapReference` con el mismo `sap_code` en otra empresa no altera el acumulado (control verde) |
| `test_r193_04_dos_reversos_dejan_el_acumulado_en_cero` | A1=400, A2=400 aprobadas · reversos efectivos de ambas · C=1000 ⇒ 201 · D=1 ⇒ 400 | `assert rC.status_code == 201` — HEAD: **400** (`ya recibidas: 1600`) |
| `test_r193_05_el_mensaje_reporta_el_neto` | A=400 aprobada y revertida · B=400 aprobada · C=700 ⇒ 400 | `assert 'ya recibidas: 400' in detail` — HEAD: «ya recibidas: 1200» |

Control adicional (verde en HEAD, se conserva): `test_purchase_order_receipt.py::test_t_014_05_una_recepcion_cancelada_deja_de_contar`.

## 2 · E2E runtime (API, pila local aislada)

Actores `TEST Super Admin` (`tokA`) y `TEST Aprobador` (`tokP`); OC importada por `POST /sap/references/import {references:[{ref_type:'purchase_order', sap_code:'AUD-R193-OC', quantity:1000}]}` (patrón `fixture-sap-refs` de la pasa 2); lote `AUD-R193` broiler con `TEST Galpon 02`.

| Paso | Acción | RED (HEAD) | GREEN | Limpieza |
|---|---|---|---|---|
| `R193-RT-00` | fixture OC + lote | 201 | 201 | borrar por prefijo `AUD-R193` |
| `R193-RT-01` | recepción 400 aprobada → reverso aprobado → recepción 400 | **400 BR-18** `ya recibidas: 800` | 201 | — |
| `R193-RT-02` | solicitud de reverso pendiente → recepción 700 → aprobar → recepción 700 | 400 / 400 | 400 / 201 | — |
| `R193-RT-03` | contrapartida rechazada → recepción 600 | 400 | 201 | — |
| `R193-RT-04` | dos reversos → recepción 1000 / 1001 | 400 / 400 | 201 / 400 | — |
| `R193-RT-05` | exceso real → texto `ya recibidas` | neto incorrecto | neto | — |

Artefacto: `audit/ga-claude-final-audit/evidence/r193/runtime-{red,c3}.json` (status, `detail`, `rule`, ids). Criterio: 0 5xx.

## 3 · UAT

No aplica (regla de backend sin superficie de usuario; `R-207` dará superficie al reverso). Caso opcional de aceptación técnica si el propietario lo solicita: «Tras anular por reverso una recepción, la misma OC admite de nuevo la cantidad» (ejecutado por el equipo con el runner y acta firmada).
