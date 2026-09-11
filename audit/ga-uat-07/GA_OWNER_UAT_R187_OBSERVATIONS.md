# GA-UAT-07 · R-187 — REGISTRO DE OBSERVACIONES DEL PROPIETARIO

Estado: **DECISIÓN REGISTRADA — A) ACEPTO R-187 (2026-09-11)** · sin observaciones del propietario.

## 1 · Casos (resultado con la respuesta del propietario)

| UAT ID | Resultado | Observación | Severidad | Captura | ¿Backlog existente? | ¿Candidato nuevo? | ¿Bloquea aceptación? | Comentario del propietario |
|---|---|---|---|---|---|---|---|---|
| UAT-01 nuevo valor IPE | **PASS** | — | — | UI-C01/C02 | — | — | NO | Aceptación global A |
| UAT-02 claridad de clasificación | **PASS** | — | — | UI-C01/C07 | — | — | NO | Aceptación global A |
| UAT-03 detalle/reporte | **PASS** | — | — | UI-C01/C03 | — | — | NO | Aceptación global A |
| UAT-04 refresh/relogin | **PASS** | — | — | UI-C04/C05 | — | — | NO | Aceptación global A |
| UAT-05 móvil | **PASS** | — | — | UI-C06 | — | — | NO | Aceptación global A |
| UAT-06 aceptación global | **PASS (A)** | — | — | — | — | — | NO | «ACEPTO R-187» |

## 2 · Notas técnicas pre-registradas (no bloquean; informativas para calibrar la sesión)

| # | Nota | Clasificación tentativa | ¿Bloquea? |
|---|---|---|---|
| N-1 | En el reporte de un lote de **engorde** aparece el aviso amarillo «los indicadores se calculan solo con datos aprobados» — proviene del KPI de **Incubadora** (`insufficient_data`), pre-existente (GA-REM-022 AC05) y ajeno a R-187. En la guía se explica al propietario para evitar confusión. | COPY/UX pre-existente | NO |
| N-2 | Durante el walkthrough, el operador mínimo genera **403 silenciosos** en widgets opcionales (permisos que no tiene); no hay errores fatales de página (0 `pageerror`) y la tarjeta IPE y el reporte funcionan. Comportamiento de gobierno existente. | Técnico esperado | NO |
| N-3 | El valor legado del lote 11 (`L-BO-2026-05`) muestra 5.6 con su FCR simplificado (limitación documentada, independiente de OD-22) — solo como contexto de transición; no forma parte de los casos. | Documentación | NO |

## 3 · Clasificación post-decisión

**Sin observaciones del propietario** (decisión A limpia) ⇒ nada que clasificar. N-1…N-3 permanecen como notas informativas: no bloquean, no generan finding y no se implementan en esta tranche.
