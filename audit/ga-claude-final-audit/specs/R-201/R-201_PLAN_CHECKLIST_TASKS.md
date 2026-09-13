# R-201 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · HEAD de partida `c0b4afc` · GA-REM a asignar al autorizar (siguiente libre GA-REM-043).

**Regla de la tranche: RED antes que GREEN; producto sólo en C2.** Sin migración, sin endpoint, sin permiso.

## PLAN por tranches

| Tranche | Contenido | Entrada | Salida | Estado |
|---|---|---|---|---|
| **C1 · Gobernanza + RED** | Finding/spec/clarificaciones/AC/diseño (hecho); escribir RED `test_r201_sap_no_context.py` + ampliación `test_sap_transversal.py`; ejecutar RED (rojo en 4, verde en 2 controles) | este paquete | commit C1 + `evidence/red/` | ☐ |
| **C2 · Implementación** | `_company_filter`→`false()`; guardas al inicio de consolidate/export/retry; limpieza opcional `get_company_filter`; GREEN dirigido + regresión SAP; sensibilidad tras commit | C1 | commit C2 + `evidence/green/` | ☐ |
| **C3 · Certificación runtime (API)** | Desplegado el backend, E2E API `R201-RT-01…06` sobre pila local/nube de pruebas; artefacto JSON | C2 | `evidence/r201/runtime-c3.json` + certificación | ☐ |
| **C4 · Cierre** | Backlog: R-201 `CLOSED` con GA-REM; referencias R-112/GA-REM-017/eje seguridad | C3 | backlog actualizado | ☐ |

## CHECKLIST

- ☐ C1.1 RED escrita (4 rojos + 2 controles) y ejecutada en HEAD; salida a `evidence/red/`
- ☐ C1.2 Commit C1 sin producto
- ☐ C2.1 Predicado fail-closed + guardas tempranas
- ☐ C2.2 AC-R201-01…04 rojos→verdes; AC05/06 controles verdes
- ☐ C2.3 Regresión `test_sap.py` + `test_sap_transversal.py` completa verde
- ☐ C2.4 Sensibilidad S1/S2 ejecutada tras commit y revertida
- ☐ C3.1 Run API con artefacto (dos empresas, tres actores)
- ☐ C4.1 Backlog + referencias

## TAREAS

| ID | Tarea | Ficheros | Tamaño | Depende | Tranche |
|---|---|---|---|---|---|
| T-01 | RED de frontera de contexto | `backend/tests/test_r201_sap_no_context.py` (nuevo) | M | — | C1 |
| T-02 | Ampliar frontera global situada / actor empresa | `backend/tests/test_sap_transversal.py` | S | — | C1 |
| T-03 | Predicado fail-closed | `backend/app/integrations/sap/service.py:76-81` | S | T-01 | C2 |
| T-04 | Guardas tempranas consolidate/export/retry | `sap/service.py:158-161,208,239-242,258,404-408` | S | T-03 | C2 |
| T-05 | Limpieza `get_company_filter` (opcional C-05) | `backend/app/auth/security.py:170-178`, `dependencies.py:2` | S | — | C2 |
| T-06 | GREEN + regresión + sensibilidad | — | S | T-03…T-05 | C2 |
| T-07 | E2E API + certificación | `specs/R-201/evidence/r201/` | M | T-06 | C3 |
| T-08 | Backlog/cierre | `audit/remediation/REMEDIATION_BACKLOG.md` | S | T-07 | C4 |

## SENSIBILIDAD (tras commit C2)

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| S1 | restaurar `true()` en `_company_filter` | AC-R201-01/02/03/04 |
| S2 | mover la guarda de `retry_failed` de nuevo al final | AC-R201-04 |

## Regresión obligatoria

`test_sap.py` · `test_sap_transversal.py` · `test_sap_references.py` (si existe) · suite completa backend por diferencia vs línea base GA-GOV-03 · sin diff en routers/esquemas/modelos · verificación de que `FEATURE_SAP_ENABLED` no se altera.
