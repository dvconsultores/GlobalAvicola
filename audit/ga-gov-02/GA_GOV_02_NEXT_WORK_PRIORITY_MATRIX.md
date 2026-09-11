# GA-GOV-02 · MATRIZ DE PRIORIDAD DEL PRÓXIMO TRABAJO

Regla: correctness de negocio > integridad de datos > seguridad > impacto de usuario > frecuencia > dependencias > (esfuerzo solo secundario). No se inicia nada.

## Candidatos

| Criterio | **R-186** (remediación) | **Decisión IPE** (escala/bandas) | **OBS-UAT-01** (UX lotes) | **BU-D10** (ratificación) | **Wave B** (reanudar) |
|---|---|---|---|---|---|
| Correctness de negocio | Endpoint roto (500) — restaura cálculo | Define significado del indicador | No afecta correctness | No afecta correctness | Continuidad de remediación |
| Integridad de datos | Ninguna en riesgo (cálculo en vivo) | Ninguna (display-only, sin persistencia) | Ninguna | Ninguna | Ya certificada por tranche |
| Seguridad | Ninguna | Ninguna | Ninguna | Ninguna | Ninguna |
| Frecuencia | 100 % de lotes reales con actor `reports:read` sobre el endpoint | Afecta interpretación de todo IPE mostrado | Solo descubrimiento | Bloquea habilitación de unidades | — |
| Visibilidad de usuario | API-only hoy | **USER_VISIBLE** (tarjeta/reporte) | USER_VISIBLE | Plano de control | Producto |
| Impacto de flujo | Ningún flujo visible bloqueado (sin consumidor) | Clasificaciones poco informativas | Workaround por URL directa | N/A | Wave B pausada por decisión de programa |
| Dependencias | Ninguna (patrón y evidencia ya existen) | Requiere convocatoria del propietario (no técnica) | Ninguna | Requiere ratificación del propietario | Requiere decisión de reanudación |
| Certeza de alcance | Alta (una expresión + test) | Media (decisión primero; implementación depende de la opción) | Alta (UX, sin R) | N/A | Alta pero amplia |
| Readiness de implementación | **LISTA** (misma doctrina que R-184: `_dia` + tests + runtime E2E) | No aplica hasta decidir | LISTA (sin R, según GA-GOV-01) | No aplica | Preparación requerida |

## Orden resultante

| Prioridad | Ítem | Por qué |
|---|---|---|
| **1** | **R-186 — tranche técnica de remediación** | Defecto real y reproducido (500) con expectativa canónica clara y patrón ya certificado en R-184; coste mínimo; restaura un endpoint de la familia P-15. No depende de la decisión de negocio (ortogonal). Es el único ítem *técnico* listo y sin decisiones pendientes |
| **2** | **Sesión de decisión del propietario — escala/bandas del IPE** | Única pregunta de **política de negocio**: qué escala e interpretación debe tener el IPE. No bloquea R-186; debe resolverse **antes** de cualquier cambio futuro de fórmula/bandas (secuencia OBS→OD→SPEC). Recomendado convocarla en paralelo/en cuanto el propietario quiera |
| **3** | **OBS-UAT-01 — UX de descubrimiento de Lotes (P2, sin R)** | Mejora real de UX ya inventariada; menor a los dos anteriores en correctness; puede convivir con P1/P2 |
| — | **BU-D10** | Espera **ratificación del propietario** (gobernanza); sin dependencia con 1-3; no se decide aquí |
| — | **Wave B (reanudar)** | Decisión de programa del propietario; P1/P2 no la bloquean (`INDEPENDENT`); preparación cuando lo indique |

**Recomendación: Priority 1 = R-186.** (No se inicia en esta tranche.)
