# GA-CLAUDE · CERTIFICACIÓN RUNTIME — R-198: EVIDENCIAS DEL DETALLE, GATE Y BORRADO ATÓMICO

Fecha: 2026-09-14 · Paquete: `specs/R-198/` · HEAD de partida: `56d0fcb` (T7 cerrada).

## 1 · Ejecución por ciclos

| Ciclo | Commits | Resultado |
|---|---|---|
| **C1 · RED** | `dc69375` | `test_r198_evidences_contract.py`: **BE 5F/2P** — detalle `[]` (01/02), sin gate (03: 201/204 en `approved`), orden `['remove','commit']` (05), almacenamiento descartado (07); controles 04 (auditoría, ya cubierta por P1-12/T-06) y 06 verdes. FE `r198.evidenceContract.test.tsx`: **3F/1P** — sin refetch (02), sin gate (03), `opacity-0` en acciones (07). |
| **C2 · Implementación** | `244ab43` | BE: `GET /operations/{id}` devuelve `evidences` y `egg_storage_records` (C-01=A, C-04); gate por estado en servidor (`EDITABLES`, C-02 — 400 con mensaje); borrado físico **después** del commit (C-03). FE: relee del servidor tras subir/borrar (nada optimista), gate espejo de los estados editables y acciones visibles en táctil (R3). **BE 7/7** · regresión 122/122 · **FE 394/394** + `tsc` 0. |
| **C2s · Sensibilidad** | `5b8b865` | S1 (detalle sin evidencias/almacenamiento): 3F. S2 (remove antes de commit): 1F. S3 (sin gate): 1F. |
| **C3 · Runtime** | — | En ventana (familia G-06): RT-01…05 del diseño (subir/F5, relogin, gate, auditoría, borrado). |

## 2 · Criterios de aceptación

| AC | Estado | Evidencia |
|---|---|---|
| AC-R198-01 subir ⇒ visible tras F5 | ✅ | `test_r198_01` (detalle devuelve; S1 lo rompe) |
| AC-R198-02 relogin ⇒ visible | ✅ | `test_r198_02` |
| AC-R198-03 estado no editable ⇒ denegado en servidor | ✅ | `test_r198_03` (400 en `approved`; S3 lo rompe) + FE 03 |
| AC-R198-04 alta/baja auditadas | ✅ | `test_r198_04` (control integrado con P1-12/T-06) |
| AC-R198-05 borrado sin pérdida en fallo | ✅ | `test_r198_05` (orden `commit→remove`; S2 lo rompe) |
| AC-R198-06 ruta dedicada intacta | ✅ | `test_r198_06` (control) |
| AC-R198-07 táctil: acciones visibles | ✅ | FE 07 (sin `opacity-0`) |
| AC-R198-08 sin migración/endpoint/permiso | ✅ | `git diff --stat` |
| AC-R198-09 regresión | ✅ | 122/122 (BE) + 394/394 (FE) |

## 3 · Límites declarados

- **C3 runtime** en ventana: el contrato está demostrado a nivel API-integrada (BE) y jsdom (FE) con la misma forma de respuesta.
- La UI conserva la ruta dedicada `GET /{id}/evidences` (la del detalle es la fuente de la pantalla).
- **UAT mínima** (UAT-01/02 del diseño) se recoge en la pasada runtime con el propietario (captura F5/gate).

## 4 · Veredicto

**R-198 = `CLOSED_TECHNICALLY`** — la evidencia subida sobrevive a F5 y relogin por contrato; el estado no editable se deniega en servidor y la UI es espejo; el borrado es atómico (fila y fichero tras commit) y auditado. **P-09 reparado técnicamente** en su superficie de evidencias.
