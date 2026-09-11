# GA-UAT-04 · REGISTRO DE OBSERVACIONES DEL PROPIETARIO — GA-FE-06

Estado de la sesión: **PENDIENTE** (documento preparado; se completa con la decisión del propietario).
Regla: ninguna observación se convierte en defecto ni se corrige durante la sesión.

| UAT ID | Resultado del propietario | Observación | Severidad | Captura | ¿Hallazgo existente? | ¿Candidato nuevo? | ¿Bloquea aceptación? | Comentario del propietario |
|---|---|---|---|---|---|---|---|---|
| UAT-01 | PENDIENTE | Pre-detectado por ingeniería: el producto **no tiene entrada de menú «Lotes»** (ningún rol la ve en el sidebar; solo URL directa). Pre-existente, no es regresión de GA-FE-06 | P2 (UX descubrimiento) | C01 | No (clase GA-FE-03/navegación) | Sí — candidato a registrar | A juicio del propietario | |
| UAT-02 | PENDIENTE | | | C01 | | | | |
| UAT-03 | PENDIENTE | | | C02 | | | | |
| UAT-04 | PENDIENTE | Nota: el selector incluye «Nave Operativa (GA-FE-06-A)» (área propia dada de baja lógica; el modelo no impone regla de «activa» para referenciar — no se inventa regla). Sin áreas de otra empresa (verificado) | P3 (limpieza de datos) | C03 | No | No | No | |
| UAT-05 | PENDIENTE | | | C04 | | | | |
| UAT-06 | PENDIENTE | Decisión de diseño registrada: el **detalle no muestra el Área** elegida (se muestra la Fecha prevista de cierre). ¿Debería verse el Área tras guardar? — a juicio del propietario | P3 (UX) | C04 | No («no mostrar área en detalle» fue decisión de alcance GA-FE-06-C15) | No | No | |
| UAT-07 | PENDIENTE | | | C05/C05b | | | | |
| UAT-08 | PENDIENTE | Regla vigente: Fecha prevista de cierre y Área son **opcionales** | — | — | | | | |
| UAT-09 | PENDIENTE | | | C06–C08 | | | | |
| UAT-10 | PENDIENTE | | | C09/C10 | | | | |
| UAT-11 | N/A | Sin consecuencia visible a demanda; proceso interno horario; no se fabrica aviso | — | — | | | | |
| UAT-12 | PENDIENTE | | | — | | | | |

## Observaciones de ingeniería registradas ANTES de la sesión (para honestidad)

1. **UAT-01 (descubrimiento)**: comprobado en código y runtime — la configuración de navegación no contiene ningún ítem «Lotes» (`navigationConfig.ts`) y ningún enlace apunta a `/lots` desde otras pantallas. No es regresión de GA-FE-06 (navegación intacta); es un vacío de descubrimiento pre-existente. **Candidato a hallazgo nuevo (UX P2)**, pendiente de clasificación tras la decisión del propietario.
2. **Consola**: en el detalle, las tarjetas KPI emiten peticiones que responden 403 para roles sin permiso de reportes (clase ya registrada como N-3 en GA-FE-06, no es de R-182 y es invisible en el uso normal). Errores fatales: 0.
3. **UAT-11**: N/A documentado arriba y en `GA_OWNER_UAT_GA_FE_06_GUIDE.md`.
