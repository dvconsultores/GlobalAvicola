# 03 — REQUERIMIENTOS CONSOLIDADOS Y TRAZABILIDAD

El proyecto **no tiene identificadores de requerimiento** (no existe ningún `RF-`, `REQ-`, `HU-` ni `US-` en `docs/` ni en `specs/`; verificado por búsqueda). Los requerimientos se reconstruyen aquí a partir de:

- `docs/02-functional-spec.md` — 14 módulos funcionales, 16 reglas de negocio, 11 roles.
- `specs/global-avicola/spec.md` — dominios funcionales §4.1–§4.12, reglas BR-01…BR-16, NFR §7, AC §8.
- `docs/00-product-vision.md` — diferenciadores.
- `docs/12-approval-workflow.md`, `docs/13-audit-strategy.md`, `docs/10-sap-integration-strategy.md`.

Se asignan identificadores `GA-REQ-###`. **56 requerimientos consolidados.**

## Leyenda de estado

`COMPLETO` E2E verificable · `PARCIAL` · `FRONTEND_ONLY` · `BACKEND_ONLY` · `MOCK` · `DOC_NO_IMPL` documentado sin código · `IMPL_NO_DOC` código sin requisito · `ROTO` · `NO_VERIFICABLE`

---

## 1. Tabla maestra de requerimientos

| ID | Módulo | Requerimiento | Fuente | Prior. | Depende de | Estado |
|---|---|---|---|---|---|---|
| GA-REQ-001 | Auth | Login JWT + refresh token | spec §4.1 / func §3.1 | P0 | — | **COMPLETO** |
| GA-REQ-002 | Auth | RBAC granular por módulo · acción · alcance (9 acciones) | spec §4.1 / func §6.2 | P0 | 001 | **DOC_NO_IMPL** |
| GA-REQ-003 | Auth | CRUD de usuarios con UI | func §3.1 | P1 | 002 | **ROTO** |
| GA-REQ-004 | Auth | Gestión de roles y permisos con UI | func §3.1 | P1 | 002 | **BACKEND_ONLY** |
| GA-REQ-005 | Auth | Aislamiento multi-compañía (`company_id`), Super Admin alcance `all` | spec §2/§8.14-15 | P0 | 001 | **PARCIAL** |
| GA-REQ-006 | Auth | Recuperación de contraseña · MFA · expiración · revocación | spec §30 (prompt) / func §3.1 | P2 | 001 | **DOC_NO_IMPL** |
| GA-REQ-007 | Maestros | API CRUD de 19 catálogos maestros | spec §4.2 | P1 | 005 | **PARCIAL** |
| GA-REQ-008 | Maestros | UI de administración de maestros | func §3.2 | P1 | 007 | **PARCIAL** |
| GA-REQ-009 | SAP | Importación de referencias SAP (PO, TO, centros, materiales, lotes) | spec §4.3 | P1 | 005 | **PARCIAL** |
| GA-REQ-010 | SAP | Capa de abstracción desacoplada (Adapter): manual · mock · real | spec §4.3 / docs/10 | P0 | 009 | **PARCIAL** |
| GA-REQ-011 | SAP | Consolidación de movimientos aprobados | spec §4.10 | P1 | 027 | **COMPLETO** |
| GA-REQ-012 | SAP | Envío idempotente con bitácora (SyncJob · Payload · Response) | spec BR-12 §4.3 | P1 | 011 | **PARCIAL** |
| GA-REQ-013 | SAP | Vinculación del documento SAP al evento operativo | spec §4.3, BR-11 | P0 | 009 | **ROTO** |
| GA-REQ-014 | SAP | Reporte comparativo SAP vs App | spec §4.12 | P2 | 013 | **ROTO** |
| GA-REQ-015 | Progenitoras | Importación de abuelas (plan, PO, docs sanitarios, cuarentena) | spec §4.4 | P1 | 009 | **PARCIAL** |
| GA-REQ-016 | Progenitoras | Ciclo operativo de abuelas (cría y producción) | spec §4.4 | P0 | 022 | **PARCIAL** |
| GA-REQ-017 | Reproductoras | Fases Cría → Producción con transición y cierre de fase | spec §4.5/§4.6 | P0 | 022 | **PARCIAL** |
| GA-REQ-018 | Reproductoras | Operaciones de fase Cría (11 tipos) | spec §4.5 | P0 | 017 | **PARCIAL** |
| GA-REQ-019 | Reproductoras | Operaciones de fase Producción incl. huevo fértil (12 tipos) | spec §4.6 | P0 | 017 | **PARCIAL** |
| GA-REQ-020 | Incubadora | Operaciones de incubación (9 tipos: recepción → nacimiento → despacho) | spec §4.7 | P0 | 022 | **PARCIAL** |
| GA-REQ-021 | Engorde | Operaciones de engorde + cierre formal de lote | spec §4.8 | P0 | 022 | **PARCIAL** |
| GA-REQ-022 | Lotes | Alta y gestión de lotes (tipo, granja, galpón, línea, raza) | spec §4.9 | P0 | 007 | **PARCIAL** |
| GA-REQ-023 | Lotes | Activación manual de lotes existentes / saldos iniciales | spec §4.9 / func §3.9 | P1 | 022 | **BACKEND_ONLY** |
| GA-REQ-024 | Revisión | Bandeja de revisión con filtros (granja, lote, fecha, operador, etapa, tipo, estado) | spec §4.10 | P0 | 016-021 | **PARCIAL** |
| GA-REQ-025 | Revisión | Corrección auditada (valor original + corregido + motivo) | spec §4.10, BR-09 | P0 | 024 | **ROTO** |
| GA-REQ-026 | Revisión | Devolución al operador con observaciones | spec §4.10 | P1 | 024 | **COMPLETO** |
| GA-REQ-027 | Aprobación | Aprobación / rechazo individual y por lote | spec §4.10 | P0 | 024 | **COMPLETO** |
| GA-REQ-028 | Aprobación | Aprobación multinivel configurable (1 · 2 · 3 niveles) | spec §4.10 / docs/12 | P1 | 027 | **BACKEND_ONLY** |
| GA-REQ-029 | Aprobación | Segregación de funciones — el operador no aprueba lo suyo | spec BR-14 | P0 | 027 | **PARCIAL** |
| GA-REQ-030 | Auditoría | Registro inmutable de cada acción (quién · qué · cuándo · antes/después · motivo) | spec §4.11 / docs/13 | P0 | — | **PARCIAL** |
| GA-REQ-031 | Auditoría | Visor de auditoría + línea de tiempo por registro | spec §4.11 | P1 | 030 | **PARCIAL** |
| GA-REQ-032 | Reportes | KPIs productivos (mortalidad, FCR, postura, eclosión, IPE, uniformidad, AFCR) | spec §4.12 | P1 | 016-021 | **PARCIAL** |
| GA-REQ-033 | Reportes | Reporte por lote | spec §4.12 | P2 | 032 | **PARCIAL** |
| GA-REQ-034 | Reportes | Exportación Excel / PDF | spec §4.12 | P2 | 032 | **COMPLETO** |
| GA-REQ-035 | Dashboard | Dashboard móvil del operador (lotes, pendientes, alertas) | func §3.13.1 | P1 | 016-021 | **PARCIAL** |
| GA-REQ-036 | Dashboard | Dashboard web ejecutivo con KPIs y tendencias | func §3.13.2 | P1 | 032 | **PARCIAL** |
| GA-REQ-037 | Alertas | Alertas por desviación (mortalidad, peso fuera de curva, ambiente) | spec §4.5 / func §3.14 | P1 | 016-021 | **PARCIAL** |
| GA-REQ-038 | Alertas | Notificaciones (pendiente >24 h, rechazo al operador, error SAP, cierre próximo) | func §3.14 | P2 | 037 | **DOC_NO_IMPL** |
| GA-REQ-039 | Trazabilidad | Trazabilidad generacional EggBatch / ChickBatch automática | spec §4.9 (2ª) | P1 | 019,020,021 | **ROTO** |
| GA-REQ-040 | Trazabilidad | Árbol de trazabilidad navegable en UI | spec §4.9 (2ª) | P2 | 039 | **PARCIAL** |
| GA-REQ-041 | Operaciones | Adjunto de evidencias a eventos operativos | *(sin spec)* | P2 | 016-021 | **PARCIAL** |
| GA-REQ-042 | Reglas | BR-01 mortalidad ≤ saldo de aves | spec BR-01 | P0 | 016-021 | **ROTO** |
| GA-REQ-043 | Reglas | BR-02 despacho de huevos ≤ disponible | spec BR-02 | P0 | 019 | **COMPLETO** |
| GA-REQ-044 | Reglas | BR-03 carga de incubadora ≤ huevos recibidos | spec BR-03 | P0 | 020 | **COMPLETO** |
| GA-REQ-045 | Reglas | BR-04 despacho de pollitos ≤ nacidos viables | spec BR-04 | P0 | 020 | **COMPLETO** |
| GA-REQ-046 | Reglas | BR-05 cierre de lote requiere resumen final | spec BR-05 | P1 | 021 | **PARCIAL** |
| GA-REQ-047 | Reglas | BR-06 fecha del evento ≥ activación del lote | spec BR-06 | P1 | 022 | **ROTO** |
| GA-REQ-048 | Reglas | BR-07 movimientos requieren lote activo | spec BR-07 | P0 | 022 | **COMPLETO** |
| GA-REQ-049 | Reglas | BR-08 movimientos requieren granja / galpón | spec BR-08 | P1 | 022 | **COMPLETO** |
| GA-REQ-050 | Reglas | BR-10 eliminación lógica con trazabilidad | spec BR-10 | P1 | — | **PARCIAL** |
| GA-REQ-051 | Reglas | BR-11 documentos SAP no duplicados | spec BR-11 | P1 | 013 | **PARCIAL** |
| GA-REQ-052 | Reglas | BR-16 ajuste post-SAP mediante reverso | spec BR-16 | P1 | 012 | **DOC_NO_IMPL** |
| GA-REQ-053 | NFR | i18n ES/EN, 100 % de textos visibles | spec §7 / docs/09 | P1 | — | **COMPLETO** |
| GA-REQ-054 | NFR | Mobile-first real + vista web administrativa | spec §6 / docs/11 | P0 | — | **COMPLETO** |
| GA-REQ-055 | NFR | Compatibilidad 8+ navegadores y 7 viewports | spec §6.4 / docs/08 | P2 | 054 | **NO_VERIFICABLE** |
| GA-REQ-056 | NFR | Cobertura de tests >80 % backend / >70 % frontend | spec §7 / docs/07 | P1 | — | **DOC_NO_IMPL** |

---

## 2. Distribución

| Estado | Nº | % |
|---|---|---|
| COMPLETO (E2E) | 12 | 21,4 % |
| PARCIAL | 28 | 50,0 % |
| ROTO | 7 | 12,5 % |
| DOC_NO_IMPL (documentado sin implementar) | 5 | 8,9 % |
| BACKEND_ONLY | 3 | 5,4 % |
| NO_VERIFICABLE | 1 | 1,8 % |
| MOCK / FRONTEND_ONLY | 0 | 0 % |
| **TOTAL** | **56** | 100 % |

Detalle:
- **COMPLETO (12):** GA-REQ-001, 011, 026, 027, 034, 043, 044, 045, 048, 049, 053, 054
- **ROTO (7):** GA-REQ-003, 013, 014, 025, 039, 042, 047
- **DOC_NO_IMPL (5):** GA-REQ-002, 006, 038, 052, 056
- **BACKEND_ONLY (3):** GA-REQ-004, 023, 028
- **NO_VERIFICABLE (1):** GA-REQ-055
- **PARCIAL (28):** el resto

### Cobertura funcional E2E (criterio estricto §21 del encargo)

Solo cuentan los requerimientos cuya cadena completa es verificable: **UI → validación → request → API → auth → regla de negocio → persistencia → respuesta → actualización de UI → manejo de error**.

```
Requerimientos con cadena E2E íntegra y verificable   = 12
Requerimientos aplicables                             = 56
────────────────────────────────────────────────────────────
Cobertura funcional E2E = 12 / 56 = 21,4 %
```

Métrica complementaria (implementación sustancial = COMPLETO + PARCIAL): **40 / 56 = 71,4 %**.

Nota de criterio: GA-REQ-011 (consolidación) se cuenta como completo **dentro del límite del sistema** — su cadena UI→API→servicio→`consolidated_movements`→respuesta→UI es íntegra. El envío al SAP real es un requerimiento distinto (GA-REQ-010/012) y no está completo.

---

## 3. Matriz maestra de trazabilidad

`FE` pantalla · `API` endpoint · `BE` servicio · `DB` tabla · `TEST` prueba automatizada · `E2E` cadena verificable · `SPEC` cumplimiento metodológico.

| Req | Spec | AC | Proceso | FE | API | BE | DB | Test | E2E | Spec compliance | Evidencia |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 001 | GA-SPEC-001 §4.1 | AC01 | Acceso | LoginPage | `POST /login`,`/refresh` | AuthService | users, roles | ✅ test_auth (no ejecutado) | ✅ | NO_TRACEABILITY (línea base) | `backend/app/auth/service.py:29` |
| 002 | GA-SPEC-001 §4.1 | AC-RBAC | Todos | — | — | — | permissions | ❌ | ❌ | SPEC_NOT_IMPLEMENTED | ausencia de `require_permission` |
| 003 | func §3.1 | — | Admin | UsersPage | `/users` CRUD | AuthService | users | ❌ | ❌ ROTO | SPEC_PARTIAL | `pages/users/UsersPage.tsx:21` |
| 004 | func §3.1 | — | Admin | — | `/roles` CRUD | AuthService | roles, permissions | ❌ | ❌ | SPEC_PARTIAL | sin ruta en `App.tsx` |
| 005 | GA-SPEC-001 §8.14 | AC14,AC15 | Todos | company.store | `/switch-company` | 8 servicios | *.company_id | ⚠ test_multi_company | ⚠ | SPEC_IMPLEMENTATION_DRIFT | `masters/service.py:37`; 61 filtros crudos |
| 007 | GA-SPEC-001 §4.2 | — | Maestros | MasterListPage | 82 ops `/masters/*` | MasterService | 19 tablas | ⚠ test_masters | ⚠ | SPEC_COMPLIANT | `masters/router.py:88-107` |
| 010 | GA-SPEC-001 §14.4 | — | SAP | SapManagerPage | `/sap/*` | SapService | sap_* | ⚠ test_sap | ❌ | SPEC_RETRODOCUMENTED | `sap/service.py:34` `# TODO` |
| 013 | GA-SPEC-001 §4.3 | — | SAP | OperationFormPage | `POST /operations` | OperationsService | operational_events.sap_document_ref | ❌ | ❌ ROTO | SPEC_IMPLEMENTATION_DRIFT | `extra_data.sap_order_ref` en vez del campo |
| 016-021 | GA-SPEC-001 §4.4-4.8 | AC01 | 6 cadenas | OperationFormPage | `POST /operations` | OperationsService | operational_events (+6) | ⚠ | ⚠ | SPEC_PARTIAL / OUT_OF_SPEC | `processCatalog.ts:190-215` |
| 023 | GA-SPEC-001 §4.9 | — | Apertura | — | `POST /lots/activate-manual` | LotService | opening_balances | ❌ | ❌ | SPEC_PARTIAL | sin UI |
| 024 | GA-SPEC-001 §4.10 | AC02 | Revisión | ReviewCenter | `GET /review/pending` | ReviewService | operational_events | ⚠ test_review | ⚠ | SPEC_PARTIAL | filtros `status`/`operator_id` ignorados |
| 025 | GA-SPEC-001 §4.10 | AC03 | Corrección | CorrectionForm | `POST /corrections` | CorrectionService | correction_logs | ❌ | ❌ ROTO | SPEC_PARTIAL | `corrections/service.py:52` |
| 027 | GA-SPEC-001 §4.10 | AC04 | Aprobación | ApprovalPanel | `/approvals/*` | ApprovalService | approval_actions | ⚠ | ✅ | SPEC_COMPLIANT | `review/service.py:301` |
| 028 | docs/12 | — | Aprobación | — | `/approval-steps` (5) | ApprovalStepService | approval_steps | ❌ | ❌ | SPEC_NOT_IMPLEMENTED | nunca consultado en `approve()` |
| 029 | GA-SPEC-001 BR-14 | AC04 | Aprobación | — | `/approvals/approve` | validate_segregation | — | ⚠ test_f4b | ⚠ | SPEC_PARTIAL | bypass vía `/review/complete` |
| 030 | GA-SPEC-001 §4.11 | AC10 | Auditoría | AuditPage | `/audit` | listeners + helpers | audit_logs | ⚠ test_f6 | ⚠ | CODE_BEFORE_SPEC | doble escritura |
| 039 | GA-SPEC-001 §4.9(2ª) | — | Trazabilidad | TraceabilityTree | `/lots/{id}/traceability` | OperationsService | egg_batches, chick_batches | ❌ | ❌ ROTO | CODE_BEFORE_SPEC | `operations/service.py:127-176` |
| 041 | *(ninguna)* | — | Operaciones | OperationDetailPage | `/operations/{id}/evidences` | OperationsService | evidences | ❌ | ⚠ | IMPLEMENTED_WITHOUT_SPEC | 0 menciones en spec/docs |
| 042 | GA-SPEC-001 BR-01 | — | Mortalidad | OperationFormPage | `POST /operations` | validate_mortality | bird_movements | ⚠ test_f8c | ❌ ROTO | SPEC_COMPLIANT (impl. rota) | `operations/service.py:242` |
| 052 | GA-SPEC-001 BR-16 | — | SAP | — | — | — | reversals (huérfana) | ❌ | ❌ | SPEC_NOT_IMPLEMENTED | 0 referencias fuera del modelo |
| 053 | GA-SPEC-001 §7 | AC12 | Todos | i18n | — | — | — | ✅ | ✅ | SPEC_COMPLIANT | 865/865 claves |
| 056 | GA-SPEC-001 §7 | — | QA | — | — | — | — | ❌ | ❌ | SPEC_NOT_IMPLEMENTED | 4 archivos de test frontend / 108 fuentes |

**Traceability Rate** (cadena Requisito → Spec → AC → Código verificable): **17 %** — ver `05_SPEC_DEVELOPMENT_COMPLIANCE.md`.

---

## 4. Requerimientos duplicados, contradictorios o sustituidos

| Situación | Detalle | Evidencia |
|---|---|---|
| **Numeración de reglas contradictoria** | La spec define BR-10 = "eliminación lógica" y BR-11 = "documentos SAP no duplicados". El código usa `"BR-10"` como identificador de la regla de documento SAP duplicado. Los mensajes al usuario citan un identificador equivocado. | `validators.py:227,243` vs `spec.md §5` |
| **Reglas del código sin requerimiento** | BR-17 (capacidad de galpón), BR-18 (cantidad ≤ OC), BR-19 (período cerrado >90 días) existen en el código y no están en la lista BR-01…BR-16 de la spec ni en `docs/02`. | `validators.py:296,313,332` |
| **`egg_classification` sustituido** | La spec lo lista como operación de abuelas, reproductoras producción e incubadora. El commit `f379b7e` lo fusionó en `egg_collection`; sigue en el enum del backend y en `EVENT_ICON_MAP`, pero no está en ningún `STAGE_OPERATIONS`. Spec nunca actualizada. | `processCatalog.ts:190-215`; `operations/models.py:37` |
| **Duplicación de sección en la spec** | `spec.md` tiene **dos** secciones numeradas `4.9` (Trazabilidad Generacional y Activación Manual). Edición en caliente sin renumerar. | `specs/global-avicola/spec.md` |
| **Referencia rota** | `spec.md §14` y `tasks.md` Fase 9 remiten a `docs/17-production-checklist.md`, que **no existe** (docs llega hasta 16). | `ls docs/` |
| **Dark mode: requisito invertido** | `spec.md §6.3` prohíbe el modo oscuro; se implementó (24 commits) y luego se revirtió. La spec nunca cambió; quedaron restos (`tailwind.config.ts darkMode:'class'`, `theme.store.ts`, `DarkModeToggle.tsx`, `main.tsx:19`). | ver `05_SPEC_DEVELOPMENT_COMPLIANCE.md` |
