# R-205 · CLARIFICACIONES

Fecha: 2026-09-13 · HEAD `c0b4afc` · Resolver antes de C2. Ninguna decisión del propietario requerida para el núcleo; C-06 es técnica-dominio.

| # | Pregunta | Supuesto por defecto | Fuente | Decisión |
|---|---|---|---|---|
| C-01 | ¿De dónde se deriva `stage`? | Prioridad: `?stage=` (si el enlace lo trae) → `lot.bird_type` + fase activa → etapa del hub de origen → sin contexto: paso 1 actual. | `OperationFormPage.tsx:316,1901-1915` | técnica |
| C-02 | ¿La visibilidad del cuadre depende de `stage` o del lote? | Del **lote** (`bird_type=breeder` ⇒ visible/obligatorio en `bird_reception`), con `stage` como fuente secundaria para entradas sin lote. Evita depender de un estado de navegación. | BR-20; local `BR2-*` | técnica |
| C-03 | ¿El cuadre se exige en cliente? | Sí: `superRefine` con los tres campos cuando corresponde; mensaje claro y sin petición si faltan. | patrón R-189 | técnica |
| C-04 | ¿Se añade `?stage=` a los enlaces del producto? | Opcional y compatible (C-01 lo respeta); no obligatorio si el lote/fase resuelven. Los enlaces actuales no se rompen. | `OperationTile.tsx`, `ProcessStagePage.tsx` | técnica |
| C-05 | ¿Tocar BR-20/backend? | No. Regresión de validador (control). | `validators.py:536-565` | técnica |
| C-06 | ¿Qué pasa si un lote breeder está en producción y se registra `bird_reception`? | El cuadre aplica por `bird_type` (BR-20 lo exige por cadena, no por fase); si dominio quiere restringirlo por fase, se anota como residual (no bloquea). | `validators.py` | técnica (dominio informado) |
| C-07 | ¿Interacción con R-190? | Tranche conjunta: R-205 (cuadre/paridad) + R-190 (ubicación); un commit por paquete o commits consecutivos con la misma RED; certificación runtime conjunta. | registro §3 orden 3 | técnica |
| C-08 | ¿Se actualizan ya las suites p03/p04/p11? | No en esta tranche: GA-GOV-03 las corrige; R-205 habilita su verde (sus fixtures dejarán de caer por BR-20). Verificación cruzada en la certificación de R-205. | GA-GOV-03 | técnica |

Sin decisiones abiertas que bloqueen; C-06 es nota de dominio (opcional).
