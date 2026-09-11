# GA-FE-06-A · LEDGER DE DATOS DE PRUEBA

## Identidades (empresa 1 salvo indicación)

| Recurso | ID | Nombre | Detalle | Retirada |
|---|---|---|---|---|
| Rol | 54 | «Operador Lotes GA-FE-06-A» | dashboard/lots read · lots:create · lots:update · masters:read | **desactivado** (`is_active:false`) |
| Rol | 55 | «Solo-lectura GA-FE-06-A» | dashboard:read · lots:read | **desactivado** |
| Usuario F | 120 | `ga6a.operador` | rol 54 · concesión `broiler` (ventana) | **baja lógica aplicada** (DELETE 204 → `is_active:false`) |
| Usuario G | 121 | `ga6a.sinventana` | rol 54 · sin concesión | **baja lógica aplicada** |
| Usuario H | 122 | `ga6a.rbac` | rol 55 | **baja lógica aplicada** |
| Credenciales | — | `~/ga06a_credentials.txt` · tokens `/tmp/ga06a_*` | efímeras | **destruidas** (verificado «No existe el fichero») |

## Áreas

| Recurso | ID | Código | Empresa | Retirada |
|---|---|---|---|---|
| Área A | 4 | `GA6A-AREA-A1` «Nave Operativa» | 1 | **baja lógica aplicada** |
| Área X | 5 | `GA6A-AREA-XB` «Área Ajena» | 3 | **baja lógica aplicada** |

## Lotes (empresa 1 · retenidos como histórico/evidencia)

| ID | Código | Significado |
|---|---|---|
| 26 | `GA6A-RED-FOREIGN-161729` | **Evidencia RED**: alta con área ajena aceptada (201, `area_id:5`) en la generación pre-fix |
| 27 | `GA6A-RED-BASE-161729` | Base de la prueba de edición RED (mutado a 5 y restaurado a 4 durante la captura pre-fix) |
| 32 | `GA6A-GREEN-OK-…` | **Evidencia GREEN**: alta válida con Área A + fecha prevista exacta |
| 33 | `GA6A-GREEN-NULL-…` | Control NULL |
| — | `GA6A-GREEN-UPDATE-…` | Base de la edición GREEN (denegada a ajeno; conserva Área A) |
| — | `GA6A-GREEN-NOBU-…` y `GA6A-GREEN-RBAC-…` | **Artefactos del arnés** (creados por F durante el bug del script de negativos; documentado en `GA_FE_06_A_RUNTIME_EVIDENCE.md §Corrección`) |

Intentos denegados (`GA6A-GREEN-FOREIGN-…`, `GA6A-GREEN-UNK-…`, `GA6A-NEG-*`, `GA6A-PROBE-1`, `GA6A-DIAG-*`): **sin persistencia** (verificado por búsqueda y por contrato).

## Estado de entorno al cierre

- BU empresa 1: **4×OFF** (estado de entrada restaurado, verificado).
- Concesión F→`broiler`: **revocada** (`revoked_at` con valor).
- Usuarios/roles de prueba: inoperantes. Áreas: dadas de baja lógica.
- Credenciales y tokens: destruidos. Repositorio: sin secretos (scans de C5/C6/C7).
- Auditoría: **preservada** (no se borró ninguna entrada; los registros de esta tranche quedan).
