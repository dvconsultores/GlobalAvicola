# GA-CLAUDE · VALIDACIÓN INDEPENDIENTE DE LAS CONCLUSIONES DE DEEPSEEK (§3)

Auditoría independiente Claude · 2026-09-13 · HEAD `c0b4afc` (== `origin/main`) · runtime `avicola.globaldv.net` (`index-DDCcWL76.js`). Modo: cada conclusión del programa DeepSeek se trata como **claim a verificar** contra: spec canónica, decisión del propietario, código real, tests, artefactos de ejecución y runtime. Clasificación: `CONFIRMED` · `PARTIALLY_CONFIRMED` · `STALE` · `UNSUPPORTED` · `CONTRADICTED`.

Artefactos de la validación: `GA_CLAUDE_FINAL_AUDIT_CURRENT_STATE.md §5` (resumen), informes `A–F` (`evidence/`), suites ejecutadas por esta auditoría (`backend_full_suite.log`, `playwright_e2e.log`, `frontend_checks.log`), recorridos runtime/UI (`runtime-gp-e2e.json`, `ui-e2e-local-pass1/2.json`) y greps de verificación.

## 1 · Claims de producto/ingeniería

| # | Claim (DeepSeek) | Clase | Verificación (esta auditoría) |
|---|---|---|---|
| 1 | Los commits citados (38+21) existen y tocan lo declarado | `CONFIRMED` | `git log` de HEAD: cadena GA-FE-01…08, R-181…189, R-153, OD-16/OD-21…25 presente con contenido concordante (`08d0197`, `de40d36`, `005a252`, `511c419`, `5a5bb3f`, `5a32a6c`, `f755baa`, `bee33f5`, `4ba33f6`… `c0b4afc`) |
| 2 | GA-FE-01…08 y sus artefactos (RED/GREEN/runtime) están en HEAD | `CONFIRMED` | Código y suites presentes; vitest 314/314 en HEAD (`frontend_checks.log`) |
| 3 | R-181…R-188 implementados; R-153/OD-25 implementado; R-189/F-01 implementado | `CONFIRMED` (código) | `lots/service.py` (`crear_lote_de_importacion_si_procede`), `review/service.py` (hook), `operationPayload.ts`, `Toast.tsx`, `91bd27a`; suites dirigidas verdes |
| 4 | F-01: corridas A 29/29, B 35/35, 0 fatales, 0 `5xx` | `CONFIRMED` | `audit/ga-f01/GA_F01_RUNTIME_CERTIFICATION.md:15-16,51-75` + journals `evidence/runtime-c2d|c2f`; reproducido en su momento sobre la misma generación |
| 5 | Paridad bundle/backend repo↔runtime | `CONFIRMED` | `index-DDCcWL76.js` sha256 == build local de HEAD; marcadores C2d vivos (422 `[{}]`, lectura tolerante) |
| 6 | OD-16 implementada (fail-closed) y OD-23 implementada (B) | `CONFIRMED` | `9ffc5ec` (`unidades_de_alcance_productivo`), `067fba6`+`0542310`+`bee33f5` (`revoked_at`); tests canónicos nuevos; runtime OFF→404 |
| 7 | OD-21 (inactivo = inelegible en Área→Lote) implementado | `CONFIRMED` | `verificar_catalogo_de_empresa(exigir_activo=True)` en `lots/service.py:345-347,433-435` |
| 8 | OD-22/R-187 (IPE escala) implementado sin ×100 | `CONFIRMED` | `reports/service.py:668-670`; E2E-01…14 en `audit/ga-r187/`; **nota**: entradas aún viciadas por R-131/R-132 (ver claim 20) |
| 9 | R-184 y R-186 (fecha IPE/G-05) cerrados con fix `_dia()` | `CONFIRMED` | `3f88f94`, `0309225`; E2E 14/14 documentadas |
| 10 | R-161 (concurrencia huevos/incubación) y R-166 (decisión de revisión) cerrados | `CONFIRMED` | `validators.py:239-288` con `bloquear_saldo_del_lote`; `review/service.py:89-107`; tests `test_egg_incubation_concurrency`, `test_review_decision_concurrency` verdes |
| 11 | «Wave B PAUSED · Wave C/SAP NOT STARTED» | `CONFIRMED` | Backlog `:1547-1548`; grep de tranches; sin commits posteriores de Wave B/C |
| 12 | R-188 BU-D10 (apagar termina concesiones; re-encender no devuelve) | `CONFIRMED` (código) / `PARTIALLY_CONFIRMED` (cierre) | Código y tests correctos; **su suite certificada falla 5/10 en HEAD** (grupo B: fixture `.test` ⇒ `/me` 500) y «nunca ha pasado en ningún entorno» ⇒ el cierre documentado no está respaldado por una corrida verde (ver #16) |
| 13 | «R-189 cerrado técnicamente» (C3 `c0b4afc`) | `CONFIRMED` con salvedad | Certificación técnica completa; **UAT del propietario pendiente** (el propio commit lo declara) |
| 14 | Cierre frontend: 38/38 visibles + 7/7 internas + 15/15 auth-bloqueadas reconciliadas; 0 missing/stale/broken/unknown | `PARTIALLY_CONFIRMED` | Reconexión real: 38/38 reconciliadas pero **9 DEGRADADAS** y 5 reclasificadas (runtime de esta auditoría); 7 internas con FIA-01/02/05/07 degradadas; 15/15 sin bloqueo de autenticación (9 re-ejercitadas con sesión real) |

## 2 · Claims de certificación y gobernanza

| # | Claim | Clase | Verificación |
|---|---|---|---|
| 15 | 14 certificaciones de proceso `CERTIFIED` (P-01…P-15 menos P-08) | **`STALE`** | Sin artefacto de ejecución ni commit en 13 informes; **6 suites no reproducibles en HEAD** (P-03/P-04/P-05/P-10/P-11/P-15; `playwright_e2e.log:12 failed`); 72–91 commits de producto posteriores; contradicciones internas (P-03/P-06/P-10/P-14) |
| 16 | «La suite PG corre en CI» (R-188, `9ffc5ec`, etc.) | **`STALE`** | `backend-ci.yml` solo `pull_request`; 0 merges en 466 commits ⇒ **ninguna ejecución**; R-188 local «10 skipped» |
| 17 | «1139 passed · 49 skipped · 0 failed» (2026-09-10) | `STALE` | Hoy: **1201 · 25 failed · 49 skipped** (`backend_full_suite.log:624`) |
| 18 | GA-REM-003 `CERTIFIED` (incluye AC04 logout / AC06 auth) | `PARTIALLY_CONFIRMED` → riesgo abierto | `AC04` (logout/revocación) **no implementado** (sin `POST /logout`); `AC06` parcial (login sí, logout imposible); el reporte de certificación no cierra AC04 |
| 19 | GA-REM-013/014 `CERTIFIED` (quality gates, entorno) | `PARTIALLY_CONFIRMED` | Infraestructura existe; `AC05` (gate real de tests) nunca ejecutado; 5 errores ESLint diferidos |
| 20 | Las 9 aceptaciones del propietario (GA-UAT-01…08, GA-FE-08) | **`UNSUPPORTED`** (evidencia primaria) | Walkthroughs ejecutados por el agente (`walkthrough-uat.json`); capturas duplicadas md5 entre casos distintos (incl. un PNG compartido entre UAT-07 y UAT-08); limpieza de fixtures **antes** de la decisión en UAT-07/08 y FE-08; ventanas de 17–531 s; PASS por caso derivado de una «A» global en UAT-01/02/03. La aceptación es válida como **decisión registrada** (regla del programa) pero **no como evidencia de sesión del propietario** |
| 21 | P1-12 «auditoría duplicada» (abierto) | `CONFIRMED` reabierto con evidencia | Runtime local: `created ×2`, `review_started ×3`, `approved ×2`, 13 filas/6 acciones; `review/service.py:363` fila `corrected` espuria; tests ciegos (sin `lifespan`) ⇒ paquete `P1-12-REOPEN` |
| 22 | «R-83 implementado» (empresa nulable en audit) | **`CONTRADICTED`** | `audit/models.py:78` sigue `NOT NULL`; sin cambio; el claim del encargo se resuelve: **no implementado** |
| 23 | «R-146 implementado» (idempotencia) | `PARTIALLY_CONFIRMED` | Backend sí (`schemas.py:167`, `service.py:225`); **el cliente no envía la clave** (grep FE = solo sap.service) ⇒ vertical incompleta |
| 24 | R-140 «parcial» (guarda de estados) | `CONFIRMED` | Bloqueo de estados en `cancel_event` presente; sin motivo/rol (decisión AOD-18 pendiente) |
| 25 | R-148 inmutabilidad | `CONFIRMED` (abierto) | Sin trigger en `audit_logs`; solo aplicación |
| 26 | «P-05/P-10 certificados» (procesos) | **`CONTRADICTED`** | BR-21 (`c653ff8`) y BR-04 en cascada rompen la suite; defectos de UI propios (R-194) |
| 27 | «Reverso interno implementado» como flujo completo | **`CONTRADICTED`** | Backend completo; **0 llamadores FE** (R-207); efectos colaterales R-192/R-193 abiertos |
| 28 | «Visibilidad de control de la autoridad global sobre unidad apagada» (aserción de tests) vs OD-16 | **`CONTRADICTED`** | Producto fail-closed (404); los 17 tests del grupo A quedaron obsoletos (GA-GOV-03) |
| 29 | R-130 (población exacta) implementado y probado | `CONFIRMED` | `test_population_invariant`, bracketing runtime F-01 C3 (100 ok / 101 fail) |
| 30 | «SAP no iniciado / BLOCKED_EXTERNAL» | `CONFIRMED` | `GA-REM-017`; adaptador manual; sin credenciales; frontera interna auditada (R-201/R-217) |

## 3 · Claims documentales específicos del encargo (§44)

| ID citado | Verificación |
|---|---|
| GA-FE-01…08 | Existen y su código está en HEAD (claim 2); GA-FE-02-D reclasificó D-1 como SECURITY_DEFECT y lo corrigió (`9ffc5ec`) — documentado en `BASELINE` y no reabierto |
| R-181/R-182 | Código y suites presentes (submits/gates FE-05; área/cierre FE-06) |
| R-184/R-185/R-186/R-187/R-188 | Contratos y decisiones vigentes (claims 8/9/12); R-185 = OD-21; R-188 con salvedad de suite |
| R-153 | Implementado (claim 3); certificación técnica OK; **UAT pendiente** por F-01 (luego R-189) |
| F-01 canónico | `R-189` es el hallazgo canónico (alias de descubrimiento F-01); `audit/ga-f01/` contiene spec/dedup/certificación; **ausente del backlog** hasta el apéndice de esta auditoría |
| OD-21…OD-25 | Existen como decisiones (carpetas `audit/ga-*`); sin fichero en `specs/remediation/` ni fila en `INDEX.md` (deriva documental; GA-GOV-03 T-07) |
| «OD-24 resuelta sin código» | `AOD-06 → OD-24 (A)`: régimen provisional; sin código hoy (claim confirmado) |

## 4 · Síntesis cuantitativa

| Clase | Nº (claims 1–30 + específicos) |
|---|---|
| `CONFIRMED` | 15 |
| `CONFIRMED con salvedad` | 3 |
| `PARTIALLY_CONFIRMED` | 4 |
| `STALE` | 3 |
| `UNSUPPORTED` | 1 (aceptaciones del propietario, evidencia primaria) |
| `CONTRADICTED` | 3 (R-83; P-05/P-10 «certificados»; reverso «completo») + 1 aserción de tests (OD-16) |

**Lectura**: el producto de DeepSeek **existe y está en HEAD** para la mayoría de capacidades locales (claims 1–14), pero **la capa de certificación/gobernanza no resiste HEAD** (claims 15–21): sin ejecuciones reproducibles, con suites rojas, CI inoperante y aceptaciones sin evidencia primaria. Es exactamente el diagnóstico que motiva `GA-GOV-03` y el veredicto `NO_GO` (condiciones de §69: certificaciones, UAT y suite verde).
