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

## Checklist de higiene (a verificar tras la limpieza §40)

- Concesión revocada · usuario 132 en baja · rol 64 desactivado · BU 4×OFF restaurada.
- Credenciales y `/tmp/ga06_*` destruidos; sesiones de navegador cerradas sin artefactos (sin storageState en repo).
- Auditoría preservada (incluye las altas/bajas del fixture, como evidencia del flujo oficial).
- **Ningún usuario humano modificado**; aceptaciones previas (GA-FE-02..07, GA-UAT-04/05) intactas.
