# GA-FE-02-D · OD-16 GLOBAL ACTOR READ-BOUNDARY RECONCILIATION

**Baseline**: `f030a5d` (main == remoto; worktree limpio) · **Runtime**: `https://avicola.globaldv.net`
(bundle `index-B2-tZnkI.js`) · **Fecha**: 2026-09-11 · **Autoridad**: prompt GA-FE-02-D
(clasificación y reconciliación de `D-1` contra `OD-16`; sin GA-FE-03; sin cambios de producto
antes de clasificar).

---

## 1 · Finding/referencia y dedup

**`D-1`** nació en la evidencia de GA-FE-02-C como observación documentada:

> «Lectura del actor global sin row-scope (E). Con contexto c1, `GET /lots` del bootstrap
> devuelve 8 filas aunque las unidades estén OFF y sin concesión. No es un defecto nuevo ni un
> bypass: es la excepción declarada y certificada de `GA-REM-002`/`GA-REM-040` fase 3…»
> — `audit/ga-fe-02-a/GA_FE_02_A_E2E_MATRIX.md` (sección RESULTADOS REALES, D-1)

Esta tranche **reconcilia** esa declaración contra `OD-16`: ¿qué ES realmente la lectura?
¿control o dato productivo? (§2–§3 del encargo). Resultado de la reconciliación:

**`D-1` = `SECURITY_DEFECT`** (CASE 3, §8) — la lectura es **dato productivo** y la puerta de
habilitación por empresa **no puede ser saltada por el actor global**.

**Dedup**:

| Referencia previa | Relación |
|---|---|
| Declaración fase 3 (`masters/service._apply_business_unit_filter`, `d2a67f0`, 2026-09-07: «certificada en GA-REM-002 y esta fase no la reabre») | **Superada para LECTURAS productivas**: GA-REM-002 (2026-09-04) es certificación **anterior** a OD-16; una certificación vieja no anula una decisión posterior del propietario (§1 del encargo). |
| `A01_SUPER_ADMIN_SHORTCUT_VERIFICATION.md` (2026-09-09) — inventario de los 23 atajos; los de visibilidad clasificados «certificada (fase 3)» con **norma de contraste `OD-14`** (inquilino), no `OD-16` (puerta productiva) | Es el **inventario de implementación del mismo root**; sus veredictos de visibilidad para LECTURA productiva quedan revisados por esta reconciliación. |
| `R-163` (cerrado; cierra la **escritura** del actor global sobre unidades apagadas con `exigir_unidad_operativa`) | La escritura YA es OD-16-correcta («unidad ∈ habilitadas, o `no_habilitada`… la concesión no se le exige»). El borde de **lectura** quedó fuera de su alcance — es exactamente lo que esta tranche corrige. |
| `R-139 §6` (la concesión de usuario no se le exige al actor global) | **Se preserva**: el bypass que OD-16 permite («User BU grants») sigue vigente; lo que se cierra es el bypass de la **habilitación de empresa**. |
| `BU-D10` | Intacto (`PENDING_RATIFICATION`). |
| `F1/F2/F3/F4/D1(sesión)/R-98/R-119/R-181/R-182` | No se tocan. |

---

## 2 · Evidencia runtime (2026-09-11 · ENV-01 · empresa 1 · Actor E bootstrap situado)

**Estado del fixture en la captura: las CUATRO unidades de la empresa 1 en OFF** (confirmado
antes y después). Captura `GET /me`: `effective_business_units=[]`, `granted_business_units=[]`.

### 2.1 Exposición observada (actor global, CBU todas OFF)

| Superficie | Ruta exacta | Método | Status | Exposición |
|---|---|---|---|---|
| Lotes (lista) — **la ruta D-1** | `/api/v1/lots?limit=100` | GET | 200 | **8 filas productivas** (`L-2026-001`…, `bird_type` incluido) |
| Lote (detalle) | `/api/v1/lots/1` | GET | 200 | detalle de lote de unidad apagada |
| Fases del lote | `/api/v1/lots/1/phases` | GET | 200 | sub-recurso del lote |
| Eventos operativos (lista) | `/api/v1/operations?limit=100` | GET | 200 | **34 eventos** |
| Evento (detalle) | `/api/v1/operations/37` | GET | 200 | detalle de evento productivo |
| Alertas | `/api/v1/operations/alerts` | GET | 200 | 0 filas (sin alertas en el fixture) |
| Cola de revisión | `/api/v1/review/pending` | GET | 200 | **total=8 eventos** productivos |
| Panel (agregados) | `/api/v1/dashboard/admin` | GET | 200 | **total_events=34** + desglose por estado + pending_review=8 |
| KPIs de empresa | `/api/v1/reports/kpis` | GET | 200 | diccionario de indicators (valores nulos/vacíos en este fixture) |
| KPI por lote | `/api/v1/reports/kpis/mortality?lot_id=1` | GET | 200 | `initial_population/total_deaths/mortality_rate` del lote de una unidad apagada |

### 2.2 Control ON (broiler habilitada) — la excepción no es «habilitadas», es «sin filtro»

Con **solo broiler ON** la exposición fue **idéntica** (8 lotes, 34 eventos, 8 en revisión,
34 eventos en el panel): el atajo del actor global **anula todo el predicado de unidad**, no lo
recalcula sobre las habilitadas. Es decir: ni siquiera operaba como «bypass de concesiones» —
operaba como «sin puerta de empresa».

### 2.3 Baseline de actor de empresa (de la corrida GA-FE-02-C, `MX-1`)

Actor C (rol con `lots:read`), concesión viva, CBU OFF → `GET /lots` = **0 filas** (DENY).
La puerta de empresa YA funciona para actores de empresa; el hueco es exclusivo del actor global.

**Restauración**: broiler → OFF tras el control; estado final 4×OFF. Sin secretos en la captura.

---

## 3 · Especificaciones de gobierno

| Fuente | Mandato | Vigencia para este caso |
|---|---|---|
| **OD-16** (ratificado en esta tranche, §2 del encargo) | «CompanyBusinessUnit OFF is absolute for productive operations for ALL actors, including SuperAdmin… may NEVER bypass Company BU enabled gate for productive operations. Control plane may still administer disabled BU.» Distinguir **CONTROL-PLANE READ** vs **PRODUCTIVE DATA READ**. | **Gobierna** (decisión del propietario más reciente; el encargo la explicita y ratifica). |
| `AC-A05` · `OD-16.e/f` (implementación de escritura, `exigir_unidad_operativa`) | Autoridad global: `unidad ∈ habilitadas` o `no_habilitada`; la concesión de usuario NO se le exige (R-139 §6). | **Ya conforme** — es la semántica que la lectura debe espejar. |
| `GA-REM-002` (cert., 2026-09-04 · `AC09`) | «El Super Admin conserva su alcance» (5 módulos) — pre-fase-3, pre-OD-16. | **Anterior**: no puede anular OD-16 (§1/§15). Su lectura de «visibilidad total» aplica a **control**, no a dato productivo. |
| Fase 3 (2026-09-07) | row-scope de lotes con exención declarada del Super Admin «donde queda fuera del filtro de empresa». | **Superada en LECTURAS productivas** por OD-16 + esta ratificación. |
| `R-139 §6` · `AC-C14` | La autoridad global no necesita concesiones (bypass de grants). | **Se preserva** — el fix NO exige concesiones al global; solo la puerta de empresa. |
| `R-163` | Escrituras del global: `403` sobre unidad apagada. | **Sin cambio**; el fix alinea la lectura con esta misma semántica. |

---

## 4 · Cronología OD

```
2026-09-04  GA-REM-002 certificado (AC09: alcance del Super Admin preservado) — pre-capacidad BU
2026-09-07  GA-REM-040 fase 3 (d2a67f0): row-scope de lotes + exención declarada del Super Admin
2026-09-08/09 WAVE A0-P → OD-16: alcance productivo y activación por empresa formalizados
             (AC-A05; OD-16.e/f; BU-D10 separada a propósito)
2026-09-09  A01: verificación de los 23 atajos contra OD-14 (inquilino) — visibilidad de unidad
             clasificada «certificada (fase 3)»; lecturas productivas NO reevaluadas contra OD-16
2026-09-10+  WAVE B: matrices leen OD-16.e como absoluta para ESCRITURAS; R-163 cierra ese lado
2026-09-11  GA-FE-02-C: D-1 observado en runtime (documentado como excepción)
2026-09-11  GA-FE-02-D (esta tranche): el propietario ratifica la lectura absoluta TAMBIÉN para
             LECTURAS productivas, actor global incluido → D-1 = SECURITY_DEFECT → corrección
```

**Regla de jerarquía aplicada**: la decisión del propietario (OD-16, tal como queda ratificada)
prevalece sobre certificaciones anteriores (GA-REM-002) y sobre declaraciones de fase que se
apoyaban en ellas. «Previamente certificado» ≠ «vigente» cuando una decisión posterior lo
contradice.

---

## 5 · Ruta exacta (D-1) y familia del mismo root

**Ruta D-1 (la reportada)**: `GET /api/v1/lots?limit=100`
→ `app/lots/router.py::list_lots` → `LotService.get_lots` → `MasterService.get_all`
→ `_apply_company_filter` (aplica) + **`_apply_business_unit_filter`** (`masters/service.py:113`:
`if self.unidades is None or self.is_super_admin: return query` — **salta el predicado**)
→ devuelve filas `lots` de toda la empresa. Recurso devuelto: **lotes productivos**
(`lot_code`, `bird_type`, `status`, población, etc.). RBAC: `lots:read` (el comodín lo tiene).
Guardia de inquilino: aplica (empresa efectiva). Guardia de unidad: **ausente por el atajo**.

**Familia (mismo root = atajo `is_super_admin` sobre el alcance de unidad en LECTURA productiva)**:

| # | Sitio | Mecanismo | Superficie expuesta |
|---|---|---|---|
| 1 | `masters/service.py:113` | `or self.is_super_admin` → sin predicado | `/lots` lista y detalle (vía `MasterService`) + fases |
| 2 | `dashboard/service.py:25` | `return None` (sin subconsulta de lotes) | agregados del panel (empresa) |
| 3 | `review/service.py:139, 431, 642` | `return []` (sin predicado) | colas de revisión/aprobaciones/pasos |
| 4 | `reports/service.py:42` | `or is_super_admin: return` (sin alcanzabilidad) | KPI por lote de cualquier lote |
| 5 | `reports/service.py:62` | `return None` (sin filtro) | agregados KPI sin lote |
| 6 | `operations/service.py:978` | `return query` (sin filtro de unidades) | alertas |
| 7 | `operations/service.py:1026-1035` | `if not is_super_admin:` envuelve el predicado | listado de eventos |
| 8 | `operations/service.py:1088-1092` | ídem | detalle de evento |

(Corresponde al inventario `A01` sitios #18, #4, #1–3, #14–15, #5–7; allí clasificados con
norma `OD-14`; aquí se resuelven con norma `OD-16`.)

---

## 6 · Clasificación del dato

**`C. PRODUCTIVE_OPERATIONAL_READ`** — sin ambigüedad:

- `lots`: entidad productiva por excelencia (lleva `bird_type`; la cadena se deriva de ella).
- `operations`: eventos operativos (producción).
- `review/pending`: cola de eventos productivos.
- `dashboard`/`reports`: métricas productivas derivadas de lotes/eventos.
- **NO** es control-plane: el plano de control (selector de empresa, `/business-units`, usuarios,
  roles, auditoría, maestros de configuración) queda **fuera** de este hallazgo y **permanece
  disponible** para el actor global (OD-16: «Control plane may still administer disabled BU»).

---

## 7 · Experimento runtime (resumen — detalle en §2)

```
                    CBU TODAS OFF                     CBU BROILER ON (control)
/lots               200 · 8 filas productivas         200 · 8 filas (idéntico — sin filtro)
/operations         200 · 34 eventos                  200 · 34 eventos
/operations/37      200 · detalle                      —
/review/pending     200 · total 8                     200 · total 8
/dashboard/admin    200 · total_events 34             200 · total_events 34
/reports/kpis/mort  200 · KPI del lote 1 (OFF)        —
Actor de empresa C (MX-1, GA-FE-02-C): OFF → /lots = 0 filas (DENY) ✔
```

**Resultado**: con CBU OFF, **filas productivas devueltas: SÍ** (actor global). Dato productivo
legible con la puerta de empresa apagada ⇒ **CASE 3 (§8) = `SECURITY_DEFECT`**.

---

## 8 · Esperado vs real

| | Esperado (OD-16 ratificado) | Real (baseline `f030a5d`) |
|---|---|---|
| Global, OFF, superficie productiva | DENY (0 filas / 404) | **ALLOW** (8/34/8/34…) |
| Global, ON (p. ej. broiler) | alcance = **habilitadas** (bypass de concesión, no del gate) | ALLOW **sin filtro** (todas las unidades) |
| Actor de empresa | sin cambio (efectivas) | sin cambio ✔ |

---

## 9 · Conclusión de seguridad

**`SECURITY_DEFECT`** (`CASE 3`). La frase «previamente certificada» (fase 3 → GA-REM-002) **no**
anula OD-16 (§1/§15 del encargo). La lectura ES dato productivo (§6). El actor global **no puede**
saltar la puerta de habilitación por empresa; solo puede saltar la concesión de usuario (§3,
`R-139 §6`). Se corrige con spec-first, RED, fix mínimo, deploy y re-verificación de la matriz
afectada. **Sin hotfix.**

---

## 10 · Corrección: diseño mínimo, AC y tareas

### 10.1 Diseño (la semántica, una sola vez)

Nuevo resolutor central — espejo exacto de `exigir_unidad_operativa` (escritura, ya conforme):

```python
# app/business_units/service.py
async def unidades_de_alcance_productivo(db, *, current_user, company_id) -> list[str]:
    """Alcance de LECTURA productiva. OD-16 (GA-FE-02-D):
    - actor de empresa         → efectivas (habilitada ∧ concedida viva)  [sin cambio]
    - autoridad global         → habilitadas de la empresa (la concesión no se le exige,
                                 la habilitación jamás se salta)         [corrección]
    """
```

- Los seis servicios productivos lo consumen (mismos `_unidades()`/`_lotes()` de siempre).
- Se **elimina el atajo** `is_super_admin` en los ocho sitios de §5 (flip quirúrgico: el actor
  global pasa por el mismo camino que los demás; lo que cambia para él es la lista del resolutor).
- **`/me` NO cambia**: `effective_business_units` sigue siendo la vista de concesiones
  (`test_h13_la_autoridad_global_no_hereda_unidades_productivas` permanece verde — el contrato de
  sesión no se toca). El alcance productivo es un concepto de las superficies productivas.
- Escrituras (`R-163`) y plano de control: intactos.

### 10.2 AC

| AC | Criterio |
|---|---|
| `AC-D1-01` | Global · CBU OFF · `GET /lots` → **0 filas**; detalle → **404**; fases → **404** |
| `AC-D1-02` | Global · CBU broiler ON · `GET /lots` → **solo** lotes de broiler (bypass de concesión, no del gate) |
| `AC-D1-03` | Ídem en `/operations`, `/operations/{id}`, `/review/pending`, `/dashboard/admin`, `/reports/kpis*` |
| `AC-D1-04` | Actor de empresa: **sin cambio** de comportamiento (MX-1…4 de GA-FE-02-C siguen verdes) |
| `AC-D1-05` | `/me` sin cambio de contrato (effective = concesiones; global → `[]`) |
| `AC-D1-06` | Escritura global sobre unidad apagada sigue **403** (`R-163` sin regresión) |
| `AC-D1-07` | Plano de control intacto: selector/switch, `/business-units`, usuarios/roles/auditoría |
| `AC-D1-08` | RED ejecutado (runtime, §2) → GREEN ejecutado (runtime post-deploy) + test dirigido |

### 10.3 Tareas y orden de commits

| # | Tarea | Commit |
|---|---|---|
| T1 | Este artefacto de reconciliación (spec-first) | **SPEC (este)** |
| T2 | RED: test dirigido (ruteo del resolutor; ejecutable local) + captura runtime §2 ya ejecutada | |
| T3 | Fix: resolutor + 6 rewires + 8 remociones del atajo | **IMPL** |
| T4 | Test PG de frontera (CI): OFF→0, ON→habilitadas, control intacto | **IMPL** |
| T5 | Push → pipeline normal → deploy | |
| T6 | GREEN runtime: repetir §2 con expectativa OD-16 + MX spot con actor de empresa + F2/F3/F4/D1 | **EVIDENCE** |
| T7 | Actualizar evidencia GA-FE-02-C (D-1 pasa de «excepción declarada» a «defecto corregido») | **EVIDENCE** |

---

## 11 · Impacto en certificación

```
Mientras `D-1` esté sin corregir y sin re-verificar:
    GA-FE-02 = SECURITY_REMEDIATION_REQUIRED   ·   OWNER_UAT_READY = NO

Tras deploy + re-verificación verde de la matriz afectada (§10.3 T6):
    GA-FE-02 = FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING   ·   OWNER_UAT_READY = YES
```

`BU-D10` `PENDING_RATIFICATION` · `R-98/R-119/R-181/R-182` `UNCHANGED` · Wave B `PAUSED` ·
Wave C `NOT STARTED` · SAP `NOT STARTED` · **GA-FE-03: ELIGIBLE_BUT_NOT_STARTED (no iniciada)**.

---

## 12 · Referencias de evidencia

- Runtime (esta tranche): manifiesto OFF/ON y sondas de detalle — `/tmp/ga_d1_manifest.json`
  (destruido con los temporales al cierre) + tablas §2 de este artefacto.
- `audit/ga-fe-02-a/GA_FE_02_A_E2E_MATRIX.md` — D-1 original (sección RESULTADOS REALES)
  y MX-1 (baseline del actor de empresa).
- `backend/app/masters/service.py:113` · `backend/app/dashboard/service.py:25` ·
  `backend/app/review/service.py:139,431,642` · `backend/app/reports/service.py:42,62` ·
  `backend/app/operations/service.py:978,1026,1088` · `backend/app/business_units/service.py:255`
  (`exigir_unidad_operativa`, escritura conforme).
- `audit/remediation/GA_REM_040_PHASE_3_EVIDENCE.md` (excepción declarada; 2026-09-07) ·
  `audit/remediation/A01_SUPER_ADMIN_SHORTCUT_VERIFICATION.md` (inventario) ·
  `audit/remediation/GA-REM-002-003-CERTIFICATION-REPORT.md` (AC09; 2026-09-04) ·
  `audit/remediation/R163_R162_LOTS_AND_EVIDENCE_BU_AUTHORITY_MATRIX.md` ·
  `audit/remediation/BUSINESS_UNIT_OWNER_DECISION_MATRIX.md` (OD-16 · BU-D10).

---

## 13 · Resultado runtime post-deploy (GREEN) — 2026-09-11

**Deploy por pipeline normal**: push `9ffc5ec` → imagen backend → Watchtower → contenedor
reemplazado (arranque con `alembic upgrade head`, `GA-REM-024`). Sin pasos manuales.

### 13.1 Batería OD-16 (actor global situado en empresa 1, todas las unidades OFF) — **21/21 PASS**

| Comprobación | Resultado |
|---|---|
| `/me` sin cambio de contrato | `effective=[] · granted=[]` ✔ |
| `GET /lots` | **0 filas** (antes 8) |
| `GET /lots/1` · `GET /lots/1/phases` | **404** (antes 200) |
| `GET /operations` | **0 filas** (antes 34) |
| `GET /operations/37` | **404** (antes 200) |
| `GET /review/pending` | **total 0** (antes 8) |
| `GET /dashboard/admin` | **total_events 0** (antes 34) |
| `GET /reports/kpis/mortality?lot_id=1` | **404** (antes 200) |
| Plano de control | `/business-units` 4 · `/users` 200 · `/roles` 14 — **intacto** |
| **ON control (broiler)** | `/lots` = **solo** `L-BO-2026-05/06` (`bird_type=broiler`) · `/operations` 7 (antes 34) · `/review/pending` 0 · `/dashboard/admin` 7 (antes 34) · lote fuera de alcance → **404** |
| Restauración | broiler → OFF; `GET /lots` → 0 de nuevo |

### 13.2 Matriz afectada con actor de empresa (fixture normal re-provisionado) — **12/12 PASS**

`MX-2` ON / sin concesión / RBAC sí → **DENY (0 filas)** · `MX-4` ON / concesión viva / RBAC sí →
**ALLOW (2 filas `L-BO-2026-05/06`)** · fixture restaurado por completo (C2 dado de baja, rol 37
desactivado, CBU 4×OFF). **AC-D1-04** (actor de empresa sin cambio) verificado.

### 13.3 Spots de no-regresión

`POST /lots` del global sobre unidad apagada → **403** (R-163 intacta · `AC-D1-06`) ·
F2 `GET /roles` = 14 con rol 35 exacto · F3 `GET /users` 200 · bundle `index-B2-tZnkI.js` estable
(frontend sin tocar) · D1/F4 sin cambios (no se tocó frontend).

### 13.4 AC — cierre

`AC-D1-01` ✔ · `AC-D1-02` ✔ · `AC-D1-03` ✔ · `AC-D1-04` ✔ · `AC-D1-05` ✔ · `AC-D1-06` ✔ ·
`AC-D1-07` ✔ · `AC-D1-08` ✔ (RED ejecutado pre-fix; GREEN ejecutado post-deploy; test dirigido
nuevo `tests/test_od16_global_read_boundary.py` — ruteo puro ejecutado local 1/1 + frontera PG
para CI).

### 13.5 Veredicto

```
D-1 .................. CORREGIDO Y VERIFICADO (OD-16)
Productive rows while OFF ........ 0 (era 8/34/8/34)
GA-FE-02 ............. FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING
OWNER_UAT_READY ...... YES · OWNER_ACCEPTANCE: PENDING (solo el propietario)
BU-D10 ............... PENDING_RATIFICATION · R-98/R-119/R-181/R-182 UNCHANGED
Wave B PAUSED · Wave C/SAP NOT STARTED · GA-FE-03 ELIGIBLE_BUT_NOT_STARTED
```
