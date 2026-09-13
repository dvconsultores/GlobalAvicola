# GA · PRE-SAP — PROPUESTA DE AGRUPACIÓN DE TRANCHES (TRANCHE 0 · §27/§31/§50)

Propuesta determinista. Criterios de agrupación (§31): (1) no romper seguridad; (2) desbloquear procesos; (3) mínimo riesgo de regresión multicompañía; (4) minimizar colisiones de fichero (touchpoints §22); (5) cada tranche cierra con suite verde, E2E del proceso afectado y artefacto; (6) UAT del propietario solo donde hay cambio visible.

## 1 · Tranches propuestas (agrupación y razón)

| Tranche | Contenido | Razón de la agrupación | Por qué va aquí (orden) |
|---|---|---|---|
| **T1** | GA-GOV-03: 37 tests + CI + regla de evidencia + backlog | Es gobernanza pura, sin producto; **habilita todo lo demás** (sin suite verde no hay certificación válida) | Primera: gate de arranque; su coste es bajo y evita certificar sobre línea base roja |
| **T2** | R-199 · R-200 · R-202 · R-208 (+ rider GA-REM-003 AC04) | **Fundación de seguridad/sesión/roles**: todas tocan `auth/*` o permisos; AC04 se implementa junto a R-200 (mismo ciclo de tokens) | Antes de cualquier UI de usuarios/roles (T9) y de toda recertificación; riesgo máximo si se deja para el final |
| **T3** | R-201 · R-203 · R-204(+R-216) · R-221 | **Alcance de datos multicompañía** (fail-open SAP, tenencia de lote, agregados sin unidad, unidad de eventos sin lote): mismo patrón de raíz (predicados de empresa/unidad) | Antes de tocar `lots/service.py` (T7) y `operations/service.py` (T5); independiente de T2 (paralelizable si hay dos ejecutores) |
| **T4** | R-190 + R-205 | **Misma familia FE** (ubicación BR-08 / recepción BR-20, ambas en `OperationFormPage.tsx`); R-190 habilita R-194 | Primer tramo de la cadena de eventos: sin ubicación no hay ciclo productivo por UI |
| **T5** | R-191 · R-206 · R-209 · R-210 (+ rider R-146 si AOD-16) | **Contrato de captura**: payload (vacíos/números), unidad de peso, snapshot SAP, transición de fase — misma familia de serialización FE↔BE | Después de T4 (mismo asistente ya estabilizado) y antes de R-194 (que reutiliza el payload corregido) |
| **T6** | R-194 | **Cadena de incubadora** (5 causas acopladas: farm_id, fértiles, arrival_date, dosage, hatchery_id); tranche propia por complejidad | Depende de R-190 (helper) y del payload de T5; desbloquea P-04 |
| **T7** | R-192 · R-193 · R-211 | **Validadores de cierre/reversos/distribución** (`validators.py` único, tres specs): estado REVERSED, BR-18 neto, BR-17 por galpón | Tras R-203 (tenencia de lotes); antes de R-207 (UI de reverso depende de estado REVERSED correcto) |
| **T8** | P1-12-REOPEN · R-198 · R-219 | **Auditoría y evidencias** (dedup listener/helpers, evidencias persistentes, contrato de AuditPage) — mismo subsistema `audit` + `operations.evidences` | Tras T7 (los productores de auditoría de cierre/reverso deben verse ya corregidos); antes de T9 (R-196/R-195 no dependen, pero el contrato de auditoría es entrada del gate final) |
| **T9** | R-215 · R-196 · R-195 (+ rider R-122) | **Maestros y usuarios** (estabilidad React #31 + alta estructural + edición de usuario) | Después de T2 (auth corregido) y T8 (contrato de datos fijo) |
| **T10** | R-197 · R-207 (+ rider R-142 si AOD-17) | **Centro de revisión y reverso UI**: mismas rutas/servicio; R-207 consume R-192 y R-197 | Después de T7 (estado REVERSED) y T2 (permisos batch); cierra la capacidad de reverso interno |
| **T11** | R-213 · R-212 · R-218 · R-220 | **Residuales frontend** (robustez /me, denegado≠vacío, vista semanal, residuales A-D) | Justo antes de la recertificación: son pulidos sin impacto de proceso |
| **T12** | Recertificación E2E de los 17 procesos + decisión Wave C | Recorrer P-01…P-15 con el producto remediado; certificar con artefacto | Solo cuando T1-T11 estén cerradas y Wave C decidida (AOD-10) |
| **T13** | UAT del propietario + gate final GO/NO-GO | Revalidación mínima del propietario (ver plan UAT) + cierre de Pista OPS | Último eslabón: depende de todo |
| **Pista OPS** (paralela) | R-52/RES-05 (volumen `avicola-media`), GA-REM-004 AC03 (rate limit runtime), AC07 (BD mínimo privilegio + SSL), P1-6 (respaldo comprobado) | Son acciones fuera del código; no colisionan con ninguna tranche | Pueden ejecutarse desde ya (owner/ops); **bloquean T13** |
| **Fase SAP** (fuera de este programa) | R-137, R-138, R-157, R-145, R-155, R-124, R-127.b, R-112, R-217 (+ GA-REM-017) | Requieren definición de eventos fuente y entorno SAP | No bloquean T1-T13 (bloquean `GO_SAP_INTEGRATION` únicamente) |

## 2 · Candidatos de fusión evaluados

| Candidato | Decisión | Razón |
|---|---|---|
| R-204 + R-216 (dashboard) | **Fusionar (T3)** | Mismo fichero `dashboard/service.py`; R-216 es consecuencia del formato de claves |
| R-192 + R-193 + R-211 (validators) | **Fusionar (T7)** | Misma primitiva; riesgo de pisarse si van separadas |
| P1-12 + R-198 + R-219 (audit/evidencias) | **Fusionar (T8)** | Un solo subsistema; R-219 depende del contrato de P1-12 |
| R-196 + R-215 (maestros/estabilidad) | **Fusionar (T9)** | ErrorBoundary global afecta al #31 de maestros |
| R-195 + R-122 (usuarios) | **Fusionar (T9)** | Misma pantalla |
| R-190 + R-205 | Ya juntas (T4) | Misma familia de navegación/ubicación |
| R-206 + R-209 + R-210 (+R-146) | Ya juntas (T5) | Mismo serializador |
| R-197 + R-207 | Mantener en T10 pero **serializadas** (R-197 primero) | Servicio vs UI nueva |
| R-191 dentro de T5 | Sí | Contrato de fases (FE/BE ya definido) aprovecha la tranche de payload |
| R-202 dentro de T2 | Sí (rider) | Mismo módulo auth |
| R-221 dentro de T3 | Sí (rider) | Mismo patrón de unidad/alcance que R-204 |

## 3 · Alternativa considerada y descartada

- **Ejecutar T4-T11 en paralelo total**: descartado por colisiones de fichero (familias `captura FE`, `validators`, `audit`) y por §42 (serial por defecto; paralelo solo dentro de tranche con ficheros disjuntos).
- **Meter R-199/200 al final**: descartado por §20 (la fundación de seguridad va primero; su fallo invalida toda certificación posterior).
- **Recertificar procesos uno a uno tras cada tranche**: descartado por coste; el diseño usa **E2E por tranche del proceso afectado** + recertificación integral única T12 (§43).

## 4 · Criterio de aceptación de la agrupación (§31)

1. Ninguna tranche mezcla seguridad con funcional? **Falso a propósito**: T2 es solo seguridad; T3 solo alcance de datos. T4-T11 no tocan `auth/security` (verificado contra la matriz de touchpoints).
2. Cada tranche puede ejecutarse **sin depender de decisiones no tomadas** salvo riders marcados (R-146/AOD-16, R-142/AOD-17, R-207/OD-19 §18, R-198/AOD-14, R-221/AOD-13) — que ya tienen pregunta al propietario definida (§25 del roadmap).
3. Cada tranche deja el producto desplegable (no hay tranches "a medias" de un proceso: los procesos se remedian completos dentro de una tranche o en tranches consecutivas declaradas — T4→T5→T6 es la cadena P-01/P-03→P-02→P-04).
