# R-198 · DISEÑO DE PRUEBAS RED · E2E · UAT

HEAD `c0b4afc` · Sin implementación en este documento.

## 1 · Diseño RED

`backend/tests/test_r198_evidences_contract.py` (PG de pruebas; evento con adjunto sembrado; estados editables y no editables).

| Nombre | Pasos | Aserción que **falla en HEAD** |
|---|---|---|
| `test_r198_01_detalle_devuelve_evidencias` | subir evidencia; `GET /operations/{id}` | `evidences` con la fila — HEAD: `[]` |
| `test_r198_02_estado_no_editable_deniega` | evento `approved`; `POST /evidences` y `DELETE` | 400/403 — HEAD: 200 |
| `test_r198_03_alta_auditada` | subir | fila `UPDATED`/evidencia — HEAD: 0 |
| `test_r198_04_baja_auditada` | borrar | fila — HEAD: 0 |
| `test_r198_05_borrado_no_pierde_fichero` | forzar fallo de commit tras borrado (monkeypatch) | fichero y fila coherentes — HEAD: fichero perdido |
| `test_r198_06_ruta_evidencias_control` | `GET /operations/{id}/evidences` | 200 con la fila (verde) |

UI (jsdom si el arnés lo permite; si no, verificación E2E): recarga del detalle muestra evidencias del servidor; botones ocultos en estado no editable; visibilidad táctil (clase sin `opacity-0` en el contenedor táctil).

Ejecución: `bash backend/scripts/run_tests.sh tests/test_r198_evidences_contract.py` ⇒ rojos exactos; salida a `evidence/red/`.

## 2 · Diseño E2E (C3)

| Caso | Pasos | Esperado |
|---|---|---|
| RT-01 | subir adjunto en evento editable (UI local) | visible; F5 ⇒ visible |
| RT-02 | relogin (nueva sesión) | visible |
| RT-03 | evento aprobado: intentar subir/borrar | impedido en UI + denegado en servidor (sonda) |
| RT-04 | borrar en editable | desaparece; fila de auditoría consultable |
| RT-05 | móvil 390×844: subir/descargar/borrar | botones visibles y usables |

Artefactos: `evidence/r198/runtime-{red,c3}.json` + PNG. Invariantes: 0 `5xx`; fichero presente en disco tras RT-01 (coherencia con R-52).

## 3 · Plan UAT

| Caso | Acción | Esperado |
|---|---|---|
| UAT-R198-01 | Subir un archivo, refrescar la página | El archivo sigue ahí |
| UAT-R198-02 | Intentar adjuntar en un registro aprobado | Impedido con mensaje |

Criterio: 2/2 (5 min).
