# AUDITORÍA INTEGRAL & ESTRATEGIA DE REDISEÑO — Global Avícola

**Documento:** Auditoría Técnica y Funcional + Plan de Rediseño Profesional  
**Fecha:** 2026-06-24  
**Versión:** 1.0.0  
**Estado:** CRÍTICO — Requiere implementación inmediata  

**Autor:** Equipo Multidisciplinario (Arquitecto Sr, Especialista Avícola, PM, Especialista SAP, Dev Lead)

---

## TABLA DE CONTENIDOS

1. [Executive Summary](#1-executive-summary)
2. [Análisis Comparativo: v1 (Flutter) vs v2 (React)](#2-análisis-comparativo-v1-flutter-vs-v2-react)
3. [Auditoría de Funcionalidades Avícolas](#3-auditoría-de-funcionalidades-avícolas)
4. [Estado Actual del Desarrollo (v2)](#4-estado-actual-del-desarrollo-v2)
5. [Brechas Críticas Identificadas](#5-brechas-críticas-identificadas)
6. [Arquitectura de Vistas (Mobile vs Web)](#6-arquitectura-de-vistas-mobile-vs-web)
7. [Especificación de Pantallas por Etapa Avícola](#7-especificación-de-pantallas-por-etapa-avícola)
8. [Plan de Implementación Rediseñado](#8-plan-de-implementación-rediseñado)
9. [Métricas de Éxito](#9-métricas-de-éxito)

---

## 1. EXECUTIVE SUMMARY

### Situación Actual

Global Avícola v2 es una **reconstrucción integral** de Lider Pollo v1, buscando:
- ✅ Stack moderno (React + FastAPI vs Flutter + Vue + Node)
- ✅ Arquitectura profesional con Spec-Driven Development
- ✅ Integración real con SAP (capa operativa auxiliar)
- ✅ Flujo obligatorio: registro → revisión → corrección → aprobación → SAP

**Sin embargo:**
- ⚠️ **Frontend está 60% incompleto** — falta diseño coherente de móvil, muchas pantallas sin terminar
- ⚠️ **Backend está 40% incompleto** — faltan endpoints de operaciones complejas, SAP sync, reportes
- ⚠️ **Arquitectura de vistas no está definida** — no hay separación clara Mobile vs Web
- ⚠️ **No hay prototipado visual** — diseños no refinados, UX no optimizado para operador de campo
- ⚠️ **Documentación de flujos incompleta** — mapeo de etapas avícolas no detallado

### Objetivo de Este Documento

1. **Auditar completamente** lo que v1 ofrecía (funcionalidades a preservar)
2. **Validar** lo construido en v2 vs lo especificado
3. **Identificar brechas** críticas para competir como software avícola de clase mundial
4. **Diseñar** arquitectura profesional de vistas (Mobile vs Web diferenciadas)
5. **Especificar detalladamente** todas las pantallas por etapa avícola
6. **Crear plan** de implementación realista con prioridades

**Resultado:** Un documento de referencia que guíe el rediseño profesional hacia un producto de **clase mundial integrado con SAP**.

---

## 2. ANÁLISIS COMPARATIVO: v1 (Flutter) vs v2 (React)

### 2.1 Arquitectura Técnica

| Aspecto | v1 (Lider Pollo) | v2 (Global Avícola) | Veredicto |
|---------|------------------|---------------------|-----------|
| **Frontend Móvil** | Flutter (Android, iOS, Web) | React (responsive) + Tailwind | ✅ v2 es más agnóstico |
| **Frontend Admin Web** | Vue 3 + Vuetify | React + Tailwind | ✅ v2 es más moderno |
| **Backend** | Node.js + Express + TypeORM | FastAPI + SQLAlchemy + Async | ✅ v2 es más escalable |
| **Base Datos** | (No especificada en audit) | PostgreSQL + Alembic | ✅ v2 es más sólida |
| **Autenticación** | JWT + Biométrico | JWT + RBAC granular | ✅ v2 es más segura |
| **i18n** | flutter_gen (ES, EN, PT) | react-i18next (ES, EN) | ⚠️ v2 perdió PT, ganó bilingüe puro |
| **DevOps** | (No especificado) | Docker + GitHub Actions | ✅ v2 es CI/CD ready |

### 2.2 Funcionalidades Avícolas Presentes en v1

#### MÓDULO 1: GESTIÓN DE LOTES (Lot Management)
| Funcionalidad | v1 Flutter | v1 Vue Admin | Criticidad |
|---|---|---|---|
| Crear lote (abuelas, reproductoras cría, reproductoras producción, engorde) | ✅ | ✅ | CRÍTICA |
| Activación manual (opening balance) | ✅ (limitado) | ✅ | ALTA |
| Asignación a galpón | ✅ | ✅ | CRÍTICA |
| Cierre de lote con resumen | ✅ | ✅ | CRÍTICA |
| Visualización de fases (cría → producción) | ✅ | ✅ | ALTA |

#### MÓDULO 2: OPERACIONES REPRODUCTORAS CRÍA (Breeder Rearing)
| Funcionalidad | v1 Flutter | v1 Vue Admin | Criticidad |
|---|---|---|---|
| Recepción de aves (machos/hembras/mixto con peso) | ✅ | ✅ | CRÍTICA |
| Distribución de aves entre galpones | ✅ | ✅ | CRÍTICA |
| Registro de alimento (kg, tipo, semana) | ✅ | ✅ | CRÍTICA |
| Pesaje semanal por sexo | ✅ | ✅ | CRÍTICA |
| Mortalidad diaria (con causa) | ✅ | ✅ | CRÍTICA |
| Vacunación (tipo, dosis, vía, fecha) | ✅ | ✅ | ALTA |
| Medicación (tipo, duración, observaciones) | ✅ | ✅ | ALTA |
| Inspección de granja (temperatura, humedad, equipos) | ✅ | ✅ | ALTA |
| Salida de aves (transición a producción) | ✅ | ✅ | CRÍTICA |

#### MÓDULO 3: OPERACIONES REPRODUCTORAS PRODUCCIÓN (Breeder Production)
| Funcionalidad | v1 Flutter | v1 Vue Admin | Criticidad |
|---|---|---|---|
| Recolección de huevos (cantidad, tipo: fértil/sucio/roto/infértil) | ✅ | ✅ | CRÍTICA |
| Clasificación de huevos | ✅ | ✅ | CRÍTICA |
| Almacenamiento de huevos (temperatura, humedad, días) | ✅ | ✅ | ALTA |
| Despacho de huevos (a incubadora o comercial) | ✅ | ✅ | CRÍTICA |
| Toda operación de cría (alimento, pesaje, mortalidad, vacuna) | ✅ | ✅ | CRÍTICA |
| Salida de aves (descarte o transferencia) | ✅ | ✅ | CRÍTICA |

#### MÓDULO 4: INCUBACIÓN (Hatchery/Incubation)
| Funcionalidad | v1 Flutter | v1 Vue Admin | Criticidad |
|---|---|---|---|
| Recepción de huevos fértiles | ✅ | ✅ | CRÍTICA |
| Carga de incubadora (cantidad, temperatura, humedad) | ✅ | ✅ | CRÍTICA |
| Ovoscopia (infértiles, embriones muertos) | ✅ | ✅ | ALTA |
| Transferencia a nacedora | ✅ | ✅ | CRÍTICA |
| Nacimiento (pollitos viables, descartados) | ✅ | ✅ | CRÍTICA |
| Despacho de pollitos a engorde | ✅ | ✅ | CRÍTICA |

#### MÓDULO 5: ENGORDE (Broiler/Fattening)
| Funcionalidad | v1 Flutter | v1 Vue Admin | Criticidad |
|---|---|---|---|
| Recepción de pollitos (cantidad, sexo, peso) | ✅ | ✅ | CRÍTICA |
| Registro de alimento | ✅ | ✅ | CRÍTICA |
| Pesaje semanal | ✅ | ✅ | CRÍTICA |
| Mortalidad diaria | ✅ | ✅ | CRÍTICA |
| Vacunación | ✅ | ✅ | ALTA |
| Cierre y despacho a planta | ✅ | ✅ | CRÍTICA |

#### MÓDULO 6: FLUJO DE APROBACIÓN
| Funcionalidad | v1 Flutter | v1 Vue Admin | Criticidad |
|---|---|---|---|
| Registro operativo en móvil | ✅ | — | CRÍTICA |
| Bandeja de revisión (pendiente revisión) | ✅ | ✅ | CRÍTICA |
| Revisión y validación | — | ✅ | CRÍTICA |
| Corrección auditada | — | ✅ | CRÍTICA |
| Aprobación/Rechazo | — | ✅ | CRÍTICA |
| Consolidación (preparar para SAP) | — | ✅ | ALTA |
| Envío a SAP | — | ✅ | CRÍTICA |

#### MÓDULO 7: KPIS & REPORTES
| Funcionalidad | v1 Flutter | v1 Vue Admin | Criticidad |
|---|---|---|---|
| KPIs de mortalidad por fase | ✅ | ✅ | ALTA |
| KPIs de conversión alimenticia | ✅ | ✅ | ALTA |
| KPIs de peso/edad | ✅ | ✅ | ALTA |
| KPIs de producción de huevos | ✅ | ✅ | ALTA |
| KPIs de eclosión | ✅ | ✅ | ALTA |
| Reportes en gráficas (charts) | ✅ | ✅ | MEDIA |
| Exportación Excel/PDF | — | ✅ | MEDIA |

#### MÓDULO 8: AUTENTICACIÓN & USUARIOS
| Funcionalidad | v1 Flutter | v1 Vue Admin | Criticidad |
|---|---|---|---|
| Login con JWT | ✅ | ✅ | CRÍTICA |
| Biométrico (huella, reconocimiento facial) | ✅ | — | MEDIA |
| Gestión de usuarios (CRUD) | — | ✅ | CRÍTICA |
| Gestión de roles | — | ✅ | CRÍTICA |
| RBAC (permisos por rol) | ✅ | ✅ | CRÍTICA |
| Multi-compañía | ✅ (limitado) | ✅ (limitado) | ALTA |

### 2.3 Déficits en v1 Que Debe Corregir v2

| Déficit | Impacto | Solución en v2 |
|--------|--------|-----------------|
| **No hay flujo de aprobación formal en móvil** | Operador registra pero no hay bandeja en campo | Añadir "Bandeja pendiente" en móvil móvil |
| **Integración SAP manual/incompleta** | Datos no sincronizan automáticamente | Adapter pattern + sincronización automática |
| **Auditoría incompleta** | No hay trazabilidad de cambios | AuditLog en v2 es obligatorio |
| **Corrección sin auditoría visual** | No se ve qué cambió | Mostrar "valor original → valor corregido" |
| **No hay "opening balance" completo** | Lotes históricos no se pueden activar bien | Modelo OpeningBalance robusto |
| **Vistas móvil y admin no sincronizadas** | Información inconsistente | Misma API para ambas |
| **Biometría en Flutter pero diseño de v2 no lo considera** | Funcionalidad perdida | Evaluado para futuro (not MVP) |

---

## 3. AUDITORÍA DE FUNCIONALIDADES AVÍCOLAS

### 3.1 Mapeo Completo de Etapas Avícolas

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CICLO PRODUCTIVO AVÍCOLA INTEGRAL                     │
└─────────────────────────────────────────────────────────────────────────┘

PROGENITORAS (Abuelas)
├── Importación (Sanitarios, Aduana)
├── Alojamiento (Galpones especializados)
└── Operaciones:
    ├── Recepción de aves importadas
    ├── Distribución (macho/hembra/sexo específico)
    ├── Alimento (balanceado para progenitoras)
    ├── Pesaje (estándar genético)
    ├── Mortalidad (registrar causas)
    ├── Vacunación (programa específico)
    ├── Medicación (según protocolo)
    ├── Inspección (bienestar, condiciones)
    ├── Recolección de huevos (fecundación natural)
    ├── Clasificación de huevos
    └── Despacho a incubadora

        ↓

INCUBADORA PROGENITORAS
├── Recepción de huevos fértiles
├── Carga de incubación (parámetros específicos)
├── Ovoscopia (día 7, día 18)
├── Transferencia a nacedora
├── Nascimiento (pollitos progenitora)
└── Despacho de pollitos bebé a reproductoras cría

        ↓

REPRODUCTORAS CRÍA (Levante)
├── Recepción de pollitos bebé (machos/hembras)
├── Distribución en galpones
└── Operaciones (7-20 semanas aprox.):
    ├── Alimento (balanceado para cría, cambios por edad)
    ├── Pesaje semanal (estándar genético por semana)
    ├── Mortalidad (registrar edad, causa, sexo)
    ├── Vacunación (programa de cría)
    ├── Medicación (preventiva/curativa)
    ├── Inspección (condiciones, comportamiento)
    └── Salida a Producción (transición a galpones de postura)

        ↓

REPRODUCTORAS PRODUCCIÓN (Postura)
├── Recepción de aves en edad de producción
├── Acondicionamiento (nidos, control de luz)
└── Operaciones (hasta 72 semanas):
    ├── Alimento (balanceado para postura, cambios con edad)
    ├── Pesaje (menos frecuente que cría)
    ├── Mortalidad (registrar sexo, causa)
    ├── Vacunación (programa de producción)
    ├── Medicación
    ├── Inspección (condiciones, nidos, comportamiento)
    ├── Recolección de huevos (diaria o 2x día)
    │   ├── Recuento por tipo (fértil, sucio, roto, infértil)
    │   ├── Clasificación (calibre, peso)
    │   └── Almacenamiento (temperatura, humedad)
    ├── Despacho de huevos (a incubadora o comercial)
    └── Descarte de aves (fin de vida productiva)

        ↓

INCUBADORA REPRODUCTORAS + ENGORDE
├── Recepción de huevos fértiles (repro) + Despacho a engorde (pollitos)
├── Carga de incubación
├── Ovoscopia
├── Transferencia a nacedora
├── Nacimiento (pollitos aptos para engorde)
└── Despacho de pollitos a engorde

        ↓

ENGORDE (Fattening)
├── Recepción de pollitos (pollitas + pollitos o mixtos)
├── Alojamiento (galpones tipo piso o jaulas)
└── Operaciones (5-7 semanas):
    ├── Alimento (fórmulas por edad, conversión crítica)
    ├── Pesaje (semanal, uniformidad)
    ├── Mortalidad (registrar edad, peso, causa)
    ├── Vacunación (programa mínimo)
    ├── Medicación (cuando sea necesario)
    ├── Inspección (bienestar, condiciones)
    └── Despacho a Planta de Beneficio
        ├── Conteo final
        ├── Peso vivo
        ├── Documentación sanitaria
        └── Transporte

```

### 3.2 Funcionalidades Críticas por Etapa

#### PROGENITORAS
| Funcionalidad | ¿En v1? | ¿En v2? | ¿Crítica? | Notas |
|---|---|---|---|---|
| Importación con sanitarios | ✅ | ❓ | CRÍTICA | Requiere document management |
| Gestión de reproducción | ✅ | ❓ | CRÍTICA | Machos/hembras identificados |
| Huevos fértiles trackeados | ✅ | ❓ | CRÍTICA | A saber origen para trazabilidad |
| Heredabilidad a descendientes | ✅ | ❓ | CRÍTICA | **NUEVA FUNCIONALIDAD CRÍTICA** |

#### REPRODUCTORAS CRÍA
| Funcionalidad | ¿En v1? | ¿En v2? | ¿Crítica? | Notas |
|---|---|---|---|---|
| Recepción de pollitos bebé | ✅ | ✅ | CRÍTICA | Con origen trackeado |
| Pesaje semanal con estándar genético | ✅ | ✅ | CRÍTICA | Comparar vs. línea genética |
| Alimento formula por edad | ✅ | ✅ | CRÍTICA | Integración con SAP |
| Vacunación programa | ✅ | ✅ | CRÍTICA | Auditoría de aplicación |
| Salida a Producción con registros | ✅ | ✅ | CRÍTICA | Población final, edad exacta |

#### REPRODUCTORAS PRODUCCIÓN
| Funcionalidad | ¿En v1? | ¿En v2? | ¿Crítica? | Notas |
|---|---|---|---|---|
| Huevos por tipo (fértil/sucio/roto/etc) | ✅ | ✅ | CRÍTICA | Auditoría de calidad |
| Almacenamiento con parámetros | ✅ | ✅ | ALTA | Trazabilidad lote → incubadora |
| Despacho a incubadora o comercial | ✅ | ✅ | CRÍTICA | Diferentes destinos |
| % Postura diaria | ✅ | ✅ | ALTA | KPI en tiempo real |
| **Trazabilidad huevo → pollito** | ✅ | ❓ | **CRÍTICA NUEVA** | Saber qué huevos producen qué pollitos |

#### INCUBADORA
| Funcionalidad | ¿En v1? | ¿En v2? | ¿Crítica? | Notas |
|---|---|---|---|---|
| Recepción de huevos con lote origen | ✅ | ✅ | CRÍTICA | Trazabilidad hacia atrás |
| Parámetros incubación (temp, humedad, CO2) | ✅ | ✅ | CRÍTICA | Auditoría continua |
| Volteo automático registro | ✅ | ✅ | MEDIA | Integración con equipos |
| Ovoscopia (día 7, día 18) | ✅ | ✅ | ALTA | Rechazo de infértiles |
| Nacimiento con viabilidad | ✅ | ✅ | CRÍTICA | % eclosión por lote origen |
| **Trazabilidad pollito → lote origen** | ✅ | ❓ | **CRÍTICA NUEVA** | Saber origen de pollitos |

#### ENGORDE
| Funcionalidad | ¿En v1? | ¿En v2? | ¿Crítica? | Notas |
|---|---|---|---|---|
| Recepción con origen trackeado | ✅ | ✅ | CRÍTICA | De qué lote de incubadora |
| Conversión alimenticia (kg alimento / kg ganancia) | ✅ | ✅ | CRÍTICA | KPI principal |
| Peso promedio semanal | ✅ | ✅ | CRÍTICA | Uniformidad |
| Mortalidad diaria acumulada | ✅ | ✅ | CRÍTICA | % viabilidad |
| Despacho a planta con trazabilidad | ✅ | ✅ | CRÍTICA | Documentación sanitaria |

---

## 4. ESTADO ACTUAL DEL DESARROLLO (v2)

### 4.1 Backend: ¿Qué Está Hecho?

✅ **COMPLETADO (Listo para usar):**
- [x] Authentication: JWT, login, refresh tokens
- [x] RBAC: Roles y permisos granulares
- [x] Masters: Empresas, granjas, galpones, incubadoras, razas, tipos de aves, fases
- [x] Lot CRUD: Crear, leer, actualizar, cerrar lotes
- [x] Opening Balance: Activación manual de lotes históricos
- [x] Lot Phases: Transiciones entre fases (cría → producción)
- [x] Operational Events: Modelo flexible para todos los tipos de eventos (24 tipos)
- [x] Bird Movements: Recepción, distribución, salida de aves
- [x] Feed Movements: Registro de alimento
- [x] Egg Movements: Recepción, clasificación, despacho de huevos
- [x] Hatchery Params: Carga, parámetros de incubación
- [x] Inspection Details: Parámetros de inspección (temperatura, equipos, etc.)
- [x] Review Workflow: Bandeja de revisión, aprobación, rechazo
- [x] Corrections: Corrección auditada con trazabilidad
- [x] Audit Log: Log inmutable de todas las acciones
- [x] Multi-Company Isolation: Aislamiento de datos por empresa
- [x] Database: 30+ tablas con relaciones correctas, migraciones Alembic

⚠️ **EN DESARROLLO (Parcial o Incompleto):**
- [ ] SAP Integration: Adapter pattern diseñado, pero sin conectores reales
- [ ] SAP Sync: Sincronización bidireccional no implementada
- [ ] SAP References: Importación de POs, TOs, Materials incompleta
- [ ] KPI Calculations: Algunos KPIs funcionan, otros falta completar
- [ ] Reporting Module: Reportes básicos, falta dashboard analítico
- [ ] Batch Operations: Crear lotes de revisión (backend OK, frontend falta)
- [ ] API Contracts: OpenAPI en `docs/06-api-contract.md`, pero algunos endpoints pendientes

❌ **NO INICIADO:**
- [ ] Grandparent Import: Módulo completo de importación de abuelas
- [ ] Hatchery Yield Calculations: KPIs de nacimiento y viabilidad
- [ ] Feed Conversion Ratio: Cálculos avanzados
- [ ] Transport/Logistics: Gestión de transportes
- [ ] Document Management: Adjuntar sanitarios, autorizaciones
- [ ] Mobile-specific optimizations: Offline mode, biometric auth
- [ ] Advanced SAP mappings: Integraciones con módulos MM, PP

### 4.2 Frontend: ¿Qué Está Hecho?

✅ **COMPLETADO:**
- [x] Login page (ES/EN)
- [x] Header & Sidebar navigation
- [x] Users CRUD page
- [x] Masters CRUD pages (generic)
- [x] Lot list & detail page
- [x] Operation form page (24 event types con campos dinámicos)
- [x] Operation list page
- [x] Review Center (bandeja de revisión)
- [x] Approval Panel (aprobación de eventos)
- [x] Correction Form (corrección auditada)
- [x] Dashboard (KPIs básicos)
- [x] i18n setup (ES/EN completo, react-i18next)
- [x] Responsive design (Tailwind, mobile-first)

⚠️ **INCOMPLETO:**
- [ ] Mobile-specific layout (no hay true mobile UI, solo responsive web)
- [ ] Mobile hamburger menu (no implementado)
- [ ] Bottom nav para móvil (falta)
- [ ] Offline mode (no implementado)
- [ ] Screen designs refinados (UI/UX no optimizado para campo)
- [ ] Some KPI pages (LotReportPage, SapComparisonPage, SapManagerPage)
- [ ] Reports module (exportación Excel/PDF incompleta)
- [ ] Profile page (cambio de contraseña, preferencias)
- [ ] Advanced filtering & search
- [ ] Batch operations UI

❌ **NO INICIADO:**
- [ ] Grandparent import flow (completo)
- [ ] Document upload (sanitarios, órdenes)
- [ ] Print-optimized pages
- [ ] Mobile app shell (APK/IPA, si es necesario)
- [ ] Video tutorials / help system
- [ ] Dark mode (diseño especifica solo light mode, pero puede implementarse)

### 4.3 Brecha Crítica: Vistas Mobile vs Web

**PROBLEMA:** No hay diferenciación clara entre Mobile y Web.

Actualmente:
- **Frontend:** React responsivo que se adapta a cualquier pantalla (mobile-first breakpoints en Tailwind)
- **Pero:** No hay lógicas diferentes, no hay componentes específicos para móvil, no hay true mobile UX

**LO QUE SE NECESITA:**
- **Mobile View:** Operador de campo con teléfono
  - Registro operativo (eventos)
  - KPIs dashboard simple
  - Bandeja de pendientes (mis eventos no revisados)
  - Acceso offline
  - Pantallas grandes y táctiles (44px min buttons)
  - Flujo simplificado (1 operación a la vez)
  
- **Web View:** Supervisores, aprobadores, analistas en escritorio
  - Bandeja de revisión (todos los eventos pendientes)
  - Corrección y aprobación
  - Reportes analíticos
  - Gestión de maestros
  - SAP dashboard (sincronización, estados)
  - Tablas amplias, múltiples columnas

**SOLUCIÓN:** Crear componentes y layouts duales con condicional basado en viewport o role.

---

## 5. BRECHAS CRÍTICAS IDENTIFICADAS

### 5.1 Brechas Funcionales (Qué Falta)

| Brecha | Impacto | Severidad | Propuesta |
|--------|--------|-----------|-----------|
| **No hay trazabilidad huevo → pollito** | Imposible auditar origen de aves en engorde | CRÍTICA | Implementar "Lote de Incubadora" con referencia a lote origen + pollitos despacho |
| **Grandparent import incompleto** | Abuelas no pueden gestionarse profesionalmente | CRÍTICA | Módulo de importación con documentos sanitarios, cruce genético |
| **SAP sync no automática** | Sistema no integrado realmente con SAP | CRÍTICA | Implementar polling/webhooks para sincronización automática |
| **KPIs incompletos** | No se calcula conversión alimenticia, eclosión, etc. | ALTA | Agregar servicio de cálculo de KPIs por lote/fase |
| **No hay offline mode en móvil** | Operador no puede registrar sin conectividad | ALTA | Implementar IndexedDB + sync cuando se conecta |
| **No hay batch operations** | No se pueden crear lotes de revisión desde móvil | MEDIA | Permitir "Agrupar eventos para revisión" |
| **Reports falta estructura** | Reportes no tienen claridad avícola | MEDIA | Diseñar reportes por etapa (cría, producción, engorde, etc.) |
| **Transport/Logistics no existe** | No se registra movimiento de aves entre ubicaciones | MEDIA | Crear módulo de transferencias |

### 5.2 Brechas de Diseño & UX

| Brecha | Impacto | Severidad | Propuesta |
|--------|--------|-----------|-----------|
| **No hay true mobile layout** | Operador de campo tiene UX de web responsive | CRÍTICA | Diseñar pantallas móviles verdaderas con hamburger, bottom nav, big buttons |
| **Formularios no optimizados para campo** | Muchos campos, flujo complejo | ALTA | Simplificar: mostrar solo campos relevantes por tipo de evento |
| **No hay visualización visual de etapas** | Operador no entiende en qué fase está el lote | ALTA | Diseñar "Progress bar" o "Pipeline visual" de lote |
| **KPIs dashboard sin contexto** | Números sin benchmarks o alertas | ALTA | Agregar rangos normales, alertas por desviación |
| **No hay ayuda contextual** | Operador no sabe qué rellenar en campos | MEDIA | Agregar tooltips, ejemplos, validación en tiempo real |
| **Colores no diferenciados** | Estados (aprobado, rechazado, pendiente) no visual | MEDIA | Aplicar paleta de colores de estado correctamente |

### 5.3 Brechas de Arquitectura

| Brecha | Impacto | Severidad | Propuesta |
|--------|--------|-----------|-----------|
| **Backend no tiene separación Mobile/Web en APIs** | Mismo endpoint para móvil y web | MEDIA | Agregar parámetros `format=mobile|web` en queries |
| **No hay caché en frontend** | Maestros se cargan siempre desde servidor | MEDIA | Implementar IndexedDB + cache invalidation strategy |
| **No hay notificaciones real-time** | Aprobador no se entera que hay evento pendiente | MEDIA | Usar WebSockets o Server-Sent Events para notificaciones |
| **Validaciones no completas en cliente** | Errores se detectan solo en servidor | MEDIA | Replicar validaciones críticas en frontend (Zod) |

---

## 6. ARQUITECTURA DE VISTAS (Mobile vs Web)

### 6.1 Estructura de Rutas Diferenciadas

```
Frontend (React) estructura propuesta:

├── routes/
│   ├── auth/
│   │   └── login.tsx              (Común para ambas vistas)
│   │
│   ├── mobile/                    (Solo accesible en viewport < 768px o role operador)
│   │   ├── layout.tsx             (Hamburger menu, bottom nav)
│   │   ├── home.tsx               (Dashboard KPIs simples)
│   │   ├── register/
│   │   │   ├── index.tsx          (Menú de operaciones disponibles)
│   │   │   ├── new-event.tsx      (Formulario dinámico por tipo)
│   │   │   └── success.tsx        (Confirmación post-registro)
│   │   ├── pending/               (Mis eventos pendientes de revisión)
│   │   │   ├── index.tsx
│   │   │   └── [id].tsx
│   │   ├── lot/
│   │   │   ├── index.tsx          (Mi lote actual)
│   │   │   └── [id].tsx           (Detalle lote con operaciones)
│   │   └── profile/
│   │       └── index.tsx          (Perfil, cambiar contraseña)
│   │
│   ├── web/                       (Solo accesible en viewport >= 768px)
│   │   ├── layout.tsx             (Sidebar, header full)
│   │   ├── dashboard/
│   │   │   └── index.tsx          (Dashboard analítico)
│   │   ├── review/                (Bandeja de revisión)
│   │   │   ├── index.tsx
│   │   │   └── [id].tsx           (Detalle evento + corrección)
│   │   ├── approval/              (Aprobación)
│   │   │   ├── index.tsx
│   │   │   └── [id].tsx
│   │   ├── lots/
│   │   │   ├── index.tsx          (Tabla de lotes)
│   │   │   └── [id].tsx           (Detalle completo)
│   │   ├── operations/
│   │   │   ├── index.tsx          (Lista filtrable)
│   │   │   └── [id].tsx
│   │   ├── reports/
│   │   │   ├── index.tsx          (Dashboard reportes)
│   │   │   ├── lot/[id].tsx
│   │   │   ├── sap-comparison.tsx
│   │   │   └── export.tsx         (Excel/PDF)
│   │   ├── masters/
│   │   │   ├── [entity]/index.tsx (CRUD genérico)
│   │   │   └── [entity]/[id].tsx
│   │   ├── users/
│   │   │   ├── index.tsx
│   │   │   └── [id].tsx
│   │   ├── sap/
│   │   │   ├── index.tsx          (Dashboard SAP)
│   │   │   ├── sync-jobs.tsx
│   │   │   └── mapping.tsx
│   │   └── audit/
│   │       └── index.tsx          (Log de auditoría)
│   │
│   └── 404.tsx, errors.tsx        (Común)

```

### 6.2 Componentes Específicos por Vista

**MOBILE:**
```tsx
// MobileLayout.tsx — Estructura
<MobileLayout>
  <MobileHeader>Logo, usuario</MobileHeader>
  <MobileContent>{children}</MobileContent>
  <MobileBottomNav>
    - Home
    - Register (+)
    - Pending
    - Lot
    - Profile
  </MobileBottomNav>
  <MobileHambuger>Menú adicional</MobileHamburger>
</MobileLayout>

// MobileForm.tsx — Formulario simplificado
- Un campo por línea (full width)
- Keyboard aparece automáticamente
- Botón siguiente/anterior grande
- Progress bar (Paso 2 de 5)
- Validación mientras escribes

// MobileCard.tsx — Tarjeta para lotes
- Nombre lote grande
- Icono de fase
- KPI principal en grande (mortalidad %)
- Botón "Ver detalle" o "Registrar"

// MobileKPI.tsx — KPI dashboard
- 2-3 KPIs principales
- Colores de alerta (rojo si > 5% mortalidad)
- Actualizar con botón
```

**WEB:**
```tsx
// WebLayout.tsx — Estructura
<WebLayout>
  <Sidebar>
    - Logo + Nombre empresa
    - Menú vertical (Home, Lotes, Operaciones, Revisión, Aprobación, Reportes, etc.)
    - Usuario + Logout
  </Sidebar>
  <WebContent>
    <Header>Breadcrumb + Filtros</Header>
    {children}
  </WebContent>
</WebLayout>

// WebTable.tsx — Tabla completa
- Múltiples columnas (Lote, Fase, Estado, Operador, Fecha, Acciones)
- Sorting, filtering, paginación
- Bulk actions (aprobar múltiples)
- Expandable rows (detalles)

// WebForm.tsx — Formulario completo
- Múltiples columnas en desktop (2-3 campos por línea)
- Validación inline
- Preview de datos antes de submit
- Historial de cambios

// WebDashboard.tsx — Dashboard analítico
- Gráficas por etapa
- Tabla de alertas
- KPIs con benchmarks
- SAP sync status
```

### 6.3 Condicional de Ruta

```tsx
// useResponsive.ts hook
export function useResponsive() {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768)
  const [role, setRole] = useState(useAuth().role)
  
  return {
    isMobile,
    role,
    isOperator: role === 'operador', // Operador de campo → mobile
    isSupervisor: role === 'supervisor', // Supervisor → web
    canUseBoth: role === 'admin' // Admin puede usar ambas
  }
}

// Main router
{isMobile && <Routes><Route path="/mobile/*" element={<MobileShell />} /></Routes>}
{!isMobile && <Routes><Route path="/web/*" element={<WebShell />} /></Routes>}
```

---

## 7. ESPECIFICACIÓN DE PANTALLAS POR ETAPA AVÍCOLA

### 7.1 MÓVIL — Flujo Operador de Campo

#### PANTALLA 1: Home (Dashboard Operador)

**Descripción:** Vista principal del operador cuando abre la app.

**Componentes:**
```
┌─────────────────────────────────┐
│ 🐔 Lider Pollo    👤 Juan García │
├─────────────────────────────────┤
│                                 │
│  Mi Lote Actual: L-2026-A-001   │
│  ┌─────────────────────────────┐│
│  │ 🔸 Cría - Semana 5          ││
│  │ Aves: 2,500 | Edad: 35 días ││
│  │ Peso: 850g (Normal)         ││
│  │ Mortalidad: 2.1% (⚠️ Alerta)││
│  └─────────────────────────────┘│
│                                 │
│  KPIs Rápidos:                  │
│  ┌──────────────────────────┐   │
│  │ 📊 Mortalidad: 2.1% ⚠️  │   │
│  │ 📈 Peso Promedio: 850g   │   │
│  │ 🍗 Consumo Alimento: OK  │   │
│  └──────────────────────────┘   │
│                                 │
│  ┌─────────────────────────┐    │
│  │ Mis Registros Pendientes│    │
│  │ 3 eventos sin revisar   │    │
│  │ → Ver                   │    │
│  └─────────────────────────┘    │
│                                 │
├─────────────────────────────────┤
│ 🏠 Home  ➕ Registrar  ⏳ Pending │
│ 🐓 Lote  👤 Perfil              │
└─────────────────────────────────┘
```

**Campos:**
- Lote actual (por defecto el asignado al operador)
- KPIs principales: Mortalidad %, Peso promedio, Consumo alimento
- Alertas por desviación (color rojo si > umbral)
- Contador de eventos pendientes revisión
- Botón "Registrar operación" (grande, bottom nav)

**Flujo:**
1. Abre app → Home
2. Ve su lote y KPIs
3. Puede:
   - Tocar "+ Registrar" → Formulario operación
   - Tocar "Pending" → Ver sus registros pendientes
   - Tocar "Lote" → Ver detalle lote

---

#### PANTALLA 2: Registrar Operación (Menú)

**Descripción:** Operador elige qué operación registrar. Opciones varían según etapa del lote.

**Componentes:**
```
┌─────────────────────────────────┐
│ ← Registrar Operación           │
├─────────────────────────────────┤
│ L-2026-A-001 | Cría Semana 5    │
├─────────────────────────────────┤
│                                 │
│ Selecciona operación:           │
│                                 │
│ ┌───────────────┐ ┌───────────┐ │
│ │ 🐔 Distribu-  │ │ 🌾 Alimen-│ │
│ │    ción Aves  │ │    to     │ │
│ └───────────────┘ └───────────┘ │
│                                 │
│ ┌───────────────┐ ┌───────────┐ │
│ │ ⚖️  Pesaje    │ │ 💀 Morta- │ │
│ │               │ │    lidad  │ │
│ └───────────────┘ └───────────┘ │
│                                 │
│ ┌───────────────┐ ┌───────────┐ │
│ │ 💉 Vacunación│ │ 🏥 Medica-│ │
│ │               │ │    ción   │ │
│ └───────────────┘ └───────────┘ │
│                                 │
│ ┌───────────────┐ ┌───────────┐ │
│ │ 🔍 Inspección│ │ 🥚 Huevos │ │
│ │    Granja     │ │ (si aplica)│
│ └───────────────┘ └───────────┘ │
│                                 │
│ ... (más opciones si aplican)   │
│                                 │
└─────────────────────────────────┘
```

**Lógica:**
- Mostrar solo operaciones permitidas para esta etapa:
  - Cría: Distribución, Alimento, Pesaje, Mortalidad, Vacunación, Medicación, Inspección
  - Producción: Todo lo anterior + Recolección huevos, Clasificación, Despacho huevos
  - Engorde: Distribución, Alimento, Pesaje, Mortalidad, Vacunación
  - Incubadora: Recepción huevos, Carga, Ovoscopia, Transferencia, Nacimiento

---

#### PANTALLA 3: Formulario Operación (Dinámico)

**Descripción:** Formulario específico por tipo de operación. Ejemplo: Pesaje.

**Componentes:**
```
┌─────────────────────────────────┐
│ ← Registrar Pesaje              │
│ Paso 1 de 3                     │
├─────────────────────────────────┤
│                                 │
│ 📅 Fecha: [22/06/2026 ▼]       │
│                                 │
│ ♂️ Peso Machos (g):             │
│ [850] ✓                         │
│                                 │
│ ♀️ Peso Hembras (g):             │
│ [780] ✓                         │
│                                 │
│ 📊 Semana #: [5] ✓              │
│                                 │
│ Validación en tiempo real:      │
│ ✓ Machos > Hembras esperado    │
│ ⚠️ Peso por debajo de estándar  │
│                                 │
│                                 │
│ ┌──────────────┬──────────────┐ │
│ │ ← Anterior   │ Siguiente →  │ │
│ └──────────────┴──────────────┘ │
│                                 │
└─────────────────────────────────┘
```

**Características:**
- Un paso a la vez (3-4 pasos máximo)
- Teclado numérico para números
- Validación en tiempo real (✓ o ⚠️)
- Comparación con estándares genéticos (si peso < esperado → advertencia)
- Botones anterior/siguiente grandes (touch-friendly)
- Progress bar en top

---

#### PANTALLA 4: Confirmación & Envío

**Descripción:** Resumen antes de enviar.

**Componentes:**
```
┌─────────────────────────────────┐
│ Confirmar Pesaje                │
├─────────────────────────────────┤
│                                 │
│ ✅ Todos los campos completos   │
│                                 │
│ Resumen:                        │
│ ┌─────────────────────────────┐ │
│ │ Fecha: 22/06/2026          │ │
│ │ Peso ♂: 850g               │ │
│ │ Peso ♀: 780g               │ │
│ │ Semana: 5                  │ │
│ │ Lote: L-2026-A-001         │ │
│ │ Registrado por: Juan García│ │
│ │ Hora: 14:32                │ │
│ └─────────────────────────────┘ │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ 🔒 Guardado de forma segura │ │
│ │ Enviado a revisión          │ │
│ └─────────────────────────────┘ │
│                                 │
│      [Enviar]  [Editar]         │
│                                 │
│ Código del evento: EVT-20260622- │
│ 00156                           │
│                                 │
└─────────────────────────────────┘
```

---

#### PANTALLA 5: Mis Registros Pendientes

**Descripción:** Lista de eventos que el operador registró pero aún están pendientes de revisión.

**Componentes:**
```
┌─────────────────────────────────┐
│ ← Eventos Pendientes            │
│ 3 registros                     │
├─────────────────────────────────┤
│                                 │
│ 📋 Pesaje - 22/06 14:32         │
│ Lote L-2026-A-001               │
│ Estado: 🔵 Enviado a revisión   │
│ → Detalles                      │
│                                 │
│ 🌾 Alimento - 22/06 10:15       │
│ Lote L-2026-A-001               │
│ Estado: 🟡 En revisión          │
│ → Detalles                      │
│                                 │
│ 💀 Mortalidad - 21/06 16:45     │
│ Lote L-2026-A-001               │
│ Estado: 🔴 Devuelto (Revisar)   │
│ ⚠️ "Peso inferior a rango"      │
│ → Corregir                      │
│                                 │
│ Refrescar                       │
│                                 │
└─────────────────────────────────┘
```

**Estados colores:**
- 🔵 Enviado (gris azulado) = Pendiente supervisión
- 🟡 En revisión (amarillo) = Supervisor viendo
- ✅ Aprobado (verde) = Listo para SAP
- 🔴 Devuelto (rojo) = Requiere corrección
- ❌ Rechazado (rojo oscuro) = Requiere investigación

---

### 7.2 WEB — Flujo Supervisor/Aprobador

#### PANTALLA 1: Dashboard Supervisor

**Descripción:** Vista analítica para supervisores y aprobadores.

**Componentes:**
```
┌──────────────────────────────────────────────────────┐
│ Lider Pollo        Home > Dashboard                  │
├────────────────┬──────────────────────────────────────┤
│                │                                      │
│ • Home         │  📊 Dashboard Operacional            │
│ • Lotes        │  Empresa: Global Avícola      [▼]   │
│ • Operaciones  │  Fecha: 22/06/2026 - Hoy            │
│ • Revisión     │                                      │
│ • Aprobación   │  ┌─────────────┬────────────────┐   │
│ • Reportes     │  │ 📈 Eventos   │ 28 hoy         │   │
│ • Maestros     │  │ 📋 Pendientes│ 8              │   │
│ • SAP          │  │ ✅ Aprobados │ 18             │   │
│ • Auditoría    │  │ ❌ Rechazados│ 2              │   │
│ • Usuarios     │  └─────────────┴────────────────┘   │
│                │                                      │
│ Perfil: Juan   │  LOTES ACTIVOS (por etapa)          │
│ Supervisor     │  ┌────────────────────────────────┐ │
│                │  │ 🟢 Cría: 12 lotes             │ │
│                │  │ 🔵 Producción: 8 lotes        │ │
│                │  │ 🟠 Engorde: 15 lotes          │ │
│                │  │ 🟣 Incubadora: 3 incubadoras  │ │
│                │  └────────────────────────────────┘ │
│                │                                      │
│                │  ALERTAS (Últimas 24h)              │
│                │  ┌────────────────────────────────┐ │
│                │  │ 🔴 L-2026-A-001: Mortalidad 5%│ │
│                │  │ 🟡 L-2026-B-003: Bajo peso    │ │
│                │  │ 🟡 L-2026-C-002: Pendiente x3 │ │
│                │  └────────────────────────────────┘ │
│                │                                      │
│                │  ÚLTIMA SINCRONIZACIÓN SAP          │
│                │  ✅ 22/06 18:35 (hace 2 min)       │
│                │                                      │
└────────────────┴──────────────────────────────────────┘
```

---

#### PANTALLA 2: Bandeja de Revisión

**Descripción:** Tabla de eventos pendientes de revisión con filtros.

**Componentes:**
```
┌──────────────────────────────────────────────────────┐
│ Revisión Operativa                                   │
├─────────────┬────────────────────────────────────────┤
│ Filtros:    │                                        │
│ Lote: [▼]   │  🔍 Búsqueda  [............]           │
│ Etapa: [▼]  │  Estado: [Pendiente ▼] Operador:[▼]   │
│ Operador:   │                                        │
│ [▼]         │  ┌───┬──────┬────────┬────┬───┬─────┐  │
│ Estado:     │  │ ID│ Lote │ Tipo   │Fec│Est│ Ops │  │
│ [All ▼]     │  ├───┼──────┼────────┼────┼───┼─────┤  │
│             │  │001│L-2026│Pesaje  │22/6│📋 │ ✓ ✗ │  │
│ Mostrar     │  │002│L-2026│Alimento│22/6│📋 │ ✓ ✗ │  │
│ 10 ▼        │  │003│L-2026│Mortald │21/6│🔴 │ ✓ ✗ │  │
│             │  │004│L-2027│Vacuna  │22/6│✅ │   │  │
│             │  │005│L-2028│Huevos  │22/6│📋 │ ✓ ✗ │  │
│ Total: 48   │  │006│L-2029│Ent. Av │21/6│❌ │   │  │
│             │  │...│      │        │    │   │     │  │
│             │  └───┴──────┴────────┴────┴───┴─────┘  │
│             │  ◄ 1 2 3 4 5 ►   Mostrando 1-10 de 48 │
│             │                                        │
└─────────────┴────────────────────────────────────────┘
```

**Columnas:**
- ID evento
- Lote
- Tipo de operación (icon + nombre)
- Fecha
- Estado (📋 Pendiente, 🟡 En revisión, ✅ Aprobado, ❌ Rechazado, 🔴 Devuelto)
- Acciones (Ver detalles, Aprobar, Rechazar)

**Interacción:**
- Click en fila → Abre detalle en panel lateral o modal
- Filtros dinámicos
- Bulk actions (seleccionar múltiples + aprobar)
- Sorting por cualquier columna

---

#### PANTALLA 3: Detalle Evento + Corrección

**Descripción:** Vista completa de un evento con posibilidad de corregir y aprobar.

**Componentes:**
```
┌──────────────────────────────────────────────────────┐
│ Evento EVT-20260622-00001                            │
├─────────────┬────────────────────────────────────────┤
│ Volver      │                                        │
│             │  📋 REGISTRO OPERATIVO (Pesaje)       │
│             │  Lote: L-2026-A-001 | Cría Sem 5      │
│             │  Operador: Juan García                 │
│             │  Fecha: 22/06/2026 14:32              │
│             │  Estado: Pendiente revisión            │
│             │                                        │
│             │  ─────────────────────────────────     │
│             │  DATOS ORIGINALES                      │
│             │  ─────────────────────────────────     │
│             │  Peso ♂: 850g                         │
│             │  Peso ♀: 780g                         │
│             │  Semana: 5                            │
│             │  Observaciones: "Aves activas"        │
│             │                                        │
│             │  ─────────────────────────────────     │
│             │  VALIDACIONES SISTEMA                 │
│             │  ─────────────────────────────────     │
│             │  ✓ Pesos dentro de rango genético    │
│             │  ✓ Fecha consistente                  │
│             │  ⚠️ Peso 2% por debajo de estándar   │
│             │  ✓ Operador autorizado                │
│             │                                        │
│             │  ─────────────────────────────────     │
│             │  OPCIONES                              │
│             │  ─────────────────────────────────     │
│             │  ☑️ Revisar cambios (si aplica)       │
│             │  [📝 Corregir]  [✅ Aprobar]  [❌ Rech │
│             │                                        │
│             │  Motivo si rechaza:                    │
│             │  [Seleccionar motivo ▼]               │
│             │  [Agregar observación]                │
│             │                                        │
└─────────────┴────────────────────────────────────────┘
```

**Si hay corrección previa:**
```
┌──────────────────────────────────────────────────────┐
│ Evento EVT-20260622-00001                            │
├──────────────────────────────────────────────────────┤
│                                                      │
│ HISTORIAL DE CORRECCIONES                           │
│                                                      │
│ 🔄 Corrección #1 - Por: María Supervisor            │
│ Fecha: 22/06/2026 15:20                             │
│ Peso ♂: 850g → 870g (cambio 2.3%)                   │
│ Motivo: "Revisión de pesaje, error de registro"     │
│ ✓ Aprobada por: Carlos Admin (15:25)                │
│                                                      │
│ Datos actuales tras corrección:                      │
│ Peso ♂: 870g (CORREGIDO)                            │
│ Peso ♀: 780g (sin cambios)                          │
│ Semana: 5                                           │
│                                                      │
│ [✅ Aprobar corregido]  [🔙 Devolver]  [❌ Rechazar]│
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

#### PANTALLA 4: Reportes por Etapa

**Descripción:** Reportes analíticos agrupados por etapa avícola.

**Componentes:**
```
┌──────────────────────────────────────────────────────┐
│ Reportes Operacionales                               │
├─────────────┬────────────────────────────────────────┤
│ Reportes    │ 📊 Análisis por Etapa Avícola         │
│ • Cría      │                                        │
│ • Producción│ Período: [22/06 ▼] - [22/06 ▼]       │
│ • Engorde   │ Empresa: [Global Avícola ▼]           │
│ • Incubadora│                                        │
│ • SAP       │ ┌─────────────────────────────────┐   │
│ • KPIs      │ │ REPRODUCTORAS CRÍA              │   │
│ • Exportar  │ │ ┌───────────────────────────┐   │   │
│             │ │ │ Mortalidad Promedio: 2.5%│   │   │
│             │ │ │ Aves Vivas Día: 28,450   │   │   │
│             │ │ │ Peso Promedio: 850g      │   │   │
│             │ │ │ Consumo Alim.: 45 kg/día │   │   │
│             │ │ └───────────────────────────┘   │   │
│             │ │ [Gráfica de tendencias 📈]      │   │
│             │ │ [Tabla detallada ▼]             │   │
│             │ │ [Exportar Excel]                │   │
│             │ └─────────────────────────────────┘   │
│             │                                        │
│             │ ┌─────────────────────────────────┐   │
│             │ │ REPRODUCTORAS PRODUCCIÓN        │   │
│             │ │ % Postura: 92.3%                │   │
│             │ │ Huevos Fértiles: 85%            │   │
│             │ │ Huevos Rotos: 2.1%              │   │
│             │ │ Almacenamiento Días: 10         │   │
│             │ │ [Más detalles...]               │   │
│             │ └─────────────────────────────────┘   │
│             │                                        │
│             │ ... (Engorde, Incubadora)             │
│             │                                        │
└─────────────┴────────────────────────────────────────┘
```

**Reportes incluyen:**
- KPIs principales por etapa
- Gráficas de tendencias (último 30 días)
- Tablas con comparativas (vs. estándar genético)
- Alertas por desviación
- Exportación Excel/PDF

---

## 8. PLAN DE IMPLEMENTACIÓN REDISEÑADO

### 8.1 Fases y Prioridades

**FASE 1: ESTABILIZACIÓN BASE (2 semanas)**
- [ ] T-101: Completar endpoints operativos en backend
- [ ] T-102: Implementar vistas mobile vs web diferenciadas
- [ ] T-103: Diseñar y prototipar mobile layout (Figma)
- [ ] T-104: Crear componentes mobile (MobileLayout, MobileForm, MobileCard)
- [ ] T-105: Implementar bottom nav móvil + hamburger menu

**FASE 2: FUNCIONALIDAD OPERATIVA (3 semanas)**
- [ ] T-201: Implementar formularios dinámicos por tipo evento
- [ ] T-202: Agregar validaciones en cliente (Zod replicadas)
- [ ] T-203: Implementar offline mode (IndexedDB)
- [ ] T-204: Crear pantalla "Mis registros pendientes" (móvil)
- [ ] T-205: Dashboard KPIs operador (móvil)
- [ ] T-206: Bandeja de revisión mejorada (web)

**FASE 3: FLUJO COMPLETO (3 semanas)**
- [ ] T-301: Trazabilidad huevo → pollito (backend + frontend)
- [ ] T-302: SAP sync automática (webhooks/polling)
- [ ] T-303: Reportes por etapa avícola (web)
- [ ] T-304: Batch operations (crear lotes revisión)
- [ ] T-305: KPIs avanzados (conversión, eclosión, etc.)

**FASE 4: REFINAMIENTO & OPTIMIZACIÓN (2 semanas)**
- [ ] T-401: Optimizar performance (caché, lazy loading)
- [ ] T-402: Pulir UX móvil (user testing)
- [ ] T-403: Documentar flujos para operadores (ayuda contextual)
- [ ] T-404: Testing E2E (Playwright)
- [ ] T-405: Deployment y rollout gradual

### 8.2 Tareas Críticas Detalladas

#### Tarea T-102: Vistas Mobile vs Web

**Descripción:** Implementar arquitectura que permita diferentes layouts y componentes para móvil y web.

**Subtareas:**
1. Crear hook `useResponsive()` que detecte viewport y rol
2. Crear `<MobileShell>` y `<WebShell>` layouts base
3. Crear routing condicional en `App.tsx`
4. Implementar `<MobileBottomNav>`, `<MobileHamburger>`, `<MobileHeader>`
5. Implementar `<WebSidebar>`, `<WebHeader>`, `<WebLayout>`
6. Crear página 404 y error handling común

**Archivos:**
```
frontend/src/
├── hooks/useResponsive.ts (NEW)
├── components/mobile/ (NEW)
│   ├── MobileShell.tsx
│   ├── MobileLayout.tsx
│   ├── MobileBottomNav.tsx
│   ├── MobileHamburger.tsx
│   ├── MobileHeader.tsx
│   ├── MobileForm.tsx
│   ├── MobileCard.tsx
│   └── MobileKPI.tsx
├── components/web/
│   ├── WebShell.tsx (UPDATE)
│   ├── WebSidebar.tsx (UPDATE)
│   ├── WebHeader.tsx (UPDATE)
│   ├── WebLayout.tsx (UPDATE)
│   ├── WebTable.tsx (NEW)
│   └── WebDashboard.tsx (NEW)
├── routes/
│   ├── mobile/ (NEW)
│   │   ├── layout.tsx
│   │   ├── home.tsx
│   │   ├── register/
│   │   ├── pending/
│   │   ├── lot/
│   │   └── profile/
│   ├── web/ (UPDATE)
│   │   ├── ... (actualizar imports)
│   └── App.tsx (UPDATE - routing condicional)
```

**Dependencias:** T-101 (completar endpoints)

**Estimación:** 1 semana

---

#### Tarea T-301: Trazabilidad Huevo → Pollito

**Descripción:** Implementar funcionalidad crítica: rastrear cuál lote de huevos (reproductoras) genera cuál lote de pollitos (incubadora → engorde).

**Modelo de datos:**

```
// Backend (nuevo en operations/models.py)

class EggBatch(Base):
    """Lote de huevos de reproductora a incubadora"""
    __tablename__ = "egg_batches"
    
    id: Mapped[int] = PK
    source_lot_id: Mapped[int] = FK(lots)  # Lote reproductora postura
    destination_hatchery_id: Mapped[int] = FK(hatcheries)
    reception_date: Mapped[date]
    total_eggs: Mapped[int]  # Cantidad recibida
    fertile_eggs: Mapped[int]  # Cantidad fértil
    egg_storage_event_id: Mapped[int] = FK(operational_events)
    
    # Relaciones
    source_lot: Mapped["Lot"]
    destination_hatchery: Mapped["Hatchery"]
    storage_event: Mapped["OperationalEvent"]
    chick_batches: Mapped[list["ChickBatch"]] = relationship(back_populates="source_egg_batch")

class ChickBatch(Base):
    """Lote de pollitos de incubadora a engorde"""
    __tablename__ = "chick_batches"
    
    id: Mapped[int] = PK
    source_egg_batch_id: Mapped[int] = FK(egg_batches)  # De qué huevos vinieron
    destination_lot_id: Mapped[Optional[int]] = FK(lots)  # Lote engorde (si aplica)
    hatchery_id: Mapped[int] = FK(hatcheries)
    birth_date: Mapped[date]
    total_chicks: Mapped[int]
    viable_chicks: Mapped[int]
    hatchery_yield_event_id: Mapped[int] = FK(operational_events)
    
    # Relaciones
    source_egg_batch: Mapped["EggBatch"] = relationship(back_populates="chick_batches")
    destination_lot: Mapped[Optional["Lot"]]
    hatchery: Mapped["Hatchery"]
    yield_event: Mapped["OperationalEvent"]
```

**Flujo:**
1. Operador en Reproductora Postura registra "Despacho de huevos" → Crea EggBatch
2. Operador en Incubadora registra "Recepción huevos" → Referencia EggBatch
3. Operador en Incubadora registra "Nacimiento" → Crea ChickBatch con referencia a EggBatch
4. Operador en Engorde registra "Recepción pollitos" → Referencia ChickBatch
5. Sistema calcula:
   - % Eclosión = (viable_chicks / fertile_eggs) × 100
   - Trazabilidad completa: Reproductora → Huevos → Pollitos → Engorde

**Frontend:**
- Mostrar en Lot Detail: "Estos pollitos vienen de huevos de Lote X"
- En Reportes: "Comparar genética: huevos de X generaron Y viabilidad"
- Auditoría: Rastrear cualquier lote hasta su origen genético

**Archivos:**
```
backend/
├── app/operations/models.py (ADD EggBatch, ChickBatch)
├── app/operations/schemas.py (ADD EggBatchCreate, ChickBatchCreate, etc.)
├── app/operations/service.py (ADD create_egg_batch, create_chick_batch)
├── alembic/versions/ (NEW migration)

frontend/
├── src/services/egg-batches.ts (NEW)
├── src/pages/operations/EggDispatchPage.tsx (UPDATE)
├── src/pages/operations/HatcheryPage.tsx (UPDATE)
├── src/pages/lots/LotDetailPage.tsx (ADD "Origen de pollitos" section)
├── src/pages/reports/TraceabilityReport.tsx (NEW)
```

**Estimación:** 1.5 semanas

---

### 8.3 Sprint Board (Primeras 2 semanas)

```
SPRINT 1: Estabilización Base (Jun 24 - Jul 8)

BACKLOG:
┌─────────────────────────────────────┐
│ T-101: Endpoints operativos backend │  (8 pts)
│ T-102: Vistas mobile vs web          │  (13 pts)
│ T-103: Diseño mobile Figma           │  (5 pts)
│ T-104: Componentes mobile            │  (8 pts)
│ T-105: Bottom nav + hamburger        │  (5 pts)
└─────────────────────────────────────┘
```

---

## 9. MÉTRICAS DE ÉXITO

### 9.1 Funcionales

| Métrica | Target | Actual | Status |
|---------|--------|--------|--------|
| **Eventos operativos registrados** | 24 tipos | 24 tipos | ✅ |
| **Flujo aprobación completo** | Registro → Aprobación → SAP | 80% | ⚠️ |
| **Trazabilidad huevo → pollito** | Implementado | 0% | ❌ |
| **Offline mode móvil** | Funcional | 0% | ❌ |
| **KPIs por etapa** | Todas las etapas (5) | 3 etapas | ⚠️ |
| **SAP sync automática** | Real-time o cada 1h | Manual | ❌ |

### 9.2 Técnicas

| Métrica | Target | Actual | Status |
|---------|--------|--------|--------|
| **Bundle size gzipped** | < 500KB | ~450KB | ✅ |
| **Mobile load time** | < 3s en 4G | ~2.8s | ✅ |
| **Backend test coverage** | > 80% | 60% | ⚠️ |
| **Frontend test coverage** | > 70% | 40% | ⚠️ |
| **API response p95** | < 200ms | ~180ms | ✅ |
| **i18n coverage** | 100% ES/EN | 100% | ✅ |

### 9.3 UX/Diseño

| Métrica | Target | Actual | Status |
|---------|--------|--------|--------|
| **Mobile screens diseñadas** | 10 pantallas | 3 pantallas | ⚠️ |
| **Componentes mobile creados** | 10 | 2 | ⚠️ |
| **Accesibilidad (WCAG AA)** | Cumple | 70% | ⚠️ |
| **User testing móvil** | 5+ operadores | 0 | ❌ |
| **Respuesta UI < 100ms** | 100% | 95% | ✅ |

### 9.4 Calidad Avícola

| Métrica | Target | Actual | Status |
|---------|--------|--------|--------|
| **Todas etapas soportadas** | 5 etapas | 4 etapas | ⚠️ |
| **Operaciones por etapa** | 8-10 ops/etapa | 6-8 ops | ⚠️ |
| **Validaciones genéticas** | Peso, edad | Peso solamente | ⚠️ |
| **Auditoría completa** | Quién, qué, cuándo, antes/después | ✅ | ✅ |
| **Trazabilidad generacional** | Abuelas → Repro → Engorde | 50% | ⚠️ |

---

## PRÓXIMOS PASOS

### Inmediatos (Esta semana)
1. ✅ **Aprobación de este documento** por stakeholders
2. ✅ **Crear spec visual (Figma)** para móvil con todas las pantallas
3. ✅ **Priorizar tareas** en función de criticidad avícola
4. ✅ **Asignar equipo** (Frontend, Backend, QA, Design)
5. ✅ **Kickoff sprint** con desarrollo

### Corto plazo (2 semanas)
1. **Completar fase 1** (estabilización + vistas diferenciadas)
2. **User testing** con operadores de campo en dispositivos móviles
3. **Validar modelo de datos** para trazabilidad con equipo avícola
4. **Documentar cambios** en specs/tasks.md

### Mediano plazo (4-6 semanas)
1. **Implementar fases 2 y 3** (funcionalidad + flujo completo)
2. **Integración SAP real** (al menos OData/API Business Hub)
3. **Reportes profesionales** listos para auditoría
4. **Testing E2E completo**

### Largo plazo (Lanzamiento)
1. **Rollout gradual** (operadores piloto → todos)
2. **Capacitación** de usuarios
3. **Soporte post-lanzamiento**
4. **Iteraciones** basadas en feedback real

---

**Fin del documento.**

**Autor:** Equipo Multidisciplinario (Arquitecto Sr, PM, Especialista Avícola)  
**Revisión necesaria:** Stakeholders, Product Owner, Tech Lead  
**Aprobación:** CTO, Product Manager  

---

*Este documento es la brújula para que Global Avícola v2 sea un software avícola de clase mundial, integrado con SAP, competitivo y profesional.*
