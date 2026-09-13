# R-209 · FINDING — OC SAP ENVIADA POR ID INTERNO EN SALIDA DE AVES Y ALIMENTO

| Campo | Valor |
|---|---|
| **ID canónico** | **R-209** (asignado en `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §0`; máximo previo R-189) |
| **Título** | `bird_exit` guarda `sap_document_ref = String(id)` del catálogo y `feed_registration` guarda `feed_movements.sap_order_id = String(id)`: la referencia SAP persistida es el **id interno**, no el código del documento (misma clase que F-01 §2, no propagada) |
| **Severidad** | **P2** (§49: dato fuente SAP incorrecto; BR-10/comparativo por `sap_code` no casan) |
| **Clase** | `REQUEST_CONTRACT` (ID instead of code) |
| **Proceso** | P-06 (salida de aves, alimento), P-08 (comparativo SAP) |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` (== `origin/main`) |
| **Familia** | B-09/B-10 (informe B); R-189 F-01 §2 (selector superior ya usa el código); `GA-TD-014` |
| **Paquete** | `audit/ga-claude-final-audit/specs/R-209/` (completo, 6 ficheros) |
| **GA-REM** | a asignar al autorizar; siguiente libre **GA-REM-043** |
| **Bloquea SAP** | **SÍ** (referencia de documento en datos de origen) |
| **UAT del propietario** | no (se verifica en payload/detalle; sin cambio visual salvo el valor correcto) |

## 1 · Evidencia

### 1.1 Código (verificado en HEAD)

- `frontend/src/pages/operations/OperationFormPage.tsx:917-927` — selector interno «Ref. OC SAP» de `bird_exit`: `setValue('sap_document_ref', v)` con `v = String(o.id)` (id del `SapReference`). Contraste: el **selector superior** (bloque compartido) usa el código canónico (`identificadorDeOrdenSap`, `:2008-2035`, corregido por R-189 §2).
- `:1033-1040` — `feed_registration`: `feed_movements.0.sap_order_id ← String(id)` («orden de transferencia SAP», `models.py:225`).
- Backend: BR-10/BR-18 y el comparativo operan por `sap_code` (`validators.py:471-474,758`; `reports/service.py` sap-comparison), no por id.

### 1.2 Evidencia de contrato

El payload persistido lleva `sap_document_ref:"12"` (id) en vez de `"4500001234"` (código); el comparativo SAP y cualquier conciliación por `sap_code` no casan ⇒ el evento queda «sin documento» funcionalmente.

## 2 · Causa raíz

La corrección de R-189 (código canónico) se aplicó al bloque superior compartido y no se propagó a los dos selectores internos que fijan el valor por su cuenta.

## 3 · Impacto

- Salida de aves y registro de alimento con referencia SAP inválida (id) ⇒ comparativo/conciliación P-08 no casarán; datos de origen contaminados.
- Inconsistencia interna del asistente (dos selectores del mismo concepto, uno correcto y otro no).

## 4 · Dedup realizada (§48)

| Registro | Resultado |
|---|---|
| R-001…R-189 | R-189 corrigió el bloque compartido; B-09/B-10 quedaron fuera de su alcance (AC63-65 «demás tipos sin cambio»). `GA-TD-014` cita la clase, sin hallazgo propio. |
| Informe B | B-09/B-10 con líneas exactas; sin entrada en backlog. |

Conclusión: **nuevo**; ID asignado **R-209**.

## 5 · Propietario sugerido

Equipo frontend (asistente). Regresión del comparativo SAP (backend, por API).

## 6 · Bloquea SAP y por qué

**SÍ**: `sap_document_ref`/`sap_order_id` son la referencia que P-08 conciliará; un id interno la invalida.

## 7 · Interdependencias

- **R-189** (código canónico en el bloque superior): regla a reutilizar (`identificadorDeOrdenSap`).
- **R-193** (BR-18 neto): mismo campo `sap_document_ref`; sin solape.
- **R-206** (`''` de opcionales): mismo serializador; el normalizador `''`→`undefined` puede compartirse.
