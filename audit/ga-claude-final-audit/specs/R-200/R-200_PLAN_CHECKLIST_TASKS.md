# R-200 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · Base HEAD `c0b4afc`.

## PLAN

| Fase | Contenido | Entregable | Estado |
|---|---|---|---|
| **C1 · Gobernanza + RED** | paquete · `backend/tests/test_r200_refresh_token_as_access.py` con RED-01…04 rojas por el defecto y CTL-05…08 + DOC-10 verdes · sin producto | commit «R-200 C1: gobernanza + RED (4 rojas, 5 controles)» | ☐ |
| **C2 · Implementación** | T-02 (una comprobación) · GREEN dirigido · suites vecinas · suite completa PG sin rojos nuevos | commit «R-200 C2: …» | ☐ |
| **C2s · Sensibilidad** | M1 (quitar la comprobación) rompe RED-01…04; revertir con `git checkout` desde la raíz | tabla en certificación | ☐ |
| **C3 · Certificación runtime** | despliegue · E2E-01…04 (no destructivas) · evidencia · `GA_CLAUDE_R200_RUNTIME_CERTIFICATION.md` · nota de interacción con `GA-REM-003` en registro y backlog | commit «R-200 C3: …» | ☐ |
| **C4 · UAT** | no aplica (`C-07`) | — | ☐ |

Puede ejecutarse en la misma tranche que `R-199` (mismo fichero `security.py`, cambios disjuntos).

## CHECKLIST

| AC | Tarea | Fichero | Prueba | Evidencia | Estado |
|---|---|---|---|---|---|
| AC01…AC04 | T-02 | `auth/security.py:87-93` | RED-01…RED-04 | GREEN + E2E-01/02 | ☐ |
| AC05…AC08 | — | — | CTL-05…CTL-08 | verde antes/después + E2E-03/04 | ☐ |
| AC09 | T-02 | ídem | aserción en RED-01 (`audit_logs` sin fila nueva; `get_current_audit_user()` no fijado) | GREEN | ☐ |
| AC10 | T-01 | — | DOC-10 | verde | ☐ |
| AC11 | T-03 | — | suites vecinas + completa | log | ☐ |
| AC12 | T-01 | — | — | `git diff --stat` | ☐ |
| AC13 | T-05 | registro, backlog | — | diff documental | ☐ |
| AC14 | T-04 | — | mutación M1 | tabla | ☐ |

## TAREAS

| ID | Contenido | Ficheros | Tamaño | Depende | Estado |
|---|---|---|---|---|---|
| T-01 | Gobernanza + fichero RED (login real con `test_credentials`; tokens manuales con `jwt.encode` y `settings.JWT_SECRET_KEY`); verificar que las 4 RED fallan en la aserción esperada | `specs/R-200/**`, `backend/tests/test_r200_refresh_token_as_access.py` | S | — | ☐ |
| T-02 | `get_current_user`: `if payload.get("type") != "access": raise HTTPException(401, "Token inválido: no es un token de acceso")` tras `decode_token`, antes de `sub`; `logger.warning` sin token (`C-03`) | `backend/app/auth/security.py:87-93` | XS | T-01 | ☐ |
| T-03 | GREEN: `pytest tests/test_r200_refresh_token_as_access.py tests/test_security_regression.py tests/test_rbac.py tests/test_auth.py tests/test_session_payload.py tests/test_multicompany_isolation.py`; suite completa PG | — | S | T-02 | ☐ |
| T-04 | Sensibilidad M1 tras el commit C2 | — | XS | T-03 | ☐ |
| T-05 | C3: sondas E2E-01…04 con el actor UAT-09, evidencia `evidence/r200/runtime-c3.json`, certificación, nota «no cierra `GA-REM-003 AC04`» en `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md` y `REMEDIATION_BACKLOG.md` | `audit/ga-claude-final-audit/**`, `audit/remediation/REMEDIATION_BACKLOG.md` | S | T-03 | ☐ |
