# GA-REQ-061 · DECISIÓN DE UBICACIÓN EN ROADMAP (T10–T13)

Fecha: 2026-09-14 · Base: `GA_PRE_SAP_REMEDIATION_MASTER_ROADMAP.md` (T1…T13) + `GA_PRE_SAP_PROCESS_DEPENDENCY_GRAPH.md` + código real. Esta decisión es **técnica** (no Owner Decision): se deduce de DAG/specs/código.

## 1 · Tranches existentes (estado real)

| Tranche | Alcance | Estado |
|---|---|---|
| T10 | R-197 · R-207 (+R-142 si AOD-17) — revisión/reverso UI | READY (siguiente) |
| T11 | R-213 · R-212 · R-218 · R-220 — residuales FE | pendiente |
| T12 | Recertificación E2E 17 procesos (+ decisión Wave C) | pendiente |
| T13 | UAT del propietario + gate final GO/NO-GO | pendiente |

## 2 · Dependencias del Cutover

| Capacidad del Cutover | Depende de | Tranche | Tipo |
|---|---|---|---|
| Tenancy/company/ownership | R-199/R-139/GA-REM-002 | T2 ✅ | HARD (satisfecha) |
| BU OD-16 / grants | GA-FE-02-D/R-188 | T2 ✅ | HARD (satisfecha) |
| Integridad/auditoría (ledger, gates de evidencia) | P1-12/R-198/R-219 | T8 ✅ | HARD (satisfecha) |
| Maestros/usuarios (superficies base, patrones FE) | R-196/R-195/R-215 | T9 ✅ | HARD (satisfecha) |
| Motor operacional (eventos, mortalidad, alimento, pesajes, producción) | T3-T7 ✅ | — | HARD (satisfecha) |
| Aprobaciones/revisión (patrón de estados) | T2/T7 ✅ | — | SOFT (patrón reutilizable) |
| Reverso/corrección UI (patrón para corrección de openings) | R-197/R-207 | T10 | **SOFT** (se puede implementar el backend con el patrón existente de corrections; la UI de corrección puede alinearse al patrón R-197/207 cuando exista) |
| Residuales FE | R-212/R-213/R-218/R-220 | T11 | SOFT (no comparte módulos) |

## 3 · ¿Bloquea T10?

**`T10_BLOCKED_BY_CUTOVER = NO`.** R-197/R-207 (revisión y reverso con superficie) no tocan lotes/masters/opening; el cutover no comparte módulos con T10 y su dependencia es solo de PATRONES ya certificados (§2). Ejecutar T10 antes del cutover es correcto y no crea deuda.

## 4 · Ubicación propuesta

**RECOMMENDED_PLACEMENT = nueva tranche `T14 · Cutover Operacional (GA-REQ-061)`, ejecutada DESPUÉS de T11 y ANTES de T12.**

Rationale:
- **Antes de T12** porque T12 recertifica los 17 procesos con el producto final remediado: el cutover **cambia el producto** (superficies nuevas) y debe quedar implementado+certificado para que la recertificación y el E2E final lo cubran (mandato §55: certified antes del final PRE-SAP E2E).
- **Después de T11** para no mezclar residuales FE con una capacidad nueva y para aprovechar los patrones FE ya pulidos.
- **Después de T10** porque T10 es la siguiente tranche canónica y el cutover no la bloquea.

Alternativas consideradas:

| Alternativa | Veredicto |
|---|---|
| A. Antes de T10 | ❌ innecesario; retrasa T10 sin beneficio (dependencias satisfechas por T2/T8/T9) |
| B. Intercalada T10.5 | ❌ rompe la numeración canónica sin ganancia |
| C. Después de T12 | ❌ el E2E de T12 quedaría ciego al cutover; recertificar dos veces |
| D. Después de T13 (antes del GO) | ❌ el GO no puede validarse sin que el E2E/T12 hayan cubierto cutover |
| E. **T14 entre T11 y T12** | ✅ elegida |

Nota de numeración: `T14` es el siguiente número libre (T1…T13 definidas; pista OPS aparte); su **orden de ejecución** queda fijado por esta decisión (T11 → **T14** → T12 → T13), no por el número. Se registra así en roadmap/status.

## 5 · Efectos

| Tranche | Efecto |
|---|---|
| T10 | Ninguno (continúa ya) |
| T11 | Ninguno en alcance; solo orden (T14 después) |
| T12 | Debe incluir la capacidad cutover en el universo recertificado |
| T13 | El gate final lista cutover como capacidad certificada |
| Final E2E | Cubre cutover con las 4 BUs (plan E2E del paquete) |

## 6 · Riesgos (registro RISK-CUT-01…15)

Riesgos del mandato (double counting 01, UNKNOWN=0 02, lote duplicado 03, apply duplicado 04, transacción parcial 05, cross-tenant 06, BU bypass 07, masters inactivos 08, corrección reescribe historia 09, semántica SAP 10, etapa mal mapeada 11, drift de plantilla 12, apply concurrente 13, KPI fabricado 14, identidad de lote 15) quedan **mitigados por diseño** en los ACs y planes RED/sensibilidad de este paquete; se registran en el programa al abrir T14.

## 7 · Gate de Owner

`OWNER_GATE = NONE` en esta fase. Únicos disparadores futuros posibles (documentados, no abiertos): tolerancias de consistencia (§21 del mandato), segregación más estricta que el default de la matriz de seguridad, o si el negocio exigiera obligatoriedad de un valor histórico hoy opcional. Ninguno bloquea SPEC_READY ni T10.
