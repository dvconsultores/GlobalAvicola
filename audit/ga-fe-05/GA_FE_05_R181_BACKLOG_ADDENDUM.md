# GA-FE-05 · ADDENDUM CANÓNICO R-181 (sin reescribir el backlog)

Fecha: 2026-09-11 · Generación: `index-WUv1-F9o.js` (`005a252`) · Baseline de entrada: `b448f3e`.

Este addendum **no modifica** la entrada histórica de `R-181` en
`audit/remediation/REMEDIATION_BACKLOG.md` (snapshot intacto). Registra su cierre.

## Entrada histórica (resumen fiel)

- `R-181` · P2 · «el envío/reenvío explícito a revisión no tiene control en la interfaz».
- Raíz: vertical UI nunca cableada. Requisito: `docs/12 §2` + `OD-17.b` + `spec §4.10`. Backend: IMPLEMENTED.

## Resolución (GA-FE-05)

| Dimensión | Resultado |
|---|---|
| Implementación | CTA state-aware en `/operations/:id` (submit/resubmit) + chip localizado + refresh sin optimismo |
| Permiso | `operations:create` (contrato real, sin permisos nuevos) |
| Estados | `registered` ⇒ Enviar · `returned`/`rejected` ⇒ Reenviar (`OD-17.a/b`) · resto sin acción |
| Pruebas | 10/10 automatizados + 13 casos runtime autenticados |
| Evidencia | `audit/ga-fe-05/` (RED, runtime, red, capturas, ledger, cierre, certificación) |
| Backend | 0 cambios · 0 migraciones · 0 permisos |
| Estado final | **R-181 = CLOSED** |

## No duplicación

`R-98`/`R-119` (cerrados) aportan el evaluador de autoridad reutilizado; no se crean IDs nuevos.
`R-182` permanece **UNCHANGED / OPEN** (no abordado aquí).
