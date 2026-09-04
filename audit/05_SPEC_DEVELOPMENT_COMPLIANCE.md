# 05 — AUDITORÍA FORENSE DE SPEC DEVELOPMENT

> Pregunta central: **¿Global Avícola usó realmente Spec Development, o solo generó documentos llamados specs?**
> Respuesta corta: **usó Spec Development de forma real pero discontinua.** Hay una ventana con evidencia forense inequívoca de spec-first (Fase 8) y un cuerpo mayoritario de trabajo sin trazabilidad o con spec posterior al código.

---

## 1. Metodología de la evidencia

Jerarquía aplicada (§54 del encargo): (1) primer commit Git del artefacto, (2) historial, (3) referencia cruzada, (4) metadata de filesystem — nunca la fecha del archivo como prueba principal.

Base forense:
- 171 commits, 2 autores (`Maria` 157, `dvconsultores` 14), rango 2026-06-23 → 2026-07-08.
- **0 merges, 0 pull requests, 0 tags, 1 rama.**
- **`3c93440` "first commit"** = 227 archivos, 32 954 inserciones, incluye simultáneamente `docs/` (17), `specs/` (7), `backend/app/` completo, `frontend/src/` completo y `tests/`.

**Consecuencia metodológica de primer orden:** para todo lo contenido en el commit inicial —es decir, la práctica totalidad de la arquitectura, los 25 tipos de evento, el workflow de revisión/aprobación, la integración SAP, la auditoría y las 47 tablas— **Git no puede demostrar ni refutar que la spec precediera al código**. Ese cuerpo se clasifica `NO_TRACEABILITY`, no `IMPLEMENTED_WITHOUT_SPEC`: las specs existen y son coherentes con lo implementado, pero la precedencia temporal no es demostrable.

---

## 2. Evidencia POSITIVA: spec-first demostrado

### 2.1 Fase 8 — Gap Resolution (T-067 … T-083)

| Hito | Commit | Fecha y hora | Contenido |
|---|---|---|---|
| Se escriben las tareas T-067…T-083 con gaps G-01…G-13 | `37c8f0e` | **2026-06-24 02:55** | `tasks.md` incorpora "Phase 8: Gap Resolution & Quality Elevation" |
| Se implementan Sprint A+B | `d3f37f8` | **2026-06-24 03:25** | STAGE_OPERATIONS, `BirdTypeEnum.HATCHERY`, design system, mobile UX |
| Se implementa Sprint C | `b3a0c56` | 2026-06-24 03:36 | Lot form, modal de transición de fase, Masters CRUD, Dashboard KPIs |
| Se implementa Sprint D | `2d06024` | 2026-06-24 03:51 | Export Excel/PDF, Business Rules, Trazabilidad Generacional |

**Delta spec → código: 30 minutos.** Es evidencia forense directa de especificación previa con tareas, prioridad, esfuerzo estimado y archivos objetivo. Se clasifica **SPEC_COMPLIANT** para los gaps G-01…G-13 y **SPEC_PARTIAL** para T-083 (ver §4.2).

### 2.2 Registro explícito de alcance excluido

`56cbaf8` (2026-06-24 03:06) — "docs: registrar LIVIANAS como fuera de alcance v1, arquitectura extensible" añade `spec.md §9 Out of Scope` con la cadena de aves livianas. Es una decisión de alcance documentada **antes** de cualquier código relacionado. **SPEC_COMPLIANT.**

### 2.3 Verificación del plan contra el código

`1fba4b2` (2026-06-24 02:33) — "docs: validación del plan vs código real" y la tabla "Implementation Status — 2026-06-24" en `tasks.md`, que marca honestamente 🔶 Parcial en Fases 1, 2, 3, 6 y 7. Es una práctica de Spec Development correcta: **reconciliar el estado documental con el código real** en vez de declarar todo hecho.

---

## 3. Evidencia NEGATIVA: spec posterior o ausente

### 3.1 SPEC_RETRODOCUMENTED — spec escrita en el mismo commit que el código

| Feature | Commit | Prueba |
|---|---|---|
| **Feature flags (`spec.md §14`, 100 líneas: tabla de flags, comportamiento por entorno, estados SAP, checklist)** | `b2c3f3c` 2026-06-24 15:11 | El mismo commit que implementa `FEATURE_SAP_ENABLED`, `FEATURE_RATE_LIMIT_ENABLED` en `config.py` y el routing condicional de SAP en `main.py`. `spec.md` pasa de 379 → 458 líneas en ese commit. Antes de él la sección **no existía** (`featureflags=0` en `37c8f0e` y `56cbaf8`). |

Clasificación: **SPEC_RETRODOCUMENTED**. La sección está bien escrita y sigue vigente, pero se redactó con el código, no antes.

### 3.2 CODE_BEFORE_SPEC — código anterior a su especificación

| Feature | Código | Spec | Delta |
|---|---|---|---|
| **Trazabilidad generacional (EggBatch / ChickBatch)** | `2d06024` **2026-06-24 03:51** — migración `f1e2d3c4b5a6`, modelos, endpoints, `TraceabilityTree.tsx` | `ac125b2` **2026-06-24 18:38** — aparece `spec.md §4.9 Generational Traceability` | **+14 h 47 min** |
| **Trazabilidad generacional (2ª documentación)** | igual | `8318d0f` 2026-06-27 15:14 "docs: documentar trazabilidad generacional" | +3 días |
| **Sistema de auditoría automática** | `e357dbe` 2026-06-29 19:35 (`audit/listeners.py`, `audit/helpers.py`) | `spec.md §4.11` existía desde el inicio pero describía el *qué*, no el mecanismo; el diseño real (listeners + helpers) se documentó en `AUDITORIA_FUNCIONAL_E2E.md` **después** de implementarlo | posterior |

### 3.3 IMPLEMENTED_WITHOUT_SPEC — funcionalidad sin ninguna mención en spec ni docs

Verificado por búsqueda exhaustiva en `specs/global-avicola/spec.md` y en los 16 documentos de `docs/`:

| # | Feature | Menciones en spec.md | Menciones en docs/ | Primer commit | Tamaño |
|---|---|---|---|---|---|
| 1 | `egg_reception_classification` (26º tipo de evento) | **0** | **0** | `076ca5e` 2026-06-29 06:18 | enum + catálogo + formulario + i18n |
| 2 | `hatchery_purpose` en `lots` | **0** | **0** | `762b8bd` 2026-06-27 17:29 (mig. `h8i9j0k1l2m3`) | columna + lógica |
| 3 | Tabla y flujo `egg_storage` | **0** | **0** | mig. `4396a2b7e7d6` | tabla de 12 columnas, solo escritura |
| 4 | Motor de alertas `operational_alerts` | **0** | **0** | `bdb5cde` 2026-06-27 03:12 | tabla + generador + panel |
| 5 | Evidencias adjuntas `evidences` | **0** | **0** | `e201e76` 2026-06-27 02:11 | tabla + 4 endpoints + UI |
| 6 | Patrón `SearchSelect` (34 instancias) | **0** | **0** | `b162695` 2026-06-28 21:30 | componente + refactor de 34 campos |
| 7 | Telegram Mini App + bot | **0** | **0** | `4c88dac` 2026-06-29 20:15 / `365050c` 2026-06-30 | hook 285 LOC + servicio Docker + 8 commits |
| 8 | Tabla `reversals` | **0** | **0** | mig. `bfcc893f581a` | tabla **huérfana**, 0 referencias en código |
| 9 | `bird_transfer` (tipo de evento) | **0** | 1 | commit inicial | enum + catálogo + formulario |
| 10 | Firma digital `SignaturePad` | **0** | **0** | `0b8a6b7` 2026-06-27 05:51 | componente + 8 tests, **no usado en ninguna página** |
| 11 | Reglas BR-17, BR-18, BR-19 | **0** (spec llega a BR-16) | **0** | commit inicial / `939fd14` | 3 validadores activos |
| 12 | Selector de compañía + `switch-company` | parcial (§2 multi-compañía) | 0 | `1b11c23` 2026-06-27 00:02 | endpoint + store |

**12 funcionalidades relevantes sin autorización documental.** Cinco de ellas (alertas, evidencias, SearchSelect, Telegram, switch-company) representan cambios de producto visibles para el usuario.

### 3.4 OUT_OF_SPEC — código que contradice la spec vigente

| # | Regla de la spec | Qué se implementó | Evidencia | Clasificación |
|---|---|---|---|---|
| 1 | `spec.md §6.3`: "**Sin dark mode** — diseño corporativo claro siempre" | Modo oscuro completo: store, toggle, `darkMode:'class'`, variantes en el 100 % de los TSX. **24 commits** entre 2026-06-25 17:37 (`fe4580a` "modo oscuro oficial") y 2026-06-28 23:42 (`8940d9e` "Remove dark mode"). | `git log -i --grep="dark mode\|modo oscuro"` → 24 | **UNJUSTIFIED_SCOPE_CREEP** + reversión total |
| 2 | `spec.md §6.3`: paleta `#1E3A5F` header, `#2563EB` primario, `#3B82F6` hover | Paleta **teal "Atenea"** (`#5a9bba`, `#264c5f`, `#4e8fad`…) copiada de otro proyecto, más gradientes y glassmorphism. Spec nunca actualizada. Hoy quedan 7 referencias a `#2563EB`/`#1E3A5F` frente a 51 usos teal. | `frontend/tailwind.config.ts:12-24`; `frontend/src/index.css:1-27`; commit `a1d7843` 2026-06-28 22:32 | **OUT_OF_SPEC / HIGH_DRIFT** |
| 3 | `spec.md §6.3`: "Iconografía lucide-react exclusivamente (**sin emojis en UI de producción**)" | Emojis en 3 archivos de frontend y 1 de backend: `RangeIndicator` usa ✅⚠️❌; `dashboard/service.py` devuelve `quick_actions` con 🌾💀⚖️🥚. | `frontend/src/pages/operations/OperationFormPage.tsx:60-65`; `backend/app/dashboard/service.py:48-53` | **OUT_OF_SPEC** |
| 4 | `spec.md §6.1`: bottom navigation de 5 elementos (Home, Lotes, Registrar, KPIs, Pendientes) | `MobileNav` tiene **3** (Gestión Avícola, Home, KPI). El hamburger se añadió (`cf446ef`) y se quitó dos commits después (`1d99580`). | `frontend/src/components/layout/MobileNav.tsx:25-27` | **OUT_OF_SPEC / drift de UX** |
| 5 | `spec.md §7` "sin hardcodear textos" | `ALL_EVENT_TYPES` devuelve 25 etiquetas **en español fijo** desde el backend; `quick_actions` idem; cabeceras de exportación Excel/PDF en español fijo. | `backend/app/operations/schemas.py:180-206`; `frontend/src/pages/reports/ReportsPage.tsx:38-47` | OUT_OF_SPEC menor |
| 6 | `spec.md §4.4`: abuelas incluye `egg_collection`, `egg_classification`, `egg_dispatch` en un único conjunto GRANDPARENT | El frontend inventó **6 etapas** (`grandparent_rearing/production`, `breeder_rearing/production`, `hatchery`, `broiler`) y repartió las operaciones de otra forma; `egg_classification` desapareció del catálogo. | `frontend/src/data/processCatalog.ts:16-23,190-215` | **OUT_OF_SPEC / taxonomía divergente** |

### 3.5 SPEC_NOT_IMPLEMENTED — spec sin código

| Spec | Requisito | Estado |
|---|---|---|
| `spec.md §4.1` / `docs/02 §6.2` | RBAC granular por módulo·acción·alcance | Modelo y seeds existen; **cero enforcement** |
| `spec.md BR-16` / `docs/12` | Reverso post-SAP | Tabla `reversals` **huérfana**, 0 referencias |
| `docs/02 §3.14` | Notificaciones (>24 h, rechazo, error SAP, cierre próximo) | Ninguna implementada |
| `spec.md §4.10` / `docs/12` | Aprobación multinivel 1·2·3 con `ApprovalStep` | `ApprovalStep` tiene CRUD pero **nunca se consulta** en `approve()`; solo se distingue "1 nivel" vs ">1" |
| `spec.md §4.5` | Alerta por peso fuera de curva estándar | Solo hay alertas de mortalidad, temperatura y humedad |
| `spec.md §7` | Cobertura >80 % backend / >70 % frontend | 4 archivos de test frontend para 108 fuentes |
| `spec.md §30`(prompt)/§4.1 | Recuperación de contraseña, MFA, revocación, logout | Ningún endpoint |
| `tasks.md` T-085 | `RealSapAdapter` | `# TODO` en `sap/service.py:36` |
| `tasks.md` T-090 | `docs/18-production-runbook.md` | No existe |
| `spec.md §14` | `docs/17-production-checklist.md` | **Referenciado y no existe** |

### 3.6 SPEC_IMPLEMENTATION_DRIFT

| Artefacto | Coincidía inicialmente | Diverge hoy | Nivel |
|---|---|---|---|
| `specs/.../data-model.md` (GA-SPEC-004) | sí | 47 tablas reales vs modelo documentado | **HIGH_DRIFT** |
| `specs/.../contracts/api-contract.md` + `docs/06` | sí | 167 endpoints reales; los contratos describen una fracción | **CRITICAL_DRIFT** |
| Design system (GA-SPEC-019) | sí | paleta, dark mode, emojis | **CRITICAL_DRIFT** |
| Taxonomía de etapas y eventos | sí | 6 etapas FE vs 5 dominios spec; `egg_classification` retirado; 2 eventos nuevos | **HIGH_DRIFT** |
| `README.md` estructura del backend | sí | anuncia `routers/ schemas/ services/ repositories/ models/ domain/ workflows/ migrations/`; ninguna existe | **HIGH_DRIFT** |
| `README.md` estado del proyecto | sí | dice "⚠️ El proyecto está en fase de especificación. **No se ha iniciado codificación funcional**" con 171 commits y el sistema desplegado | **CRITICAL_DRIFT** |
| Numeración de reglas BR | sí | el código llama "BR-10" a la regla que la spec numera BR-11 | MEDIUM_DRIFT |

### 3.7 SPEC_CLOSED_WITHOUT_VERIFICATION

| Declaración | Documento | Refutación |
|---|---|---|
| "RE-CERTIFICACIÓN — 16/16 hallazgos cerrados, resultado APROBADO" | `e0eed25` 2026-06-24 04:51 | 5 días después se documenta que la auditoría automática **no existía** (`AUDITORIA_FUNCIONAL_E2E.md` H2: "`audit/__init__.py` estaba vacío… la tabla `audit_logs` estaba vacía") |
| "re-certificación final V2 — 96/100" | `a84eb2d` 2026-06-27 05:14 | mismo problema de auditoría inexistente; RBAC nunca aplicado |
| "71 ops al 100 %, 14 integraciones SAP, multi-compañía certificado, listo para UAT" | `CERTIFICACION_FUNCIONAL.md` 2026-06-29 | el frontend **nunca envía `sap_document_ref`**; el aislamiento multiempresa tiene agujeros confirmados |
| "29/29 rutas definidas y funcionales" | `CERTIFICACION_FUNCIONAL.md §2` | lista `/approval-steps` y `/corrections` como rutas; **no existen** en `App.tsx` |
| "Dark Mode — Theme store con persistencia" como entregable crítico | `IMPLEMENTATION_COMPLETE.md` | eliminado 4 días después; además contradecía la spec desde el principio |
| Tests "todos pasando" | `0030ccc` "test: Add smoke tests… with all tests passing" | los 76 tests backend **nunca se han ejecutado en CI**; `test_list_event_types` afirma `len(data) == 24` y el endpoint devuelve **25** → fallo estático confirmado |

### 3.8 Specs reabiertas / ciclos de corrección repetidos

| Tema | Ciclos | Lectura |
|---|---|---|
| Modo oscuro | 15 commits de "Fix dark mode…" en 4 días, luego eliminación total | **spec deficiente ignorada** — la spec ya decía que no se hiciera |
| Navegación mobile | ~20 commits (`a9d6941`, `cddffa4`, `3fd61a0`, `7794678`, `e73a03f`, `f6f3f6c`, `010dcd3`, `1590dbb`, `ce6d7c0`, `2c17e1f`, `2b8627e`, `cf446ef`, `b38275a`, `1acd55a`, `c976113`, `1d99580`…) | **requisito no especificado** — se iteró sobre prompts, no sobre spec |
| Build de Docker/TypeScript | `51680d8`, `fcb57a7` (31 errores TS), `ae6d981`, `62bffa0`, `52cf1f8`, `5f82c41`, `81a84db`, `8469875`, `3302cfe` | **QA insuficiente** — errores de compilación llegaron a `main` porque CI nunca corre |
| Filtro `company_id` para super admin | `8860ac5`, `bfccdfb` | **implementación deficiente**: el último fix se aplicó **solo** a `SapService`; quedan 61 filtros crudos en otros 7 servicios |

---

## 4. Matriz forense Spec Development

30 features auditadas.

| # | Feature | Req | Spec | Fecha spec | Fecha código | AC | Test | Estado | Desviación |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Auth JWT + refresh | 001 | GA-SPEC-001 §4.1 | 06-23 (baseline) | 06-23 | ✗ | ✓ no ejec. | NO_TRACEABILITY | — |
| 2 | RBAC granular | 002 | GA-SPEC-001 §4.1 | 06-23 | — | ✗ | ✗ | **SPEC_NOT_IMPLEMENTED** | crítica |
| 3 | Multi-compañía | 005 | GA-SPEC-001 §2 | 06-23 | 06-26/27 | ✓ AC14/15 | ✓ no ejec. | SPEC_PARTIAL | drift |
| 4 | 19 catálogos maestros | 007 | GA-SPEC-001 §4.2 | 06-23 | 06-23 | ✗ | ✓ | NO_TRACEABILITY | 15 sin PUT |
| 5 | UI maestros | 008 | GA-SPEC-003 T-077 | 06-24 02:55 | 06-24 03:36 | ✗ | ✗ | **SPEC_COMPLIANT** | 12/19 entidades |
| 6 | 25 tipos de evento | 016-021 | GA-SPEC-001 §4.4-4.8 | 06-23 | 06-23 → 06-29 | ✗ | ✓ | SPEC_PARTIAL | +2 eventos sin spec |
| 7 | STAGE_OPERATIONS por etapa | 016-021 | GA-SPEC-003 T-067/68/70/71 | 06-24 02:55 | 06-24 03:25 | ✓ implícitos | ✗ | **SPEC_COMPLIANT** | taxonomía divergente |
| 8 | `BirdTypeEnum.HATCHERY` | 020 | GA-SPEC-003 T-069 | 06-24 02:55 | 06-24 03:25 | ✓ | ✗ | **SPEC_COMPLIANT** | — |
| 9 | Fases de lote + transición | 017 | GA-SPEC-003 T-071/72 | 06-24 02:55 | 06-24 03:36 | ✓ | ✗ | SPEC_PARTIAL | UI en pantalla rota |
| 10 | Formulario de creación de lote | 022 | GA-SPEC-003 T-073 | 06-24 02:55 | 06-24 03:36 | ✓ | ✗ | **SPEC_COMPLIANT** | — |
| 11 | Design system base | 054 | GA-SPEC-003 T-074/75/76 | 06-24 02:55 | 06-24 03:25 | ✓ | ✓ | **SPEC_COMPLIANT** → luego **OUT_OF_SPEC** | paleta/dark mode |
| 12 | Dashboard KPIs | 036 | GA-SPEC-003 T-078 | 06-24 02:55 | 06-24 03:36 | ✓ | ✗ | SPEC_PARTIAL | — |
| 13 | Mis Pendientes | 035 | GA-SPEC-003 T-079 | 06-24 02:55 | 06-24 17:55 | ✓ | ✗ | SPEC_PARTIAL | **ROTO en runtime** |
| 14 | Export Excel/PDF | 034 | GA-SPEC-003 T-081 | 06-24 02:55 | 06-24 03:51 | ✓ | ✗ | **SPEC_COMPLIANT** | — |
| 15 | Business Rules BR-05…BR-16 | 042-052 | GA-SPEC-003 T-082 | 06-24 02:55 | 06-24 03:51 | ✓ | ✓ parcial | SPEC_PARTIAL | BR-16 no impl. |
| 16 | Trazabilidad generacional | 039 | GA-SPEC-003 T-083 + spec §4.9 | 06-24 02:55 (tarea) / **06-24 18:38 (spec)** | 06-24 03:51 | ✓ tarea | ✗ | **CODE_BEFORE_SPEC** | auto-creación rota |
| 17 | Feature flags | — | GA-SPEC-001 §14 | **06-24 15:11 (mismo commit)** | 06-24 15:11 | ✓ | ✓ | **SPEC_RETRODOCUMENTED** | rate limit off en prod |
| 18 | Inspección por galpón | 016-021 | *(ninguna)* | — | 06-26 23:24 | ✗ | ✓ | **IMPLEMENTED_WITHOUT_SPEC** | JUSTIFIED_EXTENSION |
| 19 | Evidencias adjuntas | 041 | *(ninguna)* | — | 06-27 02:11 | ✗ | ✗ | **IMPLEMENTED_WITHOUT_SPEC** | sin volumen |
| 20 | Motor de alertas | 037 | *(ninguna)* | — | 06-27 03:12 | ✗ | ✗ | **IMPLEMENTED_WITHOUT_SPEC** | generador roto |
| 21 | Validadores + idempotencia + curvas | 042-049 | parcial (BR) | 06-23 | 06-27 05:31 | ✗ | ✓ | SPEC_PARTIAL | BR-17/18/19 sin spec |
| 22 | Mock SAP + firma digital | 010 | *(ninguna)* | — | 06-27 05:51 | ✗ | ✓ (SignaturePad) | **IMPLEMENTED_WITHOUT_SPEC** | ambos muertos |
| 23 | Modo oscuro | — | **prohibido por spec §6.3** | — | 06-25 → 06-28 | ✗ | ✗ | **OUT_OF_SPEC** | revertido, restos |
| 24 | Paleta Atenea teal | 054 | **contradice spec §6.3** | — | 06-28 22:32 | ✗ | ✗ | **OUT_OF_SPEC** | HIGH_DRIFT |
| 25 | SearchSelect (34 campos) | — | *(ninguna)* | — | 06-28 21:30 | ✗ | ✗ | **IMPLEMENTED_WITHOUT_SPEC** | JUSTIFIED_EXTENSION |
| 26 | `egg_reception_classification` | — | *(ninguna)* | — | 06-29 06:18 | ✗ | ✗ | **IMPLEMENTED_WITHOUT_SPEC** | nuevo tipo de evento |
| 27 | Fusión `egg_classification`→`egg_collection` | — | **contradice spec §4.4/4.6/4.7** | — | 06-29 05:27 | ✗ | ✗ | **OUT_OF_SPEC** | spec no actualizada |
| 28 | Auditoría automática | 030 | GA-SPEC-001 §4.11 / GA-SPEC-021 | 06-23 (qué) | 06-29 19:35 (cómo) | ✓ AC10 | ✓ | SPEC_PARTIAL | doble escritura |
| 29 | Telegram Mini App + bot | — | *(ninguna)* | — | 06-29 → 07-08 | ✗ | ✗ | **IMPLEMENTED_WITHOUT_SPEC** | canal de producto nuevo |
| 30 | Habilitar SAP en producción | 010 | GA-SPEC-001 §14.3 (pasos 1-5) | 06-24 | 07-08 20:35 | ✓ parcial | ✗ | **SPEC_PARTIAL** | se activó el flag sin `RealSapAdapter` (T-085) |

---

## 5. Métricas Spec Development

Universo: **30 features auditadas**.

```
Specs encontradas ................................. 23
Specs vigentes .................................... 17
Specs obsoletas / con drift alto .................. 5   (GA-SPEC-004, 006, 007, 014, 019)
Specs contradictorias ............................. 1   (GA-SPEC-019 vs implementación de paleta y dark mode)
Specs no implementadas ............................ 2   (GA-SPEC-015 qa-plan, GA-SPEC-016 browser-compat sin ejecutar)
Specs referenciadas inexistentes .................. 2   (docs/17, docs/18)

Features auditadas ................................ 30
SPEC_COMPLIANT ....................................  7   (#5,7,8,10,11,14 + #1 parcial→no; ver detalle)
SPEC_PARTIAL ......................................  9   (#3,6,9,12,13,15,21,28,30)
NO_TRACEABILITY (baseline squash) .................  2   (#1,4)
IMPLEMENTED_WITHOUT_SPEC ..........................  7   (#18,19,20,22,25,26,29)
CODE_BEFORE_SPEC ..................................  1   (#16)
SPEC_RETRODOCUMENTED ..............................  1   (#17)
OUT_OF_SPEC .......................................  3   (#23,24,27)
SPEC_NOT_IMPLEMENTED ..............................  1   (#2)   [+9 requisitos menores, ver §3.5]
Features con drift ................................  7
Specs cerradas sin validación .....................  6   (§3.7)
```

### Cálculos

```
SPEC COMPLIANCE RATE
  features correctamente trazadas y alineadas   =  7
  features auditadas                            = 30
  → 7 / 30 × 100 = 23,3 %

TRACEABILITY RATE (Requirement → Spec → AC → Code completo)
  features con cadena completa                  =  5   (#5,7,8,10,14)
  features auditadas                            = 30
  → 5 / 30 × 100 = 16,7 %

AC COVERAGE RATE
  AC implementados                              = 12   (de los 15 AC del MVP, spec §8)
  AC aplicables                                 = 30   (15 AC de MVP + 15 AC derivados de tareas Fase 8)
  → 12 / 30 × 100 = 40,0 %

SPEC TEST COVERAGE RATE
  AC con test verificable y ejecutable hoy       =  2   (AC12 i18n, AC11 diseño — vía vitest)
  AC aplicables                                 = 30
  → 2 / 30 × 100 = 6,7 %

OUT-OF-SPEC RATE
  features fuera de spec (OUT_OF_SPEC + IMPLEMENTED_WITHOUT_SPEC)  = 10
  features auditadas                                               = 30
  → 10 / 30 × 100 = 33,3 %
```

---

## 6. Trazabilidad de tests a specs (§77)

```
SPEC → AC → TEST
```

- `spec.md §8` define 15 AC de MVP. **Ninguno tiene un test nombrado o referenciado.**
- `tests/test_full_workflow_audit.py` sí nombra flujos F1…F10 que se corresponden con los AC 1-10 — es la mejor trazabilidad del proyecto — pero **no se ejecuta en ningún pipeline** y requiere una base de datos preexistente con `lot_id=2` y usuarios sembrados.
- `frontend/src/**/__tests__/` prueba 4 unidades (componentes UI, SignaturePad, auth store, useMediaQuery); ninguna corresponde a un AC de negocio.

Clasificación: **`PARTIAL_TRACEABILITY`** — existe nomenclatura de trazabilidad en un archivo de test, sin ejecución ni vínculo formal.

---

## 7. Cierre de specs (§76)

Evidencia buscada: checklist, tests, review, QA, acceptance, commit de cierre, sign-off.

| Mecanismo | Presente | Detalle |
|---|---|---|
| Checklist | Parcial | `tasks.md` "Production Activation Checklist" con casillas `☐` **todas sin marcar**; tabla "Implementation Status" con iconos |
| Tests como gate | **No** | CI nunca ejecutado |
| Code review | **No** | 0 pull requests, 0 merges |
| QA formal | **No** | `docs/07-qa-plan.md` nunca aplicado |
| Acceptance del cliente | **No** | sin evidencia |
| Commit de cierre | Parcial | commits `certify:`, `audit:` autogenerados por el mismo agente que implementó |
| Sign-off | **No** | — |

Clasificación: **`INFORMAL_CLOSE`** — las specs se "cierran" mediante informes autogenerados en el mismo hilo de trabajo que produjo el código, sin verificación independiente ni gate automatizado.

---

## 8. Baseline vigente (§74)

```
GA-SPEC-001 spec.md (06-23, 252 líneas)
        ↓ 37c8f0e (06-24 02:55)  consolidación + Fase 8
        ↓ 56cbaf8 (06-24 03:06)  LIVIANAS fuera de alcance
        ↓ b2c3f3c (06-24 15:11)  §14 Feature Flags
        ↓ ac125b2 (06-24 18:38)  §4.9 Trazabilidad Generacional
        ↓ cd64a17 (06-27 17:20)  generalización de la cadena
        =  spec.md 478 líneas  ← BASELINE DOCUMENTAL VIGENTE
```

**El baseline documental vigente es `specs/global-avicola/spec.md` @ `cd64a17` complementado por `docs/02-functional-spec.md`.** Sin embargo, **no gobierna la implementación actual**: la taxonomía de etapas, el design system, la navegación móvil, dos tipos de evento, el motor de alertas, las evidencias y el canal Telegram están fuera de él.

**Recomendación de baseline (§62 del informe principal):** declarar un nuevo baseline `v1.1` que absorba, mediante retro-specs justificadas y fechadas, las 12 funcionalidades sin spec y las 6 desviaciones OUT_OF_SPEC — sin reescribir la historia (§108).

---

## 9. Responsabilidad de las desviaciones (§86)

No se atribuyen a personas. Origen inferible:

| Origen | Casos | Peso |
|---|---|---|
| **PROCESO** | ausencia de constitución ratificada; CI solo en PR con 0 PRs; despliegue automático sin gate; specs cerradas por el mismo agente que implementa | **dominante** |
| **REQUERIMIENTO** | prompts de rediseño de UI/navegación que ordenan cambios de producto sin exigir actualización de spec | alto |
| **SPEC** | ausencia de AC verificables por funcionalidad; contratos de API y modelo de datos no mantenidos | alto |
| **IMPLEMENTACIÓN** | dark mode contra prohibición explícita; paleta sustituida; `sap_document_ref` no enviado | medio |
| **NO DETERMINABLE** | precedencia spec/código de la línea base (commit squash) | — |

---

## 10. Nivel de disciplina (§85)

# NIVEL C — DISCIPLINA INCONSISTENTE

**Justificación.** No es Nivel D ("Spec Development nominal") porque existe evidencia forense inequívoca de especificación previa con tareas, prioridad y archivos objetivo (Fase 8, delta de 30 minutos), decisiones de alcance documentadas antes del código (LIVIANAS) y reconciliación honesta del estado documental con el código real. No es Nivel B porque un tercio de las features auditadas están fuera de spec, hay violaciones explícitas de reglas escritas (dark mode, paleta, emojis), la constitución nunca se ratificó, no existe ninguna puerta de calidad y las specs se cierran con auto-certificaciones sin verificación independiente.

## Veredicto Spec Development

# `CUMPLIMIENTO PARCIAL`
