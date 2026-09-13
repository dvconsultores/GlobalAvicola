# R-209 · SPEC — CÓDIGO CANÓNICO DE LA OC SAP EN TODOS LOS SELECTORES INTERNOS

Fecha: 2026-09-13 · Hallazgo canónico: **R-209** (P2 · bloquea dato SAP) · HEAD `c0b4afc` · Origen B-09/B-10 · Registro G-21. Secciones §47.

## 1 · Contexto

El asistente fija la referencia del documento SAP con dos patrones: el selector superior compartido (6 tipos) que usa el código (`doc_number || ref_id || sap_code`, `identificadorDeOrdenSap`, R-189 §2) y dos selectores internos (`bird_exit`, `feed_registration`) que guardan `String(id)`. El backend valida y compara por `sap_code`.

## 2 · Evidencia

`R-209_FINDING.md §1`: `OperationFormPage.tsx:917-927,1033-1040,2008-2035`; `validators.py:471-474,758`; `models.py:225`.

## 3 · Causa raíz

Doble camino de captura sin reutilizar la primitive canónica; la corrección R-189 no se propagó.

## 4 · Impacto de negocio

Referencias SAP inválidas en salida de aves y alimento; comparativo/conciliación futura rota para esos eventos; dato de origen no confiable.

## 5 · Comportamiento actual

| Selector | Valor guardado |
|---|---|
| Superior (compartido) | código de la OC («4500001234») ✔ |
| `bird_exit` interno | **id** («12») ✘ |
| `feed_registration.sap_order_id` | **id** («9») ✘ |

## 6 · Comportamiento esperado

1. Ambos selectores internos guardan el **mismo código canónico** que el superior, reutilizando `identificadorDeOrdenSap(o)` (sin duplicar lógica).
2. Si el catálogo no expone código (dato incompleto), se aplica el fallback canónico (`ref_id`/`sap_code`) y, si nada existe, el campo queda **ausente** (no `String(id)`).
3. Sin cambio de contrato backend (el campo sigue siendo string libre validado por `sap_code`).
4. Regresión: R-189 (bloque superior) intacto; comparativo SAP por API casa para los tres tipos.

## 7 · Alcance

- `OperationFormPage.tsx` (dos bloques internos) + reutilización del helper existente.
- Tests: `frontend/.../__tests__/r209.sapCodeSelectors.test.tsx` (jsdom; rojo: valor = id); backend control `test_r209_sap_document_ref_contract.py` (comparativo casa por código; verde en HEAD para el bloque superior, rojo por UI no aplica — el control es de contrato API).
- Sin migración; sin endpoint; sin permiso.

## 8 · Fuera de alcance

- `sap_order_id` de otros sitios no listados (revisión exhaustiva de selectores en la tranche; si aparece otro, se añade al mismo paquete).
- Validación BR-10/BR-18 (intactas).
- UI del panel SAP (R-217).

## 9 · Impacto frontend

Dos bloques del asistente; reutiliza el helper de R-189.

## 10 · Impacto backend

Ninguno.

## 11 · Contrato frontend↔backend

`POST /operations`: `sap_document_ref`/`sap_order_id` pasan a llevar el código; sin cambio de esquema.

## 12 · Impacto en datos

Ninguno nuevo; los eventos nuevos quedan correctos. Históricos con id: no se reescriben (se anotan en el inventario de la certificación; saneamiento posible en tranche de datos si el propietario lo pide).

## 13 · Seguridad

Sin cambio.

## 14 · Inquilino

Sin cambio (el catálogo ya viene acotado).

## 15 · Unidad de negocio

Sin cambio.

## 16 · RBAC

`operations:create` sin cambio.

## 17 · Transacciones

Sin cambio.

## 18 · Auditoría

Sin cambio.

## 19 · i18n

Sin claves nuevas (etiquetas existentes).

## 20 · Escritorio · 21 · Móvil

Mismos selectores; verificación de que en móvil los `<select>` nativos muestran el código como label (sin cambio de lógica).

## 22 · Manejo de errores

Sin cambio.

## 23 · Impacto de migración

Ninguna.

## 24 · Impacto SAP

Corrige la referencia que P-08 conciliará. Sin llamadas.

## 25 · Compatibilidad hacia atrás

Cliente API que enviara id: sigue aceptándose el string (compatibilidad de esquema); la corrección es de UI. Comparativo: los eventos antiguos con id no casan (comportamiento actual, se documenta).

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| AC-R209-01 | `bird_exit` por UI con OC elegida ⇒ `payload.sap_document_ref` = código (no id) |
| AC-R209-02 | `feed_registration` por UI ⇒ `payload.feed_movements[0].sap_order_id` = código |
| AC-R209-03 | Catálogo sin código ⇒ fallback canónico; nunca `String(id)` |
| AC-R209-04 | Comparativo SAP (API) casa por `sap_code` para ambos tipos (control) |
| AC-R209-05 | Regresión R-189: selector superior intacto (vitest `f01.*`) |
| AC-R209-06 | Sin migración/endpoint/permiso |
| AC-R209-07 | ES/EN sin cambio de etiquetas (control) |
| AC-R209-08 | Inventario de históricos con id registrado (consulta de lectura) |

## 27 · Pruebas RED→GREEN

`R-209_RED_E2E_UAT_DESIGN.md §1`: `r209.sapCodeSelectors` (2 casos rojos: id), control `f01.payloadContract` (verde), backend `test_r209_*` (comparativo).

## 28 · E2E

Runtime (`§2`): `R209-RT-01…04` (salida con OC, alimento con OT, comparativo, fallback). Artefacto `evidence/r209/runtime-{red,c3}.json`.

## 29 · UAT

No requerida (el valor correcto no cambia la interacción). Verificación técnica en certificación (payload + comparativo).

## 30 · Criterios de cierre

RED válida · GREEN local · sensibilidad (S1: revertir a `String(id)` ⇒ AC-01/02 rojas) · sin migración/endpoint/permiso · R-209 → `CLOSED` con GA-REM asignado.
