# MATRIZ DE AUTORIDAD DE LAS SUPERFICIES DE DATO PRODUCTIVO — `R-139`

**WAVE A · R-139** · 2026-09-09 · base `6284a90` · construida **antes** de los AC y del código

Origen: `A01_SUPER_ADMIN_SHORTCUT_VERIFICATION.md §2` (23 usos de `is_super_admin` fuera de
`auth`: 4 asignaciones · 1 `CONTROL_GLOBAL` conforme · 8 exenciones de visibilidad de unidad
certificadas · 2 redundantes · **8 no conformes**). Norma: `OD-14.c` («dato productivo» y
«maestros» = **`INQUILINO`**: actor de empresa → el suyo; autoridad global sin contexto → **cero
filas / deniega**; situada en `A` → solo `A`) y `OD-14.d` («`PROHIBIDO sin empresa → todas`»).
Ninguna de las ocho es `CONTROL_GLOBAL`: `OD-14.c` reserva esa clase al catálogo de empresas, al
catálogo de capacidades y a las plantillas de sistema.

Convenciones vigentes que se preservan: listado sin empresa efectiva → **cero filas** (`R-116`,
`masters/service._apply_company_filter`); recurso ajeno por identificador → **`404`**
(anti-enumeración, `tenancy.verificar_pertenencia`, `get_event`, `get_lot`); evidencias ajenas →
**`403`** (convención propia de `evidences`, ya vigente para actores de empresa); referencia
foránea ajena en escritura → **`422 BR-07`** (`GA-REM-002 AC10`).

| ID | Superficie | Ruta · método | Handler → servicio | Recurso | Proceso | Clase actual (de hecho) | Clase esperada | Actor de empresa | Global sin contexto | Global situada en `A` | Global situada en `B` | Alcance de unidad | RBAC | Regla de recurso | Defecto actual | Test |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **S01** | listado de alertas operativas | `GET /operations/alerts` | `list_alerts` → `OperationsService.get_alerts` (`operations/service.py:762`) | `operational_alerts` | `P-14` / `P-03`·`P-06` (alertas de mortalidad, ambiente, peso) | global para `is_super_admin` (sin filtro de empresa) | **`INQUILINO`** | solo su empresa | **cero filas** | solo `A` | solo `B` | **sin predicado de unidad hoy** (ver `R-159`, fuera de alcance) | `operations:read` | por `lot_id` opcional | `if not is_super_admin: filtrar` → la autoridad global sin contexto lista alertas de todas las empresas; situada en `A` sigue viendo `B` | `test_od14_productive_surfaces.py::S01*` |
| **S02** | listado de eventos operativos | `GET /operations` | `list_events` → `get_events` (`:810`) | `operational_events` | todos los `P-0x` | global para `is_super_admin` | **`INQUILINO`** | su empresa y sus unidades efectivas | **cero filas** | solo `A` (todas las unidades de `A`: exención de visibilidad certificada, fase 3) | solo `B` | actor: `predicado_de_evento(unidades efectivas)` · global: exenta (**se preserva**) | `operations:read` | filtros `lot_id`, `farm_id`, … | ídem S01, además el total de la paginación revela volumen ajeno | `::S02*` |
| **S03** | borrado de evidencia | `DELETE /operations/{event_id}/evidences/{evidence_id}` | `delete_evidence` → `delete_evidence` (`:978`) | `evidences` (+ fichero en `MEDIA_DIR`) | evidencia de cualquier `P-0x` | global para `is_super_admin` | **`INQUILINO`** | propia → `204`; ajena → `403` | **`403`** | propia de `A` → `204`; de `B` → `403` | inverso | vía `get_event` no (la consulta es por `id + event_id`) — se preserva la convención `403` | `operations:delete` | `evidence.company_id == empresa efectiva` | `if not is_super_admin and evidence.company_id != self.company_id` → la autoridad global borra evidencia y fichero de cualquier empresa conociendo `event_id + evidence_id` | `::S03*` |
| **S04** | descarga de evidencia | `GET /operations/{event_id}/evidences/{evidence_id}/download` | `download_evidence` → `get_evidence_for_download` (`:997`) | `evidences` | ídem | global | **`INQUILINO`** | propia → `200` fichero; ajena → `403` | **`403`** | `A` → `200`; `B` → `403` | inverso | ídem S03 | `operations:read` | ídem | ídem S03 (lectura de fichero ajeno) | `::S04*` |
| **S05** | activación manual de lote (saldo de apertura) | `POST /lots/activate-manual` | `activate_manual` (`lots/service.py:351`) | `lots` → `opening_balances` | `P-11` | global omite pertenencia **y** alcance de unidad | **`INQUILINO`** | lote propio y alcanzable → crea; ajeno → `404` | **`404`** | lote de `A` → crea; de `B` → `404` | inverso | actor: lote alcanzable por unidad (`get_lot`, fase 3) · global: exenta de unidad (**se preserva**), no de empresa | `lots:create` | `BR-07` lote activo; sin saldo previo (`409`); sin historia (`docs/02 §3.9.2`) | `if not self.is_super_admin: verificar_pertenencia(...); get_lot(...)` → la autoridad global sin contexto o situada en `B` fija el saldo de apertura de un lote de `A` (**escritura**) | `::S05*` |
| **S06** | curvas de peso de una línea genética | `GET /masters/genetic-lines/{id}/weight-curves` · `POST /masters/weight-curves` (misma resolución `_linea_del_usuario`, `masters/curves.py:75`) | `curves._linea_del_usuario` | `genetic_lines` → `genetic_weight_curves` | `P-03`, `P-06` (`GA-REM-037`) | global **y actor sin empresa** sin filtro (`if not is_super_admin and company_id:`) | **`INQUILINO`** | línea propia → `200`; ajena → `404` | **`404`** | `A` → `200`; `B` → `404` | inverso | n/a (maestro por empresa) | `masters:read` / `masters:create` | línea de la empresa efectiva | dos huecos en una condición: la autoridad global lee/crea curvas de cualquier empresa; un actor **sin empresa** también (`R-116`) | `::S06*` |
| **S07** | galpones de una granja | `GET /masters/farms/{farm_id}/houses` | `get_houses_by_farm` (`masters/router.py:139`) | `farms` → `houses` (pertenencia por el padre, `GA-REM-002 AC12`) | `P-12` | global **y actor sin empresa** sin comprobación del padre | **`INQUILINO`** | granja propia → `200`; ajena → `404` | **`404`** | `A` → `200`; `B` → `404` | inverso | n/a | `masters:read` | granja de la empresa efectiva | `if not is_super_admin and company_id is not None:` → galpones de cualquier granja | `::S07*` |
| **S08** | incubadoras de una planta de incubación | `GET /masters/hatcheries/{hatchery_id}/incubators` | `get_incubators_by_hatchery` (`:161`) | `hatcheries` → `incubators` | `P-05`, `P-12` | ídem S07 | **`INQUILINO`** | ídem | **`404`** | ídem | ídem | n/a | `masters:read` | planta de la empresa efectiva | ídem S07 | `::S08*` |

## Causa raíz compartida

Las ocho comparten la misma forma: **el indicador de autoridad global sustituye al filtro de
empresa** (`if not is_super_admin: acotar`), que es exactamente la semántica que `OD-14 §6`
declara retirada («antes veía … de todas las empresas desde cualquier ruta; ahora tiene que
elegir una empresa»). `771b402` propagó `OD-14` a `users`, roles y `masters/service` y no al dato
productivo. Además, el primitivo compartido `tenancy.verificar_pertenencia` conserva en su
docstring y en su código la regla anterior («`company_id` nulo … no impone filtro», `tenancy.py:44-48`),
de modo que S05 seguiría abierta para la autoridad global sin contexto aunque se retirara su atajo:
la corrección de S05 pasa por `get_lot` (que ya acota por `_apply_company_filter`) **y** por hacer
que el primitivo falle cerrado con `company_id` nulo (`AC26`), lo que arrastra a sus otros
llamadores (`verificar_ubicacion`, `masters/service:199`) a la misma conformidad.

## Lo que esta matriz **no** reclasifica

- Las 8 exenciones de visibilidad de unidad certificadas (`review` ×3, `dashboard`, `operations.get_event`, `reports` ×2, `masters/service:113`): se preservan tal cual (`GA_REM_040_PHASE_3_EVIDENCE.md:88`, coherentes con `OD-09.a`). `R-139` no cambia `effective_business_units` ni concede unidades a la autoridad global.
- `masters/service:85` (`_CONTROL_GLOBAL = {"companies"}`): conforme.
- `operations:940/949`: redundantes tras `get_event`; no se tocan.

## Observación fuera de alcance

`get_alerts` (S01) no aplica predicado de unidad para actores de empresa; el panel (`dashboard._get_active_alerts`) sí. Es un hueco de **alcance de unidad**, no de clase de inquilino, y no está en `R-139`: se registra como `R-159` (P2) sin remediarlo aquí.
