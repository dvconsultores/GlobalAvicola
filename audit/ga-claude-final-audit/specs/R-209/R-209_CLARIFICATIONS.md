# R-209 · CLARIFICACIONES

Fecha: 2026-09-13 · HEAD `c0b4afc` · Resolver antes de C2. Ninguna decisión del propietario requerida.

| # | Pregunta | Supuesto por defecto | Fuente | Decisión |
|---|---|---|---|---|
| C-01 | ¿Qué helper se reutiliza? | `identificadorDeOrdenSap` (R-189 §2, bloque superior). | `OperationFormPage.tsx:2008-2035` | técnica |
| C-02 | ¿Qué se guarda si el catálogo no expone código? | Fallback canónico (`ref_id`/`sap_code`); si nada ⇒ campo ausente (`undefined`), nunca `String(id)`. | R-189 §2 | técnica |
| C-03 | ¿Se limpian históricos con id? | No en esta tranche (inventario de lectura; saneamiento aparte si el propietario lo pide). | encargo §61 | técnica |
| C-04 | ¿Se revisan otros selectores? | Sí, barrido en la tranche (grep de `String(o.id)`/`String(id)` en `OperationFormPage`); hallazgo adicional entra al mismo paquete. | diseño | técnica |
| C-05 | ¿El backend estricta el formato del código? | No: sigue `Optional[str]` (compatibilidad); la validación semántica es de P-08. | `schemas.py`; `validators.py` | técnica |
| C-06 | ¿Interacción con R-206? | Comparten serializador; el normalizador `''`→`undefined` puede aplicarse en la misma tranche (sin solape de AC). | registro G-17 | técnica |

Sin decisiones abiertas.
