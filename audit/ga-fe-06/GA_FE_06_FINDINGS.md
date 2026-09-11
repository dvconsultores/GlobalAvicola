# GA-FE-06 · HALLAZGOS NUEVOS (registrados, NO corregidos en esta tranche)

Disciplina de alcance: R-182 es un defecto **de frontend** (pérdida silenciosa en el alta). Los hallazgos siguientes aparecieron **durante** la certificación, son **preexistentes**, y por §15/§31 (no expandir alcance automáticamente) se **registran con evidencia viva** para decisión del programa. Ninguno bloquea el cierre de R-182.

## N-1 · `R-183` CANDIDATO (P2) — el alta/edición de lote acepta `area_id` de **otra empresa**

| Elemento | Verdad |
|---|---|
| Prueba viva | `POST /api/v1/lots` como C (empresa 1) con `area_id:3` (área de la empresa 3) → **201** y persistido (lote 18 `GA6-XT-CHECK-1`, fresh GET `area_id:3`) |
| Código | `lots/service.py` línea ~205: `area_id=getattr(data, "area_id", None)` — **sin guarda de inquilino**; el `farm_id` sí tiene guarda de empresa (403). `LotUpdate` también expone `area_id` (misma ausencia) |
| Capas que SÍ protegen | Selector UI filtra (solo áreas propias); `GET /masters/areas` acotado al inquilino (ids [1,2] para C); el detalle no muestra área, y el SLA filtra destinatarios por `company_id` — no se demostró lectura cruzada |
| Impacto | Referencia cruzada persistida (integridad + superficie futura de fuga si alguna vista renderiza el área ajena) |
| Recomendación | Guarda simétrica a la de granja en `create_lot` y `update_lot` (403/404) + test PG en CI. Tranche propia (backend-only) |
| Evidencia | `evidence/red/…` no aplica; captura cruda en `/tmp/ga06_xt.json` (lote 18) y registro en `runtime-green.json`/`verify-focus.json` |

## N-2 · `R-184` CANDIDATO (P2) — `GET /reports/kpi/ipe/{lot}` → **500** con lote recién creado

| Elemento | Verdad |
|---|---|
| Prueba viva | Con `reports:read` temporal para C: `GET /reports/kpi/ipe/19` → **500** (lote con `start_date`); `weight-uniformity/19` y `kpis?lot_id=19` → 200 |
| Causa raíz (código) | `reports/service.py::get_kpi_ipe`: `age_days = (date.today() - lot.start_date).days` — resta `datetime.date − datetime aware` ⇒ **TypeError** cuando hay `start_date`; sin él usa 30 (por eso pasó desapercibido) |
| Alcance | Cualquier lote nuevo (todo alta fija `start_date`) visto por un rol con `reports:read` |
| Recomendación | Normalizar a fecha de negocio (`lot.start_date.date()` o `reference_today()`) + test. Tranche propia |
| Evidencia | Reproducción curl documentada; ruido de consola `ds-01c`/`final-verify.json` |

## N-3 · Observación (ruido preexistente) — el detalle de lote llama KPIs sin permiso

— `LotDetailPage` solicita `reports/kpis`, `kpi/ipe`, `kpi/weight-uniformity` incondicionalmente; para roles sin `reports:read` el backend responde **403** (3 errores de consola por vista). NO es de GA-FE-06 (vista preexistente; backend intacto). Recomendación: condicionar las tarjetas al permiso (patrón GA-FE-04 `useCan`). P3 propuesto.

## N-4 · Observación — granularidad de auditoría del alta

— `GET /audit?module=lots` registra la creación con `new_values` = `lot_code`/`bird_type` (los campos gobernados por OD-08 —`planned_close_date`/`area_id`— no quedan en el diff de la entrada). La traza de creación **existe** (AC-38 ✓); ampliar `new_values` sería mejora de trazabilidad. P3 propuesto.

## Declaración de no-intervención

Ninguno de los cuatro se corrigió aquí: N-1/N-2 son backend (el enunciado de R-182 no los contiene y tocar backend invalidaría el resultado «0 cambios backend» declarado para esta tranche), y N-3/N-4 son observaciones de UX/trazabilidad. Quedan listados para el backlog con evidencia reproducible.
