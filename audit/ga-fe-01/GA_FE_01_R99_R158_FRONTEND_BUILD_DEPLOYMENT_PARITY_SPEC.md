# GA-FE-01 · FRONTEND BUILD & DEPLOYED RUNTIME PARITY RECOVERY — SPEC

`audit/ga-fe-01/` · **2026-09-10** · Rama `main` · Baseline `42108b0` · **REMEDIATION TRANCHE**

---

## 1. Problem statement

El frontend de `main` **no puede construir imagen** porque `npm run build` (= `tsc -b && vite build`)
falla en la etapa `tsc` con 6 errores (`R-158`). El `frontend/Dockerfile` usa exactamente
`RUN npm run build`; la consecuencia es que **ninguna entrega de frontend posterior al
2026-09-05 14:09:27 GMT ha llegado al `DEPLOYED_SHARED_RUNTIME`** (`R-99`): el artefacto servido
sigue siendo `assets/index-D5dwMXuP.js`, construido en `f46cb13`.

GA-FE-01 corrige **la causa** (errores TypeScript) en el árbol de código — **no** el pipeline,
que es correcto — y demuestra con evidencia desplegada que el runtime deja de servir la
generación congelada.

```
SOURCE FIX → TSC 0 → VITE OK → npm run build OK → VITEST OK → COMMIT → PUSH
  → AUTO-DEPLOY EXISTENTE → NEW RUNTIME FINGERPRINT → DEPLOYED PARITY PROOF
  → R-158 CLOSED → R-99 CLOSED
```

## 2. Hallazgos gobernantes

| ID | Título | Estado de entrada |
|---|---|---|
| `R-158` | `npx tsc -b --noEmit` falla con 6 errores (`TS6133`×5, `TS2493`×1) | OPEN (P2 histórico; impacto operativo P1) |
| `R-99` | El frontend del entorno compartido no sigue a `main` (artefacto congelado 2026-09-05) | OPEN (P1) |
| `R-98`/`R-119` | Frontend sin modelo de permisos | **FUERA DE ALCANCE** — no se tocan |
| `R-181` | Envío/reenvío a revisión sin control UI | **FUERA DE ALCANCE** — no se toca |

## 3. Cadena causal (demostrada, ver `GA_FE_01_HISTORICAL_REPLAY.md`)

```
1. f46cb13 (2026-09-05 16:08)  tsc GREEN (exit 0) · npm run build GREEN → dist/assets/index-D5dwMXuP.js
                               ← ese archivo, con ese nombre y 1 235 292 bytes, es EL SERVIDO por el runtime.
2. 4386f87 (2026-09-06 03:36)  retira las pestañas «por lote/usuario» de AuditPage.tsx (GA-REM-032 AC11)
                               y deja `User, Database` en el import → 2×TS6133 → tsc RED (exit 2)
3. 950bb21 (2026-09-07 13:06)  scaffold de áreas a medio cablear en LotFormPage.tsx → +4 errores → 6 (exit 2)
4. 15/15 commits de frontend posteriores: tsc RED (verificado en la auditoría)
5. Docker build (RUN npm run build) FALLA en tsc → no hay imagen nueva → Watchtower no recibe nada
   → el runtime sirve la generación 09-05 indefinidamente.
```

## 4. Contrato de build (no se toca)

| Artefacto | Contrato | Regla GA-FE-01 |
|---|---|---|
| `frontend/package.json` → `"build": "tsc -b && vite build"` | El gate oficial | **INTOCABLE** (prohibido quitar `tsc`, `\|\| true`, etc.) |
| `frontend/tsconfig*.json` | `noUnusedLocals: true`, strict | **INTOCABLE** (prohibido relajar) |
| `frontend/Dockerfile` → `RUN npm run build` | La cadena real de despliegue | **INTOCABLE** |
| `npx tsc -b --noEmit` | Typecheck de certificación | debe terminar **exit 0, 0 errores** |
| `npx vite build` | Empaquetado | debe seguir **exit 0** |
| `npm run build` | **Gate contractual** (lo usa Docker) | debe terminar **exit 0** |
| `npx vitest run` | Suite completa | **0 failed** (baseline 108/108) |

## 5. Contrato de despliegue (no se toca)

- `EX-01` (auto-deploy) permanece **riesgo aceptado e intacto**: el push a `main` es el
  mecanismo normal y **es el test** de que el pipeline funciona cuando el build deja de estar roto.
- Prohibido: tocar Watchtower · `latest` · Docker Compose · Nginx · DNS · CI/CD · triggers.
- El push de GA-FE-01 toca solo `frontend/**` (implementación) y `audit/**` (documentación):
  `docker-push-frontend.yml` se dispara con `frontend/**` — es el evento de despliegue intencional.

## 6. Contrato de fingerprint de runtime

- **ENTRADA** (capturado 2026-09-10T21:33:32Z): root 200 · `Last-Modified: Sat, 05 Sep 2026 14:09:27 GMT`
  · `ETag "6a9c2297-322"` · main JS `assets/index-D5dwMXuP.js` sha256 `4eb822a5…`.
- **SALIDA**: re-medición tras el despliegue. Criterios: asset principal **distinto**,
  `Last-Modified` **posterior**, old asset **deja de ser el primario** del HTML, marcadores
  actuales presentes, smoke público verde.
- El nombre del asset local **no** tiene que coincidir con el del runtime si el entorno de build
  difiere; la comparación usa hash + fecha + marcadores + salud.

## 7. Contrato de pruebas

- Los 6 errores se resuelven por cambios **import/dead-code only** → **sin cambio de comportamiento**
  → no se añaden tests nuevos (regla §34 del encargo: test nuevo solo si cambia comportamiento).
- Se ejecutan: gate TS, vite, npm build, Vitest completo, quality gates vigentes (`GA-REM-013`).
- Páginas afectadas: `AuditPage` (sin suite dedicada) · `LotFormPage` (sin suite dedicada) —
  la protección es el propio typecheck + Vitest completo + comportamiento idéntico.

## 8. Tratamiento semántico de cada error (detalle en `R158_TYPESCRIPT_ERROR_SEMANTIC_MATRIX.md`)

| # | Símbolo | Clase | Decisión |
|---|---|---|---|
| 1–2 | `User`, `Database` (import `AuditPage.tsx`) | `STALE_IMPORT_AFTER_INTENTIONAL_REMOVAL` | **Eliminar del import** — las pestañas se retiraron por `GA-REM-032 AC11` (gobernado); no se restauran |
| 3–4 | `areas`, `setAreas` (`LotFormPage.tsx:47`) | `INCOMPLETE_EXISTING_FEATURE` (wiring abandonado, sin AC para esta superficie) | **Eliminar el estado muerto** — nunca se leyó ni se asignó; la captura de área del alta de lote no está gobernada (el AC-A11 gobierna usuarios/maestros, ya implementado). El campo `area_id` del esquema se conserva (traza de intención) |
| 5–6 | `areaRes` (`LotFormPage.tsx:85`) | `INVALID_DESTRUCTURING` | **Destructuring a 4 elementos** — la quinta petición nunca se añadió; el valor no existe |

`OWNER_DECISION_REQUIRED`: **ninguno** — las tres resoluciones están respaldadas por gobernanza existente.

**Feature incompleta detectada y NO remediada aquí** (se registra como finding, §33 del encargo):
el alta de lote **captura `planned_close_date` y declara `area_id`, pero el payload no envía
ninguno**; `sla.py` selecciona lotes por `planned_close_date IS NOT NULL` → los lotes creados
por UI no alimentan jamás el aviso «lote próximo a cierre» ni el enrutado por área. Es una raíz
distinta de R-99/R-158 → se registra como candidato `R-182` en el cierre (sin corregir).

## 9. Alcance

**PERMITIDO (y único que se hará):** las 3 ediciones de los 6 errores · tests solo si el
comportamiento cambiara (no cambia) · evidencia · actualización de spec/backlog/R-99/R-158.

**PROHIBIDO:** fase 9 · BU admin UI · user-BU UI · multiempresa · navegación dinámica · R-181 ·
R-98/R-119 · R-140 UI · R-153 · R-177 · R-147 · R-148 · Wave B · Wave C · SAP · backend ·
migraciones · seeds · Dockerfile · CI/CD · Watchtower · Nginx · auto-deploy · debilitar
tsconfig/package/Dockerfile · `any`/`ts-ignore`/casts para silenciar.

## 10. Acceptance Criteria

### R-158 (build)

- **AC-R158-01** `npx tsc -b --noEmit` termina **exit 0** (0 errores; sin allowance de baseline).
- **AC-R158-02** `npm run build` termina **exit 0**.
- **AC-R158-03** `npx vite build` continúa **exit 0**.
- **AC-R158-04** ningún `tsconfig*.json` se relaja (diff vacío).
- **AC-R158-05** `package.json` conserva `tsc -b && vite build` (diff vacío).
- **AC-R158-06** `Dockerfile` conserva `RUN npm run build` (diff vacío).
- **AC-R158-07** los 6 errores se resuelven por los cambios semánticos declarados en §8.
- **AC-R158-08** ninguna feature existente se elimina: `AuditPage` conserva tabs/filtros vigentes (all/corrections + acción/módulo/fechas); `LotFormPage` conserva todos los campos y comportamiento actuales.
- **AC-R158-09** Vitest completo verde (0 failed).
- **AC-R158-10** no aparecen errores TypeScript nuevos ni regresiones de lint introducidas.

### R-99 (despliegue)

- **AC-R99-01** el frontend de `main` produce artefacto deployable (`npm run build` verde).
- **AC-R99-02** el push usa el mecanismo normal (`git push origin main`), sin tocar `origin`.
- **AC-R99-03** `EX-01` no se modifica.
- **AC-R99-04** Watchtower/Nginx/Docker deployment/CI sin cambios (diff vacío en esos paths).
- **AC-R99-05** el root HTML de `avicola.globaldv.net` deja de servir el asset stale (`index-D5dwMXuP.js` deja de ser el primario).
- **AC-R99-06** el fingerprint de salida es posterior a la entrada (`Last-Modified` > 2026-09-05 14:09:27 GMT).
- **AC-R99-07** los marcadores actuales seleccionados (`permissions-catalog`, `masters/areas`, `notifications/unread-count`, `weight-curves`, `import_plan`, `dead_on_arrival`, `chicks_healthy`) están presentes en el bundle desplegado.
- **AC-R99-08** el deployment nuevo carga sin errores estructurales de assets (JS/CSS 200).
- **AC-R99-09** el login público continúa cargando.
- **AC-R99-10** sin credenciales autorizadas, los flujos autenticados quedan `BLOCKED_AUTH` explícito, sin certificarse por inferencia.

### No regresión funcional

- **AC-NR-01** `AuditPage`: render y filtros vigentes intactos (tabs `all`/`corrections`, filtros acción/módulo/fecha, sin pestañas resucitadas).
- **AC-NR-02** `LotFormPage`: mismo conjunto de campos y mismo payload (8 claves); sin selectores nuevos; el scaffold de área no funcional desaparece sin cambiar comportamiento observable.

## 11. Reglas de cierre

- **R-158 = CLOSED (TECHNICAL BUILD BLOCKER)** solo con: 6→0 errores · tsc 0 · vite 0 · npm build 0 ·
  sin relajaciones · matriz semántica completa · Vitest verde · commit + evidencia.
- **R-99 = CLOSED (DEPLOYMENT PARITY RECOVERED)** solo con: build verde · push · remoto = commit ·
  runtime con generación nueva · stale no primario · marcadores presentes · smoke público verde ·
  caché de cliente descartada. Los flujos autenticados quedan `BLOCKED_AUTH` (no impiden el cierre
  de paridad; **no** se declaran las 13 capacidades `IMPLEMENTED_AND_VISIBLE`).
- Si el runtime no cambia tras el push: clasificar sin tocar deployment
  (`REMOTE_NOT_UPDATED`/`BUILD_NOT_TRIGGERED`/`BUILD_FAILED`/`IMAGE_NOT_PUBLISHED`/
  `IMAGE_PUBLISHED_RUNTIME_NOT_UPDATED`/`RUNTIME_UPDATED_BUT_BROWSER_CACHE_STALE`/`UNKNOWN_EXTERNAL`)
  y dejar R-99 en `PARTIAL/OPEN` si la causa queda fuera de R-158.

## 12. Rollback

Cambios import/dead-code only, sin migración ni estado. Rollback = revertir el commit de
implementación (`git revert`) — sin efectos de datos. No se prevé necesario.

## 13. Reglas git / evidencia

- **COMMIT 1** SPEC/preflight (este paquete) — **sin código de producto**.
- **COMMIT 2** implementación mínima + (tests solo si aplicara) — con todos los gates locales en verde.
- **COMMIT 3** evidencia/cierre + backlog + reconciliación — **prescindible para que el fix llegue**
  (el commit 2 ya lo lleva).
- Sin `git add` amplio · sin rebase/force-push · sin tocar `origin`.
- Sensibilidad/mutación: **N/A — BUILD/DELIVERY REMEDIATION** (el RED reproducible + la prueba
  causal histórica bastan; el mutation checkpoint guard permanece instalado, sin modificar).
