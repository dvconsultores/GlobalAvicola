# R-196 · DISEÑO DE PRUEBAS RED · E2E · UAT

HEAD `c0b4afc` · Sin implementación en este documento.

## 1 · Diseño RED

### 1.1 `frontend/src/pages/masters/__tests__/r196.mastersCreate.test.tsx` (jsdom)

Mock de `services/api`; catálogos: empresas (contexto), granja A, planta B.

| Nombre | Pasos | Aserción que **falla en HEAD** |
|---|---|---|
| `AC-R196-01 · farm ⇒ payload con name/code (sin company del cliente)` | abrir `/masters/farms`; nuevo; rellenar; guardar | POST con cuerpo válido; 201 simulado — HEAD: `{}` ⇒ 422 |
| `AC-R196-02 · house con granja` | nuevo galpón; elegir granja A | payload `farm_id=1` — HEAD: sin campo |
| `AC-R196-03 · hatchery/incubator/hatcher` | crear cada uno | payload correcto — HEAD: `{}`/422 |
| `AC-R196-04 · capacity vacía ⇒ null` | dejar capacidad vacía | `capacity` ausente/null — HEAD: `''` |
| `AC-R196-05 · reactivar` | editar inactivo; activar | PUT `is_active:true` — HEAD: sin control |
| `AC-R196-06 · 422 ⇒ texto` | forzar 422 | sin throw React; texto visible — HEAD: React #31 |
| `AC-R196-07 · navegación` | `/masters` | enlaces a las 21 entidades — HEAD: solo farms |

### 1.2 `backend/tests/test_r196_masters_create_context.py`

| Nombre | Aserción que **falla en HEAD** |
|---|---|
| `test_r196_01_create_farm_sin_company_en_cuerpo` | 201 con company del contexto — HEAD: 422 |
| `test_r196_02_create_farm_no_acepta_company_ajena` | 4xx — HEAD: acepta/crea en otra empresa (según R-50) |
| `test_r196_03_create_house_verifica_padre` | 404 padre ajeno (verde) |

Ejecución: `npx vitest run …/r196.*`; `bash backend/scripts/run_tests.sh tests/test_r196_masters_create_context.py`; salidas a `evidence/red/`.

## 2 · Diseño E2E (C3)

| Caso | Pasos | Esperado |
|---|---|---|
| RT-01…03 | crear granja, galpón, planta, incubadora, nacedora por UI | 201 ×5; visibles en listado |
| RT-04 | capacity vacía | 201 |
| RT-05 | reactivar área | activa |
| RT-06 | duplicado/422 | mensaje seguro |
| RT-07 | navegar por todas las entidades desde `/masters` | alcanzables |
| RT-08 | sonda API: company ajena | denegado |

Artefactos: `evidence/r196/runtime-{red,c3}.json` + PNG; 0 `pageerror`.

## 3 · Plan UAT

| Caso | Acción | Esperado |
|---|---|---|
| UAT-R196-01 | Crear una granja nueva | Guardado; aparece |
| UAT-R196-02 | Crear un galpón dentro de ella | Guardado |
| UAT-R196-03 | Crear una planta y una incubadora | Guardado |
| UAT-R196-04 | Reactivar un ítem dado de baja; provocar un error (duplicado) | Reactivado; error legible sin pantalla en blanco |

Criterio: 4/4 (agrupable con R-215).
