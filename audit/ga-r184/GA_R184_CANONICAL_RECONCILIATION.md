# GA-R184 · RECONCILIACIÓN CANÓNICA — KPI/IPE: semántica temporal + HTTP 500

Baseline de entrada: `main` `2dc10b7` == remoto · producto frontend+backend `5a5bb3f` · bundle `index-BUthrUt9.js`
(Última modificación 2026-09-11 15:46:08 GMT) · runtime https://avicola.globaldv.net.

## 1 · Síntoma original y primera evidencia

| Elemento | Verdad |
|---|---|
| Origen | Certificación **GA-FE-06** (n-2 candidato) → registrado como **R-184** (P2 propuesto, ex N-2) en el backlog |
| Prueba viva original | `GET /reports/kpi/ipe/19` → **500** con actor temporal `reports:read`; controles `weight-uniformity/19` y `kpis?lot_id=19` → 200 (documentado en `audit/ga-fe-06/GA_FE_06_FINDINGS.md` §N-2) |
| Hipótesis reportada | «`date - datetime` o tipos temporales incompatibles» — **histórica, no vinculante**; verificada aquí contra código y runtime |
| Ruido asociado | Consola del detalle de lote: tarjetas KPI sin permiso (403, clase N-3) — **ajeno a R-184** |

## 2 · Endpoint afectado (traza real, no reportada)

| Elemento | Valor |
|---|---|
| Método y ruta | `GET /api/v1/reports/kpi/ipe/{lot_id}` (`app/reports/router.py`, prefijo `/reports`) |
| Permiso | `require_permission("reports", "read")` — **exacto**, sin comodines nuevos |
| Parámetro | `lot_id` (path, entero) |
| Modelo de éxito | `dict` plano (`lot_id`, `viabilidad_pct`, `avg_weight_g`, `ganancia_diaria_g`, `age_days`, `fcr`, `ipe`, `reference`) |
| Modelos de error | 401 sin sesión · 403 sin permiso · **404 «Lote no encontrado»** para lote inexistente o fuera de alcance (anti-enumeración, `_exigir_lote`) · 500 solo por fallo no controlado |
| Servicio | `ReportsService.get_kpi_ipe` (`app/reports/service.py`) |
| Definición citada | Docstring del router (G-06) y del servicio: `IPE = (Viabilidad% × Ganancia_Diaria_g × 100) / (FCR × 10)` |

## 3 · Ubicación exacta del fallo

`app/reports/service.py::get_kpi_ipe`:

```python
age_days = (date.today() - lot.start_date).days if lot and lot.start_date else 30
```

- `date.today()` → `datetime.date`.
- `lot.start_date` → `app/masters/models.py::Lot.start_date`: `Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)` → **`datetime` con zona** (remoto PostgreSQL `timestamptz`).
- Resta `date − datetime` ⇒ **`TypeError: unsupported operand type(s) for -: 'datetime.date' and 'datetime.datetime'`** ⇒ 500.

**Por qué pasó desapercibido**: los lotes sin `start_date` caen al valor 30 (rama `else`), y toda alta nueva fija `start_date` — el defecto golpea exactamente a los lotes reales.

## 4 · Reproducción (evidencia ejecutada, baseline actual)

| Prueba | Resultado | Artefacto |
|---|---|---|
| Runtime autenticado: `GET /reports/kpi/ipe/35` · `/33` (actor global, empresa 1 efectiva, BU broiler ON temporal) | **500** ×2 | `evidence/red/runtime-red.json` |
| Controles `kpis?lot_id=35` · `weight-uniformity/35` | **200 / 200** | íd. |
| Hermano G-05 `kpis/production-index?lot_id=35` | **500** (misma clase, hallazgo separado → §7) | íd. |
| `ipe/999999` | **404** «Lote no encontrado» (no 500) | íd. |
| Reproducción local determinista de la expresión exacta (modelo real, sin BD) | **TypeError** exacto; post-normalización: `19` | `evidence/red/typeerror-local.txt` |
| Suite RED canónica | `backend/tests/test_r184_ipe_date_semantics.py` (PG; skip local declarado, CI) | commit C1 |

## 5 · Respuesta esperada canónica y significado de negocio

- Éxito 200 con el esquema actual (sin cambios de forma): `ipe` redondeado a 1 decimal; `age_days` entero de **días de calendario**.
- IPE = índice productivo Europeo (G-06): combina viabilidad, ganancia diaria y FCR. Su base temporal es el **día de calendario del lote** (edad), según la convención ya canonizada en el repositorio (`R-75` / `GA-REM-028`, `lots/service.py:379`, `operations/service.py:776`).

## 6 · Severidad, alcance y criterio de cierre

- **Severidad: P2** — un KPI de usuario final responde 500 para todo lote con `start_date` (todos los lotes reales) a cualquier actor con `reports:read`; la tarjeta IPE desaparece en el detalle de lote y en el reporte de lote.
- **Alcance R-184**: única expresión a corregir = `get_kpi_ipe`. Sin cambios de fórmula, esquema, permisos, endpoints, migraciones ni frontend.
- **Criterio de cierre**: 500 original resuelto con causa raíz demostrada; valor determinista verificado; estados de negocio inválidos controlados (404/403/0.0 documentados, nunca 500); seguridad intacta (tenant/BU/RBAC/OD-16); regresión GA-FE-02..07 PASS; runtime E2E-01..12 PASS.

## 7 · Hallazgos hermanos registrados (NO implementados en esta tranche)

| Candidato | Descripción | Evidencia | Estado |
|---|---|---|---|
| **R-186 (propuesto)** | `GET /reports/kpis/production-index` (G-05) tiene la **expresión idéntica** (`service.py:601`, `date.today() - lot.start_date`) ⇒ 500 con lote con `start_date`. Misma clase que R-184. API-only (sin consumidor frontend hoy) | `runtime-red.json` caso `prodindex35` = 500 | **REGISTRADO — SEPARATE_OPEN** (por regla de alcance §4: «si aparece otro defecto KPI, registrar por separado; no ampliar R-184 automáticamente») |
| **Observación de negocio (candidata OBS)** | La fórmula implementada (documentada en router+servicio) produce valores ~100× la escala de las bandas de referencia del propio response (`>300/250/200`) — el Índice de Producción Europeo estándar divide viabilidad en % entre (FCR × 10) sin el ×100 extra. **No se toca**: cambiar fórmula/semántica es decisión de negocio ajena a R-184 | Cálculo independiente con constantes de fixture | **REGISTRADA — OWNER_DECISION_REQUIRED (no bloquea R-184)** |

## 8 · Dedup explícito (sin conflictos de propiedad)

| Finding | Tema | Relación con R-184 |
|---|---|---|
| R-176 | paridad de re-validación en edición de operaciones (`service.py:1071-1088`) | Ninguna — otro módulo, otra causa |
| R-178 | linaje `egg_batches`/`chick_batches` al cancelar/mover | Ninguna |
| R-130 | decremento de aves (cerrado técnico) | Ninguna |
| R-168 | `sample_size` en recepción (cerrado) | Ninguna |
| R-182 | `planned_close_date` en contrato de lote (CLOSED_OWNER_ACCEPTED) | Ninguna — el defecto no involucra `planned_close_date` (se usa en SLA, no en IPE) |
| R-179/R-98/R-119/R-181/R-185 | gobernanza previa | Sin reapertura |
| Findings de reportes/KPI previos | no existe finding previo que cubra el 500 de IPE | **R-184 es propio y separado** (dueño único confirmado) |
