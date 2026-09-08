# RUTAS DE BACKEND FRENTE A UNIDAD DE NEGOCIO

Auditoría del 2026-09-07 · 198 rutas de `/api/v1` · **solo lectura**

---

## 1. Lo que hay hoy, contado

```
rutas de la aplicación .......... 199
rutas de /api/v1 ................ 198

con permiso de módulo RBAC ...... 188
sin sesión (públicas) ...........   2   /login · /refresh
por titularidad .................   8   /me · notificaciones · switch-company · event-types
```

Reparto por módulo **funcional** —que no es unidad de negocio—:

```
masters 106 · reports 14 · operations 13 · review 13 · lots 12 · sap 10
users 9 · approvals 3 · corrections 3 · audit 3 · dashboard 2
```

## 2. El hallazgo, en una línea

```
198 de 198 rutas carecen de guarda por unidad de negocio.
```

Ninguna comprueba `bird_type` ni nada equivalente. La única segmentación vigente es la
**empresa**, y el requisito nuevo es más fino: misma empresa, distinta unidad.

## 3. La matriz, por familia

| Method | Route (familia) | Unidad | Core/Multi | Company Scoped | Current Guard | Module Guard Needed |
|---|---|---|---|:--:|---|:--:|
| `GET/POST/PUT/DELETE` | `/masters/*` (22 maestros, 106 rutas) | mixta | SHARED | **sí** | `masters:*` | **sí, por maestro** |
| `GET` | `/lots` | **derivable** por `bird_type` | BUSINESS | sí | `lots:read` | **SÍ — fuga de listado** |
| `POST` | `/lots` | derivable | BUSINESS | sí | `lots:create` | **sí** |
| `GET/PUT` | `/lots/{id}` | derivable | BUSINESS | sí | `lots:*` | **SÍ — fuga de detalle** |
| `POST` | `/lots/{id}/close` | derivable | BUSINESS | sí | `lots:update` | **sí** |
| `GET` | `/operations` | **solo vía `lot_id`** | BUSINESS | sí | `operations:read` | **SÍ — fuga de listado** |
| `POST` | `/operations` | ídem | BUSINESS | sí | `operations:create` | **sí** |
| `GET` | `/operations/{id}` | ídem | BUSINESS | sí | `operations:read` | **SÍ** |
| `GET` | `/operations/alerts` | ídem | BUSINESS | sí | `operations:read` | **SÍ** |
| `GET/POST` | `/review/*`, `/approvals/*` | multi | MULTI | sí | `review:*`, `approvals:*` | **sí, al listar** |
| `GET` | `/reports/kpis/*` (14) | **agrega las cuatro** | SHARED | sí | `reports:read` | **SÍ — fuga por agregado** |
| `GET` | `/reports/lot/{id}` | derivable | SHARED | sí | `reports:read` | **sí** |
| `GET` | `/dashboard/admin`, `/dashboard/mobile` | **agrega las cuatro** | SHARED | sí | `dashboard:read` | **SÍ — fuga por agregado** |
| `GET/POST` | `/sap/*` (10) | multi | MULTI | sí | `sap:*` | a decidir |
| `GET` | `/audit` | multi | CORE | sí | `audit:read` | **decisión pendiente** |
| `GET/PATCH` | `/notifications*` | derivable vía lote | CORE | sí + titular | titularidad | **sí, al crear** |
| `*` | `/users`, `/roles` | — | CORE | sí | `users:*` | no |
| `POST` | `/login`, `/refresh` | — | CORE | — | público | no |

## 4. Los tres patrones de fuga

**Listado.** `GET /lots` y `GET /operations` filtran por empresa y devuelven **todas** las
unidades. Un usuario de Reproductoras ve los lotes de Incubadora en su propia lista. No hace
falta URL directa ni truco: sale solo.

**Detalle por identificador.** `GET /lots/{id}` comprueba empresa, no unidad. Conociendo o
adivinando un identificador —son secuenciales— se lee cualquier lote de la empresa.

**Agregado.** Los 14 KPI y los 2 paneles suman sobre todo lo de la empresa. Aunque se taparan
los dos anteriores, la mortalidad total seguiría revelando la de Incubadora por diferencia.

## 5. Lo que NO se puede resolver ruta por ruta

Con 198 rutas, copiar una guarda en cada una garantiza que alguna quede fuera — y el olvido es
silencioso, que es exactamente lo que `authorization_coverage.py` vino a impedir para `RBAC`.

La comprobación tiene que vivir donde ya vive la de empresa: en la capa que construye las
consultas. Ver §48 del informe maestro.

## 6. Y hay superficie que no pasa por rutas

`§10` del encargo lo advierte y es cierto aquí: `app/notifications/sla.py` recorre **todas** las
empresas y todos los lotes desde una tarea de fondo, sin sesión de nadie. Ver
`BACKGROUND_JOB_MODULE_MATRIX.md`.

---

## Rutas nuevas · `GA-REM-040` fase 7 (2026-09-08)

Seis superficies de plano de control. Todas `CORE` en la clasificación de módulo —no pertenecen
a ninguna cadena productiva— y `CONTROL` en la clasificación de alcance de unidad.

| Camino | Métodos | Módulo `RBAC` | Alcance de unidad | `response_model` |
|---|---|---|---|:--:|
| `/api/v1/business-units` | `GET` | `business_units:read` | `CONTROL` | sí |
| `/api/v1/business-units/{code}/enable` | `PATCH` | `business_units:update` | `CONTROL` | sí |
| `/api/v1/business-units/{code}/disable` | `PATCH` | `business_units:update` | `CONTROL` | sí |
| `/api/v1/users/{user_id}/business-units` | `GET` | `business_units:read` | `CONTROL` | sí |
| `/api/v1/users/{user_id}/business-units` | `POST` | `business_units:create` | `CONTROL` | sí |
| `/api/v1/users/{user_id}/business-units/{code}` | `DELETE` | `business_units:delete` | `CONTROL` | sí |

```
RUTAS `/api` CLASIFICADAS   207 / 207
SIN PERMISO DECLARADO         0        `authorization_coverage` aborta el arranque
SIN ALCANCE DECLARADO         0        `route_scope` aborta el arranque
FUERA DE TRANSACCIÓN          0        `transaction` aborta el arranque
```

Los tres guardianes de arranque se aplicaron a estas rutas antes que ninguna prueba: el de
transacción las rechazó por no declarar `route_class=RutaTransaccional`, y esa fue la primera
señal de que faltaba la frontera transaccional que hace que conceder y auditar confirmen juntos.
