# R-191 · DISEÑO DE PRUEBAS RED · E2E RUNTIME · UAT

HEAD `c0b4afc` · Sin implementación.

## 1 · Diseño RED

### 1.1 Frontend — `frontend/src/pages/lots/__tests__/r191.phaseTransition.test.tsx` (jsdom)

Arnés: el de `gaFe06.lotFormContract.test.tsx:16-40` (mocks de `services/api` `get`/`post`, `react-i18next` con fallback, `components/Toast` con `toastSuccess`/`toastError` espiados y `getErrorMessage` real o simulado) + `useAuthStore` con permisos `lots:read`, `lots:create`, `operations:create` (patrón `gaFe04.lotsGates.test.tsx`). Render: `<MemoryRouter initialEntries={['/lots/66']}><Routes><Route path="/lots/:id" element={<LotDetailPage/>}/></Routes></MemoryRouter>`.

Fixtures (forma HEAD del API):

```ts
const LOTE = { id: 66, lot_code: 'L-GP-2026-12', bird_type: 'grandparent', status: 'active', farm_id: 1, house_id: null, start_date: '2026-09-01' }
const FASES_HEAD = [{ id: 10, lot_id: 66, phase_id: 1, start_date: '2026-09-01', end_date: null, is_active: true, start_population_male: 0, start_population_female: 0, created_at: '…' }]
const FASES_MAESTRAS = [{ id: 1, code: 'CRIA', name: 'Cría', order: 1 }, { id: 2, code: 'PROD', name: 'Producción', order: 2 }]
```

`get` responde: `/lots/66` ⇒ LOTE; `/lots/66/phases` ⇒ `FASES_HEAD` (y tras el POST, `[{...cría, is_active:false}, {id:11, phase_id:2, is_active:true, phase:{id:2,code:'PROD',name:'Producción'}}]`); `/masters/productive-phases` ⇒ `FASES_MAESTRAS`; resto `[]`/`{}`.

| Nombre exacto del `it` | Pasos | Aserción que **falla en HEAD** |
|---|---|---|
| `AC-R191-03 · el POST lleva lot_id y phase_id (resuelto por código PROD) y nunca phase_code` | clic «Iniciar Producción» → «Confirmar» | `expect(post).toHaveBeenCalledWith('/lots/66/phases', expect.objectContaining({ lot_id: 66, phase_id: 2 }))` y `expect(body.phase_code).toBeUndefined()` — HEAD: cuerpo `{phase_code:'production',…}` |
| `AC-R191-02 · 422 del servidor ⇒ toast.error con mensaje legible` | `post.mockRejectedValueOnce({ response: { status: 422, data: { detail: [{type:'missing',loc:['body','lot_id'],msg:'Field required'}] } } })`; confirmar | `expect(toastError).toHaveBeenCalledWith(expect.stringContaining('lot_id'))` — HEAD: `toastError` no llamado |
| `AC-R191-01 · tras 201 la fase activa PROD se muestra y el botón desaparece` | `post.mockResolvedValueOnce({ data: { id: 11, …, phase: { code: 'PROD', name: 'Producción' } } })`; `get('/lots/66/phases')` devuelve la lista nueva; confirmar | `await screen.findByText('Producción')` (badge) y `expect(screen.queryByRole('button', { name: /Iniciar Producción/ })).toBeNull()` — HEAD: el badge no aparece y el botón persiste |
| `AC-R191-10 · i18n: lots.transitionSuccess y lots.phaseAlreadyActive en ES/EN` | lectura de `public/locales/{es,en}/translation.json` | `expect(es.lots.transitionSuccess).toBeTruthy()` — HEAD: `undefined` |

### 1.2 Backend — `backend/tests/test_r191_lot_phase_transition.py` (PG aislado, `pytestmark = pytest.mark.asyncio`)

Escenario `esc` (fixture de módulo, patrón `tests/test_reception_reconciliation.py`): empresa A con `breeder` ON; operador con `operations:*`, `lots:read`, `lots:create`, `masters:read`; aprobador; granja, galpón (cap. 5000), OC `R191-OC-1` (5000); lote `lb` `breeder` activo con fase `CRIA` activa (alta vía `POST /lots/{id}/phases` con `phase_id` de `CRIA`); recepción 40♂/60♀ aprobada; mortalidad 5♂ aprobada (`get_current_bird_balance` = 95). Fases maestras por `code` (`CRIA`, `PROD`) leídas de `productive_phases`.

| Test (nombre exacto) | Aserción que **falla en HEAD** |
|---|---|
| `test_r191_01_add_phase_cierra_la_fase_anterior` | tras `POST {lot_id, phase_id: PROD, start_date}` ⇒ `SELECT count(*) FROM lot_phases WHERE lot_id=:l AND is_active` == 1 y la fase CRIA tiene `end_date = start_date` — HEAD: 2 activas, `end_date` nulo |
| `test_r191_02_lectura_incluye_codigo_de_fase` | `r.json()["phase"]["code"] == "PROD"` en el 201 y en `GET /lots/{id}/phases` — HEAD: `KeyError: 'phase'` |
| `test_r191_03_poblacion_por_sexo_derivada_del_saldo` | cuerpo sin poblaciones ⇒ `start_population_male == 35` y `start_population_female == 60` — HEAD: 0/0 |
| `test_r191_04a_lote_no_activo_es_400` · `test_r191_04b_fase_ya_activa_es_400` · `test_r191_04c_fecha_anterior_al_inicio_es_400` | `r.status_code == 400` y cero filas nuevas — HEAD: 201 |
| `test_r191_05_contrato_actual_phase_id_sigue_vigente` (control) | `POST {lot_id, phase_id, start_date, start_population_male: 40, start_population_female: 60}` ⇒ 201 con esas poblaciones — HEAD: verde |
| `test_r191_06_dos_transiciones_concurrentes_una_sola_activa` | `asyncio.gather` de dos POST ⇒ `{201, 400}` y una sola activa — HEAD: `{201, 201}` |
| `test_r191_07_cuerpo_de_la_ui_actual_es_422` (documenta la RED runtime; control) | `POST {phase_code:'production', start_date, 0, 0}` ⇒ 422 con `loc` `lot_id` y `phase_id` — HEAD: verde |

Ejecución: `bash backend/scripts/run_tests.sh tests/test_r191_lot_phase_transition.py` ⇒ salida a `evidence/red/backend-r191.log`; frontend `npx vitest run src/pages/lots/__tests__/r191.*` ⇒ `evidence/red/vitest-r191.log`.

## 2 · Diseño E2E runtime (C3)

Entorno: nube sobre la generación C2. Actores: operador de abuelas (con `lots:create`; si el rol real no lo tiene, usar el administrador de la empresa 1 y documentarlo) y aprobador UAT-09. Datos: lote de abuelas activo en cría con recepción aprobada (p. ej. el creado en el retry R-189, o uno nuevo `L-GP-2026-nn` vía importación → aprobación → recepción → aprobación). Runner Playwright con journal JSON y capturas; intercepción de `POST /api/v1/lots/*/phases`.

| Caso | Actor | Pasos | Resultado esperado | Limpieza |
|---|---|---|---|---|
| E2E-R191-01 | operador | `/lots/{id}` → «Iniciar Producción» → fecha de hoy → «Confirmar» | `POST` **201**; toast «Fase de producción iniciada»; badge «Producción»; botón ausente; acciones rápidas incluyen «Recolección de huevos» | la transición es irreversible: el lote queda en producción (registrado en el ledger de datos de prueba; el lote es de pruebas UAT-09) |
| E2E-R191-01m | operador | mismo caso a 390×844 | 201; modal y toast visibles; sin overflow | — |
| E2E-R191-02 | sonda API | `GET /lots/{id}/phases` | dos fases: `CRIA` `is_active:false` con `end_date`, `PROD` `is_active:true` con `phase.code == 'PROD'` y poblaciones = saldo por sexo | — |
| E2E-R191-03 | operador | recargar `/lots/{id}` | estado persistente: «Producción», botón ausente | — |
| E2E-R191-04 | sonda API | repetir `POST` con `phase_id` de `PROD` | **400** «El lote ya está en esa fase»; por UI (segundo lote en producción, si existe) el toast muestra ese texto | — |
| E2E-R191-05 | sonda API | `POST` con el cuerpo antiguo `{phase_code:'production',…}` | **422** (contrato del servidor intacto; la UI nueva no lo envía) | — |

Invariantes: `pageerror` 0; `5xx` 0; consulta C-06 ejecutada (`lot_phases` con más de una activa) y reportada. Artefactos: `evidence/runtime-c3/journal.json`, `R191-0x.png`, `phases-antes.json`, `phases-despues.json`.

## 3 · Plan UAT del propietario (C4)

| Caso | Acción del propietario | Resultado visible esperado |
|---|---|---|
| UAT-R191-01 | En un lote de abuelas/reproductoras en cría, pulsar «Iniciar Producción» y confirmar | Mensaje de éxito; la cabecera muestra «Producción»; el botón desaparece; entre las operaciones rápidas aparecen recolección y despacho de huevo |
| UAT-R191-02 | Abrir el modal sin escribir poblaciones y confirmar (segundo lote) | La fase se crea con la población viva por sexo del lote (visible en la respuesta/detalle); el propietario ratifica C-05 |
| UAT-R191-03 | Intentar iniciar producción en un lote cerrado o ya en producción (por API guiada o lote preparado) | Mensaje claro de error en pantalla, sin pantalla en blanco |
| UAT-R191-04 | Cambiar a EN y repetir UAT-R191-01 en el móvil | Textos en inglés; modal y mensajes visibles; sin desplazamiento horizontal |

Criterio: 4/4 en verde y ratificación de C-05.
