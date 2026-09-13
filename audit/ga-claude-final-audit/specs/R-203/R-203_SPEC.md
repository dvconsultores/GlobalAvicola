# R-203 · SPEC — VERIFICACIÓN DE TENENCIA ESTRUCTURAL EN ALTA Y EDICIÓN DE LOTES

Fecha: 2026-09-13 · Hallazgo canónico: **R-203** (P2 · bloquea cruce) · HEAD `c0b4afc` · Origen GAP-06 · Registro G-14. Secciones §47.

## 1 · Contexto

El lote es el maestro operativo central (P-01…P-06). Su alta (`POST /lots`, `lots/router.py:39-46`) y edición (`PUT /lots/{id}`) aceptan referencias a granja/galpón/área/línea/curva/raza. Granja y área ya verifican tenencia; galpón, línea genética y curva no. La evaluación de peso (`GET /operations/{id}/weight-evaluation`) aplica la curva del lote y expone sus rangos.

## 2 · Evidencia

`R-203_FINDING.md §1`. Código: `lots/service.py:275-307,320-347,362-392,411-436`; `masters/service.py:187,227-254`; `lots/schemas.py:14-20,50-67`; `operations/service.py:744-824`.

## 3 · Causa raíz

El patrón de tenencia estructural quedó incompleto en `lots`: `house_id`/`genetic_line_id` no pasan por los verificadores canónicos, y `_PADRES_TENANT` del update genérico no conoce `house_id` (el padre real de `House` es `Farm`).

## 4 · Impacto de negocio

Lotes con ubicación o genética de otro inquilino; evaluación de curvas ajena y fuga de umbrales; trazabilidad/reportes con tenencia incorrecta; datos de origen dudosos para SAP.

## 5 · Comportamiento actual

| Ruta | Campo | Hoy | Esperado |
|---|---|---|---|
| `POST /lots` | `house_id` ajeno | 201 (persistido) | 404 fail-closed «Galpón no encontrado» (patrón BR-07/tenencia) |
| `POST /lots` | `genetic_line_id` ajena (no nula) | 201 | 404 «Línea genética no encontrada» (nulo=compartida sigue aceptándose, R-179) |
| `POST /lots` | `weight_curve_id` de línea ajena | 201 + curva aplicada | rechazo o `weight_curve_id` ignorado; nunca curva de otra empresa |
| `PUT /lots/{id}` | mismos campos | mismo hueco | mismas reglas que el alta |

## 6 · Comportamiento esperado

1. **Alta**: `house_id` → `verificar_pertenencia(db, House, house_id, company_id)` resolviendo la empresa por la granja del galpón; `genetic_line_id` → `verificar_catalogo_de_empresa` (nulo compartido intacto); `breed_id` → verificar contra la línea/empresa si aplica (mismo patrón); curva → `_curva_del_lote` exige que la línea de la curva sea **de la empresa** (o compartida) y que el lote declare esa línea.
2. **Edición**: mismas verificaciones para todo cambio de `house_id`/`genetic_line_id`/`weight_curve_id`; `MasterService.update` no basta (no conoce estos campos) ⇒ la verificación vive en `lots` antes de delegar.
3. **Sin cambio de contrato HTTP** para el caso legítimo (mismos 200/201); el caso ajeno pasa a 404 fail-closed (patrón de la casa, anti-enumeración).
4. `weight-evaluation` no cambia de forma; deja de poder devolver rangos de curva ajena porque ya no hay curva ajena aplicable.

## 7 · Alcance

- `backend/app/lots/service.py`: alta (`:362-392`), `_curva_del_lote` (`:275-307`), edición (`:411-436`).
- Reuso de helpers canónicos de `app/tenancy.py` (`verificar_pertenencia`, `verificar_catalogo_de_empresa`).
- Tests: `backend/tests/test_r203_lot_reference_tenancy.py` (nuevo; API) + ampliación de `test_lot_area_ownership.py` con los tres campos.
- Sin migración (los datos existentes no se reescriben; ver §12).

## 8 · Fuera de alcance

- `company_id` fijable en maestros (**R-50/GAP-05**, tranche de seguridad coordinada).
- `R-164` (`lots.company_id` nulable, deuda de esquema).
- Verificación de `area_id`/`farm_id` (ya cerradas).
- Saneamiento de filas históricas cruzadas (ver §12: recomputar inventario en la certificación; si alguna existe en el entorno certificable, se decide aparte).
- UI de edición de lote (no existe; CF-33 residual).

## 9 · Impacto frontend

Ninguno de producto. Los selectores (`LotFormPage`) ya cargan catálogos acotados por empresa; el 404 fail-closed se renderizará vía el manejador existente. Regresión: alta de lote por UI (flujo de P-03/P-06) intacta.

## 10 · Impacto backend

`lots/service.py`: 3 puntos de verificación (+1 en edición). Sin cambios en routers, esquemas, modelos, migraciones.

## 11 · Contrato frontend↔backend

`POST/PUT /lots` sin cambio de forma. Nuevo rechazo `404 {detail: "<X> no encontrado"}` para referencias ajenas (clase BR-07; mismo patrón que granja/área). Cliente legítimo: sin cambio.

## 12 · Impacto en datos

Sin migración. **Inventario obligatorio en la certificación**: `SELECT` de control (por SQL de solo lectura en el entorno de pruebas) para `lots` con `house_id`/`genetic_line_id` apuntando fuera de su empresa; si el recuento > 0, se documenta y se decide saneamiento en tranche aparte (no se toca producto aquí). En entornos de prueba con seeds, el recuento esperado es 0.

## 13 · Seguridad

Cierra el vector de cruce por referencias del lote (clase R-42/R-59/R-180). Fail-closed 404 (anti-enumeración, I.4 del informe D). Sin contexto/empresa: los caminos ya exigen empresa efectiva (`_acotar`/unidad).

## 14 · Inquilino

Es el objeto del paquete. Se conserva la semántica nulo=compartida de los catálogos (R-179) para `GeneticLine`; el galpón nunca es compartido (cuelga de granja con `company_id` no nulo).

## 15 · Unidad de negocio

Sin cambio (la unidad sigue derivándose del tipo de lote, `exigir_unidad_operativa`).

## 16 · RBAC

`lots:create`/`lots:update` sin cambio.

## 17 · Transacciones

Verificación dentro de la transacción del alta/edición, antes de persistir. Sin bloqueos nuevos.

## 18 · Auditoría

Sin cambio: el alta/edición de lote auditan como hoy (`CREATED`/`UPDATED` vía `MasterService`/listener). El rechazo no genera fila (patrón de rechazos de validación).

## 19 · i18n

Mensajes de rechazo en ES (patrón vigente); sin claves nuevas en frontend.

## 20 · Escritorio · 21 · Móvil

Sin cambio de UI; regresión por UI de alta de lote en ambos viewports.

## 22 · Manejo de errores

`404` fail-closed para referencia ajena; `400 BR-07`/`403` de unidad sin cambio; 409 de `lot_code` sin cambio; 422 de esquema sin cambio.

## 23 · Impacto de migración

Ninguna.

## 24 · Impacto SAP

Indirecto (fiabilidad de datos de origen). Sin cambio de contrato SAP. La medición de inventario (§12) alimenta la nota de preparación.

## 25 · Compatibilidad hacia atrás

- Clientes legítimos (referencias propias/compartidas): idénticos.
- Clientes que enviaban referencias ajenas: pasan de 201 a 404 (corrección de seguridad).
- Seeds/tests existentes: no usan referencias cruzadas (verificado por lectura de fixtures en la certificación).

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| AC-R203-01 | `POST /lots` con `house_id` de otra empresa ⇒ **404** «Galpón no encontrado»; cero filas creadas |
| AC-R203-02 | `POST /lots` con `genetic_line_id` de otra empresa ⇒ 404; con **null** ⇒ 201 (compartida, R-179 intacta) |
| AC-R203-03 | `POST /lots` con `weight_curve_id` cuya línea es de otra empresa ⇒ rechazo (404/400) sin aplicar la curva |
| AC-R203-04 | `PUT /lots/{id}` cambiando `house_id`/`genetic_line_id` a ajenos ⇒ 404; con propios ⇒ 200 |
| AC-R203-05 | `weight-evaluation` de un lote con curva propia devuelve los mismos rangos que hoy (regresión) |
| AC-R203-06 | Alta legítima por UI (granja+galpón+línea+área propios) ⇒ 201 (regresión `test_lot_area_ownership`, flujo P-03/P-06) |
| AC-R203-07 | Empresa: fixtures A/B; A no puede referenciar B por ninguna de las tres puertas |
| AC-R203-08 | Sin migración/endpoint/permiso; diff limitado a `lots/service.py` + tests |
| AC-R203-09 | Inventario de control (§12) ejecutado y registrado; 0 filas cruzadas esperadas en el entorno de pruebas |
| AC-R203-10 | Regresión: `test_lot_row_scope.py`, `test_lot_area_ownership.py`, `test_master_reference_tenancy.py`, `test_submovement_structural_tenancy.py`, `test_genetic_curves.py` verdes |

## 27 · Pruebas RED→GREEN

`R-203_RED_E2E_UAT_DESIGN.md §1`: `test_r203_01_galpon_ajeno_es_404`, `test_r203_02_linea_ajena_es_404_y_nula_es_201`, `test_r203_03_curva_de_linea_ajena_rechazada`, `test_r203_04_edicion_por_put_no_cruza`, `test_r203_05_weight_evaluation_sin_fuga` (control), `test_r203_06_alta_legitima_intacta` (control).

## 28 · E2E

API sobre pila local (`§2`): `R203-RT-01…06` (A/B cruzados por las tres puertas + alta legítima + weight-evaluation); artefacto `evidence/r203/runtime-{red,c3}.json`. Regresión UI mínima: alta de lote por UI en local (0 fatales).

## 29 · UAT

**No requiere UAT del propietario** (endurecimiento invisible en el flujo legítimo). Se informa en las actas de la tranche de seguridad.

## 30 · Criterios de cierre

RED válida · GREEN local (AC01-10) · sensibilidad (S1: retirar la verificación de `house_id` ⇒ AC01/04 rojas; S2: retirar la de línea/curva ⇒ AC02/03 rojas) · inventario §12 registrado · sin migración/endpoint/permiso · R-203 → `CLOSED` con GA-REM asignado.
