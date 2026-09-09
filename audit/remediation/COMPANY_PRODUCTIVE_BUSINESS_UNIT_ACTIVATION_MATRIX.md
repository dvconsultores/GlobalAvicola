# MATRIZ DE ACTIVACIÓN DE UNIDADES DE NEGOCIO PRODUCTIVAS POR EMPRESA

**Addendum Master 360 · WAVE A0-P** · 2026-09-09 · base `7ee72a1` · **sin código**

Requisito vigente: `OD-16` (`spec.md §4.0`). Implementación: `GA-REM-040` fases 1 (modelo y
resolutor), 7 (`API` de administración), 8 (sesión). Cada celda cita dónde está y qué prueba lo
demuestra; una celda sin prueba se declara así.

| Columna | `grandparent` | `breeder` | `hatchery` | `broiler` |
|---|---|---|---|---|
| **Soportada en todo el producto** | sí · `business_units.code` sembrado (`baseline_seeds.UNIDADES_DE_NEGOCIO`), `is_active` | sí | sí | sí |
| **Puede habilitarse por empresa** | sí · `PATCH /business-units/grandparent/enable` (`admin.fijar_habilitacion`, crea la fila si no existe) | sí | sí | sí |
| **Puede deshabilitarse por empresa** | sí · `PATCH …/disable` (`is_enabled=false`, fila conservada) | sí | sí | sí |
| **Política por omisión** | **apagada**: sin fila no hay habilitación (`unidades_habilitadas`, `GA-REM-040 §7.4`); ninguna semilla la enciende (`sembrar_unidades_de_negocio` solo catálogo) · alta real → `BU-D05` | ídem | ídem | ídem |
| **Permiso** | ver `business_units:read` · habilitar/deshabilitar `business_units:update` (Administrador de Accesos, Super Administrador) · nunca por nombre de rol | ídem | ídem | ídem |
| **Acotada a inquilino** | sí · `router._empresa_efectiva` → 403 sin empresa efectiva; `company_id` de la empresa efectiva (`OD-11`, `OD-14`: `TENANT_SCOPED`) | ídem | ídem | ídem |
| **Efecto en la sesión** | `GET /me` → `company_business_units` (habilitadas), `granted_business_units`, `effective_business_units` (resolutor central) — fase 8, `AC-H11` | ídem | ídem | ídem |
| **Requiere concesión de usuario** | sí · `unidades_efectivas` exige `user_business_units` viva de **esa** empresa (`AC-B02`, `OD-09.d`) | ídem | ídem | ídem |
| **Apagar prevalece sobre la concesión** | sí · `CompanyBusinessUnit.is_enabled IS TRUE` en el resolutor (`AC-A05`); concesión conservada (`AC-A04`) | ídem | ídem | ídem |
| **Política de reactivación** | provisional `GA-REM-040 §6.3` (la concesión previa vuelve a ser efectiva, `AC-A06`) · **`BU-D10` = `PENDING_RATIFICATION`** | ídem | ídem | ídem |
| **Spec** | `GA-REM-040 AC-A01…A07`, `AC-B01…B12`, `AC-H11…H14` · `OD-09`, `OD-15`, `OD-16` | ídem | ídem | ídem |
| **Test** | `test_business_units.py` (31) · `test_business_unit_admin.py` (39: `test_habilitar_una_unidad_apagada_la_enciende`, `test_deshabilitar_apaga_la_unidad`, `test_habilitar_no_concede_la_unidad_a_nadie`, `test_deshabilitar_no_borra_las_concesiones_y_rehabilitar_las_devuelve`, `test_una_unidad_nunca_configurada_se_puede_habilitar`) · `test_business_unit_guard.py` (25) · `test_session_payload.py` (16) — **ninguno es específico de una unidad: prueban la mecánica con códigos del catálogo** | ídem | ídem | ídem |
| **Estado** | `REQUIREMENT EXISTS · IMPLEMENTATION EXISTS · CERTIFICATION GAP` | ídem | ídem | ídem |

## Comprobaciones del requisito `OD-16` (§30 del encargo)

| Condición | Resultado | Evidencia |
|---|---|---|
| Las cuatro existen | ✓ | catálogo sembrado; `test_ac_c15_toda_ruta_esta_clasificada`; sin quinta unidad (la clasificación pendiente no lo es, `OD-10.c`) |
| Las cuatro se configuran independientemente por empresa | ✓ | `uq_company_business_unit(company_id, business_unit_id)`; ninguna restricción cruzada en `fijar_habilitacion`; sin «breeder obligatoria»; sin «todas encendidas» en código ni semillas |
| La configuración pertenece al plano de control de Global Avícola | ✓ | `OD-09.b`; rutas `CONTROL`; sin acoplamiento a SAP |
| Una unidad inactiva no puede hacerse efectiva para un usuario | ✓ | `unidades_efectivas_por_id` exige `is_enabled`; `test_deshabilitar_*` |
| Habilitar no concede | ✓ | `test_habilitar_no_concede_la_unidad_a_nadie` |
| `UserBusinessUnitAccess` separada | ✓ | `user_business_units` apunta a `company_business_units`, no al catálogo |
| `RBAC` separado | ✓ | `AC-B06`; `test_el_nombre_del_rol_no_concede_nada` |
| Alcance de empresa preservado | ✓ | `AC-A07`, `AC-B10`; `RQ-03 COMPLETE` |
| El resolutor honra la habilitación | ✓ | `unidades_efectivas_por_id` |
| La sesión honra al resolutor | ✓ | `/me` usa `unidades_efectivas_por_id`; `test_h11_*`, `test_la_efectividad_del_listado_coincide_con_el_resolutor_central` |
| **Ningún hardcode del frontend asume las cuatro activas** | **✗** | `navigationConfig.ts`, `processCatalog.ts`, `LotFormPage.BIRD_TYPES`, `DashboardPage` son estáticos; **0 lecturas** de `effective_business_units` en `frontend/src` → `H360A-01` (alcance de la fase 9, `GA-REM-040 §14.2-14.3`; la autoridad sigue en el backend) |
| Las pruebas demuestran la distinción | ✓ (mecánica) · ✗ (proceso) | 111 pruebas de integración; **0 E2E** de configuración por empresa; certificación de acceso por proceso `0/15` |

## Qué significa exactamente «`BU 0/15`» (§31 del encargo)

`PROCESS_BUSINESS_UNIT_ACCESS_MATRIX.md` (2026-09-07) mide una **segunda dimensión de
certificación** por proceso: que cada uno de los 15 procesos, ya certificados funcionalmente,
respete además empresa `OFF`, usuario sin concesión y contrato entre unidades. Cuando se creó, la
capacidad no existía; hoy existe (fases 1-8) y la matriz sigue en `PENDIENTE` porque **su
certificación es la fase 10-11 de `GA-REM-040`**, todavía no ejecutada. Por tanto:

```
requisito de activación por empresa ........ EXISTE  (GA-REM-040 §17 A · OD-16)
implementación ............................. EXISTE  (fases 1, 7, 8 · 111 pruebas de integración)
certificación como proceso de negocio ...... NO      (0 E2E · 0/15 por proceso)
```

La existencia de las `API` de `CompanyBusinessUnit` **no** certifica ningún proceso. El número
`0/15` no se toca.

## Combinaciones

Las 16 combinaciones `ON/OFF` de cuatro unidades son representables (una fila por par, sin
reglas cruzadas). Ninguna prueba recorre las 16; `test_ac_a02_la_habilitacion_distingue_encendida_de_apagada`
prueba la independencia por par. No se considera hueco: el requisito exige representabilidad, no
combinatoria exhaustiva.

## Empresa SAP frente a inquilino de aplicación (§25 del encargo)

`companies` es a la vez la entidad empresarial (nombre, `tax_id`, país, moneda) y el inquilino
de seguridad (`company_id` en 44 tablas). El mapeo **no es explícito**: no hay código de
sociedad SAP ni columna que separe ambos papeles. Clasificación: **`PARTIAL` ·
`REQUIREMENT_CONFLICT`** ya registrada (`R-124`, `AOD-06`, `H360-D06`). `OD-16.c` fija la
distinción de autoridad (SAP crea la entidad; Global Avícola configura las unidades) **sin cambiar
el modelo**.
