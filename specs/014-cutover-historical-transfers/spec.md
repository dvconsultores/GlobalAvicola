# SPEC 014 — Cutover: transferencias históricas entre lotes en saldos de apertura
**Identificador:** `CUTOVER-HISTORICAL-TRANSFERS` · tarea `GA-CUTOVER-HISTORICAL-TRANSFERS` (hallazgo `CUTOVER-BALANCE-TRANSFER-01`) · **Fecha:** 2026-11-07
**Tipo:** amendment de SPEC 006 (cutover v2) y SPEC 009 (versionado de plantillas). No es una arquitectura nueva: añade campos al contrato por BU existente.
**Entrada:** carga real de Reproductoras (Emiglé): `alojadas − mortalidad − descartes ≠ vivas` aunque los cuatro datos son correctos, porque hubo transferencias de aves entre lotes antes del corte.

## 1. Discovery
| Pregunta | Hallazgo (código real) |
|---|---|
| Fórmula actual | `validation.py::_consistencia_reproductoras`: por sexo, **solo si** `live`, `birds_placed`, `historical_mortality` y `historical_culls` son KNOWN: `placed − mortalidad − descartes == live`; si no, `CONSISTENCY_MISMATCH` (error duro). Con cualquier pieza UNKNOWN **no se evalúa** (test `test_consistencia_sin_tolerancias`). |
| Por qué falla con datos reales | La ecuación supone que solo hubo mortalidad y descarte. Un lote que entregó o recibió aves queda fuera de la identidad ⇒ rechazo de un lote válido. |
| Contrato compartido | `grandparent` y `breeder` usan el **mismo** `_metricas_reproductoras` y el mismo validador (`ONE_CONTRACT_PER_BUSINESS_UNIT` por población por sexo). |
| Semántica de `live_*` | `live_males/females → opening_balances.initial_*_count`. `get_current_bird_balance` = apertura + eventos; el histórico **no se resta** (RC-08, `docs/02 §3.9.2`). Por tanto los nuevos acumulados son **informativos + verificación**, igual que mortalidad/descartes: no pueden duplicar saldo. |
| Modelo de transferencia existente | Operativo: `EventType.BIRD_TRANSFER` es **neutro intra-lote** (`RR-02`); no existe hoy movimiento de población entre lotes. Una transferencia entre lotes posterior al corte se registra con los eventos de salida/recepción existentes (`BIRD_EXIT` en origen, `BIRD_RECEPTION` en destino): fuera de alcance. Terminología del cutover: `historical_<concepto>_<sexo>` (`historical_mortality_males`) y DB `accumulated_<concepto>_<male|female>`. |
| Versionado | Por BU: `contrato.version`, exigida por igualdad en el parser (SPEC 009: incubadora `v3`, resto `v2`). Opción A (rechazar la anterior) ya es el sistema vigente. El default de CSV es `TEMPLATE_VERSION` global (`v2`): con breeder/grandparent `v3` hay que usar la versión del contrato. |
| UNKNOWN | Parser: vacío = UNKNOWN, `0` = KNOWN, `N/A` solo si `allow_na`. `_entero` guarda 0 pero el `*_status` conserva UNKNOWN (`UNKNOWN nunca es 0`). |
| Aplicación | `_opening_reproductoras` escribe `OpeningBalance`; `reconciliacion` = apertura + post-corte; `current_live = live + entradas − salidas` (post). |

## 2. Alcance por BU
| BU | Transferencias históricas posibles | Modelo actual las representa | Cambio |
|---|---|---|---|
| Reproductoras (`breeder`) | **SÍ, demostrado** | NO | **SÍ** — 4 campos + v3 |
| Progenitoras (`grandparent`) | Plausible (misma estructura de población por sexo; sin evidencia directa del usuario) | NO | **SÍ**, por **contrato compartido**: dejar `grandparent` atrás reproduciría el mismo rechazo y obligaría a bifurcar el contrato/validador. Campos opcionales (UNKNOWN si no se conocen) ⇒ coste nulo para quien no los necesita. *Decisión de alcance a confirmar por el usuario clave; reversible.* |
| Engorde (`broiler`) | Posible, **no demostrado**. Población mixta; ya tiene `accumulated_birds_received` (recepciones, incluye llegadas de cualquier origen) y `partial_outbound_birds` (salidas a planta). | Parcialmente (entradas sí; salidas entre lotes no) | **NO** en este delta. Si el usuario confirma movimientos entre lotes en Engorde, delta propio con campos *mixtos* (sin sexo). No se copia el modelo macho/hembra. |
| Incubadora (`hatchery`) | No (balance de huevos/pollitos) | n/a | **NO** |

## 3. Modelo elegido
Nombres canónicos (convención del repo): `historical_transfers_in_males`, `historical_transfers_in_females`, `historical_transfers_out_males`, `historical_transfers_out_females` — enteros ≥ 0, `metric=True`, **opcionales**, sin `N/A` (la ausencia de transferencias se declara con `0`; desconocido = vacío).
Destino DB (`opening_balances`, aditivo): `accumulated_transfers_in_male|female`, `accumulated_transfers_out_male|female` (Integer **nullable**; NULL = UNKNOWN) + `transfers_in_status`, `transfers_out_status` (String(15); `server_default 'UNKNOWN'`: las aperturas existentes **no** pasan a «0 conocido»).
Semántica: **acumulados históricos hasta el corte**; no son eventos nuevos; no se crean eventos ficticios; `birds_placed_*` sigue siendo el alojamiento original.

**Ecuación (por sexo, todo KNOWN):** `live = placed + transfers_in − mortality − culls − transfers_out`.
**Veredicto por sexo:** `CONSISTENT` (los 6 componentes KNOWN y cuadra) · `INCONSISTENT` (los 6 KNOWN y no cuadra ⇒ `CONSISTENCY_MISMATCH`, error duro, mensaje con la ecuación nueva) · `NOT_FULLY_VERIFIABLE` (algún componente UNKNOWN ⇒ **sin error**, sin inventar ceros). El veredicto se expone en `derived.balance_check` (`{males, females}`) del preview y `summary.balance_not_fully_verifiable_rows`.
**Rechazadas:** un solo campo neto «transferidos» (solo resuelve el origen, pierde el receptor y la trazabilidad); sumar transferencias a `birds_placed_*` (destruye el alojamiento original); inflar mortalidad/descartes (cambia semántica); eventos históricos ficticios (fechas inventadas); cambiar la obligatoriedad de mortalidad/descartes; hacer bloqueante una reconciliación global `Σ in = Σ out` (el origen/destino puede no estar en la carga; fuera de alcance, no se implementa).

## 4. Versionado y compatibilidad
`grandparent` y `breeder` pasan de `v2` a **`v3`**; `schema_id` `CUTOVER_GRANDPARENT_V3` / `CUTOVER_BREEDER_V3`; descarga `cutover_template_breeder_v3.xlsx`. `broiler` sigue `v2`, `hatchery` `v3`. Compatibilidad: **opción A** (rechazar `v2` de breeder/grandparent con `TEMPLATE_VERSION_UNSUPPORTED` y mensaje «descargue la v3»): una plantilla sin las 4 columnas no puede representar el saldo. CSV sin hoja `Meta`: la versión por defecto es la **del contrato de la BU**. `opening_balances.template_version` guarda `v3`. Sin migración de datos de lotes ya aplicados (decisión separada).

## 5. Criterios de aceptación
| AC | Enunciado |
|---|---|
| **AC-HT-01** | El contrato de `breeder` y `grandparent` expone los 4 campos (int ≥ 0, opcionales, sin N/A, destino `opening_balances.accumulated_transfers_*`), versión `v3`, `schema_id …_V3`; `lineage()` sin campos sin destino. |
| **AC-HT-02** | Hoja `Instrucciones` (XLSX y CSV equivalente) explica cada campo: unidad aves, acumulado hasta el corte, sin movimientos posteriores, `0` solo si se sabe que no hubo, vacío = desconocido. |
| **AC-HT-03** | Parser: `v2` de breeder/grandparent ⇒ `TEMPLATE_VERSION_UNSUPPORTED`; negativo/decimal/texto ⇒ error de campo con mensaje claro (`La cantidad de transferencias históricas no puede ser negativa.` y equivalentes); `N/A` ⇒ `NOT_APPLICABLE_NOT_ALLOWED`; CSV por defecto = versión del contrato. |
| **AC-HT-04** | Validación por sexo con la ecuación nueva (BR-T01…T10 y los dos lotes realistas); `NOT_FULLY_VERIFIABLE` sin error ni cero inventado; `broiler`/`hatchery` sin cambios. |
| **AC-HT-05** | Staging y preview: los valores y su estado pasan por el pipeline normal; `derived.balance_check` y el conteo en el resumen. |
| **AC-HT-06** | Apply: los acumulados forman parte del opening (`accumulated_transfers_*` + status); `initial_*_count == live_*` declarado; no se crea ningún evento operativo. |
| **AC-HT-07** | Reconciliación: el bloque `opening` expone transferencias y sus estados (UNKNOWN no se muestra como 0); `current_live = live + entradas − salidas` **no** vuelve a sumar el histórico (sin doble conteo, probado con evento posterior al corte). |
| **AC-HT-08** | Migración Alembic aditiva y reversible (6 columnas); aperturas existentes quedan `UNKNOWN`; la cabeza Alembic y los pines del arnés se avanzan de forma consciente. |
| **AC-HT-09** | Auditoría: staging normalizado + `opening_balances` reconstruyen placed/mortality/culls/transfers in/out/live. RBAC y aislamiento de empresa sin cambios (regresión de suites de cutover). |
| **AC-HT-10** | E2E breeder v3: lote **origen** (salida histórica) y lote **receptor** (entrada histórica) completan descarga→carga→validar→preview→enviar→aprobar→aplicar→reconciliar, evento posterior al corte, refresh/relogin y sin doble conteo. |
| **AC-HT-11** | RED→GREEN: la carga con salida histórica (`1300−165−0−300=835`) y con entrada (`1000+300−100−20−0=1180`) falla con el modelo/plantilla anteriores y pasa con v3. |

## 6. Matriz BEFORE / AFTER (a demostrar con tests)
| Caso | Modelo anterior | Nuevo | Esperado |
|---|---|---|---|
| Sin transferencias (todo 0) | cuadra | cuadra | PASS |
| Salida histórica | `CONSISTENCY_MISMATCH` | cuadra | PASS |
| Entrada histórica | `CONSISTENCY_MISMATCH` | cuadra | PASS |
| Saldo realmente incorrecto | error | error | PASS |
| UNKNOWN | no evalúa | `NOT_FULLY_VERIFIABLE`, sin cero inventado | PASS |

## 7. Fuera de alcance
SAP; transferencias individuales (lote origen/destino, fecha, documento); cambios al flujo operativo; Engorde e Incubadora; migración de lotes ya aplicados; correcciones formales de opening sobre los nuevos campos (los `placed_*` tampoco son corregibles); KPIs; reglas de roles.

## 8. Constitution Gate · Authorization Gate
Spec suficiente PASS · alcance acotado (2 BU de contrato compartido + versión) PASS · sin decisión material nueva (el usuario final confirmó que ocurren; no se exige lote origen/destino, ni eventos individuales, ni tratamiento SAP, ni cambio sobre batches aplicados) PASS · API: sin endpoints nuevos; `template_version`/`schema_id` cambian; payloads de preview/reconciliación aditivos PASS · DB: 6 columnas aditivas, reversibles PASS · seguridad/tenant: sin cambio PASS · UNKNOWN≠0 preservado PASS · AC verificables PASS.
**AUTHORIZATION GATE: PASS.** Observación a confirmar (no bloqueante): inclusión de `grandparent` por contrato compartido; Engorde diferido.

## 9. Trazabilidad / tareas
T1 contrato+versión · T2 migración+modelo · T3 parser (CSV default, mensajes) · T4 validación tri-estado + `balance_check` · T5 apply (`_opening_reproductoras`) · T6 reconciliación/preview · T7 plantilla/Instrucciones/docs · T8 fixtures y tests existentes (v2→v3, pines Alembic) · T9 RED/GREEN nuevos · T10 E2E · T11 regresión + sensibilidad + evidencia.
