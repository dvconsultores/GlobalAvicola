# GA-UAT-08 · R-188 / BU-D10 / OD-23 — REGISTRO DE OBSERVACIONES

Estado: **PENDIENTE DE LA DECISIÓN DEL PROPIETARIO** (sin aceptación pre-rellenada).

## 1 · Casos

| UAT ID | Resultado | Observación | Severidad | Captura | ¿Backlog existente? | ¿Candidato nuevo? | ¿Bloquea aceptación? | Comentario del propietario |
|---|---|---|---|---|---|---|---|---|
| UAT-01 acceso válido | PENDIENTE | — | — | C01 | — | — | — | — |
| UAT-02 apagar quita acceso | PENDIENTE | — | — | C02/C08 | — | — | — | — |
| UAT-03 re-encender no devuelve | PENDIENTE | — | — | C03 | — | — | — | — |
| UAT-04 concesión nueva restaura | PENDIENTE | — | — | C04/C04b/C05 | — | — | — | — |
| UAT-05 móvil | PENDIENTE | — | — | C07/C08 | — | — | — | — |

## 2 · Notas técnicas pre-registradas (informativas; no bloquean)

| # | Nota | Clasificación tentativa | ¿Bloquea? |
|---|---|---|---|
| N-1 | El operador sin unidad efectiva ve «Permiso requerido» en el inicio (sin `dashboard:read`); es el fallo cerrado existente del home para roles operativos, ajeno a R-188. | UX pre-existente | NO |
| N-2 | La consola del navegador quedó **sin errores** en todo el walkthrough (operador y admin). | — | NO |
| N-3 | Cualquier comentario del propietario sobre descubribilidad de la navegación de lotes se asociará a **OBS-UAT-01** (P2, UX), sin mezclarse con R-188. | Backlog existente | NO |

## 3 · Clasificación post-decisión (si Acepta con Observaciones)

Categorías: BUG · UX · COPY · ENHANCEMENT · DOCUMENTATION · OUT_OF_SCOPE. Severidad P0-P3 cuando aplique. **Nada se implementa durante el UAT.**
