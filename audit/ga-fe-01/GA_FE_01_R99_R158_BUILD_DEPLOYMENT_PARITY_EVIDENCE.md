# GA-FE-01 · R-99 + R-158 — EVIDENCIA DE PARIDAD DE BUILD Y DESPLIEGUE

**Baseline del encargo**: `42108b0` · **Tranche**: GA-FE-01 · **Modalidad**: remediación de
entrega (sin rediseño) · **Fecha**: 2026-09-10.

> Las secciones 12–16/18–19 (observación de despliegue, fingerprint de egreso, smoke del
> runtime, BR-20/21/22 y reconciliación) se completan en este mismo documento al cerrar la
> observación. El marcador `⏳` indica medición pendiente en el momento de la redacción.

---

## 1 · ENTRY — verdad del repositorio y del runtime

```
REPO        HEAD 42108b0 · remoto == local · worktree limpio · origin HTTPS
            (delta post-42108b0 reconciliado: solo commits de auditoría, sin producto)
RUNTIME     root 200 · Last-Modified Sat, 05 Sep 2026 14:09:27 GMT · ETag "6a9c2297-322"
            main JS servido ......... assets/index-D5dwMXuP.js
            sha256 .................. 4eb822a57f9a04fd664ef48117968dd6e21df9613b6419146ffba417478c64be
            bytes ................... 1 235 292
            index.html sha256 ....... 61a41cb5ce8a8fd13a9e2fbdca08c61cbc5ec7c31aaceb6655a5e320cbdffb57
            origen stale vs caché ... ORIGEN (ETag/Last-Modified del servidor; sin SW)
```

Fuente: `GA_FE_01_RUNTIME_ENTRY_FINGERPRINT.md`.

## 2 · R-158 — bloqueo técnico de build (entrada)

```
tsc -b --noEmit .......... exit 2 · 6 diagnósticos (5×TS6133 + 1×TS2493 sobre 5 símbolos)
npm run build ............ exit 2 — muere en `tsc -b`; `vite build` nunca se alcanza
npx vite build (aislado) . exit 0
```

Los 6 diagnósticos y su tratamiento semántico: `R158_TYPESCRIPT_ERROR_SEMANTIC_MATRIX.md`.
Ninguno exigió decisión del propietario; ninguna corrección fue cosmética, supresión o
debilitamiento (`any`, casts, `ts-ignore`, renames falsos, options relajadas: 0).

## 3 · R-99 — generación servida (entrada)

La raíz sirve `index-D5dwMXuP.js` — artefacto congelado desde 2026-09-05 — con `Last-Modified`
de esa fecha y verificado byte a byte idéntico a la medición de la auditoría. `R-99` NO es caché
del cliente: el propio origen declara la antigüedad.

## 4 · Replay causal histórico

`GA_FE_01_HISTORICAL_REPLAY.md`. Cierre de cadena por ambos extremos:

| SHA | Fecha | `tsc -b --noEmit` | Errores | `npm run build` |
|---|---|---|---|---|
| `f46cb13` | 2026-09-05 | **exit 0** | 0 | **exit 0** → `dist/assets/index-D5dwMXuP.js` (1 235,29 kB) = **el asset servido** |
| `4386f87` | 2026-09-06 | exit 2 | 2 | FAIL (no alcanza vite) |
| `950bb21` | 2026-09-07 | exit 2 | 6 | (gate roto idéntico) |
| `42108b0` baseline | 2026-09-10 | exit 2 | 6 | FAIL (no alcanza vite) |

## 5 · Matriz semántica (documento dedicado)

`R158_TYPESCRIPT_ERROR_SEMANTIC_MATRIX.md` — 6 filas · clases: `STALE_IMPORT_AFTER_INTENTIONAL_REMOVAL`
(E1/E2, de `4386f87`, gobernado por `GA-REM-032 AC11`) · `INCOMPLETE_EXISTING_FEATURE`
(E3/E4, de `950bb21`; sin AC para la superficie de lote → finding `R-182`) ·
`INVALID_DESTRUCTURING` (E5/E6). `OWNER_DECISION_REQUIRED: 0`.

## 6 · Spec development compliance

- Spec: `GA_FE_01_R99_R158_FRONTEND_BUILD_DEPLOYMENT_PARITY_SPEC.md` (AC-R158-01…10 · AC-R99-01…10 · AC-NR-01/02).
- Clarify: `GA_FE_01_CLARIFICATIONS.md` (C-01…C-06).
- Plan/Checklist/Tasks: `GA_FE_01_PLAN.md` · `GA_FE_01_CHECKLIST.md` · `GA_FE_01_TASKS.md`.
- Artículos del encargo respetados: sin cambios de producto antes del RED válido; sin relajación
  de gates; sin retirar funcionalidad gobernada; sin tocar EX-01/Watchtower/Nginx/CI.

## 7 · RED válido antes del fix (reproducibilidad)

Medido sin tuberías (códigos de salida reales) en `frontend/` con cachés de tsc eliminadas:
`tsc` exit 2 / 6 errores · `npm run build` exit 2 · `vite build` exit 0.

## 8 · Implementación mínima (3 ediciones)

Diff completo (2 archivos · +2 −3), registrado en el commit `08d0197`:

| # | Archivo | Cambio | Clase |
|---|---|---|---|
| 1 | `frontend/src/pages/audit/AuditPage.tsx` | `import { Shield, User, Database, RotateCcw }` → `import { Shield, RotateCcw }` | retiro de imports muertos de una remoción **gobernada** |
| 2 | `frontend/src/pages/lots/LotFormPage.tsx` | elimina `const [areas, setAreas] = useState<SelectOption[]>([])` | retiro de estado muerto (jamás leído/llamado) |
| 3 | `frontend/src/pages/lots/LotFormPage.tsx` | destructuring `[farmRes, houseRes, lineRes, breedRes, areaRes]` → `[farmRes, houseRes, lineRes, breedRes]` | corrección de tuple (el 5.º elemento no existe: hay 4 peticiones) |

No se retiró ninguna feature gobernada: las pestañas `all`/`corrections` de Auditoría y todos los
controles del alta de lote permanecen; `area_id` del esquema zod se conserva como traza y el caso
se registra como `R-182` (sección 20).

## 9 · Pruebas dirigidas (regla «solo si el comportamiento cambia»)

No existen suites dedicadas a `AuditPage`/`LotFormPage` y los 3 cambios **no alteran comportamiento
observable** (dos símbolos jamás leídos + un retiro de imports sin uso). En consecuencia: no se
añaden tests nuevos y se ejecuta la suite completa como cinturón (sección 11). Justificación
registrada en `GA_FE_01_CLARIFICATIONS.md` (C-02/C-03) y `GA_FE_01_TASKS.md`.

## 10 · Gates de construcción (todos verdes)

| Gate | Comando | Resultado |
|---|---|---|
| TypeScript (limpio, sin caché) | `rm -f node_modules/.tmp/tsconfig.*.tsbuildinfo && npx tsc -b --noEmit` | **exit 0** · 6 → **0** errores |
| Vite | `npx vite build` | **exit 0** (987 módulos) |
| Build oficial (comando del Dockerfile) | `npm run build` | **exit 0** |
| Reduplicación en limpio | `rm -rf dist && npm run build` | **exit 0** · hash reproducible |
| Tests | `npx vitest run` | **exit 0** · 12 archivos · **108/108** |
| Sin relajaciones | `git diff` de tsconfig*/package*/Dockerfile | **0 líneas** |
| Diagnósticos del IDE | `get_errors` en los 2 archivos | 0 errores |
| Docker local | — | `DOCKER_BUILD_NOT_EXECUTED` (Docker no disponible en la estación); el gate equivalente (`npm run build`) pasó |

## 11 · Fingerprint del build LOCAL

```
LOCAL_BUILD_JS ............ assets/index-kzREeQp6.js  (1 275 424 bytes)
LOCAL_BUILD_JS_SHA256 ..... 4b6a6a044d6ccc850c017ba93868fd08b2cc2d859e666b2390204a66bb4038b9
LOCAL_BUILD_CSS ........... assets/index-CgiG0VY8.css (86 677 bytes)
LOCAL_INDEX_SHA256 ........ 909ea0733fb9b2b4c638b03f943573b0940b81818ded8ca63a5ea190dcef7bc4
Reproducibilidad .......... idéntico hash en builds consecutivos (vite build; npm run build)
```

Marcadores en el bundle local (post-fix): `permissions-catalog` ×1 · `masters/areas` ×1 ·
`notifications/unread-count` ×1 · `weight-curves` ×6 · `import_plan` ×13 · `dead_on_arrival` ×3 ·
`chicks_healthy` ×2 · `planned_close_date` ×3 · `switch-company` ×1 (control, presente también en
el bundle viejo).

## 12 · Checkpoint de implementación (commit C2)

```
COMMIT    08d0197 · "fix(r158): desbloquea la cadena de build del frontend …"
CONTENIDO estrictamente las 3 ediciones (2 archivos · +2 −3)
WORKTREE  limpio tras el commit
```

## 13 · Push y verdad remota

```
PUSH              GIT_TERMINAL_PROMPT=0 git push origin main → 397cc02..08d0197 · exit 0
REMOTE_IMPL_HEAD  08d01979e6bdf5d61b178faec3e8581e0c92db6a (08d0197)
ORIGIN            intacto (HTTPS; sin cambios de transporte ni de configuración)
DEPLOY_TRIGGER    push de C2 toca frontend/** → docker-push-frontend (EX-01) — NO intervenido
```

## 14 · Observación de despliegue

```
T+0    21:41:17Z  push C2 aceptado (397cc02..08d0197)
T+1m   21:42:08Z  root aún generación 09-05 (index-D5dwMXuP.js · LM 2026-09-05)
T+2m   21:42:39Z  idem
T+2.5m 21:43:35Z  CAMBIO DETECTADO: index-kzREeQp6.js · Last-Modified Thu, 10 Sep 2026 21:42:54 GMT
                  ETag "6aa3245e-322" · CSS index-CgiG0VY8.css
CLASIFICACIÓN    RUNTIME_UPDATED — cadena CI → Docker Hub → Watchtower completada sola
ACCIONES MANUALES  0 (ni docker pull, ni reinicios, ni tocar Watchtower/Nginx/CI/EX-01)
```

## 15 · Fingerprint de EGESO (ENTRY vs EXIT)

`GA_FE_01_RUNTIME_EXIT_FINGERPRINT.md`. Resumen:

| Señal | ENTRY | EXIT |
|---|---|---|
| Main JS | `index-D5dwMXuP.js` (sha256 `4eb822a5…`) | **`index-kzREeQp6.js` (sha256 `4b6a6a04…`)** |
| `Last-Modified` | 2026-09-05 14:09:27 GMT | **2026-09-10 21:42:54 GMT** |
| ETag | `"6a9c2297-322"` | `"6aa3245e-322"` |
| index.html | sha256 `61a41cb5…` | **sha256 `909ea073…`** |
| Asset viejo | primario | **404 (retirado)** |
| Paridad con local | — | **byte a byte (JS/CSS/HTML idénticos)** |
| Marcadores M1–M7 | 0/0/0/0/0/0/0 | **1/1/1/6/13/3/2 — todos presentes** |

## 16 · Smoke PÚBLICO del runtime

| Sonda | Código | Lectura |
|---|---|---|
| `/` | 200 | nueva generación |
| `/login` | 200 | SPA responde |
| `/assets/index-kzREeQp6.js` | 200 | bundle servido |
| `/assets/index-CgiG0VY8.css` | 200 | estilos servidos |
| `/assets/rolldown-runtime-QTnfLwEv.js` | 200 | chunk de runtime |
| `/api/v1/lots` | 401 | backend vivo y protegido |
| `/api/v1/operations/event-types` | 200 | backend público vivo |
| Navegador (contexto fresco) | — | login renderiza (Usuario/Contraseña/Iniciar Sesión/English); **sin error fatal** |

## 17 · BR-20 / BR-21 / BR-22 (paridad estática)

Los marcadores del contrato del frontend actual están PRESENTES en el bundle servido:
`dead_on_arrival` ×3 (BR-20) · `chicks_healthy` ×2 (BR-21) · `import_plan` ×13 (BR-22), además de
`planned_close_date` ×3. La paridad de despliegue que hoy faltaba queda restituida: el runtime ya
no es la generación que producía los 400 por campos ausentes en el cliente. La verificación
**funcional** autenticada (envío real de los formularios) queda `BLOCKED_AUTH` por falta de
credenciales autorizadas — NO se declara recuperación funcional.

## 18 · Runtime autenticado

`BLOCKED_AUTH` — no se dispone de credenciales autorizadas del entorno compartido; el encargo
prohíbe inventarlas. Todo lo observable sin sesión quedó medido (secciones 15–17).

## 19 · Reconciliación de certificación

Addendum fechado añadido a `audit/frontend-runtime/CERTIFICATION_SCOPE_RECONCILIATION.md` y al
backlog (`REMEDIATION_BACKLOG.md`): la frontera de las 13 capacidades `DEPLOYMENT_STALE` pasa a
«generación servida = árbol de código actual» (paridad de despliegue restituida). **Ninguna
capacidad se auto-reclasifica a IMPLEMENTED_AND_VISIBLE**: su visualización/funcionamiento
autenticado sigue pendiente de verificación con sesión. `R-98`/`R-119`/`R-181` sin cambio ·
fase 9 FROZEN · Ola B PAUSADA.

## 20 · Hallazgos

```
R-158   CLOSED (TECHNICAL BUILD BLOCKER) — 6 → 0 errores; tsc/vite/npm build exit 0;
        Vitest 108/108; build desplegado y verificado en runtime (secciones 10–15).
R-99    CLOSED — la generación servida ya no es el artefacto congelado del 09-05:
        asset/LM/ETag nuevos · paridad byte a byte con el build de `08d0197` ·
        marcadores presentes · smoke público OK · caché de cliente descartada
        (contexto fresco). Restricción declarada: verificación funcional autenticada
        queda BLOCKED_AUTH (sin credenciales) — la paridad de ENTREGA queda probada.
R-182   NUEVO (propuesto) · P2 · idem texto previo (alta de lote: `planned_close_date` capturado
        pero no enviado; `area_id` sin control; `sla.py` filtra por `planned_close_date IS NOT NULL`).
R-98 / R-119 / R-181   sin cambio (vigentes).
Fase 9 y Ola B         sin cambio (fase 9 FROZEN · Ola B PAUSADA).
```
````
This is the description of what the code block changes:
<changeDescription>
Replace the pending deployment/exit/smoke/auth/reconciliation/closing sections with the observed results.
</changeDescription>

This is the code block that represents the suggested code change:
````markdown
## 14 · Observación de despliegue

```
T+0    21:41:17Z  push C2 aceptado (397cc02..08d0197)
T+1m   21:42:08Z  root aún generación 09-05 (index-D5dwMXuP.js · LM 2026-09-05)
T+2m   21:42:39Z  idem
T+2.5m 21:43:35Z  CAMBIO DETECTADO: index-kzREeQp6.js · Last-Modified Thu, 10 Sep 2026 21:42:54 GMT
                  ETag "6aa3245e-322" · CSS index-CgiG0VY8.css
CLASIFICACIÓN    RUNTIME_UPDATED — cadena CI → Docker Hub → Watchtower completada sola
ACCIONES MANUALES  0 (ni docker pull, ni reinicios, ni tocar Watchtower/Nginx/CI/EX-01)
```

## 15 · Fingerprint de EGESO (ENTRY vs EXIT)

`GA_FE_01_RUNTIME_EXIT_FINGERPRINT.md`. Resumen:

| Señal | ENTRY | EXIT |
|---|---|---|
| Main JS | `index-D5dwMXuP.js` (sha256 `4eb822a5…`) | **`index-kzREeQp6.js` (sha256 `4b6a6a04…`)** |
| `Last-Modified` | 2026-09-05 14:09:27 GMT | **2026-09-10 21:42:54 GMT** |
| ETag | `"6a9c2297-322"` | `"6aa3245e-322"` |
| index.html | sha256 `61a41cb5…` | **sha256 `909ea073…`** |
| Asset viejo | primario | **404 (retirado)** |
| Paridad con local | — | **byte a byte (JS/CSS/HTML idénticos)** |
| Marcadores M1–M7 | 0/0/0/0/0/0/0 | **1/1/1/6/13/3/2 — todos presentes** |

## 16 · Smoke PÚBLICO del runtime

| Sonda | Código | Lectura |
|---|---|---|
| `/` | 200 | nueva generación |
| `/login` | 200 | SPA responde |
| `/assets/index-kzREeQp6.js` | 200 | bundle servido |
| `/assets/index-CgiG0VY8.css` | 200 | estilos servidos |
| `/assets/rolldown-runtime-QTnfLwEv.js` | 200 | chunk de runtime |
| `/api/v1/lots` | 401 | backend vivo y protegido |
| `/api/v1/operations/event-types` | 200 | backend público vivo |
| Navegador (contexto fresco) | — | login renderiza (Usuario/Contraseña/Iniciar Sesión/English); **sin error fatal** |

## 17 · BR-20 / BR-21 / BR-22 (paridad estática)

Los marcadores del contrato del frontend actual están PRESENTES en el bundle servido:
`dead_on_arrival` ×3 (BR-20) · `chicks_healthy` ×2 (BR-21) · `import_plan` ×13 (BR-22), además de
`planned_close_date` ×3. La paridad de despliegue que hoy faltaba queda restituida: el runtime ya
no es la generación que producía los 400 por campos ausentes en el cliente. La verificación
**funcional** autenticada (envío real de los formularios) queda `BLOCKED_AUTH` por falta de
credenciales autorizadas — NO se declara recuperación funcional.

## 18 · Runtime autenticado

`BLOCKED_AUTH` — no se dispone de credenciales autorizadas del entorno compartido; el encargo
prohíbe inventarlas. Todo lo observable sin sesión quedó medido (secciones 15–17).

## 19 · Reconciliación de certificación

Addendum fechado añadido a `audit/frontend-runtime/CERTIFICATION_SCOPE_RECONCILIATION.md` y al
backlog (`REMEDIATION_BACKLOG.md`): la frontera de las 13 capacidades `DEPLOYMENT_STALE` pasa a
«generación servida = árbol de código actual» (paridad de despliegue restituida). **Ninguna
capacidad se auto-reclasifica a IMPLEMENTED_AND_VISIBLE**: su visualización/funcionamiento
autenticado sigue pendiente de verificación con sesión. `R-98`/`R-119`/`R-181` sin cambio ·
fase 9 FROZEN · Ola B PAUSADA.

## 20 · Hallazgos

```
R-158   CLOSED (TECHNICAL BUILD BLOCKER) — 6 → 0 errores; tsc/vite/npm build exit 0;
        Vitest 108/108; build desplegado y verificado en runtime (secciones 10–15).
R-99    CLOSED — la generación servida ya no es el artefacto congelado del 09-05:
        asset/LM/ETag nuevos · paridad byte a byte con el build de `08d0197` ·
        marcadores presentes · smoke público OK · caché de cliente descartada
        (contexto fresco). Restricción declarada: verificación funcional autenticada
        queda BLOCKED_AUTH (sin credenciales) — la paridad de ENTREGA queda probada.
R-182   NUEVO (propuesto) · P2 · idem texto previo (alta de lote: `planned_close_date` capturado
        pero no enviado; `area_id` sin control; `sla.py` filtra por `planned_close_date IS NOT NULL`).
R-98 / R-119 / R-181   sin cambio (vigentes).
Fase 9 y Ola B         sin cambio (fase 9 FROZEN · Ola B PAUSADA).
```
````
<userPrompt>
Provide the fully rewritten file, incorporating the suggested code change. You must produce the complete file.
</userPrompt>
