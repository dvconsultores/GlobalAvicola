# R-189 · SPEC — CONTRATO DEL FORMULARIO DE OPERACIONES EN EL GUARDADO (F-01)

Fecha: 2026-09-12 · Hallazgo canónico: **R-189** (P1) · Origen: F-01 (GA-UAT-09) · Commits: C1 (este paquete) · C2 (implementación).

## 1 · Contexto y hallazgo

GA-UAT-09 quedó bloqueada en UAT-01: el alta de importación por interfaz es rechazada (422) y el error rompe el render (React #31 → pantalla en blanco). Dos causas raíz encadenadas + una de presentación (§ trazas `GA_F01_*`). La misma carga por omisión afecta el alta de recepción.

## 2 · Propiedad y protección

- **OD-25 (B) no cambia**. R-153 se protege (se recertificará sobre la UI corregida). R-130, P-07, BR-17/18/20 intactos. Tenant/BU/RBAC sin cambios. `/roles` sin tocar. Sin migración, sin endpoint nuevo, sin permiso nuevo.

## 3 · Alcance (implementación)

1. **Serializador de almacenamiento**: `egg_storage_records` → solo registros con contenido; sin contenido ⇒ `[]` (canónico). En import Y recepción (mismo `onSubmit`).
1b. **Serializador de movimientos de aves**: los campos numéricos vacíos llegan como `NaN` (`valueAsNumber`) y **bloquean el submit en silencio** (validación zod); las filas sin contenido (p.ej. ♀ vacía) se descartan y los `NaN` se omiten — sin inventar valores, sin tocar cantidad 0 declarada.
2. **Mapeo de OC**: el bloque compartido escribe el **código canónico** de la referencia en `sap_document_ref` (campo tipado que el dominio valida, precedente `GA-TD-014`) **y** en `extra_data.sap_order_ref` (consumo de UI existente); resuelve la orden por `id` (contrato de `SearchSelect`); completa los extras declarados. Aplica a la rama no-cría y a la rama cría (transferencia/compra) del bloque compartido.
3. **Errores seguros**: `getErrorMessage` (helper compartido existente) normaliza `detail` string | lista FastAPI | objeto | Error | string | desconocido → **string siempre**; `OperationFormPage` lo usa en el `catch`. Sin stack, sin `[object Object]`, sin romper render.

**Fuera de alcance**: F-01b, F-01c, OBS-2, OBS-3, cualquier otro residual, AOD-06/AOD-24, Wave B/C, SAP.

## 4 · Claves técnicas

- Ruta `/operations/new` · componente `OperationFormPage` · endpoint `POST /api/v1/operations`.
- `SearchSelect` entrega `String(item.id)`; el valor **canónico** de la referencia SAP es su código (`doc_number || ref_id || sap_code`).
- `[]` es la representación canónica de «sin registros» para la lista de almacenamiento (default del esquema).
- Normalizador: en `Toast.tsx` (helper existente, endurecido; todos sus consumidores se benefician sin cambiar su contrato actual: string para casos simples).

## 5 · Criterios de aceptación

Payload: **AC01** alta válida de importación por UI · **AC02** sin lote previo (OD-25) · **AC03** almacenamiento ausente serializado canónicamente · **AC04** nunca `{}` accidental · **AC05** objeto completo conservado · **AC06** parcial inválido rechazado de forma segura · **AC07** sin debilitar validación.
OC: **AC08** retenida en estado · **AC09** mapeada al campo canónico · **AC10** backend recibe el identificador · **AC11** validación la reconoce · **AC12** sin campo paralelo · **AC13** sin pérdida silenciosa al re-render.
Recepción: **AC14** alta válida por UI · **AC15** sin `{}` · **AC16** semántica de almacenamiento sin cambio · **AC17** población sin cambio · **AC18** R-130 autoritativo.
Errores: **AC19** 400/409/422 no rompen React · **AC20** `detail` estructurado → texto · **AC21** sin objetos como hijos · **AC22** página usable · **AC23** mensaje humano · **AC24** sin stack · **AC25** fatal consola 0 · **AC26** sin pantalla en blanco.
R-153/OD-25: **AC27** flujo alcanzable por UI · **AC28** sin lote antes · **AC29** al aprobar exactamente 1 · **AC30** delta población 0 · **AC31** recepción puebla una vez · **AC32** manual preservado · **AC33** legado sin duplicar · **AC34** OD-25 intacta.
Seguridad: **AC35** tenant · **AC36** BU empresa OFF cierra · **AC37** sin concesión cierra · **AC38** RBAC cierra · **AC39** sin referencias ajenas nuevas · **AC40** sin autorización en frontend.
UX/i18n: **AC41/42** escritorio import/recepción usables · **AC43** móvil · **AC44** overflow 0 · **AC45/46** ES/EN · **AC47** sin texto fijo nuevo.
Gobernanza: **AC48** dedup · **AC49** finding canónico · **AC50** spec antes · **AC51** AC antes · **AC52** RED antes · **AC53** sin cambios no relacionados · **AC54** GA-UAT-09 re-ejecutable.

## 6 · Pruebas

- RED/GREEN frontend (jsdom, camino real del formulario): payload import (almacenamiento+OC), payload recepción, render de error con 422 realista; unit del normalizador.
- Controles de contrato backend (API, runtime) documentados en la traza.
- Regresión: suite vitest completa (≥295), tsc, build; suites R-153 (PG, CI declarada).
- Runtime E2E-01…13 + recertificación R-153 (addendum) + walkthrough UAT-01…07.

## 7 · Éxito

Import válido sin lote por UI ⇒ 201; OC presente en `sap_document_ref`; almacenamiento `[]`; recepción válida por UI; 4xx visible y seguro; React fatal 0; sin pantalla en blanco; R-153 recertificada sobre la nueva generación; GA-UAT-09 re-ejecutable.
