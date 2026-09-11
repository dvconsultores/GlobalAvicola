# GA-FE-04 · UAT DEL PROPIETARIO (P-13 visible)

**OWNER_UAT_READY: YES** (2026-09-11, tras GA-FE-04-A: P13-AC20/AC21 PASS; sin cambios de producto; generación `index-B66tpdeW.js` estable).

Para el propietario · sin jerga · 10-15 min · producción https://avicola.globaldv.net

## Qué cambió para usted

Antes: si un usuario solo podía **leer**, las pantallas igual le mostraban botones de escritura (Crear, Editar, Eliminar, Aprobar…). La operación fallaba al pulsar (el servidor la rechazaba), pero el botón estaba ahí.

Ahora: la interfaz muestra **solo las acciones que su permiso permite**. Quien no puede ejecutar una acción, no la ve. El servidor sigue rechazando lo que no está permitido (eso no cambió).

## Qué observar (5 puntos)

1. **Usuario de solo lectura en Maestros** — entre a «Maestros → Granjas» con un usuario de solo consulta: no debe ver «Nuevo», ni «Editar», ni «Eliminar»; verá una nota «Vista de solo lectura».
2. **El mismo usuario en Usuarios** — no debe ver «Crear» ni lápiz ni papelera en las filas.
3. **Enlaces directos** — si ese usuario escribe directamente la dirección de «Nuevo lote», «Nueva operación» o «Corregir», verá «No tiene permiso para ver esta sección» en lugar de la pantalla de alta.
4. **Usuario con permiso y unidad** — quien sí puede registrar operaciones y tiene su unidad asignada sigue viendo sus botones y pantallas de alta con normalidad.
5. **Aprobaciones** — quien puede aprobar pero no rechazar, verá «Aprobar» sin «Rechazar» (y al revés). El botón de lote solo aparece para revisores.

## Preguntas (responda con A/B/correcciones)

1. ¿La conducta descrita (1-5) corresponde a lo que esperaba de un control por permisos?
   A) SÍ, correcto B) NO — detalle: ____
2. ¿Algún caso donde **ahora falte un botón que sí debería ver** un usuario con permiso?
   A) NO B) SÍ — detalle: ____
3. ¿Observaciones de negocio?

## Estado técnico (resumen)

- R-98 (residuo histórico «ninguna pantalla ocultaba acciones de escritura»): **CLOSED** técnicamente — pendiente solo de su visto bueno.
- Evidencia: 16 capturas, pruebas 22/22 específicas + 263/263 totales, verificaciones directas contra el servidor (403 cuando corresponde).
- Datos de prueba: creados y retirados en la misma sesión; su empresa quedó exactamente como estaba (4 unidades apagadas); el rol «Administrador de Accesos» (35) no se tocó.

_Al responder «ACEPTO GA-FE-04», el registro de aceptación se anexará a este documento y el estado pasará a OWNER_ACCEPTANCE=PASS._
