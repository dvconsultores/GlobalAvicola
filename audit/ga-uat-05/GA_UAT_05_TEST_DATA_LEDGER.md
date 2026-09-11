# GA-UAT-05 · LEDGER DE DATOS DE PRUEBA (§37)

Sesión: aceptación del propietario de GA-FE-07 (R-185 / OD-21) · entorno: producción de prueba (empresa 1 = Avícola Global C.A.).

## Registros creados para la sesión

| Registro | Identificador | Mecanismo de creación | Estado actual | Uso en la sesión | Limpieza prevista | ¿Se retiene? |
|---|---|---|---|---|---|---|
| Rol «Operador Lotes UAT GA-FE-07» | 59 | API admin (roles) | activo | cuenta de trabajo | desactivar (`is_active:false`) tras la decisión | No |
| Rol «Consulta Maestros UAT GA-FE-07» | 60 | API admin (roles) | activo | cuenta de consulta | desactivar tras la decisión | No |
| Usuario `uat7.lotes` | 127 | API admin (users) | activo · concesión Engorde efectiva | UAT-01/02/03/05 | baja lógica tras la decisión | No |
| Usuario `uat7.consulta` | 128 | API admin (users) | activo | UAT-04 | baja lógica tras la decisión | No |
| Concesión Engorde → `uat7.lotes` | — (ventana BU) | API admin | efectiva | habilitar operación | revocar tras la decisión | No |
| Área «Nave Disponible (UAT GA-FE-07)» | 14 (ACT) | API admin (masters/areas) | **activa** | UAT-01/02/05 (área elegible) | baja lógica tras la decisión | Se conserva el registro en baja (sin valor) |
| Área «Nave Retirada (UAT GA-FE-07)» | 15 (X) | API admin · baja oficial (DELETE) | en baja lógica | UAT-01/04 (no elegible / visible en admin) | ya en baja | Sí (estado final) |
| Área «Nave Histórica (UAT GA-FE-07)» | 16 (H) | API admin · **retirada tras crear el lote histórico** | en baja lógica | UAT-03/04 | ya en baja | Sí (estado final) |
| Lote `UAT7-HIST-01` | 51 | Flujo oficial del producto: operador + Área H + fecha prevista | activo, área 16 (retirada) | UAT-03 (histórico usable) | **sin limpieza** | **Sí — evidencia** |
| Lote `UAT7-NUEVO-01` | 52 | UI del producto (walkthrough de referencia, 201) | activo, área 14 | UAT-02 (referencia) | **sin limpieza** | **Sí — evidencia** |
| Lote del propietario (sugerido `UAT7-OP-01`) | (no creado) | — | — | UAT-02 (referencia: cubierto por `UAT7-NUEVO-01`) | — | No aplica: el propietario registró su decisión A de aceptación sin ejecutar el recorrido en vivo (patrón GA-UAT-04: medida de referencia + decisión explícita) |

## Otros elementos

- Credenciales efímeras: `~/ga_uat05_credentials.txt` (600) — **destruir** tras la decisión. Tokens temporales `/tmp/ga05_*` — destruir.
- BU `broiler`: fue habilitada para la sesión; debe quedar **OFF** (catálogo 4×OFF) tras la limpieza.
- Auditoría del sistema: **preservada** (los registros de altas/bajas quedan como evidencia de la sesión).
- Ningún usuario humano ni registro de aceptaciones previas (GA-FE-02/03/04/05/06) se modifica.

## Verificación de limpieza (§36 — EJECUTADA 2026-09-11)

| Comprobación | Resultado |
|---|---|
| Concesión Engorde → `uat7.lotes` revocada | **200** (verificado) |
| Usuarios 127/128 dados de baja lógica | **204 / 204** |
| Roles 59/60 desactivados | **200 / 200** |
| BU `broiler` OFF · catálogo 4×OFF | **verificado** (`breeder·broiler·grandparent·hatchery` = OFF) |
| Área 14 en baja · áreas 14/15/16 todas en baja | **204** + listado verificado |
| Lotes 51/52 retenidos como evidencia | Sí (no borrados; lectura productiva cerrada con BU OFF por diseño OD-16) |
| Credenciales `~/ga_uat05_credentials.txt` destruidas | **verificado inexistente** |
| Temporales `/tmp/ga05_*` eliminados | **verificado inexistente** |
| Auditoría preservada · usuario admin operativo · ningún humano modificado | **verificado** |

Cierre: limpieza completa y verificada antes del commit de decisión C2.
