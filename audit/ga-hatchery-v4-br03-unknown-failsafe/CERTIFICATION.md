# CERTIFICACIÓN LOCAL — GA-HATCHERY-V4-BR03-UNKNOWN-FAILSAFE

Continuación de `GA-HATCHERY-V4-PIT-PRELOAD-DOMAIN-CORRECTION` (OD-HATCH-V4-02). Spec: `specs/018-cutover-hatchery-v4-non-incubables/spec.md` §10 (D-28..D-31, AC-V4-30..36; reemplaza a D-25).
Baseline `develop` = `92fa7d3`; IMPL = `fd52b90`; `main` = `1587073` (sin tocar). Rama `develop`; sin PR, sin cambios en `main`, sin despliegue a producción.

## 1. Causa raíz

D-25 (OD-02) permitía a BR-03 restar solo los componentes pre-carga **KNOWN**: con la fosa o un no incubable vacío, el saldo operativo era `recibidos − cargados − Σ(conocidos)`, una **cota superior**, y se usaba como saldo disponible demostrado. Una carga de incubación podía así consumir huevos que en realidad ya estaban en fosa o descartados. Preview y reconciliación ya mostraban UNKNOWN; BR-03 no: dos semánticas para la misma magnitud.

## 2. Regla

```text
UNKNOWN != 0   ·   UNKNOWN != SAFE_TO_IGNORE
available_to_set = received − set − oversized − dirty − broken − pit   (solo si los seis son KNOWN)
                 = UNKNOWN                                            (si cualquiera es UNKNOWN)
requested > 0 AND available_to_set = UNKNOWN  ⇒  DENY 400 CUTOVER_BALANCE_INCOMPLETE
```

Mensaje funcional (sin nombres técnicos): «No se puede determinar el saldo disponible para cargar porque la carga inicial de Incubadora contiene valores desconocidos. Corrija o complete la carga inicial antes de registrar una nueva carga de huevos.»

| | Antes (D-25) | Ahora (§10) |
|---|---|---|
| BR-03 con un componente UNKNOWN | no lo resta: autoriza contra la cota superior | saldo UNKNOWN ⇒ **DENY** toda carga positiva |
| Cero conocido | se computa | se computa (no es UNKNOWN) |
| Preview / reconciliación / BR-03 | BR-03 divergía | **una sola función**: `backend/app/cutover/saldo_incubadora.py · saldo_apertura_por_cargar` |
| Anular recepción de incubadora (retiro de entrada) | usaba la cota | mismo DENY con saldo UNKNOWN |
| Apertura V3 histórica | `received − set` | `received − set` (sin cambios; los componentes V4 no existen en V3) |
| `eggs_in_process` | `set − transferred` | sin cambios |
| Fosa | PRE-CARGA | PRE-CARGA (sin cambios) |

## 3. Suma parcial conocida

| Uso | ¿Se usa? |
|---|---|
| Consistencia (`set + Σ(pre-carga KNOWN) ≤ received`; si ya excede, la fila se rechaza aunque haya UNKNOWN) | **SÍ** |
| Autorización (saldo para cargar, BR-03, retiro de entrada) | **NO** |

## 4. Desbloqueo gobernado

El operador nunca escribe un saldo. `POST /opening-balances/{id}/corrections` se extiende a los cuatro componentes pre-carga de aperturas de incubadora **V4** (`eggs_non_incubable_oversized|dirty|broken`, `fertile_eggs_to_pit`): permiso `corrections:correct`, motivo obligatorio, auditoría (`audit_accion`) con estado previo/nuevo, el original se conserva (`old_value = null` cuando era UNKNOWN), el componente pasa a KNOWN. 422 si el valor es negativo, si la apertura no es V4 o si `set + Σ pre-carga` superaría lo recibido. La reconciliación expone `opening_id` para encadenar la corrección. Ruta: Cargas Iniciales → corrección auditada → reconciliación.

## 5. Pruebas

RED (antes de implementar): `evidence/10_red.log` — 10 failed, 1 passed (U07, todo KNOWN, ya pasaba).

| Caso | Resultado |
|---|---|
| BR03-U01 `dirty` UNKNOWN ⇒ UNKNOWN en preview/reconciliación/BR-03; cargar 1 ⇒ 400 `CUTOVER_BALANCE_INCOMPLETE` | PASS |
| BR03-U02 corregir `dirty = 700` ⇒ saldo 300; 300 ⇒ 201; 1 más ⇒ 400 BR-03 | PASS |
| BR03-U03 `dirty = 0` conocido ⇒ 1000; también tras corregir UNKNOWN → 0 | PASS |
| BR03-U04 suma conocida > recibidos con un UNKNOWN ⇒ fila rechazada; corrección que la provocaría ⇒ 422 | PASS |
| BR03-U05 fosa UNKNOWN ⇒ DENY | PASS |
| BR03-U06 oversized / dirty / broken UNKNOWN ⇒ DENY (parametrizado) | PASS ×3 |
| BR03-U07 todo KNOWN (10000/8500/200/200/100/200) ⇒ 800; 801 ⇒ 400; 800 ⇒ 201 | PASS |
| Retiro de entrada con saldo UNKNOWN ⇒ 400 | PASS |
| V3 histórica: sin bloqueo; corrección de componente V4 ⇒ 422 | PASS |
| O-15 (en proceso UNKNOWN por fila ⇒ agregado UNKNOWN) | PASS (suites V4/OD-02 y E2E `proceso-spec018c`) |

Tests ajustados a la regla nueva (no relajados): PRELOAD-05 de `test_cutover_hatchery_v4_od02.py` y AC-V4-10(c) de `test_cutover_hatchery_v4.py` afirmaban la cota superior (D-25); ahora afirman `is None`.

E2E `proceso-spec018e` (E2E-BR03-01): carga inicial V4 con `dirty` vacío → preview UNKNOWN (API y UI) → envío, aprobación por otro actor, aplicación → reconciliación UNKNOWN → carga de 1 ⇒ 400 con mensaje funcional (sin `None/null/UNKNOWN/eggs_`) → corrección `dirty = 0` (old_value null) → reconciliación 1000 → carga 600 ⇒ 201 → 401 ⇒ 400 BR-03 → saldo 400 → recarga → re-login. Evidencia: `evidence/e2e_br03/`.

| Suite | Pre-commit | Post-mutación (HEAD `fd52b90`) | Evidencia |
|---|---|---|---|
| Backend completa | **2152 passed, 0 failed, 60 skipped** | **2152 passed, 0 failed, 60 skipped** | `evidence/backend_full_*.log` |
| Vitest completa | 821 passed, **1 failed (O-28)** | 820 passed + 1 skipped, **1 failed (O-28)** | `evidence/frontend_vitest_*.log`, `evidence/frontend_o28_clasificacion.txt` |
| `tsc -b` / `vite build` | RC 0 / OK | RC 0 / OK | `evidence/frontend_{tsc,build}_*.log` |
| Backend dirigida (13 archivos de incubadora/cutover/correcciones) | 152 passed | — | — |
| E2E dirigida incubadora (018e, 018d, 018, 018c, p16) | **15/15** | — | `evidence/e2e_hatchery_dirigida.log` |
| E2E completa `--workers=1` | **239 passed, 0 failed** (238 + 1) | **239 passed, 0 failed** | `evidence/e2e_full_*.log` |
| Mutación (tras `fd52b90`, restauración por SHA) | **9/9 muertos** | — | `evidence/mutation/driver_run.log` |

Mutantes: M1 fosa UNKNOWN → 0 · M2 `dirty` UNKNOWN → 0 · M3 suma conocida como saldo exacto · M4 se elimina el bloqueo de BR-03 · M5 el 0 conocido se trata como UNKNOWN (los cinco del mandato) · M6 la guarda de retiro ignora el UNKNOWN · M7 la corrección permite una apertura imposible · M8 la corrección no marca KNOWN · M9 V3 tratada como V4.

## 6. Observaciones

- **O-28** (preexistente, abierta): `userBuPanel` de vitest falla de forma intermitente (un test distinto en cada corrida). Esta misión no toca frontend (`git diff 92fa7d3 fd52b90 -- frontend` vacío) y la misma falla ya estaba clasificada sobre la línea base 963f536. Ahora reaparece también aislada y con la máquina descargada: requiere su propia remediación. No se relajó ningún test.
- La E2E completa reescribe evidencia versionada de otras specs: restaurada con `git restore`, fuera de los commits.
- Desviación de rol: el ejecutor DeepSeek corrió todos los comandos (parches, suites, commit, mutación); el código, los parches literales, la E2E y este documento fueron redactados por Claude por el patrón conocido de agotamiento de turnos del ejecutor.
- `OPERATIONAL_MODEL_GAP` (sin evento operativo de fosa ni `oversized`) sigue abierto, fuera de alcance.

## 7. Decisión local

`BR03_UNKNOWN_SAFETY = CERTIFIED` · `OD-HATCH-V4-02 = CLOSED` · `HATCHERY_V4 = CERTIFIED` (local; la paridad de runtime se verifica tras el push) · `OWNER_ACCEPTED = NO`.
