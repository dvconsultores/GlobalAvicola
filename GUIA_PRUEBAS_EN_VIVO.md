# 🐔 GUÍA DE PRUEBAS EN VIVO — Global Avícola v2.0

> **Fecha:** 2026-06-29
> **Objetivo:** Pruebas funcionales multi-usuario simulando operación real de una empresa avícola integrada.
> **Duración estimada:** 2-3 horas por ciclo completo. Repetir varias veces.

---

## 1. CONFIGURACIÓN INICIAL

### 1.1 Credenciales de prueba

#### 📱 Usuarios MÓVILES (vista app / Telegram Mini App)

| Usuario | Contraseña | Rol | ¿Qué ve? |
|---|---|---|---|
| `movil.progenitoras` | `proge123` | Operador Progenitoras | Solo granjas de abuelas |
| `movil.reproductoras` | `repro123` | Operador Reproductoras | Solo granjas de reproductoras |
| `movil.incubadora` | `incu1234` | Operador Incubadora | Solo planta de incubación |
| `movil.engorde` | `engorde12` | Operador Engorde | Solo granjas de engorde |
| `movil.multiproceso` | `multi123` | Operador Multi-Proceso | **TODOS** los procesos |
| `movil.supervisor` | `super123` | Supervisor General | Revisa y corrige todo |
| `movil.contralor` | `contra123` | Contralor Avícola | Revisa, aprueba, rechaza, audita |

#### 🖥️ Usuarios WEB (vista escritorio)

| Usuario | Contraseña | Rol | ¿Qué ve? |
|---|---|---|---|
| `web.progenitoras` | `proge123` | Operador Progenitoras | Solo granjas de abuelas |
| `web.reproductoras` | `repro123` | Operador Reproductoras | Solo granjas de reproductoras |
| `web.incubadora` | `incu1234` | Operador Incubadora | Solo planta de incubación |
| `web.engorde` | `engorde12` | Operador Engorde | Solo granjas de engorde |
| `web.multiproceso` | `multi123` | Operador Multi-Proceso | **TODOS** los procesos |
| `web.supervisor` | `super123` | Supervisor General | Revisa y corrige todo |
| `web.contralor` | `contra123` | Contralor Avícola | Revisa, aprueba, rechaza, audita |
| `admin` | `admin123` | Super Administrador | Control total |

### 1.2 Cobertura mínima de datos (obligatoria)

Antes de convocar testers, la base debe cumplir como mínimo lo siguiente:

| Recurso | Mínimo requerido | Para qué se usa en pruebas |
|---|---|---|
| **Compañías operativas** | 2 con lotes + eventos + refs SAP | Validar segregación multiempresa real |
| **Usuarios por compañía** | Operador, Supervisor, Contralor/Aprobador | Flujo completo registro → revisión → aprobación |
| **Granjas/Galpones** | Al menos 3 granjas y 10+ galpones por compañía operativa | Cobertura por proceso y ubicación |
| **Lotes activos** | 4 o más por compañía operativa | Pruebas por proceso y concurrencia |
| **Lotes cerrados** | 1 o más por compañía operativa | Validar filtros, reportes e histórico |
| **Referencias SAP** | OCs + transferencias por compañía operativa | Pruebas BR-10 y trazabilidad SAP |
| **Estados de eventos** | `registered`, `pending_review`, `in_review`, `corrected`, `approved`, `rejected` | Ver evolución real de información |
| **Tipos de evento** | Recepción aves, alimento, huevos, despacho, incubación, mortalidad | Cobertura funcional de escenarios A-F |

### 1.3 Preflight de readiness (NO iniciar sin esto)

Ejecutar en backend:

```bash
cd backend
PYTHONPATH=. python3 seeds/live_readiness_check.py
```

Resultado esperado: `READY: live testing dataset meets minimum coverage.`

Si el resultado es `NOT READY`, cargar/reparar data y volver a validar:

```bash
cd backend
PYTHONPATH=. python3 seeds/dev_seeds.py
PYTHONPATH=. python3 seeds/integration_seeds.py
PYTHONPATH=. python3 seeds/live_data_boost.py
PYTHONPATH=. python3 seeds/live_readiness_check.py
```

---

## 2. ESTRUCTURA DEL FLUJO DE PRUEBA

Cada proceso avícola sigue esta secuencia. El objetivo es que **diferentes usuarios** ejecuten **diferentes partes** del flujo, simulando la operación real:

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ OPERADOR │───▶│SUPERVISOR│───▶│CORRECTOR │───▶│ APROBADOR│───▶│   SAP    │
│ Registra │    │  Revisa  │    │ Corrige  │    │ Aprueba/ │    │(pendiente)│
│ (mobile/ │    │  (web)   │    │ (web)    │    │ Rechaza  │    │          │
│  web)    │    │          │    │          │    │  (web)   │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

---

## 3. ESCENARIOS DE PRUEBA

### 🔵 ESCENARIO A: Progenitoras (Abuelas) — Ciclo Completo

**Participantes necesarios:** 4-5 personas
- Operador Progenitoras (mobile o web)
- Supervisor General (web)
- Contralor (web)
- Admin (web, opcional)

#### A.1 — Recepción de Aves (Importación de Abuelas)

1. **Operador** (`movil.progenitoras` o `web.progenitoras`) inicia sesión
2. Navega a: **Progenitoras → Cría → Importación de Abuelas**
3. Registra una recepción:
   - Lote: `L-GP-2026-06`
   - Cantidad: 5000 hembras, 500 machos
   - Peso promedio: 42g
   - Referencia SAP: `PO-4500001001` (OC Importación Abuelas Ross 308)
   - Observación: "Recepción de abuelas Ross 308 — Lote GP-06"
4. Verifica que el estado queda en **"Registrado"**
5. Toca **"Enviar a Revisión"**

**✅ A verificar:**
- El evento aparece en el historial
- La OC `PO-4500001001` queda asociada
- El operador NO puede editar después de enviar

#### A.2 — Registro de Alimento

1. **Operador** registra consumo de alimento:
   - Lote: `L-GP-2026-06`
   - Tipo: Alimento Iniciador BB
   - Cantidad: 250 kg (5 sacos de 50 kg)
2. Enviar a revisión

#### A.3 — Inspección de Granja

1. **Operador** registra inspección:
   - Temperatura: 28.5°C (Galpón GP-A1), 29.0°C (Galpón GP-A2)
   - Humedad: 65% (Galpón GP-A1), 62% (Galpón GP-A2)
   - Estado de cama: "Seca" en ambos
2. Enviar a revisión

#### A.4 — Revisión y Corrección

1. **Supervisor** (`web.supervisor`) inicia sesión
2. Navega a **Revisión → Pendientes**
3. Encuentra los eventos del operador
4. **Inicia revisión** de cada uno
5. Si encuentra un error (ej. la cantidad de aves era 5200, no 5000):
   - Registra una **corrección auditada**:
     - Campo: `bird_movements[0].quantity`
     - Valor original: `5000`
     - Valor corregido: `5200`
     - Motivo: "Guía de despacho indica 5200 aves hembra"
   - El estado cambia a **"Corregido"**
6. Si todo está bien, completa la revisión

**✅ A verificar:**
- La corrección queda registrada con trazabilidad (original → corregido)
- Se puede ver el historial de correcciones en `/corrections/event/{id}`
- La auditoría registra quién corrigió qué

#### A.5 — Aprobación o Rechazo

1. **Contralor** (`web.contralor`) inicia sesión
2. Navega a **Aprobaciones → Pendientes**
3. Revisa los eventos en estado "Corregido"
4. Para cada evento:
   - **APROBAR**: "Datos verificados contra guía de despacho. OK."
   - O **RECHAZAR**: "Cantidad no coincide con remito físico. Verificar nuevamente."
5. Verifica que los aprobados pasan a estado **"Aprobado"**
6. Verifica que los rechazados pasan a estado **"Rechazado"** con el motivo

**✅ A verificar:**
- El contralor NO puede aprobar sus propios registros (segregación BR-14)
- El rechazo requiere motivo (mínimo 10 caracteres)
- El evento rechazado puede ser reenviado por el operador
- Cada acción queda en auditoría

#### A.6 — Auditoría

1. **Contralor** o **Admin** navega a **Administración → Auditoría**
2. Busca por el ID del evento creado en A.1
3. Verifica el **timeline completo**:
   - `created` — quién creó el evento y cuándo
   - `updated` — quién lo envió a revisión
   - `review_started` — quién inició la revisión
   - `corrected` — qué campo se corrigió, valor anterior → nuevo, motivo
   - `approved` — quién aprobó y comentarios
4. Filtra por usuario, acción, lote, fecha

**✅ A verificar:**
- **NADA se borra.** Cada paso es visible
- El timeline muestra user_id, action, timestamp
- Se puede exportar/filtrar por cualquier criterio

---

### 🟢 ESCENARIO B: Reproductoras — Ciclo de Producción de Huevos

**Participantes:** 3-4 personas
- Operador Reproductoras (mobile)
- Operador Incubadora (mobile/web)
- Supervisor (web)
- Contralor (web)

#### B.1 — Recolección de Huevos (YA HAY DATOS)

Ya existen 2 recolecciones pendientes de revisión para el lote `L-BR-2026-02`.

1. **Operador** (`movil.reproductoras`) inicia sesión
2. Navega a **Reproductoras → Producción → Recolección de Huevos**
3. Registra una NUEVA recolección:
   - Fértiles: 4800, Sucios: 75, Rotos: 20, Descartes: 40
   - Enviar a revisión

#### B.2 — Revisión de Recolecciones

1. **Supervisor** (`web.supervisor`) revisa las recolecciones pendientes
2. Corrige si es necesario, completa revisión

#### B.3 — Despacho de Huevos a Incubadora

1. **Operador** registra un despacho:
   - Huevos fértiles: 4000 unidades
   - Destino: Planta Incubadora Central
   - Referencia SAP: `STO-4800002001` (Transferencia huevos fértiles)
2. Enviar a revisión

**✅ A verificar:**
- BR-02: El despacho no puede exceder los huevos disponibles
- Si no hay suficientes huevos fértiles registrados, el sistema bloquea el despacho

#### B.4 — Recepción en Incubadora

1. **Operador Incubadora** (`movil.incubadora`) inicia sesión
2. Registra la recepción de los mismos huevos en incubadora
3. Verifica que los 4000 huevos coinciden con el despacho
4. Enviar a revisión

#### B.5 — Carga de Incubación

1. **Operador Incubadora** registra carga:
   - Incubadora 1, 19000 huevos cargados
   - Temperatura: 37.5°C, Humedad: 55%
2. Enviar a revisión

**✅ A verificar:**
- BR-03: La carga no puede exceder los huevos recibidos en incubadora
- Si se intenta cargar más huevos de los disponibles, el sistema bloquea

#### B.6 — Aprobación

1. **Contralor** aprueba todos los eventos corregidos
2. Verifica el timeline de auditoría

---

### 🟠 ESCENARIO C: Pollo de Engorde — Ciclo Completo

**Participantes:** 3-4 personas

#### C.1 — Recepción de Pollitos BB

1. **Operador** (`movil.engorde`) registra recepción en lote `L-BO-2026-06`:
   - 9500 hembras, 9500 machos
   - Peso: 42g
   - Referencia SAP: `STO-4800002003` (Transferencia pollitos engorde)
2. Enviar a revisión

#### C.2 — Registro de Alimento Semanal

1. **Operador** registra alimento:
   - Semana 1: 2800 kg (56 sacos)
   - Semana 2: 3500 kg (70 sacos)
   - Semana 3: 4200 kg (84 sacos)
   - (Cada semana se registra por separado)
2. Enviar a revisión

#### C.3 — Registro de Pesaje

1. **Operador** registra pesaje semanal:
   - Muestra: 100 aves
   - Peso promedio: 180g (semana 1), 450g (semana 2), 900g (semana 3)
2. Enviar a revisión

#### C.4 — Registro de Mortalidad

1. **Operador** registra mortalidad:
   - 25 aves (semana 1) — normal (< 0.3%)
   - Intentar registrar 5000 aves → **DEBE SER BLOQUEADO** por BR-01 (excede saldo)

**✅ A verificar:**
- La mortalidad pequeña se registra sin problema
- La mortalidad excesiva es bloqueada
- El sistema muestra el saldo actual de aves

#### C.5 — Vacunación

1. **Operador** registra vacunación:
   - Vacuna: Newcastle B1
   - Lote: `VAC-2026-001`
   - Vía: Agua de bebida
   - Dosis: 0.5 ml/ave
2. Enviar a revisión

---

### 🔴 ESCENARIO D: Orden de Compra — Consumo Único

**Objetivo:** Verificar que una orden de compra NO se puede usar dos veces.

#### D.1 — Primer uso de la OC

1. **Operador Multi-Proceso** (`web.multiproceso`) registra recepción de aves:
   - Lote: `L-GP-2026-06`
   - SAP: `PO-4500001002` (OC Cobb 500 — 4620 aves)
   - Cantidad: 4620 aves
2. Enviar a revisión

#### D.2 — Intento de reutilizar la OC

1. El mismo operador (u otro) intenta registrar OTRA recepción con `PO-4500001002`
2. **DEBE SER BLOQUEADO** por BR-10: "El documento SAP ya fue registrado para este lote"

**✅ A verificar:**
- Primera recepción: éxito
- Segunda recepción con misma OC: **bloqueada**
- El mensaje de error es claro

---

### 🟣 ESCENARIO E: Operador Multi-Proceso

**Objetivo:** Verificar que el operador multi-proceso puede trabajar en TODOS los tipos de ave.

1. **Operador Multi-Proceso** (`movil.multiproceso`) inicia sesión
2. Navega por los 6 procesos:
   - Progenitoras Cría
   - Progenitoras Producción
   - Reproductoras Cría
   - Reproductoras Producción
   - Incubadora
   - Pollo de Engorde
3. Registra al menos 1 operación en cada proceso
4. Verifica que puede ver el historial de todas

**✅ A verificar:**
- El menú muestra los 6 procesos
- Puede registrar en cualquiera
- El historial muestra eventos de todos los tipos

---

### ⚪ ESCENARIO F: Contralor — Vista Panorámica

**Objetivo:** El contralor ve TODO lo que está pasando.

1. **Contralor** (`web.contralor`) inicia sesión
2. Dashboard muestra:
   - Total de eventos del día
   - Pendientes de revisión
   - Pendientes de aprobación
   - Eventos por estado (gráfico)
3. Navega a **Revisión** → ve todos los eventos pendientes de todos los operadores
4. Navega a **Aprobaciones** → ve todos los eventos corregidos listos para aprobar
5. Puede aprobar en lote (seleccionar varios y aprobar juntos)
6. Puede rechazar con motivo
7. Navega a **Auditoría** → ve el timeline de cualquier evento
8. Navega a **Reportes** → KPIs de mortalidad, conversión alimenticia

---

## 4. PRUEBAS DE CONCURRENCIA (Múltiples usuarios simultáneos)

### Escenario G: Operación simultánea

1. **3 operadores** inician sesión AL MISMO TIEMPO:
   - `movil.progenitoras` — registra recepción de aves en GP
   - `movil.reproductoras` — registra recolección de huevos en BR
   - `movil.engorde` — registra alimento en BO
2. Los 3 envían a revisión
3. **Supervisor** (`web.supervisor`) ve los 3 eventos en su bandeja
4. **Contralor** (`web.contralor`) aprueba/rechaza

**✅ A verificar:**
- Los 3 eventos aparecen en las bandejas correctas
- No hay conflictos ni datos mezclados entre lotes
- La segregación multi-compañía funciona (solo ven datos de Avícola Global C.A.)

---

## 5. PRUEBAS DE IDEMPOTENCIA

### Escenario H: Prevención de duplicados

1. **Operador** registra un evento de alimento con `idempotency_key: "test-key-001"`
2. **Operador** intenta registrar el MISMO evento con la misma key
3. El segundo intento **NO crea un duplicado** — devuelve el evento existente

**✅ A verificar:**
- Mismo ID de evento en ambas respuestas
- Solo existe 1 registro en la base de datos

---

## 6. LISTA DE VERIFICACIÓN FINAL

### Por cada escenario, verificar:

- [ ] El operador correcto puede registrar en su proceso asignado
- [ ] El operador NO puede registrar en procesos que no le corresponden
- [ ] Los eventos aparecen en estado "Registrado" tras crearse
- [ ] Los eventos aparecen en la bandeja de revisión tras enviarse
- [ ] El supervisor puede iniciar revisión y cambia a "En Revisión"
- [ ] Las correcciones preservan valor original + valor corregido + motivo
- [ ] El contralor puede aprobar → estado "Aprobado"
- [ ] El contralor puede rechazar → estado "Rechazado" con motivo obligatorio
- [ ] El timeline de auditoría muestra TODOS los pasos
- [ ] Las reglas de negocio bloquean operaciones inválidas:
  - [ ] BR-01: Mortalidad no excede saldo
  - [ ] BR-02: Despacho de huevos no excede recolección
  - [ ] BR-03: Carga de incubación no excede recepción
  - [ ] BR-10: Documento SAP no se duplica
  - [ ] BR-14: Operador no aprueba su propio registro
- [ ] La idempotencia previene duplicados
- [ ] Los usuarios móviles ven la interfaz adaptada
- [ ] Los usuarios web ven la interfaz completa con sidebar
- [ ] La OC queda "consumida" tras el primer uso

---

## 7. CONSULTAS RÁPIDAS DE AUDITORÍA

Para verificar que todo quede registrado, el contralor o admin puede consultar:

```bash
# Timeline de un evento específico
GET /api/v1/audit/timeline/operational_event/{event_id}

# Todas las acciones de un usuario
GET /api/v1/audit?user_id={user_id}&limit=50

# Todos los eventos creados hoy
GET /api/v1/audit?action=created&date_from=2026-06-29

# Aprobaciones de un lote específico
GET /api/v1/audit?action=approved&lot_id={lot_id}

# Correcciones de un evento
GET /api/v1/corrections/event/{event_id}
```

---

## 8. NOTAS PARA LOS TESTERS

1. **Usen los usuarios asignados** — no compartan credenciales entre roles. La segregación es parte de la prueba.
2. **Registren con datos realistas** — cantidades, pesos, temperaturas que tengan sentido en el contexto avícola.
3. **Prueben los casos borde** — intenten romper el sistema con datos inválidos. El sistema DEBE bloquearlos.
4. **Tomen capturas de pantalla** de cada paso para documentar hallazgos.
5. **Anoten cualquier comportamiento inesperado** — si algo no coincide con lo descrito en esta guía, repórtenlo.
6. **Ejecuten cada escenario al menos 2 veces** — la primera para familiarizarse, la segunda para verificar consistencia.
7. **Prueben con múltiples usuarios simultáneos** — la concurrencia es el escenario más realista.

---

## 9. REINICIO Y VALIDACIÓN DE DATOS DE PRUEBA

Si necesitan reiniciar o reparar la data antes de un ciclo de pruebas en vivo:

```bash
cd backend
PYTHONPATH=. python3 seeds/dev_seeds.py
PYTHONPATH=. python3 seeds/integration_seeds.py
PYTHONPATH=. python3 seeds/live_data_boost.py
PYTHONPATH=. python3 seeds/live_readiness_check.py
```

Notas importantes:

1. `dev_seeds.py` crea/actualiza compañías, roles, usuarios y catálogos base.
2. `integration_seeds.py` agrega lotes, referencias SAP y eventos para escenarios funcionales.
3. `live_data_boost.py` cierra brechas de cobertura (multiempresa, estados y tipos de evento faltantes).
4. `live_readiness_check.py` es el criterio de salida para decidir si se puede arrancar con testers.
5. No iniciar pruebas en vivo si el check termina en `NOT READY`.

---

> **"Nada se borra. Todo se audita. Cada acción queda registrada con: quién, qué, cuándo, valor anterior, valor nuevo y motivo."**
