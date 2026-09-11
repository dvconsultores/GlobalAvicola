# GA-UAT-04 · LEDGER DE DATOS DE PRUEBA

Sesión: GA-UAT-04 (Owner UAT de GA-FE-06) · Empresa: Avícola Global C.A. (1) · Entorno: prueba controlado.

| Alias | Tipo | Empresa | Propósito | Creado por | Mecanismo | Estado previo | Estado durante UAT | Disposición | ¿Retenido? | Motivo |
|---|---|---|---|---|---|---|---|---|---|---|
| `uat.lotes` (usuario 123) | Usuario | 1 | Operador sintético de la sesión (inicio, lotes leer/crear, maestros leer + ventana Engorde) | DeepSeek | API oficial (admin situado) | no existía | activo con sesión | desactivar tras la decisión | No | efímero |
| «Operador Lotes UAT GA-FE-06» (rol 56) | Rol | — | Autoridad mínima del operador | DeepSeek | API oficial | no existía | activo | desactivar tras la decisión | No | efímero |
| Concesión `uat.lotes`→broiler | Concesión | 1 | Ventana operativa para crear lotes | DeepSeek | API oficial | — | efectiva | revocar tras la decisión | No | efímero |
| BU `broiler` | Habilitación | 1 | Ventana encendida durante la sesión | DeepSeek | API oficial | OFF | ON | **restaurar OFF** | No | estado de entrada |
| Área 1 «Nave Norte (GA-FE-06)» | Área | 1 | Área propia ofrecida en el selector | preexistente (GA-FE-06) | reactivada por DeepSeek | baja lógica | activa | **volver a baja lógica** tras la sesión | — | restauración |
| Área 2 «Nave Sur (GA-FE-06)» | Área | 1 | Segunda opción propia | preexistente (GA-FE-06) | reactivada | baja lógica | activa | **volver a baja lógica** | — | restauración |
| Área 4 «Nave Operativa (GA-FE-06-A)» | Área | 1 | Preexistente; aparece en el selector pese a estar de baja (observación P3; sin regla de «activa» inventada) | preexistente | — | baja lógica | baja lógica | dejar como está | — | histórico |
| Área 5 «Área Ajena (GA-FE-06-A)» | Área | **3** | Fixture de ingeniería (cruce de empresa) | preexistente | — | baja lógica | baja lógica | dejar como está | — | histórico; **NO se expone al propietario** |
| Lote `UAT-LOTE-01` (id 37) | Lote | 1 | Evidencia de referencia: alta escritorio con Área 1 y cierre 2026-09-25 | operador UAT (script de referencia) | UI real | no existía | activo | **retener** | **Sí** | evidencia UAT (histórico del producto; sin borrado canónico) |
| Lote `UAT-LOTE-02` (id 38) | Lote | 1 | Evidencia de referencia: alta móvil con Área 2 y cierre 2026-10-02 | operador UAT | UI real | no existía | activo | **retener** | **Sí** | íd. |
| Lote `UAT-LOTE-03` | Lote | 1 | Caso UAT-05 del propietario | — | — | — | **no creado** (el propietario revisó y decidió A sin crear lote propio) | — | No | — |

## Estado FINAL (post-decisión, ejecutado)

- Concesión revocada · usuario 123 baja lógica · rol 56 desactivado · BU **restaurada OFF (4×OFF verificado)** · áreas 1/2 **devueltas a baja lógica** (estado previo) · credenciales y tokens **destruidos** · auditoría preservada · humanos intactos.

## Notas

- Auditoría: **preservada** (no se elimina nada).
- Ningún usuario humano (propietario ni otros) es creado, modificado ni bajado.
- Credenciales: `~/ga_uat04_credentials.txt` (600, fuera del repo) — **destruir tras la decisión**; tokens temporales del administrador — destruir.
- La retirada se ejecuta tras la decisión del propietario (paso 75–86 del orden estricto).
