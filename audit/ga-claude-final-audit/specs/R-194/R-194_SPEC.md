# R-194 · SPEC — CADENA DE INCUBADORA COMPLETABLE POR UI (RECEPCIÓN → CARGA → NACIMIENTO → DESPACHO)

Fecha: 2026-09-13 · Hallazgo canónico: **R-194** (P1 · bloquea) · HEAD `c0b4afc` · Origen B-01…B-33 + runtime local · Registro G-05. Secciones §47.

## 1 · Contexto

La cadena P-05 (`processCatalog.ts:406-417`): alta de lote incubadora → `hatchery_inspection` → `egg_reception_hatchery` → clasificación → `incubation_load` → `ovoscopía` → `transfer_to_hatcher` → `birth_registration` → despacho de pollitos. El backend implementa el dominio (BR-02/03/04/21, tenencia); el asistente tiene cinco defectos de contrato que la cortan.

## 2 · Evidencia

`R-194_FINDING.md §1` (código + runtime local HAT2-* + suites). Código: `OperationFormPage.tsx:139-149,170-177,274-278,386,438,1218-1236,1651,2044-2056`; `validators.py:149-175,828-839`; `schemas.py:85-87,101`; `service.py:873-877,956-960`.

## 3 · Causa raíz

Cinco defectos de contrato acumulados (ubicación excluida sin exención; saldo leído de movimientos no escritos; requerido no capturado; input sin `valueAsNumber`; selector sin camino al payload).

## 4 · Impacto de negocio

P-05/P-10/X-BU incompletas; datos de incubadora ausentes para KPI y para consolidación futura; operación real de incubadora imposible por la interfaz.

## 5 · Comportamiento actual → esperado

| # | Defecto | Hoy | Esperado |
|---|---|---|---|
| 1 | `farm_id` etapa incubadora ⇒ BR-08 | 400 siempre | **C-01**: la etapa incubadora envía granja/galpón de la planta/lote **o** BR-08 la exime (decisión de dominio); sin 400 |
| 2 | Fértiles en `egg_storage_records` | carga ⇒ BR-03 «0 disponibles» | La recepción escribe **`egg_movements[{egg_type:'fertile', quantity}]`** además del almacenamiento (el saldo BR-03 los lee) |
| 3 | `arrival_date` | 422 | **C-02**: capturada (campo) o derivada de `event_date`/`dispatch_date` (decisión); nunca 422 por omisión |
| 4 | `dosage_per_bird` | envío silencioso | `valueAsNumber` + error visible si inválido; el guardado procede |
| 5 | `hatchery_id` | nunca viaja | El selector viaja en las filas de parámetros (`hatchery_params.hatchery_id`) con tenencia |
| 6 | (B-33) `egg_dispatch` incubadora destino | uso dudoso | Documentado; sin cambio funcional en este paquete |

## 6 · Comportamiento esperado (cadena completa)

Tras el fix: recepción por UI ⇒ 201 con almacenamiento y fértiles; `incubation_load` consume el saldo (BR-03 real); ovoscopía y transferencia sin cambio; nacimiento con sanos/débiles (ya en UI) y dosis válida ⇒ 201; `chick_dispatch` ⇒ 201; los vínculos `EggBatch`/`ChickBatch` se completan (X-BU aguas arriba desbloqueado).

## 7 · Alcance

- `OperationFormPage.tsx`: etapa incubadora (ubicación según C-01), serializador de recepción (fértiles + almacenamiento + `arrival_date`), `dosage_per_bird`, `hatchery_id`.
- `operationPayload.ts`: extensiones del serializador (recepción incubadora) + helper de dosis; tests.
- i18n ES/EN: clave de error de dosis (si no reutilizable) y etiquetas.
- Tests: RED jsdom por defechos (5 casos) + regresión f01; backend control BR-03/BR-04/BR-21 (sondas).
- **Sin** migración; **sin** endpoint; **sin** permiso.

## 8 · Fuera de alcance

- Reverso/KPI de incubadora (OD-19 §18; R-204/R-214).
- AOD-23/AOD-24 (decisiones de nacimiento/tipos de huevo): se citan; el flujo actual se respeta.
- B-33 (uso semántico de `incubator_id` en despacho): documentado, sin cambio.
- Suites p05/p10 (GA-GOV-03 las actualiza).

## 9 · Impacto frontend

Cinco puntos del asistente + serializador; sin rediseño.

## 10 · Impacto backend

Ninguno de producto (BR-02/03/04/21 intactas). Solo pruebas de control.

## 11 · Contrato frontend↔backend

`POST /operations` (`egg_reception_hatchery`): gana `egg_movements[{fertile}]`, `arrival_date` (o equivalente decidido) y ubicación según C-01; `birth_registration` envía `dosage_per_bird` número o ausente; `hatchery_params[].hatchery_id` poblado. Esquemas existentes los admiten (`schemas.py:75-119`).

## 12 · Impacto en datos

Ninguno estructural. Eventos históricos de prueba con huevos «sin fértiles» no se reescriben; la bandeja/reportes quedan como están.

## 13 · Seguridad

Sin cambio (tenencia de `hatchery_id`/galpones ya verificada en servicio).

## 14 · Inquilino · 15 · Unidad · 16 · RBAC

Sin cambio (la unidad del lote incubadora se deriva como hoy).

## 17 · Transacciones

Sin cambio; los bloqueos de saldo BR-03 existentes aplican.

## 18 · Auditoría

Sin cambio.

## 19 · i18n

| Clave | ES | EN |
|---|---|---|
| `operations.dosageRequired` (si aplica) | Introduzca una dosis válida | Enter a valid dosage |

Etiquetas de recepción (fértiles, fecha de llegada) siguen el patrón existente.

## 20 · Escritorio

Recepción con campos completos; carga consume saldo; nacimiento envía; despacho 201.

## 21 · Móvil

390×844: los cinco pasos usables (verificación E2E móvil).

## 22 · Manejo de errores

| Caso | Comportamiento |
|---|---|
| dosis inválida | error visible junto al campo; sin envío |
| 422/400 residuales | texto seguro (R-189) |
| BR-03 sin saldo real | 400 legible (no será el caso normal tras el fix) |

## 23 · Impacto de migración

Ninguna.

## 24 · Impacto SAP

Habilita datos de origen de incubadora (nacimientos/despachos). Sin llamadas.

## 25 · Compatibilidad hacia atrás

- Lotes de otras cadenas: intactos.
- API: admite ambos cuerpos (fértiles añadidos); sin romper clientes.
- C-01/C-02 son decisiones de dominio: se documentan en el acta.

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| AC-R194-01 | `egg_reception_hatchery` por UI ⇒ **201** (sin 400 BR-08 ni 422 `arrival_date`) |
| AC-R194-02 | El payload incluye `egg_movements[fertile]` con la cantidad recibida; el saldo BR-03 queda > 0 tras aprobar |
| AC-R194-03 | `incubation_load` por UI ⇒ hay petición y 201 (consume saldo); mensaje claro si excede |
| AC-R194-04 | `birth_registration` con dosis rellenada ⇒ 201; con dosis inválida ⇒ error visible y sin envío; sin dosis ⇒ decisión C-03 registrada (opcional según dominio) |
| AC-R194-05 | `chick_dispatch` por UI ⇒ 201; BR-04 real si no hay viables |
| AC-R194-06 | `hatchery_id` viaja en filas y la tenencia se respeta (404/403 si ajena) |
| AC-R194-07 | Cadena completa E2E por UI (recepción→clasificación→carga→ovoscopía→transferencia→nacimiento→despacho) con 0 fatales y 0 `5xx` |
| AC-R194-08 | ES/EN y móvil 390×844 usables en los pasos de la cadena |
| AC-R194-09 | Sin migración/endpoint/permiso; BR-02/03/04/21 intactas (controles backend) |
| AC-R194-10 | X-BU: los vínculos `EggBatch`/`ChickBatch` se completan por UI (verificación cruzada con P-10) |

## 27 · Pruebas RED→GREEN

`§1`: `r194.hatcheryChain.test.tsx` (5 rojos: BR-08, fértiles, arrival_date, dosis, hatchery_id) + controles backend (`test_r194_hatchery_controls.py`: BR-03 con fértiles 201; BR-04; BR-08 exención/ubicación según C-01).

## 28 · E2E

`§2`: `E2E-R194-01…08` (cadena completa + móvil + EN + controles). Artefactos `evidence/runtime-c3/` (journal + PNG + payloads).

## 29 · UAT

`UAT-R194-01…05` (propietario; agrupable): recepción de huevos, carga, nacimiento con dosis, despacho, móvil. Criterio 5/5.

## 30 · Criterios de cierre

C-01/C-02/C-03 decididas · AC-R194-01…10 verdes · RED leída en `c0b4afc` · GREEN local · runtime con artefactos · suites p05/p10 remediadas (GA-GOV-03) verificadas · UAT 5/5 · sin migración/endpoint/permiso · R-194 → `CLOSED` con GA-REM asignado.
