# GA-FE-06 · ESPECIFICACIÓN R-182 — CONTRATO DE ALTA DE LOTE + FECHA PREVISTA DE CIERRE + ÁREA/AREA_ID + ACTIVACIÓN SLA + CERTIFICACIÓN RUNTIME

Hallazgo (backlog R-182): el formulario de alta de lote **no enviaba** `planned_close_date` (tenía control) ni `area_id` (ni siquiera control) ⇒ la fecha prevista nunca llegaba a DB ⇒ el aviso SLA «lote próximo a cierre» quedaba hambriento de datos. Backend, esquema, migración y evaluación SLA **ya existían y son correctos** (ver reconciliation).

Criterios de aceptación (estado inicial: pendiente; se actualizan con evidencia):

| AC | Enunciado verificable | Estado |
|---|---|---|
| R182-AC01 | El alta de lote captura `planned_close_date` desde UI (control tipo fecha) | pendiente |
| R182-AC02 | El payload HTTP del alta incluye `planned_close_date` con el valor elegido | pendiente |
| R182-AC03 | El backend persiste `planned_close_date` (medianoche UTC, R-75) y un fresh GET lo devuelve | pendiente |
| R182-AC04 | UI sin fecha ⇒ `planned_close_date=null` explícito (sin valor inventado) | pendiente |
| R182-AC05 | No hay corrimiento ±1 día en ningún salto (UI→wire→DB→GET→display) | pendiente |
| R182-AC06 | El alta captura área mediante **selector de áreas propias de la empresa** | pendiente |
| R182-AC07 | El payload HTTP del alta incluye `area_id` cuando hay área elegida | pendiente |
| R182-AC08 | El backend persiste `area_id` y fresh GET lo devuelve | pendiente |
| R182-AC09 | UI sin área ⇒ `area_id=null` (opcional real) | pendiente |
| R182-AC10 | El selector de áreas nunca ofrece áreas de otra empresa (filtro por inquilino) | pendiente |
| R182-AC11 | `area_id` de otra empresa enviado por API ⇒ rechazo/denegación; **sin persistencia** | pendiente |
| R182-AC12 | Ninguna representación de UI muestra IDs crudos de área | pendiente |
| R182-AC13 | El detalle del lote muestra «Cierre previsto» con el día correcto cuando existe | pendiente |
| R182-AC14 | Base de alta de lote sin campos obligatorios nuevos (PLD y área opcionales; no rompe alta mínima) | pendiente |
| R182-AC15 | Errores de validación del alta no producen falso éxito (ni navegación ni lote creado) | pendiente |
| R182-AC16 | Registro de cambios del lote (edición) sigue soportado por backend; UI de edición N/A documentado | pendiente |
| R182-AC17 | SLA «próximo a cierre» consume `planned_close_date` de lotes creados por UI (fuente de datos reparada) | pendiente |
| R182-AC18 | Ventana vigente `0..3` días naturales se comporta en frontera +3 y dentro +1 (no reimplementar) | pendiente |
| R182-AC19 | `+10` fuera de ventana no genera aviso | pendiente |
| R182-AC20 | `NULL` excluido (no se inventa referencia) | pendiente |
| R182-AC21 | Fecha pasada (`−1`) excluida | pendiente |
| R182-AC22 | Solo lotes `active` entran (condición de código; evidencia canónica) | pendiente |
| R182-AC23 | Aviso `lot_near_close` lleva lote, fecha ISO y `days_remaining` correctos | pendiente |
| R182-AC24 | Ocurrencia idempotente `lot:{id}:{fecha}` (re-evaluar no duplica; replanificar = nuevo aviso) | pendiente |
| R182-AC25 | Destinatarios del aviso nunca cruzan empresa (resolución por company/área/originador) | pendiente |
| R182-AC26 | `area_id` del lote participa donde corresponde (resolución de destinatarios) sin UI extra | pendiente |
| R182-AC27 | Alta de lote no gana permisos nuevos; sigue exigida la ventana operativa de la BU del `bird_type` | pendiente |
| R182-AC28 | Usuario sin `lots:create` no accede a `/lots/new` (guard) ni crea por API (403) | pendiente |
| R182-AC29 | Usuario con rol pero **sin BU** no crea lote (UI y API) — CBU sigue vigente | pendiente |
| R182-AC30 | CBU desactivada (ventana apagada) no ofrece bypass en UI ni API | pendiente |
| R182-AC31 | Selector de áreas respeta la empresa del usuario (agrupación/ausencia de ajenas) | pendiente |
| R182-AC32 | Alta por UI bajo móvil 390×844 funciona (selector y fecha usables) | pendiente |
| R182-AC33 | Alta por UI desktop 1440×900 funciona | pendiente |
| R182-AC34 | Textos nuevos existen en ES y EN (sin claves crudas visibles) | pendiente |
| R182-AC35 | 0 errores de consola fatales en los flujos certificados | pendiente |
| R182-AC36 | 0 paneles de red con 5xx; payloads conformes; sin datos sensibles en red | pendiente |
| R182-AC37 | Sin tormenta de peticiones (conteo de fetches acotado en alta y detalle) | pendiente |
| R182-AC38 | Traza de auditoría de creación presente y consultable para lotes GA6 | pendiente |
| R182-AC39 | Refresh/relogin conserva la verdad persistida (fresh GET idéntico) | pendiente |
| R182-AC40 | Bundle servido es el de la generación implementada (hash congelado) | pendiente |
| R182-AC41 | Regresiones GA-FE-02/03/04/05 siguen CLOSED (R-98/R-119/R-181) | pendiente |
| R182-AC42 | Suite frontend total verde (baseline + nuevos) y tsc 0 | pendiente |
| R182-AC43 | Suite canónica SLA/PG del repo sigue verde donde corre (CI; local skipped declarado) | pendiente |
| R182-AC44 | Evidencia RED previa a implementación archivada (vitest + runtime pre-fix) | pendiente |
| R182-AC45 | Evidencia GREEN completa y ligada a bundle/commit | pendiente |
| R182-AC46 | `GA_FE_06_NETWORK_EVIDENCE.md` con capturas sanitizadas | pendiente |
| R182-AC47 | `GA_FE_06_TEST_DATA_LEDGER.md` con alta/retiro exactos | pendiente |
| R182-AC48 | Reconciliación de cierre R-182 responde «¿se perdía la fecha en silencio? ¿ahora persistida/visible?» con evidencia | pendiente |
| R182-AC49 | Auditoría maestra del frontend actualizada (addendum) y catálogo de hallazgos | pendiente |
| R182-AC50 | Cero expansión de alcance: sin cambios backend/migración/SLA/permisos | pendiente |
| R182-AC51 | Worktree limpio y local==remoto tras cada commit de la tranche | pendiente |
| R182-AC52 | Paquete UAT del propietario listo (guía reproducible + evidencia indexada) | pendiente |

## Fuera de alcance (registrado)

- `sap_reference` fuera de `LotBase` (observación separada, no R-182).
- UI de edición de lote (no existe; backend correcto) — ver matriz UPDATE.
- Cualquier cambio de umbrales SLA, permisos nuevos o migraciones.
