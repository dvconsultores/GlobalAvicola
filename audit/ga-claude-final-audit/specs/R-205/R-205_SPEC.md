# R-205 · SPEC — CUADRE BR-20 DISPONIBLE EN TODAS LAS RUTAS DE ENTRADA AL ASISTENTE

Fecha: 2026-09-13 · Hallazgo canónico: **R-205** (P1 · bloquea) · HEAD `c0b4afc` · Origen runtime local (P-03) · Registro G-16. Secciones §47.

## 1 · Contexto

El asistente `/operations/new` (único `onSubmit`, `POST /operations`) entra por tres vías: hub/etapa (`?type=…`, ruta dominante), detalle de lote (acciones rápidas, `?type=…&lot_id=…`) y URL directa (wizard completo con paso 1). El cuadre BR-20 de la recepción de reproductoras quedó condicionado al paso 1 (estado `stage`), que la ruta dominante no ejecuta.

## 2 · Evidencia

`R-205_FINDING.md §1`: `OperationFormPage.tsx:316,319,667-680,1901-1915`; `validators.py:536-565`; local `BR2-01-bird_reception-por-hub` (400) vs `BR2-02-…-asistente` (201); `playwright_e2e.log` (p03/p04/p11 rojas por BR-20).

## 3 · Causa raíz

`stage` como estado exclusivo del paso 1; sin derivación desde el contexto (tipo de evento, lote seleccionado/fase) ni desde el enlace (`?stage=`); el cliente no conoce la obligatoriedad de BR-20 por cadena del lote.

## 4 · Impacto de negocio

Cadena de reproductoras bloqueada en su primer paso de datos (recepción con cuadre); certificaciones P-03/P-04/P-11 obsoletas; riesgo de que operadores usen rutas no enlazadas (conocimiento fuera del producto).

## 5 · Comportamiento actual

| Entrada | `stage` | Cuadre visible | Resultado |
|---|---|---|---|
| Hub/etapa (`?type=bird_reception`) | `null` | **no** | `400 BR-20` |
| Detalle de lote (`?type=…&lot_id=`) | `null` | **no** | `400 BR-20` |
| URL directa sin `?type=` (paso 1→2) | `breeder_rearing` (elegido) | sí | 201 |

## 6 · Comportamiento esperado

1. **`stage` derivado del contexto** (prioridad): (a) `?stage=` si el enlace lo aporta (tiles por etapa); (b) `lot.bird_type` + fase activa del lote (`grandparent|breeder` + `rearing|production`); (c) tipo de evento/etapa del hub cuando no hay lote (p. ej. `farm_inspection` desde el hub de cría). Sin contexto ⇒ comportamiento actual (paso 1).
2. **Cuadre por cadena del lote**: con lote `breeder` y evento `bird_reception`, el bloque BR-20 se renderiza y sus tres campos son **obligatorios en cliente** (con validación previa al envío; mensaje claro si faltan), en cualquier ruta de entrada.
3. **Misma forma para todos**: hub, detalle de lote y URL directa producen el mismo formulario (paridad de ruta).
4. **Backend intacto**: BR-20 sigue validando (los campos siguen siendo obligatorios/prohibidos por cadena); el 400 remoto sigue renderizándose seguro (R-189).
5. Sin romper R-190/F-01e (misma derivación de ubicación; cambios coordinados).

## 7 · Alcance

- `OperationFormPage.tsx`: derivación de `stage` (helper puro `resolverStageDelAsistente(...)` en `operationPayload.ts` para test unitario), visibilidad/obligatoriedad del cuadre ligada a `bird_type` del lote (no solo a `stage`), `superRefine` de campos de cuadre.
- `operationPayload.ts`: helper puro (testeable).
- i18n ES/EN: 1-2 claves de validación (si no reutilizables).
- Tests RED: unit jsdom (paridad de rutas por `?type=` vs directa) + regression suites.
- **Sin** cambios de backend (BR-20 intacta).

## 8 · Fuera de alcance

- `rejected_on_arrival`/`received_total` semántica de dominio (RR-12; sin cambio).
- Otros tipos de evento con campos por cadena (solo se evaluará el patrón; sin cambios salvo los necesarios para paridad del cuadre).
- Actualización de las suites p03/p04/p11 (GA-GOV-03 las corrige; esta spec **habilita** su corrección).
- `stage` en el resto de etapas más allá de lo necesario para derivar la etapa del evento.

## 9 · Impacto frontend

`OperationFormPage.tsx` (derivación/visibilidad/validación), `operationPayload.ts` (helper), i18n. Sin nuevas rutas ni rediseño visual.

## 10 · Impacto backend

Ninguno. BR-20 intacta (`validators.py:536-565`).

## 11 · Contrato frontend↔backend

`POST /api/v1/operations` (`bird_reception`): el payload ahora incluye `received_total`/`dead_on_arrival`/`rejected_on_arrival` cuando el lote es breeder (contrato ya exigido por BR-20). Respuesta 201 sin cambio. Errores: 400 BR-20 solo alcanzable por clientes que omitan el cuadre.

## 12 · Impacto en datos

Ninguno nuevo; los eventos de recepción de reproductoras pasan a registrar el cuadre que el dominio ya exige.

## 13 · Seguridad

Sin cambio (mismos permisos/tenencia; el cliente no gana autoridad).

## 14 · Inquilino

Sin cambio (lote y catálogos ya acotados).

## 15 · Unidad de negocio

Sin cambio (unidad derivada del lote).

## 16 · RBAC

`operations:create` sin cambio.

## 17 · Transacciones

Sin cambio; el bloqueo cliente evita peticiones inválidas.

## 18 · Auditoría

Sin cambio (alta audita como hoy).

## 19 · i18n

| Clave | ES | EN |
|---|---|---|
| `operations.receptionReconciliationRequired` (si el mensaje no es reutilizable) | Complete el cuadre de recepción (recibidas, mortalidad al arribo, rechazadas) | Complete the reception reconciliation (received, dead on arrival, rejected) |

Sin texto fijo nuevo fuera de claves (patrón vigente).

## 20 · Escritorio

Cuadre visible en la columna del formulario de recepción junto a los datos de aves; sin overflow a 1280×800.

## 21 · Móvil

Verificación 390×844: campos accesibles con teclado táctil; mensajes sin desplazamiento horizontal.

## 22 · Manejo de errores

| Caso | Comportamiento |
|---|---|
| Faltan campos de cuadre | bloqueo en cliente con mensaje (no se envía) |
| 400 BR-20 (cliente antiguo) | `getErrorMessage` → texto (R-189) |
| 401/403/404/409/422 | flujos existentes sin cambio |

## 23 · Impacto de migración

Ninguno.

## 24 · Impacto SAP

Indirecto: la recepción de reproductoras registra el cuadre de arribo (dato de origen). Sin llamadas SAP.

## 25 · Compatibilidad hacia atrás

- URL directa (paso 1): idéntico.
- Hub/detalle de lote: dejan de fallar (corrección).
- `bird_reception` de otras cadenas (grandparent/broiler/hatchery): campos de cuadre siguen prohibidos/ausentes según cadena (BR-20 intacta; regresión).
- Clientes API: sin cambio.

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| AC-R205-01 | Hub/etapa `?type=bird_reception` con lote breeder ⇒ cuadre visible y obligatorio ⇒ 201 con los tres campos |
| AC-R205-02 | Detalle de lote (acción rápida) ⇒ mismo resultado (paridad de ruta) |
| AC-R205-03 | URL directa (paso 1) ⇒ sin regresión (cuadre y 201) |
| AC-R205-04 | Lote `broiler`/`grandparent`: sin campos de cuadre (BR-20 prohibida) y 201 sin ellos (regresión) |
| AC-R205-05 | Sin cuadre completo ⇒ **sin petición** y mensaje claro (no se depende del 400) |
| AC-R205-06 | API sin los campos (cliente antiguo) ⇒ 400 BR-20 (backend intacto) |
| AC-R205-07 | `?stage=` respetado si el enlace lo aporta; sin `?type=` ni contexto ⇒ comportamiento actual (paso 1) |
| AC-R205-08 | ES/EN: mensajes presentes; sin texto fijo |
| AC-R205-09 | Móvil 390×844: campos y mensajes usables |
| AC-R205-10 | Sin migración/endpoint/permiso; diff FE (+tests) |
| AC-R205-11 | Runtime: recepción de reproductoras por hub 201 sobre lote breeder real; suites p03/p04/p11 corregidas en GA-GOV-03 quedan verdes |
| AC-R205-12 | Regresión R-189/F-01e y R-190 (tranche conjunta) verdes |

## 27 · Pruebas RED→GREEN

`R-205_RED_E2E_UAT_DESIGN.md §1`: `r205.stageDerivation.test.ts` (helper; rojo: no existe), `r205.breederReceptionParity.test.tsx` (jsdom: hub/detalle/directa; rojo: sin cuadre por `?type=`), regresión `f01e/f01/r153/r190`. Backend: control BR-20 verde.

## 28 · E2E

Runtime nube (`§2`): `E2E-R205-01…06` (recepción breeder por hub, por detalle, directa, control broiler, EN/móvil, sonda API). Artefactos `evidence/runtime-c3/` (journal + PNG + payloads).

## 29 · UAT

`UAT-R205-01…04` (propietario; agrupada con R-190): recepción de reproductoras por hub en escritorio y móvil; error claro con cuadre incompleto; EN. Criterio 4/4.

## 30 · Criterios de cierre

AC-R205-01…12 verdes · RED en `c0b4afc` · GREEN local (vitest/tsc/build) · runtime C3 con artefactos · suites p03/p04/p11 remediadas en GA-GOV-03 verificadas · UAT 4/4 · R-189 recertificada (retry 7/7) · sin migración/endpoint/permiso · R-205 → `CLOSED` con GA-REM asignado.
