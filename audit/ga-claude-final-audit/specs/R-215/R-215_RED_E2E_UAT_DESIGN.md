# R-215 · DISEÑO DE PRUEBAS RED · E2E · UAT

HEAD `c0b4afc` · Sin implementación en este documento.

## 1 · Diseño RED

`frontend/src/components/__tests__/r215.errorRendering.test.tsx` (jsdom; mock api).

| Nombre | Pasos | Aserción que **falla en HEAD** |
|---|---|---|
| `AC-R215-01 · maestros 422 ⇒ texto` | montar `MasterListPage`; guardar con 422 lista | `screen.getByText(/campo:/)` — HEAD: throw React #31 |
| `AC-R215-02 · lotes/trazabilidad/perfil` | montar cada uno con 422 lista | texto visible — HEAD: throw |
| `AC-R215-03 · usuarios` | montar con 422 | sin «[object Object]» — HEAD: alert |
| `AC-R215-04 · boundary` | renderizar componente que lanza; verificar recuperación | pantalla de recuperación con botón — HEAD: no existe boundary |

Ejecución: `npx vitest run src/components/__tests__/r215.*` ⇒ rojos exactos; salida a `evidence/red/`.

## 2 · Diseño E2E (C3)

| Caso | Pasos | Esperado |
|---|---|---|
| RT-01 | Maestros ▸ nuevo ▸ solo nombre ▸ guardar (repro C#6) | mensaje legible; app usable |
| RT-02 | Forzar 422 en alta de lote (sap_reference/otro) | toast seguro |
| RT-03 | Usuarios: error simulado | mensaje |
| RT-04 | (Inocuo) introducir excepción de render en un entorno de prueba / o verificar boundary por unit + captura de su UI | recuperación usable |
| RT-04b | ES/EN del boundary; móvil | usable |

Artefactos: `evidence/r215/runtime-{red,c3}.json` + PNG.

## 3 · Plan UAT

| Caso | Acción | Esperado |
|---|---|---|
| UAT-R215-01 | Provocar un error de guardado en maestros | Mensaje claro; sin pantalla blanca; puede corregir |
| UAT-R215-02 | (Si se puede de forma inocua) ver la pantalla de recuperación | Botones funcionan |

Criterio: 2/2.
