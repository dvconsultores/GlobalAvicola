# RECONCILIACIÓN MAESTRA DEL ESTADO DEL PROGRAMA — AUDITORÍA 360°

**2026-09-09** · base `7310adb` (`main`, árbol limpio, remoto = local) · Alembic `s9t0u1v2w3x4` ·
**MODO AUDIT ONLY**: no se implementó, remedió, refactorizó ni cambió modelo, migración, spec,
AC, test, frontend ni SAP; no se arregló `R-127`; no se inició la fase 9.

Documentos de esta auditoría (todos en `audit/remediation/`):
`DOCUMENT_AUTHORITY_AND_SUPERSESSION_MATRIX` · `SYSTEM_OF_RECORD_AND_AUTHORITY_MATRIX` ·
`SAP_DEFERRED_LOCAL_PLACEHOLDERS` · `OPERATIONAL_PROCESS_STATE_AND_CLOSURE_MATRIX` ·
`KPI_FORMULA_AND_DATA_SOURCE_MATRIX` · `SAP_INTEGRATION_READINESS_AUDIT` ·
`GLOBAL_AVICOLA_REQUIREMENT_COMPLETENESS_360` · `BUSINESS_PROCESS_CERTIFICATION_MATRIX_360` ·
`AUDIT_OWNER_DECISIONS_REQUIRED` · este.

```
VEREDICTO 360
  principio «no es un ERP paralelo» .... RESPETADO en finanzas/inventario · INCUMPLIDO en identidad de maestros hacia SAP
  P0 nuevos ............................ 0
  P1 nuevos ............................ 11  (P01 población · K01 K02 K03 K06 fórmulas · P03 estados · P05 reverso · S08 S09 payload/entrante · B05 agua · F01 UI)
  P0/P1 previos abiertos ............... R-127 (P1) · R-99 (P1, BLOCKED_BY_OUT_OF_SCOPE_DEPLOYMENT) · R-119/R-98 (P1) · R-124 · R-125
  decisiones del propietario ........... 16 (AOD-01…16) + BU-D10 intacta
  R-127 ................................ MODEL DEFECT · BLOCKER PHASE 9 (no BLOCKER NOW: latente)
  FASE 9 ............................... BLOCKED
  certificaciones P-xx ................. 14 CERTIFIED registradas, 15/15 con evidencia envejecida (≤ 2026-09-06, 85 commits)
```

---

## 1. Estado verificado hoy

| Elemento | Medido |
|---|---|
| Rutas API | 208 (`enumerar_rutas`); 198 con permiso declarado; 10 exentas con justificación escrita (`authorization_coverage.py:21-58`); 208/208 con alcance de unidad declarado (`route_scope`) |
| Tablas | 54 (`Base.metadata`); 44 con `company_id` o pertenencia derivada (`TENANT_RESOURCE_CLASSIFICATION.md`, 0 sin clasificar) |
| Estados / tipos | `EventStatus` 13 (`DRAFT`, `SENT_TO_SAP`, `SAP_CONFIRMED`, `SAP_ERROR` sin productor) · `EventType` 26 · `LotStatus` 3 (`cancelled` sin productor) |
| Backend | `784 passed · 49 skipped · 0 failed` (487 s, `run_tests.sh -rs`); los 49 saltados son `test_upgrade_path.py` (35) y `test_runtime_startup.py` (14), que exigen `upgrade_test.sh` / `runtime_test.sh` |
| Frontend | `87 passed / 8 archivos` (vitest) · paridad i18n 988/988 |
| E2E | 17 suites en `e2e/`; **no ejecutadas hoy**; última ejecución registrada 2026-09-06 |
| Entorno | `ENV-01` compartido; BD y SSH inalcanzables desde esta estación (verificado en tranche 5); **ningún dato de runtime en esta auditoría** |

## 2. Reconciliación de las 40 `GA-REM` (sustituye la lectura de `INDEX.md` hasta su corrección)

| Estado reconciliado | Specs | Fuente del estado |
|---|---|---|
| `CERTIFIED` (31) | 001 002(+B) 003 004 005 006 007 008 009 010 012 013 014 015 020 023 024 025 026 028 029 030 031 032 033 034 035 036 037 038 039 | informes `*-CERTIFICATION-REPORT.md`, `MASTER_REMEDIATION_MATRIX §4-§12`, `USER_TENANT_ISOLATION_P0_EVIDENCE` |
| `PARTIALLY CERTIFIED` (2) | 011 (contratos FE↔BE) · 027 (proxy, `AC08` manual) | informes |
| `PARTIAL` (1) | 022 — enmienda A certificada (`P-15`); alcance base (completitud KPI) abierto y **ampliado por esta auditoría** (`K01…K13`) | `MASTER_REMEDIATION_MATRIX §7` + `KPI_FORMULA_AND_DATA_SOURCE_MATRIX` |
| `SPEC_READY` (2) | 021 (agua y datos del cliente) · 018 (trazabilidad Spec Development) | `INDEX.md` (coincide) |
| `SPEC_DRAFT` en uso (1) | 016 — marco de certificación de procesos, citado por 15 informes | `H360-D05` |
| `BLOCKED_EXTERNAL` (1) | 017 — SAP real (`P-08`) | — |
| `DEFERRED` (1) | 019 | — |
| `IN_PROGRESS` · `BLOCKED` (1) | 040 — fases 1-8 cerradas; fase 9 bloqueada por `R-127`; fases 10-11 pendientes | `PHASE_9_DEPENDENCY_PREFLIGHT.md` |

Discrepancias de `INDEX.md` corregidas por esta lectura: 004, 009, 010, 011, 013, 020, 022, 002,
024, 040 (detalle en `DOCUMENT_AUTHORITY_AND_SUPERSESSION_MATRIX §2`). **Corregir `INDEX.md` es
WAVE A documental** (`H360-D01/D05`); no se hizo aquí porque `specs/` está bajo prohibición.

## 3. Hallazgos previos abiertos (backlog) — sin cambio de estado

`R-77` (BR-10/BR-11 numeración) · `R-80` (fecha local vs UTC) · `R-83` (`AuditLog.company_id` no
nulable) · `R-98` / `R-119` (permisos en UI) · `R-99` (frontend congelado en `ENV-01`,
**no tocar**) · `R-111`, `R-112` (registrados 2026-09-07; `R-112` se solapa con `OD-12`, verificar
cierre) · `R-122`, `R-123` · `R-124`, `R-125` (`OWNER_DECISION_REQUIRED` → `AOD-06`, `AOD-13`) ·
`R-127` (§9) · `BU-D10`. Los `⚠ R-44` y `⚠ R-58` que `INDEX.md` mantiene junto a 002 y 024 no
aparecen como abiertos en el backlog: **deriva del índice**, no del backlog.

## 4. Índice de hallazgos nuevos `H360-*`

Clases: `MODEL` · `RULE` · `CONTRACT` · `SEMANTIC` · `SPEC/DOC` · `TEST` · `UI` · `SAP` · `PLACEHOLDER`.
Todos tienen evidencia en el documento indicado; ninguno se remedia aquí.

| ID | Sev. | Clase | Hallazgo | Documento |
|---|:--:|---|---|---|
| `H360-P01` | **P1** | RULE | `cull_recording` y `bird_exit` no validan contra el saldo → población negativa posible; sin test | STATE §4 |
| `H360-K01` | **P1** | RULE | «FCR» = alimento/1000; se propaga a índice de producción e IPE | KPI §1 |
| `H360-K02` | **P1** | RULE | % mortalidad = 0 en lotes sin `OpeningBalance` (todos los activados por recepción); `P-15` no lo cubre | KPI §1 |
| `H360-K03` | **P1** | RULE | eficiencia de vacunación cuenta eventos, no aves | KPI §4 |
| `H360-K06` | **P1** | RULE | AFCR suma cantidades de aves como si fueran gramos | KPI §5 |
| `H360-P03` | **P1** | CONTRACT + CONFLICT | `RETURNED` no reenviable; `REJECTED` terminal contra `docs/12` | STATE §1 · `AOD-09` |
| `H360-P05` | **P1** (SAP) | MODEL | `reversals` sin servicio/ruta; `BR-16` sin mecanismo | STATE §5 |
| `H360-S08` | **P1** (D) | SAP | payload no mapeable a documento SAP; sin matriz por proceso (Rec. §24) | SAP §3 |
| `H360-S09` | **P1** (D) | SAP | sin confirmación entrante; estados SAP sin productor | SAP §2 |
| `H360-B05` | **P1** | GAP | consumo de agua ausente (`R-13`, cliente lo exige en 3 etapas) | COMPLETENESS §2 |
| `H360-F01` | **P1** (E) | UI | ninguna pantalla oculta acciones por permiso (`R-98/R-119`) | COMPLETENESS §6 |
| `H360-S05` | P1 (D) | MODEL | `lots` sin identificador SAP | SOR §1 · `AOD-03` |
| `H360-S01/S02/S03` | P1 (D) | PLACEHOLDER | materiales locales sin clave SAP; sin material por raza/sexo/huevo; proveedor por dos vías | SOR §1 |
| `H360-A01` | P2 (PLAUSIBLE) | SECURITY | 23 atajos `is_super_admin` en 8 módulos fuera de `auth` no reevaluados tras `OD-14`; sin test que niegue autoridad global sin contexto en esas superficies | §5 |
| `H360-P04` | P2 (P1 con SAP) | CONTRACT | `cancel` sin motivo, sin rol administrador, no bloquea `SAP_CONFIRMED`/`SAP_ERROR` | STATE §1 |
| `H360-P06` | P2 | SEMANTIC | `CORRECTED` = «pendiente de aprobador» sin corrección | STATE §1 |
| `H360-P08` | P2 | CONTRACT | resumen de cierre sin FCR ni peso final | STATE §3 |
| `H360-P10` | P2 | RULE | `docs/12 R2` (corrector ≠ aprobador) no implementada | STATE §5 |
| `H360-K04/K05/K07/K11/K13` | P2 | RULE | hen-day ×30 · bienestar heurístico · edad en lotes cerrados · % sanos denominador · tendencia sin filtro de estado | KPI |
| `H360-K10` | P2 | GAP | 12 KPI del cliente sin productor | KPI §8 |
| `H360-S04/S06/S07/S10/S11/S12/S13` | P2 | SAP | OT no validada · período 90 días fijo · backoff fijo · sin integridad de consolidación · outbox pasivo · sin `idempotency_key` de cliente · id externo tardío | SAP |
| `H360-B01/B02/B03/B04/B06/B07/B09/B13` | P2 | GAP | cuadre de recepción · pesos en rango · alimento lote/silo/diferencias · evidencia obligatoria · unidad de medida · umbrales T°/H° fijos · `date.today()` sin TZ · sanos/débiles | COMPLETENESS · PLACEHOLDERS |
| `H360-F02/F03` | P2 | UI | estados de error solo en `/users` · evidencia solo en detalle | COMPLETENESS §6 |
| `H360-D01…D05` | P2 (doc) | SPEC/DOC | `OD-04/06/08` sin archivo · `docs/17` inexistente · `BR-17…19` fuera de `spec §5` · auditoría inmutable solo en aplicación · `GA-REM-016` en borrador | AUTHORITY |
| `H360-T01` | P2 | TEST | CI no define `FEATURE_SAP_ENABLED` → 9 tests SAP saltan en CI | SAP §6 |
| `H360-C01` | P2 | CONTRACT | 67/208 rutas sin `response_model`: contrato no declarado en OpenAPI | §8 |
| `H360-P02/P09/P11`, `B08/B10/B11/B12`, `K08` | P3 | — | `DRAFT` muerto · dos «cierres» · `version` · roles por nombre · `sex` String vs Enum · peso proveedor · capacidad incubadora · ganancia diaria aproximada | varios |

## 5. Comprobación de regresión de seguridad (solo verificación; sin re-certificar)

| Control | Estado en `7310adb` | Evidencia |
|---|---|---|
| Toda ruta declara permiso o está exenta con motivo | ✓ | guardián de arranque `authorization_coverage`; 10 exentas listadas |
| Toda ruta declara alcance de unidad | ✓ | `route_scope` 208/208 |
| Sin empresa efectiva → cero filas / 403 | ✓ | `masters/service._apply_company_filter` (`sa_false`), `auth/service._acotar`, `business_units/router._empresa_efectiva` |
| Autoridad global necesita contexto (`OD-14`) en usuarios y maestros | ✓ | `test_user_tenant_isolation` (17), `test_master_tenant_isolation` (16), `test_role_tenancy` (12) |
| Segregación de accesos (`OD-15`) | ✓ | `test_access_administration` (16), `test_grant_candidates` (14) |
| Sin contraseñas literales · sin `if "admin" in role.name` | ✓ | CI `GA-REM-004`; `grep -rn '"admin" in' backend/app` → 0 |
| Suite completa verde hoy | ✓ | 784/49/0 |
| **Residuo** | `H360-A01`: 23 usos de `is_super_admin` como atajo en `operations` (7), `masters/router` (4), `masters/service` (3), `review` (3), `lots` (2), `reports` (2), `dashboard` (1), `curves` (1). Los de `masters` están cubiertos por `_CONTROL_GLOBAL`; los demás **no tienen prueba post-`OD-14`** | `grep -rn is_super_admin backend/app` |

Conclusión: **no se observa regresión** respecto a `RQ-03 COMPLETE`; `H360-A01` es una
verificación pendiente, no un fallo demostrado.

## 6. Validez de las pruebas

| Aspecto | Hecho | Consecuencia |
|---|---|---|
| Backend | 784 verdes; skips justificados por script dedicado | válida |
| CI backend | `backend-ci.yml` sin `FEATURE_SAP_ENABLED` → `test_sap.py` (9) saltado en CI | `H360-T01` |
| Frontend | 87 verdes; solo 8 archivos: cobertura de páginas mínima (`UsersPage` es la única página con test de estados) | `H360-F02` |
| E2E | sin ejecución registrada desde 2026-09-06; 85 commits después | evidencia envejecida en 15/15 procesos |
| Cobertura de invariantes | ningún test para descarte/salida > saldo (`P01`); ningún test de mortalidad % con lote de recepción (`K02`); ningún test reproduce `R-127` (la fixture lo evitó con `sap_config=None`) | tres defectos P1 **sin red** |
| Mutaciones | ver §10 | — |

## 7. Auditorías de base de datos, tiempo, unidades y dominio

| Dimensión | Estado | Evidencia / hallazgo |
|---|---|---|
| Temporal | `event_date Date` + `event_time timestamptz` ✓; `created_at/updated_at` tz ✓; `lots.start_date/end_date` con helper de fecha de negocio (`R-47/R-75`) ✓; **`date.today()` (hora del contenedor) en 10 puntos** (`validators:488`, `reports:596,642`, `lots:34,306,318,326`, `sla:152`, `operations:633`); sin `TIMEZONE` en `config.py` | `H360-B09`, `R-80` abierto |
| Unidades | kg alimento ✓; **gramos implícitos** en `avg_weight`; `unit` texto libre en `consolidated_movements`/`sap_references`; `standard_dosage String`; `dosage_per_bird` sin unidad | `H360-B06` |
| Sexo | `SexEnum` en `lots`; `String(10)` en `bird_movements.sex` | `H360-B10` P3 |
| Edad | derivada de `start_date`; `opening_balances.age_days`; `lot_phases` con fechas ✓ | `else 30` en KPI (PL-20) |
| Objetivos | `genetic_weight_curves(+points min/max)` ✓; evaluación y alerta solo en `weight_recording` | `H360-B02` |
| Genética | `genetic_lines`, `breeds` locales ✓; sin material SAP por raza/sexo | `H360-S02` |
| Bioseguridad / inspección | `inspection_details(parameter, value, value_numeric, status)` genérico; T°/H° 18-35 / 40-90 fijos; sin checklist ni equipos | `H360-B07`, G-R11 |
| Alimento | `quantity_kg`, `feed_type_id`, `week_number`; sin lote, silo, diferencias, OT validada | `H360-B03`, `S04` |
| Vacunas / medicinas | ruta, lote de vacuna, dosis, días de tratamiento ✓; sin método en medicación | G-R16 parcial |
| Mortalidad | causa, sexo, evidencia ✓; % contra población actual ✗ | `H360-K13` |
| Descarte | causa ✓; **sin validación de saldo** | `H360-P01` |
| Recepciones | OC acumulada ✓ (`BR-18`), capacidad ✓ (`BR-17`), muestra ✓; cuadre ✗, pesos ✗, peso proveedor ✗ | `H360-B01/B02/B11` |
| Capacidad | `houses`, `incubators`, `hatchers`, `transports.capacity`; solo `houses` validada | `H360-B12` P3 |
| Auditoría | listeners de aplicación; sin trigger/regla en BD | `H360-D04` |

## 8. Frontend, errores, contratos, hard-coding, semillas

- Frontend: 30 rutas; móvil por `view_type`; formulario único para 26 tipos; evidencia en detalle; sin offline (`AOD-16`); sin permisos en UI (`F01`); 401 global, 403/5xx por página (`F02`); selector de empresa bloqueado por `R-127`.
- Contratos API: `response_model` declarado en **141/208** rutas; **67 sin él** (masters 20 · reports 14 · sap 9 · review 5 · approvals 5 · approval-steps 3 · operations 3 · users 2 · dashboard 2 · audit 2 · roles 1 · corrections 1): su contrato no existe en OpenAPI y el frontend lo infiere → `H360-C01` P2 (misma familia que `GA-REM-011 PARTIALLY CERTIFIED`); `BusinessRuleViolation` → 422 uniforme (`main.py:88`).
- Hard-coding: 9 constantes sin fuente normativa (`SAP_DEFERRED_LOCAL_PLACEHOLDERS §3`), de las que 2 son configurables (umbrales de mortalidad, SLA).
- Semillas: ninguna se ejecuta al arrancar (`docker-entrypoint.sh` solo migra); `dev_seeds` puebla todos los maestros que SAP sustituirá con datos ficticios en el único entorno (`AOD-11`).

## 9. Clasificación de `R-127`

```
R-127  /masters/companies devuelve 500 si la empresa tiene sap_config

CAUSA RAÍZ     Company.sap_config declarada Mapped[Optional[dict]] sobre columna String
               (masters/models.py:65; migración b53bbe02a476 «sa.String()», commit inicial 3c93440),
               mientras specs/global-avicola/data-model.md:12 y docs/03:67 la declaran JSON.
               CompanyRead.sap_config: Optional[dict] (masters/schemas.py:19/32/40) valida texto
               como dict → ResponseValidationError → 500 en lectura. En escritura, setattr de un
               dict sobre String (masters/service.py:249-250) falla en el driver → 500
               (INFERIDO por lectura; no ejecutado en esta auditoría).
CLASIFICACIÓN  MODEL DEFECT  (la columna diverge del modelo de datos de la spec)
               con consecuencia CONTRACT DEFECT (esquema de lectura). No es LEGACY FIELD:
               docs/02 §3.1.4 declara «Configuración SAP por compañía». No es SAP_DEFERRED: es
               configuración propia de la app. No exige OWNER_DECISION para el tipo (la spec ya
               dice JSON); sí para la exposición del campo en el listado (AOD-12, no bloqueante).
BLOQUEO        BLOCKER PHASE 9 — el selector de empresa (company.store.ts:39) tiene como única
               fuente esta ruta (PHASE_9_DEPENDENCY_PREFLIGHT.md) y §70 prohíbe rodeos en frontend.
               NO es BLOCKER NOW: las semillas no pueblan sap_config y la API no puede escribirlo
               sin error, luego en ENV-01 el campo es con alta probabilidad NULL. Verificación
               pendiente del propietario: SELECT count(*) FROM companies WHERE sap_config IS NOT NULL.
RED DE PRUEBA  ninguna: la fixture de R-115 lo esquivó (sap_config=None). Toda remediación debe
               empezar por un test que falle con sap_config poblado (GA-REM-016 AC13).
AUTORIDAD      GA-REM-033 (gestión de maestros) o enmienda a GA-REM-002 — no requiere GA-REM nueva.
```

## 10. MUTATION VALIDITY LESSONS

Regla vigente (tranche 11, §34): una mutación solo cuenta si **se instaló**, **la rama mutada se
ejecutó**, **la propiedad quedó realmente retirada** y **la prueba falló por esa razón**. Lo
aprendido en las tranches 7-15, con su ancla:

| # | Lección | Caso | Ancla |
|---|---|---|---|
| 1 | Un `NameError` no es una mutación: la prueba falló porque el código explotó, no porque la propiedad se retiró. Peor si un `except Exception` lo traga y el test **pasa** | `S5` (`request` inexistente) · fase 6 | `USER_TENANT_ISOLATION_P0_EVIDENCE.md:83`, `GA_REM_040_PHASE_6_EVIDENCE.md:285` |
| 2 | Mutar el archivo que el test **no** lee es no mutar nada | `S7` mutó `dev_seeds.py`; el test leía `baseline_seeds.py` | `R-128-BUSINESS-UNIT-SELF-GRANT-EVIDENCE.md:66` |
| 3 | Una aserción que no puede fallar (regex `\w+` que no casa con `*`) es vacua; se reescribe importando la constante | `S7` | ídem |
| 4 | Un ancla duplicada (mismo bloque en `conceder` y `revocar`) hace que el guion mute el sitio equivocado: **no instalar, no contar** | `S9`, `S1` | `R-128…:89` |
| 5 | Si la fixture está más allá de la primera página, la prueba del filtro no ve la mutación | `S8` | `USER_TENANT_ISOLATION_P0_EVIDENCE.md` |
| 6 | `column == None` sigue siendo fail-closed (`IS NULL`): la mutación no retiró la propiedad; no se cuenta como prueba de sensibilidad | `M6` | `MASTER_TENANT_ISOLATION_EVIDENCE.md` |
| 7 | Una prueba que inspecciona **solo la fixture** no ejercita el sistema; se reescribe para pasar por la API | `S6` | `R-128…:95` |
| 8 | `extra="allow"` en el esquema no es la puerta que se quería abrir; se sustituyó por un endpoint que sirviera el campo prohibido | `S11` | `GA_REM_040_PHASE_8_EVIDENCE.md:201` |
| 9 | Verificar leyendo la aserción cuando la mutación no se puede instalar (`S4/S6` de `R-129`): «200 + campos filtrados» es evidencia; «probablemente fallaría» no | `R-129` | `R-129-…-EVIDENCE.md` |
| 10 | **Leer antes de escribir**: `eb10739` se anunció «784 passed» con 1 fallo real (recuento de rutas `== 6` con la 7.ª ruta añadida). Rectificado en `21e7423` sin reescribir historia; ningún push en rojo | tranche 15 | `R-129-…-EVIDENCE.md`, `git log eb10739..21e7423` |
| 11 | Esta auditoría añade: un proceso **certificado** puede convivir con fórmulas incorrectas si el E2E prueba la cadena y no la conformidad (`K01`, `K02`); la sensibilidad debe apuntar a la **fuente del cliente**, no al código | `P-15` | `KPI_FORMULA_AND_DATA_SOURCE_MATRIX §8` |

## 11. Hoja de ruta final por olas (sin fechas; sin implementar aquí)

| Ola | Objetivo | Contenido (IDs) | Autoridad existente | Decisiones previas |
|---|---|---|---|---|
| **WAVE A** · P0 autoridad, seguridad, datos | cerrar lo que corrompe datos o bloquea el plano de control | `R-127` (tipo `JSON` + test rojo primero) · `H360-P01` (saldo en descarte/salida) · `H360-A01` (verificar atajos `is_super_admin`) · `H360-P04` (guarda de `cancel`) · `H360-T01` (CI SAP) · documental: `INDEX.md`, `docs/17`, `OD-04/06/08` archivos, `BR-17…19` en `spec §5` (`D01…D05`) | `GA-REM-033`, `GA-REM-002`, `GA-REM-005`, `GA-REM-013`, `GA-REM-001` | `AOD-12` (solo exposición) |
| **WAVE B** · procesos faltantes | completar captura y estados exigidos por el cliente | `B05` agua (`GA-REM-021`) · `B01/B02/B03/B04/B13` · `P03` estados (`RETURNED`/`REJECTED`) · `P05` reverso · `P06/P08/P10` · `S04` OT · `S12` idempotencia de cliente | `GA-REM-021`, `GA-REM-029`, `GA-REM-006`, nueva enmienda a `GA-REM-010`/`spec §4.10` | `AOD-08`, `AOD-09`, `AOD-14` |
| **WAVE C** · KPI y trazabilidad | conformidad de fórmulas con `Bases` | `K01 K02 K03 K06` (P1) · `K04 K05 K07 K11 K13` · `K10` 12 ausentes · `B09` TZ · `R-80` | `GA-REM-022` (ampliar), `GA-REM-028` | `AOD-10` |
| **WAVE D** · preparación SAP | matriz formal por proceso (Rec. §24) y claves externas | `S01 S02 S03 S05 S08 S09` · `S06 S07 S10 S11 S13` · `R-124` · `AOD-11` · consumo del espejo (§5 SAP) | `GA-REM-010`, `GA-REM-017` (spec), `OD-12` | `AOD-01…06`, `AOD-11`, `AOD-15` |
| **WAVE E** · frontend / UX | fase 9 y experiencia móvil | fase 9 (tras `R-127`) · `F01` (`R-98/R-119`) · `F02` · `F03` · `R-122` · `R-123` · fases 10-11 de `GA-REM-040` | `GA-REM-040`, `GA-REM-011` | `AOD-13`, `AOD-16` |
| **WAVE F** · certificación final | 360 por proceso | re-ejecución E2E en `main` · sección de conformidad en cada `PROCESS-xx` · certificación de acceso BU 15/15 · `GA-REM-016` a `SPEC_READY` · `P-09` `R-83` | `GA-REM-016` | — |
| **WAVE G** · SAP real | `GA-REM-017`, `P-08`, `AOD-07` | `GA-REM-017` | todas las de D |

## 12. Posición de la fase 9

```
FASE 9 = BLOCKED

  bloqueo directo ....... R-127 (única fuente del selector de empresa; §70 prohíbe rodeos)
  P0 abiertos ........... 0
  P1 de contrato backend/modelo relevantes para la fase ... R-127 · H360-F01 (R-98/R-119) · H360-A01 (verificar)
  BU-D10 ................ intacta (no la requiere la fase 9)
  P-08 .................. intacto
  condición para READY AFTER REMEDIATION: WAVE A cerrada (R-127 con test rojo→verde, A01 verificado,
                                          INDEX reconciliado) — F01 puede ir dentro de la propia fase 9
```

## 13. Límites de esta auditoría

- Sin acceso a la BD ni al contenedor de `ENV-01`: nada de runtime se afirma; `R-127` «latente» es inferencia declarada.
- E2E no ejecutada: ningún proceso se re-certifica ni se desclasifica.
- Recomendación central, Bases y `Sap y App` leídos íntegros; manuales Ross/Cobb no leídos (referencia de dominio, no requisito).
- `BU-D10`, `R-99`, `P-08` y `EX-01` no tocados.
