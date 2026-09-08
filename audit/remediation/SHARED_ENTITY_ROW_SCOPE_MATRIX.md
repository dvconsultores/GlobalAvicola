# FILAS COMPARTIDAS: ¿DE QUÉ UNIDAD ES CADA UNA?

Auditoría del 2026-09-07 · **documento crítico** · solo lectura

---

## 1. Por qué este documento es el más importante

Esconder pantallas es fácil. Lo difícil es que una consulta que hoy devuelve «los lotes de la
empresa» pase a devolver «los lotes de la empresa **y de las unidades del usuario**». Para eso
cada fila tiene que saber de qué unidad es — y hoy casi ninguna lo sabe.

## 2. La matriz

| Entity | Rows Can Belong to Multiple Modules? | Current Discriminator | Reliable? | Missing Field? | Leakage Risk |
|---|:--:|---|:--:|:--:|:--:|
| **`lots`** | **sí** | `bird_type` | **no — nulable** | reforzarlo o no confiar | **P0** |
| **`operational_events`** | **sí** | `lot_id → Lot.bird_type` | **no — `lot_id` nulable** | **sí** | **P0** |
| `bird_movements` | sí | vía evento | no | sí | **P0** |
| `egg_movements` | sí | vía evento | no | sí | **P0** |
| `feed_movements` | sí | vía evento | no | sí | **P1** |
| `inspection_details` | sí | vía evento; **el evento puede no tener lote** | **no** | sí | **P1** |
| `hatchery_params` | en la práctica solo Incubadora | vía evento | no | sí | **P1** |
| `operational_alerts` | sí | `lot_id` | parcial | sí | **P1** |
| `notifications` | sí | `related_entity_*` → lote | **no** | sí | **P1** |
| `audit_logs` | sí | `lot_id` nulable | **no** | decisión | **P1** |
| `egg_batches` | **cruzan por diseño** | `generation` | parcial | contrato | **P0** |
| `chick_batches` | **cruzan por diseño** | `generation` | parcial | contrato | **P0** |
| `consolidated_movements` | sí | `lot_id` | parcial | sí | **P1** |
| `approval_actions` | sí | vía evento | no | sí | **P1** |
| `correction_logs` | sí | vía evento | no | sí | **P1** |
| `lot_phases`, `opening_balances` | sí | `lot_id` | sí | no | **P2** |

## 3. Los tres casos sin salida limpia

**Eventos sin lote.** `farm_inspection` y `hatchery_inspection` tienen `lot_id` nulo por
decisión de esquema (`i9j0k1l2m3n4`). No hay forma de derivar su unidad. Las opciones —dejarlos
visibles para todos, ocultarlos a todos, o darles unidad propia— son **decisión de negocio**, no
técnica.

**Lotes sin `bird_type`.** El campo es nulable. Con `fail closed` desaparecerían para todos; con
`fail open` serían un agujero permanente.

**Lotes de huevo y de pollito.** `egg_batches` y `chick_batches` existen **para** cruzar la
frontera: Reproductoras produce el huevo que Incubadora recibe. Filtrarlos por unidad rompería
`P-10`. Aquí no falta un campo: falta un **contrato** que diga qué ve cada lado.

## 4. Lo que esto implica para la implementación futura

```
WHERE company_id = :empresa                       ← lo que hay hoy
WHERE company_id = :empresa
  AND unidad IN :unidades_efectivas_del_usuario   ← lo que haría falta
```

La segunda línea necesita que `unidad` **esté en la fila** o sea alcanzable con un `JOIN`
determinista. Hoy no lo es en catorce de las dieciséis entidades de esta matriz.

Añadir la columna a cada tabla la duplicaría en catorce sitios y abriría la puerta a que se
desincronicen. Derivarla siempre por `JOIN` obliga a que **todas** las consultas pasen por el
lote, incluidas las de los submovimientos. Es la decisión de diseño central de esta capacidad, y
esta auditoría la deja planteada sin resolverla.

---

## 5. Estado real del acotamiento (2026-09-07 · `GA-REM-040` fase 3)

`§4` planteaba la decisión de diseño y la dejaba sin resolver. Se resolvió así: **política por
entidad**, no columna en cada tabla ni `JOIN` obligatorio para todas. `predicado()` devuelve el
acotamiento de la entidad que sabe acotar y `None` para el resto — que **no** es dejarla pasar:
el filtro de empresa y el `RBAC` siguen actuando, y simplemente no se afirma nada sobre su unidad.

| Entidad | Estado | Dónde |
|---|:--:|---|
| `lots` | **`ACOTADA`** | listado, detalle, mutación, total, sub-recursos |
| `lot_phases` | **`ACOTADA`** | vía el lote, en lectura y escritura |
| `opening_balances` | **`ACOTADA`** | vía el lote, incluida la activación manual |
| `operational_events` | `NO ACOTADA` | `lot_id` nulable → **fase 6** |
| `bird_movements` · `egg_movements` · `feed_movements` | `NO ACOTADAS` | heredan del evento → **fase 6** |
| `inspection_details` | `NO ACOTADA` | el evento puede no tener lote → **fase 6** |
| `hatchery_params` | `NO ACOTADA` | **fase 6** |
| `operational_alerts` | `NO ACOTADA` | **fase 4** / **6** |
| `notifications` | `NO ACOTADA` | **fase 10** |
| `audit_logs` | `NO ACOTADA` | decisión `BU-D03` |
| `egg_batches` · `chick_batches` | **`ACCESO CONTRACTUAL`** | fase 5: proyección `B` explícita, origen acotado, destino obligatorio y validado |
| `consolidated_movements` | **`APLAZADA A LA FASE 5`** | contrato del flujo 5 |
| `approval_actions` · `correction_logs` | `NO ACOTADAS` | heredan del evento → **fase 6** |

```
ACOTADAS               3 / 16
APLAZADAS A LA FASE 5  3 / 16      son contratos, no filas de un dueño
PENDIENTES DE LA 6     8 / 16      dependen de que lo no clasificable tenga estado
OTRAS FASES            2 / 16
```

### Los tres bloqueantes de `§3`, revisados

**Lotes sin `bird_type`.** Resuelto por `OD-10.c` en su parte de seguridad: se **deniega**. No se
abre —sería el agujero permanente que `§3` temía— y no se borra. La bandeja donde resolverlos es
la fase 6.

**Eventos sin lote.** Sigue sin salida limpia, y por eso no se acotan todavía: acotarlos hoy los
haría desaparecer para todos, incluida la persona que acaba de registrarlos.

**Lotes de huevo y de pollito.** Confirmado que **no falta un campo, falta un contrato**. No
reciben predicado de propietario único, y no se les añade columna de unidad.

## 6. Estado tras la fase 6 (2026-09-07)

| Entidad | Estado | Cómo |
|---|:--:|---|
| `operational_events` | **`ACOTADA`** | deriva del lote, o se clasifica a mano; lo que no puede, queda pendiente |
| `bird_movements` · `egg_movements` · `feed_movements` | **`ACOTADAS`** | por construcción: sin ruta propia, viajan dentro del evento |
| `inspection_details` · `hatchery_params` | **`ACOTADAS`** | ídem |
| `approval_actions` · `correction_logs` | **`ACOTADAS`** | ídem |
| `lots` con `bird_type` nulo | `DENEGADOS` | completar la cadena es de `P-03`/`P-06`, no de esta capa |
| `notifications` | `NO ACOTADA` | **fase 10** |
| `audit_logs` | `NO ACOTADA` | decisión `BU-D03` |

```
ACOTADAS   13 / 16      eran 3
PENDIENTES  3 / 16      notifications (10) · audit_logs (BU-D03) · lots sin cadena
```

Los tres bloqueantes que `§3` declaró quedan resueltos o acotados: los eventos sin lote tienen
estado, las entidades de traspaso tienen contrato, y los lotes sin cadena siguen denegados con su
hueco registrado en el proceso que sí tiene autoridad sobre `bird_type`.
