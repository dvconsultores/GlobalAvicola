# GA-R187 · RECONCILIACIÓN DE CIERRE (AC01-AC52 → evidencia)

Fecha: 2026-09-11 · Commits: C1 `5a32a6c` · C2 `f755baa` · Evidencia: `evidence/green/` · Generación certificada: C2 (probe `ipe/11 = 5.6`).

## 1 · Respuestas explícitas (§68)

| Pregunta | Respuesta |
|---|---|
| Extra ×100 removed | **YES** |
| Canonical formula | **PASS** (`(viab% × gain)/(fcr×10)`) |
| Viability scale | **0-100 CONFIRMED** |
| ADG unit | **g/day CONFIRMED** |
| FCR | **PRESERVED** |
| Bands | **PRESERVED** |
| 250 behavior | **PRESERVED** (250.0 → 🟡; 249.9 → 🔴) |
| 300 behavior | **PRESERVED** (300.0 → 🟢) |
| Date semantics | **PRESERVED** |
| R-184 | **PRESERVED (técnica) / valor 556.6 SUPERSEDED_BY_OD22** |
| R-186 | **PRESERVED** (G-05 = 5.1 estable) |
| Frontend value | **PASS** (333.3 visible) |
| Detail/report | **CONSISTENT** |
| Security | **PASS** |
| Migration | **NONE** |
| Residual | **NONE** (fixtures retenidos documentados; actores/cred fuera) |

## 2 · AC01-AC52

| AC | Estado | Evidencia |
|---|---|---|
| AC01 OD-22 autoridad | **PASS** | reconciliation §1-2; spec §2 |
| AC02 distinción R-184/R-186 | **PASS** | reconciliation §1/§8 |
| AC03/AC04 fórmulas doc | **PASS** | reconciliation §2; spec §4-5 |
| AC05 unidades probadas | **PASS** | unit trace §1-4 + runtime (95.0/105.26/3.0) |
| AC06 ×100 eliminado | **PASS** | diff C2 + `ipe 333.3 ≠ 33333.3` (suite) + runtime |
| AC07 forma canónica | **PASS** | `service.py` C2 |
| AC08 sin otros cambios | **PASS** | diff 24+/8− (solo fórmula+docstrings+1 aserción) |
| AC09/AC10/AC11 fuentes intactas | **PASS** | diff; runtime viab/gain/fcr esperados |
| AC12 edad/fecha intacta | **PASS** | runtime age 19/110 exactos; `_dia()` sin diff |
| AC13 bandas intactas | **PASS** | sin diff bandas; fronteras exactas PASS |
| AC14 labels intactos | **PASS** | sin diff i18n; UI «Excelente» observada |
| AC15 frontera 250 | **PASS** | B249 249.9 🔴 · B250 250.0 🟡 |
| AC16 frontera 300 | **PASS** | B300 300.0 🟢 |
| AC17 sin umbral nuevo | **PASS** | grep umbrales: solo 300/250 existentes |
| AC18 consistencia UI/backend | **PASS** | detalle=reporte=333.3; banda por comparador espejo |
| AC19…AC23 fechas | **PASS** | E2E-06; controles suite (skip declarado local) |
| AC24 determinista == independiente | **PASS** | 333.3 exacto (5 casos con esperado a mano) |
| AC25 esperado no derivado del producto | **PASS** | cálculo a mano en RED/UNIT_TRACE + suite |
| AC26 redondeo intacto | **PASS** | 1d (5.6/241.1/282.7/249.9/250.0/300.0 exactos) |
| AC27/AC28 NaN/Infinity | **PASS** | 0 en toda la batería |
| AC29 cero/faltante controlado | **PASS** | lotes 33/35 → 0.0; guarda fcr |
| AC30 detalle valor nuevo | **PASS** | UI 333.3 + captura |
| AC31 reporte igual | **PASS** | 333.3 + captura |
| AC32 clasificación correcta | **PASS** | 🟢/🟡/🔴 por valor OD-22 |
| AC33 refresh estable | **PASS** | 333.3 tras reload |
| AC34 relogin estable | **PASS** | 333.3 tras sesión nueva |
| AC35 móvil usable | **PASS** | 390×844, overflow 0, captura |
| AC36 sin error crudo | **PASS** | sin «Internal Server Error»/«Lote no encontrado» en pantallas válidas |
| AC37 lote ajeno | **PASS** | 404 op→14 |
| AC38 BU OFF denegado | **PASS** | 404 (empresa y global) |
| AC39 sin concesión | **PASS** | 404 ra187nobu |
| AC40 sin RBAC | **PASS** | 403 ra187noperm |
| AC41 global no evade BU OFF | **PASS** | 404 admin con BU OFF |
| AC42 sin fuga cross-tenant | **PASS** | negativos sin cuerpo de datos |
| AC43 R-184 500 fix preservado | **PASS** | 200 en todos los lotes |
| AC44 fechas R-184 | **PASS** | age 110/19; start 2026-05-24 |
| AC45 contrato R-184 (sin congelar 556.6) | **PASS** | claves íntegras; 5.6 == OD-22 |
| AC46 R-186 G-05 | **PASS** | 200 · 5.1 (certificado) |
| AC47 R-185/área inactiva | **PASS** | spot 400 «Área inactiva»/BR-07 |
| AC48…AC50 GA-FE-05/06/07 | **PASS (spot)** | sin diff en superficies; GA-FE-07 verificado |
| AC51 OBS-UAT-01 sin tocar | **PASS** | sin cambios |
| AC52 BU-D10 sin decisión | **PASS** | sin cambios |

## 3 · Veredicto

**Todos los AC críticos PASS ⇒ R-187: CLOSED (técnico), FUNCTIONALLY_CERTIFIED; Owner UAT REQUIRED/READY; acceptance PENDING.**
