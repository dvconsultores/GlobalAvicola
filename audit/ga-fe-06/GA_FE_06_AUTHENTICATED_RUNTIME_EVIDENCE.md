# GA-FE-06 · EVIDENCIA RUNTIME AUTENTICADO (E2E-01…16)

Generación certificada: **`index-DcqmSs-R.js`** (LM 2026-09-11 13:57:59 GMT · ETag `"6aa408e7-13cfbd"`), confirmada en corrida (`E2E-00-bundle`).
Datos crudos: `evidence/green/runtime-green.json` · `verify-focus.json` · `final-verify.json`.

## Resultados por escenario

| E2E | Escenario | Resultado | Evidencia |
|---|---|---|---|
| 01 | Alta válida completa (PLD +10 · área A1) | **PASS** | Lote 19 `GA6-E01-…`: POST **201**; payload `planned_close_date:"2026-09-21"`, `area_id:1`; fresh GET `2026-09-21T00:00:00Z` / `1`; detalle «Fecha prevista de cierre **2026-09-21**» |
| 02 | Exactitud del valor de fecha | **PASS** | typed == stored (19) |
| 03 | Selector de áreas (propias, sin IDs crudos) | **PASS** | Opciones asentadas: `Seleccionar área…, Nave Norte (GA-FE-06), Nave Sur (GA-FE-06)`; sin «Del Sur»; `masters/areas` de C = ids 1,2 |
| 04 | Opcionalidad real (NULL explícito) | **PASS** | Lote 23 `GA6-NN-…`: payload y fresh `null/null`; detalle '—' |
| 05 | Sin corrimiento ±1 (bordes +10/+3/+1/−1) | **PASS** | Los 4: `typed == slice(0,10)(stored)` exacto |
| 06 | Área de otra empresa | **PARTIAL → N-1** | Selector filtrado ✓ · `master/areas` solo propias ✓ · **POST directo `area_id=3` → 201 y persistió** (lote 18 `GA6-XT-CHECK-1`) — hallazgo nuevo registrado (`GA_FE_06_FINDINGS.md`), fuera de alcance R-182 |
| 07 | Refresh / relogin conserva verdad | **PASS** | Fresh idéntico tras reload; la fila del detalle persiste |
| 08 | RBAC (actor D sin `lots:create`) | **PASS** | UI: «No tiene permiso para ver esta sección» (fail-closed); API POST **403** |
| 09 | CBU (actor E con rol pero sin BU) | **PASS** | Submit real → **403** «sin acceso operativo a la unidad de negocio 'broiler'»; sin lote creado; API **403** |
| 10 | SLA fuera (+10) | **datos ✓ · aviso PENDING_SCAN_WINDOW** | Lote 19 con `2026-09-21` (hoy 2026-09-11, +10). Relecturas vivas 14:06/14:15 UTC → 0 avisos (ciclo horario no alcanzado antes de la higiene) |
| 11 | SLA frontera (+3) | **datos ✓ · íd.** | Lote 20 `GA6-B3` `2026-09-14` |
| 12 | SLA dentro (+1) | **datos ✓ · íd.** | Lotes 21 `GA6-I1` y 24 `GA6-MOB` `2026-09-12` |
| 13 | SLA NULL excluido | **datos ✓** | Lote 23 con NULL (no hay referencia → no hay aviso) |
| 14 | Fallo de validación sin falso éxito | **PASS** | 0 POST disparados; error «Mínimo 2 caracteres» visible |
| 15 | Auditoría de creación | **PASS** | `GET /audit?module=lots`: 9 altas GA6 por user 117; timeline lot 19 = (`created`, `lots`) |
| 16 | Update | **N/A** | Sin UI de edición (ver matriz UPDATE); backend íntegro |

Extras: lote 22 `GA6-PAST` (−1) excluido por fecha pasada (dato ✓) y lote 25 `GA6-VERIFY-1` (paso de sesión de verificación; NULL, se documenta en ledger).

## Vistas y idiomas

- **Móvil 390×844** (isMobile/hasTouch): alta REAL completada (lote 24 `GA6-MOB` `2026-09-12`, área 2). Capturas asentadas `mb-01b`, `mb-02b`.
- **Inglés**: `PLANNED CLOSE DATE`, `Area`, `Select area...` presentes (regex tolerante a la transformación CSS `uppercase`; `en-01b`).
- **Consola**: 0 errores propios de los flujos GA-FE-06. Ruido preexistente identificado y registrado: el detalle solicita KPIs; sin `reports:read` → 403 (N-3); con `reports:read` → `kpi/ipe` **500** en lotes con datos vacíos (N-2, causa raíz localizada: `date − datetime` en `get_kpi_ipe`). Ninguno causado por esta tranche (backend intacto).
- **Red**: `/lots/new` = 8 peticiones exactas (sin tormenta); ver `GA_FE_06_NETWORK_EVIDENCE.md`.

## Notas de método (honestidad de evidencia)

- La primera pasada de capturas (`ds-01`, `ds-02`, `ds-04`, `en-01`, `mb-01`) fotografió estados «Cargando…» (carrera de render); se conservan como SUPERSEDED y toda afirmación se apoya en las capturas asentadas `*-b/*-c` y en los JSON de red. La razón de los primeros `false` textuales quedó explicada (race y `text-transform: uppercase`, que afecta a `innerText` pero no al dato).
- El aviso SLA no se fuerza (el producto lo evalúa por su tarea interna horaria; no hay endpoint manual). La certificación del aviso se cubre en 3 capas (ver `GA_FE_06_SLA_CONTRACT_MATRIX.md`): datos runtime (esta tabla) + regla canónica (suite CI) + relectura oportunista al cierre de la tranche.
