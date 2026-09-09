# `R-127` · CATÁLOGO SEGURO DE EMPRESAS — EVIDENCIA

**WAVE A1** · 2026-09-09 · spec `GA-REM-033` enmienda A (`e9ab11e`) · implementación `e339c1e` ·
decisión **`OD-18`** (alias `AOD-12`) · clase `MODEL DEFECT → CONTRACT DEFECT` · **`BLOCKER PHASE 9`**

```
R-127   CERRADO   sap_config no nulo ya no rompe el catálogo · proyección explícita sin sap_config
R-127.b DEFERRED  escritura de sap_config (POST/PUT con dict sobre String) · OD-18.b · sin migración
FASE 9  FROZEN    bloqueo técnico retirado · autorización del propietario: NO
```

## 1. Requisito raíz y decisión

`docs/02 §3.1.4` («Configuración SAP por compañía») legitima el campo; **`OD-18.a`** decide que el
catálogo general **no lo contiene**; `OD-14.c` fija que el catálogo es `CONTROL_GLOBAL`; la fase
9 depende de él (`PHASE_9_DEPENDENCY_PREFLIGHT.md §3`, `company.store.ts:39`).

## 2. Causa raíz

```
Company.sap_config        String (masters/models.py:65 · migración b53bbe02a476 · commit inicial 3c93440)
                          tipada Mapped[Optional[dict]]  ← data-model.md:12 dice JSON: la columna diverge
CompanyRead(CompanyBase)  sap_config: Optional[dict]     ← contrato de lectura de list/get/create/update
```

Reproducción de la causa **sin revertir código** (`scratchpad/r127_causa.txt`): el contrato
antiguo reconstruido (`CompanyBase` + `sap_config: Optional[dict]`) validando una fila con
`sap_config='{"sap_client": "100"}'`:

```
ANTIGUO: ValidationError · campo=('sap_config',) · tipo=dict_type · msg='Input should be a valid dictionary'
NUEVO  : validó · claves = [approval_levels, country, created_at, currency, id, is_active, name, tax_id, updated_at]
NUEVO  : 'sap_config' in dump → False
```

## 3. Contrato antes y después

| | Antes (`CompanyRead(CompanyBase)`) | Después (`CompanyCatalogRead`) |
|---|---|---|
| Campos | `name, tax_id, country, currency, sap_config, approval_levels, id, is_active, created_at, updated_at` (hereda; crece con `CompanyBase`) | **exactamente** `id, name, tax_id, country, currency, approval_levels, is_active, created_at, updated_at` |
| `sap_config` | expuesto; `dict` sobre texto → `500` | **ausente** |
| Rutas afectadas | `GET /masters/companies`, `GET …/{id}`, respuestas de `POST` y `PUT` (`register_crud`, un solo `read_schema`) | las mismas |
| Escritura (`CompanyCreate`/`CompanyUpdate`) | `sap_config: Optional[dict]` | **sin cambio** (`R-127.b DEFERRED`, `OD-18.b`) |
| Persistencia | `String` | **sin cambio** (`alembic heads` = `s9t0u1v2w3x4`) |
| Frontend | `Company`, `CompanyOption` sin `sap_config` | **sin cambio** (`grep sap_config frontend/src` → 0) |

## 4. Rojo previo (`scratchpad/r127_red.txt`, contra `e9ab11e`)

`tests/test_company_catalog.py`, 11 pruebas: **9 fallaron · 2 pasaron**.

| Prueba | Resultado en rojo | Por qué |
|---|:--:|---|
| `T1` `AC13` control (empresa B, `sap_config` NULL) | **PASS** | autenticación, permiso `masters:read`, ruta y filtro de inquilino correctos |
| `T10` `AC20/21` sin migración, sin conector | PASS | invariante, no cambia |
| `T2`, `T2b` `AC14` tratamiento (empresa A, texto no nulo), listado y detalle | FAIL `assert 500 == 200` | el `500` de `R-127` |
| `T3` `AC15`, `T4` `AC16`, `T8` `AC22`, `T9` `AC23` | FAIL `500` | misma causa (la respuesta no llega a evaluarse) |
| `T5` `AC17` (actor A y actor B) | FAIL | el listado de A es `500`; el cuerpo de B **mostraba `"sap_co…"`**: el contrato antiguo exponía el campo |
| `T6` `AC18`, `T7` `AC19` autoridad global | FAIL `500` | una sola empresa con configuración rompía el catálogo global |

Nueve fallos con la **misma** aserción (`500 == 200`) y un control verde con el mismo rol y la
misma ruta: el fallo es el desajuste de `sap_config`, no autenticación, permiso ni alcance.

## 5. Implementación (`e339c1e`)

- `backend/app/masters/schemas.py`: `CompanyCatalogRead(BaseModel)` explícito, `from_attributes`, sin herencia de `CompanyBase`, sin `sap_config`; `CompanyRead` retirado (0 referencias restantes).
- `backend/app/masters/router.py:101-104`: `register_crud("companies", …, schemas.CompanyCatalogRead, …)`.
- Sin tocar `_apply_company_filter`, `_CONTROL_GLOBAL`, `switch-company`, modelo, migración, esquemas de escritura, frontend.

## 6. Verde objetivo y relacionado

```
tests/test_company_catalog.py .............................. 11 passed
test_masters · test_master_tenant_isolation (R-115/R-116/OD-14) ·
test_user_tenant_isolation · test_role_tenancy · test_master_management  64 passed · sin ajustes
```

`T-033-16` (ajuste de `test_r115_ningun_campo_de_la_empresa_ajena_viaja`) **no fue necesario**:
esa prueba afirma por marca textual, no por conjunto de campos; el helper `_empresa` que lee
`sap_config` de la base no se compara con la respuesta. Se deja constancia en lugar de tocarla.

## 7. Sensibilidad (`§63`–`§69`)

| Mutación | Instalada | Rama ejecutada | Propiedad retirada | Pruebas rojas | Motivo del rojo | Validez |
|---|:--:|:--:|---|---|---|:--:|
| `S1` `sap_config: Optional[str]` en `CompanyCatalogRead` | sí | sí (misma ruta) | ausencia del campo | **4/11**: `T3`, `T4`, `T6`, `T8` | campo prohibido **observado** en listado, detalle y catálogo global; `T2` sigue verde (texto válido) → el rojo es la fuga, no un `500` | **válida** |
| `S2` `sap_config: Optional[dict]` (contrato antiguo) | sí | sí | tolerancia a texto | **9/11**: todo menos `T1` y `T10` | el `500` original de `R-127` reaparece exactamente | **válida** |
| `S3` serialización cruda de columnas en `list_items` + `response_model=None` | sí | sí (listado) | proyección acotada | **3/11**: `T3`, `T4`, `T6` | `sap_config` y su contenido viajan en el listado; `T8` (detalle) verde porque la mutación es del listado — coherente | **válida** · sin `extra="allow"` |
| `S4` retirar filtro de inquilino | — | — | — | `N/A` | la enmienda no toca `_apply_company_filter`; `R-115` vigente (`test_master_tenant_isolation`, 16 verdes hoy) | n/a |
| `S5` contexto seleccionado sobre el catálogo global | — | — | — | `N/A` | no se toca el resolutor; `OD-14` vigente (`test_od14_contraste_empresas_global_frente_a_granjas_de_inquilino`, verde hoy) | n/a |

```
intentadas 3 · inválidas inicialmente 0 · reconstruidas 0 · válidas finales 3 · N/A con motivo 2
reversión: git diff --quiet en schemas.py y router.py tras cada una · grep MUTACION backend/app → 0
```

## 8. Inquilino, `OD-14` y fase 9

- `AC17`: `T5` (A ve solo A; B ve solo B; ninguna marca ajena viaja) ✓.
- `AC18`/`AC19`: `T6` (global sin contexto ve A y B) y `T7` (global situado en B sigue viendo A y B) ✓ — el contexto **no** estrecha el catálogo.
- `AC23`: `T9` (`id:int`, `name:str`, `is_active:bool`) ✓ — el selector de la fase 9 tiene lo que `company.store.ts` consume.
- `AC20`/`AC21`: `T10` ✓ — cabeza única `s9t0u1v2w3x4`, columna `String`, `SAP_ADAPTER ∈ {manual, mock}`.

## 9. Regresión completa

Backend **795 passed · 49 skipped · 0 failed** (539 s; 784 previas + 11 de `test_company_catalog.py`; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado). Vitest 87 passed / 8 archivos. `tsc -b --noEmit`: **6 errores TS6133/TS2493 preexistentes** (`AuditPage.tsx`, `LotFormPage.tsx`): reproducidos en `7ee72a1`, frontend sin cambios en esta ola → `R-158`. Guardianes de arranque y `test_rbac` (`SOLO_SUPER_ADMIN`) dentro de la suite, verdes. `test_business_unit_admin` conserva `== 7` rutas.

## 10. Cierre

`R-127` cumple la puerta de `§71`: `sap_config` no nulo → `200` · `sap_config` ausente · proyección
explícita · inquilino preservado · catálogo global preservado y no estrechado · sin migración ·
sin conectividad SAP · objetivo verde · sensibilidad válida 3/3 · regresión completa verde.

**Lo que no cierra**: `R-127.b` (escritura de `sap_config`, `OD-18.b`, `DEFERRED`) y el diseño de
persistencia/superficie administrativa de la configuración SAP (`SAP_DEFERRED`). La fase 9 pierde
su bloqueo técnico y **sigue `FROZEN`** por decisión del propietario.
