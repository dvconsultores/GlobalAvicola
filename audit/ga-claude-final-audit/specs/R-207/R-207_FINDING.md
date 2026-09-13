# R-207 · FINDING — REVERSO INTERNO (OD-19) SIN SUPERFICIE DE USUARIO (FLUJO SOLO BACKEND)

| Campo | Valor |
|---|---|
| **ID canónico** | **R-207** (asignado en `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §0`; máximo previo R-189) |
| **Título** | El flujo de reverso de aprobados (solicitar → contrapartida `pending_review` → aprobación → ambos `reversed`) funciona por API pero no tiene **ninguna** superficie: 0 llamadores de `reversals` en `frontend/src`; estado `reversed` sin badge; sin enlace original↔contrapartida |
| **Severidad** | **P2** (§49 + §10: capacidad decidida y requerida sin UI; backend-only) |
| **Clase** | `MISSING_UI` / `FRONTEND_INTEGRATION_GAP` |
| **Proceso** | P-07 (revisión/aprobación), OD-19 (reverso interno), transversal a cadenas con aprobados |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` |
| **Familia** | `GA-REM-041` («sin frontend»); RES-04/OPS-09 (OOS «diferral fase 9»); C-13/C-27; E T14 |
| **Paquete** | `audit/ga-claude-final-audit/specs/R-207/` (completo, 6 ficheros) |
| **GA-REM** | a asignar al autorizar; siguiente libre GA-REM-043 |
| **Bloquea SAP** | **SÍ** (§10: ningún flujo requerido solo backend; el reverso es el único camino de corrección de un aprobado) |
| **UAT del propietario** | sí (flujo visible y sensible: anulación de aprobados) |

## 1 · Evidencia

### 1.1 Código (verificado en HEAD)

- `grep -ril reversal frontend/src` ⇒ **0**; `reversals` (router `reversals/router.py:16-37`) sin consumidor.
- Motor backend completo y probado por API (`test_internal_reversal.py`, 22 casos): solicitud (`POST /reversals` · `reversals:create`, `reversals/service.py:88-131`) ⇒ contrapartida generada por el servidor en `pending_review` (`:131`) ⇒ revisión/aprobación por el motor P-07 (`review/service.py:341-345`) ⇒ `efectuar_reverso_si_procede` marca ambos `REVERSED` (`:181-216`); cancelación prohibida (`NO_CANCELABLES`); reglas OD-19 (motivo, elegibilidad, una contrapartida activa `409`).
- Evidencia local: `ui-e2e-local-pass1/2` `H8-*`/`H8b-*` (solo por API): solicitud 201 con contrapartida; ambos `reversed`; `reversed` no cancelable (400).
- `statusColors.ts:122-138` sin `reversed` (badges neutros, C-27); `domain.types.ts:20-33` sin `reversed`.
- Respuesta de aprobación descartada (C-13): sin enlace al lote (OD-25) ni otros objetos creados.

### 1.2 Efectos colaterales ya registrados

R-192 (cierre con reverso efectivo), R-193 (BR-18 tras reverso), P1-12 (auditoría de la contrapartida): se citan; los fixes de integridad van en sus paquetes.

## 2 · Causa raíz

El reverso se implementó como capacidad backend-first (`GA-REM-041` certificó «sin frontend»); la fase de UI quedó fuera y nunca se retomó (RES-04 lo declara diferido).

## 3 · Impacto

- El único camino para corregir un registro **aprobado** (neutralización con contrapartida y rastro) es inalcanzable por la interfaz ⇒ en la práctica, registros aprobados erróneos quedan sin remedio legítimo (o se «resuelve» por vías externas, contra §10).
- El operador/revisor no ve contrapartidas ni el estado `reversed`.

## 4 · Dedup realizada (§48)

| Registro | Resultado |
|---|---|
| R-001…R-189 | `R-136` (reverso, parcial), `GA-REM-041` («sin frontend»), RES-04 — capacidad sin UI reconocida; no hay hallazgo con paquete. |
| Informes C/E | C-13/C-27 + E T14; registro G-19 lo eleva a P2 bloqueante por §10. |

Conclusión: **nuevo**; ID asignado **R-207**.

## 5 · Propietario sugerido

Frontend (detalle de operación + bandeja de revisión + badges) con backend ya listo. Sin migración.

## 6 · Bloquea SAP y por qué

**SÍ**: §10 prohíbe procesos requeridos solo-backend; y un aprobado que no puede neutralizarse por UI pone en riesgo la calidad del dato que se consolidará.

## 7 · Interdependencias

- **P1-12-REOPEN**: auditoría de la contrapartida (productor).
- **R-192/R-193**: integridad del ciclo (paquetes propios; la UI no debe exponerse antes de que cierre sea posible tras reverso — dependencia de orden sugerida).
- **R-197/R-208/R-212**: bandejas/aprobación/gates reutilizados.
- **R-215**: render seguro en el nuevo formulario de solicitud.
