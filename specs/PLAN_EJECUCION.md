# PLAN DE IMPLEMENTACIÓN EJECUTIVO — Global Avícola v2

**Documento:** plan-ejecucion-rediseño.md  
**Versión:** 1.0.0  
**Fecha:** 2026-06-24  
**Estado:** EN EJECUCIÓN  

**Objetivo:** Transformar Global Avícola v2 de un sistema 60% incompleto a una solución de **clase mundial en 10 semanas**.

---

## I. VISIÓN DE TRANSFORMACIÓN

### Situación Actual
- **Frontend:** 60% completo, sin diferenciar mobile/web, UI no optimizada
- **Backend:** 40% completo, faltan sincronización SAP, KPIs, trazabilidad
- **Diseño:** Responsive pero no "mobile-first", UX no operativa
- **Funcionalidad avícola:** Operaciones básicas pero sin trazabilidad generacional

### Situación Objetivo (10 semanas)
- **Frontend:** 100% completo, vistas mobile y web diferenciadas, UX profesional
- **Backend:** 100% completo, SAP sync automática, KPIs completos, trazabilidad
- **Diseño:** Mobile y web optimizados, componentes reutilizables
- **Funcionalidad avícola:** Trazabilidad integral, todas las etapas, reportes analíticos

### Impacto Esperado
✅ Software avícola **competitivo globalmente**  
✅ Integración **real con SAP**  
✅ **Trazabilidad generacional** completa  
✅ **UX profesional** para operadores  
✅ **Reportes de clase mundial**  

---

## II. DESGLOSE DE SPRINTS (10 semanas = 70 días hábiles)

### SPRINT 1: Arquitectura & Estabilización (Semana 1-2, Jun 24 - Jul 8)

**Objetivo:** Sentar las bases para el resto del proyecto.

#### Frontend
- **T-F101:** Crear estructura mobile vs web (routing condicional)
  - Crear hook `useResponsive.ts` 
  - Crear `<MobileShell>` y `<WebShell>`
  - Actualizar `App.tsx` con routing condicional
  - Duración: 3 días
  - Responsable: Frontend Lead

- **T-F102:** Crear componentes base mobile
  - `MobileLayout.tsx`, `MobileBottomNav.tsx`, `MobileHeader.tsx`
  - `MobileForm.tsx`, `MobileCard.tsx`, `MobileKPI.tsx`
  - Duración: 4 días
  - Responsable: Senior Frontend Dev

- **T-F103:** Crear componentes base web mejorados
  - `WebLayout.tsx` (update), `WebTable.tsx` (new), `WebDashboard.tsx` (new)
  - Mejorar `WebSidebar.tsx`, `WebHeader.tsx`
  - Duración: 3 días
  - Responsable: Senior Frontend Dev

- **T-F104:** Diseñar mobile en Figma (mockups)
  - Home, Registrar, Pending, Perfil
  - Componentes: Formulario, Card, KPI, Bottom Nav
  - Duración: 3 días (paralelo)
  - Responsable: UI/UX Designer

#### Backend
- **T-B101:** Completar endpoints operativos faltantes
  - `POST /operations/events/` (create con validaciones)
  - `GET /operations/events/{id}/` (detail con relacionamientos)
  - `PATCH /operations/events/{id}/` (update con auditoría)
  - `GET /lots/{id}/operations/` (list)
  - Duración: 4 días
  - Responsable: Backend Lead

- **T-B102:** Implementar servicio de KPIs básicos
  - Mortalidad por lote y fase
  - Peso promedio por semana
  - Consumo alimento por día
  - Duración: 3 días
  - Responsable: Backend Dev

- **T-B103:** Crear modelos EggBatch y ChickBatch (preparación)
  - Diseño de tablas en diagram
  - Campos, relaciones, índices
  - Duración: 2 días
  - Responsable: Database Architect

#### Testing & QA
- **T-QA101:** Crear plan de testing E2E (Playwright)
  - Escenarios móvil (home, register, pending)
  - Escenarios web (review, approval)
  - Duración: 2 días
  - Responsable: QA Lead

**Deliverables Sprint 1:**
- ✅ Arquitectura mobile/web implementada
- ✅ Componentes base frontend listos
- ✅ Endpoints operativos completados
- ✅ KPIs básicos calculados
- ✅ Plan de testing listo

**Métricas al final del Sprint:**
- Frontend coverage: 50%
- Backend API coverage: 60%
- Design mockups completados: 80%

---

### SPRINT 2: Funcionalidad Operativa (Semana 3-4, Jul 9 - Jul 22)

**Objetivo:** Implementar flujo completo operador de campo.

#### Frontend
- **T-F201:** Implementar Home móvil
  - Dashboard KPIs operador
  - Lote actual con detalles
  - Botón "+ Registrar" prominente
  - Alertas por desviación
  - Duración: 2 días
  - Responsable: Frontend Dev

- **T-F202:** Implementar formulario dinámico por evento
  - Detectar tipo evento → mostrar campos dinámicos
  - Validación en tiempo real (Zod)
  - Progress bar (paso N de M)
  - Duración: 4 días
  - Responsable: Senior Frontend Dev

- **T-F203:** Implementar pantalla "Mis Registros Pendientes"
  - Lista con estado (enviado, en revisión, devuelto)
  - Colores de estado (🔵 🟡 ✅ 🔴)
  - Botón "Detalles" y "Corregir"
  - Duración: 2 días
  - Responsable: Frontend Dev

- **T-F204:** Implementar offline mode (IndexedDB)
  - Cache de maestros
  - Cola de eventos pendientes envío
  - Sync cuando se conecta
  - Duración: 3 días
  - Responsable: Senior Frontend Dev

#### Backend
- **T-B201:** Implementar corrección auditada
  - PATCH `/operations/events/{id}/` con corrección
  - Registrar valor original → corregido en AuditLog
  - Validar permisos (solo supervisor+)
  - Duración: 3 días
  - Responsable: Backend Dev

- **T-B202:** Implementar batch review operations
  - POST `/review/batch/` (crear lote de revisión)
  - PATCH `/review/batch/{id}/approve`
  - Duración: 2 días
  - Responsable: Backend Dev

- **T-B203:** Crear migración Alembic para EggBatch y ChickBatch
  - Tablas, relaciones, índices
  - Data migration si aplica
  - Duración: 1 día
  - Responsable: Database Architect

#### Testing
- **T-QA201:** Implementar tests Playwright para mobile
  - Scenario: Register bird movement
  - Scenario: View pending events
  - Duración: 2 días
  - Responsable: QA Dev

**Deliverables Sprint 2:**
- ✅ Flujo operador móvil funcional
- ✅ Offline mode implementado
- ✅ Corrección auditada en backend
- ✅ Nuevos modelos (EggBatch, ChickBatch) en BD
- ✅ 60% coverage E2E testing

---

### SPRINT 3: Flujo de Aprobación & Trazabilidad (Semana 5-6, Jul 23 - Aug 5)

**Objetivo:** Completar flujo aprobación y trazabilidad generacional.

#### Frontend
- **T-F301:** Mejorar bandeja de revisión (web)
  - Tabla con múltiples filtros
  - Bulk actions (aprobar múltiples)
  - Sidebar detalles evento
  - Duración: 3 días
  - Responsable: Frontend Dev

- **T-F302:** Implementar detalle evento con corrección
  - Mostrar datos originales
  - Ver correcciones previas (historial)
  - Botones: Aprobar, Rechazar, Corregir
  - Duración: 3 días
  - Responsable: Frontend Dev

- **T-F303:** Crear página trazabilidad (web)
  - Flujo visual: Reproductora → Huevos → Incubadora → Pollitos → Engorde
  - Timeline interactiva
  - KPIs por fase
  - Duración: 3 días
  - Responsable: Senior Frontend Dev

- **T-F304:** Implementar reporte trazabilidad
  - Exportar a PDF con diagrama
  - Tabla de eventos en el recorrido
  - Duración: 2 días
  - Responsable: Frontend Dev

#### Backend
- **T-B301:** Crear servicios EggBatch y ChickBatch
  - `create_egg_batch(source_lot_id, destination_hatchery_id, eggs)`
  - `create_chick_batch(source_egg_batch_id, destination_lot_id, chicks)`
  - Duración: 3 días
  - Responsable: Backend Dev

- **T-B302:** Implementar endpoints EggBatch/ChickBatch
  - POST, GET, UPDATE, DELETE
  - Auditoría completa
  - Validaciones
  - Duración: 2 días
  - Responsable: Backend Dev

- **T-B303:** Crear servicio de trazabilidad
  - `get_traceability_chain(lot_id)` → devuelve ruta completa
  - `calculate_hatchery_yield(egg_batch_id)` → % eclosión
  - Duración: 2 días
  - Responsable: Backend Dev

- **T-B304:** Implementar SAP sync preparación
  - Crear tabla `SapSyncJob`
  - Crear tabla `SapPayload`
  - Logic para consolidar eventos aprobados
  - Duración: 3 días
  - Responsable: SAP Specialist

#### Testing
- **T-QA301:** Tests para trazabilidad (unitarios + integración)
  - Test crear EggBatch
  - Test crear ChickBatch
  - Test calcular yield
  - Duración: 2 días
  - Responsable: Backend QA

**Deliverables Sprint 3:**
- ✅ Flujo aprobación web completo
- ✅ Trazabilidad generacional funcional
- ✅ Reportes trazabilidad
- ✅ SAP sync preparado
- ✅ KPI yield calculations

---

### SPRINT 4: SAP Integration & KPIs Completos (Semana 7-8, Aug 6 - Aug 19)

**Objetivo:** Integración real con SAP y KPIs avanzados.

#### Backend
- **T-B401:** Implementar SAP sync automática
  - Polling cada hora o webhook
  - Enviar lotes aprobados a SAP
  - Recibir confirmación y registrar
  - Manejo de errores y reintentos
  - Duración: 4 días
  - Responsable: SAP Specialist

- **T-B402:** Crear servicio KPIs avanzados
  - Conversión alimenticia (kg alimento / kg ganancia)
  - Eclosión (%) por lote reproducción
  - Viabilidad (%) por lote engorde
  - Uniformidad (CV de pesos)
  - Índice productivo (ganancia/mortalidad/conversión)
  - Duración: 3 días
  - Responsable: Backend Dev

- **T-B403:** Crear endpoint reportes por etapa
  - GET `/reports/breeding/` (reportes etapa cría)
  - GET `/reports/production/` (reportes etapa producción)
  - GET `/reports/fattening/` (reportes etapa engorde)
  - GET `/reports/hatchery/` (reportes incubadora)
  - Duración: 2 días
  - Responsable: Backend Dev

#### Frontend
- **T-F401:** Crear dashboard SAP (web)
  - Status último sync
  - Lotes enviados a SAP
  - Confirmaciones recibidas
  - Errores y reintentos
  - Duración: 3 días
  - Responsable: Frontend Dev

- **T-F402:** Implementar reportes por etapa (web)
  - KPIs gráficas (charts)
  - Tablas con datos detallados
  - Filtros por fecha, granja, etc.
  - Exportar Excel/PDF
  - Duración: 4 días
  - Responsable: Senior Frontend Dev

- **T-F403:** Crear dashboard KPIs avanzados (web)
  - Conversión alimenticia por lote
  - Eclosión por reproducción
  - Benchmarking vs. genética estándar
  - Alertas por desviación
  - Duración: 3 días
  - Responsable: Frontend Dev

#### Testing
- **T-QA401:** Tests SAP sync
  - Mock SAP responses
  - Test envío exitoso
  - Test manejo de errores
  - Test reintentos
  - Duración: 2 días
  - Responsable: Backend QA

**Deliverables Sprint 4:**
- ✅ SAP sync funcionando
- ✅ KPIs avanzados calculados
- ✅ Reportes completos por etapa
- ✅ Dashboard SAP en web
- ✅ 80% backend test coverage

---

### SPRINT 5: Refinamiento & Optimización (Semana 9-10, Aug 20 - Sep 2)

**Objetivo:** Pulir, optimizar y preparer para lanzamiento.

#### Frontend
- **T-F501:** Performance optimization
  - Code splitting (lazy loading rutas)
  - Bundle size < 500KB gzipped
  - Caché de assets
  - Optimización imágenes
  - Duración: 2 días
  - Responsable: Senior Frontend Dev

- **T-F502:** Accesibilidad (WCAG AA)
  - Auditoría con herramientas
  - Fijar contrasts, labels, alt text
  - Testing con screen reader
  - Duración: 2 días
  - Responsable: QA Dev

- **T-F503:** Mobile UX polish
  - User testing con 5+ operadores
  - Incorporar feedback
  - Ajustes finales de tamaños, colores
  - Duración: 3 días
  - Responsable: UI/UX Designer + Frontend Dev

- **T-F504:** Documentación y ayuda contextual
  - Tooltips en campos complejos
  - Modal "Primeros pasos"
  - Video tutorial (opcional)
  - Help links en cada pantalla
  - Duración: 2 días
  - Responsable: Tech Writer + Frontend Dev

#### Backend
- **T-B501:** Optimización de queries
  - Identificar N+1 queries
  - Agregar índices faltantes
  - Implementar caching estratégico
  - Duración: 2 días
  - Responsable: Backend Lead

- **T-B502:** Validaciones completas
  - Validar todas las operaciones contra reglas avícolas
  - Edad mínima/máxima por evento
  - Capacidades de galpones
  - Duración: 2 días
  - Responsable: Backend Dev

#### Testing
- **T-QA501:** E2E testing completo (Playwright)
  - Scenario: Operador registra evento en móvil
  - Scenario: Supervisor revisa en web
  - Scenario: Aprobador aprueba
  - Scenario: SAP sync ocurre
  - Scenario: Reporte se genera
  - Duración: 3 días
  - Responsable: QA Lead

- **T-QA502:** Testing performance
  - Load testing (100+ usuarios simultáneos)
  - Test mobile en 4G
  - Test offline sync
  - Duración: 2 días
  - Responsable: QA Dev

#### DevOps
- **T-OPS501:** Preparar deployment
  - CI/CD pipeline actualizado
  - Staging environment listo
  - Rollback procedure documentado
  - Duración: 2 días
  - Responsable: DevOps Engineer

**Deliverables Sprint 5:**
- ✅ Aplicación optimizada
- ✅ WCAG AA cumplido
- ✅ 100% test coverage (backend), 80% (frontend)
- ✅ Documentación de usuario completa
- ✅ Listo para producción

---

## III. DISTRIBUCIÓN DE EQUIPO

### Requerimientos de Equipo

| Rol | Cantidad | Semana |
|-----|----------|--------|
| **Frontend Lead** | 1 | Todas |
| **Senior Frontend Dev** | 2 | Todas |
| **Frontend Dev** | 2 | Todas |
| **Backend Lead** | 1 | Todas |
| **Backend Dev** | 2 | Todas |
| **SAP Specialist** | 1 | Sprint 3-5 |
| **Database Architect** | 1 | Sprint 1-2 |
| **QA Lead** | 1 | Todas |
| **QA Dev** | 2 | Todas |
| **UI/UX Designer** | 1 | Sprint 1-2, 5 |
| **Tech Writer** | 1 | Sprint 5 |
| **DevOps Engineer** | 1 | Sprint 5 |
| **Product Manager** | 1 | Todas |

**Total:** ~16 personas simultáneamente, reducible a 12 en sprints posteriores.

---

## IV. TIMELINE MACROESTRUCTURA

```
┌─────────────────────────────────────────────────────────────┐
│              TIMELINE GLOBAL AVÍCOLA v2                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  S1          S2          S3          S4          S5         │
│  ─────────────────────────────────────────────────         │
│  Jun24 Jul08  Jul09 Jul22  Jul23 Aug05  Aug06 Aug19  Aug20 Sep02
│
│  Arquitect  Operativo  Trazab.    SAP+KPI   Polish
│  ─────────  ────────── ────────   ──────   ──────
│  Est: 35%   Est: 60%   Est: 80%   Est: 95% Est: 100%
│
│  Releases:
│  • Alpha (S2): Mobile operativa
│  • Beta (S3): Flujo completo
│  • RC (S4): SAP integrado
│  • GA (S5): Producción ready
│
└─────────────────────────────────────────────────────────────┘
```

---

## V. RIESGOS Y MITIGACIÓN

### Riesgos Identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------|--------|-----------|
| **SAP no tiene API/OData clara** | MEDIA | CRÍTICO | Contactar SAP pre-Sprint 4, plan B: manual exports |
| **Mobile performance issues** | MEDIA | ALTA | Testing temprano, optimización en S4 |
| **Cambios scope mid-project** | ALTA | MEDIA | Cuarentena de scope post-Sprint 1 |
| **Attrasos personal clave** | MEDIA | CRÍTICO | Tener backups identificados |
| **Integración DB complexity** | BAJA | MEDIA | Architect review pre-implementación |
| **Operadores rechacen cambios UI** | BAJA | MEDIA | User testing con feedback loops |

### Plan de Contingencia

- **Semana 1:** Daily standups si hay desviaciones
- **Semana 3:** Review scope, ajustar si necesario
- **Semana 5:** Identificar qué es MVP vs. fase 2
- **Semana 9:** Potencial extension de 1-2 semanas si hay gaps críticos

---

## VI. CRITERIOS DE ACEPTACIÓN

### Por Sprint

#### Sprint 1 Acceptance
- [ ] Routing mobile/web funciona correctamente
- [ ] Componentes mobile renderean sin errores
- [ ] Endpoints backend retornan datos válidos
- [ ] KPIs básicos se calculan correctamente
- [ ] Mockups Figma aprobados por stakeholders

#### Sprint 2 Acceptance
- [ ] Operador puede registrar evento completo en móvil
- [ ] Offline mode funciona (guardar, sync posterior)
- [ ] Supervisor puede ver eventos pendientes en web
- [ ] Corrección auditada se registra correctamente
- [ ] 3 scenarios Playwright pasan

#### Sprint 3 Acceptance
- [ ] Trazabilidad huevo→pollito se ve en Lot Detail
- [ ] Reportes trazabilidad generan correctamente
- [ ] SAP payload se prepara pero no envía (simulado)
- [ ] Backend tests: 70% coverage
- [ ] 5 scenarios Playwright pasan

#### Sprint 4 Acceptance
- [ ] SAP sync envía datos y recibe confirmación
- [ ] KPIs avanzados (conversión, yield) calculan bien
- [ ] Reportes por etapa muestran gráficas y tablas
- [ ] Dashboard SAP muestra status sincronización
- [ ] Backend tests: 80% coverage

#### Sprint 5 Acceptance
- [ ] Bundle size < 500KB gzipped
- [ ] WCAG AA pass en accessibility audit
- [ ] 10 scenarios E2E pass end-to-end
- [ ] Performance: Mobile load < 3s, API p95 < 200ms
- [ ] Documentación usuario completa
- [ ] Listo para producción (green light CTO)

---

## VII. DEFINICIÓN MÍNIMO VIABLE (MVP)

**MVP para lanzamiento (Sprint 4):**
- ✅ Operador móvil registra eventos
- ✅ Supervisor revisa y aprueba
- ✅ SAP sync automática funciona
- ✅ Trazabilidad básica (evento → evento)
- ✅ Reportes KPIs por etapa
- ✅ Offline mode (opcional pero deseable)

**Fase 2 (Post-lanzamiento):**
- 🔄 Grandparent import automation
- 🔄 Document management (sanitarios, órdenes)
- 🔄 Biometric authentication móvil
- 🔄 Video tutorials
- 🔄 Dark mode
- 🔄 API pública para integraciones

---

## VIII. COMUNICACIÓN & STAKEHOLDERS

### Cadencia

| Artefacto | Frecuencia | Audiencia |
|-----------|----------|-----------|
| Daily Standup | 10:00 AM | Equipo dev (15 min) |
| Sprint Planning | Lunes 14:00 | Equipo + PM (1h) |
| Sprint Review | Viernes 16:00 | Stakeholders + Equipo (1h) |
| Sprint Retro | Viernes 17:00 | Equipo (45 min) |
| Weekly Status | Miércoles 11:00 | Ejecutivos (30 min) |
| Demo to Customers | Bi-weekly | Operadores piloto |

### Artefactos

- **Board Jira/GitHub:** Actualizado diariamente
- **Burndown chart:** Visible para equipo
- **Release notes:** Al final de cada sprint
- **Test coverage report:** Semanal

---

## IX. SUCESOS HITO

| Hito | Fecha | Criterio |
|------|-------|---------|
| **Architecture Ready** | Jun 28 | Frontend/Backend base OK |
| **Mobile Alpha** | Jul 15 | Operador puede registrar 5 eventos tipo |
| **Full Flow Beta** | Jul 30 | Registro → Aprobación → SAP pipeline |
| **SAP Connected** | Aug 15 | Sync automática enviando/recibiendo datos |
| **Polish Complete** | Aug 30 | Tests, docs, performance OK |
| **GA Ready** | Sep 2 | Aprobación CTO, release a producción |

---

## X. PRESUPUESTO & RECURSOS

### Estimación esfuerzo por Sprint

| Sprint | Frontend (días) | Backend (días) | Testing (días) | Total |
|--------|---------|---------|---------|-------|
| S1 | 20 | 15 | 5 | **40 días** |
| S2 | 18 | 12 | 5 | **35 días** |
| S3 | 16 | 14 | 5 | **35 días** |
| S4 | 14 | 12 | 5 | **31 días** |
| S5 | 12 | 8 | 8 | **28 días** |
| **TOTAL** | **80** | **61** | **28** | **169 días** |

**Personas-semana needed:** 169 / 5 = ~34 personas-semana  
**Equipo 12 personas × 10 semanas:** 120 personas-semana  
**Margen:** 34% (permite documentación, meetings, buffer)

---

## XI. SUCCESS METRICS POST-LANZAMIENTO

### Métricas Técnicas
- ✅ Uptime > 99.5%
- ✅ Load time móvil < 3s
- ✅ API response p95 < 200ms
- ✅ 0 bugs críticos en primer mes

### Métricas de Negocio
- ✅ 80%+ de operadores usando diariamente
- ✅ 95%+ eventos aprobados en < 24h
- ✅ 0 rechazos por datos incompletos
- ✅ SAP sync 100% successful
- ✅ ROI > 3x en primer año

### Métricas de Satisfacción
- ✅ NPS > 7/10
- ✅ 90%+ usuarios sienten mejora en eficiencia
- ✅ < 2 horas formación requerida por usuario

---

**PRÓXIMOS PASOS INMEDIATOS:**

1. **HOY:** Aprobación de este plan por CTO + Product Manager
2. **MAÑANA:** Kickoff Sprint 1 + asignación equipo
3. **Esta semana:** Primer PR con arquitectura mobile/web
4. **Próxima semana:** Primera build en staging con componentes base

**Compromisos:**
- ✅ Entrega en 10 semanas (Sep 2, 2026)
- ✅ Calidad de clase mundial
- ✅ Zero technical debt acumulado
- ✅ 100% documentación al entregar

---

**Documento aprobado por:**

- CTO: _________________ Fecha: ___________
- Product Manager: _________________ Fecha: ___________
- Arquitecto Sr: _________________ Fecha: ___________
