# GA-FE-06 · ÍNDICE DE CAPTURAS

Directorio: `audit/ga-fe-06/evidence/`. Todas las capturas se tomaron contra la generación certificada `index-DcqmSs-R.js` (salvo las RED, indicadas).

## GREEN · desktop 1440×900 (operador C)

| Archivo | Contenido | Estado |
|---|---|---|
| `green/ds-02b-lot-form-selector-area-render.png` | Formulario de alta con el **selector «Área»** poblado (Nave Norte/Sur) y «Fecha prevista de cierre» | ASENTADA |
| `green/ds-01b-detail-e01-render.png` | Detalle lote 19 con la fila **«Fecha prevista de cierre | 2026-09-21»** | ASENTADA |
| `green/ds-01c-detail-final.png` | Detalle final (misma vista; verificación consolidada) | ASENTADA |
| `green/ds-03-validacion.png` | Fallo de validación («Mínimo 2 caracteres») sin alta | ASENTADA (estado estático tras submit) |
| `green/ds-04b-rbac-d-render.png` | Actor D en `/lots/new`: **«No tiene permiso para ver esta sección»** (fail-closed) | ASENTADA |
| `green/ds-05-cbu-e.png` | Actor E: alta rechazada por CBU (posterior al 403) | POST-ERROR (no asentada; la prueba es el 403 registrado) |
| `green/en-01b-alta-ingles-render.png` | Formulario en inglés: `PLANNED CLOSE DATE`, `Area`, `Select area...` | ASENTADA |
| `green/ds-01-detail-e01.png` · `ds-02-…` · `ds-04-…` · `en-01-…` | Primeras tomas (carrera de render «Cargando…») | **SUPERSEDED** (se conservan por trazabilidad) |

## GREEN · móvil 390×844 (operador C)

| Archivo | Contenido | Estado |
|---|---|---|
| `green/mb-01b-alta-movil-form.png` | Formulario móvil asentado con selector de área | ASENTADA |
| `green/mb-02b-detalle-movil.png` | Detalle móvil del lote 24 con `2026-09-12` | ASENTADA |
| `green/mb-01-alta-movil.png` | Primera toma (carrera) | **SUPERSEDED** |

## RED · generación de entrada `index-WUv1-F9o.js`

| Archivo | Contenido |
|---|---|
| `red/runtime-red.json` | Alta real como C con PLD rellenada: payload de 8 claves (sin `planned_close_date`/`area_id`), 201, fresh GET `null/null`, lista de controles sin área |
| `red/vitest-red-summary.txt` | Salida íntegra del RED de contrato (4 failed / 1 passed) |

## JSON de soporte

`green/runtime-green.json` (batería E2E) · `green/verify-focus.json` (correcciones con esperas + trazas 4xx) · `green/final-verify.json` (consolidado final: detalle limpio, reload, notificaciones, guard D, EN).
