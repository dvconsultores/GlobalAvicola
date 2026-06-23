# Global Avícola — Spec-Driven Specification

> **Spec Kit Format**
> **Proyecto:** global-avicola
> **Versión:** 1.0.0
> **Fecha:** 2026-06-22

---

## SPEC: Global Avícola — Plataforma de Gestión Operativa Avícola Integrada con SAP

### 1. Overview

**Global Avícola** es una plataforma empresarial web/mobile-first para la gestión operativa integral del ciclo productivo avícola (abuelas, reproductoras cría, reproductoras producción, incubación y engorde), funcionando como capa auxiliar operativa de SAP. SAP mantiene el control administrativo/contable; Global Avícola gestiona la captura en campo, revisión, corrección, aprobación, consolidación y envío controlado a SAP con trazabilidad y auditoría completas.

### 2. Tech Stack

- **Frontend:** React 18+ / Vite / TypeScript / TailwindCSS (sin CDN) / react-i18next
- **Backend:** FastAPI / Python 3.11+ / SQLAlchemy 2.x (async) / Alembic / Pydantic v2
- **Database:** PostgreSQL 15+
- **Auth:** JWT + RBAC (roles y permisos granulares, multi-compañía con `company_id` isolation, Super Admin scope `all`)
- **Infrastructure:** Docker / Docker Compose / Nginx / GitHub Actions
- **QA:** Pytest / Playwright (cross-browser + mobile viewports)
- **SAP Integration:** Adapter pattern for SAP S/4HANA (OData/SOAP/IDoc, manual initial, ready for OData REST + API Business Hub)

### 3. Core Principles

1. **SAP es el sistema principal.** Global Avícola es auxiliar operativo.
2. **Nada va a SAP sin aprobación.** Revisión → Corrección → Aprobación → Consolidación → SAP.
3. **Auditoría total.** Cada acción queda registrada (quién, qué, cuándo, valor anterior/nuevo, motivo).
4. **Corrección auditada.** Valor original + valor corregido siempre visibles.
5. **Mobile-first real.** Diseñado para el operador de campo en teléfono.
6. **Diseño corporativo blanco/azul.** Profesional, limpio, de alto impacto.
7. **Bilingüe ES/EN.** Desde el inicio, sin hardcodear textos.
8. **Spec-Driven Development.** Especificar → Planificar → Tareas → Implementar.

### 4. Functional Domains

#### 4.1 Authentication & User Management
- Login JWT con refresh tokens
- RBAC: Roles (Super Admin, Admin, Supervisor, Aprobador, Operador, Veterinario, Analista SAP, Auditor, Consulta)
- Permisos por módulo, acción (CRUD + revisar, corregir, aprobar, rechazar, enviar SAP) y alcance (empresa/granja)
- Gestión de usuarios, roles, permisos

#### 4.2 Masters / Catalogs
- Companies, Farms, Houses, Hatcheries, Incubators, Hatchers
- GeneticLines, Breeds, BirdTypes, ProductivePhases
- Suppliers, FeedTypes, Vaccines, Medications
- MortalityCauses, CullCauses, Transports, ProcessingPlants
- RejectionReasons, CorrectionTypes
- Statuses (13 estados de registro operativo)

#### 4.3 SAP References & Integration
- Importación de referencias SAP: Purchase Orders, Transfer Orders, Centers, Warehouses, Materials, Vendors, Batches
- Capa de abstracción desacoplada (Adapter pattern)
- Modo inicial: manual (upload CSV/JSON)
- Diseñado para API/OData/BAPI/RFC futuro
- Idempotencia garantizada (SHA-256 hash)
- Bitácora de sincronización (SapSyncJob, SapPayload, SapResponse)

#### 4.4 Grandparent Importation
- Plan de importación con documentos sanitarios/aduana
- Creación de lote de abuelas
- Trazabilidad a generaciones posteriores

#### 4.5 Breeder Rearing Phase
- Registro de lote de cría
- Recepción y distribución de aves (machos/hembras, peso, galpón)
- Registro de alimento, pesaje (semanal), mortalidad (diaria), vacunación, medicación
- Inspección de granja (condiciones, equipos, temperatura, humedad)
- Salida de aves (transición a producción)
- Alertas por desviaciones (peso, mortalidad, consumo)

#### 4.6 Breeder Production Phase
- Transición desde cría (cierre/apertura, población inicial)
- Registro de postura/recolección de huevos (fértiles, sucios, rotos, infértiles, descartados)
- Clasificación de huevos
- Despacho de huevos a incubadora
- Salida de aves
- KPIs: % postura, fertilidad, huevos/ave alojada

#### 4.7 Hatchery / Incubation
- Recepción de huevos fértiles
- Carga de incubación (temperatura, humedad, CO2, volteo)
- Ovoscopia (infértiles, embriones muertos)
- Transferencia a nacedora
- Nacimiento (pollitos viables, descartados, vacunación en planta)
- Despacho de pollitos a engorde
- KPIs: % eclosión, % nacimiento, rendimiento

#### 4.8 Broiler / Fattening
- Recepción de pollitos
- Registros operativos (alimento, pesaje, mortalidad, vacunación)
- Cierre y despacho a planta de beneficio
- KPIs: ganancia diaria, conversión alimenticia, viabilidad, uniformidad

#### 4.9 Manual Lot Activation (Opening Balance)
- Activar lotes existentes antes de la implantación
- Datos: fase actual, edad, población, mortalidad acumulada, peso, producción acumulada
- Saldos iniciales documentados
- Auditoría de activación manual
- Reporte de apertura (opening balance)

#### 4.10 Review Center / Approval Workflow
**CENTRAL MODULE:**
- Bandeja de revisión con filtros (granja, lote, fecha, operador, etapa, tipo, estado)
- Corrección auditada (valor original + corregido + motivo)
- Devolución al operador con observaciones
- Aprobación multinivel configurable (1, 2 o 3 niveles)
- Aprobación individual, por lote, por período
- Rechazo con motivo obligatorio
- Consolidación de movimientos aprobados
- Preparación para envío a SAP

#### 4.11 Internal Audit
- Registro inmutable de cada acción
- Vista de auditoría para roles autorizados
- Trazabilidad completa por registro (línea de tiempo)
- Corrección: original + corregido + responsable + fecha + motivo
- Aprobación: responsable + fecha + versión aprobada
- Rechazo: responsable + fecha + motivo
- Envío SAP: payload + respuesta + ID SAP + estado

#### 4.12 Reports & KPIs
- Mortalidad diaria/acumulada, viabilidad
- Peso promedio vs estándar, uniformidad
- Consumo de alimento, conversión alimenticia
- Producción de huevos, fertilidad, eclosión, nacimiento
- Rendimiento de incubadora y engorde
- Diferencias SAP vs App
- Auditoría por usuario/lote/documento SAP
- Exportación Excel/PDF

### 5. Business Rules (Non-Negotiable)

| ID | Rule |
|----|------|
| BR-01 | Mortalidad no puede exceder saldo disponible de aves |
| BR-02 | Despacho de huevos no puede exceder disponible |
| BR-03 | Carga de incubadora no puede exceder huevos recibidos |
| BR-04 | Despacho de pollitos no puede exceder nacidos viables |
| BR-05 | Cierre de lote requiere resumen final |
| BR-06 | Fechas operativas no pueden ser anteriores a activación del lote |
| BR-07 | Movimientos requieren lote activo |
| BR-08 | Movimientos requieren granja/galpón cuando aplique |
| BR-09 | Toda corrección es auditada (original + corregido) |
| BR-10 | Eliminación es lógica con trazabilidad (nunca física) |
| BR-11 | Documentos SAP no se duplican |
| BR-12 | Envíos a SAP son idempotentes |
| BR-13 | Ningún dato va a SAP sin aprobación |
| BR-14 | Operador no aprueba su propia carga (segregación) |
| BR-15 | Registros enviados a SAP no se editan directamente |
| BR-16 | Ajustes post-SAP requieren reverso, corrección auditada o nuevo movimiento autorizado |

### 6. UI/UX Requirements

- **Mobile-first:** Formularios usables con una mano, botones >44px, validación visible
- **Web ejecutiva:** Dashboard, tablas con filtros, panel de revisión/aprobación
- **Paleta:** Blanco (#FFF) base, Azules corporativos (#1E3A5F, #2563EB, #3B82F6)
- **Estados:** Verde (aprobado), Amarillo (pendiente), Rojo (rechazado), Azul (en proceso)
- **Bilingüe:** Español (default) + Inglés, selector de idioma visible
- **Compatibilidad:** Chrome, Edge, Firefox, Safari, Opera, iOS Safari, Android Chrome
- **Viewports:** 360×640 a 1440×900

### 7. Non-Functional Requirements

- **Performance:** Carga móvil < 3s en 4G, formularios < 60s para completar
- **Security:** JWT + RBAC, CORS restringido, validación Pydantic, sanitización, rate limiting
- **Auditability:** 100% de acciones registradas, logs inmutables
- **Testability:** > 80% coverage backend, > 70% frontend
- **i18n:** 100% textos visibles traducidos (ES/EN)
- **Browser:** Certificado en 8+ navegadores/plataformas

### 8. Acceptance Criteria (MVP)

1. ✅ Operador registra datos desde móvil → estado "Registrado"
2. ✅ Supervisor revisa en Centro de Revisión Operativa
3. ✅ Usuario autorizado corrige (original conservado, auditado)
4. ✅ Aprobador aprueba o rechaza (con motivo)
5. ✅ Datos aprobados se consolidan
6. ✅ Datos consolidados listos para SAP
7. ✅ Envío a SAP auditado (payload + respuesta)
8. ✅ Errores SAP registrados con reintento
9. ✅ Idempotencia: sin envíos duplicados
10. ✅ Trazabilidad completa de cualquier registro
11. ✅ Diseño blanco/azul profesional mobile + web
12. ✅ Funciona en español e inglés
13. ✅ Compatible con navegadores y viewports especificados
14. ✅ Aislamiento multi-compañía: usuario de Empresa A no ve datos de Empresa B
15. ✅ Super Admin ve todas las compañías; usuario regular solo la suya

### 9. Out of Scope (v1)

- Reemplazar SAP como sistema contable
- App nativa (iOS/Android) — se usa PWA si aplica
- Módulo de nómina/RRHH, facturación electrónica
- Integración con otros ERPs
- Machine Learning / IA predictiva
- IoT / Sensores en tiempo real
- Notificaciones push (v2)

### 10. Migration Strategy from Legacy

- **NO migrar código.** Extraer conceptos, reglas, flujos.
- **NO copiar arquitectura Flutter/Vue/Node.** Rediseñar desde cero.
- **NO heredar deuda técnica.**
- **Fuente funcional:** Repos legend (`app_liderpollo`, `app_liderpollo_fronend`, `app_liderpollo_backend`)
- **Ver:** [docs/01-legacy-audit.md](../docs/01-legacy-audit.md) para análisis completo.

### 11. Project Structure

```
global-avicola/
├── README.md
├── Makefile
├── docker-compose.yml
├── .env.example
├── .github/workflows/
├── docs/          (14 documentos de especificación)
├── specs/         (Spec Kit specification)
├── backend/       (FastAPI + PostgreSQL)
└── frontend/      (React + Vite + TailwindCSS)
```

### 12. Deliverables

1. ✅ `README.md`
2. ✅ `docs/00-product-vision.md`
3. ✅ `docs/01-legacy-audit.md`
4. ✅ `docs/02-functional-spec.md`
5. ✅ `docs/03-domain-model.md`
6. ✅ `docs/04-technical-plan.md`
7. ✅ `docs/10-sap-integration-strategy.md`
8. ✅ `docs/12-approval-workflow.md`
9. ✅ `docs/13-audit-strategy.md`
10. ✅ `specs/global-avicola/spec.md` (este documento)
11. ⬜ `docs/05-migration-plan.md`
12. ⬜ `docs/06-api-contract.md`
13. ⬜ `docs/07-qa-plan.md`
14. ⬜ `docs/08-browser-compatibility-plan.md`
15. ⬜ `docs/09-i18n-plan.md`
16. ⬜ `docs/11-ui-ux-design-system.md`
17. ⬜ Plan técnico generado por `/speckit.plan`
18. ⬜ Tareas generadas por Spec Kit

### 13. Next Steps

1. Completar documentos restantes
2. Ejecutar `/speckit.plan` para generar plan técnico detallado
3. Generar tareas derivadas
4. Iniciar implementación Fase 0 (setup del proyecto)
5. **NO codificar funcionalidad antes de completar especificación y plan**
