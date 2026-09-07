# CATÁLOGO REAL DE MÓDULOS

Auditoría del 2026-09-07 · **solo lectura** · ninguna decisión ni `ID` asignados todavía

---

## 1. La colisión de vocabulario que hay que deshacer primero

El sistema ya usa la palabra «módulo», y **no significa lo que el propietario pide**:

```
MÓDULO RBAC        approvals · audit · corrections · dashboard · lots · masters
(funcional)        operations · reports · review · sap · users
                   → qué PARTE DEL SOFTWARE puede tocar un usuario

UNIDAD DE NEGOCIO  Progenitoras · Reproductoras · Incubadora · Engorde
(lo que se pide)   → qué CADENA PRODUCTIVA puede ver
```

Son ejes ortogonales. Un usuario puede tener `operations:create` (módulo funcional) y aun así
no deber ver las operaciones de Incubadora (unidad de negocio). Confundirlos al implementar
sería el error más caro de esta capacidad, y por eso el catálogo se nombra aquí de forma
distinta: **unidad de negocio**, no «módulo».

## 2. Las cuatro unidades sí existen, con otro nombre

| Owner term | Representación real | Evidencia |
|---|---|---|
| Progenitoras | `BirdTypeEnum.GRANDPARENT` | `app/masters/models.py` · `processCatalog.ts` (24 usos) |
| Reproductora | `BirdTypeEnum.BREEDER` | ídem · 19 usos |
| Incubadora | `BirdTypeEnum.HATCHERY` | ídem · 18 usos |
| Pollo de Engorde | `BirdTypeEnum.BROILER` | ídem · 9 usos |

```
Progenitoras ....... FOUND, como `grandparent`
Reproductora ....... FOUND, como `breeder`
Incubadora ......... FOUND, como `hatchery`
Pollo de Engorde ... FOUND, como `broiler`
```

Pero `BirdTypeEnum` **no es un catálogo de producto**: es un atributo de un lote y de una raza.
No hay tabla, no es administrable, y nada lo relaciona con una empresa ni con un usuario.

## 3. La matriz

| Module/Capability | Code/Route/Entity Evidence | Classification | Toggleable? | Core? | Notes |
|---|---|---|:--:|:--:|---|
| **Progenitoras** | `BirdTypeEnum.GRANDPARENT` · `/poultry/grandparent/:phase` · `P-01`, `P-02` | BUSINESS MODULE | **no** | no | solo como valor de enum |
| **Reproductoras** | `BirdTypeEnum.BREEDER` · `/poultry/breeder/:phase` · `P-03`, `P-04` | BUSINESS MODULE | **no** | no | ídem |
| **Incubadora** | `BirdTypeEnum.HATCHERY` · `/poultry/hatchery/:phase` · `P-05` | BUSINESS MODULE | **no** | no | ídem |
| **Engorde** | `BirdTypeEnum.BROILER` · `/poultry/broiler/:phase` · `P-06` | BUSINESS MODULE | **no** | no | ídem |
| Autenticación y sesión | `app/auth` · `/login`, `/refresh`, `/me` | CORE | no | **sí** | sin ella no hay sistema |
| Usuarios y roles | `app/auth` · `users`, `roles` · `P-13` | CORE | no | **sí** | administra el acceso |
| Empresas | `masters/companies` | CORE | no | **sí** | es el inquilino |
| Datos maestros | `app/masters` · 22 maestros · `P-12` | SHARED BUSINESS CAPABILITY | no | parcial | ver `MASTER_DATA_MODULE_MATRIX.md` |
| Auditoría | `app/audit` · `P-09` | CORE | no | **sí** | inmutable, transversal |
| Revisión y aprobación | `app/review` · `P-07` | MULTI-MODULE PROCESS | no | no | atraviesa las cuatro unidades |
| Consolidación SAP | `app/integrations/sap` · `P-08` | MULTI-MODULE PROCESS | quizá | no | `BLOCKED_EXTERNAL` |
| Reportes y KPI | `app/reports` · `P-15` | SHARED BUSINESS CAPABILITY | no | no | agrega sobre las cuatro |
| Notificaciones | `app/notifications` · `P-14` | CORE | no | **sí** | canal, no unidad |
| Trazabilidad generacional | `egg_batches`, `chick_batches` · `P-10` | MULTI-MODULE PROCESS | no | no | **cruza unidades por diseño** |
| Áreas funcionales | `areas` · `GA-REM-039` | CORE | no | **sí** | organigrama, ver `MODULE_AREA_RELATIONSHIP_MATRIX.md` |

## 4. Recuento

```
Unidades de negocio identificadas .... 4     ninguna administrable
Capacidades CORE ..................... 6
Capacidades compartidas .............. 2
Procesos multi-unidad ................ 3
Sin clasificar ....................... 0
```

## 5. Lo que NO existe

```
tabla de catálogo de módulos ......... NO
módulo habilitado por empresa ........ NO
módulo concedido a usuario ........... NO
código estable de módulo ............. NO   (solo el enum, que no es un catálogo)
```

`BirdTypeEnum` es un **enum de dominio en el código**, no un dato configurable. Convertirlo en
catálogo administrable es parte de lo que la futura spec tendría que decidir; esta auditoría no
propone códigos finales todavía, porque hacerlo antes de resolver la colisión de vocabulario
fijaría el error en el esquema.
