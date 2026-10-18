# 08 · Verificación en runtime — Revisión QA 2026-10-17

**Documento**: estado de verificación en entorno y checklist manual para UAT
**Fecha**: 2026-10-18 · **SHA de implementación**: `{{IMPL_SHA}}`
**Estado global**: **`NOT_VERIFIED_FROM_WORKSTATION`**
**Carácter**: declara explícitamente lo que **no** se comprobó en ejecución real y entrega el procedimiento para hacerlo

---

## 1. Estado

| Aspecto | Estado | Detalle |
|---|---|---|
| Verificación en UAT | **`NOT_VERIFIED_FROM_WORKSTATION`** | La base UAT **no es alcanzable** desde esta estación de trabajo: todo lo afirmado en `06_IMPLEMENTATION_EVIDENCE.md` procede de código y de pruebas automatizadas, no de una sesión real |
| Dataset **QA-DEMO-V1** (SPEC 007) | **`BLOCKED_EXTERNAL`** | Sigue **sin cargar** en el runtime compartido. El runbook de carga está en `audit/qa-integral-dataset/09_RUNTIME_VERIFICATION.md` |
| Llamadas SAP reales | **0** | Ninguna prueba tocó HANA: los escenarios BR-23 se construyen con referencias cargadas en modo manual |
| Migraciones | Sin migración nueva en esta ronda | No hay cambio de esquema: todo el enriquecimiento es aditivo en lectura (`enrichment.py`) |
| Ramas / push | Sin rama nueva | Trabajo sobre `main` en el árbol de trabajo |

**Consecuencia para la certificación**: los estados `IMPLEMENTADO` de `05_FIX_PLAN.md` deben leerse como
«implementado y cubierto por pruebas», **no** como «observado funcionando en UAT». La sesión de checklist (§3)
es el paso que falta para pasar de `IMPLEMENTED_PENDING_CERTIFICATION` a certificado.

---

## 2. Requisitos previos de la sesión

1. Backend desplegado con el árbol de trabajo de la ronda (`{{IMPL_SHA}}`) y frontend construido.
2. Dataset **QA-DEMO-V1** cargado (runbook: `audit/qa-integral-dataset/09_RUNTIME_VERIFICATION.md`). Si no se carga,
   las pantallas de Lotes/Historial aparecerán vacías y el checklist no probará nada.
3. Al menos una **OC de compra con desglose de centros mapeados a `business_unit_code`** (para QA-007) y una
   **OC sin mapping** (para el caso «sin cadena»). Se pueden sembrar desde SAP Manager en modo manual; **no** hace
   falta llamar a SAP.
4. Un usuario con permiso de revisión y otro con permiso de aprobación (para QA-017/QA-018).
5. Usuarios de prueba distintos para el paso de segregación (QA-011), ya sembrados: no crear un administrador ad hoc.

---

## 3. Checklist manual por pantalla

Marcar cada casilla con la evidencia (captura + hora + usuario). Cada bloque indica **qué debe verse** si el
hallazgo está cerrado.

### 3.1 Lotes (`Maestros → Lotes` / `Lotes`) — QA-014, QA-015, QA-018

- [ ] La tabla muestra una columna **Granja** con el **nombre**, no el id.
- [ ] La tabla muestra **Lote** (código legible) y no solo `#id`.
- [ ] El filtro **Granja** existe; al elegirlo, la lista se reduce y la petición de red lleva `farm_id`
      (DevTools → Network: `GET /lots?...&farm_id=<n>`).
- [ ] Al limpiar el filtro vuelven todos los lotes y `farm_id` desaparece de la petición.
- [ ] **No** aparece filtro por planta de incubación: es la brecha declarada de QA-015, no un fallo de la sesión.

### 3.2 Historial / Operaciones (`Operativo`) — QA-014, QA-015, QA-018

- [ ] Columnas **Lote**, **Granja**, **Fecha del evento**, **Registrado por**, **Fecha de registro**.
- [ ] **Fecha del evento** y **Fecha de registro** muestran valores distintos cuando el hecho se registró en otro
      día (no son la misma columna duplicada).
- [ ] «Registrado por» muestra nombre y apellidos (o el usuario si la cuenta no tiene nombre declarado).
- [ ] Filtro **Granja** operativo y enviado al servidor (`GET /operations?...&farm_id=`).
- [ ] Con un filtro de granja activo, el desplegable de filtros se abre y se cierra con un clic y «Limpiar» responde
      (regresión del `<button>` anidado corregida en `FilterPanel`).

### 3.3 Mis pendientes (`Operativo → Mis pendientes`) — QA-014, QA-018

- [ ] Cada tarjeta muestra el **código de lote** y la **granja**.
- [ ] La fecha mostrada es la del **evento**, y la de registro aparece identificada como tal.

### 3.4 Centro de Revisión — QA-017, QA-014, QA-015, QA-018

- [ ] **Prueba del bucle (QA-017)**: abrir la pantalla, **no tocar nada** y dejar DevTools → Network abierto
      60 segundos. Debe haber **una sola** petición `GET /review/pending`. No debe repetirse sola.
- [ ] Cambiar de pestaña de estado: **una** petición por cambio, sin ráfagas.
- [ ] Cambiar de página: **una** petición por cambio.
- [ ] Columnas **Lote**, **Granja**, **Registrado por**, **Fecha del evento**, **Fecha de registro**.
- [ ] El filtro **Granja** ya existente sigue funcionando (`farm_id` en la petición).

### 3.5 Aprobaciones (`Revisión → Aprobaciones`) — QA-015, QA-018

- [ ] Filtro **Granja** presente y operativo (`farm_id` en la petición).
- [ ] Columnas de autor del registro y fecha de registro con datos reales.
- [ ] Aprobar un caso de un solo nivel y confirmar que el estado pasa a **aprobado** (no debe haber cambios de
      comportamiento respecto al baseline).

### 3.6 Recepción de aves con OC de otra cadena — QA-007 (BR-23)

Preparación: un lote de **Reproductoras** y una OC cuya cadena derivada sea **Engorde**.

- [ ] Al abrir el formulario de **Recepción de aves** de ese lote, el selector de OC **no ofrece** la OC de Engorde
      (el selector pide `business_unit=<cadena del lote>`).
- [ ] Cada OC del selector muestra su cadena; la OC sin mapping se rotula **«sin cadena»** y **sí** se puede elegir.
- [ ] Antes de elegir lote, el selector de OC está **deshabilitado** con el texto «Seleccione el lote primero».
- [ ] Si se fuerza la OC de Engorde por API o con una pestaña antigua, el backend responde **`400` con `rule = "BR-23"`**
      y el mensaje nombra la cadena de la OC y el código del lote. La operación **no** se registra.
- [ ] Recepción con una OC de la **misma** cadena: se registra sin error (BR-23 no aplica).
- [ ] Recepción con OC **sin cadena derivable**: se registra sin error (BR-23 no aplica).
- [ ] **BR-18 intacta**: una OC que excede la cantidad pendiente sigue rechazándose con su regla propia.

### 3.7 Maestros: Desactivar/Reactivar y columnas — QA-002, QA-012, QA-013

- [ ] La cabecera de las tablas dice el **nombre del campo** («RIF/ID fiscal», «Código», «Capacidad», «Placa»,
      «Laboratorio», «Categoría», «Orden», «Descripción», «Código SAP», «Ubicación», «País»). **Ninguna** cabecera
      dice «Editar» ni «Guardar» (QA-013).
- [ ] Un registro activo ofrece **Desactivar**; uno inactivo ofrece **Reactivar** y **no** Desactivar.
- [ ] La columna **Estado** muestra `Activo` / `Inactivo` (QA-002).
- [ ] La fila de un registro inactivo aparece **atenuada** y sigue visible en la lista.
- [ ] El diálogo dice «¿Desactivar registro?» con el aviso «Dejará de poder seleccionarse; podrá reactivarlo después.»
      y **no** «no se puede deshacer».
- [ ] Desactivar y luego **Reactivar** el mismo registro: vuelve a estar disponible en los selectores.
- [ ] Provocar un fallo de baja (p. ej. registro protegido o sesión sin permiso): aparece un **toast de error**;
      no falla en silencio ni en consola.
- [ ] **Galpones**: columna **Granja** con el nombre del padre (QA-012).
- [ ] **Equipos de incubadora** y **Nacedoras**: columna **Planta de incubación** con el nombre del padre.
- [ ] Un hijo cuyo padre está inactivo **también** muestra el nombre del padre (no queda vacío).

### 3.8 Fechas futuras — QA-016

- [ ] En el formulario de operaciones, el campo **Fecha del evento** no permite seleccionar una fecha posterior a hoy
      (el calendario la muestra deshabilitada).
- [ ] Con el navegador en la zona horaria de la planta, «hoy» coincide con el día en curso (no el anterior ni el
      siguiente): la fecha se calcula en hora local, no en UTC.
- [ ] En la importación de abuelas, **Fecha de salida** y **Fecha de llegada** no aceptan futuro.
- [ ] Las fechas **planificadas** y de **cutover** siguen aceptando futuro: es lo esperado hasta **OD-QA2-05**.

### 3.9 Segregación de funciones — QA-011 (documentado, sin cambio)

- [ ] Registrar una operación con el usuario A y aprobarla con el mismo usuario A: el sistema lo **impide** (403).
- [ ] Revisar con el supervisor y aprobar con otro usuario autorizado: **sí** se permite.
- [ ] No se creó ningún usuario administrador para esta prueba.

### 3.10 Estados, rechazo, cancelación y reverso — QA-010 (documentado, sin cambio)

- [ ] Un evento **aprobado** no se puede cancelar; uno en `pending_review` sí.
- [ ] El **reverso** solo aparece sobre un evento aprobado y genera la contrapartida.

---

## 4. Nota sobre el dataset QA-DEMO-V1

El dataset **QA-DEMO-V1** (SPEC 007) sigue **sin cargar** en el runtime compartido: `BLOCKED_EXTERNAL`
desde esta estación porque la base no es alcanzable. Mientras no se cargue:

- Las pantallas de Lotes, Historial y las bandejas de revisión aparecerán **vacías** o sin datos representativos.
- Los pasos 3.1 a 3.6 no podrán completarse con datos reales; los pasos 3.7 a 3.9 se pueden verificar con los
  maestros sembrados.
- El procedimiento y las comprobaciones de carga están en **`audit/qa-integral-dataset/09_RUNTIME_VERIFICATION.md`**;
  la matriz de cobertura de datos, en `audit/qa-integral-dataset/QA_DATA_COVERAGE_MATRIX.md`.

---

## 5. Qué no se hizo y por qué

| No se hizo | Por qué |
|---|---|
| Verificación en UAT desde esta estación | Base **no alcanzable**; se declara `NOT_VERIFIED_FROM_WORKSTATION` en lugar de inferir resultados |
| Carga del dataset QA-DEMO-V1 | `BLOCKED_EXTERNAL` (ver runbook); no se borró ni recreó ningún dato QA |
| Llamadas SAP reales | Prohibidas por el mandato: **0 llamadas**; los escenarios se construyen con datos manuales |
| Creación de usuarios de prueba con privilegios | Prohibido; la segregación se prueba con los usuarios y roles sembrados |
| Migración de esquema | No hace falta: el enriquecimiento es aditivo y solo de lectura |

---

## 6. Registro de la sesión (a completar en UAT)

| Campo | Valor |
|---|---|
| Fecha de la sesión | `PENDING` |
| Entorno | `PENDING` (UAT) |
| SHA desplegado | `PENDING` (`{{IMPL_SHA}}` esperado) |
| Dataset cargado | `PENDING` (QA-DEMO-V1) |
| Bloques verificados | `PENDING` (3.1 … 3.10) |
| Resultado | `PENDING` |
| Incidencias abiertas | `PENDING` |
