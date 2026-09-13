# R-205 · FINDING — RECEPCIÓN DE REPRODUCTORAS: CUADRE BR-20 INALCANZABLE POR LA NAVEGACIÓN DEL PRODUCTO

| Campo | Valor |
|---|---|
| **ID canónico** | **R-205** (asignado en `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §0`; máximo previo R-189) |
| **Título** | El bloque de cuadre BR-20 (`received_total`/`dead_on_arrival`/`rejected_on_arrival`) solo se renderiza con `stage === 'breeder_rearing'`, y `stage` solo lo fija el paso 1 del asistente; todas las rutas del producto entran con `?type=` (paso 3, `stage=null`) ⇒ toda recepción de reproductoras por el hub/alta de lote cae en `400 BR-20` |
| **Severidad** | **P1** (§49: paso obligatorio de la cadena P-03/P-04 inalcanzable por UI; certificaciones P-03/P-04/P-11 no reproducibles en HEAD) |
| **Clase** | `REQUEST_CONTRACT` / `BROKEN_FLOW` (familia F-01/R-189) |
| **Proceso** | P-03 (Reproductoras cría — recepción `bird_reception` con cuadre B01/BR-20), P-04, P-11 (fixtures) |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` (== `origin/main`) |
| **Familia** | GA-REM-021-B (BR-20 certificada solo por API); R-189 (contrato del asistente); interdependiente de R-190 (misma derivación/tranche) |
| **Paquete** | `audit/ga-claude-final-audit/specs/R-205/` (completo, 6 ficheros) |
| **GA-REM** | a asignar al autorizar; siguiente libre GA-REM-043 |
| **Bloquea SAP** | **SÍ** (recepción de reproductoras por UI rota; población/ledger de P-03/P-04) |
| **UAT del propietario** | sí (flujo visible; se agrupa con R-190 en la misma sesión) |

## 1 · Evidencia

### 1.1 Código (verificado en HEAD)

- `frontend/src/pages/operations/OperationFormPage.tsx:316` — `stage` es estado local (`useState`); `:319` — `goToStep2` es el **único** setter, alcanzable solo desde el paso 1 del asistente («tarjetas de proceso»).
- `:1901-1915` — con `prefillType` (todas las llegadas `?type=`), el asistente arranca directamente en el **paso 3** con formulario; `stage` queda `null`.
- `:667-680` — bloque de cuadre condicionado a `stage === 'breeder_rearing'`: campos `received_total`, `dead_on_arrival`, `rejected_on_arrival`.
- `backend/app/operations/validators.py:536-565` — BR-20: para `bird_type=breeder` los tres campos son **obligatorios** (y prohibidos en otras cadenas) ⇒ sin el bloque, `400` «falta: received_total, dead_on_arrival, rejected_on_arrival».
- Enlaces del producto a `/operations/new`: todos con `?type=` (`App.tsx:260`; hub vía `OperationTile.tsx:60-62`; `StageTimeline` → `ProcessStagePage.tsx:49`; detalle de lote `LotDetailPage.tsx:234`). **Ninguno** sin `?type=` (grep exhaustivo: solo `App.tsx:260`).

### 1.2 Evidencia runtime/local (2026-09-13)

- Runtime (P-01/P-02): importación/recepción de abuelas OK (no aplica BR-20).
- Local pasa 2 (`evidence/ui-e2e-local-pass2.json`): `BR2-00-lote-ui` (alta de lote breeder 201), `farm_inspection` 201; **`BR2-01-bird_reception-por-hub` ⇒ 400 BR-20** con `BR2-hub-campo-cuadre-visible: 0`; el mismo formulario por **URL directa** `/operations/new` (paso 1 → paso 2) muestra el cuadre (`BR2-asistente-campo-cuadre-visible: 1`) y responde 201; `BR2-entrada-asistente-sin-type: 0 enlaces` del producto. Capturas `P2-B01-br-reception-por-hub.png`, `P2-B02-br-reception-asistente.png`.
- Suites `e2e/proceso-p03-reproductoras-cria.spec.ts`, `p04`, `p11` (API) **fallan en HEAD** por BR-20/derivados (`evidence/playwright_e2e.log`) ⇒ certificaciones P-03/P-04/P-11 no reproducibles (GA-GOV-03).

## 2 · Causa raíz

El cuadre depende de un estado de UI (`stage`) que quedó desconectado de la navegación real del producto (introducida después, OD-hub/GA-FE-08): todas las entradas usan `?type=` y nunca ejecutan el paso 1. El formulario no deriva `stage` del contexto (tipo de evento, `lot.bird_type`, fase del lote), y el vínculo entre el lote seleccionado (breeder) y la obligatoriedad del cuadre no existe en cliente (el usuario descubre BR-20 por el 400).

## 3 · Impacto

- **P-03/P-04 cortadas por UI en el paso de recepción** (primer paso con datos de población de la cadena reproductoras): sin recepción no hay saldo, distribución, ni resto de la cadena. No hay rodeo legítimo en el producto (el asistente sin `?type=` no está enlazado).
- Suites de certificación obsoletas por la misma causa (arrastre de gobernanza, GA-GOV-03).
- Fixtures de otras suites (p11) dependen del mismo defecto.

## 4 · Dedup realizada (§48)

| Registro | Resultado |
|---|---|
| R-001…R-189 | `GA-REM-021-B` certificó BR-20 solo por API («no se fabricaron pruebas de interfaz»); R-189 limitó su corrección a importación/recepción de abuelas (AC63-65, «demás tipos sin cambio»). No existe hallazgo del formulario por ruta. |
| GA-FE-01…08 | GA-FE-08 conectó el hub (`?type=`), creando la ruta dominante; sin hallazgo entonces. |
| Informes B/C | B-16/B-41 y C-3 documentan el bloqueo; el runtime local de esta auditoría lo confirmó como causa de las suites rojas. |
| Backlog | «certificación de proceso: BLOCKED_RUNTIME (no se reclama)» en Wave B — deuda reconocida sin hallazgo asignado. |

Conclusión: **nuevo**; ID asignado **R-205**. Misma tranche que **R-190** (comparten `onSubmit`/derivación y el estado `stage`).

## 5 · Propietario sugerido

Equipo frontend (asistente de operaciones), con dominio para C-02 (fuente canónica de `stage`). Regresión de suites p03/p04/p11 al actualizarse (GA-GOV-03).

## 6 · Bloquea SAP y por qué

**SÍ.** La recepción de reproductoras (con cuadre de arribo) es un paso núcleo de P-03/P-04; su población alimenta ledger, KPI y consolidación futura. Un flujo inalcanzable por UI rompe la certificación pre-SAP.

## 7 · Interdependencias

- **R-190** (galpón/granja del evento): misma tranche; ambos tocan `onSubmit` y la derivación del asistente; RED conjunta.
- **R-191** (transición de fase): mismo lote breeder (cría→producción) — tranches contiguas.
- **R-206** (`''` opcional): mismo serializador del asistente.
- **GA-GOV-03**: actualización de las suites p03/p04/p11 depende de esta corrección (fixtures dejarán de caer por BR-20).
