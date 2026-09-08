# `RQ-03` · CIERRE DEL AISLAMIENTO DE INQUILINO

`AC05` · `OD-13` · `OD-14` · 2026-09-08

```
RQ-03  =  COMPLETE
```

Recalculado sobre el universo de `Base.metadata`, recurso a recurso. **No** por haber cerrado
`R-121` y `R-126`: cerrarlos no certifica «todas las consultas», y eso sería transitividad.

---

## 1. El universo, y qué le pasa a cada clase

| Clase | Recursos | Cómo se cumple `RQ-03` |
|---|--:|---|
| `TENANT` directo | 20 | predicado `company_id` en la consulta, antes de paginar |
| `TENANT` derivado | 18 | por el padre — `AC12` |
| `SAP` · inquilino | 4 | `company_id` propio; la excepción de **unidad** es `OD-12`, no de empresa |
| `CONTROL` de inquilino | 7 | `users`, `roles` de inquilino, `companies` (por su `id`), habilitaciones, concesiones, `audit_logs`, `approval_steps` |
| `CONTROL` derivado | 1 | `permissions`, vía `roles` |
| `TRASPASO` | 2 | los dos lados pertenecen a la misma empresa — `OD-10` |
| `CONTROL_GLOBAL` | 2 | **excepción normativa explícita**: `business_units`, `productive_phases` |
| **TOTAL** | **54** | **0 sin clasificar · 0 huecos** |

## 2. Las excepciones, nombradas y justificadas

`RQ-03` dice «en todas las consultas **aplicables**». Tres cosas no lo son, y consta por qué:

```
permissions            capacidad de producto, no dato de empresa            `OD-13.a`
roles `company_id NULL`  plantilla de producto, compartida por diseño        `OD-13.b`
companies (para la
autoridad global)      catálogo de control global — `docs/02 §3.1.4`        `OD-14.c`
business_units ·
productive_phases      catálogo de plataforma, sin dueño de inquilino       clasificación
```

Ninguna es «no llegamos a mirarlo». Las cinco están escritas en una decisión de propietario y
tienen prueba que las sostiene.

## 3. Lo que hizo falta para llegar aquí

| Hallazgo | Recurso | Cerrado por |
|---|---|---|
| `R-114` `R-117` `R-118` | `users` | `GA-REM-002` enmienda B |
| `R-115` | `companies` | clave de inquilino por identidad |
| `R-116` | todos los maestros | `fail-closed` sin empresa efectiva |
| `R-121` | `roles` · `permissions` | `OD-13` |
| `R-126` | la semántica del actor global | `OD-14` |

## 4. Por qué esto no se pudo declarar antes

```
`AC05` CORRECTA  +  LISTA DE APLICACIÓN INCOMPLETA  =  SEGURIDAD INCOMPLETA
```

La `AC` estaba escrita desde el primer día. Lo que faltaba era el universo, y el universo se
construía **desde el modelo operativo**: lotes, eventos, granjas. Toda la administración quedó
fuera, y con ella cuatro `P0` en `users`, uno en `companies` y dos decisiones sin tomar.

Ahora el inventario se deriva de `Base.metadata` con un paso que **falla ruidosamente** si
aparece una tabla que no encaja. Repetirlo tras cada migración es lo que impide que el universo
vuelva a quedarse corto — y es la única parte de este cierre que hay que mantener viva.

## 5. Sensibilidad acumulada del aislamiento

```
`/users`        9 mutaciones · 9 detectadas · 2 rehechas por inválidas
maestros        7 mutaciones · 7 detectadas · 1 rehecha por inválida
roles           5 mutaciones · 5 detectadas
`OD-14`         6 mutaciones · 6 detectadas · 2 rehechas (1 no instalada, 1 fuera de camino)
                ────────────────────────────────────────────────────────
                27 mutaciones · 27 detectadas · 5 corregidas antes de contarlas
```

Las cinco correcciones importan más que el 27: una mutación que no se instala, que no ejecuta la
rama, o que no llega a quitar la propiedad, **no prueba nada**, y contarla habría inflado la
cobertura exactamente igual que una lista de recursos incompleta la inflaba antes.

## 6. Lo que sigue abierto, y no lo bloquea

```
R-127   `/masters/companies` da 500 con `sap_config` poblado   ·  P1  ·  no es de inquilino
R-119   el frontend no comprueba permisos en 27 de 28 pantallas ·  P2  ·  el backend sí
R-120   generalizar los cinco estados al resto de pantallas     ·  P2
R-112   ocho rutas SAP sin `response_model`                     ·  P2
```

Ninguno es un hueco de aislamiento. Se enumeran para que `COMPLETE` no se lea como «no queda
nada».
