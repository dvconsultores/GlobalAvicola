# Lotes, maestros y fechas — respuestas QA-001, QA-002, QA-003, QA-004, QA-006, QA-011

**Documento**: explicación funcional para QA (sin código)
**Fecha**: 2026-10-18 · **Spec asociada**: `specs/008-qa-yolinel-findings-remediation/spec.md` (FR-08 / AC-08.3, AC-08.4)
**Carácter**: descripción del comportamiento vigente; recoge lo que queda a decisión del Owner

---

## 1. ¿De dónde salen los lotes? (QA-006)

**SAP nunca crea lotes.** Los lotes nacen de dos orígenes, siempre dentro de Global Avícola:

| Origen | Cómo nace | Cuándo se usa |
|---|---|---|
| **NATIVE** | Alta **manual** del lote, o consecuencia de aprobar una **importación de abuelas** (el lote de la cadena progenitora nace al aprobarse la importación, con su código propio) | Operación normal y entrada de material genético |
| **MIGRATED** | **Cargas iniciales** de la puesta en marcha (cutover) | Traspaso del histórico al arrancar el sistema |

Además cada lote tiene su tipo de activación (normal o manual), que no cambia el origen. Lo importante
para QA: cuando ve un lote, su origen le dice si vino de una carga histórica o de una operación real, y
**ningún lote puede aparecer «creado por SAP»**.

## 2. Maestros y unidad de negocio (QA-001)

- **No existe una relación directa** entre una granja (o una planta) y una unidad de negocio. No hay
  campo que las una, y es **deliberado**: según el requisito de negocio, **una granja aloja galpones de
  varias unidades** (por ejemplo, cría y producción en el mismo predio). Forzar una granja = una unidad
  sería incorrecto.
- La unidad de negocio se **deriva del lote**: del tipo de ave del lote sale la cadena (progenitoras,
  reproductoras, engorde), y de ahí el alcance de lo que cada usuario ve y puede registrar.
- Las **plantas de incubación** se clasifican como una cadena única (incubadora), no se reparten entre
  progenitoras y reproductoras.
- Consecuencia para QA: en los listados, la cadena de un registro **no** se lee de la granja, se lee del
  lote. Si una granja muestra galpones de dos cadenas distintas, es correcto y esperado.
- Decisión Owner opcional (OD-24): filtrar el listado de plantas de incubación por unidad concedida. No
  se implementa en esta ronda.

## 3. ¿Se puede eliminar un maestro? (QA-002)

**No se borra nada.** La acción «Desactivar» es una **baja lógica**:

- el maestro deja de ofrecerse en los formularios, pero la fila sigue existiendo;
- es **reactivable** en cualquier momento desde el mismo listado;
- el histórico que lo referencia **no** queda huérfano ni provoca errores;
- el listado ahora muestra una columna **Estado**, atenúa las filas inactivas y avisa con un mensaje
  claro si la operación falla (antes el fallo era silencioso y el texto decía «no se puede deshacer»,
  que era falso).

Esto vale también para los maestros que provienen de SAP: hoy son referencias locales y **no** hay
borrado destructivo desde Global Avícola. Cuando exista el espejo SAP de solo lectura previsto para
empresas y granjas, seguirán sin poder borrarse desde aquí.

## 4. Identidad de vacunas, medicamentos y causas (QA-003)

- Hoy estos maestros se identifican por su **nombre**, que es obligatorio pero **no único** por empresa.
- **No hay código** de vacuna, medicamento ni causa, y **ninguna fuente lo exige** por contrato.
- Se han corregido las columnas de los listados para mostrar los atributos descriptivos reales
  (laboratorio, tipo, vía; principio activo; descripción) con etiquetas propias, en lugar de reutilizar
  etiquetas de botones.
- **Queda a decisión del Owner (OD-QA2-01)**: ¿se exige que el nombre sea único por empresa? ¿Se añade
  un código? Mientras no se decida, dos vacunas con el mismo nombre en la misma empresa son posibles;
  no es un defecto, es una ausencia de regla.

## 5. Zona en incubadoras (QA-004)

- Las **plantas de incubación** tienen **ubicación** (texto libre) y **no** tienen zona/área como las
  granjas.
- Según el requisito de negocio, «Área» es una estructura **organizativa**, no una zona física; por eso
  no se copia sin más el modelo de granja.
- **Decisión Owner (OD-QA2-02)**: si las plantas deben manejar zona igual que las granjas. Sin
  implementación en esta ronda.

## 6. Segregación de funciones (QA-011)

Regla **BR-14**, configurable por empresa mediante los pasos de aprobación (regla **RR-03**). Por
defecto está **activa**.

**Quién no puede aprobar un registro:**

1. quien lo **registró**;
2. quien lo **corrigió**;
3. quien lo **rechazó** previamente.

**Quién sí puede**: el supervisor que lo revisó (devolver con observaciones no es aprobar, así que el
mismo supervisor revisa el reenvío) y cualquier aprobador que no incurra en los tres casos anteriores.

La comprobación se aplica en **todos** los caminos de aprobación, incluido el de un único nivel de
aprobación, en el que «completar la revisión» equivale a aprobar. Si la empresa tiene configurada la
segregación como **desactivada**, las tres exclusiones dejan de aplicarse a la vez; una empresa sin pasos
configurados **no** puede haber renunciado al control sin saberlo, así que se le exige.

Nota para QA: si alguien intenta aprobar su propio registro, verá un **403** con el mensaje de
segregación de funciones. Es el comportamiento correcto, no un fallo de permisos.

## 7. Fechas (QA-016)

- **Solo la fecha del evento** rechaza valores futuros. Es la fecha que sitúa el hecho productivo y la
  que alimenta saldos y periodos.
- En pantalla, el selector de la fecha del evento —y las fechas de salida y llegada en la importación de
  abuelas— ya no permite elegir un día posterior a hoy.
- Las **demás fechas** (fechas de inspección, de parámetros de incubación, de documentos) no se limitan
  hoy. Algunas pueden ser legítimamente futuras porque describen un plan. **Decisión Owner**: cuáles se
  limitan y con qué semántica.
