# GA-FE-02-E · FINAL POST-SECURITY-FIX · FULL AUTHENTICATED RECERTIFICATION

**Baseline de entrada**: `ccb47b5` (main == remoto; worktree limpio) · **Fecha**: 2026-09-11 ·
**Generación congelada** (§4): frontend `assets/index-B2-tZnkI.js` · backend desplegado con el
fix `9ffc5ec` (GA-FE-02-D / OD-16) · **Runtime**: `https://avicola.globaldv.net` (health 200).
**Método**: rerun TOTAL desde cero — sin transitividad, sin reutilizar PASS previos. Cero
desarrollo nuevo; el único cambio posterior a este baseline son documentos.

---

## 1 · Preflight

```
main · HEAD ccb47b5 == remoto · worktree limpio
Runtime 200 OK · bundle index-B2-tZnkI.js · /health 200
TSC ......... 0 errores           PASS
npm build ... ✓ built             PASS
Vitest ...... 205/205 (21 files)  PASS
Backend dirigido (migración+OD-16 ruteo) ... 7/7 + 2 PG (CI)   PASS
compileall .. OK                  PASS
```

## 2 · Remediaciones cerradas re-verificadas (sin reabrir — verdes)

| Remedio | Verificación runtime | Estado |
|---|---|---|
| **F1** catálogo 4 BUs | `GET /business-units` c1 = `breeder·broiler·grandparent·hatchery`; c3 = 4 | **PASS** |
| **F2** rol canónico | `GET /roles`: rol 35 activo con exactamente `business_units:read|update|create|delete`; sin comodín | **PASS** |
| **F3** `/users` sin 500 | `GET /users?limit=100` → 200 (n=28+) | **PASS** |
| **F4 + D1** selector/sesión | UI: selector visible sin contexto; switch; **hard refresh** → contexto persiste, `/me` hidratado, sin forbidden | **PASS** |
| **D-1** OD-16 | global OFF read → **0 filas/404** · global OFF write → **403** (detalle §13) | **PASS** |

## 3 · Fixtures (sintéticos, solo mecanismos oficiales; sin credenciales en repo)

| Actor | username | id | rol | empresa | login | /me | final |
|---|---|---|---|---|---|---|---|
| A · Company-BU Admin | `ga-fe02e-a` | 77 | temp 36 (read/update + dashboard:read) | 1 | 200 | 200 | dado de baja |
| B · Access Admin | `ga-fe02e-b` | 78 | canónico 35 | 1 | 200 | 200 | dado de baja |
| C · Operational Target | `ga-fe02e-c` | 79 | temp 37 (`lots:read`) | 1 | 200 | 200 | dado de baja |
| D · Unauthorized | `ga-fe02e-d` | 80 | temp 38 (`dashboard:read`) | 1 | 200 | 200 | dado de baja |
| X · Foreign fixture | `ga-fe02e-x` | 81 | temp 38 | 3 | 200 | 200 | dado de baja |
| E · Global | bootstrap | 1 | Super Admin | — | 200 | 200 | intacto |

Roles temporales 36/37/38 reactivados (`PUT`, oficial) y **desactivados al cierre**; rol 35
intacto y activo. Credenciales efímeras solo en `/tmp` (600), destruidas al cierre.

## 4 · Generación congelada

Capturada al inicio: bundle `index-B2-tZnkI.js` + backend con `9ffc5ec` (el comportamiento
OD-16 solo existe post-fix). **Sin cambios de producto durante la corrida** (los commits de
esta tranche son solo `audit/**`). Sin movimiento de generación ⇒ sin reinicio.

## 5–9 · E2E completo (desde cero) + matriz 3D

**Desktop (Playwright local 1440×900): 46/46 PASS** — secuencia completa:

| Escenario | Resultado | Evidencia |
|---|---|---|
| E2E-01 selector/dropdown/switch c1 + **hard refresh (D1/F4)** | PASS | `E2E01_selector/switched/refresh.png` |
| E2E-01b switch c1→c3→c1 | PASS | `E2E01b_back.png` |
| E2E-02 navegación descubrible (Configuración→Acceso por unidad) + 4 unidades (Progenitoras·Reproductoras·Incubadora·Engorde) todas «Inactiva» | PASS | `E2E02_four_units.png` |
| E2E-02 **habilitar Engorde por UI** (diálogo) → Activa; otras 3 intactas; refresh persiste; backend fresh `broiler=true`; **0 concesiones automáticas** | PASS | `E2E02_enable_dialog/enabled.png` |
| E2E-04 **conceder C por UI**; distinción empresa Activa / usuario «No concedida»; backend viva+efectiva | PASS | `E2E04_before/after_grant.png` |
| E2E-04 **target**: C relogin → `/me` `["broiler"]` → **ALLOW 2** (`L-BO-2026-05/06`) — IMMEDIATE | PASS | red/persistencia |
| E2E-03 **desactivar por UI** → Inactiva; refresh persiste; **C DENY (0)**; concesión almacenada viva `is_effective=false` (BU-D10 obs.); **GLOBAL read DENY + write DENY** | PASS | `E2E03_disabled.png` |
| E2E-10 UI: unidad inactiva → aviso, sin implicar acceso | PASS | `E2E10_unit_inactive_notice.png` |
| AC-A06 rehabilitar → concesión vuelve → C **ALLOW 2** | PASS | — |
| E2E-05 **revocar por UI** → C relogin **DENY (0)** | PASS | `E2E05_revoked.png` |
| E2E-06 auto-concesión: **excluido de candidatos** + API **403** `OD-15.a` + sin persistencia | PASS | `E2E06_candidates_self_excluded.png` |
| E2E-07 cross-company: candidatos sin X (n=26) + `POST` **404** + sin persistencia | PASS | red |
| E2E-08 D: ruta protegida (alerta) + API **403×4** + sin persistencia | PASS | `E2E08_forbidden.png` |
| **3D**: OFF/YES/YES→**DENY** · ON/NO/YES→**DENY** · ON/YES/NO→**403 DENY** · ON/YES/YES→**ALLOW 2** | **4/4** | red |

**Móvil (390×844, isMobile+hasTouch): 10/10 PASS** — 4 unidades visibles, **sin overflow
(delta=0)**, toggles por UI, revocación por UI, persistencia tras refresh, C DENY y `/me`
vacía tras la revocación; capturas `MOBILE_*`.

## 10 · Refresh / Relogin (sin evidencia solo-React)

Company switch refresh ✓ · BU enable refresh ✓ · BU disable refresh ✓ · **grant refresh** (UI
tras MX-4) ✓ · **revoke refresh** (UI tras revocación móvil) ✓ · **C relogin tras grant** →
ALLOW (**IMMEDIATE**) ✓ · **C relogin tras revoke** → DENY (**IMMEDIATE**) ✓.

## 11 · Desktop / Móvil

Desktop 1440×900: flujos completos (selector, 4 BUs, enable/disable, panel de concesiones,
grant/revoke, denegaciones). Móvil 390×844: los mismos flujos operables — sin botones
inaccesibles, sin overflow, sin modal bloqueado.

## 12 · Network / Persistencia / Auditoría

- **Red** (captura automática por contexto): mutaciones 1× por acción — A: PATCH enable×3 /
  disable×3; B: POST grant C (UI) + DELETE revoke C (UI) + POST/DELETE D (MX-3) + POST grant C
  (MX-4 API) + DELETE revoke C (móvil); E: logins/switches. Sin duplicados por clic.
- **Persistencia**: cada mutación con fresh GET + refresh + estado final UI coincidente.
- **Auditoría**: filas **1:1 con las operaciones** — A(77) `config_change`×5 = sus 5
  flujos UI (enable/disable/enable desktop + disable/enable móvil); B(78)
  `permission_change`×6 = **6 operaciones reales** (C grant e10, C revoke e10, D grant e11,
  D revoke e11, C grant e12 MX-4, C revoke e12 móvil); batería (actor global, user_id=1)
  `config_change`×3 (disable OFF 02:51:46 · enable ON 02:51:49 · disable restore
  02:51:50) — 1:1 en los tres actores, con `business_unit`/`target_user_id`/`is_enabled`
  en `new_values` y timestamp; **denegadas sin fila de éxito**: auto-concesión → 0,
  cross-company → 0. Muestra en `/tmp/ga_e_audit_sample.json` (efímero).

## 13 · Regresión OD-16 (familia D-1) — OFF vs ON

**OFF (todas apagadas)** — familia completa: `/lots` **0** · `/lots/1` **404** · `/lots/1/phases`
**404** · `/operations` **0** · `/operations/37` **404** · `/review/pending` **0** ·
`/dashboard/admin` **0** · `/reports/kpis/mortality?lot_id=1` **404**; **plano de control
intacto** (BU=4 · users 200 · roles 200). **ON (solo broiler)**: `/lots` = solo
`L-BO-2026-05/06` · `/operations` 7 · `/dashboard/admin` 7 · review 0 · lote fuera de alcance
**404**. **GLOBAL OFF read DENY + OFF write DENY (403)** explícitos. Todo PASS.

## 14 · BU-D10

`PENDING_RATIFICATION` — observado: con CBU OFF y concesión viva, la fila se conserva con
`is_effective=false` y rehabilitar la devuelve (`AC-A06`). `OWNER_RATIFIED_POLICY: NONE`.
Sin cambio de spec por observación.

## 16 · Restauración

CBU 4×OFF · sin concesiones vivas (C/D/B/X=0) · usuarios 77–81 dados de baja (login posterior
**403**) · roles 36/37/38 desactivados · **rol 35 intacto** (activos=14 canónicos) · auditoría
conservada (append-only) · usuarios humanos sin tocar · residuo inseguro: NO · secretos
persistidos: NO.

## 17 · Gates finales

```
TSC 0 · build PASS · Vitest 205/205 · backend dirigido 7/7 (+2 PG CI)
D-1 regression PASS (familia completa) · E2E-01…10 PASS · 3D 4/4 PASS
global OFF read DENY · global OFF write DENY · refresh PASS · relogin PASS
desktop PASS · mobile PASS · persistence PASS · audit PASS · security PASS
runtime stable: index-B2-tZnkI.js idéntico inicio→fin · health 200
```

## 18 · Certificación

```
GA-FE-02-A: PASS_FINAL_GENERATION
GA-FE-02:   FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING
OWNER_UAT_READY: YES · OWNER_ACCEPTANCE: PENDING (solo el propietario)
GA-FE-03: ELIGIBLE_BUT_NOT_STARTED — NO INICIADA
```

## 19 · Límites del programa (intactos)

`R-98/R-119/R-181/R-182` UNCHANGED · `BU-D10` PENDING_RATIFICATION · Wave B PAUSED ·
Wave C NOT STARTED · SAP NOT STARTED.

## 20 · Evidencia y Git

- Capturas: `audit/ga-fe-02-e/evidence/` (20 PNG: desktop + móvil).
- Reportes de corrida (JSON, efímeros): ruteo/red/consola en los tres runners (fixtures, UI
  desktop, UI móvil, batería) — resumidos en este documento; temporales destruidos al cierre.
- Ledger de mutaciones: entrada #12 (fixtures + corrida + restauración).
- Commit de evidencia + push; `local == remote`; worktree limpio; `0 passwords · 0 tokens ·
  0 cookies · 0 storageState` en el diff.
