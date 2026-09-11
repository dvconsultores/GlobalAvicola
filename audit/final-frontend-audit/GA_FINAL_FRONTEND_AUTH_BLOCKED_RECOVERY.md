# FINAL FRONTEND AUDIT · RECUPERACIÓN DE LAS 15 FILAS HISTÓRICAMENTE BLOQUEADAS POR AUTENTICACIÓN

Fecha: 2026-09-11 · Blocker histórico: `AUTHENTICATED_RUNTIME_BLOCKER` (§38 del encargo original; `GA-REM-004` rotó credenciales; seeds prohibidos). Las 15 quedan **ejercitadas y clasificadas** con actores sintéticos oficiales (empresa 1).

| FVA | CAP | Blocker histórico | Actor usado (hoy/previo) | Empresa | BU | Concesión | RBAC | Ruta | Resultado runtime | ¿Sigue bloqueada? | Estado final |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FVA-01 | CAP-SES-01 | sin cuentas | todos los actores | 1 | per-actor | per-actor | login | `/login` | sesión real + relogin | NO | F_C_OA |
| FVA-02 | CAP-SES-02 | sin cuentas | fdaop | 1 | 4 | — | — | `/users/{id}/password` (API oficial) | 204 → relogin 200 → 204 | NO | VNC |
| FVA-03 | CAP-SES-03 | sin cuentas | fdaop | 1 | 4 | — | — | `/profile` | carga | NO | VNC |
| FVA-04 | CAP-SES-04 | sin cuentas | fdaop/global | 1 | — | — | dashboard | header/dashboard | nombre de empresa visible | NO | F_C_OA |
| FVA-06 | CAP-ADM-01 | sin cuentas | fdaadm | 1 | — | — | masters:read | `/masters/companies` | 1 fila | NO | VNC |
| FVA-13 | CAP-ADM-08 | patrón denegación-vacío | fdaadm | 1 | — | — | users:* | `/users` | 20 filas + alta | NO | F_C_OA |
| FVA-15 | CAP-ADM-10 | sin cuentas | fdaadm | 1 | — | — | users:create/update | form de usuario | 3 selects de rol | NO | F_C_OA |
| FVA-16 | CAP-BU-01 | gating por unidad | fdaop (4 unidades) | 1 | 4 ON | 4 grants | operations:read | `/menu/poultry` + etapas | hub 5 tarjetas; etapas cargan | NO | F_C_OA |
| FVA-20 | CAP-OPS-01 | sin cuentas | fdaop | 1 | breeder+ | grant | operations:* | `/operations` + recepción | lista + formulario | NO | VNC |
| FVA-22 | CAP-OPS-03 | sin cuentas | fdaop | 1 | 4 | grants | operations:* | `/operations` (feed/water/weight/…) | superficies cargan | NO | VNC |
| FVA-26 | CAP-OPS-07 | R-181 secundario | fdarev + fdaop | 1 | broiler | grant | review/approvals | `/review`, `/approvals`, submit | cargan; submit certificado | NO | VNC |
| FVA-29 | CAP-OPS-10 | sin entrada (luego auth) | fdaop/fdamob | 1 | broiler+ | grant | lots:read/create | `/lots*` (hub) | descubrible; 82-95 filas | NO | F_C_OA |
| FVA-30 | CAP-OPS-11 | R-52 | fdaop (acciones) | 1 | breeder+ | grant | operations:create/delete | detalle de operación | acciones presentes | NO (R-52 es infra, no auth) | VNC |
| FVA-31 | CAP-OPS-12 | sin cuentas | fdaop + aceptaciones R-184/187 | 1 | broiler+ | grant | dashboard/reports | `/`, `/kpi`, `/lots/:id`, `/reports` | IPE 333.3 · G-05 5.1 | NO | F_C_OA |
| FVA-32 | CAP-OPS-13 | backend partial | fdaadm | 1 | — | — | sap:read | `/sap` | UI carga; integración real P-08 | NO (BLOCKED_EXTERNAL de producto, no auth) | BLOCKED_EXTERNAL |

**Recuperadas/ejercitadas: 15/15 · Siguen legítimamente bloqueadas por auth: 0 · Desconocidas: 0.**
(dos filas pasan a estados de gobernanza/infra propios: R-52 en FVA-30 · P-08/R-112 en FVA-32 — no son bloqueos de autenticación.)
