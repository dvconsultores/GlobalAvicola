# GA-FE-02-A · CHECKLIST (§23)

`[x]` hecho · `[ ]` pendiente · `[n/a]` no aplicable en `MODE_C` · marcado al ejecutar.

## Precondiciones

- [x] repo baseline válido (`main` · `d120fdd` · remoto==local · limpio)
- [x] runtime current (GA-FE-02: `index-C_aR7TJ6.js` · hash `35ea38e2…` · LM 23:39:07 GMT)
- [x] `OD-20` leída (autoriza fase 9 + GA-FE-02 + E2E; no requiere OD nueva)
- [x] GA-FE-02 spec leída
- [x] GA-FE-02 evidencia leída (exit fingerprint byte a byte)
- [x] contratos backend sin cambios (diff 0; matriz B01–B11 vigente)
- [x] frontend build green (`tsc` 0 · `npm run build` exit 0)
- [x] 198/198 Vitest green

## Credenciales y actores

- [x] credenciales autorizadas: **NINGUNA** (determinación acotada; sin búsqueda)
- [x] actor A (Company-BU Admin): `MISSING`
- [x] actor B (Access Admin): `MISSING`
- [x] actor C (Target User): `MISSING`
- [x] actor D (Unauthorized Control): `MISSING`
- [x] actor global: clasificado `OPTIONAL_MISSING` (no bloquea por sí — §15/§46)

## Fixture

- [ ] empresa de prueba elegida — `BLOCKED_AUTH` (requiere actor bootstrap)
- [ ] estado inicial de Company BU capturado — `BLOCKED_AUTH`
- [ ] concesiones iniciales capturadas — `BLOCKED_AUTH`
- [ ] RBAC inicial capturado — `BLOCKED_AUTH`
- [x] snapshot pre-test: registrado como «no capturado — sin sesión» (`GA_FE_02_A_PRETEST_STATE.md`)
- [x] datos de prueba aislados: **no se creó ningún dato**

## E2E planificado (planos y bloqueados por igual)

- [ ] E2E-01 Company context/switch — `BLOCKED_AUTH`
- [ ] E2E-02 Enable Company BU — `BLOCKED_AUTH`
- [ ] E2E-03 Disable Company BU — `BLOCKED_AUTH`
- [ ] E2E-04 Grant User BU — `BLOCKED_AUTH`
- [ ] E2E-05 Revoke User BU — `BLOCKED_AUTH`
- [ ] E2E-06 Self-grant — `BLOCKED_AUTH`
- [ ] E2E-07 Cross-company user — `BLOCKED_AUTH`
- [ ] E2E-08 Unauthorized actor — `BLOCKED_AUTH`
- [ ] E2E-09 BU ON + no user grant — `BLOCKED_AUTH`
- [ ] E2E-10 Stored grant + BU OFF — `BLOCKED_AUTH`
- [ ] refresh (5 puntos) — `BLOCKED_AUTH`
- [ ] relogin (objetivo ×2) — `BLOCKED_AUTH`
- [ ] mobile — `BLOCKED_AUTH`
- [ ] network evidence — `BLOCKED_AUTH`
- [ ] audit evidence — `BLOCKED_AUTH`
- [x] cleanup/restore planificado (ledger vacío; nada que restaurar)
- [x] protocolo de fallo planificado (taxonomía §67 + SECURITY STOP §68 + rama de remediación §70)

## Frontera del programa

- [x] GA-FE-03 excluida · [x] R-181 excluida · [x] R-182 excluida · [x] BU-D10 sin resolver

## Cierre

- [x] `GA_FE_02_REQUIRED_TEST_ACCOUNTS.md` actualizado (matriz fina §79)
- [x] evidencia §117 producida (con secciones `BLOCKED_AUTH`)
- [x] commit de gobernanza + push + verificación remota
- [x] sin cambios de producto · worktree limpio tras el commit
