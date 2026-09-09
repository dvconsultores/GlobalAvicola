# VERIFICACIÓN EXACTA DE `A01` — ATAJOS `is_super_admin` FUERA DE `auth`

**WAVE A0-G** · 2026-09-09 · base `5d2e355` · **verificación documental, sin código**

## 1. Qué es `A01`

`MASTER_PROGRAM_STATUS_RECONCILIATION.md §4/§5/§11` (Master 360): **`H360-A01` · P2 · PLAUSIBLE**
— «23 atajos `is_super_admin` en 8 módulos fuera de `auth` no reevaluados tras `OD-14`; sin test
que niegue autoridad global sin contexto en esas superficies». Acción prevista en `WAVE A`:
**verificar**. El addendum lo confirmó como `H360A-08`. Aquí se verifica **sitio por sitio**.

Norma de contraste: `OD-14.c` (dato productivo y maestros = `INQUILINO`: autoridad global **sin
contexto → cero filas / deniega**; situada en `A` → solo `A`; catálogo de empresas =
`CONTROL_GLOBAL`) y `OD-14.d` («`PROHIBIDO sin empresa → todas las empresas`»).
Semántica certificada previa: `GA_REM_040_PHASE_3_EVIDENCE.md:88` («el Super Administrador queda
fuera del filtro **de unidad** exactamente donde queda fuera del de empresa»).

## 2. Los 23 sitios (`grep -rn is_super_admin backend/app` sin `auth/` ni `schemas.py`)

| # | Sitio | Qué hace el atajo | ¿Filtro de empresa vigente en la consulta? | Clase | Veredicto |
|:--:|---|---|:--:|---|---|
| 1 | `review/service.py:88` `_ambito_de_unidad` | devuelve `[]` (sin predicado de unidad) | sí (`:113-121`) | exención de **visibilidad de unidad** | certificada (fase 3) · coherente con `OD-09.a` |
| 2 | `review/service.py:371` ídem (aprobaciones) | ídem | sí (`:396-401`) | ídem | ídem |
| 3 | `review/service.py:572` ídem (pasos) | ídem | sí | ídem | ídem |
| 4 | `dashboard/service.py:25` `_lotes` | `None` → sin filtro de lotes por unidad | sí (9 consultas con `company_id == self.company_id`) | ídem | ídem |
| 5 | `operations/service.py:762` `get_alerts` | **omite el filtro de empresa** | **no** | **fail-open de inquilino** | **NO CONFORME `OD-14.c/d`**: el actor global sin contexto ve las alertas de **todas** las empresas |
| 6 | `operations/service.py:810` `get_events` | **omite el filtro de empresa** | **no** | **fail-open de inquilino** | **NO CONFORME**: listado de eventos de todas las empresas sin contexto |
| 7 | `operations/service.py:873` `get_event` | omite el predicado de unidad | sí (`:871`) | exención de visibilidad de unidad | certificada |
| 8 | `operations/service.py:940` `get_evidences` | omite comparación de empresa | sí, vía `get_event` (`:871`) | redundante | inocuo |
| 9 | `operations/service.py:949` `create_evidence` | ídem | sí, vía `get_event` | redundante | inocuo |
| 10 | `operations/service.py:978` `delete_evidence` | omite comparación de empresa; la evidencia se busca por `id + event_id` **sin empresa** | **no** | **fail-open de inquilino (escritura)** | **NO CONFORME**: borrado de evidencia ajena con `event_id` + `evidence_id` conocidos |
| 11 | `operations/service.py:997` `get_evidence_for_download` | ídem | **no** | **fail-open (lectura de fichero)** | **NO CONFORME** |
| 12 | `lots/service.py:60` | asignación | — | — | n/a |
| 13 | `lots/service.py:351` `activate_manual` | omite `verificar_pertenencia` del lote | **no** | **fail-open (escritura)** | **NO CONFORME**: saldo de apertura sobre lote de otra empresa |
| 14 | `reports/service.py:42` `_exigir_lote` | omite alcanzabilidad por unidad | sí (todas las KPI filtran `company_id == self.company_id`) | exención de visibilidad de unidad | certificada |
| 15 | `reports/service.py:62` `_filtro_de_lotes` | `None` | sí | ídem | certificada |
| 16 | `masters/service.py:39` | asignación | — | — | n/a |
| 17 | `masters/service.py:85` `_apply_company_filter` | sin filtro **solo** en `_CONTROL_GLOBAL` (`companies`) | por diseño | `CONTROL_GLOBAL` | **CONFORME `OD-14.c`** (`771b402`) |
| 18 | `masters/service.py:113` `_apply_business_unit_filter` | omite predicado de unidad | sí (`:85-99`) | exención de visibilidad de unidad | certificada |
| 19 | `masters/curves.py:75` `_linea_del_usuario` | omite filtro de empresa de la línea genética | **no** (y solo filtra si hay `company_id`) | **fail-open de inquilino** | **NO CONFORME** (lectura por `id`) |
| 20 | `masters/router.py:137` | asignación | — | — | n/a |
| 21 | `masters/router.py:139` `get_houses_by_farm` | omite comprobación de que la granja es de la empresa | **no** | **fail-open de inquilino** | **NO CONFORME**: galpones de granja ajena |
| 22 | `masters/router.py:159` | asignación | — | — | n/a |
| 23 | `masters/router.py:161` `get_incubators_by_hatchery` | ídem con la planta de incubación | **no** | **fail-open de inquilino** | **NO CONFORME** |

```
asignaciones (n/a) ............................ 4    (#12 #16 #20 #22)
CONTROL_GLOBAL conforme a OD-14 ............... 1    (#17)
exención de visibilidad de unidad, certificada  8    (#1 #2 #3 #4 #7 #14 #15 #18)
redundantes (empresa ya impuesta antes) ....... 2    (#8 #9)
NO CONFORMES con OD-14.c/d .................... 8    (#5 #6 #10 #11 #13 #19 #21 #23)
```

## 3. Resultado

`A01` **se confirma** y se precisa: no son 23 huecos sino **8**, en 4 módulos (`operations` ×4,
`lots` ×1, `masters/curves` ×1, `masters/router` ×2). Cuatro son lecturas de todos los inquilinos
sin contexto (#5, #6, #19, #21/#23) y tres son escrituras o descargas sobre recurso ajeno (#10,
#11, #13). El actor afectado es únicamente la autoridad global; **no hay escalada para actores de
inquilino**. Severidad **P1** (conformidad con `OD-14`, no `P0`).

Las 8 exenciones de visibilidad de unidad son semántica **certificada** (fase 3) y coherente con
`OD-09.a` (visibilidad de control de toda la empresa efectiva). Queda anotado para las fases 10-11:
comprobar que las **escrituras** del actor global sobre dato productivo siguen exigiendo concesión
(`exigir_acceso_a_unidad`), como exige `OD-16.f`.

## 4. Naturaleza de la acción

```
VERIFICACIÓN ..... hecha (este documento)
SPEC ............. requerida: enmienda a GA-REM-002 (clase C, dato productivo) o a GA-REM-040
                   — la propagación de OD-14.c a las 8 superficies, con AC por sitio
TEST ............. requerido: 8 pruebas CONTROL+TREATMENT (actor global sin contexto → cero filas / 404;
                   situado en A → solo A) — hoy 0
IMPLEMENTACIÓN ... requerida
ALCANCE .......... FUERA de esta ejecución (A0-P · A0-G · A1). Se registra como R-139 (WAVE A, tanda propia)
                   y precede a la fase 9 por OD-14.
```

---

## 5. Cierre (2026-09-09 · `R-139`)

Los 8 sitios no conformes de `§2` (#5 #6 #10 #11 #13 #19 #21 #23) quedaron conformes en `ec536c0`
(`GA-REM-002` enmienda C); además el primitivo `tenancy.verificar_pertenencia` falla cerrado con
empresa nula (`AC26`). Las 8 exenciones de visibilidad de unidad (#1 #2 #3 #4 #7 #14 #15 #18) se
preservan como semántica certificada; #17 sigue `CONTROL_GLOBAL`; #8/#9 siguen redundantes.
Evidencia: `R-139-OD14-PRODUCTIVE-DATA-EVIDENCE.md`.
