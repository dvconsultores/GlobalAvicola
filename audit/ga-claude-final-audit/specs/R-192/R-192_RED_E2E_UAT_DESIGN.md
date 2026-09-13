# R-192 · DISEÑO RED · E2E RUNTIME · UAT

Fecha: 2026-09-13 · HEAD `c0b4afc`. Los RED se escriben en C1 y se ejecutan sobre HEAD **antes** de tocar producto; el aserto que falla se cita con el valor observado esperado.

## 1 · Pruebas RED

### 1.1 Backend — `backend/tests/test_r192_lot_close_after_reversal.py`

Fixtures reutilizadas: `client`, `auth_headers`, `seeded_ids`, `motor` (patrón `tests/test_lot_close_approval.py:44-91`), `lote_cerrable` (`:94-135`: lote `broiler` con pesaje, alimento e inspección **aprobados**; BR-05 satisfecho) y los helpers de reverso de `tests/test_internal_reversal.py:226-253` (`_solicitar`, `_contrapartida`, `_aprobar_reverso`, `_reverso_efectivo`) adaptados a `client`/`auth_headers` (actor con `reversals:create` y aprobador distinto: `cabecera_de_rol`, `conftest.py:293`). Prefijo de datos `R192-`; teardown como `test_lot_close_approval.py:44-75` **más** `delete(Reversal)` y `ApprovalAction`.

| Test | Montaje | Aserto que falla en HEAD (valor observado) |
|---|---|---|
| `test_r192_01_un_par_revertido_no_impide_el_cierre` | `lote_cerrable` + `mortality_recording` de 5 aprobada por el flujo real (submit/start/complete) sobre saldo de recepción 100 aprobada; `POST /reversals {event_id, reason}` ⇒ 201; aprobar contrapartida ⇒ ambos `reversed` (control: `_estado == 'reversed'` ×2) | `assert r.status_code == 200` — HEAD: **400**, `rule == 'R7'`, `detail` contiene «2 en «reversed»» |
| `test_r192_02_la_contrapartida_pendiente_si_impide_el_cierre` | ídem sin aprobar la contrapartida (queda `pending_review`; variante `in_review` tras `review/start`) | `assert r.status_code == 400 and r.json()['rule']=='R7'` — HEAD: verde (**control**). Asertos de no mutación: `Lot.status=='active'`, `end_date is None`. Aserto condicional C-07: `'reverso pendiente' in detail` — HEAD: rojo |
| `test_r192_03_el_resumen_excluye_cancelados` | `lote_cerrable` + mortalidad 5 aprobada + mortalidad 10 **cancelada** (`POST /operations/{id}/cancel` en `registered`) + `egg_collection` 100 aprobada y 40 cancelada (lote `breeder` en la variante de huevos, o mismo lote: el tipo de lote no gobierna el sumatorio) | `assert body['total_mortality'] == 5` — HEAD: **15**; `assert body['total_eggs'] == 100` — HEAD: **140** |
| `test_r192_04_el_resumen_excluye_el_par_revertido` | `lote_cerrable` (alimento 100 kg aprobado de la fixture) + `feed_registration` 7 kg aprobada y **revertida** (par) | `assert body['total_feed_kg'] == 100.0` — HEAD: **400 antes de llegar** (R7); tras T-03 sin T-04: **114.0**. Aserto secundario `approved_events` no cuenta el par (verde en HEAD) |
| `test_r192_05_br05_ignora_el_pesaje_revertido` | lote con **un solo** pesaje aprobado y revertido (par) + alimento aprobado; sin más registros vivos | `assert r.status_code == 400 and rule == 'BR-05'` — HEAD (tras T-03; en HEAD puro devuelve 400 **R7**, por eso el aserto exige `rule == 'BR-05'` y falla en ambos casos) |
| `test_r192_06_ningun_estado_cambia_de_veredicto` | parametrizado: `BLOQUEAN` (7) ⇒ 400; `NO_BLOQUEAN` (6) ⇒ 200; **`REVERSED` por `_fijar_estado`** (sin fila `reversals`) ⇒ 200 | sólo el parámetro `reversed` falla en HEAD (400). Documenta que R7 decide por estado (C-10) |

Nota de aislamiento: cada test crea su lote (`PREFIJO`), no comparte estado; el reverso requiere aprobador ≠ solicitante (BR-14) — usar `auth_headers` (Super Admin) para solicitar y `cabecera_de_rol('approver')` para aprobar, como `test_internal_reversal.py`.

### 1.2 Frontend — `frontend/src/pages/lots/__tests__/r192.closeLotError.test.tsx`

Arnés: patrón `f01e.receptionHouse.test.tsx:1-65` (mock de `../../../services/api` con `get`/`post`; `react-i18next` con `t(k,f)=>f??k`; `MemoryRouter` `/lots/5` + `Route path="/lots/:id"`; `ToastProvider`; sesión `useAuthStore.setState` con `permissions:['lots:read','lots:create']` como `gaFe04.mastersGates.test.tsx:29-40`). `get` responde: `/lots/5` ⇒ `{id:5, lot_code:'R192', status:'active', bird_type:'broiler', farm_id:1}`; el resto (`/reports/kpis…`, `/operations?lot_id`, `/lots/5/phases`, `/operations/alerts`) ⇒ `{data:[]}` (los 403 de KPI no deben romper: control de robustez).

| Test | Acción | Aserto que falla en HEAD |
|---|---|---|
| «un 400 R7 al cerrar se muestra como toast con el detail» | click «Cerrar Lote» → confirmar en el modal → `post` rechaza con `{response:{status:400,data:{detail:'No se puede cerrar el lote: 1 registro(s) sin aprobar (1 en «pending_review»)…', rule:'R7'}}}` | `await screen.findByText(/sin aprobar/)` — HEAD: **no existe** (sólo `console.error`); además `expect(console.error).not.toHaveBeenCalledWith(expect.objectContaining(...))` opcional |
| «un 200 pinta el resumen» (control) | `post` resuelve `{data:{lot_id:5, lot_code:'R192', age_days:40, total_mortality:5, total_feed_kg:3, total_eggs:0, total_events:4, approved_events:2, status:'closed', end_date:'2026-09-13'}}` | `findByText('Lote Cerrado — Resumen Final')` y `getByText('5')` — verde en HEAD |
| «403 y 404 se muestran» | `post` rechaza 403 `{detail:'Permission denied: lots:create'}` / 404 `{detail:'Lot no encontrado'}` | `findByText(/lots:create/)` — HEAD: rojo |
| «un 422 con detail estructurado no rompe el render» (robustez) | `post` rechaza 422 `{detail:[{loc:['body','x'],msg:'Field required',type:'missing'}]}` | sin `pageerror`, toast «x: Field required» — HEAD: rojo (nada se muestra; no rompe porque no se renderiza) |

## 2 · E2E runtime (pila local aislada)

Entorno: `scripts_e2e.sh`-equivalente (backend 8099, frontend 5199, `seeds.test_seeds`, `Company.approval_levels = 1`). Actores: `TEST Super Admin` (crea lotes, registra, solicita reverso: tiene `reversals:create` por `("*", all)`), `TEST Aprobador` (`review:review`, aprueba). Datos: granja `TEST Granja`, galpón `TEST Galpon 02`.

| Paso | Actor | Acción | Esperado RED (HEAD) | Esperado GREEN (post-fix) | Limpieza |
|---|---|---|---|---|---|
| `H8b-control-fixture` | admin | lote `AUD-REV-CTRL` broiler + recepción 100 + pesaje + alimento 7 kg, cada uno aprobado (submit→start→complete por aprobador) | 201/200 | ídem | lotes con prefijo `AUD-REV-` se eliminan al final (SQL por prefijo, como los tests) |
| `H8b-control-cierra-200` | admin | `POST /lots/{ctrl}/close` | **200** | 200 | — |
| `H8b-reverso-fixture` | admin | lote gemelo `AUD-REV-REV` idéntico | 201/200 | ídem | — |
| `H8b-reverso-solicitado` | admin | `POST /reversals {event_id: feed, reason}` | 201, contrapartida `pending_review` | ídem | — |
| `H8b-reverso-efectuado` | aprobador | start + complete de la contrapartida | original `reversed`, contrapartida `reversed` | ídem | — |
| `H8b-cierre-con-reverso` | admin | `POST /lots/{rev}/close` | **400 R7** «2 registro(s) sin aprobar (2 en «reversed»)» | **200**, `total_feed_kg` = 0.0 (el único alimento fue revertido ⇒ **BR-05 400** si C-05 se implementa: entonces el gemelo lleva **dos** alimentos, uno revertido y otro vigente ⇒ 200 con `total_feed_kg` = kg del vigente) | — |
| `H8b-reversed-no-cancelable` | admin | `cancel` del original | 400 | 400 | — |
| `R192-UI-01` | admin (UI) | `/lots/{ctrl2}` → «Cerrar Lote» → confirmar | tarjeta de resumen | tarjeta con totales netos | captura |
| `R192-UI-02` | admin (UI) | lote con **contrapartida pendiente** → «Cerrar Lote» → confirmar | modal se cierra, **nada visible**; consola con el detail | **toast** con el detail R7 (y «reverso pendiente» si C-07); lote sigue `active` | captura escritorio 1366×768 + móvil 390×844 |
| `R192-UI-03` | admin (UI) | lote con par revertido → «Cerrar Lote» | sin feedback (400) | resumen (200) | captura |
| `R192-UI-04` | aprobador (UI) | `/lots/{id}`: botón «Cerrar Lote» | oculto (sin `lots:create`) — control | ídem; sonda API `close` ⇒ 403 | JSON |
| `H8b-timeline-*` | admin | `GET /audit/timeline/operational_event/{id}` original y contrapartida | filas `reversed` presentes (nota: duplicados por `P1-12-REOPEN`, no de este paquete) | ídem | — |

Registro: `audit/ga-claude-final-audit/evidence/r192/runtime-{red,c3}.json` (formato del runner: `pasos`, `asserts`, `pageerror`, `httpErrores`, `fatal_react`, `http5xx`) + PNG `R192-UI-0x.png`. Criterio: 0 `pageerror` React, 0 5xx.

## 3 · Plan UAT del propietario (visible al usuario)

Entorno: runtime real (`avicola.globaldv.net`) tras el despliegue de C2, con empresa de UAT y actores `UAT-09` (operador/aprobador/administrador), o pila local si el propietario lo prefiere. Duración estimada: 20 min.

| Caso | Pasos | Resultado esperado | Veredicto |
|---|---|---|---|
| UAT-R192-01 «Cerrar un lote con un reverso aprobado» | 1) Lote de engorde con recepción, pesaje y alimento aprobados. 2) Solicitar reverso de un registro de mortalidad (por API o, cuando exista `R-207`, por UI) y aprobarlo (ambos «Revertido»). 3) Detalle del lote → «Cerrar Lote» → confirmar. | El lote cierra; aparece «Lote Cerrado — Resumen Final»; la mortalidad del resumen **no incluye** la revertida. | ☐ |
| UAT-R192-02 «El sistema explica por qué no cierra» | 1) Lote con una solicitud de reverso **pendiente**. 2) «Cerrar Lote» → confirmar. | Mensaje visible (toast) con el motivo («registro(s) sin aprobar… reverso pendiente de decisión»); el lote sigue activo; el botón sigue disponible. | ☐ |
| UAT-R192-03 «El resumen no cuenta lo anulado» | 1) Lote con dos registros de mortalidad (5 aprobada, 10 anulada antes de aprobar) y alimento. 2) Cerrar. | `Mortalidad total = 5` (no 15); alimento sólo el vigente. | ☐ |

Decisión que el propietario ratifica en UAT: **C-01** (un reverso aprobado no impide el cierre) y **C-05** (un pesaje/alimento revertido no cuenta para BR-05).
