# ACTIVACIÓN DE MÓDULOS POR EMPRESA

Auditoría maestra · 2026-09-08 · **solo lectura**

```
VEREDICTO   NO EXISTE EN EL PRODUCTO, Y TAMPOCO EN LA NORMA
```

---

## 1. Lo que se buscó, y no apareció

```
docs/  y  specs/   →   "módulos activados"      0 coincidencias
                       "activar/desactivar módulo"  0
                       "entitlement"            0
                       "licencia" · "suscripción"   0

backend/app/       →   CompanyModule            no existe
                       CompanyModuleAccess      no existe
                       CompanyFeature           no existe
                       Entitlement · License    no existen
```

Lo único que existe con el nombre «módulo» es el **módulo `RBAC`**, que es otra cosa.

---

## 2. Las tres preguntas que hoy se confunden en una

| Pregunta | Quién la contesta hoy | Estado |
|---|---|---|
| ¿Esta **empresa** tiene contratado este módulo? | **nadie** | `MISSING` · sin norma |
| ¿Esta **empresa** opera esta cadena productiva? | `CompanyBusinessUnit` | `COMPLETE` — `GA-REM-040` fase 1 |
| ¿Este **usuario** puede ejecutar esta acción? | `Permission(module, action)` | `COMPLETE` — `GA-REM-002` |

`RBAC` **no sustituye** al entitlement. `Permission.module` dice qué puede hacer una persona;
no dice qué ha contratado una empresa. Hoy dos empresas distintas ven exactamente el mismo
producto, y la única forma de apagarle algo a una es no darle el permiso a ninguno de sus
usuarios — que es una decisión por persona, no por empresa, y que se deshace en cuanto alguien
crea un rol nuevo.

---

## 3. La matriz

| Módulo (`RBAC`) | ¿Habilitación por empresa? | ¿`RBAC` existe? | ¿El menú lo usa? | ¿El backend lo exige? | Runtime |
|---|:--:|:--:|:--:|:--:|---|
| `approvals` | **no** | sí | **no** | sí | visible para todos |
| `audit` | **no** | sí | **no** | sí | visible para todos |
| `business_units` | **no** | sí | **no** | sí | sin pantalla (fase 9) |
| `corrections` | **no** | sí | **no** | sí | visible para todos |
| `dashboard` | **no** | sí | **no** | sí | visible para todos |
| `lots` | **no** | sí | **no** | sí | visible para todos |
| `masters` | **no** | sí | **no** | sí | visible para todos |
| `operations` | **no** | sí | **no** | sí | visible para todos |
| `reports` | **no** | sí | **no** | sí | visible para todos |
| `review` | **no** | sí | **no** | sí | visible para todos |
| `sap` | **no** | sí | **no** | sí | visible para todos |
| `users` | **no** | sí | **no** | sí | visible para todos |

**Doce módulos, cero habilitaciones por empresa, cero puertas en el menú.**

---

## 4. La pila de autorización real, hoy

```
LO QUE EL PROPIETARIO ESPERABA          LO QUE HAY
─────────────────────────────           ──────────────────────────
INQUILINO / EMPRESA                     INQUILINO / EMPRESA        ✓ (con dos fugas · F-A, F-B)
MÓDULO HABILITADO A LA EMPRESA          ── ausente ──
UNIDAD HABILITADA A LA EMPRESA          UNIDAD HABILITADA          ✓
CONCESIÓN DE UNIDAD AL USUARIO          CONCESIÓN AL USUARIO       ✓
PERMISO RBAC                            PERMISO RBAC               ✓
REGLA DE NEGOCIO                        REGLA DE NEGOCIO           ✓
```

Falta **una dimensión completa**, y no por descuido de implementación: nunca se pidió.

---

## 5. Clasificación

```
SPEC_GAP                   el requisito no está escrito en ninguna parte
OWNER_DECISION_REQUIRED    hay que decidir antes de poder especificar
MISSING (como producto)    no existe modelo, ni API, ni UI, ni runtime
NO ES REGRESIÓN            nunca estuvo, nunca se certificó, nada se rompió
```

La decisión previa que hay que tomar no es técnica:

```
¿Global Avícola se vende por módulos contratables?
¿O es un producto único donde el `RBAC` basta para acotar quién hace qué?
```

Si la respuesta es la primera, esto es una `GA-REM` nueva con modelo, migración, guarda de
backend y puerta de menú. Si es la segunda, se cierra como `NOT_REQUIRED_BY_SPEC` y el menú
sigue gobernado por permisos — que hoy tampoco lo está (`F-D`).
