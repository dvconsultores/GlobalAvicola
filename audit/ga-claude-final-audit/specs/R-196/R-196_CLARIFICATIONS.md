# R-196 · CLARIFICACIONES

Fecha: 2026-09-13 · HEAD `c0b4afc` · Resolver antes de C2.

| # | Pregunta | Supuesto por defecto | Fuente | Decisión |
|---|---|---|---|---|
| C-01 | ¿Formularios por entidad o config extendida del genérico? | Extender la config del genérico con tipos de campo (texto/number/select-padre/bool) y por-entidad; sin reescribir la pantalla. | `MasterListPage.tsx`; `App.tsx:135-166` | técnica |
| C-02 | ¿`company_id` en Create de inquilino? | Resuelto en servidor; el campo no se acepta del cliente (salvo autoridad global que crea para otra empresa si se decide — hoy no previsto). Coordina R-50. | `masters/service.py:227-235` | técnica/seguridad |
| C-03 | ¿Reactivación por qué acción? | PUT `is_active:true` con confirmación (misma ruta de edición); sin endpoint nuevo. | `masters/schemas.py` (`*Update.is_active`) | técnica |
| C-04 | ¿OD-24 (empresas/granjas SAP)? | Régimen provisional intacto; el fix no habilita edición de campos SAP. | OD-24 | técnica |
| C-05 | Navegación: ¿selector dentro de `/masters` o submenú? | Selector/lista dentro de `/masters` (una pantalla, todas las entidades), respetando permisos/unidad; mínimo y sin tocar NAV global salvo enlace. | F G-01 | técnica |
| C-06 | productive-phases `order` vacío | Número 0 por defecto o `null` (según esquema opcional); sin 422. | `:227` | técnica |
| C-07 | ¿Curvas? | Fuera (pantalla propia). | registro | técnica |

Sin decisiones abiertas que bloqueen; C-02 coordina con R-50.
