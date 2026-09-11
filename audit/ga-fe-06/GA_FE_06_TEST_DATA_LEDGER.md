# GA-FE-06 · LEDGER DE DATOS DE PRUEBA

Todos los fixtures son identificables por prefijo `GA6-`/`ga6.`. Estado de retirada al cierre de la tranche (higiene §101) marcado en la última columna.

## Identidades

| Recurso | ID | Nombre/Usuario | Detalle | Retirada |
|---|---|---|---|---|
| Rol | 52 | «Operador Lotes GA-FE-06» | 5 permisos (dashboard/lots/masters/operations read + lots:create) | **desactivado** (`is_active:false`) |
| Rol | 53 | «Solo-lectura GA-FE-06» | dashboard:read + lots:read | **desactivado** |
| Usuario C | 117 | `ga6.operador` | empresa 1 · rol 52 · concesión broiler | **retirado** (DELETE 204 → baja lógica `is_active:false`) |
| Usuario D | 118 | `ga6.rbac` | empresa 1 · rol 53 | **retirado** |
| Usuario E | 119 | `ga6.sinventana` | empresa 1 · rol 52 · sin concesión | **retirado** |
| Credenciales | — | `~/ga06_credentials.txt` (600) · tokens `/tmp/ga06_*` | efímeras | **destruidas y verificadas inexistentes** |

## Datos

| Recurso | ID | Código | Detalle | Retirada |
|---|---|---|---|---|
| Área (emp. 1) | 1 | `GA6-AREA-A1` | Nave Norte (GA-FE-06) | **baja lógica aplicada** |
| Área (emp. 1) | 2 | `GA6-AREA-A2` | Nave Sur (GA-FE-06) | **baja lógica aplicada** |
| Área (emp. 3) | 3 | `GA6-AREA-XB` | Área Del Sur (GA-FE-06) — inquilino ajeno | **baja lógica aplicada** |
| BU `broiler` (emp. 1) | — | — | habilitada durante la tranche | **restaurada OFF** (catálogo 4×OFF verificado) |
| Concesión C→broiler | — | — | efectiva durante la tranche | **revocada** (`revoked_at` con valor) |
| Lote | 17 | `GA6-RED-…` | RED: PLD rellenada y perdida (pre-fix; NULL persistido) | documentar retención (histórico) |
| Lote | 18 | `GA6-XT-CHECK-1` | Evidencia N-1 (área 3 de otra empresa persistida vía API) | documentar retención (evidencia) |
| Lote | 19 | `GA6-E01-…` | E2E-01: PLD 2026-09-21 · área 1 | documentar retención |
| Lote | 20 | `GA6-B3-…` | SLA frontera +3 · 2026-09-14 · área 1 | documentar retención |
| Lote | 21 | `GA6-I1-…` | SLA dentro +1 · 2026-09-12 · área 1 | documentar retención |
| Lote | 22 | `GA6-PAST-…` | SLA pasado −1 · 2026-09-10 | documentar retención |
| Lote | 23 | `GA6-NN-…` | NULL explícito | documentar retención |
| Lote | 24 | `GA6-MOB-…` | Móvil: PLD 2026-09-12 · área 2 | documentar retención |
| Lote | 25 | `GA6-VERIFY-1` | Sesión de verificación (NULL) | documentar retención |

## Criterio de retirada

- **Producto real (lotes)**: el lote es un registro histórico del negocio; no existe borrado (correcto). Se documenta su presencia con códigos `GA6-` inequívocos. La fecha de negocio de referencia de la corrida: **2026-09-11**.
- **Identidades y accesos**: se retiran por completo (rol/usuario/concesión) o se desactivan; BU `broiler` se restaura al estado de entrada (**OFF**, como las otras tres).
- **Áreas**: baja lógica (contrato del modelo: «un área con usuarios, lotes o avisos históricos se da de baja»).
- **Secretos**: destrucción total de ficheros (credenciales y tokens) al cierre; nada quedó en el repo.
