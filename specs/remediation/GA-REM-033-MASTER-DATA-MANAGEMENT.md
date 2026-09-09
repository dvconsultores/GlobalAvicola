# `GA-REM-033` · GESTIÓN DE DATOS MAESTROS

| Campo | Valor |
|---|---|
| **ID** | `GA-REM-033` · `CAPABILITY + CONTRACT SPEC` |
| **Prioridad** | **P1** · **Estado** `SPEC_READY` |
| **Hallazgos** | `R-89` (total descartado) · `R-90` (siete maestros sin gestión) · `R-91` (siete sin edición) |
| **Proceso** | `P-12` · Gestión de datos maestros |
| **Dependencias** | `GA-REM-002` (permisos y pertenencia) · `GA-REM-011` (contratos) |
| **Antecedentes** | `P12_NORMATIVE_MASTER_CATALOG.md` · `P12_BACKEND_MASTER_MATRIX.md` · `P12_FRONTEND_MASTER_MATRIX.md` · `P12_MASTER_PARITY_MATRIX.md` · `P12_PAGINATION_CONTRACT_MATRIX.md` · `P12_PROCESS_CHAIN_MATRIX.md` |

> **Una spec y no siete.** Los siete maestros comparten ciclo de vida, permisos, modelo de
> interacción, patrón de interfaz y forma de contrato. `§23` del encargo permite gobernarlos
> juntos precisamente en ese caso. Donde difieren —el alcance de inquilino— la spec lo dice.

---

## 1. Los tres problemas

**`R-90`.** Siete maestros que `docs/02 §3.2` exige —seis por nombre y prioridad, uno por
uso— no tienen ninguna forma de gestionarse desde el producto:

```
incubators · hatchers · productive-phases · medications
cull-causes · rejection-reasons · correction-types
```

No aparecen en `masterEntities` (`App.tsx:94`), que es la única fuente de rutas de maestros.
Hoy solo pueden poblarse por API o por SQL.

**`R-91`.** Esos mismos siete pasan `None` como esquema de actualización, de modo que
`register_crud` no registra la ruta `PUT`. No pueden corregirse ni por API.

**`R-89`.** `masters/router.py:38` calcula el total y lo descarta al devolver una lista
pelada. La interfaz muestra el tamaño de la página donde promete «resultados», y decide con
ese número equivocado si enseña la paginación.

## 2. Los maestros afectados, enumerados

`§102` del encargo prohíbe decir «crear las pantallas faltantes» sin nombrarlas.

| Maestro | Fuente normativa | Prioridad | Alcance | Padre |
|---|---|:--:|---|---|
| `incubators` | por uso: `HatcheryParams.incubator_id`, proceso `P-05` | — | por el padre | `hatchery_id` |
| `hatchers` | `§3.2.1` «Nacedoras» | Alta | por el padre | `hatchery_id` |
| `productive-phases` | `§3.2.1` «Fases Productivas» | Alta | **global** | — |
| `medications` | `§3.2.1` «Medicamentos» | Media | `company_id` | — |
| `cull-causes` | `§3.2.1` «Causas de Descarte» | Alta | `company_id` | — |
| `rejection-reasons` | `§3.2.2` «Motivos de Rechazo» | Alta | `company_id` | — |
| `correction-types` | `§3.2.2` «Tipos de Corrección» | Alta | `company_id` | — |

## 3. Fuera de alcance

- **`BirdTypeEnum` y `EventStatus`**: `§3.2` los lista, pero gobiernan la lógica del proceso
  —el tipo de ave selecciona la cadena productiva; el estado gobierna el flujo de revisión—.
  Hacerlos editables permitiría crear un valor que ninguna rama sabe atender. Divergencia
  consciente y registrada, no un hueco.
- El backend de los doce maestros completos: **no se toca**.
- Borrado físico y cascadas: el ciclo es **baja lógica** y así se queda.
- Un «motor genérico de maestros»: ya existe y funciona.
- `P-13`, `P-14`, `OD-04`, `GA-TD-014`.

## 4. Criterios de aceptación — grupo A · el total (`R-89`)

### `AC01` · El listado expone el total que calcula
`GET /masters/{entidad}` devuelve el total en la cabecera **`X-Total-Count`**, y el cuerpo
sigue siendo la lista.

> **Enmienda, y por qué.** Este criterio decía `{"items": [...], "total": n}`, siguiendo el
> contrato de `/audit`, `/corrections` y `/review`. Al ir a implementarlo se contaron los
> consumidores: **43 puntos del frontend** leen `/masters/*` como lista —los desplegables de
> los formularios operativos, entre ellos—, mientras que los endpoints con envoltorio tienen
> un consumidor cada uno.
>
> Cambiar la forma del cuerpo convertiría un defecto **P2 de contador** en un cambio de 43
> puntos de llamada, y `§51` del encargo lo prohíbe expresamente: `P-12` no es excusa para un
> refactor general. `X-Total-Count` es la convención estándar para exactamente esto: el total
> de una colección paginada sin tocar el cuerpo.
>
> La divergencia del contrato de la casa es **consciente y acotada a este endpoint**, y queda
> dicha aquí en lugar de descubrirse leyendo el código.

### `AC02` · El total respeta el filtro
Con `search` aplicado, `total` es el número de coincidencias, no el del catálogo entero.

### `AC03` · La interfaz muestra el total, no el tamaño de página
**Puerta de validez.** El conjunto de prueba tiene **más registros que el tamaño de página**.
Con menos, el tamaño de la página y el total coinciden y la comprobación no podría fallar.

## 5. Criterios de aceptación — grupo B · la gestión (`R-90`, `R-91`)

### `AC04` · Los siete son administrables
Cada uno de los siete tiene ruta, listado, alta, edición y baja lógica, **con el patrón
vigente**: `MasterListPage` parametrizada y una entrada en `masterEntities`. No se escriben
siete pantallas ni se rediseña la administración.

### `AC05` · Los siete admiten edición
Cada uno declara su esquema de actualización y `register_crud` registra su `PUT`. El esquema
expone los campos que `§3.2` llama «campos clave» y **no** expone `company_id`, `id` ni las
marcas del sistema (`UPDATE_SCHEMA_SECURITY_MATRIX`).

### `AC06` · Persistencia inmediata
`R-68`: tras crear o editar, una lectura posterior ve el nuevo estado. Sin esperas.

### `AC07` · Baja lógica, no borrado
`DELETE` marca `is_active = false` y el registro desaparece de las listas activas sin
perderse. No se añade borrado físico.

### `AC08` · Pertenencia del padre
`incubators` y `hatchers` no pueden crearse ni moverse bajo una planta de otra empresa
(`R-59`).

**Puerta de validez.** CONTROL y TRATAMIENTO con el mismo actor y la misma petición; lo único
que cambia es de quién es la planta.

### `AC09` · El maestro global no se filtra por empresa
`productive-phases` no declara `company_id`. **No** se le aplica `verificar_pertenencia`:
meterlo ahí lo rompería. Se comprueba que sigue siendo visible desde cualquier empresa.

### `AC10` · El maestro creado se puede usar
Una causa de descarte creada desde la gestión se puede seleccionar al registrar un descarte.
Es el paso 5 de la cadena: una pantalla que abre no certifica el proceso.

### `AC11` · Permiso obligatorio
Sin `masters:create` / `masters:update` no se crea ni se edita: `403`.

## 6. Criterio transversal

### `AC12` · La evidencia puede fallar
`GA-REM-016 AC13`. Mutación controlada y revertida sobre el total, sobre la persistencia de
un campo y sobre la pertenencia del padre.

## 7. Trazabilidad

| `AC` | Prueba | Nivel |
|---|---|---|
| `AC01` `AC02` | `backend/tests/test_master_pagination.py` | integración HTTP |
| `AC04`…`AC11` | `backend/tests/test_master_management.py` | integración HTTP |
| `AC03` | `e2e/proceso-p12-datos-maestros.spec.ts` | `UI_E2E` |
| `AC10` | ídem | `API_E2E` |
| `AC12` | informe de certificación | mutación |

> **Por qué `AC03` sí necesita interfaz.** `§68` del encargo lo condiciona al requisito, no al
> vocabulario: lo que falla es lo que el usuario **lee** en la pantalla. Un `API_E2E` no puede
> comprobar un número renderizado. Es el primer proceso de este programa cuya certificación
> exige `UI_E2E`, y solo para ese criterio.

## 8. Definición de terminado

- Los doce criterios pasan.
- Existe prueba que **falla contra el código actual** por la causa exacta.
- Sensibilidad demostrada y revertida.
- Los 8 pasos de `P12_PROCESS_CHAIN_MATRIX` se recorren.
- Paridad i18n preservada; ninguna cadena embebida.
- Regresión completa sin fallos nuevos.

---

# Enmienda A · el catálogo de empresas es una proyección acotada y segura (2026-09-09)

| Campo | Valor |
|---|---|
| **Enmienda** | `GA-REM-033-A` · `CONTRACT SPEC` · **Estado** `SPEC_READY` |
| **Hallazgo** | **`R-127`** · `/masters/companies` devuelve `500` si la empresa tiene `sap_config` (`REMEDIATION_BACKLOG.md:781`) |
| **Decisión que la gobierna** | **`OD-18`** (alias `AOD-12`): el catálogo general de empresas no contiene configuración SAP; persistencia `DEFERRED` |
| **Clasificación** | `MODEL DEFECT` con consecuencia `CONTRACT DEFECT` · **`BLOCKER PHASE 9`** (`MASTER_PROGRAM_STATUS_RECONCILIATION.md §9`, `PHASE_9_DEPENDENCY_PREFLIGHT.md §3`) |
| **Proceso** | `P-12` (catálogo) · dependencia de la fase 9 de `GA-REM-040` (selector de empresa) |
| **Dependencias** | `OD-14` (clase `CONTROL_GLOBAL` del catálogo) · `OD-11` · `GA-REM-002` enm. B (`R-115`, `R-116`) |
| **Fuera de alcance** | migración `String → JSON/JSONB` · API de configuración SAP · conector · secretos · OData · HANA · fase 9 · `CompanyBusinessUnit` |

## A.1 Propósito y requisito de origen

`docs/02 §3.1.4` declara «Configuración SAP por compañía»: el campo es legítimo. `OD-18`
decide **dónde no se expone**: en el catálogo general. El selector de empresa de la fase 9
(`company.store.ts:39`) solo puede leer `GET /masters/companies` (`PHASE_9_DEPENDENCY_PREFLIGHT.md`),
y esa ruta se rompe para todos —autoridad global incluida— en cuanto una empresa tiene
`sap_config` poblado. El propósito de esta enmienda es **un contrato de catálogo explícito,
acotado y que no dependa del contenido de `sap_config`**.

## A.2 El defecto, con precisión

```
Company.sap_config           columna String            masters/models.py:65 · migración b53bbe02a476
                             tipada Mapped[Optional[dict]]
CompanyRead.sap_config       Optional[dict]            masters/schemas.py:40 (y CompanyBase:19)
register_crud("companies")   read_schema = CompanyRead masters/router.py:101 → list · get · create · update
lectura                      texto en la columna → validación como dict → ResponseValidationError → 500
```

La proyección actual es la fila entera (`CompanyRead(CompanyBase)`): expone `sap_config` y
cualquier campo que se añada mañana. Eso es lo que `OD-18.a` prohíbe.

## A.3 Alcance

Se cambia **solo la proyección de lectura del catálogo de empresas**: el `read_schema` que
`register_crud("companies")` usa para responder en `GET /masters/companies`,
`GET /masters/companies/{id}` y, por construcción del helper, en las respuestas de `POST` y `PUT`.
No se toca `_apply_company_filter`, `_CONTROL_GLOBAL`, `switch-company`, el modelo, la migración,
los esquemas de escritura (`CompanyCreate`, `CompanyUpdate` conservan `sap_config`: su
tratamiento es la superficie administrativa futura, `OD-18.b`) ni el frontend (`domain.types.ts`
`Company` y `CompanyOption` ya no declaran `sap_config`).

## A.4 Criterios de aceptación (alias `AC-R127-01…12` del encargo)

| `AC` | Alias | Criterio |
|---|---|---|
| **`AC13`** | `AC-R127-01` | `GET /masters/companies` con `sap_config` `NULL` → `200`. |
| **`AC14`** | `AC-R127-02` | `GET /masters/companies` con `sap_config` **no nulo** (texto, el formato que la columna admite) → `200`. |
| **`AC15`** | `AC-R127-03` | `sap_config` **no aparece** en ninguna respuesta del catálogo (listado, detalle, alta, edición). |
| **`AC16`** | `AC-R127-04` | La respuesta contiene **exactamente** los campos aprobados: `id`, `name`, `tax_id`, `country`, `currency`, `approval_levels`, `is_active`, `created_at`, `updated_at`. Ni uno más. |
| **`AC17`** | `AC-R127-05` | La visibilidad de inquilino se preserva: el actor de la empresa `A` ve solo `A` (`R-115`). |
| **`AC18`** | `AC-R127-06` | El catálogo es `CONTROL_GLOBAL` para la autoridad global (`OD-14.c`): ve todas las empresas, con o sin contexto. |
| **`AC19`** | `AC-R127-07` | La autoridad global **situada** en `A` (`switch-company` / contexto autorizado) sigue viendo el catálogo **global**: el contexto no lo estrecha. |
| **`AC20`** | `AC-R127-08` | Sin migración: la cadena Alembic conserva su cabeza (`s9t0u1v2w3x4`) y `Company.sap_config` sigue siendo `String`. |
| **`AC21`** | `AC-R127-09` | Sin conectividad SAP real: `SAP_ADAPTER` y `FEATURE_SAP_ENABLED` no cambian; ningún adaptador nuevo. |
| **`AC22`** | `AC-R127-10` | La proyección es un esquema **explícito** (`CompanyCatalogRead`) con campos enumerados; no hereda de `CompanyBase` ni admite extras. |
| **`AC23`** | `AC-R127-11` | Los campos que el selector de la fase 9 necesita (`id`, `name`, `is_active`) están presentes y tipados. |
| **`AC24`** | `AC-R127-12` | Ninguna regresión de contrato ajena: `test_masters.py`, `test_master_tenant_isolation.py` (`R-115`, `R-116`, `OD-14`), `test_user_tenant_isolation.py` y `test_role_tenancy.py` siguen en verde; la única prueba que se ajusta es la que comparaba campo a campo **incluyendo** `sap_config` (`test_r115_ningun_campo_de_la_empresa_ajena_viaja`), y se ajusta a la proyección aprobada dejando constancia. |

## A.5 Tareas

| Tarea | Contenido | `AC` |
|---|---|---|
| `T-033-13` | prueba **roja** `backend/tests/test_company_catalog.py`: empresa con `sap_config` texto no nulo, actor de empresa y autoridad global; `GET /masters/companies` y `/{id}` → hoy `500`; prueba de ausencia de `sap_config` y de conjunto exacto de campos → hoy fallan | `AC13–AC16`, `AC22` |
| `T-033-14` | `CompanyCatalogRead` en `masters/schemas.py`, explícito, `from_attributes`, sin `sap_config`; `register_crud("companies", …, CompanyCatalogRead, …)` | `AC15`, `AC16`, `AC22` |
| `T-033-15` | pruebas de control y tratamiento (`NULL` / no nulo), inquilino (`A` no ve `B`), autoridad global sin contexto y situada en `A`, campos de la fase 9, sin campos internos del ORM, sin migración (`alembic heads`) | `AC13`, `AC14`, `AC17–AC21`, `AC23` |
| `T-033-16` | ajuste documentado de `test_r115_ningun_campo_de_la_empresa_ajena_viaja` a la proyección aprobada | `AC24` |
| `T-033-17` | sensibilidad `S1–S3` (+ `S4`, `S5` declaradas `N/A` con motivo), regresión completa, evidencia `R-127-SAFE-COMPANY-CATALOG-EVIDENCE.md`, preflight de la fase 9 recalculado | todos |

## A.6 Estrategia de prueba

- **Rojo primero** (`GA-REM-016 AC13`): con el código actual, el tratamiento (`sap_config` no nulo) debe devolver `500` por `ResponseValidationError` sobre `sap_config`, con autenticación y permiso correctos, empresa visible y ruta alcanzada — no por otra causa. Se captura la salida.
- **Control + tratamiento**: `NULL` y no nulo, ambos `200`, ambos con el mismo contrato, ninguno con `sap_config`.
- **Inquilino y autoridad global**: reutiliza el patrón de `test_master_tenant_isolation.py` (`_token(user_id, company_id)`; `OD-11`: la reclamación de contexto solo vale para quien puede cambiar de empresa).
- **Contrato**: igualdad exacta del conjunto de claves (`AC16`), no inclusión.

## A.7 Sensibilidad (validez según `§63` del encargo)

| Mutación | Qué retira | Prueba que debe caer | Validez exigida |
|---|---|---|---|
| `S1` | reintroduce `sap_config: Optional[str]` en `CompanyCatalogRead` (la vía real del catálogo) | `AC15` (ausencia) y `AC16` (conjunto exacto) | observación directa del campo prohibido |
| `S2` | restaura el contrato antiguo: `sap_config: Optional[dict]` | `AC14` (tratamiento → `500`) | el `500` original de `R-127` |
| `S3` | sustituye la proyección acotada por serialización cruda de columnas en `list_items` (`response_model=None`) | `AC15`, `AC16` | campo prohibido observado; **no** `extra="allow"` |
| `S4` | retirar el filtro de inquilino | `N/A` — la enmienda no toca `_apply_company_filter`; lo cubre `R-115` (vigente) | — |
| `S5` | aplicar el contexto seleccionado al catálogo global | `N/A` — no se toca el resolutor de alcance; lo cubre `OD-14` (vigente) | — |

Contabilidad separada: intentadas · inválidas inicialmente · reconstruidas · válidas finales.

## A.8 Lo que esta enmienda deja fuera, a propósito

- La **escritura** de `sap_config` (`POST`/`PUT` con un `dict` sobre una columna `String`) sigue siendo un defecto latente **del mismo origen**; queda como `R-127.b · DEFERRED` bajo `OD-18.b` (representación persistente y superficie administrativa futura). No se remedia aquí ni se convierte el catálogo local en CRUD definitivo de empresas (`R-124`, `PL-05`).
- La fase 9 **no** se inicia: esta enmienda retira su bloqueo técnico; la autorización sigue siendo del propietario (`FROZEN`).

## A.9 Definición de terminado

`AC13–AC24` verdes · rojo previo documentado con su causa · `S1–S3` válidas y revertidas · regresión completa verde · `alembic heads` sin cambio · evidencia publicada · preflight de la fase 9 recalculado.
