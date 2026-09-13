# `OD-23` · CICLO APAGAR/ENCENDER DE UNA UNIDAD DE EMPRESA (BU-D10, OPCIÓN B)

**Estado**: `RATIFIED_IMPLEMENTED_OWNER_ACCEPTED` (2026-09-11 · `GA-BU-D10` · `R-188` · UAT `GA-UAT-08`, decisión A).
**Hogar canónico**: `audit/ga-bu-d10/GA_BU_D10_LIFECYCLE_SPEC.md` · `audit/ga-uat-08/GA_OWNER_ACCEPTANCE_R188_BU_D10_RECORD.md`.
**Contrato**: apagar una unidad **termina** sus concesiones vivas (marca `revoked_at` + auditoría individual con causa; nunca borra); re-encender **no devuelve** — cada usuario requiere concesión nueva explícita; sin migración.
**Implementación**: C1 `067fba6` · C2 `0542310` · C3 `bee33f5` · C3b `399751c` · C4 `7762e4e` · UAT C1 `a2fe22a` + decisión `30fe3dc`.
**Ficha de índice** (el hogar canónico es el anterior).
