# GA-FE-08 · GUÍA DE UAT DEL PROPIETARIO — DESCUBRIMIENTO DE «LOTES»

Versión para validación del propietario. Sin tecnicismos. Sesión preparada por ingeniería; usted solo comprueba lo que ve.

## Contexto (recuerde)

En su sesión de aceptación de Lotes (UAT-01 de esa fecha) usted señaló: **no encontraba «Lotes» en el menú** y hubo que darle un enlace directo. Eso quedó registrado como mejora pendiente. Esta versión añade el acceso **natural** al módulo, sin cambiar nada más del producto.

## Qué observar (5 casos)

1. **Encontrar «Lotes» sin enlace directo**: entre con un usuario operativo de su confianza → en el menú, abra **«Gestión Avícola»** → ¿aparece la opción **«Lotes»** en la primera posición?
2. **Al pulsarla**: ¿abre el **listado de lotes** correcto (el mismo que ya conocía)?
3. **Sin acceso**: cuando el usuario no tiene la línea concesionada (o la empresa la tiene apagada), ¿la opción **desaparece** del menú?
4. **Al conceder un acceso nuevo** (por la pantalla de administración de accesos, como siempre): ¿la opción **vuelve a aparecer** en su menú?
5. **Móvil**: con el mismo usuario, ¿el camino es claro? (barra inferior → «Gestión Avícola» → «Lotes»).

## Preguntas (UAT)

- «¿Puede encontrar la opción Lotes de forma natural en el menú?»
- «¿Al pulsarla llega al listado correcto?»
- «¿Cuando el usuario no tiene acceso, la opción desaparece?»
- «¿Después de una concesión válida, la opción vuelve a aparecer?»
- «¿En móvil la ubicación es clara?»

## Qué NO necesita probar

Rutas técnicas, permisos internos, ataques de seguridad, cálculos: ya están certificados y se le entregan como evidencia (capturas C01-C09).
