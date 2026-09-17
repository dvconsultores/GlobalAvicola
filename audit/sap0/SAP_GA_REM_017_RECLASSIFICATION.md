# SAP-0 · SAP_GA_REM_017_RECLASSIFICATION

Fecha: 2026-09-17 · Fase SAP-0 (SPEC ONLY)
Objeto: reevaluar `GA-REM-017 — INTEGRACIÓN SAP REAL` (`specs/remediation/GA-REM-017-SAP-REAL-INTEGRATION.md`, estado `BLOCKED_EXTERNAL`) con la evidencia legacy + discovery de SAP-0.
**Invariante preservada**: `REAL SAP INTEGRATION = NOT IMPLEMENTED` (el código no cambia; no existe `RealSapAdapter`; nada simula éxito).

Estados permitidos (mandato §37): `RESOLVED_BY_LEGACY_EVIDENCE` · `PARTIALLY_RESOLVED` · `STILL_BLOCKED_CURRENT_SAP` · `OWNER_DECISION_REQUIRED`.

---

## 1 · Reevaluación elemento por elemento (tabla original §«Información que falta»)

| Elemento de GA-REM-017 | Antes (2026-09) | Reevaluación SAP-0 | Nuevo estado | Evidencia |
|---|---|---|---|---|
| Mecanismo de integración (OData · SOAP · IDoc · RFC/BAPI) | No disponible | El legacy prueba que **existían** SQL directo a HANA y al menos 1 servicio SOAP Z; la disponibilidad **actual** sigue sin verificar | `PARTIALLY_RESOLVED` | `SAP_LEGACY_REPOSITORY_AUDIT.md §3,§7` |
| URL del servicio | No disponible | Endpoints históricos observados (WS `vhemsws1wd01:44300`, host `vhemsds4ci…`); vigencia desconocida | `PARTIALLY_RESOLVED` | idem §7 |
| Método de autenticación | No disponible | Histórico: usuario/clave HANA por env + Basic en SOAP; modelo actual por definir | `PARTIALLY_RESOLVED` | §3 (T-05,T-18) |
| Estructura del payload esperado por SAP (export) | No disponible | El legacy **nunca escribió** en SAP; no hay evidencia de contrato de escritura | `STILL_BLOCKED_CURRENT_SAP` | §5 (procesos solo lectura) |
| Estructura de la respuesta y códigos de error | No disponible | Legacy parseaba XML genérico sin códigos; contrato formal inexistente | `STILL_BLOCKED_CURRENT_SAP` | §7 |
| Credenciales | No disponibles | Siguen sin estar en el proyecto; se agrega modelo conceptual de custodia | `OWNER_DECISION_REQUIRED` (`SAP-CUSTODY-01`/AOD-12) | `SAP_OWNER_DECISIONS_REQUIRED.md` |
| Catálogo de tipos de movimiento SAP | No confirmado | Patrones observados (641/303) como **lectura**, no como catálogo oficial | `PARTIALLY_RESOLVED` | §6 (BWART) |
| Ventanas de disponibilidad y política de reintentos | No disponible | Nada nuevo; será parte del probe autorizado | `STILL_BLOCKED_CURRENT_SAP` | `SAP_DISCOVERY_EXECUTION_PLAN.md §2` |

## 2 · Efecto sobre los AC preliminares de GA-REM-017

`AC01–AC06` (envío real, idempotencia, reconciliación de timeout, errores, no-ficticios, cadena reconstruible) **permanecen SIN VERIFICAR**: dependen de un SAP real, que SAP-0 no contacta. SAP-0 aporta la **ruta para desbloquearlos**: contrato inbound formal + plan de probe + gates de autorización.

## 3 · Clasificación de bloqueo resultante

```
GA_REM_017 = STILL_BLOCKED_EXTERNAL (por ausencia de evidencia CURRENT de SAP)
  · subelementos parcialmente resueltos = pistas legacy (NO contrato vigente)
  · subelemento de custodia = OWNER_DECISION_REQUIRED (AOD-12/SAP-CUSTODY-01)
  · ningún subelemento pasa a RESOLVED_BY_LEGACY_EVIDENCE como contrato actual
REAL SAP INTEGRATION = NOT IMPLEMENTED   ← invariante preservada
```

Regla aplicada (mandato §37): la evidencia legacy **no convierte** a GA-REM-017 en resuelto; se reclasifica **por tipo de bloqueo restante**, y el desbloqueo pasa por `SAP-BASIS-01` + probe + decisiones Owner.

## 4 · Relación con GL-OD-06

`GL-OD-06` (go-live) queda **`BLOCKED_EXTERNAL_SAP_INFORMATION`** (§38): el landscape y las fuentes no pueden darse por definidos sin evidencia current. La spec SAP-0 reduce la **incertidumbre sobre qué preguntar y qué validar**, pero no sustituye la respuesta de SAP.
