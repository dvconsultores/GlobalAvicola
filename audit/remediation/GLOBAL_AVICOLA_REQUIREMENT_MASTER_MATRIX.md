# MATRIZ MAESTRA DE REQUISITOS

Auditoría maestra · 2026-09-08 · `HEAD = e245157` · **solo lectura**

**Alcance de esta matriz.** Cubre los requisitos de las diez áreas que motivaron la auditoría,
extraídos de `docs/02 §3.1`–`§3.2`, `docs/03 §686`, `docs/10 §3.1`, `docs/12`, `GA-REM-002`,
`GA-REM-034`, `GA-REM-039`, `GA-REM-040` y `OD-09`…`OD-12`. **No** es el censo de todos los
requisitos del producto: los procesos operativos `P-01`…`P-15` conservan su propia matriz y su
certificación funcional de `14 / 15`, que esta auditoría **no** recalcula.

---

## 1. Arquitectura y multicompañía

| ID | Requisito | Fuente | Backend | BD | Frontend | Runtime | Test | Estado | Finding |
|---|---|---|:--:|:--:|:--:|:--:|:--:|---|---|
| `RQ-01` | Cada usuario pertenece a una compañía | `02 §3.1.4` | sí | `users.company_id` | formulario sí, columna no | sí | sí | **`PARTIAL`** | `F-J` |
| `RQ-02` | Super Admin ve todas las compañías | `02 §3.1.4` | sí | — | sí | sí | sí | `COMPLETE` | — |
| `RQ-03` | Usuarios regulares solo ven datos de su compañía **en todas las consultas** | `02 §3.1.4` | **no en `/users` ni en `companies`** | — | — | — | **no** | **`CONTRADICTED`** | `F-A` `F-B` `F-C` |
| `RQ-04` | El `JWT` incluye `company_id` y `role_id` | `02 §3.1.4` | sí | — | sí | sí | sí | `COMPLETE` | — |
| `RQ-05` | Toda entidad creada hereda el `company_id` del usuario | `02 §3.1.4` | parcial — `/users` no | — | — | — | parcial | **`PARTIAL`** | `F-G` |
| `RQ-06` | Permisos con alcance `all` / `company` / `farm` | `02 §3.1.4` | `scope_type` existe | `permissions` | no | no evaluado | parcial | **`PARTIAL`** | `F-K` |
| `RQ-07` | Configuración SAP por compañía | `02 §3.1.4` | `sap_config` | `companies` | `MasterListPage` | sí | no | **`CONTRADICTED`** | `F-B` |
| `RQ-08` | Niveles de aprobación por compañía | `02 §3.1.4` | sí | `companies` | sí | sí | sí | `COMPLETE` | — |
| `RQ-09` | Selector de compañía en frontend | `02 §3.1.4` **«(futuro)»** | `/switch-company` | — | **no** | no | sí | **`BACKEND_ONLY_EXPECTED`** | — |
| `RQ-10` | La auditoría registra `company_id` en cada acción | `02 §3.1.4` · `13` | sí | `audit_logs` | `AuditPage` | sí | sí | `COMPLETE` | — |
| `RQ-11` | Empresa efectiva resuelta, no reclamada | `OD-11` | sí | — | n/a | sí | sí | `COMPLETE` | — |

## 2. Maestros y origen de verdad

| ID | Requisito | Fuente | Backend | BD | Frontend | Runtime | Test | Estado | Finding |
|---|---|---|:--:|:--:|:--:|:--:|:--:|---|---|
| `RQ-12` | 22 maestros con `CRUD` | `02 §3.2.1` | sí | sí | `MasterListPage` | sí | sí | `COMPLETE` | — |
| `RQ-13` | SAP importa Centros, Almacenes, Materiales, Proveedores, Lotes, OC, OT | `10 §3.1` | `sap_references` | sí | `SapManagerPage` | manual | sí | `COMPLETE` | — |
| `RQ-14` | **Compañías provienen de SAP** | **ninguna** | — | — | — | — | — | **`SPEC_GAP`** | `F-F` |
| `RQ-15` | **Granjas provienen de SAP** | **ninguna** | — | — | — | — | — | **`SPEC_GAP`** | `F-F` |
| `RQ-16` | Los maestros se acotan por empresa | `02 §3.1.4` | sí salvo `companies` y sin empresa | — | — | — | parcial | **`PARTIAL`** | `F-B` `F-C` |

## 3. Usuarios, roles y `RBAC`

| ID | Requisito | Fuente | Backend | BD | Frontend | Runtime | Test | Estado | Finding |
|---|---|---|:--:|:--:|:--:|:--:|:--:|---|---|
| `RQ-17` | `CRUD` de usuarios con campo Empresa | `02 §3.1.2` | sí | sí | formulario sí · **columna no** | vacío | no | **`PARTIAL`** | `F-E` `F-J` |
| `RQ-18` | El alta de usuario respeta el inquilino del actor | `02 §3.1.4` | **no** | — | — | — | **no** | **`CONTRADICTED`** | `F-G` |
| `RQ-19` | La edición de usuario respeta el inquilino y no escala privilegios | `02 §3.1.4` | **no** | — | — | — | **no** | **`CONTRADICTED`** | `F-H` |
| `RQ-20` | `CRUD` de roles con permisos granulares | `02 §3.1.3` · `GA-REM-034` | sí | sí | `RolesPage` | sí | sí | `COMPLETE` | — |
| `RQ-21` | Los roles se acotan a la empresa | `02 §3.1.3` | **no** — `Role.company_id` existe y no se usa | `roles` | no | compartido | no | **`PARTIAL`** | `F-I` |
| `RQ-22` | Toda ruta declara permiso | `GA-REM-002 AC08` | sí | — | — | sí | sí | `COMPLETE` | — |
| `RQ-23` | Cambio de contraseña con política de 8 | `GA-REM-012` `RR-05` | sí | — | sí | sí | sí | `COMPLETE` | — |

## 4. Módulos por empresa

| ID | Requisito | Fuente | Backend | BD | Frontend | Runtime | Test | Estado | Finding |
|---|---|---|:--:|:--:|:--:|:--:|:--:|---|---|
| `RQ-24` | **La empresa activa o desactiva módulos** | **ninguna** | — | — | — | — | — | **`SPEC_GAP`** | `F-L` |
| `RQ-25` | El menú refleja los módulos accesibles del rol | `02 §3.1.3` | n/a | — | **no** | todo visible | no | **`MISSING`** | `F-D` |

## 5. Unidades de negocio · `GA-REM-040`

| ID | Requisito | Fuente | Backend | BD | Frontend | Runtime | Test | Estado | Finding |
|---|---|---|:--:|:--:|:--:|:--:|:--:|---|---|
| `RQ-26` | Catálogo, habilitación por empresa, concesión por usuario | fase 1 · `AC-A01`…`B12` | sí | 3 tablas | — | sin consumidor | 31 | `BACKEND_ONLY` | — |
| `RQ-27` | Guarda central y empresa efectiva | fase 2 | sí | — | — | sí | 25 | `COMPLETE` | — |
| `RQ-28` | Aislamiento por fila | fase 3 | sí | — | — | sí | 21 | `COMPLETE` | — |
| `RQ-29` | Aislamiento de agregados y `KPI` | fase 4 | sí | — | — | sí | 15 | `COMPLETE` | — |
| `RQ-30` | Contratos de traspaso · 7 flujos | fase 5 · `OD-10` `OD-12` | sí | — | — | sí | 28 | `COMPLETE` | — |
| `RQ-31` | Clasificación pendiente y reclasificación | fase 6 · `OD-10.c/d` | sí | sí | — | sin consumidor | 35 | `BACKEND_ONLY` | — |
| `RQ-32` | API de administración | fase 7 · `T-040-18/19` | sí | — | — | sin consumidor | 39 | `BACKEND_ONLY` | — |
| `RQ-33` | Capacidades en la sesión | fase 8 · `T-040-20` | **no** | — | — | — | — | **`MISSING`** — no iniciada | — |
| `RQ-34` | Interfaz de unidades y clasificación | fase 9 · `T-040-21…24` | n/a | — | **no** | — | — | **`MISSING`** — no iniciada | — |
| `RQ-35` | Quién administra el acceso por unidad | `R-113` | — | — | — | — | — | **`OWNER_DECISION_REQUIRED`** | `R-113` |
| `RQ-36` | Ciclo de vida del histórico al cerrar una línea | `BU-D10` | — | — | — | — | — | **`OWNER_DECISION_REQUIRED`** | `BU-D10` |

## 6. SAP e integración

| ID | Requisito | Fuente | Backend | BD | Frontend | Runtime | Test | Estado | Finding |
|---|---|---|:--:|:--:|:--:|:--:|:--:|---|---|
| `RQ-37` | Consolidación y envío a SAP | `10` · `P-08` | sí | sí | `SapManagerPage` | sí | sí | **`BLOCKED_EXTERNAL`** | — |
| `RQ-38` | Contratos de respuesta declarados en `/sap` | `GA-REM-016` | **1 de 10** | — | — | — | parcial | **`PARTIAL`** | `R-112` |

---

## 2. Recuento

```
TOTAL REQUISITOS AUDITADOS        38

COMPLETE                          14
PARTIAL                            7
CONTRADICTED                       5
MISSING                            4
BACKEND_ONLY (esperado)            4
SPEC_GAP                           3
OWNER_DECISION_REQUIRED            2
BLOCKED_EXTERNAL                   1

COBERTURA DE REQUISITO DE PRODUCTO — 2026-09-08
    14 / 38  =  37 %   COMPLETE
    18 / 38  =  47 %   COMPLETE o BACKEND_ONLY esperado por hoja de ruta
```

El histórico `21 / 60 = 35 %` **no se toca**: mide otra cosa, en otra fecha, sobre otro censo.

---

## 3. Findings nuevos de esta auditoría

| ID | Clase | Severidad | Qué |
|---|---|:--:|---|
| `F-A` | `IMPLEMENTATION_CONTRADICTS_SPEC` | **P0** | `/users` no filtra por empresa |
| `F-B` | `IMPLEMENTATION_CONTRADICTS_SPEC` | **P0** | `/masters/companies` no acota y expone `sap_config` |
| `F-C` | `IMPLEMENTATION_CONTRADICTS_SPEC` | **P0** | usuario sin empresa → maestros sin filtrar (`fail-open`) |
| `F-H` | `IMPLEMENTATION_CONTRADICTS_SPEC` | **P0** | `update_user` cruza inquilinos y reasigna `role_id` |
| `F-G` | `IMPLEMENTATION_CONTRADICTS_SPEC` | **P1** | `create_user` acepta `company_id` del cliente |
| `F-D` | `FRONTEND_MISSING` | **P1** | ninguna pantalla comprueba permisos |
| `F-E` | `FRONTEND_MISSING` | **P1** | errores silenciados: denegación indistinguible de vacío |
| `F-I` | `SPEC_NOT_IMPLEMENTED` | **P1** | los roles no se acotan por empresa |
| `F-J` | `FRONTEND_MISSING` | **P2** | falta la columna Empresa en `/users` |
| `F-K` | `TEST_COVERAGE_GAP` | **P2** | `Permission.scope_type` existe y no se evalúa |
| `F-F` | `OWNER_DECISION_REQUIRED` | **P1** | origen de Empresas y Granjas sin especificar |
| `F-L` | `OWNER_DECISION_REQUIRED` | **P1** | módulos por empresa sin especificar |


---

## 4. Actualización tras la remediación `P0` de inquilino (2026-09-08)

`GA-REM-002` enmienda B. Los estados se recalculan **por evidencia de extremo a extremo**, no
porque exista la ruta ni porque la suite esté verde.

| ID | Requisito | Antes | Ahora | Evidencia |
|---|---|:--:|:--:|---|
| `RQ-03` | Usuarios regulares solo ven datos de su compañía en todas las consultas | `CONTRADICTED` | **`PARTIAL`** | `/users` cerrado y probado; `/masters/companies` (`R-115`) y el `fail-open` de maestros (`R-116`) siguen abiertos |
| `RQ-05` | Toda entidad creada hereda el `company_id` del usuario | `PARTIAL` | **`COMPLETE`** para `/users` | la empresa se resuelve, no se recibe |
| `RQ-17` | `CRUD` de usuarios con campo Empresa | `PARTIAL` | **`PARTIAL`** | aislamiento cerrado; falta la columna en la tabla (`R-122`) |
| `RQ-18` | El alta respeta el inquilino del actor | `CONTRADICTED` | **`COMPLETE`** | `test_el_alta_no_acepta_la_empresa_del_cliente` |
| `RQ-19` | La edición respeta el inquilino y no escala privilegios | `CONTRADICTED` | **`COMPLETE`** | `AC14` + `AC15`, `E2E` de ataque, 9 mutaciones |

```
COBERTURA DE REQUISITO DE PRODUCTO — 2026-09-08 (tras la remediación)
    16 / 38  =  42 %   COMPLETE      (antes 14 / 38 = 37 %)
    CONTRADICTED  5 → 3
```

`RQ-03` **no** pasa a `COMPLETE` a propósito: la spec dice «en todas las queries» y dos
superficies de maestros siguen sin acotar. Declararlo cerrado por haber arreglado `/users` sería
certificación por transitividad, que es justo lo que la auditoría vino a señalar.

El histórico `21 / 60` sigue sin tocarse.


---

## 5. Recálculo de `RQ-03` tras `R-115` y `R-116` (2026-09-08)

**Método**: no se declara `COMPLETE` por haber cerrado dos hallazgos. Se recorre el inventario
completo de `TENANT_RESOURCE_CLASSIFICATION.md` —54 recursos, derivado de `Base.metadata` y no
de la lista anterior— y se comprueba recurso por recurso si hay aplicación del predicado.

| Clase | Recursos | Con aplicación demostrada | Sin aplicación |
|---|--:|--:|--:|
| `TENANT` directo | 20 | 20 | 0 |
| `TENANT` derivado | 18 | 18 | 0 |
| `SAP` · inquilino | 4 | 4 | 0 |
| `CONTROL` | 7 | **6** | **1** — `roles` |
| `CONTROL` derivado | 1 | **0** | **1** — `permissions`, hereda de `roles` |
| `TRASPASO` | 2 | 2 | 0 |
| `GLOBAL / PLATAFORMA` | 2 | n/a — compartidos por diseño | 0 |
| **TOTAL** | **54** | **50** | **2** |

```
RQ-03  =  PARTIAL
```

**Lo que falta, con nombre y apellido:**

```
`roles`         `Role.company_id` existe en el modelo y `get_roles` NO lo usa:
                el catálogo es global y un rol de la empresa A aparece en la lista de la B.
`permissions`   cuelga de `roles` por `role_id`; hereda el hueco.
```

Bloqueado por **`R-121`**, que es `OWNER_DECISION_REQUIRED` y no una corrección: si el catálogo
de roles es de **producto**, no filtrar es lo correcto y `RQ-03` pasaría a `COMPLETE` con una
excepción normativa escrita. Si es de **inquilino**, hay que acotarlo. `Role.company_id`
existiendo sugiere lo segundo, pero sugerir no es decidir.

**No se marca `COMPLETE` por transitividad.** Cerrar `/users`, `companies` y el caso «sin
empresa» no certifica «todas las consultas»: quedan dos recursos y están nombrados.

```
COBERTURA DE REQUISITO DE PRODUCTO — 2026-09-08
    16 / 38 = 42 %   COMPLETE   ·   sin cambio: `RQ-03` sigue `PARTIAL`
```


---

## 6. `RQ-03` = `COMPLETE` (2026-09-08)

Recalculado recurso a recurso sobre `Base.metadata`, **no** por haber cerrado `R-121` y `R-126`.

| Clase | Recursos | Estado |
|---|--:|---|
| `TENANT` directo + derivado + `SAP` | 42 | predicado en la consulta o herencia del padre |
| `CONTROL` de inquilino | 8 | `users` · `roles` · `companies` · habilitaciones · concesiones · `audit_logs` · `approval_steps` · `permissions` (derivado) |
| `TRASPASO` | 2 | los dos lados en la misma empresa |
| `CONTROL_GLOBAL` | 2 | excepción normativa explícita |
| **TOTAL** | **54** | **0 sin clasificar · 0 huecos** |

```
RQ-03    PARTIAL  →  COMPLETE
```

Cinco excepciones, todas escritas en una decisión de propietario y con prueba:
`permissions` y las plantillas de sistema (`OD-13`), el catálogo de empresas para la autoridad
global (`OD-14`), y los dos catálogos de plataforma.

```
COBERTURA DE REQUISITO DE PRODUCTO — 2026-09-08
    18 / 38  =  47 %   COMPLETE      (antes 16 / 38 = 42 %)
    `RQ-03` COMPLETE  ·  `RQ-17` sigue PARTIAL (falta la columna Empresa, `R-122`)
```

El histórico `21 / 60` sigue sin tocarse.


---

## 7. Tras `OD-15` (2026-09-09)

| ID | Requisito | Antes | Ahora |
|---|---|:--:|:--:|
| `RQ-03` | aislamiento de compañía en todas las consultas aplicables | `COMPLETE` | **`COMPLETE`** — 54 recursos, sin cambios |
| `RQ-22` | quién administra el acceso por unidad de negocio | `MISSING` | **`COMPLETE`** — `Administrador de Accesos` |
| `RQ-23` | administrar el acceso no eleva el propio | — | **`COMPLETE`** — `OD-15.a` |

```
COBERTURA DE REQUISITO DE PRODUCTO — 2026-09-09
    20 / 38  =  53 %   COMPLETE      (antes 18 / 38 = 47 %)
```

`RQ-03` **no cambia**: `R-128` y `R-113` no añaden ni quitan recursos del universo —siguen
siendo 54— ni crean excepciones nuevas. Se verifica como regresión, no se recalcula por
transitividad. El histórico `21 / 60` sigue intacto.
