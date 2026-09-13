# R-203 · FINDING — REFERENCIAS ESTRUCTURALES DEL LOTE SIN VERIFICAR (GALPÓN, LÍNEA GENÉTICA, CURVA)

| Campo | Valor |
|---|---|
| **ID canónico** | **R-203** (asignado en `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §0`; máximo previo R-189) |
| **Título** | `POST/PUT /lots` acepta `house_id`, `genetic_line_id` y `weight_curve_id` sin comprobar pertenencia: un lote de la empresa A puede quedar ubicado en un galpón de B y evaluarse contra la curva de B (cuyos rangos se exponen en `weight-evaluation`) |
| **Severidad** | **P2** (§49: cruce de inquilino silencioso; bloquea por integridad/seguridad condicional — clase R-42/R-59/R-180 no aplicada a lotes) |
| **Clase** | `SECURITY` (tenencia estructural) / `DATA_INTEGRITY` (curva ajena aplicada) |
| **Proceso** | P-11/P-03/P-06 (alta y edición de lotes; evaluación de peso) |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` (== `origin/main`) |
| **Familia** | GAP-06 (informe D A.11); vecinos `R-42`/`R-59`/`R-180` (tenencia estructural en operaciones), `R-179` (catálogos con nulo compartido), `R-176` (edición) |
| **Paquete** | `audit/ga-claude-final-audit/specs/R-203/` (completo, 6 ficheros) |
| **GA-REM** | a asignar al autorizar; siguiente libre **GA-REM-043** |
| **Bloquea SAP** | **SÍ** (cruce de inquilino en maestro básico; la fiabilidad de datos de origen exige tenencia verificada) |
| **UAT del propietario** | no (superficie técnica; verificación por API + regresión de alta de lote) |

## 1 · Evidencia

### 1.1 Código (verificado en HEAD)

- `backend/app/lots/service.py:362-392` — alta: `house_id = data.house_id`, `genetic_line_id = data.genetic_line_id` se asignan **sin** `verificar_pertenencia`/`verificar_catalogo_de_empresa`. Contraste: `:320-329` sí verifica `farm_id` (403 si ajena) y `:341-347` verifica `area_id` (`OD-21`, `exigir_activo=True`).
- `lots/service.py:275-307` — `_curva_del_lote`: solo comprueba `curva.genetic_line_id == genetic_line_id`; **nunca** la empresa de la línea ⇒ una curva de B puede colgar de un lote de A si la línea no se verifica.
- `lots/service.py:411-436` — edición (`update_lot`) delega en `MasterService.update`; su `_PADRES_TENANT = {farm_id, hatchery_id}` (`masters/service.py:187`) **no incluye `house_id`**; `LotUpdate` admite `house_id` y `genetic_line_id` (`lots/schemas.py:65-67`).
- `backend/app/operations/service.py:744-824` — `weight-evaluation` expone `expected_min/max` de la curva aplicada ⇒ los rangos de B quedan **visibles** para A.
- Catálogo `houses` con dueño derivado (`House` → `Farm.company_id`); `GeneticLine` con `company_id` nulable (= compartida para `verificar_catalogo_de_empresa`, `tenancy.py:114`).

### 1.2 Cobertura de tests

**Ningún test** envía `house_id`/`genetic_line_id` ajenos en `POST/PUT /lots` (grep en `tests/` sin caso). `test_lot_area_ownership.py` cubre el área; `test_submovement_structural_tenancy.py` cubre submovimientos de operaciones.

## 2 · Causa raíz

La tenencia estructural se implementó por tranches (R-42/R-59/R-180 en operaciones; R-179 en catálogos de eventos; área en OD-21) y el **alta/edición de lote** quedó fuera del patrón: sus dos referencias estructurales (`house_id` vía granja, `genetic_line_id` catálogo) y la curva asociada no pasaron por los verificadores canónicos (`verificar_pertenencia`, `verificar_catalogo_de_empresa`).

## 3 · Impacto

- **Cruce de inquilino**: lote de A «vive» en un galpón de B (visibilidad/operaciones de B sobre el galpón; datos de tenencia rotos en trazabilidad y reportes).
- **Curva ajena**: evaluación de pesos contra la curva de B; los umbrales (`expected_min/max`) de B se exponen a A (fuga de dato de negocio) y las decisiones (alertas `weight_out_of_standard`) se toman con parámetros de otro inquilino.
- **Edición**: `PUT /lots/{id}` permite introducir/cambiar a referencias ajenas (mismo hueco por la otra puerta).

## 4 · Dedup realizada (§48)

| Registro inspeccionado | Resultado |
|---|---|
| R-001…R-189 | `R-42`/`R-59`/`R-180` (opera sobre eventos/submovimientos), `R-179` (catálogos nulo-compartido), `R-176` (edición de operaciones) — ninguno cubre `lots` |
| GA-REM-001…042 | `GA-REM-034` (delegación de masters) no cubre tenencia de referencias del lote |
| Informe D | GAP-06: «No registrado en backlog (grep `house_id.*lot`, `línea genética ajena`: vacío)» |

Conclusión: **nuevo**; ID asignado **R-203**.

## 5 · Propietario sugerido

Equipo backend (módulo `lots` + `masters`). Sin UI nueva; **regresión** del formulario de lotes (los selectores del frontend ya filtran por empresa, pero el fix debe impedir el envío directo por API).

## 6 · Bloquea SAP y por qué

**SÍ.** Los lotes y sus atributos (ubicación, línea genética, curva) alimentan trazabilidad, KPI y consolidación (P-08). Una referencia cruzada puede producir datos de origen con tenencia incorrecta enviados a SAP. No se toca SAP; solo se cierra la frontera interna.

## 7 · Interdependencias

- **R-50/GAP-05** (`company_id` fijable en maestros): mismo vector por el lado de maestros; tranche coordinada de seguridad.
- **R-164** (`lots.company_id` nulable): relacionado (deuda de esquema); aquí solo verificación de referencias.
- **R-179**: reutiliza `verificar_catalogo_de_empresa` (nulo = compartida) para `GeneticLine`.
- **weight-evaluation**: sin cambio de contrato; solo deja de exponer curvas ajenas como consecuencia de que ya no se aplican.
