# Plan de Migración Funcional — Global Avícola

> **Documento:** 05-migration-plan.md
> **Versión:** 1.0.0
> **Fecha:** 2026-06-22

---

## 1. PRINCIPIO

> **Esto NO es una migración de código. Es una reingeniería conceptual.**

No se migra código del legacy. Se extraen conceptos funcionales, reglas de negocio, flujos de usuario, estructuras de datos y necesidades operativas. Todo se reconstruye con estándares modernos.

---

## 2. MAPA DE EQUIVALENCIA TECNOLÓGICA

| Legacy | Nueva Versión | Tipo de migración |
|---|---|---|
| Flutter 3.16 (Dart) | React 18 (TypeScript) | Conceptual — solo flujos y pantallas |
| Vue 3 / Vuetify 3 | React + TailwindCSS | Conceptual — solo funcionalidad |
| Node.js / Express | FastAPI (Python) | Conceptual — endpoints y lógica |
| TypeORM | SQLAlchemy 2.x | Conceptual — entidades y relaciones |
| PostgreSQL (legacy) | PostgreSQL 15 | Migración de esquema (rediseñado) |
| JWT manual | FastAPI JWT + RBAC | Conceptual — patrón de auth |
| Swagger manual | OpenAPI automático | Automático |
| Sin tests | Pytest + Playwright | Nuevo |
| Sin CI/CD | GitHub Actions | Nuevo |
| jQuery CDN | Sin dependencias CDN | Eliminado |

---

## 3. MAPA DE ENTIDADES

| Legacy (TypeORM) | Nueva (SQLAlchemy) | Cambio |
|---|---|---|
| `crias_lotes` + `produccion_lotes` + `engorde_lotes` | `lots` (unificada con `phase`) | Unificado |
| `crias_pesaje` + `produccion_pesaje` + `engorde_pesaje` | `operational_events` + `weight_records` | Unificado |
| `crias_mortalidad` + `produccion_mortalidad` + `engorde_mortalidad` | `operational_events` + `mortality_records` | Unificado |
| `crias_alimento_granja` + `produccion_alimento_granja` + `engorde_alimento_granja` | `operational_events` + `feed_records` | Unificado |
| `crias_vacunas` + `produccion_vacunas` + `engorde_vacunas` | `operational_events` + `vaccination_records` | Unificado |
| `inspecciones_granjas` | `operational_events` + `inspection_records` | Unificado |
| `users` + `users_roles` + `users_modulos` | `users` + `roles` + `permissions` | Rediseñado (RBAC granular) |
| `*_ordenes_recepcion`, `*_ordenes_salida` | `sap_references` + `operational_events` | Rediseñado |
| (No existe) | `review_batches` | **NUEVO** |
| (No existe) | `approval_steps` + `approval_actions` | **NUEVO** |
| (No existe) | `correction_logs` | **NUEVO** |
| (No existe) | `audit_logs` | **NUEVO** |
| (No existe) | `sap_sync_jobs` + `sap_payloads` + `sap_responses` | **NUEVO** |
| (No existe) | `opening_balances` | **NUEVO** |
| (No existe) | `consolidated_movements` | **NUEVO** |

---

## 4. MAPA DE ENDPOINTS

| Legacy (Express) | Nueva (FastAPI) | Notas |
|---|---|---|
| `POST /user/login` | `POST /api/v1/auth/login` | Rediseñado |
| `POST /user/create-user` | `POST /api/v1/users` | Rediseñado |
| `GET /consult_granjas/get-granjas` | `GET /api/v1/masters/farms` | Rediseñado |
| `POST /granjas/set-alimento` | `POST /api/v1/operations/feed` | Rediseñado |
| `POST /granjas/set-pesaje` | `POST /api/v1/operations/weight` | Rediseñado |
| `POST /granjas/set-mortalidad` | `POST /api/v1/operations/mortality` | Rediseñado |
| `POST /granjas/set-vacuna` | `POST /api/v1/operations/vaccination` | Rediseñado |
| `POST /incubadora/set-recepcion` | `POST /api/v1/operations/egg-reception` | Rediseñado |
| `POST /incubadora/set-incubacion` | `POST /api/v1/operations/incubation-load` | Rediseñado |
| `POST /incubadora/set-nacimiento` | `POST /api/v1/operations/birth` | Rediseñado |
| (No existe) | `POST /api/v1/review/batches` | **NUEVO** |
| (No existe) | `POST /api/v1/approvals/approve` | **NUEVO** |
| (No existe) | `POST /api/v1/corrections` | **NUEVO** |
| (No existe) | `GET /api/v1/audit` | **NUEVO** |
| (No existe) | `POST /api/v1/sap/sync` | **NUEVO** |

---

## 5. REGLAS DE NEGOCIO A MIGRAR (CONCEPTUAL)

| Regla detectada en legacy | Acción |
|---|---|
| StatusEnum: ACTIVO / CERRADO | Expandir a 13 estados de registro operativo |
| EtapaGranjaEnum: CRIA / PRODUCCION / ENGORDE | Agregar INCUBACION, ABUELAS |
| Zona horaria UTC | Mantener |
| Eliminación vía endpoints `delete-*` | Reemplazar por soft delete con auditoría |
| JWT requerido en todas las rutas | Mantener + RBAC granular |
| `id_sap` en entidades | Rediseñar como `sap_references` con tabla dedicada |
| Distribución de aves por galpón | Mantener lógica, rediseñar modelo |

---

## 6. ESTRATEGIA DE CORTE (BIG BANG VS INCREMENTAL)

**Estrategia recomendada: Incremental por módulo**

1. **Fase 0:** Setup + Auth + Maestros (sin afectar operación legacy)
2. **Fase 1:** Gestión de Lotes + Activación Manual (en paralelo con legacy)
3. **Fase 2:** Registro Operativo (convivencia con legacy — ambos sistemas registran)
4. **Fase 3:** Revisión y Aprobación (el diferenciador — no existe en legacy)
5. **Fase 4:** Integración SAP (convivencia hasta validar)
6. **Fase 5:** Corte final — legacy se desactiva, Global Avícola es el sistema único

---

## 7. PLAN DE CONTINGENCIA

- El legacy se mantiene operativo hasta que Global Avícola esté completamente validado
- Ambos sistemas pueden coexistir durante la transición
- Los datos del legacy pueden exportarse para carga inicial en Global Avícola
- Si un módulo nuevo falla, se revierte al legacy para ese módulo específico
- La activación manual de lotes permite empezar con datos reales desde cualquier punto
