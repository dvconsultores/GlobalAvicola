# GA · PRE-SAP — MATRIZ DE TOUCHPOINTS COMPARTIDOS (TRANCHE 0 · §22)

Regla: un fichero, un responsable a la vez; las specs que comparten fichero **se serializan** en el orden indicado. Toda colisión no listada aquí se considera excepción y debe declararse (§41).

## 1 · Backend

| Fichero | Specs que lo tocan | Riesgo de conflicto | Orden requerido | Merges propuestos |
|---|---|---|---|---|
| `auth/service.py` | R-199, R-202, GA-REM-003 AC04 (posible), R-200 (solo lectura) | **Alto** (creación/edición de roles y contraseñas en el mismo módulo) | R-199 → R-200 → AC04 → R-202 (T2) | — |
| `auth/security.py` | R-199, R-200 | Alto (fundación de tokens/permisos) | R-200 tras R-199 (T2) | — |
| `auth/schemas.py` | R-213 (lectura `UserRead.email`) | Bajo | T11 (aislado) | — |
| `auth/router.py` | GA-REM-003 AC04 (nuevo endpoint logout) | Bajo (fichero poco tocado) | T2 | — |
| `operations/validators.py` | R-192, R-193, R-211 (+ BR-20/BR-21 ya vigentes) | **Alto** (tres specs sobre la misma primitiva de saldos/distribución) | R-192 → R-193 → R-211 (T7) | **Fusionar R-192+R-193+R-211 en una única tranche T7** (ya previsto) |
| `operations/service.py` | R-221 (T3), R-209 (T5), R-198 (T8, evidencias), P1-12 (helpers de auditoría) | Medio-alto (serializado por tranches) | T3 → T5 → T8 | — |
| `operations/schemas.py` | R-206 (validadores de entrada), R-146 rider | Medio | T5 | R-206 junto a R-209/R-210 |
| `lots/service.py` | R-203 (T3), R-192 (T7), P1-12 (T8, productores de auditoría de lote) | **Alto** | T3 → T7 → T8 | — |
| `lots/schemas.py` | R-191 (contrato ya vigente; sin cambio) | Bajo | — | — |
| `masters/models.py` / `masters/service.py` | R-203 (tenencia) | Medio | T3 | — |
| `review/service.py` | R-197 (T10), R-142 rider (T10), P1-12 (T8, llamadas de auditoría) | **Alto** (estados + auditoría) | T8 (P1-12) → T10 (R-197/R-142) | Fusionar R-197+R-142 si AOD-17 se decide antes |
| `review/router.py` | R-208 (T2, solo permisos), R-197 (T10, filtros) | Medio | T2 → T10 | — |
| `reports/service.py` | R-204 (T3), Wave C (condicional), R-218 (BE del shape semanal) | Medio | T3 → T11 | — |
| `dashboard/service.py` | R-204, R-216 (mismo fichero) | Bajo-medio | T3 (juntos) | **Fusionar R-204+R-216** |
| `integrations/sap/service.py` | R-201 (T3), R-217 (fase SAP), R-145 (fase SAP) | Bajo | T3 | — |
| `audit/listeners.py` + `audit/helpers.py` + `audit/service.py` + `audit/models.py` | P1-12 (T8), R-198 (T8), R-219 (contrato), R-83 (contexto) | **Alto** (deduplicación + productores) | P1-12 → R-198 → R-219 (T8) | **Fusionar P1-12+R-198+R-219 en T8** |
| `alembic/versions/**` | Sin cambios en T2-T11 (verificado: fixes de contrato/validación); R-83/R-148 solo si se decide | — | — | — |

## 2 · Frontend

| Fichero | Specs que lo tocan | Riesgo | Orden requerido | Merges |
|---|---|---|---|---|
| `OperationFormPage.tsx` | R-190 (T4), R-205 (T4), R-194 (T6), R-210 (T5) | **Muy alto** (asistente multipropósito) | R-190 → R-205 (T4) · R-210 (T5) · R-194 (T6) | T4 un solo autor |
| `operationPayload.ts` | R-206 (T5), R-209 (T5), R-210 (T5), R-146 rider | **Alto** (serializador único) | R-206 → R-209 → R-210 (T5) | **T5 un solo autor** |
| `LotDetailPage.tsx` | R-191 (T5, fases), R-205 (T4, enlace de entrada), R-212 (T11, guards) | Medio | T4 → T5 → T11 | — |
| `lots.service.ts` | R-191 (T5), R-205 (T4 entrada), P1-15/RES-02 (T11 UI activación) | Medio | T4 → T5 → T11 | — |
| `MasterListPage.tsx` | R-196 (T9), R-215 (boundary global) | Medio | R-215 → R-196 (T9) | **Fusionar R-196+R-215** |
| `UsersPage.tsx` | R-195 (T9), R-202 (T2 FE, si toca formulario), R-122 rider (columna Empresa) | Medio | T2 → T9 | R-195 + R-122 juntos |
| `ReviewCenter.tsx` / panel de aprobación | R-197 (T10), R-208 (T2 solo BE), R-142 rider | Medio | T2 (BE) → T10 (FE) | — |
| `AuditPage.tsx` | R-219 (T8), P1-12 (contrato) | Bajo | T8 | — |
| App shell / `PermissionRoute` / layout | R-212 (T11), R-215 (T9 boundary) | Medio | T9 → T11 | — |
| `SapManagerPage.tsx` | R-217 (fase SAP) | Bajo | No pre-SAP | — |

## 3 · Gobernanza / tests / CI

| Fichero | Specs | Riesgo | Orden | Nota |
|---|---|---|---|---|
| `backend/tests/**` | GA-GOV-03 (T1, 7 ficheros) + todas las tranches (tests nuevos por spec) | Medio | T1 primero; cada tranche añade sus tests | Los 25 rojos se corrigen **solo** en T1 |
| `e2e/**` | GA-GOV-03 (T1, 6 specs de proceso) + T4-T11 (fixtures/regresiones) | Medio | T1 → luego recertificación T12 | Los 12 rojos se corrigen en T1 |
| `.github/workflows/**` | GA-GOV-03 (OD-23) | Bajo | T1 | CI a `push` sin bloquear `docker-push` |
| `audit/remediation/REMEDIATION_BACKLOG.md` + `specs/remediation/INDEX.md` | GA-GOV-03 (reconciliación de backlog: R-189, GA-UAT-09, OD-21…25) | Bajo | T1 | — |
| `audit/ga-pre-sap-program/**` | Este programa (T0) | — | Congelado | — |

## 4 · Síntesis de colisiones y regla operativa

- **Familias serializadas**: `auth` (T2), `validators` (T7), `audit` (T8), `captura FE` (T4→T5→T6), `review` (T2 permisos→T10 servicio), `lots` (T3→T7→T8).
- **Merges confirmados por esta matriz**: R-204+R-216 (dashboard), R-192+R-193+R-211 (validators/cierre — ya en T7), P1-12+R-198+R-219 (audit/evidencias — ya en T8), R-196+R-215 (maestros/estabilidad — ya en T9), R-195+R-122 (usuarios).
- **Ninguna tranche toca dos ficheros de la misma familia a la vez**; el ejecutor de cada tranche declara su lista de ficheros antes de empezar (declaración en el commit).
