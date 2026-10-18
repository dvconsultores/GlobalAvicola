# Global Avícola — Manual de usuario

Guía de todas las opciones del sistema y qué hace cada una. Pensada para usuarios finales: operadores de granja e incubadora, revisores, aprobadores y administradores.

> Lo que cada persona ve en el menú depende de sus **permisos** y de las **unidades de negocio** que tenga concedidas. Si una opción descrita aquí no aparece en su pantalla, es que su rol no la tiene habilitada: solicítela al administrador.

---

## 1 · Conceptos básicos

- **Unidad de negocio (cadena productiva)**: Progenitoras (abuelas), Reproductoras, Incubadora y Pollo de Engorde. El sistema solo muestra las unidades que su empresa tiene habilitadas y que a usted le han concedido.
- **Lote**: un grupo de aves (o un proceso de incubación) que se sigue a lo largo de su ciclo de vida. Todo movimiento se registra contra un lote.
- **Evento operativo**: cada hecho que se registra (recepción, mortalidad, pesaje, recolección de huevo, etc.). Un evento nace en borrador, se envía a revisión, se aprueba y queda consolidado.
- **Empresa activa**: si usted pertenece a varias empresas, trabaja «situado» en una; puede cambiarla desde su sesión. Todo lo que ve y registra pertenece a esa empresa.
- **Estados de un registro**: Borrador → Registrado → En revisión → Aprobado (o Devuelto para corregir / Rechazado) → Consolidado. Los documentos que van a SAP añaden Enviado y Confirmado.

El menú se agrupa en seis secciones: **Principal, Operativo, Revisión, Integración, Reportes y Administración**.

---

## 2 · Dashboard (Inicio)

Pantalla de entrada. Muestra un resumen del estado: indicadores clave, lotes activos, pendientes y accesos rápidos a las tareas más frecuentes. Es el punto de partida; desde el menú lateral se llega a todo lo demás. Requiere el permiso de lectura de panel.

---

## 3 · Gestión Avícola (sección Operativo)

Es el corazón del día a día. Agrupa los lotes, el historial, sus pendientes y las cuatro cadenas productivas.

### 3.1 · Lotes

Lista de todos los lotes de las unidades que usted maneja, con su estado, unidad, granja y saldo. Permite:

- **Ver el detalle de un lote**: población viva, fase actual, saldo de apertura, indicadores (mortalidad, conversión de alimento, peso), eventos recientes, alertas y el árbol de trazabilidad generacional (de qué lote vienen los huevos/pollitos y a cuáles dieron origen).
- **Crear un lote nuevo** (si tiene permiso): se define empresa, granja, galpón, unidad y código.
- **Transición de fase**: pasar un lote de Cría a Producción, registrando la población con la que entra a la nueva fase.
- **Cierre de lote**: cerrar un lote al final de su ciclo; el sistema resume su resultado.
- **Informe del lote** y enlace a sus reportes e indicadores.

### 3.2 · Historial

Lista de todos los eventos operativos registrados, con filtros por lote, tipo y estado. Sirve para consultar qué se registró, cuándo, por quién y en qué estado está.

### 3.3 · Mis pendientes

Sus tareas abiertas: eventos en borrador o devueltos para corregir que dependen de usted. Es su «bandeja de entrada» operativa.

### 3.4 · Registrar una operación

Desde cualquier lote o proceso se abre el **asistente de registro de operaciones**, que muestra solo los eventos que corresponden a la etapa del lote, agrupados por categoría:

- **Movimientos de aves**: recepción, distribución a galpones, transferencia interna y salida de aves.
- **Manejo diario**: alimento, agua, pesaje, mortalidad y descarte.
- **Sanidad**: vacunación y medicación.
- **Inspecciones**: de granja, de transporte y de incubadora.
- **Huevos**: recolección y clasificación, despacho, recepción en incubadora y clasificación de lo recibido.
- **Incubación**: carga a incubadora, ovoscopia, transferencia a nacedora, registro de nacimiento y despacho de pollitos.
- **Ciclo del lote**: importación de abuelas y cierre de lote.

Cada operación valida reglas de negocio automáticamente (no se puede registrar más mortalidad que aves vivas, no se despacha más huevo del disponible, las fechas deben ser coherentes, etc.).

### 3.5 · Las cuatro cadenas y sus procesos

Cada unidad tiene su propio flujo guiado. El sistema solo ofrece, en cada etapa, las operaciones que tienen sentido allí.

**Progenitoras (abuelas)** — ícono avión. Dos etapas:
- **Cría**: importación y llegada de las abuelas, inspección de granja, recepción y distribución, alimento, pesaje semanal, vacunación, medicación, mortalidad, descarte y traslado a producción.
- **Producción**: inspección, alimento, pesaje, sanidad, mortalidad, descarte, recolección y clasificación de huevos, despacho de huevo y cierre.

**Reproductoras** — ícono pluma. Dos etapas:
- **Cría**: inspección, recepción y distribución de pollitas, alimento, agua, pesaje semanal, sanidad, mortalidad, descarte y traslado a producción.
- **Producción**: inspección, alimento, agua, pesaje, sanidad, mortalidad, descarte, recolección diaria de huevo fértil, despacho a incubadora y cierre.

**Incubadora** — ícono llama. Proceso de planta: inspección, recepción de huevos, clasificación de los huevos recibidos, carga a las máquinas de incubación, ovoscopia, transferencia a nacedora, registro de nacimiento y despacho de pollitos (con su mortalidad y descarte propios).

**Pollo de Engorde** — ícono muslo. Recepción y distribución, alimento, agua, pesaje, sanidad, mortalidad, descarte, salida a planta de beneficio y cierre de lote.

---

## 4 · Revisión y Aprobaciones (sección Revisión)

Separa a quien registra de quien aprueba (segregación de funciones).

### 4.1 · Centro de Revisión

Bandeja de los eventos que esperan revisión, con tres vistas:
- **Pendientes**: lo que falta revisar.
- **Aprobados**: lo ya validado.
- **Devueltos**: lo que se regresó al operador para corregir.

Desde el detalle de un evento el revisor puede **aprobar**, **devolver para corrección** (indicando el motivo) o **corregir** directamente cuando tiene ese permiso. Las correcciones quedan registradas con su antes/después y motivo.

### 4.2 · Aprobaciones

Pantalla del aprobador: confirma o rechaza los registros que llegan a su nivel. Quien creó o devolvió un registro no puede aprobarlo (control de segregación).

---

## 5 · Integración SAP (sección Integración)

Panel de la conexión con SAP. Según la fase activa muestra:
- **Documentos pendientes** de sincronizar o enviar.
- **Envíos a SAP** realizados.
- **Errores SAP** para su revisión.
- **Bitácora SAP**: historial de la integración.

En la fase actual la integración es de **solo lectura entrante** (el sistema recibe maestros y órdenes desde SAP); el envío saliente está deshabilitado hasta su activación formal. Requiere el permiso de lectura SAP.

---

## 6 · Reportes (sección Reportes)

Indicadores y comparativos. Las opciones del menú:
- **Producción**: huevos producidos, postura (hen-day), fertilidad.
- **Mortalidad**: tasa de mortalidad sobre la población real del lote.
- **Diferencias SAP vs App**: comparación entre lo registrado en la aplicación y lo que figura en SAP.

Además, el informe por lote reúne sus indicadores: **conversión de alimento (FCR y AFCR)**, **índice de productividad (IPE)**, **uniformidad de peso**, **mortalidad**, **producción de huevo** y la serie semanal del lote. Los datos que no se conocen se muestran como UNKNOWN, nunca como cero. Requiere el permiso de lectura de reportes.

---

## 7 · Administración (sección Administración)

### 7.1 · Cargas Iniciales (saldos de apertura)

Para poner en marcha el sistema con lotes y procesos que ya existían el día del arranque («corte»). Flujo guiado, una plantilla por unidad de negocio:

1. Elegir **unidad** y **fecha/hora de corte** y **crear la carga**.
2. **Descargar la plantilla** de esa unidad en Excel o CSV (incluye instrucciones por campo y los catálogos válidos de su empresa).
3. Rellenar los datos. Regla de oro: **celda vacía = dato desconocido · `0` = cero real · `N/A` = no aplica**. Fechas AAAA-MM-DD, pesos en gramos.
4. **Subir el archivo**: el sistema valida cada fila y muestra los errores (fila, campo, código, mensaje, valor recibido); se pueden **descargar los errores** para corregir en bloque.
5. Ver la **vista previa** por unidad, **enviar a aprobación**, que **otro usuario apruebe**, y **aplicar**.
6. Ver la **reconciliación** (saldo de apertura, movimientos posteriores al corte y saldo actual) y continuar la operación normal registrando el primer evento, que debe tener fecha posterior al corte.

Es una capacidad de administración; requiere permisos de cargas iniciales.

### 7.2 · Auditoría

Bitácora de quién hizo qué y cuándo: altas, cambios, aprobaciones, aplicaciones, intentos fallidos. Consulta de solo lectura para control interno. Requiere el permiso de auditoría.

### 7.3 · Maestros

Administra los catálogos que alimentan todo el sistema: empresas, granjas, galpones, plantas de incubación, incubadoras, nacedoras, áreas, líneas genéticas, razas, fases productivas, proveedores, tipos de alimento, vacunas, medicamentos, causas de mortalidad, causas de descarte, transportes, plantas de beneficio, motivos de rechazo y tipos de corrección. Crear, editar y activar/desactivar cada registro. Requiere el permiso de maestros.

### 7.4 · Configuración

- **Usuarios y Roles**: alta y gestión de usuarios, asignación de rol.
- **Roles**: definición de roles y sus permisos (qué puede ver y hacer cada rol, módulo por módulo).
- **Mi Perfil**: sus datos y preferencias; disponible para todos.
- **Acceso por unidad**: qué cadenas productivas tiene habilitadas la empresa y cuáles se conceden a cada usuario. Es lo que determina qué unidades aparecen en el menú de cada persona.

---

## 8 · Anexos

### 8.1 · Catálogo de eventos operativos

| Evento | Qué registra |
|---|---|
| Importación de abuelas | Llegada e importación de aves abuelas (país, embarque, proveedor) |
| Recepción de aves | Entrada de aves a la granja, con cantidades |
| Distribución | Reparto de las aves recibidas a los galpones |
| Transferencia | Movimiento interno de aves entre galpones del lote |
| Salida de aves | Salida del lote (a otra etapa o a planta) |
| Alimento | Consumo de alimento (kg) |
| Agua | Consumo de agua (reproductoras y engorde) |
| Pesaje | Peso promedio del lote (gramos) |
| Mortalidad | Aves muertas, con causa |
| Descarte | Aves descartadas, con causa |
| Vacunación | Vacuna aplicada |
| Medicación | Medicamento aplicado |
| Inspección de granja / transporte / incubadora | Verificación de condiciones |
| Recolección de huevos | Huevos producidos, por tipo y peso |
| Clasificación de huevos | Clasificación de lo recolectado |
| Despacho de huevos | Envío de huevo (a incubadora u otro destino) |
| Recepción de huevos (incubadora) | Llegada de huevo a la planta |
| Clasificación de huevos recibidos | Aptos / no aptos |
| Carga de incubación | Huevos cargados a las máquinas |
| Ovoscopia | Control de fertilidad del huevo incubado |
| Transferencia a nacedora | Paso de incubadora a nacedora |
| Nacimiento | Pollitos nacidos (sanos y débiles) |
| Despacho de pollitos | Salida de pollitos viables |
| Cierre de lote | Cierre del ciclo del lote |

### 8.2 · Permisos por módulo

Cada rol se arma con permisos sobre estos módulos: panel, lotes, operaciones, revisión, aprobaciones, correcciones, reportes, SAP, cargas iniciales, auditoría, maestros, usuarios y unidades de negocio. Las acciones posibles son leer, crear, actualizar, revisar, corregir, aprobar, rechazar, validar, enviar y aplicar, según el módulo.

### 8.3 · Móvil

En teléfono, el menú se concentra en **Gestión Avícola** y sus cadenas, para el registro de campo. El resto de la administración se realiza desde la vista de escritorio.
