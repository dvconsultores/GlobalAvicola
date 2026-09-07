# `P-14` · MODELO DE ÁREA FUNCIONAL — QUÉ EXISTE Y QUÉ FALTA

`OD-08` · `docs/02 §6.1` · 2026-09-07 · **antes de tocar código**

`OD-08` decide que las notificaciones lleguen también al **gerente del área** y al **supervisor
del área**. El checkpoint anterior lo dejó como `BLOCKED_BY_MODEL_GAP` porque el concepto de
área no existe. Esta matriz mide exactamente cuánto falta, antes de crear nada.

---

## 1. El resultado, por delante

```
No existe NADA del modelo organizacional.
```

Se buscó tabla de área, departamento, unidad, división, equipo y posición: ninguna. Y el
usuario se asocia a **una empresa y un rol**, a nada más:

```
User:  id · company_id · first_name · last_name · email · username · phone
       hashed_password · role_id · view_type · is_active · last_login
       created_at · updated_at

Role:  id · company_id · name · description · is_active · created_at
```

Ni los roles identifican el área ni el usuario la tiene asignada. Es el **`CASE C`**.

## 2. La matriz

| Capability | Existing | Correct | Gap | Action |
|---|:--:|:--:|---|---|
| Area master | **NO** | — | falta entero | crear `areas`, con el patrón de `GA-REM-033` |
| Company → Area | **NO** | — | falta | `areas.company_id`, como los otros 21 maestros |
| User → Area | **NO** | — | falta | `users.area_id`, nulable |
| Area manager | **NO** | — | ni rol de gerencia ni relación | rol con nombre de gerencia **+** `area_id` — ver §4 |
| Area supervisors | parcial | sí | existe `Supervisor Avícola`; falta el área | mismo criterio |
| Area CRUD | **NO** | — | falta | `register_crud`, como los 21 existentes |
| Tenant isolation | parcial | sí | el patrón existe (`MasterService._apply_company_filter`) | se hereda, no se reinventa |
| Event → Area resolution | **NO** | — | ningún evento sabe de qué área es | `lots.area_id` — ver §5 |

## 3. Rol y área no son lo mismo

```
Role   qué PUEDE hacer el usuario
Area   dónde funcionalmente PERTENECE
```

Un `Supervisor Avícola` puede supervisar; el área dice **qué** supervisa. Usar `role.name` como
sustituto de `area_id` habría metido las dos cosas en un campo, y el día que existan dos
supervisores de áreas distintas los dos recibirían todo.

## 4. Cómo se resuelve el gerente, sin duplicar la verdad

Dos diseños posibles, y solo uno deja una única fuente:

| Diseño | Problema |
|---|---|
| `Area.manager_user_id` **y** usuarios con rol de gerencia y `area_id` | dos fuentes que pueden discrepar: el campo dice A, el rol dice B, y no hay regla de autoridad |
| **`User.area_id` + rol** | una sola fuente: la pertenencia está en el usuario y la capacidad en su rol |

Se elige el segundo:

```
GERENTE DEL ÁREA    = usuario activo · misma empresa · misma área · rol de gerencia
SUPERVISOR DEL ÁREA = usuarios activos · misma empresa · misma área · rol de supervisión
```

**La relación con el área es explícita** —`user.area_id`—, que es lo que `§10` del encargo
exige. Lo que aporta el nombre del rol es la **capacidad**, no el área: sin `area_id` un usuario
con rol de gerencia no es gerente de ninguna área y no recibe nada por ese concepto.

### El rol de gerencia no existe todavía

`docs/02 §6.1` enumera once roles y ninguno es de gerencia. Tampoco se crea aquí: `GA-REM-034`
dio administración de roles, de modo que una empresa que necesite un gerente lo crea como dato.
El resolutor lo reconoce por el nombre —igual que ya hace con administración, contraloría y
supervisión— y si no existe, **no se avisa a nadie por ese concepto y nada falla**.

Hardcodearlo en una migración sería inventar catálogo, que es lo que `§33` prohíbe.

## 5. De dónde saca su área un evento

`§19` prohíbe la correspondencia inventada —«si es mortalidad, área Producción»—: tiene que
salir del dato. Se auditaron las entidades de origen de los seis eventos:

| Evento | Entidad de origen | Camino al área |
|---|---|---|
| Registro pendiente > 24h | `OperationalEvent` | → `lot_id` |
| Registro rechazado | `OperationalEvent` | → `lot_id` |
| Mortalidad > umbral | `OperationalEvent` | → `lot_id` |
| Peso fuera de estándar | `OperationalEvent` | → `lot_id` |
| Error de envío SAP | `SapPayload` → `ConsolidatedMovement` | → `lot_id` |
| Lote próximo a cierre | `Lot` | directo |

Los seis convergen en el **lote**. No hay contexto organizacional previo que reutilizar —`Farm`
no tiene área—, de modo que el vínculo mínimo va donde todos lo alcanzan:

```
lots.area_id     nulable, FK a areas
```

Una columna, no una por tabla. `§22`: debe existir una fuente única y coherente.

**Un evento sin lote** —las inspecciones de granja tienen `lot_id` nulo desde `i9j0k1l2m3n4`—
no resuelve área. No es un error: se avisa a quien cargó el dato, a los administradores y a la
contraloría, y no al gerente ni al supervisor, porque no hay área que los identifique.

## 6. Lo que NO se modela

`§24` es explícito y conviene repetirlo: solo `Area`.

```
Department · Division · BusinessUnit · CostCenter · Region · Team
```

Ninguno. Ni jerarquía de áreas, ni áreas dentro de áreas, ni áreas globales compartidas entre
empresas. El área pertenece a una empresa, como los otros veintiún maestros.

## 7. Lo heredado que no se reinventa

| Pieza | De dónde |
|---|---|
| Filtro de tenencia en maestros | `MasterService._apply_company_filter` |
| `CRUD` parametrizado y `X-Total-Count` | `register_crud` · `GA-REM-033` / `R-89` |
| Baja lógica en vez de borrado | `is_active`, patrón de los 21 maestros |
| Pantalla de maestros | `MasterListPage`, con su entrada en `masterEntities` |
| Administración de usuarios | `UsersPage`, que ya edita rol y empresa |

## 8. Resumen

```
Existing Area model ............ NO
Existing user-area relation .... NO
Existing area-manager ......... NO
Existing supervisor resolution . parcial (rol sí, área no)
```

Todo lo que falta es **una tabla, dos columnas y un resolutor**. El resto se hereda de patrones
ya certificados.
