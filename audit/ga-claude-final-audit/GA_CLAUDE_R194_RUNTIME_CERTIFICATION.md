# GA-CLAUDE · R-194 — CERTIFICACIÓN (cadena de incubadora P-04/P-05 por UI + API)

Fecha: 2026-09-14 · Hallazgo **R-194** (P1 · bloquea P-04/P-05/X-BU, «5 causas acopladas») · Paquete `specs/R-194/` · Commits: C1 `c413fdb` · C2 `0bfba2e` · C2s `cd33d23` · Clarificaciones C-01 (A/B) y C-02 (capturar/derivar) con **default A** encoladas.

## 1 · Fases

| Fase | Estado | Evidencia |
|---|---|---|
| **C1 · RED** | ✅ | FE `evidence/red/vitest-r194.log` — **4F/1P**: `farm_id` undefined (BR-08), fértiles no escritos, dosis con envío silencioso, `hatchery_id` ausente; control: la carga ya enviaba. BE `evidence/red/backend-r194.log` — **1F/4P**: la cadena canónica encontró un defecto **real de servidor** (`egg_storage` con `lot_id=NULL` ⇒ 500: el `setdefault` no operaba porque el schema emite `lot_id: None` explícito); controles BR-03/BR-04/BR-08/BR-21 verdes |
| **C2 · Implementación** | ✅ | `evidence/green/` — BE **5/5** (cadena completa con `ChickBatch` y trazabilidad X-BU) · FE **41/41** dirigidas (R-194 6 + regresiones contiguas) · FE completa **386/386** · `tsc` 0 · commit `0bfba2e` |
| **C2s · Sensibilidad** | ✅ S1·S2·S3·S4 | **S1** (sin fértiles): 1F · **S2** (sin `valueAsNumber`): 1F · **S3** (sin ubicación de etapa): 1F · **S4** (sin `hatchery_id`): 1F — `evidence/sensibilidad/` |
| **C3 · Runtime** | ⏸ ventana de deploy | E2E-R194-01…07/07m/07en (cadena completa nube o local estable) — incluye repetición de `e2e/proceso-p05-incubacion.spec.ts` sobre fixtures corregidos |
| **UAT** | ⏸ agrupable | UAT-R194-01…05 (con R-190/R-205) |

## 2 · Implementación

- **Ubicación de etapa (C-01=A)**: `egg_reception_hatchery` y `chick_dispatch` entran en `location_events` con la ubicación del **lote incubadora** (planta/galpón; `resolverUbicacionDelEvento` extendido); el gate `farm_id` de la etapa incubadora los deja pasar y mantiene el mapeo anterior para el resto.
- **Saldo BR-03 (B-02)**: la recepción escribe `egg_movements[{egg_type:'fertile', quantity: recibidos}]` (C-04) además del almacenamiento.
- **`arrival_date` (B-03, C-02=A)**: capturada con default `event_date` y persistida en `egg_storage_records`.
- **Dosis (B-05)**: `valueAsNumber` en `birth_registration`; `-1` ⇒ error visible `operations.dosageInvalid` **sin petición** (validación por schema, sin `min` nativo que bloquee el submit).
- **`hatchery_id` (B-22)**: la incubadora elegida viaja en `hatchery_params[0]` (tenencia verificada en servidor).
- **Servidor (hallazgo B-03b)**: `egg_storage.lot_id` hereda del evento en alta **y** verificación (`or data.lot_id`), sin migración (`AC-R194-09`).

## 3 · AC

| AC | Estado |
|---|---|
| AC-R194-01 (recepción 201 con ubicación y `arrival_date`) | ✅ jsdom 01 · S3 · BE cadena |
| AC-R194-02 (fértiles en `egg_movements`) | ✅ jsdom 02 · S1 · BE saldo 1000 |
| AC-R194-03 (carga con petición/201) | ✅ control jsdom · BE carga 500 |
| AC-R194-04a/b (dosis válida envía; inválida ⇒ error visible sin POST) | ✅ jsdom 04a/04b · S2 |
| AC-R194-05 (despacho ⇒ 201 BR-04 real) | ✅ BE despacho 100 + BR-04 10000 |
| AC-R194-06 (`hatchery_id` en filas) | ✅ jsdom 06 · S4 |
| AC-R194-07 (cadena completa 0 fatales/0 5xx) | ⏸ C3 (API integrada ya en BE 5/5) |
| AC-R194-08 (ES/EN + móvil) | ⏸ C3 |
| AC-R194-09 (sin migración/endpoint/permiso; BR-02/03/04/21 intactas) | ✅ controles verdes |
| AC-R194-10 (EggBatch/ChickBatch X-BU) | ✅ BE: `chick_batches ≥ 1` + `traceability.chick_batches_sent ≥ 1` |

## 4 · Veredicto

**R-194 = `CLOSED_TECHNICALLY`** — la cadena de incubadora queda íntegra por UI y por API: recepción con saldo fértil y almacenamiento persistente, carga con BR-03, nacimiento con dosis validada, despacho con BR-04 y **handoff X-BU** (`ChickBatch` + trazabilidad). Defaults **C-01=A / C-02=capturada** (cola del propietario, no bloquean); C3 runtime en ventana. **P-04/P-05 quedan reparados técnicamente**; su `FUNCTIONALLY_CERTIFIED_E2E` se completa con la pasada runtime.
