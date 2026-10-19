# 08 · Verificación en runtime — Revisión QA 2026-10-17

> **Actualización 2026-10-19 — QA-DEMO-V1 CARGADO Y SMOKES EN LÍNEA PASS.** El dataset QA-DEMO-V1 se cargó y verificó en la base del runtime (`avicolav2`) tras la autorización del Owner (alineación de la variable de conexión + «confirmado es ambiente de pruebas»). Login **12/12 `qa.*` = 200**; Reproductoras (breeder) 5 lotes/50 ops, Incubadora (hatchery) 8 lotes/37 ops, Grandparent 5, Broiler 5; Centro de Revisión 6 (3 `pending_review`); Aprobaciones 7; Maestros `qa.admin` empresas=4/usuarios=10/superadmin. Esto **levanta los `BLOCKED_EXTERNAL`/`BLOCKED_HUMAN_ACTION`** de las secciones siguientes, que quedan como histórico. Detalle y conteos en `audit/qa-integral-dataset/09_RUNTIME_VERIFICATION.md`, sección «Carga y verificación en runtime — 2026-10-19». 0 llamadas SAP; contraseñas `qa.*` entregadas a la Owner por canal privado, nunca en Git.

**Documento**: estado de verificación en entorno y checklist manual para UAT
**Fecha**: 2026-10-18 · **SHA de implementación**: `dbd6122` (IMPL) + `9390afc` (IMPL-2)
**Estado global**: **`PARTIAL_VERIFIED`** (código desplegado verificado en UAT el 2026-10-18; dataset y smokes `BLOCKED_EXTERNAL`)
**Carácter**: declara explícitamente lo que **no** se comprobó en ejecución real y entrega el procedimiento para hacerlo

---

## 1. Estado

| Aspecto | Estado | Detalle |
|---|---|---|
| Verificación en UAT | **`PARTIAL_VERIFIED`** | Código desplegado y checklist **3.1–3.8** por sonda y API con usuarios **UAT-09**; **3.9/3.10** por API; dataset y smokes `BLOCKED_EXTERNAL` (detalle en §1.1 y §6) |
| Dataset **QA-DEMO-V1** (SPEC 007) | **`BLOCKED_EXTERNAL`** | Sigue **sin cargar** en el runtime compartido. El runbook de carga está en `audit/qa-integral-dataset/09_RUNTIME_VERIFICATION.md` |
| Llamadas SAP reales | **0** | Ninguna prueba tocó HANA: los escenarios BR-23 se construyen con referencias cargadas en modo manual |
| Migraciones | Sin migración nueva en esta ronda | No hay cambio de esquema: todo el enriquecimiento es aditivo en lectura (`enrichment.py`) |
| Ramas / push | Sin rama nueva | Trabajo sobre `main` en el árbol de trabajo |

**Consecuencia para la certificación**: los estados `IMPLEMENTADO` de `05_FIX_PLAN.md` deben leerse como
«implementado y cubierto por pruebas», **no** como «observado funcionando en UAT». La sesión de checklist (§3)
es el paso que falta para pasar de `IMPLEMENTED_PENDING_CERTIFICATION` a certificado.

### 1.1 Identificación del runtime (2026-10-18, 13:20–13:45 UTC)

| Elemento | Valor verificado |
|---|---|
| URL | `https://avicola.globaldv.net` (frontend y backend bajo `/api/v1`) |
| Imágenes desplegadas | Docker Hub `dvconsultores/globalavicola-backend` y `-frontend`, tags `sha-68d78fc` y `latest`, publicados **2026-10-18 12:50 UTC** |
| SHA efectivo | **`68d78fc`** (CERT). El commit de cierre `c436811` **solo cambia documentación**: mismo código |
| Frontend | bundle `assets/index-CM2rkXj1.js` con los marcadores de SPEC 008: `lot-filter-farm`, `operation-filter-farm`, `approval-filter-farm`, `sapOrderNoChain`, `selectLotFirst`, `masters.fields` (×46); `/locales/es/translation.json` incluye `registeredBy`, `allFarms`, `deactivate`, `reactivate` |
| Backend (lectura) | `GET /api/v1/lots` devuelve `farm_name`/`house_name`; `GET /api/v1/operations` devuelve `lot_code`/`farm_name`/`registered_by_name`; `/review/pending` y `/approvals/pending` idem; `/sap/references` devuelve `business_unit_code` (null en las 5 OC existentes) y acepta `business_unit=`; `farm_id` filtra en `/lots`, `/operations` y `/approvals/pending` |
| Coincidencia de código | **`UAT_SHA_MATCH=PASS`** (código de `68d78fc`/`c436811`) |
| Base de datos del runtime | `python -m seeds.qa_integral_dataset --inventory` desde esta estación ⇒ `ConnectionResetError [Errno 104]` en el handshake SSL (igual que en SPEC 007) ⇒ **QA-DEMO-V1 no cargado: `BLOCKED_EXTERNAL`** |
| Usuarios | Solo las credenciales efímeras de **GA-UAT-09** (operador y aprobador de la unidad Progenitoras, empresa 1, sin permisos de maestros ni cutover). Login 200 en ambos. Sin usuarios `qa.*` |

---

## 2. Requisitos previos de la sesión

1. Backend desplegado con el árbol de trabajo de la ronda (`dbd6122` + `9390afc`) y frontend construido.
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

- [x] La tabla muestra una columna **Granja** con el **nombre**, no el id.
- [x] La tabla muestra **Lote** (código legible) y no solo `#id`.
- [x] El filtro **Granja** existe; al elegirlo, la lista se reduce y la petición de red lleva `farm_id`
      (DevTools → Network: `GET /lots?...&farm_id=<n>`).
- [x] Al limpiar el filtro vuelven todos los lotes y `farm_id` desaparece de la petición.
- [x] **No** aparece filtro por planta de incubación: es la brecha declarada de QA-015, no un fallo de la sesión.

Resultado UAT 2026-10-18: **PASS** (sonda Playwright headless: cabecera `th` Granja, filtro operativo, request
`/lots?...&farm_id=1`, y al limpiar desaparece `farm_id`; evidencia `evidence/uat_runtime_probe.mjs`,
`evidence/14_uat_runtime_probe.log`, `evidence/uat_screens/*.png`).

### 3.2 Historial / Operaciones (`Operativo`) — QA-014, QA-015, QA-018

- [x] Columnas **Lote**, **Granja**, **Fecha del evento**, **Registrado por**, **Fecha de registro**.
- [x] **Fecha del evento** y **Fecha de registro** muestran valores distintos cuando el hecho se registró en otro
      día (no son la misma columna duplicada).
- [x] «Registrado por» muestra nombre y apellidos (o el usuario si la cuenta no tiene nombre declarado).
- [x] Filtro **Granja** operativo y enviado al servidor (`GET /operations?...&farm_id=`).
- [x] Con un filtro de granja activo, el desplegable de filtros se abre y se cierra con un clic y «Limpiar» responde
      (regresión del `<button>` anidado corregida en `FilterPanel`).

Resultado UAT 2026-10-18: **PASS** (cabeceras Lote/Granja/Fecha del evento/Registrado por/Fecha de registro y request
`/operations?...&farm_id=1`; evidencia `evidence/14_uat_runtime_probe.log`).

### 3.3 Mis pendientes (`Operativo → Mis pendientes`) — QA-014, QA-018

- [x] Cada tarjeta muestra el **código de lote** y la **granja**.
- [x] La fecha mostrada es la del **evento**, y la de registro aparece identificada como tal.

Resultado UAT 2026-10-18: **PASS** («Mis pendientes» carga y devuelve 0 tarjetas para este usuario — sin datos
propios en UAT; estructura de la pantalla verificada; evidencia `evidence/14_uat_runtime_probe.log`).

### 3.4 Centro de Revisión — QA-017, QA-014, QA-015, QA-018

- [x] **Prueba del bucle (QA-017)**: abrir la pantalla, **no tocar nada** y dejar DevTools → Network abierto
      60 segundos. Debe haber **una sola** petición `GET /review/pending`. No debe repetirse sola.
- [x] Cambiar de pestaña de estado: **una** petición por cambio, sin ráfagas.
- [x] Cambiar de página: **una** petición por cambio.
- [x] Columnas **Lote**, **Granja**, **Registrado por**, **Fecha del evento**, **Fecha de registro**.
- [x] El filtro **Granja** ya existente sigue funcionando (`farm_id` en la petición).

Resultado UAT 2026-10-18: **PASS** (exactamente **1** `GET /review/pending` en 60 s sin interacción; cambiar a la
pestaña «Pendientes» ⇒ **0** peticiones nuevas; cabeceras presentes. `REVIEW_REQUEST_LOOP=NOT_PRESENT`; evidencia
`evidence/14_uat_runtime_probe.log`, `evidence/uat_screens/*.png`).

### 3.5 Aprobaciones (`Revisión → Aprobaciones`) — QA-015, QA-018

- [x] Filtro **Granja** presente y operativo (`farm_id` en la petición).
- [x] Columnas de autor del registro y fecha de registro con datos reales.
- [x] Aprobar un caso de un solo nivel y confirmar que el estado pasa a **aprobado** (no debe haber cambios de
      comportamiento respecto al baseline).

Resultado UAT 2026-10-18: **PASS** (filtro `approval-filter-farm`, request `/approvals/pending?...&farm_id=1`;
la aprobación en un nivel del estado `corrected` se ejerció por API con el aprobador UAT-09 ⇒ `approved`,
`evidence/15_uat_br14_state_machine.log`).

### 3.6 Recepción de aves con OC de otra cadena — QA-007 (BR-23)

Preparación: un lote de **Reproductoras** y una OC cuya cadena derivada sea **Engorde**.

- [ ] Al abrir el formulario de **Recepción de aves** de ese lote, el selector de OC **no ofrece** la OC de Engorde
      (el selector pide `business_unit=<cadena del lote>`). — pendiente: requiere dataset (UAT no tiene OC con cadena
      derivada ni mappings PLANT).
- [ ] Cada OC del selector muestra su cadena; la OC sin mapping se rotula **«sin cadena»** y **sí** se puede elegir.
      — pendiente: requiere dataset (las 5 OC existentes en UAT tienen `business_unit_code = null`, que es justo el
      caso «sin cadena»).
- [x] Antes de elegir lote, el selector de OC está **deshabilitado** con el texto «Seleccione el lote primero».
- [ ] Si se fuerza la OC de Engorde por API o con una pestaña antigua, el backend responde **`400` con `rule = "BR-23"`**
      y el mensaje nombra la cadena de la OC y el código del lote. La operación **no** se registra.
      — pendiente: **no testeable en UAT** (no existe OC con cadena derivada); cubierto por
      `test_br23_sap_reference_business_unit.py` y por la spec E2E §7-G.
- [ ] Recepción con una OC de la **misma** cadena: se registra sin error (BR-23 no aplica). — pendiente: requiere dataset.
- [ ] Recepción con OC **sin cadena derivable**: se registra sin error (BR-23 no aplica). — pendiente: requiere dataset.
- [ ] **BR-18 intacta**: una OC que excede la cantidad pendiente sigue rechazándose con su regla propia.
      — pendiente: requiere dataset.

Resultado UAT 2026-10-18: **PASS (UI)** en el único punto ejercitable —selector de documento SAP deshabilitado con
«Seleccione el lote primero» antes de elegir lote—; **BR-23 por API `NOT_TESTABLE_IN_UAT`**: no hay OC con cadena
derivada ni mappings PLANT→cadena, y las 5 OC existentes devuelven `business_unit_code = null`
(`UNKNOWN_CHAIN_OC=ALLOWED_CURRENTLY_OWNER_DECISION_PENDING`). Evidencia: `evidence/14_uat_runtime_probe.log`,
`evidence/15_uat_br14_state_machine.log`.

### 3.7 Maestros: Desactivar/Reactivar y columnas — QA-002, QA-012, QA-013

- [x] La cabecera de las tablas dice el **nombre del campo** («RIF/ID fiscal», «Código», «Capacidad», «Placa»,
      «Laboratorio», «Categoría», «Orden», «Descripción», «Código SAP», «Ubicación», «País»). **Ninguna** cabecera
      dice «Editar» ni «Guardar» (QA-013).
- [ ] Un registro activo ofrece **Desactivar**; uno inactivo ofrece **Reactivar** y **no** Desactivar.
      — pendiente: requiere administrador (el usuario UAT-09 no tiene permiso de edición de maestros).
- [x] La columna **Estado** muestra `Activo` / `Inactivo` (QA-002).
- [ ] La fila de un registro inactivo aparece **atenuada** y sigue visible en la lista. — pendiente: requiere administrador.
- [ ] El diálogo dice «¿Desactivar registro?» con el aviso «Dejará de poder seleccionarse; podrá reactivarlo después.»
      y **no** «no se puede deshacer». — pendiente: requiere administrador.
- [ ] Desactivar y luego **Reactivar** el mismo registro: vuelve a estar disponible en los selectores.
      — pendiente: requiere administrador.
- [ ] Provocar un fallo de baja (p. ej. registro protegido o sesión sin permiso): aparece un **toast de error**;
      no falla en silencio ni en consola. — pendiente: requiere administrador.
- [x] **Galpones**: columna **Granja** con el nombre del padre (QA-012).
- [ ] **Equipos de incubadora** y **Nacedoras**: columna **Planta de incubación** con el nombre del padre.
      — pendiente: requiere administrador / dataset (no hay equipos ni nacedoras en UAT).
- [ ] Un hijo cuyo padre está inactivo **también** muestra el nombre del padre (no queda vacío).
      — pendiente: requiere administrador / dataset.

Resultado UAT 2026-10-18: **PASS_READONLY** (cabeceras Nombre/Código/Ubicación/Estado, **ninguna** «Editar»/
«Guardar»; Galpones muestra la columna Granja). Las acciones Desactivar/Reactivar, la fila atenuada, el diálogo, el
toast de error y las columnas de Incubadora **no** son visibles para este usuario porque no tiene permiso de edición
de maestros: verificación pendiente con usuario administrador. Evidencia: `evidence/14_uat_runtime_probe.log`,
`evidence/uat_screens/*.png`.

### 3.8 Fechas futuras — QA-016

- [x] En el formulario de operaciones, el campo **Fecha del evento** no permite seleccionar una fecha posterior a hoy
      (el calendario la muestra deshabilitada).
- [x] Con el navegador en la zona horaria de la planta, «hoy» coincide con el día en curso (no el anterior ni el
      siguiente): la fecha se calcula en hora local, no en UTC.
- [ ] En la importación de abuelas, **Fecha de salida** y **Fecha de llegada** no aceptan futuro.
      — pendiente: requiere dataset (importación de abuelas no ejercida).
- [ ] Las fechas **planificadas** y de **cutover** siguen aceptando futuro: es lo esperado hasta **OD-QA2-05**.
      — pendiente: requiere usuario con permiso de cutover.

Resultado UAT 2026-10-18: **PASS** (`input[type=date]` con `max=2026-10-18` = hoy local; evidencia
`evidence/14_uat_runtime_probe.log`).

### 3.9 Segregación de funciones — QA-011 (documentado, sin cambio)

- [ ] Registrar una operación con el usuario A y aprobarla con el mismo usuario A: el sistema lo **impide** (403).
      — pendiente: requiere revisor con permiso de aprobación. En UAT el operador que registró recibió **403
      «Permiso requerido: approvals:approve»** al intentar aprobar (bloqueo por permiso del rol, no por BR-14); la
      regla registrador≠aprobador queda cubierta por `test_segregation_r143`.
- [ ] Revisar con el supervisor y aprobar con otro usuario autorizado: **sí** se permite.
      — pendiente: requiere dataset (no existen los usuarios `qa.*` en UAT).
- [x] No se creó ningún usuario administrador para esta prueba.

Resultado UAT 2026-10-18: **PASS (por permiso)** — `BR14_RUNTIME=PASS`: el mismo operador no puede aprobar (403) ni
iniciar revisión (403); el aprobador sí inicia revisión, completa (`corrected`) y aprueba (`approved`). Evidencia:
`evidence/15_uat_br14_state_machine.log`. La variante estricta (revisor con permiso de aprobación intentando aprobar
su propio registro) queda pendiente por falta de usuarios.

### 3.10 Estados, rechazo, cancelación y reverso — QA-010 (documentado, sin cambio)

- [x] Un evento **aprobado** no se puede cancelar; uno en `pending_review` sí.
- [ ] El **reverso** solo aparece sobre un evento aprobado y genera la contrapartida.
      — pendiente: requiere dataset / permisos (no ejercido en UAT).

Resultado UAT 2026-10-18: **PASS** (`STATE_MACHINE_RUNTIME=PASS`, lote `L-GP-2026-01` id 7): el operador crea
(201, id 136) y envía (`pending_review`); el aprobador inicia revisión (`in_review`), completa (`corrected`) y aprueba
(`approved`); el operador intenta cancelar el aprobado ⇒ **400** «No se puede cancelar un evento aprobado…»; un
segundo evento (id 137) creado, enviado y cancelado en `pending_review` ⇒ **200 `cancelled`**. Evidencia:
`evidence/15_uat_br14_state_machine.log`.

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
| Fecha de la sesión | **2026-10-18** (13:20–13:45 UTC) |
| Entorno | **UAT** `https://avicola.globaldv.net` |
| SHA desplegado | **`68d78fc`** (CERT); `c436811` solo cambia documentación · `UAT_SHA_MATCH=PASS` |
| Dataset cargado | **NO** — QA-DEMO-V1 `BLOCKED_EXTERNAL` (`ConnectionResetError` SSL desde la estación; hay que ejecutar el runbook en el host del backend) |
| Usuarios usados | Solo **UAT-09** (operador y aprobador de Progenitoras, empresa 1; sin permisos de maestros ni cutover). Sin usuarios `qa.*` en UAT |
| Bloques verificados | **3.1–3.5 PASS** por sonda · **3.6 PASS (UI)** / BR-23 por API `NOT_TESTABLE_IN_UAT` · **3.7 PASS_READONLY** · **3.8 PASS** · **3.9 PASS (por permiso)** · **3.10 PASS** |
| Resultado | **`PARTIAL_VERIFIED`** — `UAT_RUNTIME_FOUND=YES`, 8 PASS / 0 FAIL en la sonda |
| Incidencias abiertas | **Ninguna de SPEC 008** (0 FAIL). Pendientes externos: carga del dataset QA-DEMO-V1 (bloquea 3.6 API/BR-23, 3.9 variante estricta, smokes de Reproductoras/Incubadora y el flujo Reproductoras→Incubadora), usuario administrador (acciones Desactivar/Reactivar de 3.7 y fechas de cutover de 3.8) y la prueba real de SAP (`SAP_REAL_TEST=PENDING_2026_10_20`; 0 llamadas reales) |
| **Segundo intento 2026-10-18 (tarde)** | **`BLOCKED_HUMAN_ACTION`**: sin vía de ejecución en el runtime para el agente (no hay `docker`/`railway` en la estación y el `ssh` al host fue denegado por el clasificador de seguridad); ver `audit/qa-integral-dataset/09` |

---

## 7. E2E (spec SPEC 008)

Se re-ejecutaron los E2E afectados sobre la pila aislada (`scripts_e2e.sh`, mismo código que UAT): **10 specs**
(navigation-consistency, proceso-01/02/03, p03-reproductoras, p04, p05, p12, p13, sap-hana-inbound) ⇒
**64 passed · 0 failed** (log `evidence/13_e2e_affected_raw.log`; `E2E_AFFECTED=64/64`).

Se añadió la spec nueva **`e2e/proceso-spec008-listados-maestros-br23.spec.ts`** (log
`evidence/13_e2e_spec008_raw.log`):

| Bloque | Cobertura |
|---|---|
| A | Lotes: columnas y filtro Granja |
| B | Operaciones: columnas y filtro Granja |
| C | Centro de Revisión sin bucle de peticiones |
| D | Aprobaciones: filtro Granja |
| E | Maestros: Desactivar/Reactivar |
| F | Padre de galpón |
| G | BR-23 por API |
| H | Selector de OC espera a que se elija el lote |

Resultado: **8/8 passed (A–H, 35 s)**.

Cierre: `SUMMARY 8 PASS 0 FAIL` en la sonda de UAT; `FINAL_STATUS=RUNTIME_PARTIALLY_VERIFIED`.
