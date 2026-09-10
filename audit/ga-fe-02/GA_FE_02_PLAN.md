# GA-FE-02 · PLAN (27 fases)

`[x]` al ejecutar/cerrar. Evidencia por fase en este paquete o en el commit correspondiente.

| # | Fase | Contenido | Estado |
|---|---|---|---|
| 1 | Repository/baseline | `main` · `cb14523` · remoto==local · limpio · GA-FE-01 verde (tsc 0 / build PASS / Vitest 108/108) | ✅ |
| 2 | Owner Decision | lectura del registro canónico → `NEXT_FREE = OD-20` → `OD-20` formalizada APPROVED + INDEX | ✅ |
| 3 | Backend contract map | `GA_FE_02_BACKEND_CONTRACT_MATRIX.md` (B01–B11 verificados contra código) | ✅ |
| 4 | Existing frontend map | `GA_FE_02_EXISTING_FRONTEND_MAP.md` (clasificado) | ✅ |
| 5 | Actor/permission matrix | `GA_FE_02_ACTOR_CAPABILITY_MATRIX.md` | ✅ |
| 6 | Company-context design contract | spec §6-S1/S2/S3a + AC-COMP; switch = contrato existente; fail-closed sin empresa | ✅ (diseño) |
| 7 | Company BU UI contract | spec §6-S3b + AC-CBU (4 tarjetas, estado backend, acciones por permiso) | ✅ (diseño) |
| 8 | User BU UI contract | spec §6-S3c/S4 + AC-UBU (separación empresa/usuario, candidatos, concesión/revocación) | ✅ (diseño) |
| 9 | Navigation/discoverability contract | spec §6-S5 + AC-NAV (1 entrada, guard por permiso, sin navegación global) | ✅ (diseño) |
| 10 | AC | spec §9 (AC-COMP/CBU/UBU/NAV/UI/DEP/NR) | ✅ |
| 11 | Tests/RED | `GA_FE_02_TEST_MATRIX.md`; RED construido y rojo ANTES de implementar — 58 rojos / 3 preexistentes | ✅ |
| 12 | Implementation | sesión extendida → servicio API → página admin → UsersPage panel → nav/guard → i18n (20 archivos) | ✅ |
| 13 | Targeted Vitest | suites GA-FE-02 verdes — 7 archivos · 90/90 | ✅ |
| 14 | TypeScript | `npx tsc -b --noEmit` → **exit 0** (sin baseline allowance) | ✅ |
| 15 | Build | `npm run build` verde (comando del Dockerfile) | ✅ |
| 16 | Frontend regression | Vitest completo → **198/198** (108 base + 90 nuevos), 0 failed, 0 skips nuevos | ✅ |
| 17 | Implementation commit | COMMIT 2 `48ffdbb` (tras todos los gates) | ✅ |
| 18 | Deploy normal | push `466f9d3..48ffdbb` → CI → Docker Hub → Watchtower (EX-01 intacto) | ✅ |
| 19 | Runtime fingerprint | `GA_FE_02_RUNTIME_EXIT_FINGERPRINT.md` (ENTRY vs EXIT) | ⏳ |
| 20 | Authenticated E2E | E2E-01…E2E-10 según credenciales disponibles; si no → `BLOCKED_AUTH` + `GA_FE_02_REQUIRED_TEST_ACCOUNTS.md` | ⏳ |
| 21 | Persistence/relogin | refresh + relogin del usuario objetivo (según contrato) | ⏳ |
| 22 | Negative controls | auto-concesión, empresa ajena, sin permiso, sin contexto (UI + API) | ⏳ |
| 23 | Responsive | escritorio 1440×900 + móvil 390×844 en las superficies nuevas | ⏳ |
| 24 | Evidence | `GA_FE_02_MULTI_COMPANY_BU_ADMIN_EVIDENCE.md` (§159) + screenshots index + network | ⏳ |
| 25 | Certification | reconciliación addendum (master audit + certificación) sin reescribir historia | ⏳ |
| 26 | UAT package | `GA_FE_02_OWNER_UAT.md` — `OWNER_ACCEPTANCE: PENDING` (no auto-declarar) | ⏳ |
| 27 | STOP | informe final §170; GA-FE-03 no iniciada | ⏳ |

## Orden de ejecución obligatorio (resumen operativo)

```
preflight ✅ → OD-20 ✅ → matrices ✅ → spec/AC ✅ → COMMIT 1 (gobernanza)
→ RED válido → implementación → gates → COMMIT 2 → push → runtime
→ E2E autenticado (o BLOCKED_AUTH documentado) → evidencia → COMMIT 3 → informe
```

## Notas de ejecución

- Cualquier necesidad de backend detectada durante la fase 12: **registrar, clasificar, no
  implementar** (la matriz declara TODO el contrato necesario READY; no se anticipa gap).
- La sensibilidad/mutación (§117) se decide en la fase 16-17: solo sobre código ya commiteado
  con checkpoint guard; si no es practicable en frontend → se documenta N/A con causa y se
  apoya en los controles negativos autenticados + guards backend certificados.
- Sensibilidad declarada para las hipótesis críticas de autorización del frontend
  (guard de ruta, gating de acciones, reset de contexto) — ver TEST_MATRIX.
