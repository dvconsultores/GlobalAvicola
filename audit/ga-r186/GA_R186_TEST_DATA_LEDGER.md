# GA-R186 · LEDGER DE DATOS DE PRUEBA

Entorno: producción de prueba (empresa 1). Regla: **ningún usuario humano modificado**; solo lectura sobre lotes existentes.

## 1 · Registros creados y su disposición

| Alias | Empresa | Registro | Estado | Propósito | Creación | Limpieza | ¿Retenido? |
|---|---|---|---|---|---|---|---|
| Rol 65 «Operador G-05 UAT R-186» | 1 | rol | **desactivado** | actor autorizado (reports:read) / sin concesión | API oficial | desactivado §68 | No |
| Rol 66 «Consulta sin reportes R-186» | 1 | rol | **desactivado** | E2E-12 (sin `reports:read`) | API oficial | desactivado | No |
| Usuario 133 `r186.kpi` | 1 | usuario | **baja lógica** (204) | actor autorizado con concesión (E2E-02/10) | API oficial | baja + grant revocado | No |
| Usuario 134 `r186.sinbu` | 1 | usuario | **baja lógica** (204) | E2E-11 (sin concesión) | API oficial | baja | No |
| Usuario 135 `r186.noreport` | 1 | usuario | **baja lógica** (204) | E2E-12 (sin RBAC) | API oficial | baja | No |
| Concesión `133→broiler` | 1 | grant | **revocada** (200) | habilitar lectura | API oficial | revocada | No |
| Ventana BU `broiler` empresa 1 | 1 | habilitación | **OFF restaurada** (4×OFF verificado) | lecturas productivas de la batería | API oficial | OFF | estado original |

## 2 · Datos usados en solo lectura (sin modificación)

| Alias | Uso | Estado |
|---|---|---|
| Lote 11 `L-BO-2026-05` | E2E-02/03 (determinista) + regresión R-184 | Intacto |
| Lotes 33/35 | E2E-01/04/08 (original 500 → 200) | Intactos |
| Lote 14 (empresa 3) | E2E-09 (ajeno) | Intacto |
| Área 16 (inactiva) | Spot GA-FE-07 (400) | Intacta |

## 3 · Higiene

- Credenciales `~/ga_r186_credentials.txt` y temporales `/tmp/ga186_*` — **destruidos** (verificado).
- Auditoría preservada (altas/bajas del fixture incluidas).
- **Ningún humano modificado** (admin verificado operativo post-limpieza); aceptaciones GA-FE-02..07 / R-184 / GA-UAT-06 intactas.
