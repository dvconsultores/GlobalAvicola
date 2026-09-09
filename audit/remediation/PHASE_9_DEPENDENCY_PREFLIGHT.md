# PREFLIGHT DE LA FASE 9 · INTERFAZ

`GA-REM-040` · `T-040-21`…`T-040-24` · 2026-09-09 · **solo lectura · nada implementado**

```
¿PUEDE LA FASE 9 CONSTRUIRSE SIN TROPEZAR CON UN BLOQUEO CONOCIDO DE BACKEND O CONTRATO?

NO.   Un bloqueo duro: R-127.
```

---

## 1. Qué es la fase 9, exactamente

| Tarea | Pantalla | `AC` |
|---|---|---|
| `T-040-21` | unidades por empresa — habilitar y deshabilitar | `AC-H04` |
| `T-040-22` | unidades por usuario — conceder entre las habilitadas | `AC-H05` |
| `T-040-23` | menú, rutas y el estado «sin unidades» | `AC-H02` `AC-H03` `AC-H06` |
| `T-040-24` | bandeja de clasificación pendiente, si el diseño la requiere | `AC-H07` |

Transversales: `AC-H08` (`i18n`, paridad), `AC-H09` (responsive), `AC-H10` (el backend sigue
siendo la autoridad, y se demuestra llamando a la `API`).

## 2. La matriz de dependencias

| Tarea | Superficie | `API` de backend | Campo de sesión | Permiso | Alcance | ¿Existe? | Hallazgo | ¿Bloquea? |
|---|---|---|---|---|---|:--:|---|:--:|
| `T-040-21` | listar y conmutar unidades de la empresa | `GET /business-units` · `PATCH …/enable` · `/disable` | `permissions` · `company_business_units` | `business_units:read` · `update` | inquilino | ✔ fase 7 | — | no |
| `T-040-22` | elegir usuario y conceder | `GET …/grant-candidates` · `POST /users/{id}/business-units` · `DELETE …/{code}` | `permissions` | `business_units:create` · `delete` | inquilino | ✔ fase 7 + `R-129` | — | no |
| `T-040-22` | ofrecer candidatos **sin** `users:read` | `GET /business-units/{code}/grant-candidates` | — | `business_units:create` | inquilino | ✔ `R-129` | `R-129` cerrado | no |
| `T-040-23` | filtrar el menú | — | `permissions` · `effective_business_units` | — | — | ✔ fase 8 | `R-119`: hoy 0 gating — **es el trabajo de esta tarea**, no un bloqueo | no |
| `T-040-23` | estado «sin unidades» | — | `effective_business_units == []` | — | — | ✔ fase 8 | — | no |
| `T-040-24` | bandeja de pendientes | `GET /operations/pending-classification` · `POST …/classify` · `/reclassify` | `permissions` | `masters:update` · `corrections:correct` | inquilino | ✔ fase 6 | — | no |
| **selector de empresa** (`OD-14`) | elegir inquilino | `GET /masters/companies` · `POST /switch-company` | `is_super_admin` · `effective_company_id` · `company_id` | `masters:read` | control global | ✔ ruta · **✘ contrato** | **`R-127`** | **SÍ** |

## 3. `R-127` · por qué es bloqueo duro, con precisión

**Lo que necesita el selector**: identificador, nombre, y saber cuál está seleccionada. Nada más.
No necesita `sap_config`.

**Lo que hay hoy**: `company.store.ts:39` llama a `GET /masters/companies`, cuyo contrato es
`CompanyRead` con `sap_config: Optional[dict]` sobre una columna `String`. **Cualquier empresa
con configuración `SAP` poblada devuelve `500` para toda la lista**, incluido el Super
Administrador. Y `docs/02 §3.1.4` declara «Configuración SAP por compañía»: configurarla es lo
esperado, no un caso raro.

**Lo que no hay**: una proyección segura. La sesión **no expone** empresas seleccionables, y la
fase 8 lo dejó fuera a propósito porque `§14.1` no lo pide — decisión correcta que ahora hace
visible el hueco.

```
FUENTE ÚNICA DEL SELECTOR   →   ruta que se rompe en cuanto se configura SAP
```

`§70` prohíbe las tres salidas fáciles —ignorar `sap_config`, capturar el `500`, ocultar las
empresas configuradas— porque cada una esconde el defecto en vez de resolverlo.

**Lo que hace falta antes de la fase 9**: remediar `R-127` en una tanda propia y autorizada, con
una decisión pequeña pero real: ¿la columna pasa a `JSON` (migración) o el esquema acepta `str`?
Y, adyacente y registrada desde `R-127`: ¿debe `sap_config` viajar en el listado de maestros, o
solo en una superficie administrativa? Ninguna de las dos se decide aquí.

## 4. Los demás hallazgos, uno a uno

| Hallazgo | ¿La fase 9 lo consume? | Veredicto |
|---|---|---|
| `R-112` — ocho rutas `SAP` sin `response_model` | ninguna tarea de la fase 9 menciona `SAP` | **no bloquea** |
| `BU-D10` — qué pasa con el histórico al cerrar una línea | `T-040-21` solo conmuta habilitación, y **`AC-A04`/`AC-A05`/`AC-A06` ya están decididas**: apagar no borra, apagado no es efectivo, rehabilitar devuelve. La interfaz puede prometer exactamente eso | **no bloquea** · riesgo: si `BU-D10` introduce «cerrar línea» como acto distinto de «deshabilitar», la pantalla necesitará un segundo control. Se registra, no se decide |
| `P-08` — `SAP` real | ajeno | **no bloquea** |
| `R-119` — el frontend no comprueba permisos | es lo que `T-040-23` construye | **no bloquea** — es el alcance |
| `R-120` — los cinco estados en el resto de pantallas | `AC-H06` lo exige para «sin unidades» | **no bloquea** — patrón ya establecido en `/users` |
| módulos por empresa | ninguna tarea lo pide | sin requisito · sin bug |
| `SAP` como dueño de maestros | ninguna tarea lo pide | `LOCAL BY SPEC` · sin cambios |

## 5. Los contratos que la fase 9 debe respetar

### El Administrador de Accesos

```
inicia sesión
  → `permissions` trae `business_units:*` y NO `users:read`
  → el menú muestra administración de unidades
  → el contexto es su propia empresa (`effective_company_id == company_id`)
  → `GET …/grant-candidates` le da a quién conceder
  → concede a otro
  → no aparece a sí mismo · y el `POST` deniega aunque se envíe
NUNCA llama a `GET /users`           ← contrato duro
NUNCA decide por `role.name`         ← `AC-F05`
```

Si el frontend actual asume `/users` para todo selector —`UsersPage` lo hace—, la fase 9
necesita **un selector propio** sobre `R-129`. Es refactor de frontend, no ampliación de
permisos.

### El Super Administrador (`OD-14`)

```
inicia sesión · `is_super_admin == true` · `effective_company_id == null`
  → el catálogo de empresas es control global      ← BLOQUEADO por R-127
  → elige A · `switch-company` · `effective_company_id == A`
  → administración de unidades y candidatos de A
  → elige B · lo mismo en B
```

### El usuario corriente

```
`is_super_admin == false` · sin selector de empresa
menú filtrado por `effective_business_units` y `permissions`
`[]` → estado explícito «sin unidades», distinguible de «no hay producción» (`AC-H06`)
```

## 6. Lo que la sesión ya entrega, y lo que no hace falta añadir

```
YA        is_super_admin · company_id · effective_company_id · permissions
          company_business_units · granted_business_units · effective_business_units
NO HACE   can_manage_business_units · can_select_users · empresas_disponibles
FALTA     lista de empresas seleccionables — y la respuesta correcta NO es meterla en la
          sesión sin norma, sino arreglar R-127, que es donde vive la fuente
```

## 7. Veredicto

```
PRERREQUISITOS   fase 8 COMPLETE · R-129 CERRADO · RQ-03 COMPLETE · OD-14 · OD-15 · R-113
BLOQUEOS         R-127 — uno, duro, con causa exacta
FASE 9           BLOQUEADA
INICIADA         NO
```

**Siguiente tanda autorizable**: `R-127`, con decisión de propietario sobre la forma de
`sap_config` y sobre si viaja en el listado. Cuando cierre, este preflight se repite — no se da
por válido por haberse escrito una vez.

---

## 8. Recálculo tras `WAVE A1` (2026-09-09 · base `e339c1e`)

| Dependencia | Antes | Ahora | Evidencia |
|---|---|---|---|
| `R-127` (única fuente del selector) | bloqueo duro | **CERRADO** — `GET /masters/companies` responde `200` con `sap_config` poblado; proyección `CompanyCatalogRead` sin `sap_config` | `R-127-SAFE-COMPANY-CATALOG-EVIDENCE.md` · `test_company_catalog.py` 11/11 |
| Contrato del selector (`company.store.ts:39`) | dependía de una ruta rota | `id`, `name`, `is_active` presentes y tipados (`AC23`); `CompanyOption` sin cambio | `T9` |
| Sesión (`GET /me`) | fase 8 `COMPLETE` | sin cambio; `test_session_payload` 16 verdes en la regresión de hoy | `§6` de este preflight |
| `R-129` candidatos | cerrado | sin cambio; `test_grant_candidates` 14 verdes | — |
| Configuración de unidades por empresa (`OD-16`) | implementada, no formalizada | **formalizada** como requisito de producto; API de fase 7 sin cambio; UI estática asume las cuatro (`H360A-01`, alcance de la propia fase 9) | `COMPANY_PRODUCTIVE_BUSINESS_UNIT_ACTIVATION_MATRIX.md` |
| **`R-139`** (atajos `is_super_admin` no conformes con `OD-14.c/d`) | no existía como bloqueo | **bloqueo de conformidad nuevo**: la fase 9 construye sobre `OD-14` y el dato productivo aún no lo cumple para la autoridad global; exige spec + AC + 8 pruebas (tanda propia de `WAVE A`) | `A01_SUPER_ADMIN_SHORTCUT_VERIFICATION.md` |
| `R-112` (8 superficies SAP sin proyección) | abierto | sin cambio; verificar frente a `OD-12` | — |
| `BU-D10` | pendiente | `PENDING_RATIFICATION`; no la requiere la fase 9 | — |
| `P-08` | `BLOCKED_EXTERNAL` | intacto | — |

```
PRERREQUISITOS TÉCNICOS   R-127 CERRADO · fase 8 COMPLETE · R-129 CERRADO · RQ-03 COMPLETE · OD-14 · OD-15 · OD-16 · OD-18
BLOQUEO TÉCNICO RESTANTE  R-139 (conformidad OD-14 en dato productivo) — precede a la fase 9
ESTADO                    READY AFTER REMEDIATION (R-139)
AUTORIZACIÓN              NO — FASE 9 FROZEN por decisión del propietario: la remediación P1 operativa/de datos/KPI va antes
INICIADA                  NO
```

---

## 9. Recálculo tras `R-139` (2026-09-09 · base `ec536c0`)

| Dependencia | Antes (§8) | Ahora |
|---|---|---|
| `R-127` | cerrado | cerrado |
| **`R-139`** (conformidad `OD-14.c/d` en dato productivo) | bloqueo de conformidad | **CERRADO** — 8/8 superficies `INQUILINO`; la autoridad global sin contexto obtiene cero filas / `404` / `403` / `400 BR-07`; situada en `A` solo `A` |
| `R-159` (alcance de unidad en `get_alerts`) | — | nuevo, P2, `WAVE B`; no es dependencia de la fase 9 (la fase 9 no decide autoridad) |
| sesión, `R-129`, `OD-15`, `OD-16`, `OD-18` | sin cambio | sin cambio (regresión verde) |

```
BLOQUEOS TÉCNICOS   ninguno
ESTADO              TECHNICALLY READY
AUTORIZACIÓN        NO — FASE 9 FROZEN por decisión del propietario (remediación P1 operativa/datos/KPI primero: WAVE B/C)
INICIADA            NO
```
