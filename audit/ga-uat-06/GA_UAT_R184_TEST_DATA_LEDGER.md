# GA-UAT-06 · LEDGER DE DATOS DE PRUEBA

Sesión: aceptación del propietario de **R-184 (KPI / IPE)** · Entorno: producción de prueba (empresa 1 = Avícola Global C.A.).

## Registros creados para la sesión

| Registro | Identificador | Empresa | BU | Mecanismo de creación | Propósito | Estado actual | Limpieza prevista | ¿Se retiene? |
|---|---|---|---|---|---|---|---|---|
| Rol «Operador IPE UAT R-184» | 64 | 1 | — | API oficial (roles) | cuenta de trabajo de la sesión (lecturas) | activo | desactivar tras la decisión | No |
| Usuario `uat6.ipe` | 132 | 1 | concesión Engorde | API oficial (users) | actor ordinario de la UAT | activo · concesión efectiva | baja lógica tras la decisión | No |
| Concesión Engorde → `uat6.ipe` | — | 1 | broiler | API oficial | habilitar lectura productiva del lote | efectiva | revocar tras la decisión | No |
| Ventana BU `broiler` | — | 1 | broiler | API oficial (enable/disable) | permitir la lectura del lote en la sesión | **ON** (temporal) | restaurar **OFF** tras la decisión (verificar 4×OFF) | estado original |
| Credenciales efímeras | `~/ga_uat06_credentials.txt` (600) | — | — | generadas en preparación | acceso del actor | existente | **destruir** tras la decisión | No |

## Datos usados en solo lectura (sin modificación)

| Registro | Uso | Estado |
|---|---|---|
| Lote **L-BO-2026-05** (id 11, empresa 1) | fixture primario: detalle, IPE 556.6, reporte, móvil | Intacto (solo lectura) |
| Eventos/pesajes/alimento del lote 11 (histórico) | entradas del KPI | Intactos (solo lectura) |
| Lote cerrado 53 (retenido de R-184) | **no usado** en esta UAT (fixture primario suficiente) | Intacto |

## Verificación de limpieza (§40 — EJECUTADA 2026-09-11)

| Comprobación | Resultado |
|---|---|
| Concesión Engorde → `uat6.ipe` revocada | **200** (verificado) |
| Usuario 132 baja lógica | **204** |
| Rol 64 desactivado | **200** |
| BU `broiler` OFF · catálogo 4×OFF | **verificado** (`breeder·broiler·grandparent·hatchery` = OFF) |
| Lote 11 / histórico | **intacto** (solo lectura) |
| Credenciales `~/ga_uat06_credentials.txt` destruidas | **verificado inexistente** |
| Temporales `/tmp/ga06_*` eliminados | **verificado inexistente** |
| Sesiones de navegador | cerradas (sin storageState versionado) |
| Auditoría preservada · admin humano operativo · ningún humano modificado | **verificado** |

Cierre: limpieza completa y verificada antes del commit de decisión C2.
