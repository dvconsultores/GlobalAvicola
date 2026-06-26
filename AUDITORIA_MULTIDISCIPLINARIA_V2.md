# AUDITORÍA MULTIDISCIPLINARIA — GLOBAL AVÍCOLA v2
### Equipo de 12 Especialistas | Revisión Integral de Sistema

> **Fecha de emisión:** 2026-06-26  
> **Versión del prompt:** 2.0  
> **Estado:** ACTIVO — Ejecutar antes de continuar implementación  
> **Principio rector:** La app anterior (Lider Pollo) define el MÍNIMO funcional. Mejorar y agregar; nunca eliminar funcionalidad existente.

---

## 🎯 CONTEXTO EJECUTIVO

**Global Avícola** es una plataforma empresarial web/mobile para la gestión operativa integral del ciclo productivo avícola. Actúa como capa auxiliar de captura operativa sobre **SAP S/4HANA**, que es el sistema administrativo/contable mandante.

### Stack tecnológico actual
- **Frontend:** React 19 / Vite 8 / TypeScript / TailwindCSS v4 / react-i18next (ES/EN)
- **Backend:** FastAPI / Python 3.11+ / SQLAlchemy 2.x async / Alembic / PostgreSQL 15+
- **Auth:** JWT + RBAC granular con `company_id` isolation
- **Integración:** Adapter pattern SAP S/4HANA (OData/SOAP/IDoc, modo manual inicial)
- **Infra:** Docker + Nginx + GitHub Actions → Docker Hub → Watchtower auto-deploy

### Documentación base disponible (ordenada por prioridad)
| Documento | Ruta | Relevancia |
|-----------|------|------------|
| Especificación funcional principal | `docs/02-functional-spec.md` | ⭐⭐⭐ |
| Modelo de dominio | `docs/03-domain-model.md` | ⭐⭐⭐ |
| Spec driven (SpecKit) | `specs/global-avicola/spec.md` | ⭐⭐⭐ |
| Auditoría sistema legacy | `docs/01-legacy-audit.md` | ⭐⭐⭐ |
| Matriz de cobertura viejo→nuevo | `docs/15-cross-reference-old-vs-new.md` | ⭐⭐⭐ |
| Auditoría vs Recomendación Central | `docs/16-audit-recomendacion-central.md` | ⭐⭐⭐ |
| Plan técnico | `docs/04-technical-plan.md` | ⭐⭐ |
| Contrato de API | `docs/06-api-contract.md` | ⭐⭐ |
| Estrategia integración SAP | `docs/10-sap-integration-strategy.md` | ⭐⭐ |
| Flujo de aprobación | `docs/12-approval-workflow.md` | ⭐⭐ |
| Estrategia de auditoría | `docs/13-audit-strategy.md` | ⭐⭐ |
| Plan QA | `docs/07-qa-plan.md` | ⭐ |

### Documentación del cliente (carpeta `Imagen de Procesos Documentado/`)
| Archivo | Tipo | Contenido |
|---------|------|-----------|
| `Sap y App Proceso Avícola Software primera version.pdf` | PDF | Flujo de proceso original SAP ↔ App — **fuente primaria de integración** |
| `Bases Consideradas en el Desarrollo de la App Avicola.pdf` | PDF | Requerimientos base originales del cliente |
| `Control de Codificación de Procesos Avicolas PROTINAL.xlsx` | Excel | Codificación de todos los procesos |
| `Recomendación central.pdf` | PDF | 26 secciones de recomendaciones SAP S/4HANA ↔ App |
| `App mobile avicola - capture pantallas.docx` | Word | Capturas de pantalla de la app móvil anterior (Lider Pollo) |
| `Sistema avicola administrativo - capture pantallas.pdf` | PDF | Capturas del frontend web administrativo anterior |
| `Formato Especificaciones Incubadoras.xlsx` | Excel | Formato de especificaciones de incubadoras |
| `PESADAS/Abuelas/` | Carpeta | Formatos de abuelas (Cría, Producción, Huevo Fértil, Incubadora) |
| `PESADAS/Reproductoras/` | Carpeta | Formatos de reproductoras pesadas |
| `LIVIANAS/Ponedoras/` | Carpeta | Formatos ponedoras (AVI-GRA-PON-01/02/03.xlsx) |
| `LIVIANAS/Reproductoras/` | Carpeta | Formatos reproductoras livianas |
| `PolloEngordeCoob.pdf` / `PolloEngordeRoss.pdf` | PDF | Guías técnicas Cobb y Ross para engorde |
| `ReproductoraRoss.pdf` / `ReproductorasCoob.pdf` | PDF | Guías técnicas Cobb y Ross para reproductoras |
| `Proceso de Avicola - Modificado-1.0.png` | Imagen | Diagrama del proceso avícola completo |
| `Incubadora.pdf` | PDF | Especificaciones técnicas de incubadora |

### Auditorías anteriores
- `AUDITORIA_COMPLETA.md` — Auditoría multidisciplinaria anterior (95/100, sin críticos detectados en ese momento)
- `GLOBAL_AVICOLA_AUDIT_REPORT.md`, `GLOBAL_AVICOLA_AUDIT_REPORT_v3.md` — Reportes anteriores
- `GLOBAL_AVICOLA_UI_UX_NAVIGATION_AUDIT.md` — Auditoría UI/UX

---

## 🚨 HALLAZGO CRÍTICO IDENTIFICADO EN PRODUCCIÓN

**Contexto:** Probando en vivo la funcionalidad de **Inspección de Granja** (`farm_inspection`), se detectó que la implementación actual registra los parámetros de forma **cualitativa** (Bueno/Regular/Malo), cuando la versión anterior capturaba **valores reales numéricos por galpón**.

### Lo que existe hoy en el código (`OperationFormPage.tsx` líneas 498-540):
```tsx
// Inspección de Granja — IMPLEMENTACIÓN ACTUAL (DEFICIENTE)
// Solo 4 parámetros a nivel de granja con dropdown bueno/regular/malo:
// - Temperatura → select: Bueno / Regular / Malo
// - Humedad → select: Bueno / Regular / Malo  
// - Condición de Cama → select: Bueno / Regular / Malo
// - Estado de Equipos → select: Bueno / Regular / Malo
```

### Lo que capturaba la versión anterior (sistema legacy Lider Pollo):
```
INSPECCIÓN DE GRANJA (por registro):
├── Granja (selección)
├── Lote (selección)
├── Fecha de inspección
├── Por cada GALPÓN de la granja:
│   ├── Galpón ID / nombre
│   ├── Capacidad operativa del galpón
│   ├── Temperatura real (°C) — valor numérico
│   ├── Humedad real (%) — valor numérico
│   ├── Concha de arroz / cama:
│   │   ├── Campo observación textual
│   │   └── (implícito: estado por galpón)
│   └── Equipos del galpón:
│       └── Por cada equipo: nombre + condición (texto libre)
└── Observaciones generales
```

**Campos en el legacy backend identificados:**
- `granja_id`, `lote_id`, `fecha_inspeccion`
- `condicion_cama` (texto), `temperatura` (numérico), `humedad` (numérico)
- `equipos[]` — array de equipos con condición
- Entidades: `InspeccionesGranjas`, `EquiposInspecciones`

**Impacto del hallazgo:**
- Pérdida de trazabilidad de valores reales ambientales (bienestar animal)
- Imposible correlacionar temperatura/humedad real con mortalidad o desempeño
- No se puede generar KPI de condiciones ambientales históricas
- Se pierde el control por galpón (la granja puede tener 10+ galpones con condiciones muy diferentes)
- Las guías técnicas Cobb/Ross requieren rangos específicos de T° y H° por semana de vida

---

## 👥 ROL DE CADA ESPECIALISTA

---

### 🟦 ESPECIALISTA 1: SAP S/4HANA

**Leer obligatoriamente:**
- `docs/10-sap-integration-strategy.md` completo
- `docs/16-audit-recomendacion-central.md` completo
- `Imagen de Procesos Documentado/Sap y App Proceso Avícola Software primera version.pdf`
- `Imagen de Procesos Documentado/Recomendación central.pdf`
- `specs/global-avicola/spec.md` §4.3 (SAP References)

**Preguntas clave a responder:**

1. **Datos maestros SAP faltantes:** En `docs/16-audit-recomendacion-central.md` se identificaron 12 items sin implementar (❌). ¿Cuáles son bloqueantes para la operación real? Específicamente:
   - Inventario en tiempo real (MM — sin consulta de stock ❌)
   - Centros de costo (CO — sin modelo ❌)
   - Cierre contable/logístico (sin validación de período fiscal ❌)
   - Consumos/mermas/bajas (sin modelo ❌)

2. **Integración en tiempo real vs batch:** ¿El modo manual (CSV/JSON upload) es suficiente para el volumen operativo de Global Avícola? ¿Cuándo se requiere OData en tiempo real?

3. **Materiales críticos para mapear:** ¿Qué materiales SAP deben estar mapeados ANTES de que un operador pueda registrar alimento, vacunas o medicamentos? ¿Cómo se gestiona el caso de material sin código SAP?

4. **Recepción de mercancía (Goods Receipt 101):** ¿El payload actual de `SapPayload` tiene todos los campos requeridos por MM para una entrada de mercancía de aves vivas? Revisar campos: Movement type, Batch, Plant, Storage Location, Quantity.

5. **Multi-compañía SAP:** ¿Cada compañía tiene su propio mandante SAP (client) o comparten mandante con distintos centros (plants)? Esto impacta la arquitectura de `sap_config` por compañía.

6. **Variante de valoración:** ¿Las aves y el alimento usan precio estándar o precio medio variable en SAP? Esto determina si la app necesita capturar precios unitarios.

7. **Inspección de granja → SAP:** ¿Los datos ambientales (T°, H°) por galpón deben enviarse a algún módulo SAP (QM - Quality Management, PP - Production Planning)? ¿O son solo operativos de la app?

**Entregable:** Lista priorizada de gaps SAP con impacto/esfuerzo, y los 3 primeros a resolver para v1.1.

---

### 🐔 ESPECIALISTA 2: Incubadora

**Leer obligatoriamente:**
- `docs/15-cross-reference-old-vs-new.md` §3 (Incubadora)
- `Imagen de Procesos Documentado/Incubadora.pdf`
- `Imagen de Procesos Documentado/Formato Especificaciones Incubadoras.xlsx`
- `specs/global-avicola/spec.md` §4.7 (Hatchery)
- `Imagen de Procesos Documentado/PESADAS/Abuelas/Incubadora/` — todos los archivos
- `Imagen de Procesos Documentado/PESADAS/Reproductoras/Incubadora/` — todos los archivos

**Hallazgo crítico a evaluar:** La inspección de incubadora (`hatchery_inspection`) tiene el mismo problema que la inspección de granja: solo captura parámetros como "bueno/regular/malo" en lugar de valores reales.

**Preguntas clave a responder:**

1. **Parámetros por máquina:** ¿Los parámetros de incubación (T°, H°, CO₂, volteo) deben registrarse por máquina incubadora individual o por lote incubado? En la práctica, ¿cuántas máquinas puede tener una incubadora?

2. **Setpoints vs actuals:** ¿Se debe registrar solo el valor real medido, o también el setpoint (valor programado) para calcular la desviación? Las guías Ross/Cobb tienen rangos muy precisos por día de incubación.

3. **Ovoscopia (candling):** La spec menciona días 7 y 14. ¿Es suficiente dos veces o se requiere registro diario de temperatura interna del huevo (egg temperature) como hacen algunos sistemas modernos?

4. **Nacedora (Hatcher):** ¿Los parámetros de la nacedora son iguales a los de la incubadora o difieren? ¿Se registran por separado? En la entidad actual, ¿la nacedora tiene su propio evento de inspección?

5. **Tasa de nacimiento por lote origen:** ¿El sistema actual permite rastrear que un lote de huevos de una granja de reproductoras X tiene una tasa de eclosión de Y%? ¿Es calculable hacia atrás?

6. **Vacunación in ovo:** ¿Está contemplado el registro de vacunación in ovo (día 18) vs vacunación spray post-nacimiento? ¿Son eventos separados?

7. **Concha de arroz en incubadora:** ¿La incubadora también usa concha de arroz u otro material de cama? ¿Cómo se registra?

8. **Formato Especificaciones Incubadoras.xlsx:** ¿Los campos de ese formato están todos contemplados en la spec actual? Listar campos faltantes.

**Entregable:** Formulario completo de inspección de incubadora con todos los campos y tipos de dato requeridos por proceso real.

---

### 🐓 ESPECIALISTA 3: Reproductoras

**Leer obligatoriamente:**
- `docs/15-cross-reference-old-vs-new.md` §1 (Reproductora Cría) y §2 (Reproductora Producción)
- `Imagen de Procesos Documentado/ReproductoraRoss.pdf`
- `Imagen de Procesos Documentado/ReproductorasCoob.pdf`
- `Imagen de Procesos Documentado/PESADAS/Reproductoras/` — todos los formatos
- `Imagen de Procesos Documentado/LIVIANAS/Reproductoras/` — todos los formatos
- `specs/global-avicola/spec.md` §4.5 y §4.6
- Capturas pantalla: `App mobile avicola - capture pantallas.docx`

**Hallazgo a evaluar:** La inspección de granja para reproductoras captura solo 4 parámetros cualitativos. Las guías Ross y Cobb tienen tablas precisas de temperatura ambiente requerida por semana de vida que no pueden verificarse con el registro actual.

**Preguntas clave a responder:**

1. **Inspección por galpón:** ¿En una granja de reproductoras con 8 galpones, se registra una inspección de granja con un solo registro de temperatura/humedad promedio, o un registro por galpón? ¿La práctica real de campo requiere datos por galpón?

2. **Concha de arroz (cama):** ¿Cuáles son los parámetros que se deben registrar para la cama de concha de arroz?
   - ¿Profundidad (cm)?
   - ¿Estado cualitativo (seca/húmeda/amoniacal)?
   - ¿Cantidad de gapones (¿galpones?) con cama renovada?
   - ¿Frecuencia de remoción/volteo?

3. **Peso por sexo:** ¿La pesaje semanal siempre incluye machos y hembras por separado? ¿Cuántas aves se pesan como muestra (cantidad mínima estadísticamente válida)?

4. **Ratio macho:hembra:** ¿Se registra el ratio macho:hembra actual en cada inspección o solo en eventos específicos? La app legacy tenía este dato.

5. **Curva de postura:** ¿El sistema debe comparar el % de postura actual vs la curva estándar Ross/Cobb? ¿Hay alertas automáticas por desviación?

6. **Clasificación de huevos:** ¿Los huevos "sucios" y "rotos" se registran por separado por galpón o solo a nivel de granja? ¿Hay un proceso de lavado que afecta la fertilidad?

7. **Formatos PESADAS/Reproductoras:** ¿Los formatos Excel del cliente tienen campos adicionales no contemplados en la spec? Hacer mapping exhaustivo.

8. **Transición Cría→Producción:** ¿Hay parámetros de cierre de cría que deben registrarse (peso promedio final, uniformidad de lote %, condición corporal) antes de habilitar la fase de producción?

**Entregable:** Checklist de campos por formulario de reproductoras (cría y producción) con marcación de los que están implementados vs los que faltan.

---

### 🐣 ESPECIALISTA 4: Pollo de Engorde

**Leer obligatoriamente:**
- `docs/15-cross-reference-old-vs-new.md` §4 (Pollo de Engorde)
- `Imagen de Procesos Documentado/PolloEngordeCoob.pdf`
- `Imagen de Procesos Documentado/PolloEngordeRoss.pdf`
- `specs/global-avicola/spec.md` §4.8 (Broiler)
- Capturas pantalla legacy: `Sistema avicola administrativo - capture pantallas.pdf`

**Preguntas clave a responder:**

1. **Etapas de alimentación:** Engorde tiene 4 fases de alimento (pre-iniciador, iniciador, crecimiento, finalizador). ¿El tipo de alimento en `FeedMovement` es suficiente para distinguirlas, o se necesita un campo de fase/período?

2. **Conversión alimenticia (FCR) por semana:** ¿Se requiere calcular FCR semanal además del acumulado? ¿Las guías Cobb/Ross tienen FCR objetivo por semana que el sistema deba comparar?

3. **Uniformidad del lote:** ¿Se registra el coeficiente de variación (CV%) del peso en cada pesaje? Es un KPI crítico en engorde.

4. **Índice de Producción Europeo (IPE):** La matriz de cobertura marca `⚠️ GAP`. ¿Es obligatorio para el cliente? Fórmula: `IPE = (Viabilidad % × Ganancia Diaria × 100) / (FCR × 10)`.

5. **Factor de corrección AFCR:** La matriz marca `⚠️ GAP`. ¿Qué es exactamente el AFCR ajustado que usa Global Avícola?

6. **Temperatura en engorde:** Las guías Ross/Cobb tienen una curva de temperatura muy específica (semana 1: 30-32°C, bajando gradualmente). ¿La inspección de granja actual puede capturar si se está siguiendo esta curva?

7. **Densidad poblacional:** ¿Se registra la densidad (aves/m²) en el galpón? Es crítico para bienestar animal y certificaciones.

8. **Cierre de lote → Planta de beneficio:** ¿Se registra peso promedio de canal, rendimiento en canal (%), decomiso en planta? ¿Estos datos regresan a la app desde la planta?

9. **Mortalidad acumulada vs diaria:** ¿Se requiere el desglose de mortalidad por causa cada día, o solo el total diario y la causa al cierre?

**Entregable:** Lista de KPIs de engorde requeridos por el cliente con su fórmula y datos fuente necesarios.

---

### 🐥 ESPECIALISTA 5: Progenitoras (Abuelas/Grandparent)

**Leer obligatoriamente:**
- `docs/15-cross-reference-old-vs-new.md` §5 (NUEVO: Abuelas)
- `specs/global-avicola/spec.md` §4.4 (Grandparent Importation)
- `Imagen de Procesos Documentado/PESADAS/Abuelas/` — todos los formatos
- `Imagen de Procesos Documentado/Procesos Avicolas/suplement macho cobb.pdf`
- `Imagen de Procesos Documentado/Bases Consideradas en el Desarrollo de la App Avicola.pdf`

**Contexto:** Las progenitoras son una etapa **nueva** que no existía en la app legacy. Se parte de cero, pero basado en los formatos del cliente.

**Preguntas clave a responder:**

1. **Flujo completo de importación:** ¿El plan de importación de abuelas tiene los campos de documentación sanitaria (certificado sanitario de origen, resultados de laboratorio, cuarentena en aduana)? ¿Qué organismos regulatorios están involucrados en Venezuela/LATAM?

2. **Formatos PESADAS/Abuelas:** Revisar los archivos:
   - `Formato Especificaciones Control de Producción - Borrador.xlsx`
   - `Formato Especificaciones Desalojo - Borrador.xlsx`
   - `Formato Especificaciones Recepción de Abuelas - Borrador.xlsx`
   - `Formato Especificaciones Recepción producción abuelas - Borrador.xlsx`
   - `Formato Especificaciones de Procesos control de producción HF - Borrador.xlsx`
   
   ¿Todos los campos de estos formatos están contemplados en los eventos operativos actuales?

3. **Genealogía:** ¿Se necesita registrar la línea genealógica (abuelo paterno, abuelo materno) además de la línea genética? ¿Cómo se traza la genealogía de reproductoras → progenitoras?

4. **Cría de machos vs hembras progenitoras:** ¿Los machos de progenitoras van siempre a reproductoras? ¿Hay un proceso de selección de machos?

5. **Inspección de granja de progenitoras:** ¿Los parámetros son iguales que reproductoras o hay diferencias específicas (son aves más exigentes ambientalmente)?

**Entregable:** Validación campo por campo de los formatos del cliente vs implementación actual.

---

### 🏗️ ESPECIALISTA 6: Arquitecto de Software

**Leer obligatoriamente:**
- `docs/04-technical-plan.md` completo
- `docs/03-domain-model.md` completo
- `specs/global-avicola/spec.md` completo
- `AUDITORIA_COMPLETA.md` §1 (Auditoría de Arquitectura)
- Código: `backend/app/operations/models.py`, `backend/app/masters/models.py`
- Código: `frontend/src/pages/operations/OperationFormPage.tsx`

**Problemas confirmados para diseñar solución:**

**PROBLEMA CENTRAL: Inspección de Granja**
El modelo actual de inspección (`inspection_details`) es una lista de parámetros + estado cualitativo:
```python
# Modelo ACTUAL (insuficiente):
class InspectionDetail:
    parameter: str   # "Temperatura"
    status: str      # "good" | "regular" | "bad"
    value: float     # campo existe pero NO se usa en UI
    notes: str
```

Se necesita:
```python
# Modelo REQUERIDO:
class FarmInspectionRecord:
    farm_id: UUID
    lot_id: UUID
    date: date
    general_observations: str
    
    houses: List[HouseInspectionDetail]

class HouseInspectionDetail:
    house_id: UUID                  # Galpón
    operational_capacity: int       # Capacidad operativa actual
    temperature_c: float            # Valor real °C (no cualitativo)
    humidity_pct: float             # Valor real % (no cualitativo)
    litter_condition: str           # "buena" | "regular" | "humeda" | "amoniacal"
    litter_notes: str               # Observaciones de concha de arroz
    equipment_list: List[EquipmentCondition]

class EquipmentCondition:
    equipment_name: str
    condition: str                  # texto libre o enum
    notes: str
```

**Preguntas arquitectónicas a responder:**

1. **Migración de datos:** El campo `inspection_details` ya tiene datos en producción. ¿La solución es:
   a) Nueva tabla `house_inspection_details` con relación al `OperationalEvent`?
   b) Ampliar el schema JSON del campo `inspection_details`?
   c) Nuevo `event_type` separado (`house_inspection`)?
   Justificar con impacto en Alembic, backward compatibility, UI.

2. **Multi-compañía — verificación de aislamiento:**
   - ¿Todas las queries del backend aplican `WHERE company_id = ?`?
   - ¿El Super Admin puede ver TODOS los datos sin filtro?
   - ¿Los JWT incluyen `company_id` y se validan en cada request?
   - ¿Los endpoints de maestros (farms, houses) aplican el filtro correctamente?
   - Revisar: `backend/app/dependencies.py`, `backend/app/auth/security.py`

3. **Hooks y Services pendientes:** `AUDITORIA_COMPLETA.md` identifica que los 9 hooks y 10 servicios modulares especificados no existen. ¿Son necesarios AHORA o pueden esperar a v2?

4. **Selector de compañía:** El usuario con acceso a múltiples compañías necesita un selector en el frontend. ¿Dónde se almacena la compañía activa? ¿En el JWT o en el estado local?

5. **Performance de inspección masiva:** Si una granja tiene 20 galpones y se hace inspección diaria, eso son 20 registros por evento. ¿El modelo actual soporta esto sin degradación?

6. **Validaciones de negocio críticas ausentes:**
   Revisar `docs/01-legacy-audit.md` §7.2 — hay 14 reglas ausentes. ¿Cuáles están ya implementadas en el backend nuevo? Hacer auditoría de `backend/app/operations/service.py`.

**Entregable:** Propuesta de modelo de datos para `HouseInspectionDetail` con migration Alembic y análisis de impacto en endpoints existentes.

---

### 🎨 ESPECIALISTA 7: Diseñador Gráfico Empresarial

**Leer obligatoriamente:**
- `docs/11-ui-ux-design-system.md` completo
- `GLOBAL_AVICOLA_UI_UX_NAVIGATION_AUDIT.md` completo
- `GLOBAL_AVICOLA_UI_IMPLEMENTATION_PLAN.md`
- `REDESIGN_SUMMARY.md`
- Código: `frontend/src/index.css` (design tokens "Precision Azul")
- Código: `frontend/src/pages/operations/OperationFormPage.tsx` — leer COMPLETO
- Código: `frontend/src/data/processCatalog.ts` — todos los eventos y flujos
- Capturas pantalla legacy: `Imagen de Procesos Documentado/App mobile avicola - capture pantallas.docx`
- Capturas pantalla legacy: `Imagen de Procesos Documentado/Sistema avicola administrativo - capture pantallas.pdf`

**Sistema de diseño actual "Precision Azul" — referencia obligatoria:**
| Token | Valor | Uso |
|-------|-------|-----|
| `--color-bg` | `#F4F6F9` | Fondo general |
| `--sidebar-from/to` | `#071829 → #0F3361` | Sidebar gradiente |
| Acento principal | `#1A6DCC` | Botones, links, activo |
| Superficies | `#FFFFFF` + `shadow-card` | Cards, formularios |
| Tipografía | Inter 300-700 | Todo el sistema |
| Border radius cards | `rounded-2xl` | Todas las tarjetas |
| Estado activo sidebar | Píldora blanca + texto `#0B2340` | Nav items |
| Header gradiente mobile | `#071829 → #0F3361` | Barra superior móvil |

---

#### HALLAZGO CRÍTICO CONFIRMADO EN REVISIÓN EN VIVO (2026-06-26)

**Se revisaron visualmente las 24 operaciones de los 6 procesos.** El formulario `OperationFormPage.tsx` usa **UN SOLO formulario genérico** para todas las operaciones. Resultado:

| Estado | Cantidad | Detalle |
|--------|----------|---------|
| 🔴 Roto / Incorrecto | 14 | Campos incorrectos o completamente ausentes |
| 🟡 Parcial | 6 | Campos básicos presentes pero incompletos |
| ✅ Correcto | 0 | Ningún formulario cubre el 100% de los campos requeridos |

---

#### PROBLEMAS DE DISEÑO POR CATEGORÍA

**A. Formularios con sección completamente equivocada:**

| Operación | Sección que muestra HOY | Sección que DEBE mostrar |
|-----------|------------------------|--------------------------|
| `vaccination` | "Movimiento de Aves" (sexo/cantidad/peso) | Vacuna del catálogo + dosis + vía de aplicación |
| `medication` | "Movimiento de Aves" | Medicamento + dosis + duración + diagnóstico |
| `birth_registration` | "Movimiento de Aves" | Nacidos totales / viables / débiles / muertos |
| `grandparent_import` | "Movimiento de Aves" | País origen / certif. sanitario / cuarentena / aduana |
| `transport_inspection` | 4 parámetros de GRANJA (cama, T°, H°, equipos) | Condición cajillas / densidad / T° viaje / ventilación |
| `ovoscopy` | "Registro de Huevos" tipo+cantidad | Fértiles / infértiles / embriones muertos tempranos / tardíos / contaminados |

**B. Formularios con campos incompletos — diseño a completar:**

| Operación | Falta en diseño |
|-----------|-----------------|
| `farm_inspection` / `hatchery_inspection` | Datos **por galpón**: T° real (°C), H° real (%), cama (texto), equipos (lista). HOY solo tiene dropdowns bueno/regular/malo a nivel global |
| `bird_reception` | Proveedor / Raza / OC SAP / Galpón destino / Machos y hembras separados |
| `bird_distribution` | Tabla de distribución por galpones (galpón + cantidad) |
| `mortality_recording` | Machos + hembras en mismo formulario / Causa (catálogo) |
| `weight_recording` | Machos y hembras separados / Tamaño de muestra |
| `egg_collection` | Todos los tipos a la vez: fértil + sucio + roto + infértil + descartado + peso promedio |
| `egg_dispatch` / `egg_reception_hatchery` | Incubadora destino/origen / Transporte / Condiciones viaje |
| `incubation_load` | Máquina incubadora específica / CO₂ / Volteo (frecuencia/ángulo) |
| `transfer_to_hatcher` | Nacedora destino / Día de incubación (debe ser 18) |
| `chick_dispatch` | Granja destino / Lote destino / Transporte / Certificado sanitario |
| `lot_closure` | Población final / FCR total / Peso promedio final / Mortalidad acumulada / Motivo cierre |
| `bird_exit` | Destino (granja o planta de beneficio) / Transporte / OC SAP |
| `cull_recording` | Causa de descarte (catálogo) |
| `feed_registration` | Fase de alimento (pre-iniciador/iniciador/crecimiento/finalizador) / Galpón |

---

#### PROBLEMAS DE DISEÑO SISTÉMICOS

1. **Arquitectura de formulario — problema raíz:**
   El wizard tiene 3 pasos: Proceso → Lote+Operación → **UN formulario genérico**. El Paso 3 debe
   renderizar secciones **específicas por tipo de operación**, no un único template.
   
   Patrón propuesto:
   ```
   OperationFormPage
   └── Step 3 → switch(event_type):
       ├── 'farm_inspection'      → <FarmInspectionSection />  (por galpón, T° numérica)
       ├── 'transport_inspection' → <TransportInspectionSection /> (cajillas, densidad)
       ├── 'vaccination'          → <VaccinationSection />     (vacuna, dosis, vía)
       ├── 'medication'           → <MedicationSection />      (med, dosis, duración)
       ├── 'mortality_recording'  → <MortalitySection />       (M+F, causa)
       ├── 'egg_collection'       → <EggCollectionSection />   (todos los tipos juntos)
       ├── 'bird_reception'       → <BirdReceptionSection />   (M+F, proveedor, raza)
       ├── 'bird_distribution'    → <DistributionSection />    (tabla por galpón)
       ├── 'birth_registration'   → <BirthSection />           (nacidos/viables/débiles)
       ├── 'lot_closure'          → <LotClosureSection />      (resumen final)
       └── ... etc (24 tipos)
   ```

2. **Patrón UX para operaciones con múltiples filas (mobile-first):**
   Las siguientes operaciones requieren captura de N filas (N variable):
   - `bird_distribution`: 1 fila por galpón (puede ser 2-20 galpones)
   - `farm_inspection`: 1 card por galpón (puede ser 2-20 galpones)
   - `egg_collection`: 5 tipos fijos en 1 pantalla (no N filas)
   - `mortality_recording`: 1 fila machos + 1 fila hembras = 2 filas fijas
   
   Patrones de diseño a evaluar para móvil:
   - **Cards acordeón por ítem** — tap para expandir/colapsar cada galpón
   - **Wizard por ítem** — "Galpón 1 de 8 → Siguiente"
   - **Tabla compacta inline** — campos en columnas pequeñas (no recomendado en móvil)

3. **Indicadores de rango técnico en tiempo real:**
   Los formularios de inspección de granja deben mostrar si la T° y H° ingresadas
   están dentro del rango esperado según la semana de vida del lote.
   
   Ejemplo visual requerido:
   ```
   Temperatura: [ 28.5 °C ] ✅ Dentro del rango (semana 3: 26-30°C)
   Temperatura: [ 35.2 °C ] ⚠️ FUERA DE RANGO (semana 3: 26-30°C)
   ```
   
   Fuente de rangos: guías técnicas Ross/Cobb por semana de vida (archivos PDF del cliente).

4. **Inspección de transporte — diseño desde cero:**
   Los campos actuales son incorrectos. Diseñar formulario específico con:
   - Vehículo/placa (texto)
   - Condición de cajillas/jaulas: dropdown (buenas / regular / malas)
   - Densidad aves/m²: campo numérico
   - Temperatura en viaje (°C): campo numérico
   - Ventilación: dropdown (adecuada / insuficiente)
   - Tiempo de viaje (minutos): campo numérico
   - Observaciones generales

5. **Colores de estado y alertas:**
   El sistema de diseño actual tiene `accent-bar-green/amber/red`. Usar consistentemente:
   - Verde `#22C55E` → valores dentro de rango
   - Ámbar `#F59E0B` → valores en zona de precaución
   - Rojo `#EF4444` → valores fuera de rango / alerta crítica

6. **Multi-compañía UI:**
   - Selector de compañía en el header (dropdown pequeño junto al nombre del usuario)
   - Badge de compañía activa siempre visible en sidebar header
   - Confirmación modal al cambiar de compañía ("¿Cambiar a [Empresa B]? Los datos no guardados se perderán.")

7. **Dashboard segmentado por compañía:**
   El dashboard admin muestra KPIs globales. Con multi-compañía:
   - Filtro de compañía en la barra de KPIs
   - Super Admin: selector "Todas las empresas" + filtro por empresa específica
   - Usuario normal: solo ve su compañía (sin selector)

---

#### REVISIÓN DE PANTALLAS DEL LEGACY — qué rescatar

Revisar obligatoriamente en `App mobile avicola - capture pantallas.docx`:
- Cómo el app móvil anterior organizaba la captura de datos por galpón
- El patrón de tabs (Alimento / Pesaje / Mortalidad / Vacunación) en la app web anterior
- Cómo se mostraba la distribución de aves por galpón
- El formulario de inspección de granja (pantalla de referencia)

Revisar en `Sistema avicola administrativo - capture pantallas.pdf`:
- Layout del dashboard administrativo anterior
- Cómo se visualizaban los KPIs por fase
- El patrón de tablas con filtros de la app web

---

**Entregables requeridos:**

1. **Sistema de secciones por operación:** Especificación visual de qué campos mostrar para cada uno de los 24 tipos de evento, con tipología de campo (numérico, texto, select, fecha, tabla dinámica).

2. **Wireframes mobile:** Pantallas para las 5 operaciones más usadas en campo:
   - `farm_inspection` (por galpón, T° y H° numéricos, cama, equipos)
   - `mortality_recording` (machos + hembras + causa)
   - `egg_collection` (todos los tipos simultáneos + peso promedio)
   - `weight_recording` (machos + hembras + muestra)
   - `vaccination` (vacuna + dosis + vía)

3. **Wireframes desktop:** Para las 3 operaciones más complejas administrativamente:
   - `bird_reception` (proveedor + raza + OC SAP + distribución por galpón)
   - `lot_closure` (resumen ejecutivo del lote: FCR + mortalidad + peso final)
   - `birth_registration` (nacidos / viables / débiles / muertos + tasa eclosión)

4. **Guía de componentes reutilizables:** Qué componentes de UI son comunes a múltiples formularios:
   - `HouseSelector` — selector de galpón con capacidad
   - `SexQuantityRow` — fila machos/hembras con totales
   - `EggTypeGrid` — grilla de tipos de huevo con cantidades
   - `RangeIndicator` — indicador visual de rango técnico
   - `CatalogSelect` — selector de catálogo con búsqueda (vacunas, medicamentos, causas)
   - `DistributionTable` — tabla de distribución por galpón

---

### ⚙️ ESPECIALISTA 8: Tech Lead Backend

**Leer obligatoriamente:**
- `backend/app/operations/models.py` completo
- `backend/app/operations/service.py` completo
- `backend/app/operations/router.py` completo
- `backend/app/masters/models.py` completo
- `backend/alembic/versions/` — todas las migraciones
- `docs/06-api-contract.md` completo

**Auditoría técnica requerida:**

1. **Modelo `InspectionDetail` actual:**
   ```python
   # Verificar en operations/models.py:
   # ¿Tiene campo `value: float` además de `status: str`?
   # ¿Hay tabla separada para equipos por galpón?
   # ¿Hay relación `house_id` en InspectionDetail?
   ```

2. **Endpoint de inspección:**
   - `POST /operations` con `event_type=farm_inspection` — ¿qué campos acepta actualmente?
   - ¿Valida que `house_id` pertenezca a la granja del lote?
   - ¿Permite múltiples galpones en un solo `OperationalEvent`?

3. **Multi-compañía — audit de código:**
   Verificar en CADA router/service:
   - `backend/app/masters/router.py` — ¿farms se filtran por `company_id`?
   - `backend/app/lots/service.py` — ¿lots se filtran por `company_id`?
   - `backend/app/operations/service.py` — ¿operations se filtran?
   - `backend/app/review/service.py` — ¿review items se filtran?
   - `backend/app/reports/service.py` — ¿reportes se filtran?
   - Endpoint `GET /dashboard/admin` — ¿agrega datos multi-empresa si es Super Admin?

4. **Validaciones de negocio faltantes (del legacy audit §7.2):**
   Verificar si están implementadas:
   - [ ] `mortality > saldo_disponible` → reject
   - [ ] `egg_dispatch > eggs_available` → reject
   - [ ] `incubator_load > eggs_received` → reject
   - [ ] `chick_dispatch > viable_chicks` → reject
   - [ ] `lot_close` requiere resumen final completo
   - [ ] `operation_date >= lot_activation_date`
   - [ ] `operation requires active lot`

5. **Idempotencia en operaciones:** ¿Las operaciones de registro tienen protección contra doble submit? ¿Hay `idempotency_key` a nivel de operación (no solo SAP)?

6. **Seeders para multi-compañía:** Los seeders actuales (`dev_seeds.py`) crean datos para una sola compañía. ¿Se necesitan datos de prueba para múltiples compañías?

7. **Índices de base de datos:** Con datos de múltiples compañías, ¿hay índices sobre `company_id` en todas las tablas principales?

**Entregable:** 
- Lista de endpoints que NO aplican filtro `company_id` correctamente
- Propuesta de migración Alembic para `HouseInspectionDetail`
- Lista de validaciones de negocio faltantes en `operations/service.py`

---

### 💻 ESPECIALISTA 9: Tech Lead Frontend

**Leer obligatoriamente:**
- `frontend/src/pages/operations/OperationFormPage.tsx` completo
- `frontend/src/data/navigationConfig.ts` completo
- `frontend/src/components/layout/` — todos los archivos
- `frontend/src/stores/` — todos los stores
- `frontend/public/locales/es/translation.json` y `en/translation.json`
- `docs/04-technical-plan.md` §Frontend

**Auditoría técnica requerida:**

1. **Formulario de inspección de granja — refactoring necesario:**
   
   El componente actual (líneas 498-540 de `OperationFormPage.tsx`) debe transformarse de:
   ```tsx
   // ACTUAL: Lista fija de 4 parámetros cualitativos
   {['Temperatura', 'Humedad', 'Condición de Cama', 'Estado de Equipos'].map(param => (
     <select value "good|regular|bad" />
   ))}
   ```
   
   A:
   ```tsx
   // REQUERIDO: Sección dinámica por galpón con valores reales
   // - Cargar galpones activos de la granja/lote seleccionado
   // - Por cada galpón: campos numéricos T°, H°, cama, equipos
   // - Indicador visual si T° o H° fuera de rango técnico
   ```
   
   ¿Cuál es el mejor approach? ¿`useFieldArray` de react-hook-form, estado local, o separar en sub-componente?

2. **Stores de Zustand — multi-compañía:**
   - ¿Existe un store para la compañía activa?
   - Si no: ¿se agrega a `auth.store` (companyId en user) o store separado?
   - ¿Cómo persiste entre refreshes? (localStorage / JWT claim)

3. **Hooks faltantes:** `AUDITORIA_COMPLETA.md` señala que los 9 hooks del plan no existen. Los más urgentes:
   - `useHouses(farmId)` — necesario para cargar galpones en formulario de inspección
   - `useCompany()` — para multi-compañía
   - `useOperations(lotId, eventType)` — para listar operaciones previas

4. **i18n — nuevas claves necesarias:**
   El formulario de inspección ampliado necesitará nuevas claves. Identificar y agregar a ambos idiomas:
   - `operations.houseInspection`, `operations.selectHouse`, `operations.operationalCapacity`
   - `operations.litterCondition`, `operations.litterNotes`, `operations.litterTypes.*`
   - `operations.equipmentName`, `operations.equipmentCondition`
   - `operations.tempOutOfRange`, `operations.humidityOutOfRange`

5. **Rendimiento mobile:** ¿El formulario de inspección con 10+ galpones y múltiples campos por galpón tiene buen rendimiento en un teléfono de gama media? ¿Se necesita virtualización?

6. **Estado del formulario:** Si el operador llena 5 galpones, el teléfono se queda sin batería, y vuelve — ¿se pierde el avance? ¿Se debe implementar borrador autosave en `localStorage`?

7. **Validaciones en cliente:** ¿El formulario actual valida rangos de T° y H°? Rango típico:
   - Temperatura: 18-32°C (varía por etapa)
   - Humedad: 40-80% (varía por etapa)

**Entregable:**
- Componente `HouseInspectionSection.tsx` propuesto con su interfaz TypeScript
- Lista de claves i18n faltantes para el nuevo formulario
- Evaluación de impacto en performance mobile

---

### 🔗 ESPECIALISTA 10: Integración SAP (técnico)

**Leer obligatoriamente:**
- `backend/app/integrations/` — estructura completa
- `docs/10-sap-integration-strategy.md` completo
- `docs/16-audit-recomendacion-central.md` §4 (Módulos SAP) y §5
- `specs/global-avicola/spec.md` §4.3

**Auditoría técnica requerida:**

1. **Adapter pattern — implementación actual:**
   ```
   backend/app/integrations/
   ├── ¿Existe __init__.py?
   ├── ¿Existe interface.py con ABC?
   ├── ¿Existe manual_adapter.py?
   ├── ¿Existe sap_s4hana_adapter.py (stub)?
   └── ¿Existe sap_service.py?
   ```
   ¿El adapter pattern está realmente implementado o es solo el servicio manual?

2. **Payload de Goods Receipt para aves:**
   ¿El payload actual de `SapPayload` para una recepción de aves tiene:
   - Movement type (101 = GR for PO)?
   - Batch number (lote SAP)?
   - Plant code?
   - Storage location?
   - Quantity (machos + hembras = total)?
   - Unit of measure (cabezas)?
   
3. **Multi-compañía en SAP:** ¿El `sap_config` por compañía está implementado? Si una compañía tiene SAP en mandante 100 y otra en mandante 200, ¿el adapter selecciona el correcto?

4. **Mock SAP para desarrollo:** ¿Existe un mock que simule respuestas SAP para testing sin acceso al sistema real? ¿Los tests usan el mock?

5. **Idempotencia SHA-256:** ¿El hash incluye `company_id` en su cálculo? Sin esto, un mismo movimiento operativo en dos compañías podría colisionar.

6. **Estado de sync y retry:** ¿`SapSyncJob` tiene timestamp de último intento? ¿El sistema de retry tiene backoff exponencial? ¿Hay alerta si un payload lleva más de N horas sin confirmar?

7. **Data faltante identificada:** `docs/16-audit-recomendacion-central.md` lista funciones de levantamiento de banderas operativas (❌) y adjunto de evidencias (❌). ¿Son requeridas para el envío a SAP o son solo operativas?

**Entregable:** Diagrama de flujo del adapter pattern actual y los gaps para llegar a OData real.

---

### 🗄️ ESPECIALISTA 11: Base de Datos

**Leer obligatoriamente:**
- `backend/app/operations/models.py` completo
- `backend/app/masters/models.py` completo
- `backend/alembic/versions/` — todas las migraciones en orden
- `docs/03-domain-model.md` completo
- `backend/app/database.py`

**Auditoría técnica requerida:**

1. **Modelo de inspección de granja — estado actual:**
   En `operations/models.py`, ¿cuál es el schema exacto de `InspectionDetail`?
   - ¿Tiene `house_id` (FK a House)?
   - ¿Tiene `temperature_c: Float`?
   - ¿Tiene `humidity_pct: Float`?
   - ¿Tiene `litter_condition: str`?
   - ¿Tiene tabla separada de equipos?
   
   **Si no tiene estos campos:** proponer migración Alembic de ALTER TABLE o nueva tabla.

2. **Aislamiento multi-compañía — verificación de constraints:**
   - ¿Hay CHECK constraints o FK constraints que garanticen que un `farm_inspection` no puede cruzar compañías?
   - ¿El índice `(company_id, lot_id)` existe en `OperationalEvent`?
   - ¿Hay Row Level Security (RLS) en PostgreSQL, o el aislamiento es solo por aplicación?

3. **Performance con multi-compañía:**
   - ¿Las tablas principales (`operational_events`, `lots`, `farms`) tienen índice en `company_id`?
   - ¿Hay índice compuesto `(company_id, created_at)` para queries de listado?
   - ¿Se usa paginación en todos los endpoints de listado?

4. **Integridad referencial de inspecciones:**
   - Un `OperationalEvent` de `farm_inspection` debe requerir que `farm_id`, `lot_id` y todos los `house_id` pertenezcan a la misma `company_id`. ¿Está esto validado a nivel de DB o solo aplicación?

5. **Propuesta de nueva tabla:**
   ```sql
   -- Propuesta: house_inspection_details
   CREATE TABLE house_inspection_details (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       operational_event_id UUID NOT NULL REFERENCES operational_events(id),
       house_id UUID NOT NULL REFERENCES houses(id),
       operational_capacity INT,
       temperature_c DECIMAL(5,2),
       humidity_pct DECIMAL(5,2),
       litter_condition VARCHAR(50),
       litter_notes TEXT,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   
   CREATE TABLE equipment_inspection_details (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       house_inspection_id UUID NOT NULL REFERENCES house_inspection_details(id),
       equipment_name VARCHAR(100) NOT NULL,
       condition VARCHAR(50),
       notes TEXT
   );
   ```
   Validar este esquema: ¿es correcto? ¿faltan campos? ¿hay conflictos con el modelo actual?

6. **Índices requeridos para el nuevo esquema:**
   ```sql
   CREATE INDEX ix_house_inspection_event_id ON house_inspection_details(operational_event_id);
   CREATE INDEX ix_house_inspection_house_id ON house_inspection_details(house_id);
   ```

7. **Seeders:** ¿Los seeds de desarrollo tienen datos de inspección de granja para probar el nuevo formulario? ¿Incluyen múltiples galpones por granja?

**Entregable:**
- Script SQL completo de las nuevas tablas
- Migration Alembic equivalente
- Lista de índices faltantes en el esquema actual

---

## 📋 AGENDA DE TRABAJO — ORDEN DE EJECUCIÓN

### FASE 0 (INMEDIATA) — Corrección del hallazgo crítico
> **Ejecutar antes de cualquier nuevo desarrollo**

| # | Tarea | Responsable | Dependencias |
|---|-------|-------------|--------------|
| 0.1 | Definir modelo completo de `HouseInspectionDetail` | Arq + DB + Avícola Reproductoras | Ninguna |
| 0.2 | Crear migration Alembic | Tech Lead Backend | 0.1 |
| 0.3 | Actualizar `POST /operations` para aceptar `house_inspections[]` | Tech Lead Backend | 0.2 |
| 0.4 | Crear componente `HouseInspectionSection.tsx` | Tech Lead Frontend | 0.1 |
| 0.5 | Integrar nuevo componente en `OperationFormPage.tsx` | Tech Lead Frontend | 0.4 |
| 0.6 | Agregar claves i18n nuevas | Tech Lead Frontend | 0.5 |
| 0.7 | Tests: backend + E2E | QA | 0.3, 0.5 |

### FASE 1 — Multi-compañía

| # | Tarea | Responsable | Dependencias |
|---|-------|-------------|--------------|
| 1.1 | Auditoría de aislamiento `company_id` en todos los endpoints | Tech Lead Backend | Ninguna |
| 1.2 | Corregir endpoints que no filtran por `company_id` | Tech Lead Backend | 1.1 |
| 1.3 | Agregar índices `company_id` en tablas principales | DB | 1.1 |
| 1.4 | Selector de compañía en frontend (header) | Tech Lead Frontend + Diseñador | Ninguna |
| 1.5 | Store `company` en Zustand | Tech Lead Frontend | 1.4 |
| 1.6 | Seed multi-compañía para desarrollo | Tech Lead Backend | 1.2 |

### FASE 2 — Completar funcionalidad mínima legacy

| # | Tarea | Responsable | Dependencias |
|---|-------|-------------|--------------|
| 2.1 | Implementar validaciones de negocio faltantes del legacy §7.2 | Tech Lead Backend | Ninguna |
| 2.2 | KPIs faltantes: IPE, AFCR, uniformidad de lote | Tech Lead Backend + Especialistas | 2.1 |
| 2.3 | Validar formatos Excel del cliente vs implementación | Especialistas Avícolas | Ninguna |
| 2.4 | Inspección de incubadora con valores reales | Tech Lead Backend + Frontend | 0.1 |
| 2.5 | Adjunto de evidencias (fotos de inspección) | Arquitecto + Backend + Frontend | Ninguna |

### FASE 3 — Mejoras y nuevas funcionalidades

| # | Tarea | Responsable | Dependencias |
|---|-------|-------------|--------------|
| 3.1 | Indicadores de rango técnico (curvas Ross/Cobb) en formularios | Frontend + Avícolas | 0.4 |
| 3.2 | Alertas por desviación (peso, mortalidad, T°, H°) | Backend + Frontend | 3.1 |
| 3.3 | SAP OData en tiempo real | Integración SAP | Ninguna |
| 3.4 | Banderas operativas | Backend + Frontend | Ninguna |
| 3.5 | Módulo CO (centros de costo) SAP | Integración SAP + SAP S4 | Ninguna |

---

## 🔴 REGLAS DE ORO DEL DESARROLLO

1. **La app anterior es el MÍNIMO.** Cada formulario, cada campo, cada flujo del sistema Lider Pollo debe existir en Global Avícola. Adicionar, nunca quitar.

2. **Valores reales, no cualitativos.** Temperatura es un número en °C. Humedad es un porcentaje. Un select "bueno/regular/malo" NUNCA reemplaza un valor numérico para datos ambientales.

3. **Granularidad por galpón.** Las condiciones de una granja con 10 galpones pueden variar enormemente. Siempre capturar datos al nivel más granular posible (por galpón, no por granja).

4. **SAP primero.** Antes de implementar cualquier nuevo tipo de operación, verificar qué datos necesita SAP para ese movimiento (movement type, fields requeridos).

5. **Multi-compañía desde el inicio.** Toda nueva entidad, endpoint y query debe incluir `company_id` desde el día 1. No hay retrofitting.

6. **Bilingüe siempre.** Ningún string hardcodeado. Todo `t('clave')`. Agregar clave a ES y EN simultáneamente.

7. **Auditoría total.** Cada cambio de dato deja registro de quién, cuándo, valor anterior, valor nuevo, motivo.

8. **Mobile-first real.** Cada formulario nuevo debe probarse en viewport 375px antes de desktop.

---

## 📊 ESTADO ACTUAL DEL SISTEMA

### Implementado y funcional ✅
- Login JWT + RBAC granular
- Maestros completos (19 catálogos)
- Lotes con fases productivas (6 ciclos)
- Operaciones: 24 event_types con validaciones básicas
- Flujo revisión → corrección → aprobación → SAP
- Auditoría total
- Dashboard admin + mobile
- Reportes KPI básicos
- Integración SAP (modo manual)
- UI/UX "Precision Azul" corporativa
- Bilingüe ES/EN completo
- CI/CD automático (Docker Hub + Watchtower)

### Gaps confirmados ⚠️

#### Gaps de formularios operativos (revisión visual en vivo — 2026-06-26)

Se revisaron los **24 formularios de operación** de los 6 procesos. Estado general:

| Estado | Cantidad | Descripción |
|--------|----------|-------------|
| 🔴 Roto / Incorrecto | 14 | Muestra sección equivocada o no tiene campos específicos |
| 🟡 Parcial / Incompleto | 6 | Tiene campos básicos pero faltan los requeridos por el proceso |
| ✅ Correcto | 0 | Ninguno cubre el 100% de campos operativos reales |

**Formularios con sección completamente incorrecta:**

| Operación | Problema | Afecta procesos |
|-----------|----------|-----------------|
| `vaccination` | Muestra "Movimiento de Aves" — debe mostrar vacuna/dosis/vía | Todos (6) |
| `medication` | Muestra "Movimiento de Aves" — debe mostrar medicamento/dosis/duración | Todos (6) |
| `transport_inspection` | Muestra parámetros de granja (cama, T°, H°) — debe mostrar cajillas/densidad/T° viaje | Todos (6) |
| `birth_registration` | Muestra "Movimiento de Aves" — debe mostrar nacidos/viables/débiles/muertos | Incubadora |
| `grandparent_import` | Muestra "Movimiento de Aves" — debe mostrar país origen/cert. sanitario/cuarentena | Progenitoras |
| `ovoscopy` | Muestra huevos genérico — debe mostrar fértiles/infértiles/embriones muertos | Incubadora |
| `farm_inspection` | Dropdowns bueno/regular/malo — debe ser valores numéricos T°/H° **por galpón** | Todos (excepto hatchery) |
| `hatchery_inspection` | Igual que farm_inspection — debe ser T°/H°/CO₂ por máquina | Incubadora |

**Formularios con campos incompletos:**

| Operación | Campos faltantes críticos | Afecta procesos |
|-----------|---------------------------|-----------------|
| `bird_reception` | Proveedor / Raza / OC SAP / Galpón / M+F separados | Todos |
| `bird_distribution` | Sin tabla de distribución por galpones | Todos |
| `mortality_recording` | Sin causa de muerte del catálogo / M+F en mismo registro | Todos |
| `weight_recording` | Sin M+F separados / sin tamaño de muestra | Todos |
| `egg_collection` | Solo 1 tipo a la vez — debe capturar todos los tipos simultáneamente | Prod/Progenitoras |
| `egg_dispatch` | Sin incubadora destino / transporte / condiciones viaje | Prod/Progenitoras |
| `egg_reception_hatchery` | Sin granja origen / orden de despacho / condiciones llegada | Incubadora |
| `incubation_load` | Sin máquina específica / CO₂ / volteo | Incubadora |
| `transfer_to_hatcher` | Sin nacedora destino / día de incubación | Incubadora |
| `chick_dispatch` | Sin granja destino / lote destino / transporte / certificado | Incubadora |
| `bird_exit` | Sin destino (granja o planta) / transporte / OC SAP | Todos |
| `lot_closure` | Solo lote+fecha+obs — sin FCR final / peso final / mortalidad acumulada | Engorde |
| `cull_recording` | Sin causa de descarte del catálogo | Todos |
| `feed_registration` | Sin fase de alimento (pre-iniciador/iniciador/crecimiento/finalizador) | Todos |

#### Otros gaps del sistema

| Gap | Severidad | Fase |
|-----|-----------|------|
| 14 formularios con sección incorrecta o completamente vacía de campos operativos | 🔴 CRÍTICO | 0 |
| Inspección de granja: valores cualitativos en vez de numéricos, sin datos por galpón | 🔴 CRÍTICO | 0 |
| Inspección de transporte: campos completamente incorrectos (muestra campos de granja) | 🔴 CRÍTICO | 0 |
| Vacunación y medicación: muestran sección de movimiento de aves (completamente incorrecto) | 🔴 CRÍTICO | 0 |
| Multi-compañía: spec define pero no verificado en todos los endpoints | 🔴 CRÍTICO | 1 |
| Validaciones de negocio del legacy (14 reglas sin implementar) | 🟡 Alto | 2 |
| KPIs faltantes: IPE, AFCR, uniformidad de lote | 🟡 Alto | 2 |
| Adjunto de evidencias / fotos de campo | 🟡 Alto | 2 |
| Componentes UI reutilizables pendientes: HouseSelector, SexQuantityRow, EggTypeGrid, RangeIndicator, CatalogSelect | 🟡 Alto | 2 |
| Banderas operativas | 🟡 Medio | 3 |
| SAP OData en tiempo real | 🟡 Medio | 3 |
| Indicadores de rango técnico Ross/Cobb en formularios | ⚪ Menor | 3 |
| Curvas técnicas Ross/Cobb integradas como referencia | ⚪ Menor | 3 |

---

## ✅ CRITERIOS DE ACEPTACIÓN PARA ESTE PROMPT

El equipo multidisciplinario habrá completado exitosamente su trabajo cuando:

1. **Cada especialista** haya revisado todos los documentos indicados en su sección
2. **Inspección de granja** tenga modelo definitivo aprobado por Especialista Avícola + Arquitecto + DB
3. **Multi-compañía** tenga auditoría completa de todos los endpoints con lista de correcciones
4. **Formatos del cliente** (Excel/PDF) tengan mapping 100% campo a campo vs implementación
5. **KPIs faltantes** tengan fórmula validada y datos fuente identificados
6. **Plan de ejecución** por fases tenga estimaciones y orden de prioridad acordado
7. **Sin regresiones:** ninguna funcionalidad del sistema Lider Pollo será eliminada

---

*Prompt construido con base en: documentación técnica, código fuente actual, auditorías previas, formatos del cliente y hallazgo crítico identificado en pruebas en vivo — 2026-06-26*
