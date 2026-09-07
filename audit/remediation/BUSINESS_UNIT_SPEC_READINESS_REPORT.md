# ¿SE PUEDE ESCRIBIR YA LA SPEC?

2026-09-07 · veredicto de preparación para `GA-REM-040`

---

## 1. Veredicto

```
NOT_READY_FOR_GA-REM-040_SPEC
```

Faltan **dos decisiones del propietario** sin las cuales la spec tendría que inventarlas, y
`NO SPEC = NO DEVELOPMENT` no se cumple escribiendo una spec que adivina.

```
BU-D01   ¿qué ve cada línea cuando el producto cambia de manos?   (siete flujos)
BU-D02   ¿quién ve un registro cuya línea no se puede determinar?
```

**Actualización del 2026-09-07.** Eran cinco. El propietario resolvió tres —`BU-D11 = C`,
`BU-D12 = B`, `BU-D09 = B`—, formalizadas en `specs/remediation/OD-09-CONTROL-PLANE-VS-BUSINESS-UNIT.md`:

```
BU-D11  →  OD-09.a   visibilidad de control de empresa · operación por unidad
BU-D12  →  OD-09.b   plano de control transversal · plano operativo por unidad
BU-D09  →  OD-09.c   entra sin unidades · lo transversal que su rol permita · nada productivo
```

Con ellas quedan resueltas las fases 1, 2 y 3 de la hoja de ruta en lo que dependía de decisión.
`BU-D05` sigue sin bloquear la spec: `ENV-01` lo sitúa en el alta del primer cliente real.

## 2. Lo que sí está listo

No todo está bloqueado, y conviene decirlo para que la decisión no parezca más grande de lo que
es:

| Preparado | Evidencia |
|---|---|
| El inventario de lo que existe y lo que falta | 21 matrices de auditoría, 2026-09-07 |
| La correspondencia línea ↔ dato descriptivo | las cuatro, verificadas |
| El aislamiento por empresa sobre el que apoyarse | certificado y probado |
| La guarda que impide olvidar una ruta | `authorization_coverage.py`, en arranque |
| El identificador compartido para los traspasos | `lots.lot_code`, único e indexado |
| La forma de las entidades de traspaso | bilateral, sin columna nueva |
| El identificador de spec libre | `GA-REM-040` |

La base es sólida. Lo que falta es una dimensión nueva, no un arreglo de lo que hay.

## 3. Qué desbloquea qué

```
BU-D11 + BU-D12 + BU-D09   →  FASE 1  catálogo, modelo y migración vacía
                               FASE 2  resolución del acceso efectivo
                               FASE 3  guarda central en las consultas

BU-D01                     →  FASE 12 contratos entre líneas
BU-D02                     →  FASE 4  filtro por fila
BU-D05                     →  FASE 13 migración        (y el primer cliente real)
```

Las tres primeras decisiones desbloquean **la mitad de la hoja de ruta**. Decidirlas primero no
es un orden arbitrario: es lo que permite empezar.

## 4. Una spec o dos

**Dos**, y por una razón concreta.

```
GA-REM-040   MECÁNICA DE ACCESO POR UNIDAD DE NEGOCIO
             catálogo · habilitación · concesión · acceso efectivo · guarda central
             filtro por fila · sesión · navegación · agregados · administración
             depende de   BU-D09 · BU-D11 · BU-D12 · BU-D02

GA-REM-041   CONTRATO DE VISIBILIDAD ENTRE UNIDADES
             los siete flujos · las cuatro categorías · el dato de destino en el despacho
             depende de   BU-D01
```

La primera es mecánica de acceso, se prueba con «ve / no ve» y es homogénea. La segunda es
**diseño de producto**: decide qué necesita cada línea del negocio para trabajar, y su prueba es
funcional, no de seguridad. Mezclarlas haría que un cambio de criterio comercial obligara a
tocar la spec de seguridad.

`GA-REM-041` está libre y se propone reservarlo; **no se crea ninguno de los dos aquí**.

## 5. La segunda dimensión de certificación

Los catorce procesos certificados hacen exactamente lo que sus specs exigen. Ninguno se rebaja:
cuando se certificaron, este requisito no existía. Rebajarlos ahora sería reescribir la historia.

Lo que se propone es **medir dos cosas en vez de una**:

```
CERTIFICACIÓN FUNCIONAL              14 / 15      sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD    0 / 15      el requisito aún no existe
```

Un proceso quedará **plenamente certificado** cuando pase las dos. Hasta que la primera unidad
exista, la segunda columna no puede tener ningún `PASS`, y **no se va a rellenar con ninguno**:
un `PASS` sobre una capacidad inexistente es exactamente el tipo de evidencia que
`GA-REM-016 AC13` prohíbe, porque no hay forma de hacerlo fallar.

### Estructura propuesta de `PROCESS_BUSINESS_UNIT_ACCESS_MATRIX.md`

A crear **cuando la capacidad exista**, no antes:

| Columna | Qué contesta |
|---|---|
| Proceso | `P-01` … `P-15` |
| Certificación funcional | estado actual, copiado, no recalculado |
| ¿Toca alguna línea? | o es transversal |
| Entidades filtradas | las que el proceso lee y escribe |
| Aislamiento en listados | ¿ve solo lo suyo? |
| Aislamiento en agregados | ¿el total cuenta solo lo suyo? |
| Contrato de traspaso | ¿respeta las cuatro categorías? |
| Prueba `E2E` de seguridad | la que lo demuestra |
| Mutación que la hace fallar | `GA-REM-016 AC13` |
| Certificación de acceso | `PASS` · `FAIL` · `N/A` |

Las quince filas nacerían con la última columna en **`PENDIENTE`**, y la penúltima es la que
impide que un `PASS` signifique «no lo probamos».

## 6. Riesgo de construir antes de decidir

```
BU-D02 sin decidir    o puerta abierta, o inspecciones que desaparecen
BU-D01 sin decidir    P-10 se rompe al cortar la cadena generacional

RESUELTOS (OD-09, 2026-09-07)
BU-D11    P-14 conserva OD-08: los avisos no se filtran por concesión de unidad
BU-D12    la frontera es una decisión, no una deducción de cada pantalla
BU-D09    entrar sin unidades queda escrito, y con ello el primer día de cada cliente
```

El primero es el que más pesa: es el único que **rompe algo que hoy está certificado**, y lo hace
sin ruido.

## 7. Recomendación

```
1   decidir BU-D11 · BU-D12 · BU-D09          HECHO — OD-09, 2026-09-07
2   decidir BU-D01 con su matriz de flujos    la más larga, y la de más valor de negocio
3   decidir BU-D02
4   escribir GA-REM-040 y reservar GA-REM-041
5   construir en el orden de la hoja de ruta, con los agregados dentro
6   BU-D05 antes del primer cliente real
```

## 8. Alcance de este informe

```
MODO                     ANÁLISIS DE DECISIÓN
CÓDIGO MODIFICADO        NINGUNO
TABLAS · MIGRACIONES     NINGUNA
SPEC CREADA              NINGUNA
CERTIFICACIONES TOCADAS  NINGUNA
OD- DEFINITIVOS          NINGUNO ASIGNADO
DECISIONES TOMADAS       NINGUNA
```
