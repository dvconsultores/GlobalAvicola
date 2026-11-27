# CERTIFICACIÓN LOCAL — GA-HATCHERY-V4-PIT-PRELOAD-DOMAIN-CORRECTION

Continuación de `GA-HATCHERY-V4-OD-FERTILE-EGGS-TO-PIT`. Spec: `specs/018-cutover-hatchery-v4-non-incubables/spec.md` §9 (§7 marcado SUPERSEDED).
Baseline `develop` = `4433ff1`; `main` = `1587073` (sin tocar). Rama `develop`; sin PR, sin cambios en `main`, sin despliegue a producción.

## 1. Decisión de dominio

```text
OD-HATCH-V4-01 = SUPERSEDED   (fosa POST-CARGA, 2026-11-21; texto conservado en §7)
OD-HATCH-V4-02 = RATIFIED     (fosa PRE-CARGA, 2026-11-26)
ROOT_CAUSE     = DOMAIN_CLARIFICATION   (no PROGRAMMER_REGRESSION)
```

Evidencia de la usuaria funcional (Maira Arellano): «La cantidad de Huevos Fértiles enviados a Fosa se descuenta desde el principio de la cantidad de Huevos recibidos. Cuando se realiza la Carga de Huevos, esa cantidad ya fue descontada.» La implementación anterior seguía la decisión Owner vigente entonces (OD-01).

## 2. Modelo

| | Antes (OD-01) | Ahora (OD-02) |
|---|---|---|
| Etapa de la fosa | post-carga (`set → transferred / fosa / en proceso`) | **pre-carga** (`received → no incubables / fosa / set / pendiente`) |
| `eggs_in_process` | `set − transferred − pit` (los tres KNOWN) | **`set − transferred`** (ambos KNOWN) |
| Validación de la fosa | `pit ≤ set`; `transferred + pit ≤ set` | **`pit ≤ received`**; **`set + oversized + dirty + broken + pit ≤ received`** (`≤`, igualdad válida) |
| Saldo disponible para cargar | `received − set − Σ no incubables` (sin la fosa) | **`received − set − oversized − dirty − broken − pit`**, solo con todo KNOWN; si no, UNKNOWN |
| BR-03 operativo | no restaba la fosa | resta la fosa **KNOWN** (un UNKNOWN no se resta: cota superior, igual que los no incubables) |
| `transferred ≤ set` | se conservaba | se conserva, sin la fosa |

UNKNOWN ≠ 0 en todo el recorrido: con un componente UNKNOWN el saldo disponible es UNKNOWN y solo se valida la cota con la suma conocida (si aun así supera lo recibido ⇒ `CONSISTENCY_MISMATCH`). `eggs_discarded` V4 sigue `NOT_APPLICABLE`, no se deriva y no recibe la fosa. V3 (`CUTOVER_HATCHERY_V3`) intacta.

## 3. Discovery de consumidores (búsqueda exhaustiva de `fertile_eggs_to_pit`)

| Consumidor | Cambio |
|---|---|
| `backend/app/cutover/validation.py` (`_consistencia_incubadora`, `_derivados`) | D-21/D-22; D-23; nuevo derivado `eggs_available_to_set` (D-24) |
| `backend/app/cutover/service.py` (reconciliación, orden del preview) | en proceso sin la fosa; disponible con la fosa; preview en dos etapas (D-26) |
| `backend/app/operations/validators.py` (`get_hatchery_egg_balance`, BR-03) | resta la fosa KNOWN (D-25) |
| `backend/app/cutover/contracts.py` | instrucciones de la plantilla (pre-carga) y reglas de promoción |
| `backend/scripts/cutover_v2_docs.py` → `audit/cutover-initial-balances/05`, `07` | reglas y linaje regenerados (los demás documentos solo cambiaban la fecha: restaurados) |
| `frontend/src/pages/cutover/CargasInicialesPage.tsx`, i18n es/en | preview en dos etapas + «Saldo disponible para cargar (derivado)» + leyenda; reconciliación reordenada; «(pre-carga)» |
| `docs/MANUAL_CARGAS_INICIALES.md`, `docs/plantillas_carga_inicial/cutover_template_hatchery_v4.xlsx` | regla vigente OD-02, OD-01 SUPERSEDED; plantilla regenerada |
| Reportes / KPIs | ningún reporte ni KPI fuera de la reconciliación de cargas iniciales consume la fosa: sin cambios |
| `backend/seeds/qa_integral_dataset.py` | fosa 0 / vacía: ya cumple la invariante; sin cambios |

## 4. Plantilla

`template_version = v4` · `schema_id = CUTOVER_HATCHERY_V4` · **columnas sin cambios** (23, mismo orden) · instrucciones regeneradas: «Cantidad acumulada de huevos fértiles recibidos que fueron enviados a fosa antes de la carga en incubadora, hasta la fecha de corte. Esta cantidad ya no forma parte de los huevos cargados.» Sin «ovoscopia» ni «POST-CARGA» (`evidence/20_template_v4_inspection.txt`). **Sin migración** (`fertile_eggs_to_pit` ya existe; cabeza Alembic sin cambios): `DB_MIGRATION_REQUIRED = NO`.

## 5. Pruebas

| Caso | Resultado |
|---|---|
| PIT-PRELOAD-01 (10000/8500/200/200/100/200 ⇒ saldo 800, BR-03 800) | PASS |
| PIT-PRELOAD-02 (suma = recibidos ⇒ saldo 0) | PASS |
| PIT-PRELOAD-03 (suma > recibidos; también cuando solo la fosa rompe; y con un UNKNOWN cuya suma conocida ya supera) | DENY ✔ |
| PIT-PRELOAD-04 (fosa 10001 > 10000; 10000 válida) | DENY ✔ |
| PIT-PRELOAD-05 (fosa UNKNOWN ⇒ saldo UNKNOWN; `dirty` UNKNOWN igual; BR-03 no resta lo desconocido) | PASS |
| PIT-PRELOAD-06 (fosa 0 conocida ⇒ saldo 1000) | PASS |
| PIT-POST-01 (9000/8000/fosa 500 ⇒ en proceso 1000, nunca 500) | PASS |
| PIT-POST-02 (transferidos 9001 > 9000 ⇒ un error en `eggs_transferred`) | DENY ✔ |
| PIT-POST-03 (transferidos = cargados con fosa 500 ⇒ válido, en proceso 0; transferidos UNKNOWN ⇒ UNKNOWN) | PASS |
| Doble conteo (… transferidos 8000 ⇒ saldo 800, en proceso 500, nunca 300) | PASS |
| O-15 (una fila con en proceso UNKNOWN ⇒ agregado UNKNOWN; la fosa vacía ya no lo vuelve UNKNOWN) | PASS |
| V3 histórica | PASS (sin cambios) |

| Suite | Pre-commit | Post-mutación | Evidencia |
|---|---|---|---|
| Backend completa | **2141 passed, 0 failed, 60 skipped** | **2141 passed, 0 failed, 60 skipped** | `evidence/backend_full_*.log` |
| Vitest completa | **822/822** | **821 passed + 1 skipped** (condicional preexistente de SPEC 016) | `evidence/frontend_vitest_*.log` |
| `tsc -b` / `vite build` | RC 0 / OK | RC 0 / OK | `evidence/frontend_{tsc,build}_*.log` |
| Backend dirigida (incubadora + cutover, 9 archivos) | 153 passed | — | — |
| E2E dirigida incubadora (OD-02, V4, O-15, p16) | **14/14** | — | `evidence/e2e_hatchery_dirigida.log` |
| E2E completa `--workers=1` | **238 passed, 0 failed** (241 − 7 de OD-01 + 4 de OD-02) | **238 passed, 0 failed** | `evidence/e2e_full_*.log` |
| Mutación (tras `8b288b2`, restauración por SHA) | **12/12 muertos**: M1..M5 del mandato §33 + reconciliación (2), BR-03, regla superada y 3 de UI | — | `evidence/mutation/` |

E2E OD-02 (`proceso-spec018d`): plantilla del batch con la instrucción nueva → carga → preview (saldo 800, en proceso 500) → aprobación con otro actor → aplicación → reconciliación (API y UI) → BR-03 (801 rechazado, 800 aceptado; luego saldo 0 y en proceso 1300) → recarga → re-login; negativos (suma y fosa > recibidos, igualdad válida); fosa vacía por CSV (saldo UNKNOWN en API y UI); transferidos = cargados con fosa 500. La «Reconciliación Opening/Post/Lifetime/Current» es el reporte de Cargas Iniciales.

Tests reemplazados (no relajados): la suite y la E2E de OD-01 se retiraron porque fijaban la regla superada; los mismos ejes se cubren con la regla nueva en `test_cutover_hatchery_v4_od02.py` y `proceso-spec018d`. Datos de tests que la invariante nueva invalidaba (fosa > 0 con 10000 = 9000 + 1000) se ajustaron bajando los cargados, sin tocar aserciones de regla.

## 6. Observaciones

- La E2E completa reescribe evidencia versionada de otras specs (capturas/JSON): restaurada con `git restore`, fuera del commit.
- O-28 (flake preexistente de `userBuPanel` en vitest completa) no apareció en la corrida pre-commit.
- `OPERATIONAL_MODEL_GAP` (sin evento operativo de fosa ni `oversized`) sigue abierto, fuera de alcance.

## 7. Decisión local

`OD-HATCH-V4-01 = SUPERSEDED` · `OD-HATCH-V4-02 = CLOSED` · `HATCHERY_V4 = CERTIFIED` (local; la paridad de runtime se verifica tras el push) · `OWNER_ACCEPTED = NO`.
