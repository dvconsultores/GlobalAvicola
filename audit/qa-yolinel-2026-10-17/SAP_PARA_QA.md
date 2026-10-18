# Cómo Global Avícola recibe información de SAP — respuesta a QA-005

**Documento**: explicación funcional para QA (sin código, sin SQL)
**Fecha**: 2026-10-18 · **Spec asociada**: `specs/005-*` (integración SAP inbound) · **Spec de esta ronda**: `specs/008-qa-yolinel-findings-remediation/spec.md` (FR-08 / AC-08.2)
**Carácter**: descripción del flujo vigente; el envío a SAP **no está activo**

---

## 1. Idea de partida: SAP es la fuente, Global Avícola es el lector

Global Avícola **no escribe** en SAP. Lee de **SAP HANA Cloud** en modo **solo lectura**. La conexión es
unidireccional: SAP → Global Avícola. No existe en esta ronda ningún proceso que envíe información de
vuelta a SAP, y la conexión contra el sistema real **todavía no está establecida**: la prueba programada
está fijada para el **2026-10-20**.

Mientras esa prueba no se complete, todo el flujo funciona con el **modo sintético** descrito en §4.

## 2. Los 14 objetos que se leen

La integración lee exactamente **14 objetos** de HANA. Cada objeto corresponde a una entidad de SAP que
Global Avícola necesita conocer (sociedades, centros, almacenes, proveedores, materiales, órdenes de
compra y sus posiciones, etc.). No se lee la base completa de SAP ni tablas arbitrarias: la lista es
cerrada y declarada en el registro de objetos de entrada.

## 3. El recorrido de un dato, en cinco pasos

```
 SAP HANA Cloud (solo lectura)
        │  lectura de los 14 objetos
        ▼
   1. RAW            copia fiel de lo leído; nada se interpreta ni se corrige
        ▼
   2. VALIDACIÓN     se comprueba forma y coherencia; lo inválido se marca y no avanza
        ▼
   3. MAPEO          sociedad / centro / almacén  →  empresa (y cadena, cuando es determinable)
        ▼
   4. STAGING        todo queda guardado y consultable, ya validado y mapeado
        ▼
   5. PROMOCIÓN CONTROLADA
        └─► referencias operativas (lo que usan los formularios)
```

- **RAW**: la fotografía de lo que SAP devolvió. Sirve de contraste cuando alguien pregunta «¿esto qué
  decía en SAP?».
- **VALIDACIÓN**: descarta lo incompleto o incoherente; un dato rechazado no desaparece, queda visible
  como no válido.
- **MAPEO**: traduce las claves de SAP al lenguaje de Global Avícola. Es el paso clave para QA: la
  **empresa** de una referencia no se deduce del nombre, se deduce del **centro/almacén** de SAP cuando
  existe equivalencia declarada.
- **STAGING**: el dato ya es legible, pero todavía no es «verdad operativa».
- **PROMOCIÓN CONTROLADA**: solo un subconjunto de objetos se convierte en **referencia** utilizable en
  los formularios. La promoción no es automática para todo; está acotada por tipo de objeto.

## 4. Qué se promueve y qué se queda solo en staging

- Se promueven a **referencias** los objetos que los formularios necesitan seleccionar y que tienen una
  equivalencia empresa/clave **aprobada**. La promoción de la **unidad de negocio** solo ocurre para los
  objetos de tipo **planta** (`PLANT`): es la única vía por la que una referencia de SAP «sabe» a qué
  cadena pertenece.
- El **resto** de objetos permanece **solo en staging**: se consulta, se audita, se usa como evidencia,
  pero **no** alimenta selectores ni se puede usar para registrar operaciones.

Consecuencia práctica para QA: si un valor aparece en SAP y no aparece en un desplegable, lo primero que
hay que comprobar es si su objeto **se promueve** y si su mapeo empresa/cadena está aprobado. No es un
defecto de la pantalla; es un objeto staging-only o un mapeo pendiente.

## 5. Qué ve QA en la pantalla de Integración SAP

- El **estado** de la integración y el modo en que está corriendo (sintético o real).
- Las **ejecuciones** de lectura con su resultado: cuántos registros se leyeron, cuántos pasaron la
  validación, cuántos se mapearon y cuántos se promovieron.
- Los **errores de validación o de mapeo**, con el objeto y la clave afectados.
- Las **referencias** que ya están disponibles para operar y las que están pendientes de mapeo.
- La **trazabilidad**: qué ejecución trajo cada referencia.

Lo que QA **no** verá: escritura, envío, sincronización en dos sentidos, ni cambios hechos desde Global
Avícola hacia SAP.

## 6. Qué significa `QA_SYNTHETIC`

`QA_SYNTHETIC` identifica los datos de referencia creados **para poder probar** sin conexión real a SAP.
Son registros deliberadamente marcados como sintéticos:

- se reconoce su origen en la etiqueta, así que **no** se confunden con información real de SAP;
- permiten ensayar el flujo completo (selección de OC, mapeo, filtros, BR-23);
- **no** acreditan que la integración real funcione. Esa acreditación depende de la prueba del
  **2026-10-20**.

## 7. Qué **no** está activo hoy

| Capacidad | Estado |
|---|---|
| Envío de operaciones a SAP | **No activo** |
| Conexión contra SAP real | **No activa** — prueba programada **2026-10-20** |
| Escritura en SAP | **No existe por diseño** (HANA solo lectura) |
| Creación de lotes desde SAP | **No existe**: SAP nunca crea lotes (ver `LOT_ORIGIN_AND_MASTERS_FOR_QA.md`) |
| Autocompletado de granja/galpón/lote desde la OC | **Pendiente de mapeo** (SAP-STO-01, AOD-02, OD-24 P-08) |

El estado `consolidated` es el último paso interno del flujo operativo; los estados de SAP
(`sent_to_sap`, `sap_confirmed`, `sap_error`) existen en el modelo y quedan **fuera** del flujo humano
mientras el envío no se active.

## 8. La regla nueva **BR-23** (respuesta a QA-007)

Una orden de compra puede estar asociada a una **cadena productiva** (progenitoras, reproductoras,
incubadora, engorde) gracias al mapeo de sus **centros** de SAP.

- Si la cadena de la OC es **conocida** y **no coincide** con la cadena del lote que recibe las aves, el
  sistema **rechaza** la recepción con un mensaje de negocio: una OC de engorde no puede usarse en
  reproductoras ni al revés.
- Si los centros de la OC apuntan a **cadenas distintas entre sí**, se rechaza: no hay una cadena única
  que comparar.
- Si la cadena de la OC es **desconocida** (sin mapeo aprobado), la recepción **se permite** y la OC se
  muestra rotulada como **«sin cadena»**. No se inventa una cadena ni se bloquea por ignorancia: se
  informa.

La regla se aplica en la **recepción de aves**, que es el momento en que la entrega física debe cuadrar
con la cadena productiva del lote. Como complemento, el selector de órdenes de compra ya **filtra** las
OC por la cadena del lote, de modo que lo que se ofrece en pantalla es coherente con lo que el backend
acepta.

Decisión pendiente (Owner): si en el futuro una OC **sin cadena** debe **bloquearse** en lugar de
permitirse y rotularse.
