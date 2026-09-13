# GA-GOV-03 · MATRIZ DE EJECUCIÓN DE LOS 37 CASOS CANÓNICOS (T1 · §5/§10)

Estado: **PRE-FIX congelado** (baseline + RED dirigido). La sección §POST-FIX se completa con la corrida GREEN. Fuentes canónicas citadas por caso. **Product defect: NO en los 37** (reconfirmado contra baseline pre-T1).

## Leyenda
- **Fuente canónica A** = `OD-16` (specs/remediation/OD-16-*.md; producto `9ffc5ec`, `unidades_de_alcance_productivo`) + test canónico `tests/test_od16_global_read_boundary.py` — «apagar una unidad de empresa prevalece, también para la autoridad global; la lectura productiva es fail-closed (404 / fila invisible)».
- **Fuente canónica B** = `R-213` (registro G-25; `email_validator 2.3` rechaza `.test`/TLD reservados en `UserRead.email`) + `OD-23`/GA-UAT-08 (ciclo BU-D10 que el test debe seguir probando).
- **Fuente canónica C** = cabeza Alembic canónica `y5z6a7b8c9d0` (migración `b4d8c3a`, catálogo BU) + política `T-028` (`tests/time_reference.py`; guarda `test_t028_04`).
- **Fuentes Playwright**: BR-20 (`GA-REM-021` enm. B/B01; `validators.py:536-565`; antes `a759a17`), BR-21 (`GA-REM-005`/`GA-REM-021` C/B13; `validators.py:577-613`; `c653ff8`), BR-03 (`R-172`; `TIPO_DISPONIBLE="fertile"`; `64dff76`), R-118 (`OD-14.c`; `auth/service.py:349-357`), C-08 (locator sin tocar producto).

## 1 · Grupo A — 17 casos backend OD-16/fail-closed (pre-T1: FAILED)

| # | Test (fichero::función) | Firma pre-T1 (línea) | Aserción actual | Expectativa canónica | Fuente | Por qué es TEST_DEFECT | Corrección planificada | Producto |
|---|---|---|---|---|---|---|---|---|
| A1 | `test_lots_bu_enforcement.py::test_l08_put…` (342) | `404 == 403` «Lot no encontrado» | 403 | **404** + sin cambio de fila | A | Aserción anterior a `9ffc5ec` | `assert r.status_code == 404` (+ comentario OD-16) | NO |
| A2 | `::test_l08_close…` (348) | `404 == 403` | 403 | **404** + estado sigue activo | A | ídem | ídem | NO |
| A3 | `::test_l08_activate_manual…` (354) | `404 == 403` | 403 | **404** + 0 aperturas | A | ídem | ídem | NO |
| A4 | `::test_l08_phases…` (360) | `404 == 403` | 403 | **404** + 0 fases | A | ídem | ídem | NO |
| A5 | `::test_l11_frontera…sigue_viendo…` (393) | fila OFF visible → invisible | lh ∈ listado + GET 200 | **lh ∉ listado + GET 404** (fail-closed) + renombrar y actualizar docstring | A (sucede a la exención fase-3) | Docstring «no reabre lecturas» obsoleto tras GA-FE-02-D | Reescribir bloque; renombrar a `…_no_ve_la_unidad_apagada` | NO |
| A6 | `::test_e06_control_la_autoridad_global` (473) | `404 == 200` | situada descarga evidencia OFF → 200 | **404** (lectura productiva fail-closed); 403 sin contexto y 403 de otra empresa se mantienen | A | Ídem | Cambiar 2.ª aserción a 404 + docstring | NO |
| A7 | `test_operations_bu_enforcement.py::test_w13_submit…` (423) | `404 == 403` «Evento no encontrado» | 403 | **404** + estado REGISTERED (0 cambios) | A | ídem | 404 | NO |
| A8 | `::test_w13_cancel…` (429) | `404 == 403` | 403 | **404** + sin cambios | A | ídem | 404 | NO |
| A9 | `::test_w13_upload…` (437) | `404 == 403` | 403 | **404** + 0 evidencias | A | ídem | 404 | NO |
| A10 | `::test_w13_delete…` (443) | `404 == 403` | 403 | **404** + evidencia intacta | A | ídem | 404 | NO |
| A11 | `::test_a08…ve_toda_la_empresa` (520) | `{242,243,246} == {242,243,244,246}` | 4 alertas (incluye OFF) | **3 alertas** (OFF excluida) | A | Visibilidad de control heredada | Ajustar conjunto esperado + mensaje | NO |
| A12 | `::test_a13…no_resuelve_sobre_unidad_apagada` (548) | `404 == 403` «Alerta no encontrada» | 403 | **404** + sigue sin resolver | A | ídem | 404 | NO |
| A13 | `test_review_bu_enforcement.py::test_165_01…` (153) | `404 == 403` (acción `start`) | todas 403 | **todas 404** + estados intactos | A | ídem | 404 en el bucle | NO |
| A14 | `test_state_continuity.py::test_s07…corrige_ni_reenvia…` (330) | `404 == 403` | 403/403 | **404/404** + estado `returned` | A | ídem | 404 ×2 | NO |
| A15 | `test_internal_reversal.py::test_s03_s04…` (385) | `404 == 403` «Evento no encontrado» | 403 | **404** + 0 reversos | A | ídem | 404 | NO |
| A16 | `test_od14_productive_surfaces.py::test_s02_situada_en_a…` (316) | `{1013,1014} <= {1013}` | evento OFF visible | **ev_a visible, ev_a_h NO** + renombrar/docstring | A | «exención fase 3» derogada por lectura fail-closed | Reescribir aserción; renombrar a `…_ve_solo_sus_unidades_habilitadas` | NO |
| A17 | `test_review_decision_concurrency.py::test_r166_12…` (356) | `404 == 403` (unidad apagada) | 403 | **404** + sin historia de decisión | A | ídem | 404 + mensaje | NO |

## 2 · Grupo B — 5 casos backend fixture R-188 (pre-T1: FAILED)

| # | Test | Firma pre-T1 | Causa | Corrección | Fuente | Producto |
|---|---|---|---|---|---|---|
| B1-B5 | `test_r188_bu_lifecycle.py::{apagar_termina_las_concesiones_vivas (165), reactivar_no_devuelve (189), concesion_nueva_restaura_y_conserva_historia (202), zero_bu_sin_dato_productivo (290), transferencia_de_empresa_intacta (312)}` | helper `:133` → `/me` **500** == 200 | Fixture `:79` crea correos `…@e.test` (TLD reservado → `EmailStr` 500 en lectura) | `@e.test` → **`@example.com`** (solo fixture sintético; NO se toca la validación de producto) | B | NO (R-213 es el defecto de lectura de `/me`; su fix va en T11) |

**Invariante que las 5 deben seguir probando (OD-23)**: concesión nueva ⇒ acceso · apagar ⇒ sin acceso (marca, no borra) · re-encender sin concesión ⇒ sigue sin acceso · transferencia ⇒ no reactiva sin concesión nueva.

## 3 · Grupo C — 3 casos backend gobernanza (pre-T1: FAILED)

| # | Test | Firma pre-T1 | Corrección | Fuente | Migración |
|---|---|---|---|---|---|
| C1 | `test_company_catalog.py::test_t10` (267) | `['y5z6a7b8c9d0'] == ['x4y5z6a7b8c9']` | `len(cabezas)==1` + `cabezas == ['y5z6a7b8c9d0']` | C | 0 |
| C2 | `test_population_invariant.py::test_ac14` (398) | ídem | ídem (+comentario actualizado; se conserva el recuento exacto de rutas 211) | C | 0 |
| C3 | `test_time_determinism.py::test_t028_04` (113) | 4 fechas literales: `test_r188_bu_lifecycle.py:3`, `test_r184_ipe_date_semantics.py:4,50`, `test_r187_ipe_od22_scale.py:3` | Retirar las fechas de los docstrings/comentarios (texto sin literal ISO); la guarda queda intacta | C | 0 |

## 4 · Playwright — 12 casos (pre-T1: 12 FAILED en `evidence/playwright_e2e.log`)

| # | Spec:línea | Firma pre-T1 | Corrección planificada | Fuente | Producto |
|---|---|---|---|---|---|
| P1 | `proceso-p03-curvas-ui.spec.ts:374` (aserción :438) | `strict mode violation: getByText(/135/) → 2 elements` («Evento #135» vs «135–165 g») — latente (depende del id del evento) | Locator por rango canónico: `new RegExp(\`${MINIMO_A_LOS_15}\\s*[–-]\\s*${MAXIMO_A_LOS_15}\`)` | C-08 (sin tocar producto) | NO |
| P2 | `proceso-p03-reproductoras-cria.spec.ts:107` (`:117`) | 400 **BR-20** (faltan `received_total`,`dead_on_arrival`,`rejected_on_arrival`) | Añadir al paso `bird_reception` (lote breeder): `received_total: PRIMERA, dead_on_arrival: 0, rejected_on_arrival: 0` (cuadre exacto con Σ movimientos) | BR-20/B01 | NO |
| P3 | `proceso-p04-reproductoras-huevo-fertil.spec.ts:71` (`:79`) | 400 **BR-20** | Añadir campos al `bird_reception` de la cadena (Σ=5000): `received_total: 5000, dead_on_arrival: 0, rejected_on_arrival: 0` | BR-20/B01 | NO |
| P4 | `proceso-p05-incubacion.spec.ts:60` (`:73`) | 400 **BR-21** (faltan `chicks_healthy`,`chicks_weak`) + cascada **BR-04** en `chick_dispatch` (viables 0) | Nacimiento: añadir `chicks_healthy: 780, chicks_weak: 20` (Σ=800 ≤ nacidos 800); despacho 700 ≤ 780 | BR-21/B13 + BR-04 | NO |
| P5-P9 | `proceso-p10-trazabilidad-generacional.spec.ts:73,145,167,186,203` (helper `:58`) | 400 **BR-21** en el helper `tresGeneraciones` | Añadir al nacimiento del helper: `chicks_healthy: POLLITOS*2, chicks_weak: 0` (Σ = nacidos) | BR-21/B13 | NO |
| P10 | `proceso-p11-activacion-manual-de-lotes.spec.ts:160` (`:167`) | 400 **BR-20** | Añadir campos (Σ=800): `received_total: 800, dead_on_arrival: 0, rejected_on_arrival: 0` | BR-20/B01 | NO |
| P11 | `proceso-p11-…:210` (`:224-248`) | «el sujeto debe estar en la empresa B» (2 == 1) | Crear rol **y** usuario con la cabecera del admin situado en B (`adminAlla`) — R-118: la empresa del actor manda | R-118/OD-14.c | NO |
| P12 | `proceso-p15-reportes-e-indicadores.spec.ts:28` (`:37-38`) | 400 **BR-03** (carga 1000 > fértiles 800) | `CARGADOS = 800` (≤ fértiles) **y** nacimiento con `chicks_healthy: 580, chicks_weak: 20` (Σ=600) | BR-03 (R-172) + BR-21/B13 | NO |

## 5 · Recuento

| Grupo | Casos | Pre-T1 FAILED | Product defect | Reclasificados |
|---|---|---|---|---|
| A | 17 | 17 | 0 | 0 |
| B | 5 | 5 | 0 (colateral R-213 en producto de lectura — fuera de T1 por paquete propio) | 0 |
| C | 3 | 3 | 0 | 0 |
| Playwright | 12 | 12 | 0 | 0 |
| **Total** | **37** | **37** | **0** | **0** |

**RENOMBRADOS documentados**: A5 `test_l11_…sigue_viendo_la_unidad_apagada` → `test_l11_…no_ve_la_unidad_apagada`; A16 `test_s02_situada_en_a_solo_ve_a_incluidas_todas_sus_unidades` → `test_s02_situada_en_a_ve_solo_sus_unidades_habilitadas`. (Los nombres antiguos afirmaban el contrato derogado.)

## 6 · POST-FIX RESULTS

| Grupo | Casos | GREEN | Evidencia |
|---|---|---|---|
| A | 17 | **17/17** | `evidence/backend_group_a_green.log` (17 passed · 44.49 s) y `evidence/backend_targeted_25_green.log` (25 passed · 37.02 s) |
| B | 5 | **5/5** | `evidence/backend_group_b_green.log` (fichero completo 10/10 · 18.87 s) y targeted 25 |
| C | 3 | **3/3** | `evidence/backend_group_c_green.log` (3 passed · 2.77 s) |
| Playwright | 12 | **12/12** | RED: `evidence/playwright_targeted_7specs_red_pre_t1.log` (11 fallos reproducidos + locator latente); GREEN: `evidence/playwright_targeted_7specs_green.log` (49 passed · 1.3 m, tras corregir 11) + `evidence/playwright_p11_green_retry.log` (6/6 tras la concesión del sujeto) |
| Full backend | 1275 | **1226 passed · 0 failed · 0 errors · 49 skipped** (20:18) | `evidence/backend_full_suite_post_t1.log` + `evidence/backend-junit-post-t1.xml` (JUnit: tests=1275, failures=0, errors=0) |
| Full Playwright | 129 | **129 passed · 0 failed** (3.0 m) | `evidence/playwright_full_suite_post_t1.log` |

Notas de disposición final:
- **P1 (locator)**: en la corrida RED de T1 el fallo **no se reprodujo** (el id del evento no colisionó con `135` en la BD nueva) — es un TEST_DEFECT **latente por construcción** (así quedó capturado en la auditoría con la BD de entonces). El locator se desambiguó igualmente (rango canónico `135–165`) y queda verificado en GREEN; la disposición final sigue siendo TEST_DEFECT corregido, no APP_DEFECT.
- **P11 (aislamiento)**: el fixture requería **dos** correcciones encadenadas — (1) crear rol y usuario con la cabecera del admin situado en B (R-118/OD-14.c: la empresa del actor manda) y (2) conceder al sujeto la unidad `breeder` de B por el endpoint canónico `POST /users/{id}/business-units` (AC-B01). Sin (2), el 404 del control medía alcance, no pertenencia; con ambas, el caso prueba lo que declara.
- **0 reclassificaciones a producto** en los 37: el único defecto de producto colateral (R-213, `/me` 500 con dominios reservados) ya estaba fuera de alcance de T1 por decisión C-05 y conserva su paquete propio (T11).
