# Global Avícola — Guía de prueba funcional integral para QA

Versión del juego de datos: **QA-DEMO-V1** · Ambiente: QA/UAT compartido · Fecha de preparación: 2026-10-18

Esta guía está escrita para la persona de QA que probará Global Avícola de punta a punta. No requiere conocimientos técnicos. Todo lo que aquí se describe ya está cargado en el ambiente con **datos sintéticos** (ficticios, identificables por el prefijo **QA-** en códigos y **qa.** en usuarios). Puede registrar, aprobar, rechazar, corregir y cerrar con libertad: nada de lo que haga afecta datos reales ni a SAP.

> **Importante sobre SAP**: la pantalla de Integración SAP muestra información **sintética**, marcada como `QA_SYNTHETIC`. El sistema no está conectado a SAP real; la prueba con el usuario técnico SAP está programada para el **martes 20 de octubre de 2026** y no forma parte de esta guía.

---

## 1 · Antes de empezar

### 1.1 · Acceso

- URL del ambiente: la indicada por el equipo del proyecto.
- Las **contraseñas** de los usuarios QA se entregan por separado (no están en este documento). Todos los usuarios QA comparten la misma contraseña temporal; cámbiela desde **Mi Perfil** si el equipo lo pide.
- Use un navegador de escritorio actualizado (Chrome, Edge o Firefox). Para la prueba móvil, use el teléfono o el modo «dispositivo móvil» del navegador con el usuario `qa.mobile`.

### 1.2 · Usuarios de prueba

| Usuario | Rol | Empresa | Unidades que ve | Para qué usarlo |
|---|---|---|---|---|
| qa.admin | Super Administrador | QA Avícola Integral C.A. | las 4 | configuración, maestros, usuarios, diagnóstico |
| qa.supervisor | Supervisor Avícola | QA Avícola Integral C.A. | las 4 | revisión, correcciones, reversos, cargas iniciales |
| qa.approver | Aprobador | QA Avícola Integral C.A. | las 4 | aprobar y rechazar |
| qa.operator.gp | Operador de Granja | QA Avícola Integral C.A. | Progenitoras | registrar operaciones de Progenitoras |
| qa.operator.breeder | Operador de Granja | QA Avícola Integral C.A. | Reproductoras | registrar operaciones de Reproductoras |
| qa.operator.hatchery | Operador de Granja | QA Avícola Integral C.A. | Incubadora | registrar operaciones de Incubadora |
| qa.operator.broiler | Operador de Granja | QA Avícola Integral C.A. | Pollo de Engorde | registrar operaciones de Engorde |
| qa.sap | Analista SAP | QA Avícola Integral C.A. | las 4 | Integración SAP (datos sintéticos) |
| qa.auditor | Auditor | QA Avícola Integral C.A. | las 4 | auditoría y reportes |
| qa.mobile | Operador de Granja | QA Avícola Integral C.A. | Pollo de Engorde | registro de campo en **móvil** |
| qa.isolation | Supervisor Avícola | QA Avícola Aislamiento C.A. | Reproductoras y Engorde | probar que una segunda empresa no ve a la primera y que las unidades apagadas no aparecen |
| qa.isolation.operator | Operador de Granja | QA Avícola Aislamiento C.A. | Reproductoras y Engorde | registrar en la segunda empresa |

### 1.3 · Las dos empresas

- **QA Avícola Integral C.A.**: la empresa principal, con las cuatro cadenas (Progenitoras, Reproductoras, Incubadora, Pollo de Engorde) habilitadas y dos niveles de aprobación (supervisor y aprobador).
- **QA Avícola Aislamiento C.A.**: empresa de control. Solo tiene Reproductoras y Engorde habilitadas; Progenitoras e Incubadora están **apagadas** a propósito. Un nivel de aprobación.

### 1.4 · Cómo leer esta guía

Cada sección describe una opción del menú con: **qué hay cargado**, **qué hacer** y **resultado esperado**. Anote cada resultado en la plantilla `QA_EXECUTION_RESULTS_TEMPLATE.docx` (OK / FALLO / BLOQUEADO + observación + captura). Un «resultado esperado» que no se cumple es un hallazgo: anótelo con el usuario, la pantalla, los datos usados y la hora.

### 1.5 · Estados de un registro

Borrador → Registrado → Pendiente de revisión → En revisión → (Devuelto) → Corregido/Validado → Aprobado o Rechazado → Consolidado. Además: Cancelado (anulado por el operador antes de aprobación) y Revertido (anulado con contrapartida después de aprobado). Los estados «Enviado a SAP» y «Confirmado SAP» **no** aparecen en este ambiente.

---

## 2 · Inicio de sesión y menú por rol

**Qué hay cargado**: 12 usuarios con roles y unidades distintas.

**Qué hacer**: inicie sesión con cada usuario de la tabla 1.2 y observe el menú lateral.

**Resultado esperado**
- `qa.admin`, `qa.supervisor`, `qa.approver`, `qa.auditor`, `qa.sap`: ven las cuatro cadenas dentro de **Gestión Avícola** (según su permiso) y las secciones que su rol permite (ver 2.1).
- `qa.operator.gp` ve solo **Progenitoras**; `qa.operator.breeder` solo **Reproductoras**; `qa.operator.hatchery` solo **Incubadora**; `qa.operator.broiler` solo **Pollo de Engorde**. Ninguno ve Revisión, Aprobaciones, Integración ni Administración (salvo Mi Perfil).
- `qa.isolation` y `qa.isolation.operator`: solo Reproductoras y Pollo de Engorde; **no** aparecen Progenitoras ni Incubadora.
- `qa.mobile` en teléfono: solo **Gestión Avícola** con su cadena (Pollo de Engorde).
- Un usuario que escribe mal la contraseña recibe un mensaje de error y no entra.

### 2.1 · Qué debe ver cada rol

| Sección / opción | Admin | Supervisor | Aprobador | Operador | Analista SAP | Auditor |
|---|---|---|---|---|---|---|
| Dashboard | Sí | Sí | Sí | Sí | Sí | Sí |
| Gestión Avícola (Lotes, Historial, Mis pendientes, cadenas) | Sí | Sí | Sí | Sí (su unidad) | Sí (lectura) | Sí (lectura) |
| Centro de Revisión | Sí | Sí | Sí | No | No | Sí (lectura) |
| Aprobaciones | Sí | No | Sí | No | No | No |
| Integración SAP | Sí | No | No | No | Sí | Sí (lectura) |
| Reportes | Sí | Sí | Sí | No | Sí | Sí |
| Cargas Iniciales | Sí | Sí | Sí (aprobar) | No | No | Sí (lectura) |
| Auditoría | Sí | No | No | No | No | Sí |
| Maestros | Sí | Sí (lectura) | No | No | No | No |
| Usuarios y Roles / Acceso por unidad | Sí | No | No | No | No | No |
| Mi Perfil | Sí | Sí | Sí | Sí | Sí | Sí |

Si una celda dice «Sí» y la opción no aparece —o dice «No» y sí aparece— es un hallazgo.

---

## 3 · Dashboard (Inicio)

**Qué hay cargado**: 25 lotes (23 activos y 3 cerrados en la empresa principal, 2 en la de aislamiento), más de 360 registros operativos de las últimas 8 semanas, pendientes de revisión y notificaciones.

**Qué hacer**: entre con `qa.supervisor` y revise los indicadores y accesos rápidos. Repita con `qa.operator.broiler` y con `qa.isolation`.

**Resultado esperado**: indicadores con valores distintos de cero; los pendientes coinciden con lo que se ve en Centro de Revisión; el operador de engorde solo ve datos de Pollo de Engorde; `qa.isolation` ve únicamente los dos lotes de su empresa (QA-ISO-BR-001 y QA-ISO-BRO-001).

---

## 4 · Gestión Avícola

### 4.1 · Lotes

**Qué hay cargado** (empresa principal):

| Cadena | Lote | Situación |
|---|---|---|
| Progenitoras | QA-GP-CRIA-001 | cría, 6 semanas, llegó por importación |
| Progenitoras | QA-GP-PROD-001 | producción, con recolección de huevo y despacho a incubadora |
| Progenitoras | QA-GP-CLOSE-001 | producción, **fecha prevista de cierre vencida** (alerta) |
| Progenitoras | QA-GP-CLOSED-001 | **cerrado** |
| Progenitoras | QA-CUT-GP-001 | producción, creado por **Cargas Iniciales** (alimento acumulado desconocido) |
| Reproductoras | QA-BR-CRIA-001 | cría, 8 semanas; sus pollitas nacieron en la incubadora QA (lote QA-HAT-GPGEN-001) |
| Reproductoras | QA-BR-PROD-001 | producción, recolección **diaria** de huevo las últimas 2 semanas |
| Reproductoras | QA-BR-PROD-002 | producción |
| Reproductoras | QA-BR-CLOSED-001 | **cerrado** |
| Reproductoras | QA-CUT-BR-001 | cría, creado por Cargas Iniciales |
| Incubadora | QA-HAT-GPGEN-001 | ciclo completo (huevo de progenitoras → pollitas reproductoras despachadas) |
| Incubadora | QA-HAT-REC-001 | huevos **recibidos**, pendiente de clasificar y cargar |
| Incubadora | QA-HAT-INC-001 | **en incubación** |
| Incubadora | QA-HAT-OVO-001 | en incubación, pendiente de **ovoscopia** |
| Incubadora | QA-HAT-NAC-001 | **transferido a nacedora** |
| Incubadora | QA-HAT-BIRTH-001 | **nacimiento registrado**, pollitos por despachar |
| Incubadora | QA-HAT-CHICK-001 | pollitos **despachados** a la granja de engorde QA-EN-01 |
| Incubadora | QA-CUT-HAT-001 | incubación en curso creada por Cargas Iniciales |
| Pollo de Engorde | QA-BRO-001 | 1.ª semana, recibió los pollitos de QA-HAT-CHICK-001 |
| Pollo de Engorde | QA-BRO-002 | 4.ª semana, con una recepción **revertida** y una transferencia entre galpones |
| Pollo de Engorde | QA-BRO-003 | 6.ª semana, salida parcial a planta, cierre previsto vencido |
| Pollo de Engorde | QA-BRO-CLOSED-001 | **cerrado** |
| Pollo de Engorde | QA-CUT-BRO-001 | engorde, creado por Cargas Iniciales (alimento desconocido) |

**Qué hacer**
1. Con `qa.supervisor`, abra **Lotes**, filtre por cadena y abra el detalle de QA-BR-PROD-001.
2. Revise población viva, fase, saldo de apertura, indicadores (mortalidad, conversión, peso), últimos eventos y alertas.
3. Abra **Trazabilidad** en QA-HAT-GPGEN-001 y en QA-HAT-CHICK-001.
4. Abra QA-CUT-GP-001 y observe los datos desconocidos.
5. Con `qa.operator.gp` intente abrir un lote de engorde (por ejemplo escribiendo su URL).

**Resultado esperado**
- El detalle muestra números coherentes con la historia (ej. QA-BR-PROD-001: ~10 000 aves al inicio de producción, mortalidad acumulada visible, huevos recolectados a diario).
- La trazabilidad muestra el árbol: QA-GP-PROD-001 → QA-HAT-GPGEN-001 → QA-BR-CRIA-001, y QA-BR-PROD-001 → QA-HAT-CHICK-001 → QA-BRO-001.
- En QA-CUT-GP-001 el alimento acumulado aparece como **desconocido (UNKNOWN)**, nunca como 0.
- El operador de progenitoras **no puede** abrir un lote de engorde (mensaje de «no encontrado» o sin acceso).

### 4.2 · Crear un lote y transición de fase

**Qué hacer**: con `qa.supervisor`, cree un lote nuevo de Reproductoras en la granja QA-BR-01 (galpón QA-BR-01-G1 u otro libre), código `QA-BR-NUEVO-<sus iniciales>`. Luego, en QA-BR-CRIA-001, pruebe la **transición de fase** Cría → Producción.

**Resultado esperado**: el lote nuevo aparece en el listado con estado activo; la transición pide la población con la que entra a producción y queda registrada en el detalle del lote.

### 4.3 · Historial y Mis pendientes

**Qué hay cargado**: registros en todos los estados; borradores y devueltos para cada operador.

**Qué hacer**: con `qa.operator.breeder` abra **Mis pendientes** y luego **Historial**; filtre por estado «Devuelto».

**Resultado esperado**: Mis pendientes muestra al menos 1 borrador (consumo de agua) y 1 devuelto (alimento con sacos que no cuadran) del propio operador, con el motivo de la devolución visible; el historial permite filtrar por lote, tipo y estado.

### 4.4 · Registrar operaciones (por cadena)

Para cada cadena, entre con su operador, abra el lote indicado y use **Registrar operación**. Registre con fecha de hoy. Después, el supervisor y el aprobador procesarán lo registrado (sección 5).

#### Progenitoras — `qa.operator.gp`
| Prueba | Lote | Datos | Resultado esperado |
|---|---|---|---|
| Alimento | QA-GP-CRIA-001 | 3 800 kg, 95 sacos, alimento «QA Inicio» | queda Registrado; se puede enviar a revisión |
| Pesaje | QA-GP-CRIA-001 | 30 aves, 760 g | registrado; si el peso se aleja de la curva genética aparece alerta |
| Mortalidad | QA-GP-CRIA-001 | 6 hembras, causa «QA Asfixia» | registrado; la población viva baja al aprobarse |
| Mortalidad excesiva | QA-GP-CRIA-001 | 5 000 hembras | **rechazado**: no puede morir más de lo vivo |
| Recolección de huevo | QA-GP-PROD-001 | 37 000 fértiles, 900 sucios | registrado |
| Despacho de huevo | QA-GP-PROD-001 | 20 000 fértiles a QA-INC-F1 | registrado; el saldo de huevo disponible baja |
| Despacho excesivo | QA-GP-PROD-001 | 900 000 fértiles | **rechazado**: no hay saldo |
| Fecha anterior al corte | QA-CUT-GP-001 | cualquier evento con fecha anterior a hace 10 días | **rechazado**: fecha anterior al corte (CUT-GL-02) |

#### Reproductoras — `qa.operator.breeder`
| Prueba | Lote | Datos | Resultado esperado |
|---|---|---|---|
| Agua | QA-BR-CRIA-001 | 7 000 L | registrado |
| Vacunación | QA-BR-CRIA-001 | vacuna «QA Newcastle», vía agua, lote vacuna QA-VL-099 | registrado |
| Recolección diaria | QA-BR-PROD-001 | 6 200 fértiles, 150 sucios, 60 rotos | registrado; el reporte de producción incorpora el día |
| Clasificación | QA-BR-PROD-001 | 6 000 fértiles clasificados | registrado |
| Descarte | QA-BR-PROD-002 | 10 hembras, causa «QA Baja postura» | registrado |
| Transición de fase | QA-BR-CRIA-001 | ver 4.2 | fase Producción activa |

#### Incubadora — `qa.operator.hatchery`
Siga el proceso **en el orden real**, cada paso en el lote que está justo en esa etapa:
| Paso | Lote | Datos | Resultado esperado |
|---|---|---|---|
| Clasificación de huevos recibidos | QA-HAT-REC-001 | 29 600 aptos, 400 descartados | registrado |
| Carga a incubadora | QA-HAT-REC-001 | 29 600 en «QA Incubadora A4», 37,6 °C, 55 % | registrado; la máquina muestra ocupación |
| Ovoscopia | QA-HAT-OVO-001 | 1 300 infértiles | registrado; el saldo de huevo en incubación baja |
| Transferencia a nacedora | QA-HAT-INC-001 | 27 000 a «QA Nacedora N1» | registrado |
| Nacimiento | QA-HAT-NAC-001 | 24 500 sanos, 500 débiles | registrado; aparecen pollitos disponibles |
| Despacho de pollitos | QA-HAT-BIRTH-001 | 10 000 a granja QA-EN-01 | registrado; al aprobarse, QA-EN-01 puede recibirlos |
| Nacimiento excesivo | QA-HAT-NAC-001 | 50 000 sanos | **rechazado**: más pollitos que huevos transferidos |

#### Pollo de Engorde — `qa.operator.broiler`
| Prueba | Lote | Datos | Resultado esperado |
|---|---|---|---|
| Recepción dentro de la OC | QA-BRO-001 | 500 aves, OC `QA-OC-BRO-AVES-003` | registrado (la OC tiene 10 000 y lleva 10 000 recibidas: **este caso debe rechazarse por exceder la OC**) |
| Recepción con OC de prueba BR-18 | lote nuevo en QA-EN-01-G3 | 1 200 aves, OC `QA-OC-BR18-TEST` (límite 1 000) | **rechazado**: excede la orden de compra |
| Recepción válida | mismo lote nuevo | 900 aves, OC `QA-OC-BR18-TEST` | registrado |
| Alimento, agua, mortalidad | QA-BRO-002 | 4 500 kg · 15 000 L · 12 aves | registrados |
| Transferencia entre galpones | QA-BRO-002 | 200 aves a QA-EN-01-G3 | registrado |
| Salida a planta | QA-BRO-003 | 5 000 aves a «QA Planta de Beneficio Norte» | registrado |
| Cierre de lote | QA-BRO-003 | — | **bloqueado** mientras tenga registros sin aprobar; tras aprobarlos y registrar la salida total, el cierre muestra el resumen |

#### Móvil — `qa.mobile`
En el teléfono, abra Gestión Avícola → Pollo de Engorde → QA-BRO-001 y registre alimento (300 kg), agua (800 L) y mortalidad (3 aves). **Resultado esperado**: los tres quedan registrados y aparecen en el historial desde el escritorio.

---

## 5 · Revisión y Aprobaciones

### 5.1 · Centro de Revisión — `qa.supervisor`

**Qué hay cargado**: 3 pendientes de revisión (huevo de progenitoras, mortalidad de engorde, ovoscopia), 2 en revisión, 3 devueltos, 7 corregidos/validados, cientos de aprobados.

**Qué hacer**
1. Pestaña **Pendientes**: tome uno, inícielo y **devuélvalo** con un motivo.
2. Tome otro y **complete la revisión**: en la empresa principal pasa a «Corregido/Validado» (espera al aprobador).
3. Pestaña **Devueltos**: verifique que aparece el que acaba de devolver.
4. Pestaña **Aprobados**: abra uno y revise su detalle.
5. Abra el registro «mortalidad QA-GP-PROD-001» corregido por supervisión y mire la **corrección** (antes/después y motivo).
6. Intente aprobar usted mismo un registro: el supervisor no aprueba en esta empresa (dos niveles).

**Resultado esperado**: las tres vistas se actualizan al instante; el operador ve el devuelto en Mis pendientes con el motivo; la corrección muestra valor original, valor corregido, motivo y autor.

### 5.2 · Aprobaciones — `qa.approver`

**Qué hacer**
1. Apruebe uno de los validados y rechace otro con motivo.
2. Seleccione los 3 validados de los lotes de engorde (QA-BRO-002/003) y apruébelos **en lote**.
3. Abra el registro «mortalidad QA-BR-PROD-001 corregido por el aprobador» e intente aprobarlo.

**Resultado esperado**: aprobado/rechazado se reflejan en el historial y el operador recibe notificación del rechazo; la aprobación en lote aprueba los 3; el registro que **el propio aprobador corrigió no puede ser aprobado por él** (segregación de funciones, BR-14): otro aprobador o el administrador debe hacerlo.

### 5.3 · Reverso de un registro aprobado — `qa.supervisor` + `qa.approver`

**Qué hay cargado**: en QA-BRO-002 ya existe un reverso completo (recepción extra de 500 aves) con su contrapartida aprobada.

**Qué hacer**: abra QA-BRO-002, localice la recepción revertida y su contrapartida; luego solicite el reverso de un **alimento aprobado** de QA-BRO-003 (motivo: «cantidad duplicada»), revíselo como supervisor y apruébelo como `qa.approver`.

**Resultado esperado**: ambos registros quedan **Revertidos**; el consumo acumulado de alimento del lote baja en esa cantidad; un segundo intento de revertir el mismo registro es rechazado; los registros de huevo/incubación no admiten reverso.

### 5.4 · Cancelación — operador

Con `qa.operator.broiler`, en QA-BRO-001 registre un consumo de agua y **cancélelo** antes de enviarlo a revisión. **Resultado esperado**: estado Cancelado; no cuenta en saldos ni reportes.

---

## 6 · Integración SAP — `qa.sap`

**Qué hay cargado** (todo sintético, `QA_SYNTHETIC`): 14 tipos de objeto recibidos (centros, almacenes, materiales, proveedores, centros de costo, lotes SAP, órdenes de compra, órdenes de traslado…), 47 referencias promovidas, 1 centro pendiente de mapeo (QAP7), 1 material inválido (QA-MAT-INVALIDO), 0 envíos.

**Qué hacer**: recorra **Documentos Pendientes**, **Envíos a SAP**, **Errores SAP** y **Bitácora SAP**.

**Resultado esperado**: los listados muestran registros sintéticos con su origen `QA_SYNTHETIC`; el pendiente de mapeo y el inválido aparecen donde corresponde; **no hay envíos** y el envío saliente está deshabilitado; en ningún lugar se indica «SAP conectado». Las órdenes de compra visibles coinciden con las usadas en recepciones (QA-OC-GP-AVES-001 5 000; QA-OC-BR-AVES-002 10 000; QA-OC-BRO-AVES-003 10 000; QA-OC-BRO-AVES-004 12 500; QA-OC-BR18-TEST 1 000).

---

## 7 · Reportes — `qa.auditor` (o supervisor)

**Qué hay cargado**: más de 200 registros aprobados de alimento, peso, mortalidad y huevo en 8 semanas.

**Qué hacer**: abra **Producción**, **Mortalidad** y **Diferencias SAP vs App**; filtre por lote QA-BR-PROD-001 y QA-BRO-003; abra el **informe del lote** QA-CUT-GP-001.

**Resultado esperado**: gráficas y tablas con datos (postura diaria en QA-BR-PROD-001; mortalidad con un pico en la 4.ª semana de QA-BRO-003); en «SAP vs App» las diferencias se calculan sobre datos sintéticos; en el informe de QA-CUT-GP-001 el alimento acumulado aparece como **UNKNOWN** y la conversión alimenticia no se inventa.

---

## 8 · Cargas Iniciales — `qa.supervisor` crea, `qa.approver` aprueba

**Qué hay cargado**: 4 cargas **aplicadas** (una por cadena) con sus lotes QA-CUT-*, y 4 plantillas listas para una carga nueva: `QA_cutover_grandparent.xlsx`, `QA_cutover_breeder.xlsx`, `QA_cutover_hatchery.xlsx`, `QA_cutover_broiler.xlsx` (las entrega el equipo del proyecto junto con esta guía).

**Qué hacer**
1. Abra **Cargas Iniciales** y revise las 4 cargas aplicadas y su **reconciliación** (saldo de apertura, movimientos posteriores, saldo actual).
2. Cree una carga nueva de **Pollo de Engorde** con fecha de corte de hace 5 días, descargue la plantilla y compárela con `QA_cutover_broiler.xlsx`.
3. Suba `QA_cutover_broiler.xlsx`, revise la vista previa, envíe a aprobación; con `qa.approver` apruébela; con `qa.supervisor` aplíquela.
4. Repita con una plantilla **con error**: edite `QA_cutover_breeder.xlsx` y escriba texto en «aves vivas hembras»; súbala.
5. Descargue el informe de errores.

**Resultado esperado**: las aplicadas muestran reconciliación coherente; la nueva carga crea el lote QA-CUT-BRO-NEW-001 con su saldo; la plantilla con error muestra fila, campo, código y mensaje y permite descargar los errores; una celda **vacía** se interpreta como desconocido, **0** como cero real y **N/A** como no aplica; quien crea la carga no puede aprobarla.

---

## 9 · Auditoría — `qa.auditor`

**Qué hacer**: filtre por usuario `qa.operator.broiler` y por acción «aprobación»; abra una entrada.

**Resultado esperado**: se ven las altas, envíos a revisión, aprobaciones, rechazos, correcciones, reversos y aplicaciones de carga, con usuario, fecha y detalle; las acciones de la sección 5 realizadas hoy aparecen con su autor real.

---

## 10 · Administración — `qa.admin`

### 10.1 · Maestros
**Qué hay cargado**: granjas QA-GP-01, QA-BR-01, QA-EN-01, QA-EN-02, QA-INC-F1; incubadora QA-INC-01 con 4 incubadoras y 2 nacedoras; un galpón **inactivo** «QA-GP-01-GX (inactivo)»; catálogos de alimentos, vacunas, medicamentos, causas, transportes, plantas, proveedores, motivos y tipos de corrección con prefijo «QA».

**Qué hacer**: edite el nombre de un proveedor QA; cree un alimento «QA Prueba QA»; intente registrar un evento en el galpón inactivo.

**Resultado esperado**: los cambios se guardan y aparecen en los selectores; el galpón inactivo no es seleccionable.

### 10.2 · Usuarios y Roles
Abra la lista de usuarios y filtre «qa.». **Resultado esperado**: 10 usuarios de la empresa principal (2 pertenecen a la empresa de aislamiento) con su rol; la pantalla de **Roles** muestra los permisos de cada rol por módulo.

### 10.3 · Acceso por unidad
Quite a `qa.operator.broiler` la unidad Pollo de Engorde y pídale que recargue su sesión. **Resultado esperado**: deja de ver la cadena y sus lotes; al devolverle la unidad, vuelve a verlos. En la empresa de aislamiento, intente **habilitar Incubadora** y compruebe que `qa.isolation` pasa a verla.

### 10.4 · Mi Perfil
Con cualquier usuario, cambie la contraseña y vuelva a entrar. **Resultado esperado**: la nueva contraseña funciona; la anterior no.

---

## 11 · Multiempresa — `qa.isolation` y `qa.isolation.operator`

**Qué hay cargado**: QA-ISO-BR-001 (reproductoras en producción) y QA-ISO-BRO-001 (engorde), con un registro de alimento pendiente.

**Qué hacer**: con `qa.isolation.operator` registre mortalidad en QA-ISO-BRO-001; con `qa.isolation` revísela y apruébela (esta empresa tiene un solo nivel: el supervisor aprueba). Busque el lote QA-BRO-001.

**Resultado esperado**: el flujo se completa en un paso; QA-BRO-001 (de la otra empresa) **no existe** para estos usuarios; Progenitoras e Incubadora no aparecen en el menú ni se pueden abrir por URL.

---

## 12 · Notificaciones

**Qué hay cargado**: avisos de cierre previsto vencido (QA-GP-CLOSE-001 y QA-BRO-003), uno leído y otros no, más las alertas que el sistema generó por mortalidad alta y peso fuera de curva.

**Qué hacer**: con `qa.operator.broiler` abra las notificaciones y márquelas como leídas; rechace un registro suyo desde `qa.approver` y vuelva a mirar.

**Resultado esperado**: el contador baja al leer; el rechazo genera una notificación nueva con el motivo.

---

## 13 · Qué hacer si algo falla

1. Anote usuario, pantalla, lote, datos exactos, hora y mensaje recibido en la plantilla de resultados.
2. Tome una captura.
3. Si puede, repita el paso una vez para confirmar.
4. No intente «arreglar» datos: todo el juego de datos es reproducible por el equipo del proyecto.

## 14 · Fuera del alcance de esta prueba

- Conexión a SAP real, usuario técnico SAP, envíos a SAP (martes 20 de octubre de 2026).
- Datos reales del cliente.
- Borrado del juego de datos QA (lo hace el equipo del proyecto cuando el Owner lo decida).
