# GA-R184 · LEDGER DE DATOS DE PRUEBA

Entorno: producción de prueba (empresa 1 Avícola Global C.A. y ventana puntual en empresa 3). Regla: ningún usuario humano modificado.

## 1 · Registros creados y su disposición

| Alias | Empresa | Registro | Estado | Propósito | Creación | Limpieza | ¿Retenido? |
|---|---|---|---|---|---|---|---|
| Rol 61 «Aprobador KPI R-184» | 1 | rol | **desactivado** | aprobar eventos del fixture F3 (segregación) | API oficial | desactivado §69 | No (registro en baja) |
| Rol 62 «Operador KPI R-184» | 1 | rol | **desactivado** | E2E-11 (sin concesión) | API oficial | desactivado | No |
| Rol 63 «Consulta sin reportes R-184» | 1 | rol | **desactivado** | E2E-12 (sin RBAC) | API oficial | desactivado | No |
| Usuario 129 `r184.aprob` | 1 | usuario | **baja lógica** (204) | actor UI/E2E con empresa+grant | API oficial | baja + concesión revocada | No |
| Usuario 130 `r184.lotes` | 1 | usuario | **baja lógica** (204) | E2E-11 | API oficial | baja | No |
| Usuario 131 `r184.consulta` | 1 | usuario | **baja lógica** (204) | E2E-12 | API oficial | baja | No |
| Concesión `129→broiler` | 1 | grant | **revocada** (200) | UI/E2E | API oficial | revocada | No |
| Lote **53** `R184-E2E-CLOSE-…` | 1 | lote | **cerrado** (BR-05 cumplida) | E2E-05 lote cerrado | API oficial (alta+eventos+flujo review/approve+cierre) | **sin limpieza** | **Sí — evidencia** |
| Eventos **61/62** (peso 1800g/100; alimento 2500 kg) | 1 | eventos | **aprobados** | inputs de F3 | API oficial (submit→review→approve) | **sin limpieza** | **Sí — evidencia** |
| BU `broiler` empresa 1 | 1 | habilitación | **OFF restaurada** (4×OFF verificado) | ventana de lecturas productivas | API oficial | OFF | estado original |
| BU `broiler` empresa 3 | 3 | habilitación | **OFF restaurada** (4×OFF verificado) | E2E-09 lote ajeno | API oficial | OFF | estado original |

## 2 · Registros usados en solo lectura (sin modificación)

| Alias | Uso | Estado verificado |
|---|---|---|
| Lote 11 `L-BO-2026-05` | E2E-02/03/04 + UI (edad 110, IPE 556.6) | Intacto |
| Lote 33 / 35 (GA-FE-06-A) | E2E-01 (antes 500), E2E-06/07 | Intactos |
| Lote 14 empresa 3 | E2E-09 | Intacto |
| Área 16 (UAT GA-FE-07, inactiva) | Spot regresión GA-FE-07 (400 «Área inactiva») | Intacta |

## 3 · Higiene

- Credenciales efímeras `~/ga_r184_credentials.txt` — **destruidas** (verificado). Temporales `/tmp/ga184_*` — **destruidos** (verificado).
- Auditoría del sistema preservada (incluye las mutaciones de fixture, como evidencia del flujo oficial).
- **Ningún usuario humano modificado** (admin verificado operativo post-limpieza; aceptaciones GA-FE-02..07 intactas).
