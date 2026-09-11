# GA-UAT-07 · R-187 — REGISTRO DE OBSERVACIONES DEL PROPIETARIO

Estado: **PENDIENTE DE LA DECISIÓN DEL PROPIETARIO** (no se pre-rellena aceptación alguna).

## 1 · Casos (a completar con la respuesta del propietario)

| UAT ID | Resultado | Observación | Severidad | Captura | ¿Backlog existente? | ¿Candidato nuevo? | ¿Bloquea aceptación? | Comentario del propietario |
|---|---|---|---|---|---|---|---|---|
| UAT-01 nuevo valor IPE | PENDIENTE | — | — | UI-C01/C02 | — | — | — | — |
| UAT-02 claridad de clasificación | PENDIENTE | — | — | UI-C01/C07 | — | — | — | — |
| UAT-03 detalle/reporte | PENDIENTE | — | — | UI-C01/C03 | — | — | — | — |
| UAT-04 refresh/relogin | PENDIENTE | — | — | UI-C04/C05 | — | — | — | — |
| UAT-05 móvil | PENDIENTE | — | — | UI-C06 | — | — | — | — |
| UAT-06 aceptación global | PENDIENTE | — | — | — | — | — | — | — |

## 2 · Notas técnicas pre-registradas (no bloquean; informativas para calibrar la sesión)

| # | Nota | Clasificación tentativa | ¿Bloquea? |
|---|---|---|---|
| N-1 | En el reporte de un lote de **engorde** aparece el aviso amarillo «los indicadores se calculan solo con datos aprobados» — proviene del KPI de **Incubadora** (`insufficient_data`), pre-existente (GA-REM-022 AC05) y ajeno a R-187. En la guía se explica al propietario para evitar confusión. | COPY/UX pre-existente | NO |
| N-2 | Durante el walkthrough, el operador mínimo genera **403 silenciosos** en widgets opcionales (permisos que no tiene); no hay errores fatales de página (0 `pageerror`) y la tarjeta IPE y el reporte funcionan. Comportamiento de gobierno existente. | Técnico esperado | NO |
| N-3 | El valor legado del lote 11 (`L-BO-2026-05`) muestra 5.6 con su FCR simplificado (limitación documentada, independiente de OD-22) — solo como contexto de transición; no forma parte de los casos. | Documentación | NO |

## 3 · Clasificación post-decisión (a completar si el propietario acepta con observaciones)

Categorías permitidas: BUG · UX · COPY · ENHANCEMENT · DOCUMENTATION · OUT_OF_SCOPE. Severidad P0/P1/P2/P3 cuando aplique. **Nada se implementa dentro del UAT.**
