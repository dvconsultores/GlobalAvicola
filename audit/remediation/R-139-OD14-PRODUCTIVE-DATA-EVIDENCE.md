# `R-139` · `OD-14.c/d` EN EL DATO PRODUCTIVO — EVIDENCIA

**WAVE A (cierre)** · 2026-09-09 · spec `GA-REM-002` enmienda C (`270e73e`) · implementación
`ec536c0` · autoridad **`OD-14.c/d`** · origen `H360-A01` = `H360A-08` · verificación previa
`A01_SUPER_ADMIN_SHORTCUT_VERIFICATION.md` · matriz `R139_PRODUCTIVE_SURFACE_AUTHORITY_MATRIX.md`

```
R-139   CERRADO    8/8 superficies INQUILINO conformes a OD-14.c/d · primitivo compartido falla cerrado
        35/35 objetivo · rojo previo 24/35 · sensibilidad 8 válidas + 1 N/A (1 intento inválido reconstruido)
R-159   REGISTRADO get_alerts sin predicado de unidad para actores de empresa (fuera de alcance)
WAVE A  COMPLETE   fase 9 TECHNICALLY READY · FROZEN
```

## 1. Las ocho superficies (extraídas de `A01`, no inventadas)

| ID | Superficie | Sitio | Clase | Cambio (`ec536c0`) |
|---|---|---|---|---|
| S01 | `GET /operations/alerts` | `operations/service.py` `get_alerts` | `INQUILINO` | predicado de empresa incondicional (`_acotar_a_empresa`; `sa_false()` sin empresa efectiva) |
| S02 | `GET /operations` | `get_events` | `INQUILINO` | ídem; el predicado de **unidad** sigue solo para actores no globales (exención de la fase 3 preservada) |
| S03 | `DELETE …/evidences/{id}` | `delete_evidence` | `INQUILINO` | `evidence.company_id != empresa efectiva → 403`, para todos |
| S04 | `GET …/evidences/{id}/download` | `get_evidence_for_download` | `INQUILINO` | ídem |
| S05 | `POST /lots/activate-manual` | `lots/service.py` `activate_manual` | `INQUILINO` | `verificar_pertenencia` + `get_lot` sin rama por `is_super_admin` |
| S06 | `GET /masters/genetic-lines/{id}/weight-curves` · `POST /masters/weight-curves` | `masters/curves.py` `_linea_del_usuario` | `INQUILINO` | filtro por empresa efectiva incondicional; sin empresa → `404` |
| S07 | `GET /masters/farms/{id}/houses` | `masters/router.py` `get_houses_by_farm` | `INQUILINO` | comprobación del padre incondicional; sin empresa → `404` |
| S08 | `GET /masters/hatcheries/{id}/incubators` | `get_incubators_by_hatchery` | `INQUILINO` | ídem |
| `AC26` | primitivo compartido | `tenancy.verificar_pertenencia` | — | `company_id` nulo → `BR-07` (antes: `return`); docstring corregido. Llamadores arrastrados: `verificar_ubicacion`, `verificar_vinculo_generacional`, `masters/service._verificar_padres` |

Ninguna es `CONTROL_GLOBAL`. No se añadió `is_global_actor` ni lógica paralela; `is_super_admin`
solo sigue condicionando el predicado de unidad (S02, `get_event`), que es semántica certificada.
`grep is_super_admin` en las ocho funciones tras el cambio: 0.

## 2. Rojo previo (`scratchpad/r139_red.txt`, contra `270e73e`)

`tests/test_od14_productive_surfaces.py`, 35 pruebas: **24 fallaron · 11 pasaron**. Las 11 verdes
son los **controles**: aislamiento de actores de empresa en las ocho superficies, RBAC (`403` sin
`operations:read`), unidad apagada oculta (`AC-A05`) — prueban ruta, permiso, fixture y unidad correctos.

| Superficie | Prueba roja | Esperado (`OD-14`) | Observado | Cláusula |
|---|---|---|---|---|
| S01 | global sin contexto | `[]` | alertas de A **y** B (`[3, 4]`) | `OD-14.d` |
| S01 | situada en A / en B | solo A / solo B | `{5, 6}` en ambas | `OD-14.c` |
| S02 | global sin contexto | `[]` | 3 eventos de A y B | `OD-14.d` |
| S02 | situada en A · situada en B | solo A · solo B | evento de B visible desde A y viceversa | `OD-14.c` |
| S03 | global sin contexto · situada en A sobre B | `403` | **`204`** (evidencia y fichero de B borrados) | `OD-14.c/d` |
| S04 | global sin contexto · situada en A sobre B | `403` | **`200`** con `CONTENIDO-B` | `OD-14.c/d` |
| S05 | global sin contexto · situada en B sobre lote de A | `400 BR-07`, 0 saldos | **`201`**, saldo de apertura creado sobre lote ajeno | `OD-14.c/d` |
| S05 | control actor B | `400 BR-07` | `400 BR-07` ✓ (mi `AC` decía `404`: se corrigió el `AC` a la convención vigente, no el código) | — |
| S06 | global sin contexto · situada en A sobre B · **actor sin empresa** · `POST` curva | `404` | `200` / `201` | `OD-14.c` · `R-116` |
| S07 | global sin contexto · situada en A sobre B · actor sin empresa | `404` | `200` con galpones ajenos | ídem |
| S08 | ídem con plantas | `404` | `200` | ídem |
| `AC26` | primitivo con `company_id=None` · galpón bajo granja ajena por la global sin contexto | `BR-07` · no creado | `DID NOT RAISE` · **creado** | `OD-14.d` |

## 3. Verde objetivo y relacionado

```
tests/test_od14_productive_surfaces.py .......................... 35 passed
27 archivos relacionados (aislamiento, multiempresa, saldo de apertura, curvas, alertas,
smoke de evidencias, filas por unidad, guardas, maestros, operaciones, cierre, linaje) ... 377 passed
```

Un ajuste de fixture documentado (`T-002-18b`): `test_genetic_curves.py::test_t_037_15` creaba la
curva de la empresa 2 con la autoridad global situada en la 1 —el atajo que `R-139` retira—; pasa a
crearla situada en la 2 (patrón de `771b402`). Sus aserciones no cambian.

## 4. Sensibilidad (`§44`–`§48`)

| Mutación | Superficie | Instalada | Rama ejecutada | Propiedad retirada | Rojas | Motivo del rojo | Validez |
|---|---|:--:|:--:|---|---|---|:--:|
| `S1` | S01 · sin predicado de empresa | sí | sí | aislamiento de inquilino | **3**: control, global sin contexto, situada | el actor de A **ve la alerta de B**; la global ve la unión | válida |
| `S2` | S02 · la global vuelve a la unión (`if not is_super_admin` restaurado) | sí | sí | `OD-14.c/d` para la global | **3**: sin contexto, situada A, situada B | situada en A **ve el evento de B** (unión > 1 empresa observada) | válida |
| `S3` | `CONTROL_GLOBAL` → filtrado por contexto | — | — | — | `N/A` | ninguna de las ocho es `CONTROL_GLOBAL` | n/a |
| `S4` | S02 · sin predicado de unidad para actores | sí | sí | habilitación de unidad (`AC-A05`) | **1**: unidad apagada oculta | el actor **ve el evento de la unidad apagada** | válida |
| `S5` | S01 · puerta RBAC equivocada (`masters:read`) | 1.º intento **inválido**: comentario dentro de `Depends(...)` → `SyntaxError` → 34 errores de setup, sin crédito · **reconstruida** sin comentario | sí | RBAC | **1**: `sin_perm` obtiene `200` con alertas | permiso retirado y dato servido | válida (reconstruida) |
| `S6` | S07 · sin comprobación del padre | sí | sí | pertenencia por el padre (`AC12`) | **2**: control, situada | el actor de A **lista los galpones de B** | válida |
| `S7` | S04 · sin comparación de empresa | sí | sí | aislamiento de la evidencia | **3**: control, sin contexto, situada | `CONTENIDO-B` **descargado** por A y por la global | válida |
| `S8` | `AC26` · el primitivo vuelve a `return` | sí | sí | fail-closed sin empresa | **3**: `ac26` helper (`DID NOT RAISE`), `ac26` galpón (**creado** bajo granja ajena), `s05` global sin contexto | las dos de `AC26` por la propiedad; la de `s05` cae por **otro motivo** (`404` de `get_lot` en vez de `400`: `get_lot` sigue cerrando) — no se cuenta | válida (2 de 3 por la razón prevista) |
| `S9` | S06 · sin filtro de empresa | sí | sí | aislamiento de la línea | **2**: control, situada | el actor de A **lee las curvas de la línea de B** | válida |

```
intentadas 9 · inválidas inicialmente 1 (S5) · reconstruidas 1 · válidas finales 8 · N/A con motivo 1
reversión: git diff --quiet por fichero tras cada una · grep MUTACION backend/app → 0 · árbol limpio
```

## 5. Regresión

Backend **830 passed · 49 skipped · 0 failed** (542 s; 795 previas + 35 de `test_od14_productive_surfaces.py`; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado). Por archivo: aislamiento de maestros 16 · usuarios 18 · roles 12 · unidades 31 · guarda 25 · administración 39 · sesión 16 · accesos 16 · candidatos 14 · `test_rbac` 21 (`SOLO_SUPER_ADMIN` ≤ 15 sin tocar) · clasificación pendiente 35 · curvas 16 · multiempresa 5 + 12 · saldo de apertura 12 · filas por unidad 21 · KPI por unidad 15 · catálogo de empresas 11. Vitest 87 passed / 8 archivos. `tsc -b --noEmit`: 6 errores preexistentes (`AuditPage.tsx`, `LotFormPage.tsx`), mismo número y mismos ficheros que en `7ee72a1` (`R-158`, sin cambio). Guardianes de arranque (`authorization_coverage`, `route_scope`, `transaction`) sin excepción; `test_business_unit_admin` conserva `== 7` rutas. E2E: `BLOCKED_RUNTIME` (no ejecutada; 15/15 sigue histórica).

## 6. Lo que `R-139` preserva, explícitamente

- **Exención de visibilidad de unidad de la autoridad global** (fase 3, `OD-09.a`): situada en `A`, ve todas las unidades de `A` (`test_s02_situada_en_a_solo_ve_a_incluidas_todas_sus_unidades`). No se concede ninguna unidad; `effective_business_units` no cambia (`test_session_payload` 16 verdes).
- **Administrador de Accesos**: plano de control sin dato productivo (`test_access_administration`, `test_h14_*`); nada de `R-139` amplía la lógica del actor global.
- **Contraloría / SAP transversal**: ninguna de las ocho superficies pertenece a `OD-09.a` ni a `OD-12`; `P-08` intacto.
- **`BU-D10`**: `PENDING_RATIFICATION`; las fixtures habilitan explícitamente `breeder` (`is_enabled=True`) y apagan `hatchery` en `A` (`is_enabled=False`) como precondición asertada; ninguna prueba depende de rehabilitar.
- **Contratos**: los cuerpos de `200` no cambian; cambian los actores que los obtienen. Convenciones de error: las vigentes (`[]`, `404`, `403`, `400 BR-07`).

## 7. Fuera de alcance, registrado

`R-159` (P2): `get_alerts` no aplica predicado de unidad para actores de empresa (`GA_REM_040_PHASE_3_EVIDENCE.md:38` lo dejó «parcial»; `route_scope` lo declara «alertas de sus lotes»). Es alcance de **unidad**, no clase de inquilino; no se remedia aquí.

## 8. Cierre

`AC17–AC26` verdes · rojo previo por superficie con causa · `S1–S9` según `§4` · regresión completa
(`§5`) · sin migración (`s9t0u1v2w3x4`) · sin rutas nuevas · sin frontend · sin SAP · `BU-D10`
intacta → **`R-139 CERRADO`** · **`WAVE A COMPLETE`** · fase 9 **`TECHNICALLY READY · FROZEN`**.
