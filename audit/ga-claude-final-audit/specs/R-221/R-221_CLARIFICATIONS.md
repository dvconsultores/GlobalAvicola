# R-221 · CLARIFICACIONES

Fecha: 2026-09-13 · HEAD `c0b4afc` · Resolver antes de C2. C-02 es `OWNER_DECISION_REQUIRED` (acotada); el resto, técnica.

| # | Pregunta | Supuesto por defecto | Fuente | Decisión |
|---|---|---|---|---|
| C-01 | `hatchery_inspection` ⇒ unidad `hatchery`: ¿inequívoca? | Sí (nombre del tipo y cadena única); se deriva al nacer como `grandparent_import` en R-153 C2b. | `service.py:242-246`; `classification.py` | técnica |
| C-02 | `farm_inspection` sin lote: ¿qué unidad tiene? | **OWNER_DECISION_REQUIRED** — opciones: (A) derivar de la granja/galpón declarados si declaran cadena única; (B) exigir clasificación previa siempre; (C) mantener statu quo («alguna unidad» + bandeja). Recomendado: **A con fallback B**. | OD-16.e; `classification.py:116-148`; bandeja de pendientes | **`OWNER_DECISION_REQUIRED`** |
| C-03 | ¿Se reescriben eventos históricos `business_unit_id=null`? | No (sin migración; la bandeja de clasificación sigue operativa para históricos). | encargo §61 | técnica |
| C-04 | ¿La guarda estricta devuelve 400 o 403? | Se reutilizan los errores de `exigir_unidad_operativa` sin códigos nuevos (patrón vigente del módulo). | `business_units/service.py:278-290` | técnica |
| C-05 | ¿`grandparent_import` se toca? | No: se conserva su derivación y su flujo (R-153). | `service.py:242-246` | técnica |
| C-06 | Tipos futuros: ¿cómo se declara «inequívoco»? | Lista explícita (documentada en el código) ampliable por decisión de dominio; sin heurísticas implícitas. | diseño general | técnica |
| C-07 | ¿Afecta a eventos con lote? | No: la unidad se deriva del lote (camino intacto; AC-06). | `service.py:185-197` | técnica |

Decisiones abiertas: **C-02** (propietario). El resto de ACs no dependen de ella salvo AC-04.
