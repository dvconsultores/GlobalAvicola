# GA-FE-06 · EVIDENCIA DE HIGIENE (§101)

Ejecutada al cierre de la tranche, tras la certificación runtime. Fuente de identidades: `~/ga06_credentials.txt` (600, destruido) + tokens `/tmp/ga06_*` (destruidos).

## Resultado verificado

| Acción | Resultado verificado |
|---|---|
| Concesión C→`broiler` | **Revocada** (`revoked_at` con valor, `is_effective:false`) |
| Usuarios 117/118/119 (`ga6.*`) | **Retirados** (DELETE → 204; el contrato del producto es baja lógica: quedan `is_active:false`, verificado en listado) |
| Roles 52/53 (`…GA-FE-06`) | **Desactivados** (`is_active:false` devuelto por la API; ya no aparecen en el listado de roles activos) |
| BU `broiler` (empresa 1) | **Restaurada a OFF** — estado final del catálogo: `[('breeder', False), ('broiler', False), ('grandparent', False), ('hatchery', False)]` = estado de entrada |
| Áreas 1/2 (`GA6-AREA-A1/A2`) y 3 (`GA6-AREA-XB`) | **Baja lógica** (`is_active:false`), conforme al contrato del modelo («un área con histórico se da de baja») |
| Credenciales y tokens | **Destruidos**: `~/ga06_credentials.txt`, `/tmp/ga06_admin_token`, `/tmp/ga06_admin3_token`, `/tmp/ga06_c_token`, JSON temporales. Verificado: «No existe el fichero» |
| Repositorio | Ningún secreto entró al repo (scan del diff indexado en C1/C2/C4 = limpio) |

## Residual declarado (honestidad)

- Los **lotes `GA6-*` permanecen** como registros históricos del producto (no existe borrado de lote; es correcto). Son identificables por código y quedan documentados en el ledger con su propósito original (incluido el lote 17 del RED y el lote 18 de la evidencia N-1).
- El **escáner SLA horario** puede producir en el futuro avisos `lot_near_close` para los lotes de ventana (+3/+1) retenidos. Sus destinatarios se resolverán en ese momento según el producto (originador dado de baja + gerentes/supervisores de área —ninguno asignado—) ⇒ si no hay destinatario válido, no hay aviso; en ningún caso cruza empresa.
- Los usuarios retirados quedan como filas inactivas (contrato de baja lógica del producto); no pueden iniciar sesión (verificado indirectamente: sin credenciales activas emitidas y `is_active:false`).

## Cumplimiento del criterio de limpieza

- [x] Identidades de prueba inoperantes (inactivas/desactivadas)
- [x] Accesos de ventana restaurados (4×OFF)
- [x] Datos de organización dados de baja lógica
- [x] Secretos efímeros destruidos (fichero verificado inexistente)
- [x] Trazabilidad completa en `GA_FE_06_TEST_DATA_LEDGER.md` + este documento
