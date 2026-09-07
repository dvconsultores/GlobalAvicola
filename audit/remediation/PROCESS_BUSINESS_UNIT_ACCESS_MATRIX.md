# CERTIFICACIÓN DE ACCESO POR UNIDAD DE NEGOCIO

Creada 2026-09-07 · gobierna `GA-REM-040` · **ninguna fila certificada todavía**

---

## 1. Por qué existe esta matriz y no una columna más

Los catorce procesos certificados hacen exactamente lo que sus specs exigen. Cuando se
certificaron, el acceso por unidad de negocio **no era un requisito**. Rebajarlos ahora sería
reescribir la historia.

```
CERTIFICACIÓN FUNCIONAL                14 / 15     no cambia
CERTIFICACIÓN DE ACCESO POR UNIDAD      0 / 15     dimensión nueva
```

Un proceso queda **plenamente certificado** cuando pasa las dos.

## 2. Por qué todo está en `PENDIENTE` y va a seguir estándolo

La capacidad **no existe**: no hay catálogo de unidades, ni habilitación por empresa, ni
concesión por usuario. Un `PASS` sobre una capacidad inexistente es exactamente la evidencia que
`GA-REM-016 AC13` prohíbe, porque **no hay forma de hacerlo fallar**.

```
Ninguna fila se rellena hasta que exista lo que se está midiendo.
```

## 3. La matriz

| Proceso | Cert. funcional | Alcance de unidad | Empresa `OFF` | Usuario sin concesión | Entre unidades | Cert. de acceso |
|---|:--:|---|:--:|:--:|:--:|:--:|
| `P-01` Progenitoras — Cría | `CERTIFIED` | Progenitoras | `PENDIENTE` | `PENDIENTE` | no | **`PENDIENTE`** |
| `P-02` Progenitoras — Producción | `CERTIFIED` | Progenitoras → Reproductoras | `PENDIENTE` | `PENDIENTE` | **sí** · flujo 1 | **`PENDIENTE`** |
| `P-03` Reproductoras — Cría | `CERTIFIED` | Reproductoras | `PENDIENTE` | `PENDIENTE` | no | **`PENDIENTE`** |
| `P-04` Reproductoras — Huevo fértil | `CERTIFIED` | Reproductoras → Incubadora | `PENDIENTE` | `PENDIENTE` | **sí** · flujo 2 | **`PENDIENTE`** |
| `P-05` Incubación | `CERTIFIED` | Incubadora | `PENDIENTE` | `PENDIENTE` | **sí** · flujos 2 y 3 | **`PENDIENTE`** |
| `P-06` Pollo de engorde | `CERTIFIED` | Engorde | `PENDIENTE` | `PENDIENTE` | **sí** · flujo 3 | **`PENDIENTE`** |
| `P-07` Revisión → Aprobación | `CERTIFIED` | las cuatro | `PENDIENTE` | `PENDIENTE` | **sí** · flujo 6 | **`PENDIENTE`** |
| `P-08` Consolidación SAP | `PARTIAL` `BLOCKED_EXTERNAL` | las cuatro | `PENDIENTE` | `PENDIENTE` | **sí** · flujo 5 | **`PENDIENTE`** |
| `P-09` Auditoría interna | `CERTIFIED` | `CORE` · visibilidad decidida | `PENDIENTE` | `PENDIENTE` | no | **`PENDIENTE`** |
| `P-10` Trazabilidad generacional | `CERTIFIED` | **cruza por diseño** | `PENDIENTE` | `PENDIENTE` | **sí** · flujo 7 | **`PENDIENTE`** |
| `P-11` Activación manual de lotes | `CERTIFIED` | derivable del lote | `PENDIENTE` | `PENDIENTE` | no | **`PENDIENTE`** |
| `P-12` Datos maestros | `CERTIFIED` | **mixta** · 22 maestros | `PENDIENTE` | `PENDIENTE` | no | **`PENDIENTE`** |
| `P-13` Usuarios y roles | `CERTIFIED` | **`CORE`** · plano de control | n/a | n/a | no | **`PENDIENTE`** |
| `P-14` Notificaciones | `CERTIFIED` | operativo vs control | `PENDIENTE` | `PENDIENTE` | **sí** | **`PENDIENTE`** |
| `P-15` Reportes y KPI | `CERTIFIED` | las cuatro, **agregadas** | `PENDIENTE` | `PENDIENTE` | **sí** | **`PENDIENTE`** |

```
CERTIFICACIÓN DE ACCESO POR UNIDAD     0 / 15
PASS sobre capacidad inexistente       0        y así debe seguir hasta la fase 11
```

## 4. Qué tendrá que demostrar cada fila

Los cinco casos de `GA-REM-040 §18`:

```
CASO 1   unidad ON · concesión ON · permiso ON      →  el proceso funciona
CASO 2   unidad OFF · concesión histórica ON        →  DENEGAR
CASO 3   unidad ON · sin concesión · permiso ON     →  DENEGAR
CASO 4   otra empresa                                →  DENEGAR
CASO 5   traspaso entre unidades                     →  solo dato de contrato
```

Y en toda denegación, **cero efecto lateral**: sin mutación en base, sin movimiento de
inventario, sin cambio de saldo, sin transición de flujo, sin notificación con efecto, sin envío
a SAP y sin asiento de auditoría de éxito. Denegar después de haber escrito no es denegar.

## 5. Las columnas que faltan a propósito

No hay columna de «prueba que lo demuestra» ni de «mutación que la hace fallar» **todavía**: se
añaden cuando existan, no antes. Escribir el nombre de una prueba que no existe convierte esta
matriz en una promesa en lugar de un registro.

Cuando se rellenen, la de la mutación es la que impide que un `PASS` signifique «no lo probamos».

## 6. Tres filas que merecen atención anticipada

**`P-10`** cruza las cuatro unidades **por diseño**. Su certificación de acceso tendrá que
demostrar las dos cosas a la vez: que la cadena generacional se sigue reconstruyendo entera, y
que el interior de cada eslabón no se abre.

**`P-14`** es donde esta capacidad podría romper algo ya certificado. `OD-08` exige que
administración y contraloría reciban avisos de toda la empresa; filtrar esos avisos por concesión
de unidad los haría incumplir en silencio. `OD-09.a` lo resuelve, y esta fila debe probarlo.

**`P-13`** es plano de control y no se filtra por unidad. Su certificación de acceso consiste en
demostrar justamente eso: que administrar el acceso **no concede** acceso al dato.
