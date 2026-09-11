# GA-UAT-05 · Notas de interpretación — walkthrough de referencia

Este documento aclara la lectura de `reference-walkthrough.json` para evitar sobreinterpretaciones.

## Campo `masters_admin.columnas_estado_visibles`

El valor `true` del JSON es un **falso positivo del detector automático**: la comprobación buscaba texto con «activa/inactiva/estado» en la página, y el texto encontrado proviene del **nombre** de un área («Nave Activa …» de pruebas anteriores), no de una columna de estado.

**Verificado visualmente en `C05-masters-admin.png`:** la pantalla «Áreas Funcionales» muestra **nombre + código** y **no marca visualmente** cuál está retirada. Conclusión correcta: **presencia** de las áreas retiradas = **PASS**; **distinción visual de estado** = no soportada hoy (limitación registrada como nota en evidencia y guía; no es defecto de R-185, cuyo efecto verificable es la no elegibilidad en el selector).

## Consola (`console_desktop`)

10 entradas de error, todas del mismo mensaje: «Failed to load resource: … 403 (Forbidden)» — widgets KPI sin permiso para roles operativos (clase N-3 preexistente, ya registrada en GA-FE-06; invisible en uso normal del formulario). **Errores fatales: 0.** El conteo varía según las páginas visitadas y no indica regresión.

## `create`

Creación por UI en el walkthrough de referencia: HTTP **201**, lote `UAT7-NUEVO-01` id **52**, `area_id` 14 (la activa) — registrado en el JSON y consistente con el ledger de datos.

## Opciones del selector

Desktop y móvil devuelven la **misma** lista: «Seleccionar área…» + «Nave Disponible (UAT GA-FE-07)». Las áreas retiradas (15 y 16) **no** aparecen. Sin IDs crudos.
