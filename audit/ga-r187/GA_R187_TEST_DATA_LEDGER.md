# GA-R187 · LEDGER DE DATOS DE PRUEBA

Entorno: producción de prueba (empresa 1). Regla: **ningún usuario humano modificado**; actores 100 % sintéticos; mecanismos por API oficial; sin mutación directa de BD.

## 1 · Actores y accesos (todos efímeros)

| Registro | ID | Estado final | Propósito | Limpieza |
|---|---|---|---|---|
| Rol «R187 OP» | 67 | **desactivado** (PUT 200) | crear/consultar lote, eventos, IPE, UI | desactivado |
| Rol «R187 REV» | 68 | **desactivado** | revisión (review:review) | desactivado |
| Rol «R187 APP» | 69 | **desactivado** | aprobación (approvals:approve) | desactivado |
| Rol «R187 NOPERM» | 70 | **desactivado** | E2E-14 (sin reports:read) | desactivado |
| Usuario `ra187op` | 136 | **baja lógica** (204) | actor autorizado (OP/UI/E2E) | baja + grant revocado |
| Usuario `ra187rev` | 137 | **baja lógica** | revisor | baja + grant revocado |
| Usuario `ra187app` | 138 | **baja lógica** | aprobador | baja + grant revocado |
| Usuario `ra187nobu` | 139 | **baja lógica** | E2E-13 (sin concesión) | baja (sin grant) |
| Usuario `ra187noperm` | 140 | **baja lógica** | E2E-14 | baja + grant revocado |
| Concesiones broiler | — | **revocadas** (4×200) | habilitar lectura/UI | revocadas |
| Ventana BU broiler (empresa 1) | — | **OFF restaurada** (4×OFF verificado) | batería productiva | OFF |

Credenciales: `/tmp/ga187_credentials.txt` (600) **destruido**; sesiones de sintéticos invalidadas por baja lógica.

## 2 · Fixtures de negocio RETENIDOS (oficiales, empresa 1)

| Lote | Código | Insumos (1000 aves) | IPE OD-22 | Banda | Eventos (IDs) |
|---|---|---|---|---|---|
| 54 | `L-R187-DET` | 19 d · 50 muertes · 2000 g · 3000 kg | **333.3** | 🟢 | 63/64/65 |
| 55 | `L-R187-LOW` | 28 d · 100 muertes · 1500 g · 2000 kg | **241.1** | 🔴 | 66/67/68 |
| 56 | `L-R187-MID` | 28 d · 50 muertes · 2500 g · 3000 kg | **282.7** | 🟡 | 69/70/71 |
| 57 | `L-R187-B249` | 10 d · 20 muertes · 1020 g · 4000 kg | **249.9** | 🔴 | 72/73/74 |
| 58 | `L-R187-B250` | 10 d · 0 muertes · 1000 g · 4000 kg | **250.0** | 🟡 | 75/76 |
| 59 | `L-R187-B300` | 10 d · 0 muertes · 1200 g · 4000 kg | **300.0** | 🟢 | 77/78 |

Todos los eventos por cadena completa (submit → review → approve; segregada) y **approved**. Retenidos: evidencia reproducible para futuras verificaciones/observación del propietario; identificables por prefijo `L-R187-`.

## 3 · Datos en solo lectura (sin modificación)

| Registro | Uso | Estado |
|---|---|---|
| Lote 11 | E2E-02 escala + R-184 técnico (5.6; pre 556.6) | Intacto |
| Lote 53 | E2E-02 escala (378.9; pre 37894.7) | Intacto |
| Lotes 33/35 | control cero | Intactos |
| Lote 14 (empresa 3) | E2E-11 ajeno | Intacto |
| Área 16 (inactiva) | spot GA-FE-07 (400) | Intacta |

## 4 · Higiene

- Sin usuarios humanos modificados (admin verificado operativo post-limpieza).
- Auditoría preservada (altas/bajas/roles en AuditLog del sistema).
- Sin residuo inseguro: sin tokens/sesiones temporales persistidos; temporales `/tmp/ga187*` destruidos al cierre.
