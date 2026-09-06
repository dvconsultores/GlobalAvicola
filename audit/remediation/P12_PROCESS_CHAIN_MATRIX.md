# `P-12` · GESTIÓN DE DATOS MAESTROS — CADENA COMPLETA

`docs/02 §3.2` · 2026-09-06

`P-12` se certifica como **proceso**, no como «siete pantallas que abren» (`GA-REM-016 AC05`).

---

| # | Paso | Actor | Entrada | Acción | Salida | Estado |
|:--:|---|---|---|---|---|:--:|
| 1 | Consultar un catálogo | administrador con `masters:read` | — | listar con búsqueda y paginación | página + **total** | **FAIL** — `R-89` |
| 2 | Dar de alta | `masters:create` | campos clave de `§3.2` | `POST` | registro creado y visible al instante | **PASS** 12/19 · **FAIL** 7 |
| 3 | Editar | `masters:update` | cambios | `PUT` | nuevo estado visible | **PASS** 12/19 · **FAIL** 7 |
| 4 | Dar de baja | `masters:delete` | — | baja **lógica** (`is_active = false`) | fuera de las listas activas | **PASS** 12/19 · **FAIL** 7 |
| 5 | Usar el maestro en la operación | operador | catálogo poblado | seleccionarlo al registrar un evento | evento con la referencia | **PASS** por API · **FAIL** cuando el catálogo no puede poblarse |
| 6 | Aislamiento entre empresas | administrador de la empresa A | — | no alcanzar maestros de B | 404 | **PASS** — `GA-REM-002 AC10` |
| 7 | Pertenencia del padre | administrador | `farm_id` · `hatchery_id` ajeno | rechazo | `BR-07` | **PASS** — `R-59` |
| 8 | Permiso obligatorio | sin `masters:*` | — | rechazo | 403 | **PASS** |

```
8 pasos · PASS 4 · FAIL 4 (parcialmente: los 7 maestros sin gestión)
```

## Por qué el paso 5 importa

Certificar que una pantalla abre no basta (`§54`). `cull-causes` es obligatoria al registrar
un descarte y `productive-phases` gobierna la fase de un lote: si el catálogo no puede
poblarse desde el producto, el paso operativo depende de que alguien inserte filas por SQL.

La cadena se cierra cuando **un maestro creado desde la interfaz puede seleccionarse en la
operación que lo exige**.

## Alcance

```
AUTORIZADO   ·  R-89, R-90, R-91 — los tres con backend existente y patrón vigente
FUERA        ·  BirdTypeEnum y EventStatus (system-managed, §3 del catálogo normativo)
             ·  P-13 y P-14
```
