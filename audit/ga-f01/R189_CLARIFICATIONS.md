# R-189 · CLARIFICACIONES (F-01)

Fecha: 2026-09-12 · Resueltas antes de implementar (C1).

| # | Pregunta | Resolución | Fuente |
|---|---|---|---|
| C01 | Ruta exacta de importación | `/operations/new` (wizard 3 pasos) | `App.tsx:260` |
| C02 | Componente del formulario | `OperationFormPage.tsx` (único `onSubmit`) | código |
| C03 | Endpoint de alta | `POST /api/v1/operations` | FormPage:418 |
| C04 | Esquema backend | `OperationalEventCreate` (schemas.py:159) | código |
| C05 | Campo de almacenamiento | `egg_storage_records: list[EggStorageSchema]`, default `[]` | schemas.py:164 |
| C06 | Semántica de omisión | Válida; `[]` es canónico («sin registros»); nunca `[{}]` | control runtime [1]/[2] |
| C07 | Semántica parcial | Registro con contenido se envía; rechazo gobernado se muestra seguro | spec §5 AC06 |
| C08 | Campo frontend de la OC | `extra_data.sap_order_ref` (SearchSelect entrega `String(item.id)`) | FormPage:1969-1984 |
| C09 | Campo wire esperado | `sap_document_ref` con el **código** de la referencia (también `extra_data.sap_order_ref` para UI) | `validate_import_plan`; GA-TD-014 |
| C10 | Campo backend | `OperationalEventBase.sap_document_ref` (string, consumido por BR-22/BR-18) | schemas/service |
| C11 | Por qué se pierde hoy | el bloque escribe solo `extra_data.sap_order_ref` **y** con el id (lookup por etiqueta falla) | payload real; FormPage:1969-1984 |
| C12 | Ruta de recepción | `/operations/new` → Progenitoras Cría → «Recepción de Aves» (mismo componente) | catálogo + código |
| C13 | Componente de recepción | Mismo `OperationFormPage` (caso `bird_reception`) | código |
| C14 | Endpoint de recepción | `POST /api/v1/operations` (mismo) | código |
| C15 | Almacenamiento en recepción | No exigido; `[]` canónico; sin cambio de semántica | control [2] |
| C16 | ¿Serializador compartido? | Sí: un único `onSubmit` para todas las altas ⇒ arreglo central seguro | código |
| C17 | Forma real del 422 | `{"detail":[{"type","loc","msg","input"}]}` (evidencia F-01) | journal |
| C18 | Punto del React #31 | `setResult({message: <array>})` → render `{result.message}` | FormPage:423-424, 1895 |
| C19 | ¿Normalizador existente? | `getErrorMessage` (Toast.tsx) existe pero devuelve `detail` crudo | código |
| C20 | Alcance del normalizador | Endurecer `getErrorMessage` (string|lista|objeto|Error) — reuso compartido, sin reescribir arquitectura | §17-18 |
| C21 | ES | Mensajes del servidor se muestran tal cual; fallback con clave existente | §42 |
| C22 | EN | Idem (sin texto nuevo fijo) | §47 |
| C23 | Móvil | Formulario alcanzable; verificación 390×844 de superficies cambiadas | §62 |
| C24 | Regresión R-153 | Recertificar el flujo completo por UI (addendum post-fix) | §44 |
| C25 | Criterio de repetición UAT | 7/7 casos del walkthrough de referencia en verde + 0 fatales | §72 |
| C26 | Campos numéricos vacíos | `valueAsNumber` produce `NaN` ⇒ zod inválida **en silencio** (submit sin petición). Resolución: saneo en el serializador (NaN ⇒ omitido; filas sin contenido descartadas; cantidad 0 declarada se conserva) — no se relaja el esquema | RED v5 + E2E UAT-09 |

| C27 | Filas `{}` en `feed_movements`/`hatchery_params` | Tercera superficie del mismo defecto (F-01d): el `[{}]` de arranque del formulario se persiste (el default 0.0 no se valida en alta) y el detalle 500 al leerlo (`gt=0`). Resolución: serializadores frontend (fila sin contenido ⇒ descartada) + esquemas de escritura estrictos (422 ruidoso, sin persistencia) + lectura tolerante para históricos | RED v6 (`evidence/f01d/` matriz + traceback) + payload nube `[{}]` |
| C28 | Compatibilidad de clientes con caché antigua | Un cliente desactualizado que envíe `[{}]` recibe 422 y el error se muestra seguro (S3 corregido); la UI nueva nunca lo envía; los datos históricos no se alteran (solo lectura tolerante) | anexo F-01d §4 (D2/D3) |

Sin clarificaciones críticas abiertas ⇒ implementación habilitada (C1); ampliación F-01d habilitada tras C2 (anexo §4).
