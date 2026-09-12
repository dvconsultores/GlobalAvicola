# GA-R153 · EVIDENCIA FRONTEND

Fecha: 2026-09-12 · Bundle certificado: `index-DNXomVaS.js` (deploy de `47ea484`/`db8ae21`).

## 1 · Cambios

| Archivo | Cambio |
|---|---|
| `OperationFormPage.tsx` | `LOT_OPTIONAL_EVENTS = {inspecciones… , grandparent_import}`; el `superRefine` deja de exigir lote para la importación; nota i18n junto al selector (el selector permanece — vía con lote visible para el legado) |
| `OperationDetailPage.tsx` | Lote: enlace `/lots/{id}` cuando existe; «Se creará al aprobar» cuando es importación sin lote; `—` en el resto |
| `translation.json` ES/EN | `operations.importLotAutoNote`, `operations.lotAutoPending` |

## 2 · Pruebas

- `r153.importLotOptional.test.ts`: **3/3** (tras RED 3/3 rojos en C1).
- Suite completa: **295/295** (39 archivos; +3 sobre la línea base 292).
- `tsc --noEmit` sin errores; `npm run build` OK.

## 3 · Verificación visual autenticada (operador de empresa, BU grandparent ON)

| Captura | Comprobación |
|---|---|
| `evidence/ui-detalle-pendiente.png` | Evento #91 (importación, registrada): «Lote: **Se creará al aprobar**»; plan y ♂40/♀60 visibles |
| `evidence/ui-detalle-aprobado.png` | Evento #88 (aprobada): «Lote: **#62**» con enlace `href=/lots/62` |
| `evidence/ui-formulario-nota.png` | Formulario Importación de Abuelas: selector de lote **opcional** + nota «Si no selecciona un lote, se creará automáticamente al aprobar la importación.» |

Consola: 403 esperados por roles mínimos (módulos maestros/SAP que el actor sintético no tiene) — falla cerrada, misma línea base que `GA-FE-*`.
