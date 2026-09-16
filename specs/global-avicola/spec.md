# Global Avícola — Spec-Driven Specification

> **Spec Kit Format**
> **Proyecto:** global-avicola
> **Versión:** 1.1.0
> **Fecha:** 2026-06-22 · enmienda A 2026-09-09 (`OD-16`, ver §15)

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

#### 4.0 Alcance productivo vigente — enmienda A (2026-09-09 · `OD-16`)

El producto soporta **cuatro unidades de negocio productivas completas**, y las cuatro deben
permanecer listas para producto (definidas, implementables, disponibles, configurables por
empresa, cubiertas por seguridad, requisitos, procesos, KPI aplicables, interfaz y certificación):

| Unidad productiva | Código | Dominio funcional |
|---|---|---|
| Progenitoras | `grandparent` | §4.4 |
| Reproductoras | `breeder` | §4.5, §4.6 |
| Incubadora | `hatchery` | §4.7 |
| Pollo de engorde | `broiler` | §4.8 |

```
SUPPORTED PRODUCTIVE BUSINESS UNITS = 4
```

- **Cada empresa / razón social activa o desactiva cada unidad de forma independiente**, dentro de Global Avícola (`company_business_units`; `GA-REM-040` fases 1 y 7). Toda combinación es representable; ninguna unidad es obligatoria ni está siempre encendida. Sin configuración, la unidad está **apagada** (`GA-REM-040 §7.4`).
- La activación por empresa es configuración del plano de control de la aplicación (`OD-09.b`): la empresa como entidad oficial pertenece a SAP; qué unidades opera en la aplicación lo decide Global Avícola. Una futura sincronización de empresas desde SAP no determina esa activación ni concede acceso.
- **Activar no concede**: la concesión de unidad a un usuario es un acto separado (`user_business_units`), dentro de lo habilitado por su empresa efectiva y con segregación (`OD-15`); el `RBAC` es un tercer plano separado.
- **Desactivar prevalece** sobre cualquier concesión existente; la concesión no se borra. El ciclo de vida al reactivar es `BU-D10` (`PENDING_RATIFICATION`); el comportamiento provisional certificado es `GA-REM-040 §6.3`.
- No existe acceso productivo implícito: cero concesiones → conjunto efectivo vacío (`OD-09.c`).
- Unidad de negocio productiva ≠ módulo `RBAC` (`GA-REM-040 §1`): no se renombra uno para hacerlo coincidir con el otro.


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
**Lot type:** `GRANDPARENT` | **BirdTypeEnum:** `grandparent`

- Plan de importación (PO SAP, proveedor internacional, docs sanitarios, aduana, cuarentena)
- Creación de lote de abuelas vinculado a granja/galpón
- Trazabilidad hacia reproductoras y generaciones posteriores
- **Operaciones disponibles (event_type):**

| event_type | Descripción |
|---|---|
| `grandparent_import` | Registro inicial de importación con documentos |
| `farm_inspection` | Inspección de granja antes y durante el ciclo |
| `bird_reception` | Recepción de aves (cantidad, sexo, peso promedio) |
| `bird_distribution` | Distribución a galpones |
| `transport_inspection` | Inspección de transporte en recepciones y despachos |
| `feed_registration` | Registro diario/semanal de alimento consumido |
| `weight_recording` | Pesaje semanal (machos/hembras, semana de vida) |
| `mortality_recording` | Mortalidad diaria por causa y sexo |
| `cull_recording` | Descarte de aves fuera de estándar |
| `vaccination` | Vacunación (vacuna, dosis, vía, lote de vacuna) |
| `medication` | Medicación (fármaco, dosis, duración, motivo) |
| `egg_collection` | Recolección de huevos (fértiles, sucios, rotos, infértiles) |
| `egg_classification` | Clasificación detallada para envío a reproductoras |
| `egg_dispatch` | Despacho de aves/huevos a granjas de reproductoras |
| `bird_exit` | Salida definitiva o descarte del lote |

---

#### 4.5 Breeder Rearing Phase
**Lot type:** `BREEDER` | **Phase:** `CRÍA` (código `rearing` / `cria`)

Un lote BREEDER tiene **dos fases secuenciales**: Cría → Producción, registradas en `lot_phases`. La UI debe mostrar operaciones filtradas según la fase activa.

- Recepción y distribución de aves desde progenitoras o externo
- Ciclo diario/semanal: alimento, pesaje, mortalidad, vacunación, medicación
- Inspección de granja (temperatura, humedad, equipos, camas)
- Registro de transporte en recepciones y transferencias
- Transferencia a fase Producción (cierre de fase + apertura nueva)
- Alertas por desviaciones (peso fuera de curva estándar, mortalidad > umbral)
- **Operaciones disponibles en FASE CRÍA:**

| event_type | Descripción |
|---|---|
| `farm_inspection` | Inspección periódica de granja |
| `bird_reception` | Recepción de aves al inicio de cría |
| `bird_distribution` | Distribución a galpones |
| `transport_inspection` | Inspección de transporte en recepciones |
| `feed_registration` | Registro de alimento |
| `weight_recording` | Pesaje semanal |
| `mortality_recording` | Mortalidad diaria |
| `cull_recording` | Descarte de aves |
| `vaccination` | Vacunación |
| `medication` | Medicación |
| `bird_exit` | Transferencia/salida (cierre de fase cría) |

> **Nota:** La fase CRÍA **no incluye** operaciones de huevos (`egg_collection`, `egg_classification`, `egg_dispatch`). Estas solo están disponibles en fase Producción.

---

#### 4.6 Breeder Production Phase
**Lot type:** `BREEDER` | **Phase:** `PRODUCCIÓN` (código `production` / `produccion`)

- Transición automática desde fase Cría (población inicial heredada)
- Ciclo: postura diaria, clasificación, despacho semanal a incubadora
- Registro de alimento, mortalidad, vacunación continúa
- KPIs clave: % postura, fertilidad, huevos/ave alojada, conversión alimenticia
- **Operaciones disponibles en FASE PRODUCCIÓN:**

| event_type | Descripción |
|---|---|
| `farm_inspection` | Inspección periódica |
| `transport_inspection` | Inspección transporte en despacho de huevos |
| `feed_registration` | Registro de alimento |
| `weight_recording` | Pesaje |
| `mortality_recording` | Mortalidad |
| `cull_recording` | Descarte |
| `vaccination` | Vacunación |
| `medication` | Medicación |
| `egg_collection` | Recolección diaria de huevos (fértiles, sucios, rotos, infértiles) |
| `egg_classification` | Clasificación de huevos para incubación |
| `egg_dispatch` | Despacho de huevos a incubadora (con transporte y guía) |
| `bird_exit` | Salida definitiva del lote (descarte, venta) |

---

#### 4.7 Hatchery / Incubation
**Lot type:** `HATCHERY` | **BirdTypeEnum:** `hatchery` *(requiere agregar este valor al enum backend)*

La incubadora es una etapa independiente que recibe huevos de reproductoras y produce pollitos de un día.

- Recepción de huevos fértiles (trazados al lote de producción origen)
- Carga en incubadoras con parámetros controlados (temperatura, humedad, CO2)
- Ovoscopia para retiro de infértiles y embriones muertos
- Transferencia a nacedoras en día 18
- Registro de nacimiento (pollitos viables, descartados, vacunación in ovo/en planta)
- Despacho de pollitos a granjas de engorde
- KPIs: % eclosión, % nacimiento, rendimiento de incubadora, costo/pollito
- **Operaciones disponibles:**

| event_type | Descripción |
|---|---|
| `egg_reception_hatchery` | Recepción de huevos fértiles (con clasificación y condición) |
| `egg_classification` | Clasificación de huevos recibidos (aptos, no aptos para incubar) |
| `hatchery_inspection` | Inspección de instalaciones, equipos, temperatura/humedad ambiental |
| `transport_inspection` | Inspección transporte de huevos en recepción |
| `incubation_load` | Carga de incubadora (parámetros: temp, humedad, CO2, volteo, cantidad) |
| `ovoscopy` | Ovoscopia (infértiles, embriones muertos tempranos/tardíos, contaminados) |
| `transfer_to_hatcher` | Transferencia a nacedora en día 18 |
| `birth_registration` | Registro de nacimiento (viables, descartados, mortalidad en planta, vacunación) |
| `chick_dispatch` | Despacho de pollitos a granjas de engorde (cantidad, destino, transporte) |

---

#### 4.8 Broiler / Fattening
**Lot type:** `BROILER` | **BirdTypeEnum:** `broiler`

- Recepción de pollitos de un día desde incubadora (trazados al lote origen)
- Distribución a galpones por lote
- Ciclo: alimento (diario), pesaje (semanal), mortalidad (diaria), vacunación
- Descarte de aves fuera de condición
- Cierre de lote y despacho a planta de beneficio
- KPIs: ganancia diaria de peso, conversión alimenticia, viabilidad, uniformidad, EPEF
- **Operaciones disponibles:**

| event_type | Descripción |
|---|---|
| `farm_inspection` | Inspección de granja |
| `bird_reception` | Recepción de pollitos (cantidad, peso promedio, mortalidad inicial) |
| `bird_distribution` | Distribución a galpones |
| `transport_inspection` | Inspección de transporte en recepción de pollitos |
| `feed_registration` | Registro de alimento |
| `weight_recording` | Pesaje semanal |
| `mortality_recording` | Mortalidad diaria |
| `cull_recording` | Descarte de aves fuera de condición |
| `vaccination` | Vacunación |
| `medication` | Medicación |
| `bird_exit` | Salida de aves / despacho a planta de beneficio |
| `lot_closure` | Cierre formal del lote con resumen final |

---

#### 4.9 Generational Traceability (Trazabilidad Generacional)

**Entidades implementadas:** `egg_batches`, `chick_batches`

El sistema registra la trazabilidad completa entre generaciones:

- **EggBatch** — Conecta un lote de Reproductoras (Producción) con un lote de Incubadora. Se crea cuando se despachan huevos desde `breeder_production` (vía `egg_dispatch`) y se reciben en `hatchery` (vía `egg_reception_hatchery`). Almacena: lote origen, lote destino, cantidad despachada, cantidad recibida, fechas.
- **ChickBatch** — Conecta un lote de Incubadora con un lote de Engorde. Se crea cuando se despachan pollitos desde `hatchery` (vía `chick_dispatch`) y se reciben en `broiler` (vía `bird_reception`). Almacena: lote origen (incubadora), lote destino (engorde), egg_batch de referencia, cantidades, fechas.

**Visualización:** El `LotDetailPage` muestra un árbol de trazabilidad (`TraceabilityTree.tsx`) con enlaces entre lotes padre e hijo, permitiendo navegar entre generaciones.

**Reglas:**
- Un EggBatch se crea automáticamente al registrar `egg_dispatch` + `egg_reception_hatchery` para el mismo lote de huevos
- Un ChickBatch se crea automáticamente al registrar `chick_dispatch` + `bird_reception` para el mismo grupo de pollitos
- La trazabilidad es bidireccional: desde un lote se puede ver su origen y destino
- La UI permite crear enlaces manuales entre lotes si la correspondencia automática no es posible

---

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

**Ver especificación completa:** `docs/11-ui-ux-design-system.md`

#### 6.1 Mobile (Operador de Campo — view_type: mobile)
- Formularios usables con una mano, botones ≥44px touch target
- Validación visible en tiempo real con mensajes claros
- Bottom navigation: Home, Lotes, Registrar, KPIs, Pendientes
- Flujo guiado: Seleccionar Lote → Etapa activa → Operaciones disponibles → Formulario → Confirmar
- Sin menús de navegación secundarios en la tarea de registro
- Hamburger/drawer para acceso a secciones secundarias

#### 6.2 Web Administrativa (Supervisor/Admin — view_type: web)
- Dashboard ejecutivo con KPIs por etapa productiva y gráficas Recharts
- Tablas con filtros avanzados, paginación, ordenamiento (TanStack Table)
- Panel de revisión: side-by-side comparación SAP vs operativo
- Panel de aprobación con selección múltiple y acciones en lote
- Visor de auditoría con línea de tiempo por registro

#### 6.3 Design System (obligatorio — no ad-hoc)
- **Paleta:** `#FFFFFF` base, `#F8FAFC` fondo, `#1E3A5F` header/sidebar, `#2563EB` primario, `#3B82F6` hover
- **Estados:** `#16A34A` aprobado, `#EAB308` pendiente, `#DC2626` rechazado, `#2563EB` en proceso
- **Tipografía:** Inter (Google Fonts), semibold para headings, regular para body
- **Componentes reutilizables obligatorios:** `Button`, `Input`, `Select`, `Card`, `Badge`, `Modal`, `Toast`, `DataTable`, `FormField`, `StatusBadge`
- **Iconografía:** lucide-react exclusivamente (sin emojis en UI de producción)
- **Sin dark mode** — diseño corporativo claro siempre
- **Transiciones:** 150ms ease para interacciones, sin animaciones excesivas

#### 6.4 Compatibilidad
- Navegadores: Chrome, Edge, Firefox, Safari, Opera, iOS Safari, Android Chrome (últimas 2 versiones)
- Viewports: 360×640 a 1440×900 (7 breakpoints validados)
- Bilingüe: Español (default) + Inglés, selector de idioma visible en header/login

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
- **Cadena de Aves Livianas (Ponedoras / Huevo Comercial)** — contempla: Reproductoras Livianas (AVI-REP-LIV-01 a 06), Incubadora Ponedoras (AVI-INC-PON-03), Granjas de Ponedoras (AVI-GRA-PON-01 a 06). Procesos distintos: cría de pollonas, producción de huevo consumo, clasificación por tamaño/peso, desalojo de ponedoras. **Arquitectura preparada para esta extensión vía BirdTypeEnum: LAYER.**

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

---

### 14. Feature Flags & Environment Configuration

> **Implementado:** 2026-06-24  
> **Ver:** `docs/17-production-checklist.md` para checklist de activación.

El sistema usa **feature flags** controlados por variables de entorno (`.env`) para habilitar/deshabilitar funcionalidades según el entorno. Esto permite desarrollar y probar en `development` sin dependencias externas (SAP), y activar progresivamente al pasar a `production`.

#### 14.1 Feature Flags Definidos

| Flag | Tipo | Dev | Prod | Descripción |
|------|------|-----|------|-------------|
| `FEATURE_SAP_ENABLED` | `bool` | `false` | `true` | Habilita rutas y servicio de integración SAP. En dev, las rutas `/api/v1/sap/*` no se cargan. Los tests de SAP se skipean automáticamente. |
| `FEATURE_RATE_LIMIT_ENABLED` | `bool` | `false` | `true` | Habilita rate limiting (slowapi). El **default del código es `true`** (fail-safe para artefactos desplegados sin configuración explícita — G-03/T13, 16-sep-2026); `development` lo desactiva explícitamente en `.env` (`false`) y entonces el decorador `@rate_limit()` es un no-op. Además, **en entornos no-dev (`ENVIRONMENT` ∉ {`development`, `test`}) el limitador está siempre activo**: un `false` heredado en el runtime del contenedor no puede desactivar la protección. En prod/UAT aplica los límites configurados (`RATE_LIMIT_LOGIN`, `RATE_LIMIT_GLOBAL`). |
| `FEATURE_AUDIT_ENABLED` | `bool` | `true` | `true` | Habilita registro de auditoría inmutable. Debe estar siempre activo. |
| `FEATURE_REVIEW_ENABLED` | `bool` | `true` | `true` | Habilita workflow de revisión/aprobación. |
| `ENVIRONMENT` | `str` | `development` | `production` | Controla headers HSTS, nivel de logging, CORS restrictivo. |
| `DEBUG` | `bool` | `true` | `false` | SQL echoing, detailed errors. |

#### 14.2 Comportamiento por Entorno

```
┌──────────────────────────────────────────────────────────┐
│ DEVELOPMENT (actual)                                      │
│ • SAP: OFF → rutas no expuestas, tests skipeados         │
│ • Rate Limit: OFF → sin bloqueos en pruebas              │
│ • HSTS: OFF                                              │
│ • CORS: permisivo (localhost)                            │
│ • DEBUG: true → SQL logs, errores detallados             │
├──────────────────────────────────────────────────────────┤
│ PRODUCTION (pendiente activar)                            │
│ • SAP: ON → RealSapAdapter (a implementar)               │
│ • Rate Limit: ON → login 5/min, global 60/min            │
│ • HSTS: ON → max-age=31536000                            │
│ • CORS: restrictivo (solo dominio producción)            │
│ • DEBUG: false                                           │
└──────────────────────────────────────────────────────────┘
```

#### 14.3 Cómo Activar para Producción

1. Cambiar en `.env` del servidor de producción:
   ```env
   ENVIRONMENT=production
   DEBUG=false
   FEATURE_SAP_ENABLED=true
   FEATURE_RATE_LIMIT_ENABLED=true
   ```
2. Implementar `RealSapAdapter` en `backend/app/integrations/sap/adapter.py`
3. Restringir `BACKEND_CORS_ORIGINS` al dominio real
4. Generar `JWT_SECRET_KEY` seguro (no usar el de desarrollo)
5. Seguir checklist completo en `docs/17-production-checklist.md`

#### 14.4 SAP Integration — Estados

| Estado | Descripción | Feature Flag |
|--------|-------------|--------------|
| **OFF** (actual) | Rutas SAP no cargadas. Tests skipeados. | `FEATURE_SAP_ENABLED=false` |
| **MOCK** | `MockSapAdapter`: simula respuestas SAP para testing interno. | `FEATURE_SAP_ENABLED=true` + adapter mock |
| **MANUAL** | `ManualSapAdapter`: genera archivos JSON/CSV para carga manual por analista. | `FEATURE_SAP_ENABLED=true` + adapter manual |
| **REAL** | `RealSapAdapter`: conexión OData/REST a SAP S/4HANA (pendiente implementar). | `FEATURE_SAP_ENABLED=true` + adapter real |

#### 14.5 Pendiente para Producción (Resumen)

> **Ver checklist detallado en:** [`docs/17-production-checklist.md`](../docs/17-production-checklist.md)

| Item | Estado | Responsable |
|------|--------|-------------|
| Activar feature flags en `.env` | ⬜ Pendiente | DevOps |
| Implementar `RealSapAdapter` | ⬜ Pendiente | Backend |
| Restringir CORS origins | ⬜ Pendiente | DevOps |
| Generar JWT_SECRET_KEY seguro | ⬜ Pendiente | DevOps |
| Configurar SSL en BD | ⬜ Pendiente | DevOps |
| Activar rate limiting | ⬜ Pendiente | Backend |
| Verificar health check | ⬜ Pendiente | QA |
| Monitorear logs 24h post-deploy | ⬜ Pendiente | DevOps |

---

### 15. Registro de enmiendas

| Versión | Fecha | Enmienda | Motivo | Autoridad |
|---|---|---|---|---|
| 1.0.0 | 2026-06-22 | — | redacción inicial | — |
| 1.1.0 | 2026-09-09 | A · §4.0 alcance productivo vigente y activación de unidades por empresa | el alcance de cuatro unidades y la activación por razón social solo constaban en una spec de remediación (`GA-REM-040`), no en la spec de producto; el propietario lo declara requisito vigente | `OD-16` |
