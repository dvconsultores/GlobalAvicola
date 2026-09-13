# R-190 · FINDING — Eventos de ubicación por UI sobre lotes sin galpón (BR-08)

| Campo | Valor |
|---|---|
| **ID canónico** | **R-190** (asignado en `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §0`; máximo previo R-189) |
| **Título** | El asistente de operaciones no resuelve `house_id`/`farm_id` para los eventos de ubicación cuando el lote no declara galpón: el backend responde `400 BR-08` y el flujo queda bloqueado por UI |
| **Severidad** | **P1** (§49: flujo requerido inalcanzable por la interfaz; sin rodeo dentro del producto) |
| **Clase** | `REQUEST_CONTRACT` / `BROKEN_FLOW` |
| **Proceso** | P-01 (Progenitoras cría), P-02 (Progenitoras producción), P-03 (Reproductoras cría), P-04 (Reproductoras huevo fértil) |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` (== `origin/main`; runtime `avicola.globaldv.net`, bundle `index-DDCcWL76.js`) |
| **Familia** | R-189 (F-01e resolvió sólo `bird_reception`); B-04 (sin selector de galpón del evento) |
| **Paquete** | `audit/ga-claude-final-audit/specs/R-190/` (completo, 6 ficheros) |
| **GA-REM** | a asignar al autorizar; siguiente libre **GA-REM-043** |
| **Bloquea SAP** | **SÍ** (véase §6) |
| **UAT del propietario** | sí (flujo visible) |

## 1 · Evidencia

### 1.1 Runtime (nube, 2026-09-13, actores UAT-09, empresa 1)

Fuente: `audit/ga-claude-final-audit/evidence/runtime-gp-e2e.json` (casos `R-08-*`, `R-10-recoleccion`) y capturas `audit/ga-claude-final-audit/evidence/R0x-*.png`. Lote autocreado `L-GP-2026-12` (id 66, `house_id = null`, `farm_id = 1`, nacido por `OD-25 (B)` al aprobar la importación):

| Caso | Evento por UI | Payload real | Respuesta |
|---|---|---|---|
| `R-08-distribucion` | `bird_distribution` con galpón destino elegido en la fila | `farm_id: 1`, **sin `house_id`** | `400` `{"detail":"El evento 'bird_distribution' requiere un galpón asignado","rule":"BR-08"}` |
| `R-08-salida` | `bird_exit` | `farm_id: 1`, **sin `house_id`** (el formulario no ofrece galpón) | `400 BR-08` «requiere un galpón asignado» |
| `R-10-recoleccion` | `egg_collection` | ídem | `400 BR-08` «requiere un galpón asignado» |
| `R-08-inspeccion` | `farm_inspection` con galpón en la fila | `house_id: 1`, **sin `farm_id`** (selector de granja vacío; la UI no lo exige antes de enviar) | `400 BR-08` «requiere una granja asignada» |

En todos los casos el error se muestra de forma segura (R-189 AC19-26 vigentes: `getErrorMessage`, sin React #31) pero **no hay forma de completar la operación** desde la interfaz.

### 1.2 Local (pila aislada, semillas `seeds.test_seeds`)

`audit/ga-claude-final-audit/evidence/ui-e2e-local-pass2.json` casos `GP2-14`, `GP2-15`, `GP2-17`: misma clase de fallo sobre un lote sin galpón creado por UI (`LotFormPage`, galpón opcional).

### 1.3 Código (verificado en HEAD)

- `frontend/src/pages/operations/OperationFormPage.tsx:387-394` — `derivedHouseId` sólo tiene fuente alternativa para `farm_inspection` (primera fila inspeccionada, `:385`) y para `bird_reception` (primer `target_house_id` de las filas, `:392-393`, F-01e); **el resto de tipos** cae en `selectedLot?.house_id ?? undefined` (`:394`).
- `OperationFormPage.tsx:386,438` — `farm_id` = `selectedFarmId ?? selectedLot?.farm_id`; en `farm_inspection` el lote es opcional (`:29-32`, selector oculto en `:2076`), de modo que la granja depende únicamente del selector de granja (`:2060-2071`), que la UI no exige.
- Captura de galpón por tipo en la UI: `bird_distribution` filas con `source_house_id`/`target_house_id` (`:792-810`); `bird_transfer` fila 0 origen/destino (`:844-862`); `bird_exit` **sin galpón** (`:869-989`: granja/planta destino, transporte, OC); `egg_collection` **sin galpón** (`:1046-1081`); `egg_dispatch` **sin galpón** (`:1083-1185`: incubadora destino y transporte); `transport_inspection` **sin galpón** (`:1352-…`).
- `backend/app/operations/validators.py:822-839` — `validate_farm_house` (BR-08): para los 10 tipos de `location_events` (`:828-832`) exige `farm_id` (`:834-835`) y `house_id` (`:836-839`) **del cuerpo**; llamada en `backend/app/operations/service.py:879` (alta) y `:1197-1201` (edición).
- Lotes sin galpón son legítimos: `backend/app/lots/service.py:158-161` (`crear_lote_de_importacion_si_procede` fija `house_id = event.house_id`, nulo porque la importación por UI no captura galpón; frontera F-01e AC-F01E-04); `frontend/src/pages/lots/LotFormPage.tsx:24,122` (`house_id` opcional ⇒ `null`); `backend/app/lots/schemas.py:14-15` (`farm_id`/`house_id` opcionales en `LotBase`).

## 2 · Causa raíz

Contrato de petición incompleto en el asistente: el dominio (BR-08) exige que **todo evento de ubicación** declare granja y galpón, y el asistente sólo resuelve el galpón desde el lote (que puede no tenerlo) salvo en dos tipos. Para cuatro tipos (`bird_exit`, `egg_collection`, `egg_dispatch`, `transport_inspection`) **no existe control** de galpón del evento (B-04); para dos (`bird_distribution`, `bird_transfer`) el galpón se captura por fila pero no se mapea al `house_id` del evento (misma clase que F-01e). Para `farm_inspection` la granja no se deriva del galpón inspeccionado ni se exige en cliente. No hay validación previa al envío: la única señal es el `400` del servidor.

## 3 · Impacto

- Los lotes del camino canónico `OD-25 (B)` (importar sin lote → aprobar → recepcionar) **no pueden distribuirse, trasladarse, dar salida, recolectar ni despachar huevo por UI**: la cadena P-01/P-02 se corta después de la recepción (F-01e sólo abrió la recepción).
- Los lotes creados por UI sin galpón (P-03/P-04/P-06) sufren lo mismo.
- No hay rodeo dentro del producto: el operador no puede editar el galpón del lote (`LotUpdate` admite `house_id`, pero la pantalla de lote no está en el flujo del operador y `lots:update` no es un permiso operativo) — cualquier «solución» fuera de la UI (API/SQL) rompe la trazabilidad exigida en §10.

## 4 · Dedup realizada (§48)

| Registro inspeccionado | Resultado |
|---|---|
| R-001…R-189 (`audit/remediation/REMEDIATION_BACKLOG.md`) | R-189/F-01e cubre exclusivamente `bird_reception` (frontera explícita: `audit/ga-f01/GA_F01E_SUBSANACION_ANNEX.md §3` «distribución/traslado no se reabren sin hallazgo propio»; clarificación C29). No existe hallazgo para los demás tipos ⇒ **nuevo** |
| GA-REM-001…042 | GA-REM-002 (`verificar_ubicacion`, tenencia) y GA-REM-005 (RR-02: distribución/traslado neutros en saldo) tocan los mismos eventos pero no el contrato del formulario ⇒ sin solape |
| GA-FE-01…08 | GA-FE-08 (hub) navega con `?type=`; no trata la derivación de ubicación ⇒ sin solape |
| OBS-UAT-01…06 · GA-UAT-01…09 | GA-UAT-09 retry (R-189 C3) certificó UAT-01…07 sin ejercer distribución/salida/recolección ⇒ sin solape |
| AOD/OD | OD-25 = B (lote autocreado sin galpón) es la **causa legítima** del dato nulo; no se reabre |
| Specs existentes | ninguna spec cubre «galpón del evento» para los 10 tipos de `location_events` |

Conclusión: brecha genuinamente nueva; ID asignado **R-190**.

## 5 · Propietario sugerido

Equipo frontend (asistente de operaciones), con revisión de dominio para C-03/C-04 (véase `R-190_CLARIFICATIONS.md`). Misma tranche que **R-205** (comparten `onSubmit`/derivación y el estado `stage` del asistente) y coordinada con **R-211** (galpón por fila y capacidad) y **R-194** (etapa incubadora, excluida aquí).

## 6 · Bloquea SAP y por qué

**SÍ.** SAP es la fuente de registro futura y consumirá los movimientos aprobados (P-08). Si distribución, salida y recolección no pueden registrarse por UI sobre los lotes del camino canónico, los saldos y consolidados que se enviarán a SAP quedan incompletos o se alimentan por vías no trazables. No se hace ninguna llamada a SAP en esta remediación; la arquitectura SAP se conserva.

## 7 · Interdependencias

- **R-205** (misma tranche): comparte la derivación en `onSubmit` y el estado `stage`; los cambios deben aterrizar en el mismo commit de implementación o en commits consecutivos con la misma RED.
- **R-211**: la validación BR-17 por fila utiliza los mismos `target_house_id`; R-190 fija cuál es el `house_id` del evento y R-211 cuál es la capacidad que se comprueba.
- **R-194**: `egg_reception_hatchery` y `chick_dispatch` (etapa incubadora, `farm_id` forzado a `undefined` en `:438`) **quedan fuera** de R-190.
- **R-189**: regresión obligatoria (`f01e.receptionHouse` 4/4; suites `f01.*`; recorrido UAT-01…07).
