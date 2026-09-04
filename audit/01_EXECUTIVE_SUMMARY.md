# 01 — RESUMEN EJECUTIVO

> **Auditoría integral end-to-end de Global Avícola**
> **Fecha de auditoría:** 2026-09-02
> **Commit auditado:** `bfccdfb` (HEAD, rama `main`, 2026-07-08 20:35)
> **Alcance:** repositorio completo — código, base de datos, API, frontend, infraestructura, specs, git.
> **Restricción aplicada:** no se modificó código productivo, no se ejecutaron pruebas contra la base de datos en la nube, no se hizo deploy.

---

## VEREDICTO FUNCIONAL

# `INTEGRACIÓN INCOMPLETA`

## VEREDICTO SPEC DEVELOPMENT

# `CUMPLIMIENTO PARCIAL`

**Madurez del producto: NIVEL 3 — INTEGRACIÓN** (no es Nivel 4 "Beta operativa" porque 5 de 24 pantallas están rotas por defectos confirmados y 2 reglas de negocio centrales no operan).

---

## 1. Qué es Global Avícola

Plataforma web/mobile-first de **gestión operativa avícola** que actúa como capa auxiliar de SAP S/4HANA. Cubre la cadena productiva completa —progenitoras (abuelas), reproductoras cría, reproductoras producción, incubación y engorde— con captura en campo, revisión, corrección, aprobación multinivel, auditoría y envío consolidado a SAP.

- **Backend:** FastAPI + Python 3.11 + SQLAlchemy 2 async + Pydantic v2 + Alembic. **167 endpoints** REST.
- **Frontend:** React 19 + Vite 8 + TypeScript 6 + TailwindCSS 4 + Zustand + react-i18next. **24 páginas / 36 rutas**.
- **Base de datos:** PostgreSQL, **47 tablas**, **21 migraciones**, cadena Alembic íntegra (1 head, 1 base).
- **Despliegue:** Docker Hub `:latest` + Docker Compose + Nginx + Watchtower (auto-update cada 60 s) en `avicola.globaldv.net`. Postgres externo en IP pública.
- **Canal adicional:** Telegram Mini App (bot lanzador + SDK en el frontend).

## 2. Cuánto está realmente construido

| Dimensión | Cifra | Base de cálculo |
|---|---|---|
| **Cobertura funcional E2E** | **21,4 %** | 12 requerimientos completos E2E / 56 requerimientos consolidados |
| Cobertura con implementación sustancial (completo + parcial) | **71,4 %** | 40/56 |
| Endpoints backend implementados | **167** | enumerados del esquema OpenAPI en runtime |
| Endpoints consumidos por el frontend | **133** (80 %) | — |
| Endpoints huérfanos (sin ningún consumidor) | **34** (20 %) | — |
| Pantallas integradas sin defecto confirmado | **10 / 24** (42 %) | — |
| Pantallas parciales | **9 / 24** (37 %) | — |
| Pantallas rotas (defecto confirmado) | **5 / 24** (21 %) | — |
| Procesos de negocio 100 % cubiertos | **0 / 15** | — |
| Tests unitarios frontend ejecutados | **61 / 61 PASS** | `vitest run`, verificado hoy |
| Tests backend | **76 recolectados, 0 ejecutables sin BD** | política de auditoría: no escribir en BD productiva |
| Cobertura i18n ES/EN | **865 / 865 claves, paridad 100 %** | verificado programáticamente |
| Deriva modelo ORM ↔ migraciones | **0 columnas, 0 tablas** | verificado programáticamente |

## 3. Lo que hoy es utilizable

Funciona de extremo a extremo y puede usarse:

1. **Login / refresh JWT** y sesión dual móvil/web.
2. **Registro de operaciones** desde el formulario guiado (25 tipos de evento, 34 selectores con búsqueda) → persiste en `operational_events` + submovimientos.
3. **Devolución al operador** con observaciones.
4. **Aprobación / rechazo individual y por lote** desde el Panel de Aprobación.
5. **Consolidación de aprobados** y generación de payload SAP con bitácora e idempotencia.
6. **Bloqueo de edición de registros enviados a SAP** (BR-15).
7. **Ningún dato llega a SAP sin aprobación** (BR-13).
8. **Exportación Excel/PDF** de KPIs (cliente, sin backend).
9. **Bilingüe ES/EN completo**.

## 4. Lo que está roto (12 bloqueadores vivos en producción)

| # | Bloqueador | Evidencia |
|---|---|---|
| P0-1 | **Registrar mortalidad lanza error 500.** `get_current_bird_balance` se invoca sin estar importado y con 3 argumentos frente a una firma de 2. La mortalidad diaria es la operación más frecuente del negocio. | `backend/app/operations/service.py:242` vs `backend/app/operations/validators.py:21` |
| P0-2 | **Las correcciones no se aplican.** `create_correction` guarda el registro de auditoría y cambia el estado a `corrected`, pero nunca escribe el valor corregido en el evento. El dato erróneo es el que se aprueba y se consolida hacia SAP. | `backend/app/corrections/service.py:37-58` |
| P0-3 | **No existe control de permisos en el backend.** La tabla `permissions` y el enum `PermissionAction` se pueblan por seeds pero **ningún endpoint los consulta**. Solo se comprueba `is_super_admin`. Cualquier usuario autenticado puede aprobar, borrar maestros o exportar a SAP. | ausencia de `require_permission` en todo `backend/app/`; `backend/app/auth/security.py:107-118` |
| P0-4 | **Escalada de privilegios por refresh de token.** `refresh_token()` emite un token sin `view_type`, `company_id` ni `role_id`; el frontend reconstruye el usuario desde el token y aplica `view_type: 'web'` por defecto. A los 30 minutos, un operador móvil obtiene las rutas web (usuarios, aprobaciones, SAP, auditoría). Sin RBAC de backend, esos endpoints responden. | `backend/app/auth/service.py:72`; `frontend/src/stores/auth.store.ts:85-101`; `frontend/src/App.tsx:63-67` |
| P0-5 | **5 pantallas rotas por incompatibilidad de contrato FE↔BE.** Seis llamadas usan `limit=200` contra endpoints con tope `le=100` → HTTP 422. Afecta Detalle de Lote, Detalle de Revisión, Formulario de Corrección, Usuarios y Reportes, además del selector de compañía. | `frontend/src/pages/lots/LotDetailPage.tsx:45`, `pages/review/ReviewDetail.tsx:32`, `pages/review/CorrectionForm.tsx:27`, `pages/users/UsersPage.tsx:21`, `pages/reports/ReportsPage.tsx:19`, `stores/company.store.ts:38` vs `backend/app/*/router.py` (`le=100`) |
| P0-6 | **Las evidencias adjuntas se pierden en cada despliegue.** Se escriben en `/app/media` dentro del contenedor y no hay ningún volumen montado; Watchtower recrea el contenedor automáticamente. | `backend/app/operations/router.py:19,166`; `docker-compose.yml` (sin `volumes` en `backend`) |
| P0-7 | **No hay integración SAP real.** `get_adapter()` devuelve siempre `ManualSapAdapter`, que escribe un JSON en `/tmp` y marca los eventos como `sent_to_sap` con un identificador ficticio `MANUAL-…`. `FEATURE_SAP_ENABLED=true` está activo en producción desde el último commit. | `backend/app/integrations/sap/service.py:34-38` (`# TODO`), `adapter.py:80-105` |
| P0-8 | **Credenciales de administrador conocidas y publicadas.** `admin / admin123` (Super Administrador) y 14 usuarios más figuran en `GUIA_PRUEBAS_EN_VIVO.md` y en los seeds, contra un entorno público, y el rate limiting está **desactivado** en producción. | `GUIA_PRUEBAS_EN_VIVO.md:13-40`; `backend/seeds/dev_seeds.py:154`; `docker-compose.yml` (sin `FEATURE_RATE_LIMIT_ENABLED`) |
| P0-9 | **El cambio de contraseña no funciona y anuncia éxito.** `UserUpdate` no declara el campo `password`; Pydantic lo descarta y `update_user` no modifica nada, pero la UI muestra "Contraseña actualizada". Ningún usuario puede cambiar su contraseña tras el alta. | `backend/app/auth/schemas.py:42-49`; `auth/service.py:130-142`; `frontend/src/pages/users/ProfilePage.tsx:24-26` |
| P0-10 | **Elusión de la segregación de funciones (BR-14).** `complete_review()` aprueba con `approval_levels <= 1` sin llamar a `validate_segregation`, que sí se aplica en `ApprovalService.approve()`. El autor puede aprobar su propio registro. | `backend/app/review/service.py:196-234` vs `:301-309` |
| P0-11 | **Trazabilidad generacional inoperante.** La creación automática de `EggBatch`/`ChickBatch` empareja despacho y recepción **por el mismo `lot_id`**, cuando por definición son lotes distintos: no se crea ningún vínculo entre generaciones. | `backend/app/operations/service.py:127-176, 190-228` |
| P0-12 | **Ninguna puerta de calidad entre commit y producción.** Los workflows de test solo se disparan en `pull_request` y el repositorio tiene **0 pull requests en 171 commits**; cada `push` a `main` publica `:latest` y Watchtower despliega en ≤ 60 s. | `.github/workflows/backend-ci.yml:8-12`; `git log --merges` → 0; commit `9004f3a` |

## 5. Se respetó Spec Development?

**Parcialmente, y de forma desigual.**

- **Sí hubo spec-first real** en la Fase 8: las tareas T-067…T-083 se escribieron en `tasks.md` el 2026-06-24 a las **02:55** (`37c8f0e`) y se implementaron entre las **03:25 y 03:51** (`d3f37f8`, `b3a0c56`, `2d06024`). Es evidencia inequívoca de especificación previa.
- **La línea base completa (227 archivos: docs, specs, backend y frontend) entró en un único "first commit"** el 2026-06-23. Git no permite demostrar orden spec→código para ~90 % del sistema.
- **Feature flags (spec §14)** se documentaron **en el mismo commit** que los implementó (`b2c3f3c`) → spec retro-documentada.
- **Trazabilidad generacional** se implementó a las 03:51 del 2026-06-24 y se especificó a las 18:38 del mismo día → **CODE_BEFORE_SPEC**.
- **8 funcionalidades relevantes no tienen ni una sola mención en spec ni en docs**: `egg_reception_classification`, `hatchery_purpose`, `egg_storage`, motor de alertas, evidencias adjuntas, patrón `SearchSelect`, Telegram Mini App y bot, tabla `reversals`.
- **Violación explícita de la spec**: `spec.md §6.3` dice literalmente "**Sin dark mode** — diseño corporativo claro siempre". Se implementó modo oscuro en **24 commits** entre el 2026-06-25 y el 2026-06-28 y luego se eliminó. La paleta corporativa obligatoria (`#2563EB`) fue sustituida por una paleta teal copiada de otro proyecto ("atenea-front") sin actualizar la spec.
- **Cero pull requests y cero merges** en 171 commits: los workflows de CI solo se disparan en `pull_request`, por lo que **nunca se han ejecutado**. Cada push a `main` publica imagen y Watchtower la despliega en producción en menos de 60 segundos, sin tests, sin lint y sin aprobación.
- Al menos **7 documentos declaran "COMPLETO / CERTIFICADO / listo para UAT"** sin evidencia verificable; `CERTIFICACION_FUNCIONAL.md` lista rutas (`/approval-steps`, `/corrections`) que no existen en el router.

**Tasas calculadas** (30 features auditadas): Spec Compliance 23 %, Trazabilidad completa 17 %, Cobertura de AC 40 %, AC con test verificable 7 %, Out-of-spec 27 %. **Disciplina Spec Development: NIVEL C — INCONSISTENTE.**

## 6. Puede continuar la arquitectura actual?

**Sí.** La arquitectura es sólida y no requiere reescritura:

- Modelo de evento unificado (`operational_events` + submovimientos) bien diseñado, sustituye 12+ tablas legacy.
- Migraciones y modelos **perfectamente sincronizados** (0 desviaciones sobre 47 tablas).
- Separación por módulos de dominio coherente (auth, masters, lots, operations, review, corrections, audit, reports, dashboard, integrations/sap).
- Adapter pattern de SAP correctamente aislado — solo falta la implementación real.
- TypeScript compila sin errores; i18n íntegro; 0 mocks y 0 datos falsos en el código.

Los problemas son **de cierre e integración, no de diseño**. La recomendación es cerrar brechas, no reconstruir.

## 7. Cuál es la deuda más importante

1. **Ausencia total de enforcement de permisos** (el modelo RBAC existe pero es decorativo).
2. **Pipeline sin puertas de calidad**: CI nunca ejecutado + despliegue automático a producción.
3. **Capa de servicios/hooks del frontend muerta**: 12 servicios y 9 hooks (~600 LOC) que ninguna página usa; todas las páginas llaman `api.get/post` con URLs literales — de ahí los desajustes de contrato.
4. **Doble mecanismo de auditoría activo** (listeners SQLAlchemy + helpers de servicio) → registros duplicados.
5. **`sap_document_ref` nunca se envía desde el frontend** → BR-11, BR-18 y el reporte comparativo SAP quedan inertes.

## 8. Orden de trabajo recomendado

```
PASO 1  Congelar despliegue automático y restablecer puertas de calidad (CI en push, quitar :latest+watchtower)
PASO 2  Corregir los 12 bloqueadores P0
PASO 3  Implementar enforcement RBAC en backend + guard de rol en frontend
PASO 4  Reparar contratos FE↔BE (límites, filtros ignorados, sap_document_ref, idempotency_key)
PASO 5  Persistencia de evidencias (volumen) y decisión sobre SAP real vs manual documentado
PASO 6  Ejecutar por primera vez la suite backend contra una BD desechable y corregir lo que falle
PASO 7  Regularizar Spec Development (retro-specs justificadas + política NO SPEC = NO DEVELOPMENT)
PASO 8  Observabilidad mínima y deuda no bloqueante
```

---

**Regla de gobierno propuesta y de aplicación inmediata:**

# NO SPEC = NO DEVELOPMENT
