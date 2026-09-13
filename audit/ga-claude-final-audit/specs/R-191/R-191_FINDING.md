# R-191 · FINDING — Transición de fase por UI (cría → producción) responde 422 en silencio

| Campo | Valor |
|---|---|
| **ID canónico** | **R-191** (registro §0; máximo previo R-189) |
| **Título** | El detalle de lote envía `POST /lots/{id}/phases` con `phase_code` y sin `lot_id`; el backend exige `lot_id` + `phase_id` (422); el error sólo va a `console.error`; además la lectura de fases no expone el código de fase y la fase anterior no se cierra, de modo que la UI nunca puede reflejar «Producción» |
| **Severidad** | **P1** (§49: transición de proceso requerida (P-02/P-04) inalcanzable por UI, fallo silencioso) |
| **Clase** | `REQUEST_CONTRACT` / `ERROR_HANDLING` / `RESPONSE_CONTRACT` |
| **Proceso** | P-02 (Progenitoras producción), P-04 (Reproductoras huevo fértil), P-06 (cierre: fases del resumen) |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` |
| **Familia** | B-07 (contrato del cuerpo), C-3 (respuesta), B-41 (`catch` sólo `console.error`) del inventario `B_form_contracts.md` / `C_response_error_state.md` |
| **Paquete** | `audit/ga-claude-final-audit/specs/R-191/` (completo, 6 ficheros) |
| **GA-REM** | a asignar al autorizar; siguiente libre GA-REM-043 |
| **Bloquea SAP** | **SÍ** (véase §6) |
| **UAT del propietario** | sí |

## 1 · Evidencia

### 1.1 Runtime (nube, 2026-09-13)

`audit/ga-claude-final-audit/evidence/runtime-gp-e2e.json` caso `R-09-transicion-ui` (lote 66 `L-GP-2026-12`, `grandparent`, activo, fase cría): clic en «Iniciar Producción» → confirmar ⇒ `POST /api/v1/lots/66/phases` con cuerpo `{"phase_code":"production","start_date":"2026-09-13","start_population_male":0,"start_population_female":0}` ⇒ **422** `{"detail":[{"type":"missing","loc":["body","lot_id"],…},{"type":"missing","loc":["body","phase_id"],…}]}`; `toasts: []`; el botón «Iniciar Producción» sigue visible; sin cambio en la página. Local: `audit/ga-claude-final-audit/evidence/ui-e2e-local-pass2.json` caso `GP2-16` (mismo resultado).

### 1.2 Código (verificado en HEAD)

- `frontend/src/pages/lots/LotDetailPage.tsx:121-138` — `handleTransitionPhase`: cuerpo `{ phase_code: 'production', start_date, start_population_male, start_population_female }` (`:125-130`); refetch de fases sólo en éxito (`:131-132`); `catch` ⇒ `console.error(...)` (`:133-135`), sin `toast` pese a tener `useToast`/`getErrorMessage` importados (`:11,:42`) y usados en otra acción (`:81`).
- `backend/app/lots/schemas.py:98-109` — `LotPhaseBase`/`LotPhaseCreate` exigen `lot_id: int` y `phase_id: int` (id de `productive_phases`); `start_population_*` con default 0 (`:103-104`).
- `backend/app/lots/router.py:136-147` — `POST /{lot_id}/phases` (`lots:create`) valida `data.lot_id == lot_id` (`400 lot_id mismatch`) **después** de que pydantic ya rechazó el cuerpo (422).
- `backend/app/lots/service.py:685-697` — `add_phase` crea la fila (`is_active` por defecto `True`, `lots/models.py:26`) **sin cerrar la fase activa anterior** ni fijar su `end_date`.
- `backend/app/lots/schemas.py:112-116` — `LotPhaseRead` no incluye la fase maestra (`phase {code, name}`) aunque el modelo tiene la relación `LotPhase.phase` (`lots/models.py:31`, `selectin`).
- `frontend/src/pages/lots/LotDetailPage.tsx:89-93` — `activePhaseName = activePhase?.phase?.name ?? activePhase?.phase?.code ?? null` ⇒ **siempre `null`** con el contrato actual ⇒ `resolveStageKey(birdType, null)` (`frontend/src/data/processCatalog.ts:312-321`) ⇒ siempre etapa «cría» para `breeder`/`grandparent` ⇒ `canTransition` (`:103-105`) siempre `true`, el badge nunca muestra «Producción» y las operaciones rápidas (`:229-241`) nunca cambian al catálogo de producción.
- `LotDetailPage.tsx:89` — `phases.find(p => p.is_active)`: con dos fases activas (consecuencia de `add_phase`) toma la primera (cría).
- Fases maestras: `backend/seeds/baseline_seeds.py:123-128` (`CRIA`, `PROD`, `INCUB`, `ENGORDE`), `dev_seeds.py:527-530` (idem), `integration_seeds.py:383-388` (`CRIA`, `PROD`, `ENG`, `INC` — códigos divergentes para engorde/incubación; `PROD` coincide en las tres). Ningún catálogo conoce el código `production`. Endpoint `GET /masters/productive-phases` (`masters/router.py:115`, permiso `masters:read`, `:36`). El frontend no lo consume (`grep productive-phases frontend/src` sólo en `App.tsx:161`, pantalla de maestros).

## 2 · Causa raíz

Contrato de petición inventado en el cliente (`phase_code` inexistente en el API; `lot_id` omitido), sin resolución del `phase_id` desde el catálogo; manejo de errores que traga la respuesta (B-41); y, encadenado, contrato de respuesta insuficiente (`LotPhaseRead` sin código de fase) y servicio que no cierra la fase anterior. Aunque el cuerpo se corrigiera, la pantalla seguiría sin reflejar la fase de producción.

## 3 · Impacto

- P-02/P-04: un lote de abuelas/reproductoras no puede pasar a producción por UI; el catálogo de operaciones del detalle sigue mostrando la cría (sin recolección/despacho de huevo en las acciones rápidas; la vía del hub sí las ofrece).
- El operador no recibe ninguna señal: cree que la acción falló «sin motivo» o que funcionó.
- El resumen de cierre y los indicadores por fase carecen de fase de producción real.

## 4 · Dedup realizada (§48)

| Registro | Resultado |
|---|---|
| R-001…R-189 | R-163 (unidad en `POST /lots/{id}/phases`, cerrado por `_exigir_unidad_operativa`) y R-42 (pertenencia del lote) tocan la ruta pero no el contrato del cliente ni la lectura de fases ⇒ **nuevo** |
| GA-REM | GA-REM-011 (alineación FE/BE, C-03 sobre `/lots/{id}`) no cubre `phases`; GA-REM-029 (cierre) no cubre fases ⇒ nuevo |
| GA-FE-01…08 | GA-FE-04 (gates de acción) certificó la **visibilidad** del botón por `lots:create`, no su contrato ⇒ nuevo |
| OBS/AOD/OD | ninguna decisión sobre fases; OD-16 (autoridad global sobre unidad apagada) intacta |
| Specs | `GA_R153_*` (lote autocreado) no trata la transición ⇒ nuevo |

Conclusión: brecha nueva; ID **R-191**. Los tests `tests/test_lots_bu_enforcement.py::test_l08_phases_*` que fallan en HEAD son `TEST_DEFECT` de OD-16 (GA-GOV-03), no producto.

## 5 · Propietario sugerido

Equipo frontend (detalle de lote) + backend lotes (contrato de lectura y `add_phase`). Tranche propia, corta (S/M), independiente de la familia del asistente; coordinada con **P1-12 (REAPERTURA)** para la auditoría de `add_phase` y con **GA-GOV-03** para `test_l08_phases_*`.

## 6 · Bloquea SAP y por qué

**SÍ.** Los consolidados por periodo y tipo (P-08) y los indicadores de producción de huevo dependen de que el lote esté en fase de producción; sin transición por UI, la fase real del lote y su historia (`lot_phases`) no reflejan la operación y los datos que SAP recibirá como fuente futura son incorrectos. Sin llamadas a SAP en esta remediación.

## 7 · Interdependencias

- **P1-12 (REAPERTURA)**: la cobertura de auditoría de `add_phase` (E-10) se resuelve allí; R-191 no la duplica pero no debe impedirla (un solo productor de auditoría).
- **GA-GOV-03**: `test_l08_phases_*` (esperan 403; hoy 404 por OD-16) se actualizan en la higiene de pruebas; R-191 añade su propia suite y no toca aquéllos.
- **R-218** (vista semanal) y **R-220** (badges) consumen `phases`; el campo aditivo `phase {id, code, name}` les sirve sin coste.
