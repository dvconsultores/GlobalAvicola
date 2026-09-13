# R-193 · SPEC — ACUMULADO BR-18 NETO DE REVERSOS

Fecha: 2026-09-13 · Hallazgo canónico: **R-193** (P2 · bloquea integridad) · HEAD `c0b4afc` · Origen E-01 · Registro G-04. Secciones §47.

## 1 · Contexto

`BR-18` (`G-R05`, `OD-04`, `GA-REM-035`): la cantidad **acumulada** recibida contra una orden de compra no puede exceder `SapReference.quantity`; el acumulado suma `bird_movements.quantity` de las recepciones con la misma `sap_document_ref` y `status ≠ CANCELLED` (`validators.py:769-783`). `OD-19`/`GA-REM-041` añadió el reverso: la contrapartida copia el original (incluida `sap_document_ref`, `reversals/service.py:126-134`) y, al aprobarse, ambos quedan `REVERSED` (`:215-216`). Los saldos de aves ya restan la contrapartida efectiva (`_suma_neta`, `validators.py:21-46`); BR-18 no.

## 2 · Evidencia

`R-193_FINDING.md §2`. Código: `validators.py:769-783`, `:744-748`, `:21-46`; `reversals/service.py:126-134, 140-145, 215-216, 33-36`; `operations/service.py:898-906`; tests sin cobertura `test_purchase_order_receipt.py:106-258`.

## 3 · Causa raíz

Deriva entre tranches (`GA-REM-035` → `GA-REM-041`): la aritmética neta se aplicó a los saldos por lote y no al acumulado por documento SAP. Sin prueba que combine BR-18 y reverso.

## 4 · Impacto de negocio

Tras un reverso de recepción, la OC «pierde» 2n de capacidad: entregas reales rechazadas; conciliación contra SAP inflada. Afecta a toda cadena que recibe aves con OC (Progenitoras, Reproductoras, Engorde).

## 5 · Comportamiento actual

OC 1000 · recepción 400 aprobada · reverso aprobado (par `REVERSED`) · nueva recepción 400 ⇒ **400 BR-18** «…elevaría lo recibido… a 1200… (ya recibidas: 800)».

## 6 · Comportamiento esperado

Mismo escenario ⇒ **201**; el mensaje de BR-18 en un exceso real reporta `ya recibidas` **neto** (0 tras el reverso). El acumulado = Σ natural de recepciones `≠ CANCELLED` que **no** son contrapartidas − Σ de contrapartidas **efectivas** (`REVERSED`) ⇒ equivalente a excluir `REVERSED` y contrapartidas (ambos miembros del par en `REVERSED`). Contrapartida **pendiente** (no efectiva): no cuenta (no es recepción). Original `APPROVED` con contrapartida pendiente: cuenta (la recepción ocurrió y sigue vigente hasta que el reverso sea efectivo — `OD-19 §2`).

## 7 · Alcance

1. `validate_oc_limit` (`validators.py:769-783`): acumulado neto (C-01: exclusión de `REVERSED` + `id ∉ Reversal.reversal_event_id`, o `_suma_neta`-por-documento; elegir la forma más simple que preserve `exclude_event_id`/`company_id`).
2. Docstring `:744-748` actualizado: precedente = `_suma_neta` (`OD-19`).
3. Tests: `test_purchase_order_receipt.py` ampliado o nuevo `test_r193_oc_limit_after_reversal.py` (RED §1 del diseño); regresión `test_internal_reversal.py`, `test_edit_validation_parity.py`, `test_reception_reconciliation.py`.
4. Certificación runtime por API (pila local): escenario OC 1000 / 400 / reverso / 400 ⇒ 201.

## 8 · Fuera de alcance

- `validate_oc_limit` invocada para `BIRD_DISTRIBUTION` (`service.py:898-906`): una distribución con `sap_document_ref` de OC suma su `total_qty` como si fuera recepción (observación OBS-R193-01; sin evidencia de uso por UI — el asistente sólo ofrece OC en recepción/importación — se registra en backlog, no se corrige aquí).
- Cierre automático de la OC, tolerancias (`GA-REM-035` los excluye).
- Reverso de `grandparent_import` (no elegible) y conciliación importación↔OC (`GA-REM-042 §2.26`).
- UI del reverso (`R-207`); UI del cuadre BR-20 (`R-205`).
- Semántica de `REVERSED` en KPI/`reports` (E-24/`R-214`).

## 9 · Impacto frontend

Ninguno. (El mensaje de BR-18 se muestra ya vía `getErrorMessage` en el asistente, `R-189`.)

## 10 · Impacto backend

`backend/app/operations/validators.py` (`validate_oc_limit`): la subconsulta `acumulado_q` gana `status.not_in([CANCELLED, REVERSED])` **y** `OperationalEvent.id.not_in(select(Reversal.reversal_event_id))` (defensa: una contrapartida no efectiva nunca es una recepción). Sin cambios en `reversals/service.py`, `operations/service.py`, esquemas, rutas, permisos.

## 11 · Contrato frontend↔backend

`POST /operations` (`bird_reception`) sin cambio de forma. Error `400 {detail, rule:'BR-18'}` sin cambio; el valor `ya recibidas` pasa a ser neto.

## 12 · Impacto en datos

Sin migración; ninguna fila cambia. Efecto inmediato sobre OCs con reversos históricos (hoy ninguna en producción real por ausencia de UI de reverso; en pruebas sí).

## 13 · Seguridad

Sin superficie nueva. La subconsulta conserva `company_id` (`validators.py:776-780`): la contrapartida hereda `company_id` del original (`reversals/service.py:126-131`), luego el filtro de empresa sigue aplicando.

## 14 · Inquilino

`SapReference` buscada dentro de la empresa (`:757-763`) y acumulado por `company_id` (`:779-780`). Sin cambio.

## 15 · Unidad de negocio

Sin cambio: la unidad se exige en el alta (`exigir_unidad_operativa`, `service.py`), no en BR-18.

## 16 · RBAC

Sin cambio (`operations:create`).

## 17 · Transacciones

BR-18 se evalúa dentro de la transacción del alta (`RutaTransaccional`), antes de persistir. No hay bloqueo de la OC (fuera de alcance: dos recepciones concurrentes contra la misma OC ya podían superar el límite — carrera preexistente, OBS-R193-02 al backlog, no P1).

## 18 · Auditoría

Sin cambio (rechazo BR-18 no audita; alta audita `CREATED`).

## 19 · i18n

Mensaje de regla en ES (patrón vigente). Sin claves nuevas.

## 20 · Escritorio · 21 · Móvil

Sin cambio de UI. El asistente muestra el 400 como ya certificó `R-189` (AC19-AC26).

## 22 · Manejo de errores

`400 BR-18` sólo cuando el neto + cantidad > ordenado; `400 BR-07/BR-08/BR-17` sin cambio; 401/403/404 sin cambio; 409 (`idempotency_key`) sin cambio; 422 sin cambio.

## 23 · Impacto de migración

Ninguna.

## 24 · Impacto SAP

El acumulado contra la OC es el dato que P-08 conciliará; pasa a reflejar lo realmente recibido. `SapReference` (réplica) intacta. SAP sigue siendo sistema de registro futuro.

## 25 · Compatibilidad hacia atrás

Comportamiento idéntico sin reversos (`test_t_014_01…07` intactos). Con reversos: cambia de «rechaza» a «acepta» — corrección, no ruptura.

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| AC01 | OC 1000 · recepción A 400 aprobada · reverso de A efectivo · recepción B 400 ⇒ **201**; mensaje BR-18 de una tercera de 700 reporta `ya recibidas: 400` (sólo B). |
| AC02 | Reverso **pendiente** (contrapartida `pending_review`): A sigue contando ⇒ recepción B de 700 ⇒ 400 BR-18 (`ya recibidas: 400`); tras aprobar el reverso ⇒ 201. |
| AC03 | Contrapartida **rechazada** o **cancelada**: A cuenta (400); la contrapartida no. |
| AC04 | Dos reversos sucesivos sobre dos recepciones de 400 ⇒ acumulado 0 ⇒ recepción de 1000 ⇒ 201; de 1001 ⇒ 400. |
| AC05 | Sin reverso: `test_t_014_01…07` intactos (parciales, resto exacto, exceso, una unidad de más, cancelada, otra empresa, completar). |
| AC06 | `exclude_event_id` (edición `R-176`): editar la recepción B no la cuenta dos veces (`test_edit_validation_parity.py` verde). |
| AC07 | Empresa: la contrapartida de otra empresa (misma `sap_code`) no influye (control de aislamiento). |
| AC08 | Sin migración, endpoint ni permiso nuevo; guardianes exactos. |
| AC09 | Regresión: `test_purchase_order_receipt.py`, `test_internal_reversal.py`, `test_reception_reconciliation.py`, `test_edit_validation_parity.py`, `test_population_invariant.py` verdes (PG local, por diferencia vs línea base `GA-GOV-03`). |
| AC10 | Runtime por API (pila local): escenario AC01 reproducido con artefacto JSON. |

## 27 · Pruebas RED→GREEN

`R-193_RED_E2E_UAT_DESIGN.md §1`: `test_r193_01_tras_un_reverso_efectivo_la_oc_recupera_su_capacidad` (rojo: 400), `test_r193_02_el_reverso_pendiente_no_libera_la_oc` (control verde + segunda mitad roja), `test_r193_03_la_contrapartida_rechazada_no_cuenta` (rojo si cuenta), `test_r193_04_dos_reversos_dejan_el_acumulado_en_cero` (rojo), `test_r193_05_el_mensaje_reporta_el_neto` (rojo). GREEN: dirigidos + regresión.

## 28 · E2E

Runtime por API sobre pila local (`R-193_RED_E2E_UAT_DESIGN.md §2`): `R193-RT-01…05`, artefacto `evidence/r193/runtime-{red,c3}.json`. Sin UI.

## 29 · UAT

No visible al usuario final de forma directa (regla de backend); **no requiere UAT del propietario**. Se informa en el acta de certificación y se propone un caso opcional de aceptación técnica (recepción tras reverso por API) si el propietario lo pide.

## 30 · Criterios de cierre

RED válido · GREEN local · AC01-AC10 · sensibilidad (S1: retirar la exclusión de `REVERSED` ⇒ AC01/AC04 rojas; S2: retirar la exclusión de contrapartidas pendientes ⇒ AC02/AC03 rojas) · runtime C3 · backlog (R-193 → GA-REM al autorizar; OBS-R193-01/02 registradas).
