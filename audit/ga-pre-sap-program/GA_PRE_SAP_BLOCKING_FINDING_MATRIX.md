# GA · PRE-SAP — MATRIZ DE HALLAZGOS BLOQUEANTES (TRANCHE 0 · §12)

Universo: (A) las **34 brechas del programa** (`GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md`, correcciones D-01/D-02/D-03 aplicadas) y (B) los **71 hallazgos heredados** de `GA_CLAUDE_OPEN_FINDING_RECONCILIATION.md` (sin doble conteo). Severidades y veredictos son los de la auditoría; nada se reclasifica aquí sin decisión del propietario.

## A · Brechas del programa (34)

Leyenda superficies: FE=frontend · BE=backend · INT=integración FE-BE · SEC=seguridad · ING=integridad de datos · TX=transaccionalidad · GOV=gobernanza · SAP=evento/capacidad SAP.

### A.1 · P1 — bloqueantes de certificación (9)

| ID | Título | Dominio | Superficies | Procesos | Decisión propietario | Spec | ¿Bloquea? | Tranche |
|---|---|---|---|---|---|---|---|---|
| R-199 | Rol de inquilino fabrica autoridad global (`("*", all)`; switch-company) | Seguridad/plataforma | BE·SEC·FE(indirecto) | P-13 | OD-13.c | GA-PRE-SAP | **SÍ** | T2 |
| R-196 | Alta estructural de maestros `{}`→422 + React #31; 20/21 maestros solo-URL | Maestros/UI | FE·INT·(BE ok) | P-12 | — | GA-PRE-SAP | **SÍ** | T9 |
| R-195 | Edición de usuario envía `username`/`company_id`→422; `alert([object Object])` | Usuarios/UI | FE·INT·(BE ok) | P-13 | — | GA-PRE-SAP | **SÍ** | T9 |
| R-194 | Cadena de incubadora rota (5 causas: farm_id, huevos fértiles, arrival_date, dosage silent, hatchery_id) | Incubadora | FE·INT·(BE parcial) | P-04 | — | GA-PRE-SAP | **SÍ** | T6 |
| R-192 | Cierre de lote imposible tras reverso efectivo (`REVERSED` fuera de aprobados) | Integridad/cierre | BE·ING·TX | P-06/P-07 | OD-19 §1 | GA-PRE-SAP | **SÍ** | T7 |
| R-191 | Transición de fase envía `phase_code` vs `lot_id`+`phase_id` (422 consola) | Ciclo de fases | FE·INT·(BE ok) | P-11 | — | GA-PRE-SAP | **SÍ** | T5 |
| R-190 | BR-08 en lotes sin galpón (10 tipos de evento) — helper `resolverUbicacionDelEvento` | Eventos producción | FE·INT·(BE ok) | P-01/P-03 | — | GA-PRE-SAP | **SÍ** | T4 |
| R-205 | BR-20 inalcanzable por navegación natural (`?type=`→`stage=null`→400) | Recepción reproductoras | FE·INT·(BE ok) | P-03 (recepción) | — | GA-PRE-SAP | **SÍ** | T4 |
| GA-GOV-03 | 37 TEST_DEFECTs + CI solo-PR + certificaciones sin evidencia + aceptación sin evidencia primaria + backlog drift (R-189/GA-UAT-09 ausentes; OD-21…25 huérfanos) | Gobernanza/calidad | GOV·todas | Todos | OD-16 (contrato 403/404) · OD-23 | GA-GOV-03 (6 ficheros) | **SÍ** | T1 |

### A.2 · P2 — bloqueantes (15)

| ID | Título | Dominio | Superficies | Procesos | Decisión | Tranche |
|---|---|---|---|---|---|---|
| R-193 | BR-18 cuenta original+contrapartida tras reverso (2n) | Integridad recepción vs OC | BE·ING | P-01 | OD-19 §3 | T7 |
| R-197 | Centro de revisión: `status`/`operator_id` ignorados; `in_review` huérfano | Revisión | BE·FE | P-07 | — | T10 |
| R-198 | Evidencias descartadas por `pop()`; sin gate de estado; sin auditoría; borrado antes de commit | Evidencias | BE·ING·GOV | P-02 | AOD-14 (obligatoriedad) | T8 |
| R-200 | Refresh token aceptado como access (sin chequeo `type`) | Seguridad | BE·SEC | P-13 | — | T2 |
| R-201 | SAP `_company_filter` fail-open sin contexto; `retry_failed` cross-company | Seguridad/alcance | BE·SEC | P-08 | — | T3 |
| R-203 | Tenencia de `house_id`/`genetic_line_id`/`weight_curve_id` del lote sin verificar | Tenencia/maestros | BE·SEC·ING | P-12 | — | T3 |
| R-204 | KPIs de incubadora y `active_alerts` sin predicado de unidad (agregan de más) | Alcance/KPI | BE·SEC·ING | P-04/P-15 | — | T3 |
| R-207 | Reverso interno (OD-19) sin UI — capacidad backend-only | Capacidad/UI | FE (ausente) | P-07 | OD-19 §UI | T10 |
| R-208 | `batch-approve`/`batch-reject` exigen `review:review` vs `approvals:*` unitario | Permisos/seguridad | BE·SEC | P-07 | — | T2 |
| R-209 | `bird_exit`/`feed_registration` guardan id de `SapReference` en vez del código | Integración/contrato | BE·ING·SAP | P-01/P-09 | — | T5 |
| R-210 | Unidad kg/g en peso (step 0.001, fallbacks «(kg)»; sistema en gramos) | Contrato/UI | FE·INT·ING | P-02/P-09 | — | T5 |
| R-211 | BR-17 valida Σ contra galpón único mientras la UI distribuye por galpón | Integridad distribución | BE·ING | P-02/P-03 | — | T7 |
| R-215 | React #31 por detalle crudo fuera del asistente; sin `ErrorBoundary` | Estabilidad UI | FE·GOV | P-09/P-12 | — | T9 |
| R-221 | Eventos sin lote no derivan unidad; `hatchery_inspection` registrable con incubadora deshabilitada | Alcance/validación | BE·SEC·INT | P-12 | AOD-13 | T3 |
| P1-12-REOPEN | Auditoría duplicada ×2/×3 (listener+helpers); productores ausentes (cierre/activación/fases, usuarios, evidencias, curvas, exports); `corrected` espurio | Auditoría/ingeniería | BE·ING·GOV | P-09 | — | T8 |

### A.3 · P2 — no bloqueantes (7)

| ID | Título | Nota | Tranche/disposición |
|---|---|---|---|
| R-202 | Reset de contraseña solo `is_super_admin`, sin contexto de empresa | Compacto; candidato T2 (auth) | T2 (rider) |
| R-206 | Opcionales como cadena vacía (`''`)→400; números en `extra_data` como string | Compacto | T5 (rider) |
| R-214 | (backlog) | SOLO en backlog, sin paquete | Fase SAP / decisión |
| R-216 | `lots_by_type` con claves `BirdTypeEnum.*` → tarjetas a 0 | Compacto; fusionar con R-204 (mismo fichero) | T3 |
| R-217 | `SapManagerPage` con estados inexistentes, sin refetch/retry | Compacto; depende de fase SAP | Fase SAP |
| R-218 | Vista semanal/gráficos planos (listado sin sublistas) | Compacto | T11 |
| R-219 | `AuditPage` lee campos inexistentes (`user_name`/`old_value`/`new_value`) | Compacto; familia P1-12 | T8 (rider) |

### A.4 · P3 (3)

| ID | Título | Tranche |
|---|---|---|
| R-212 | UI sin conciencia de permisos (403 como vacío; home sin `dashboard:read`) — compacto | T11 |
| R-213 | `/me` 500 con emails rechazados por EmailStr (lectura estricta) — compacto; explica 5 rojos grupo B | T11 |
| R-220 | Residuales A-D (contratos/UX; móvil/responsive/nav; i18n; código muerto) — compacto itemizado | T11 |

### A.5 · Recuento A

P0=0 · **P1=9** · **P2 bloqueantes=15** · P2 no bloqueantes=7 · P3=3 · **Total=34** · Con paquete de spec: 32/34; sin paquete: R-214 (backlog) y R-217 (compacto SAP-fase, sí tiene) — precisión: solo R-214 sin carpeta.

## B · Hallazgos heredados (71 filas) — disposición en el programa

| Grupo (fuente §) | Ítems | Disposición en este programa | ¿Bloquea GO final? |
|---|---|---|---|
| Wave 2-3 §1 | R-63, R-64, R-65, R-66, R-69, R-70, R-77, R-80, R-83 | No bloquean individualmente; **R-83** agrava auditoría (nota en T8); R-70/R-69 relacionados con activación de lotes (decisión OD-10.c); resto: deuda operativa/datos | NO (R-83: nota) |
| Acceso 2026-09-08 §2 | R-112 (parcial: `/consolidated` sin `response_model`), R-122 (columna Empresa en usuarios — rider T9), R-123 (`scope_type` inerte — nota T2), R-124 (SAP), R-125 (decisión), R-127.b (deferido) | R-122 candidato rider de T9 (UsersPage); R-112/R-124/R-127.b → fase SAP; R-123 → nota de seguridad (no cambio sin decisión OD-13) | NO (excepto fase SAP) |
| Wave B pausada §3 | R-142 (**condicional/AOD-17**), R-144 (**condicional/AOD-08**), R-147, R-148, R-164 (**BLOCKED_RUNTIME/UNKNOWN**), R-153 (**UAT pendiente**), R-156, R-177, R-140 parcial (**condicional/AOD-18**), R-154, R-136 parcial (→R-207), GA-REM-021 parcial (B03/B04) | R-142/R-144/R-164/R-140/GA-REM-021: **lote de decisiones del propietario (§25)** antes del cierre; R-153 → plan UAT (T13); R-136 → T10 (cubierto por R-207+R-192); R-147/R-148/R-154/R-156/R-177 → aceptación o fase SAP | **SÍ condicional** hasta decisión IA-05/IA-06 (ver §25 del roadmap) |
| Ola C §4 | **R-131, R-132, R-133, R-134 (P1)**, R-141 | **SIN SPEC** (GA-REM-022 no redactada) → **GAP DE PROGRAMA**: requiere decisión AOD-10/AOD-10.e (¿corregir fórmulas o aceptar documentado?) y, si «corregir», redactar spec antes de T12 (P-15) | **SÍ** (P1 funcional en P-15; contamina IPE aceptado) |
| Ola D §5 | R-137, R-138, R-157, R-145, R-155, GA-REM-017/P-08 | Fase SAP (`SAP_DEFERRED`/`BLOCKED_EXTERNAL`): definición de eventos fuente y mapeo | Solo para `GO_SAP_INTEGRATION` (A) |
| Ola E §6 | R-146 (BE sí/FE no — rider captura móvil), R-150, R-151 | R-146 → rider de la tranche de captura (T5, AOD-16); R-150/R-151 → aceptación/T11 | **SÍ condicional** (R-146 integridad P2) |
| Gobernanza §7 | R-149, GA-REM-016 (SPEC_DRAFT), GA-REM-018, GA-REM-019, GA-REM-011 AC04/05/06/08 diferidos, GA-REM-005 AC08, GA-REM-009 AC04/07, GA-REM-010 AC07, GA-REM-013 AC02, **GA-REM-004 AC07 (BD superusuario pública) y AC03 (rate limit runtime)**, **GA-REM-003 AC04 (logout sin denylist — P1)**, GA-REM-003 AC06, **P1-5 observabilidad**, **P1-6 respaldos (release blocker)**, P1-12 (→P1-12-REOPEN), **P1-13 aprobación multinivel**, **P1-15 activación manual sin UI**, P1-16, P1-8 | GA-REM-003 AC04 → **rider T2**; GA-REM-004 AC03/AC07 + P1-6 + R-52/RES-05 → **Pista OPS**; P1-5 → spec-expansión o riesgo aceptado (decisión); P1-13 → decisión AOD-17 + posible spec (familia T10); P1-15 → rider T11 (UI de activación, OD-10.c); GA-REM-016/R-149 → T12 (certificación real) | **SÍ** los marcados en negrita (decisión/ops); resto NO |
| Residuales §8 | RES-02 (clasificación pendiente sin UI — OD-10.c), RES-04 (→T10), RES-05/R-52 (**PENDING_OPS: volumen `avicola-media`**), RES-07 (19 VNC), RES-10, N-1/N-3/N-4, OBS-UAT-06, procesos PARTIAL P-01/03/06/13/14 | RES-05/R-52 → **Pista OPS (bloquea integridad de evidencias)**; RES-07 → T12/T13 (certificación de las 19 filas; 8 requieren UAT); RES-02/P1-15 → T11 con decisión OD-10.c; N-* → T11/T12 | **SÍ condicional** (RES-05: evidencias efímeras) |
| §9 | **R-189** (no registrado en backlog; UAT-09 pendiente) + limpieza post-decisión | Registro en backlog → **T1 (GA-GOV-03, reconciliación de backlog)**; UAT-09 → T13; limpieza → post-UAT | **SÍ** (UAT + registro) |
| §11 CL | CL-01→R-190; CL-02→R-191; CL-03→R-192; CL-04→R-193; CL-05→R-194; CL-06→R-195; CL-07→R-196; CL-08→R-197; CL-09→R-198; CL-10→R-199/200/201/202/203/204/221; CL-11→P1-12; CL-12→R-207/140/RES-02/P1-15; CL-13→R-212; CL-14→R-205; CL-15→R-206; CL-16→GA-GOV-03; CL-17→R-208/197/204/216/219/P1-12 | **Cubiertos** por las 25 specs + riders | **SÍ** (vía sus specs) |

### B.1 · Recuento B

- Filas heredadas: **71** · bloquean o bloquean-condicionalmente según la reconciliación: 36 · no bloquean: 35.
- **Bloqueantes heredados SIN spec del programa** (gaps a resolver por decisión/spec nueva): **R-131…R-134 (P1, KPI/P-15)**, R-142/R-144/R-164/R-140 (condicionales por decisión), GA-REM-003 AC04 (rider T2, sin spec nueva — ingestable), P1-5 (observabilidad, decisión/spec), P1-6 + GA-REM-004 AC03/AC07 + RES-05/R-52 (pista OPS, no código), R-146 (rider T5), P1-13 (decisión/spec), P1-15/RES-02 (rider T11/decisión), R-189 (registro T1).

## C · Totales canónicos del programa (A+B, sin doble conteo de CL)

| Categoría | Nº |
|---|---|
| P0 | **0** |
| P1 de producto/gobernanza (A) | **9** |
| P2 bloqueantes (A) | **15** |
| P2 no bloqueantes (A) | 7 |
| P3 (A) | 3 |
| Heredados que bloquean o condicionan (B) | 36 filas (incluye solapes con A vía proceso; no se suman a A) |
| Bloqueantes sin spec redactada | R-131…134 (+ condicionales por decisión) |
| **Veredicto** | `NO_GO_SAP_FUNCTIONAL_GAPS` se mantiene: **24 brechas bloqueantes + gobernanza + 0/17 procesos certificados** |
