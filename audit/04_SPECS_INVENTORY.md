# 04 — INVENTARIO DE SPECS

## 1. Marco metodológico instalado

El proyecto usa **GitHub Spec Kit v0.11.4** (`.specify/init-options.json`), integración `copilot`, flujo `speckit.specify → speckit.plan → speckit.tasks → speckit.implement`.

| Artefacto del framework | Estado | Evidencia |
|---|---|---|
| `.specify/templates/` (spec, plan, tasks, checklist, constitution) | presentes, sin usar salvo spec/plan/tasks | `.specify/templates/` |
| `.specify/scripts/bash/` (create-new-feature, setup-plan, setup-tasks…) | presentes | `.specify/scripts/bash/` |
| `.github/prompts/speckit.*.prompt.md` (11) | presentes | `.github/prompts/` |
| `.github/agents/speckit.*.agent.md` (11) | presentes | `.github/agents/` |
| **`.specify/memory/constitution.md`** | **PLANTILLA SIN RELLENAR** — contiene literalmente `[PRINCIPLE_1_NAME]`, `[GOVERNANCE_RULES]`, `**Version**: [CONSTITUTION_VERSION]` | `.specify/memory/constitution.md` |
| `.github/copilot-instructions.md` | 3 líneas genéricas del propio Spec Kit | `.github/copilot-instructions.md` |
| `CLAUDE.md` / `AGENTS.md` | **NO EXISTEN** | búsqueda en todo el repositorio |

**Hallazgo GA-SPD-DEBT-001:** la constitución del proyecto —el documento que en Spec Kit fija los principios no negociables y las reglas de gobierno— **nunca fue ratificada**. Sigue siendo la plantilla vacía. No existe, por tanto, ninguna regla formal escrita que obligue a "no desarrollar sin spec"; la obligación aparece solo como principio #8 en `spec.md §3` ("Spec-Driven Development. Especificar → Planificar → Tareas → Implementar") y como nota en `README.md`.

Corolario metodológico importante para esta auditoría: **la ausencia de constitución impide clasificar los bugfixes fuera de spec como incumplimiento formal** (§63 del encargo: "si las reglas del proyecto exigen spec para bugfix"). No las exigen explícitamente. Se reportan como observación, no como violación.

---

## 2. Inventario de documentos de especificación

23 documentos. Identificadores `GA-SPEC-###` asignados por esta auditoría.

| SPEC | Archivo | Líneas | Primer commit (Git) | Última modificación | Módulo | Objetivo | Estado documental | Implementación relacionada |
|---|---|---|---|---|---|---|---|---|
| GA-SPEC-001 | `specs/global-avicola/spec.md` | 478 | `3c93440` 2026-06-23 21:33 | `cd64a17` 2026-06-27 17:20 | Global | Spec maestra del producto | **VIGENTE** (baseline) | todo el sistema |
| GA-SPEC-002 | `specs/global-avicola/plan.md` | 317 | `3c93440` 2026-06-23 | `37c8f0e` 2026-06-24 | Global | Plan técnico | VIGENTE | arquitectura |
| GA-SPEC-003 | `specs/global-avicola/tasks.md` | 932 | `3c93440` 2026-06-23 | `b2c3f3c` 2026-06-24 15:11 | Global | 90 tareas, fases 0-9 | **VIGENTE / DESACTUALIZADA** | fases 0-9 |
| GA-SPEC-004 | `specs/global-avicola/data-model.md` | 182 | `3c93440` 2026-06-23 | `cd64a17` 2026-06-27 | DB | Modelo de datos | **OBSOLETA (drift)** | 47 tablas |
| GA-SPEC-005 | `specs/global-avicola/research.md` | 110 | `3c93440` 2026-06-23 | `3c93440` | Global | Investigación previa | VIGENTE | — |
| GA-SPEC-006 | `specs/global-avicola/quickstart.md` | 92 | `3c93440` 2026-06-23 | `3c93440` | DevOps | Arranque local | **OBSOLETA** | Makefile roto |
| GA-SPEC-007 | `specs/global-avicola/contracts/api-contract.md` | 195 | `3c93440` 2026-06-23 | `3c93440` | API | Contrato REST | **OBSOLETA (drift)** | 167 endpoints |
| GA-SPEC-008 | `docs/00-product-vision.md` | 153 | `3c93440` 2026-06-23 | `3c93440` | Producto | Visión y valor | VIGENTE | — |
| GA-SPEC-009 | `docs/01-legacy-audit.md` | 926 | `3c93440` 2026-06-23 | `3c93440` | Producto | Auditoría del legacy Lider Pollo | VIGENTE (histórica) | — |
| GA-SPEC-010 | `docs/02-functional-spec.md` | 667 | `3c93440` 2026-06-23 | `37c8f0e` 2026-06-24 | Global | 14 módulos funcionales | **VIGENTE** (fuente principal de requerimientos) | todo |
| GA-SPEC-011 | `docs/03-domain-model.md` | 688 | `3c93440` 2026-06-23 | `cd64a17` 2026-06-27 17:20 | Dominio | Entidades y estados | VIGENTE / parcialmente desfasada | modelos |
| GA-SPEC-012 | `docs/04-technical-plan.md` | 628 | `3c93440` 2026-06-23 | `3c93440` | Arquitectura | Plan técnico | VIGENTE | — |
| GA-SPEC-013 | `docs/05-migration-plan.md` | 111 | `3c93440` 2026-06-23 | `3c93440` | Migración | Migración funcional del legacy | VIGENTE | — |
| GA-SPEC-014 | `docs/06-api-contract.md` | 215 | `3c93440` 2026-06-23 | `3c93440` | API | Contrato de API | **OBSOLETA (drift)** | 167 endpoints |
| GA-SPEC-015 | `docs/07-qa-plan.md` | 168 | `3c93440` 2026-06-23 | `3c93440` | QA | Estrategia de pruebas | **NO IMPLEMENTADA** | 4 test files FE |
| GA-SPEC-016 | `docs/08-browser-compatibility-plan.md` | 97 | `3c93440` 2026-06-23 | `3c93440` | QA | Matriz de navegadores | NO VERIFICADA | Playwright sin CI |
| GA-SPEC-017 | `docs/09-i18n-plan.md` | 137 | `3c93440` 2026-06-23 | `3c93440` | i18n | Plan bilingüe | **IMPLEMENTADA** | 865 claves ES/EN |
| GA-SPEC-018 | `docs/10-sap-integration-strategy.md` | 246 | `3c93440` 2026-06-23 | `3c93440` | SAP | Estrategia de integración | **PARCIALMENTE IMPLEMENTADA** | adapter manual |
| GA-SPEC-019 | `docs/11-ui-ux-design-system.md` | 280 | `3c93440` 2026-06-23 | `3c93440` | UI | Design system obligatorio | **VIOLADA** | paleta teal, dark mode |
| GA-SPEC-020 | `docs/12-approval-workflow.md` | 266 | `3c93440` 2026-06-23 | `3c93440` | Aprobación | Flujo multinivel | **PARCIALMENTE IMPLEMENTADA** | `approval_steps` sin enforcement |
| GA-SPEC-021 | `docs/13-audit-strategy.md` | 198 | `3c93440` 2026-06-23 | `3c93440` | Auditoría | Estrategia de auditoría | **PARCIALMENTE IMPLEMENTADA** | doble mecanismo |
| GA-SPEC-022 | `docs/15-cross-reference-old-vs-new.md` | 508 | `3c93440` 2026-06-23 | `3c93440` | Migración | Cruce legacy ↔ nuevo | VIGENTE | — |
| GA-SPEC-023 | `docs/16-audit-recomendacion-central.md` | 473 | `3c93440` 2026-06-23 | `3c93440` | Producto | Recomendación central | VIGENTE | — |
| — | `docs/14-*.md` | — | **NO EXISTE** | — | — | hueco en la numeración | — |
| — | `docs/17-production-checklist.md` | — | **NO EXISTE** | — | — | **referenciado por GA-SPEC-001 §14 y GA-SPEC-003 Fase 9** | referencia rota |
| — | `docs/18-production-runbook.md` | — | **NO EXISTE** | — | — | entregable de T-090 | pendiente |

**20 de 23 documentos entraron en el mismo "first commit"** (`3c93440`, 2026-06-23 21:33) junto con los 227 archivos del sistema completo. Git no puede demostrar precedencia de la especificación sobre el código para la línea base.

---

## 3. Documentos de estado / auditoría en la raíz (NIVEL C — declaraciones)

No son specs: son informes de estado autogenerados. Se inventarían porque son la principal fuente de afirmaciones no verificadas.

| Archivo | Fecha | Afirmación central | Verificación |
|---|---|---|---|
| `AUDITORIA_COMPLETA.md` | 2026-06-24 | auditoría multidisciplinaria | histórico |
| `GLOBAL_AVICOLA_AUDIT_REPORT.md` | 2026-06-24 | 16 hallazgos → "RE-CERTIFICACIÓN APROBADO" | histórico |
| `GLOBAL_AVICOLA_AUDIT_REPORT_v3.md` | 2026-06-24 | tercera auditoría post-rediseño | histórico |
| `AUDITORIA_MULTIDISCIPLINARIA_V2.md` / `_RESULTADOS.md` | 2026-06-26/27 | "96/100" | no verificable |
| `AUDITORIA_MULTICOMPANIA.md` | 2026-06-29 | aislamiento multiempresa certificado | **REFUTADO** — ver `13_ROLES_AND_SECURITY.md` |
| `AUDITORIA_FUNCIONAL_E2E.md` | 2026-06-29 | "✅ FUNCIONAL — AUDITORÍA IMPLEMENTADA" | **PARCIAL** — doble escritura de auditoría |
| `CERTIFICACION_FUNCIONAL.md` | 2026-06-29 | "71 ops 100 %, 14 SAP, 29/29 rutas, listo para UAT" | **REFUTADO parcialmente** — ver `19_PRODUCTION_GAPS.md` |
| `IMPLEMENTATION_COMPLETE.md` | 2026-06-24 | "5 funcionalidades críticas entregadas", incl. Dark Mode | **OBSOLETO** — dark mode eliminado el 2026-06-28 |
| `INFORME_PROGENITORAS/REPRODUCTORAS/INCUBADORA/BROILER.md` | 2026-06-29 | "100 % SearchSelect", "N SAP" | parcialmente verificado (34 SearchSelect ✔, integración SAP ✘) |
| `WCAG_ACCESSIBILITY_REPORT.md` | 2026-06-24 | "Nivel AA" | NO VERIFICABLE (sin herramienta ni CI) |
| `SESSION_FINAL_REPORT.md`, `NEXT_STEPS.md`, `REDESIGN_SUMMARY.md`, `USER_GUIDE.md`, `VISUAL_GUIDE.md` | jun 2026 | varios | histórico |
| `GUIA_PRUEBAS_EN_VIVO.md` | 2026-07-01 | guía de UAT multiusuario | **contiene 15 credenciales en claro** |
| `prompt-*.md` (4) | 2026-06-25 | prompts de rediseño de navegación/UI | ver §5 |

---

## 4. Calidad de las specs (evaluación por criterio §13)

Criterios evaluados: problema · contexto · objetivo · alcance · fuera de alcance · actores · precondiciones · flujo · reglas · datos · estados · permisos · errores · escenarios negativos · edge cases · dependencias · AC · pruebas.

| SPEC | Criterios cubiertos | Clasificación | Faltantes críticos |
|---|---|---|---|
| GA-SPEC-001 spec.md | 12/18 | **ADECUADA** | escenarios negativos, edge cases, errores, precondiciones, AC verificables por función |
| GA-SPEC-002 plan.md | 9/18 | ADECUADA | AC, pruebas |
| GA-SPEC-003 tasks.md | 11/18 | **ADECUADA** | AC por tarea (solo hay descripción + archivos), criterios de cierre |
| GA-SPEC-004 data-model.md | 8/18 | **INCOMPLETA** | desactualizada frente a 47 tablas reales |
| GA-SPEC-007 / 014 api-contract | 7/18 | **DEFICIENTE** | describe una fracción de los 167 endpoints; sin OpenAPI generado versionado |
| GA-SPEC-010 02-functional-spec | 15/18 | **EXCELENTE** | escenarios negativos, edge cases |
| GA-SPEC-011 03-domain-model | 13/18 | ADECUADA | estados por entidad incompletos |
| GA-SPEC-015 07-qa-plan | 10/18 | INCOMPLETA | nunca ejecutado |
| GA-SPEC-019 11-ui-ux | 12/18 | ADECUADA | *violada por la implementación* |
| GA-SPEC-020 12-approval-workflow | 14/18 | ADECUADA | — |
| GA-SPEC-021 13-audit-strategy | 13/18 | ADECUADA | — |

**Resumen:** 1 EXCELENTE · 7 ADECUADAS · 3 INCOMPLETAS · 1 DEFICIENTE (sobre las 12 evaluadas en profundidad). Las specs restantes son documentos de contexto (visión, legacy, migración) y no requieren AC.

**Ninguna spec contiene criterios de aceptación por funcionalidad.** GA-SPEC-001 §8 aporta 15 AC globales de MVP, todos marcados `✅` **en el propio documento y sin evidencia adjunta**. No existe una sola spec con la estructura AC → test → resultado.

Clasificación global: **`SPEC_PROCESS_DEBT`** — las specs describen el qué, no el criterio verificable de terminación.

---

## 5. Auditoría de prompts (§69)

Cuatro prompts versionados, todos del 2026-06-25:

| Archivo | Qué pide | ¿Menciona spec? | ¿Ordena desarrollo directo? |
|---|---|---|---|
| `prompt-arquitectura-navegacion.md` | rediseño de navegación en 4 macroprocesos, responsive 100 % | No | **Sí** — describe entregables de UI y pide implementarlos |
| `prompt-evaluacion-visual-multimodo.md` | evaluación visual multi-viewport | No | Parcial (evaluación) |
| `prompt-rediseno-flujo-web-mobile.md` | rediseño del flujo web/mobile | No | **Sí** |
| `prompt-refinamiento-navegacion.md` | refinamiento de navegación | No | **Sí** |

**Hallazgo GA-SPD-DEBT-002:** tres de los cuatro prompts ordenan cambios de producto (navegación, jerarquía de menús, flujo del operador) **sin exigir actualización previa de la spec**. Los commits derivados (`5109418`, `8d1a0e4`, `c24dd6a`, `ed8f2ab`, `a9d6941`, `cddffa4`, `3fd61a0`…) modificaron la arquitectura de navegación del producto. `spec.md §6.1` sigue describiendo una *bottom navigation de 5 elementos* (`Home, Lotes, Registrar, KPIs, Pendientes`) que no corresponde a la implementación actual (3 botones + hub en grilla). Los prompts son **evidencia complementaria de desviación metodológica**, no prueba de implementación.
