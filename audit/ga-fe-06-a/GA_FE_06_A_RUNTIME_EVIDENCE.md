# GA-FE-06-A · EVIDENCIA RUNTIME (RED → GREEN)

Generaciones: entrada RED = backend `23ca59a` + bundle `index-DcqmSs-R.js`; GREEN = backend `69d0c95` (despliegue observado) + bundle **sin cambio** `index-DcqmSs-R.js` (LM 13:57:59 GMT · ETag `"6aa408e7-13cfbd"`).

Actor principal: **F** `ga6a.operador` (empresa 1 · rol 54 · BU `broiler` efectiva). Negativos: **G** `ga6a.sinventana` (rol con `lots:create`, sin concesión) · **H** `ga6a.rbac` (sin `lots:create`) · admin situado en empresa 1.

## 1 · Matriz RED (pre-fix)

| Caso | Resultado RED capturado |
|---|---|
| Alta con Área X (empresa 3) | **201** · lote 26 `GA6A-RED-FOREIGN-…` con `area_id: 5` persistido |
| Alta control con Área A (empresa 1) | 201 · lote 27 `GA6A-RED-BASE-…` |
| **Edición** a Área X sobre lote 27 | **200** · fresh GET `area_id: 5` |
| Edición control (restaurar Área A) | 200 |
| Área inexistente (999999) | **500** (FK sin contrato) |

Crudo: `evidence/red/runtime-red.json`.

## 2 · Matriz GREEN (post-fix `69d0c95`)

| Caso | Resultado GREEN |
|---|---|
| **Alta con Área X** | **→ 400 `{"detail":"Área no encontrado","rule":"BR-07"}`** · sin persistencia (`search` no encuentra el código) · auditoría: 0 éxitos ajenos |
| **Edición a Área X** (lote con Área A) | **→ 400 BR-07** · fresh GET conserva `area_id: 4` (sin mutación parcial) |
| Área inexistente | **→ 400 BR-07** (antes 500) — contrato canónico, no 500 |
| Control positivo misma-empresa | **201** · lote 32 · fresh GET `area_id: 4` · `planned_close_date` `2026-09-12T00:00:00Z` exacto (SLA fuente) |
| Control NULL | **201** · lote 33 · `area_id: null` |
| Edición propia (control) | **200** |
| Auditoría | creación positiva registrada (1); intento ajeno (0) |

Crudo: `evidence/green/runtime-green.json`.

### Corrección de arnés (honestidad)

La primera corrida del paso de negativos tuvo un **bug del script** (el helper `lot()` no propagaba el token del actor; los intentos G/H se ejecutaron como F y devolvieron 201). Los negativos se **re-ejecutaron con el token correcto de cada actor** y quedaron así — crudo en `evidence/green/negatives-corrected.json`:

| Negativo | Actor correcto | Resultado |
|---|---|---|
| Usuario con rol pero **sin ventana concedida** | G | **403** «sin acceso operativo a la unidad de negocio 'broiler'» |
| Usuario **sin RBAC** (`lots:create`) | H | **403** «Permiso requerido: lots:create» |
| **Global situado + ventana OFF** | admin (empresa 1) | **403** «sin empresa efectiva con unidades de negocio habilitadas» |
| F + **ventana OFF** | F | **403** íd. unidad |

Los dos lotes creados por F durante la corrida defectuosa (`GA6A-GREEN-NOBU-…`, `GA6A-GREEN-RBAC-…`) no representan al actor que dicen en el JSON original; quedan en el ledger como **artefactos del arnés**, y este documento consigna la verdad (OD-16 intacto: escrituras exigen ventana; el RBAC de permisos precede).

## 3 · Frontend (sin cambios de producto)

| Comprobación | Resultado |
|---|---|
| Selector desktop (F, `/lots/new`) | Opciones: `Seleccionar área…`, `Nave Norte (GA-FE-06)`, `Nave Sur (GA-FE-06)`, `Nave Operativa (GA-FE-06-A)` — **Área Ajena (empresa 3): AUSENTE** |
| Selector móvil 390×844 | Propia presente · Ajena ausente |
| Guard RBAC en UI (H) | «No tiene permiso para ver esta sección» (fail-closed; regresión GA-FE-04 viva) |
| Consola | 0 errores en las vistas de la corrida |
| Capturas | `evidence/green/ds-selector-desktop.png` · `mb-selector-mobile.png` · `ds-rbac-guard.png` |

**El filtrado de UI se conserva como comodidad de UX; la autoridad es el backend (verificado por API directa).**

## 4 · SLA — declaración explícita (§31)

- `planned_close_date`: **PASS** (fresh GET exacto en el alta positiva; la cadena UI→DB no se tocó en esta tranche).
- Regla (fuera/frontera/dentro/NULL): **PASS canónico** — `tests/test_lot_planned_close.py` determina estos casos; suite **no modificada** y sin cambios de lógica SLA (diffs = solo `lots/service.py`).
- **Scheduler runtime window: NOT_OBSERVED** — el aviso real depende del escáner horario interno; relecturas de notificaciones del actor en esta tranche → 0 (sin forzar el ciclo, sin reimplementar la regla). Mecanismo canónico suficiente para certificación: el evaluador (`evaluar_lotes_proximos_a_cierre`) es el mismo que cubre la suite y su fuente de datos quedó probada en runtime.

## 5 · Regresiones GA-FE

| Sujeto | Evidencia |
|---|---|
| GA-FE-02 (tenant/BU) | Negativos OD-16 arriba + gate PG-libre 7/7 + vitest de suites |
| GA-FE-03 (navegación) | Vitest completo 278/278 (incluye guards de rutas) |
| GA-FE-04 (autoridad de acción) | Guard RBAC vivo re-verificado (H, fail-closed) |
| GA-FE-05 (submit/resubmit) | Sin cambios de código; suites verdes; R-181 no tocado |
