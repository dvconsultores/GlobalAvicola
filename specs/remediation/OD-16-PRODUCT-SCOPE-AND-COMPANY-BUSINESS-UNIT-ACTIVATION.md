# `OD-16` · ALCANCE PRODUCTIVO VIGENTE Y ACTIVACIÓN DE UNIDADES DE NEGOCIO POR EMPRESA

Decisión de propietario · **requisito de producto aprobado** · 2026-09-09 · **VIGENTE**
Origen: instrucción expresa del propietario (tanda post-Master-360, «WAVE A0-P»). No es una
pregunta provisional: es una declaración. Precisa `GA-REM-040 §2` y `§5`, `OD-09` y `OD-15`; no
los sustituye.

```
CUATRO UNIDADES PRODUCTIVAS, SIEMPRE EN EL PRODUCTO
CADA RAZÓN SOCIAL ENCIENDE O APAGA CADA UNA, EN GLOBAL AVÍCOLA
ENCENDER  ≠  CONCEDER
```

---

## 1. `OD-16.a` · las cuatro unidades productivas soportadas

| Unidad productiva | Código canónico | `BusinessUnit.code` (catálogo, `baseline_seeds.UNIDADES_DE_NEGOCIO`) | `BirdTypeEnum` (clasificación de dominio) |
|---|---|---|---|
| **Progenitoras** | `grandparent` | `grandparent` | `grandparent` |
| **Reproductoras** | `breeder` | `breeder` | `breeder` |
| **Incubadora** | `hatchery` | `hatchery` | `hatchery` |
| **Pollo de engorde** | `broiler` | `broiler` | `broiler` |

```
SUPPORTED PRODUCTIVE BUSINESS UNITS = 4
```

- Las cuatro **existen en el producto** como catálogo de plataforma (`business_units`, `AC-A01`), con código estable. No hay quinta unidad productiva; la clasificación pendiente (`OD-10.c`) no es una unidad.
- Las cuatro deben permanecer **listas para producto**: definidas (`spec.md §4.4–§4.8`), implementables, disponibles, configurables por empresa, cubiertas por seguridad, requisitos, procesos, KPI aplicables, interfaz futura y certificación. **Progenitoras no es** una extensión futura, una opción, un alias informal de Reproductoras ni un «no aplica».
- No se aceptan variantes de nombre (`grandparents`, `parent_stock`, `incubator`, `growout`) salvo normalización explícita a la tabla anterior.
- `BirdTypeEnum` sigue siendo clasificación de dominio y no control de acceso (`GA-REM-040 §2`). La coincidencia de códigos es deliberada; la separación conceptual se conserva.

## 2. `OD-16.b` · cada empresa activa o desactiva cada unidad, independientemente

```
Empresa A   grandparent ON   breeder ON   hatchery ON    broiler ON
Empresa B   grandparent OFF  breeder ON   hatchery OFF   broiler ON
Empresa C   grandparent OFF  breeder OFF  hatchery OFF   broiler ON
```

- Toda combinación es representable (`company_business_units(company_id, business_unit_id, is_enabled)`, única por par, `AC-A02`, `AC-A03`). No existe ninguna unidad obligatoria ni ninguna «siempre encendida».
- La activación es **configuración del plano de control de Global Avícola** (`OD-09.b`): pertenece a la aplicación aunque la empresa, como entidad oficial, sea de SAP.
- Estado por omisión: **una empresa sin fila para una unidad no la tiene habilitada** (`GA-REM-040 §7.4` «lo desconocido deniega»; `business_units/service.unidades_habilitadas`). Cómo se configura en el alta del primer cliente real es `BU-D05` (`FIRST_REAL_CUSTOMER_READINESS`), pendiente y distinta de esta decisión.

## 3. `OD-16.c` · empresa SAP ≠ configuración de unidades

```
SAP Company (Sociedad)      entidad empresarial oficial · maestro ERP
CompanyBusinessUnit          qué unidades productivas opera esa empresa EN GLOBAL AVÍCOLA
```

- SAP crea y mantiene la entidad empresarial oficial (Recomendación central §1, §4). Global Avícola no la modifica al configurar unidades.
- Una futura sincronización de empresas desde SAP **podrá crear o actualizar el maestro de empresa** y **no determinará** qué unidades están activas ni concederá acceso a nadie. La activación sigue siendo decisión de configuración del negocio dentro de la aplicación.
- Que hoy `companies` represente a la vez la entidad SAP y el inquilino de seguridad es `R-124` / `AOD-06` (`OWNER_DECISION_REQUIRED`); esta decisión no lo resuelve.

## 4. `OD-16.d` · encender no concede

```
habilitar unidad a la empresa  →  CERO concesiones de usuario creadas
```

- Habilitar `hatchery` no da Incubadora a los administradores, ni a todos los usuarios, ni al Super Administrador al cambiar de empresa (`GA-REM-040 §14.4`, `OD-15 §4`, `test_habilitar_no_concede_la_unidad_a_nadie`).
- La concesión de usuario (`user_business_units`) sigue siendo un acto separado, dentro de lo habilitado por la empresa efectiva (`AC-B02`), con segregación (`OD-15`).
- El `RBAC` sigue siendo un tercer plano separado (`AC-B06`): unidad concedida sin permiso no opera; permiso sin unidad tampoco.

## 5. `OD-16.e` · apagar prevalece sobre la concesión

```
CompanyBusinessUnit.is_enabled = false  →  acceso efectivo del usuario = ninguno
                                            aunque exista user_business_units
```

- Regla vigente y certificada (`AC-A05`, `GA-REM-040 §4.2`, `unidades_efectivas`). La concesión histórica **no se borra** al apagar (`AC-A04`).
- Qué ocurre con esa concesión al **volver a encender** es `BU-D10`, que queda **separada y pendiente de ratificación** (`PENDING_RATIFICATION`). El comportamiento provisional hoy implementado y certificado es el de `GA-REM-040 §6.3` («rehabilitar → la concesión previa vuelve a ser efectiva», `AC-A06`), fijado por el propietario al autorizar aquella spec y **no** formalizado como `OD`. Esta decisión no lo ratifica ni lo cambia.

## 6. `OD-16.f` · no hay acceso productivo implícito

```
acceso operativo efectivo = misma empresa efectiva
                          AND unidad habilitada para la empresa
                          AND unidad concedida al usuario (viva, de esa empresa)
                          AND permiso RBAC
                          AND pertenencia del recurso
                          AND regla de negocio
```

Cero concesiones → conjunto efectivo vacío, nunca «toda la empresa» (`OD-09.c`, `AC-B04`). Sin retroceso por rol, por nombre de rol, por `is_super_admin` ni por contexto de cambio de empresa (`AC-C14`).

## 7. Quién configura

| Acto | Permiso | Quién lo tiene hoy | Fuente |
|---|---|---|---|
| Ver la configuración de unidades de la empresa | `business_units:read` | Super Administrador (comodín) · **Administrador de Accesos** | `OD-15 §6`, `GA-REM-040` fase 7 |
| Habilitar / deshabilitar | `business_units:update` | ídem | `PATCH /business-units/{code}/enable\|disable` |
| Conceder / revocar a un usuario | `business_units:create` / `business_units:delete` | ídem, con segregación | `OD-15` |

La autoridad es **por permiso**, nunca por nombre de rol. Que habilitar a la empresa sea acto «comercial» de una administración global y conceder sea acto «operativo» del administrador de la empresa (`BU-D07`) sigue **pendiente**: hoy un mismo permiso (`business_units:update`) en la empresa efectiva gobierna la habilitación, y esta decisión no lo altera.

## 8. Lo que esta decisión **no** hace

- No resuelve `BU-D10` (reactivación), `BU-D05` (alta real), `BU-D07` (comercial vs operativo), `BU-D08` (contratado vs habilitado) ni `R-124`/`AOD-06` (origen de la empresa).
- No cambia código, modelo, migración ni prueba: todo lo que declara **ya está implementado** por `GA-REM-040` fases 1, 7 y 8; lo que añade es rango de **requisito de producto vigente**, que antes solo constaba como alcance de una spec de remediación.
- No convierte la existencia de las API en certificación de proceso: la certificación de acceso por unidad sigue `0 / 15` (`PROCESS_BUSINESS_UNIT_ACCESS_MATRIX.md`).

## 9. Trazabilidad

| Cláusula | Ya lo exige | Prueba existente |
|---|---|---|
| `OD-16.a` | `GA-REM-040 AC-A01` · `spec.md §4.4–§4.8` | `test_business_units.py` (catálogo) · `test_ac_c15_toda_ruta_esta_clasificada` |
| `OD-16.b` | `AC-A02`, `AC-A03`, `AC-A07` | `test_ac_a02_*`, `test_ac_a07_*`, `test_habilitar_una_unidad_apagada_la_enciende`, `test_deshabilitar_apaga_la_unidad` |
| `OD-16.c` | `OD-09.b` · Recomendación §1/§4 | — (documental) |
| `OD-16.d` | `GA-REM-040 §14.4` · `OD-15 §4` | `test_habilitar_no_concede_la_unidad_a_nadie` · `test_conceder_no_habilita_la_unidad_para_la_empresa` · `test_ac_c14_*` |
| `OD-16.e` | `AC-A04`, `AC-A05` | `test_deshabilitar_no_borra_las_concesiones_y_rehabilitar_las_devuelve` |
| `OD-16.f` | `OD-09.c` · `AC-B02`, `AC-B04`, `AC-B06` | `test_ac_b04_sin_concesiones_el_conjunto_efectivo_esta_vacio` · `test_ac_b02_*` · `test_el_nombre_del_rol_no_concede_nada` · `test_h11_*` |
| `OD-16.e/f` propagadas a la **escritura productiva** (toda superficie, todo actor, autoridad global incluida) | `GA-REM-040` enmienda G (`operations`, 2026-09-09) · enmienda H (`lots` y descarga de evidencia, 2026-09-09) — **aclaran y propagan**, no sustituyen | `test_operations_bu_enforcement.py` · `test_lots_bu_enforcement.py` |

Enmienda de alcance correspondiente en `specs/global-avicola/spec.md §4.0` (versión 1.1.0).
