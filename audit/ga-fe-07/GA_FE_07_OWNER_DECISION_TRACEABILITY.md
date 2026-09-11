# GA-FE-07 · TRAZABILIDAD DE LA DECISIÓN DEL PROPIETARIO (OD-21)

Mapa declaración → consecuencia, para impedir reinterpretaciones futuras.

| # | Declaración del propietario (GA-FE-07 §0) | Traducción canónica | Dónde se implementa / documenta |
|---|---|---|---|
| 1 | «Option C — Domain Rule Complete» | Decisión general de maestría: baja lógica ⇒ inelegible para referencias nuevas | `OD-21`; spec §2 |
| 2 | «Inactive master cannot be used for NEW references» | Principio general **documentado** | `OD-21`; spec §2/§6 (sin implementación masiva) |
| 3 | «The Area must NOT appear as eligible option for a new Lot Area assignment» | Filtro transaccional del selector del formulario de lote | spec §12; `LotFormPage` (solo activas) |
| 4 | «Backend must reject a new Lot creation … inactive Area» | Validación de alta: referencia nueva exige activa | spec §10; `create_lot` (validador extendido `exigir_activo`) |
| 5 | «Backend must reject a Lot update that attempts to CHANGE the Area reference to an inactive Area» | Validación de edición **solo cuando hay cambio efectivo** | spec §11; `update_lot` (detección `exclude_unset` + comparación con área actual) |
| 6 | «Historical records … must KEEP that reference» | Sin reescritura de FK ni nulificación | spec §9; tests H1/H2 + E2E-05/06 |
| 7 | «Historical display … must remain valid» | Lecturas sin condicionar estado; display aceptado intacto | spec §9; controles runtime (fresh GET) |
| 8 | «Unrelated update … must NOT fail merely because the historical Area is inactive» | La validación de estado NO se aplica si no hay cambio de referencia | spec §11 H1; `update_lot` (solo valida si `area_id` en `fields_set` y distinto del actual) |
| 9 | «If the Area reference is changed, the new Area must be active, valid, same Company» | Cambio de referencia = referencia nueva ⇒ valida activa + tenencia | spec §11 H3/H4/H5; validador canónico extendido |
| 10 | «Logical deactivation prevents new use; does not erase or invalidate history» | Principio rector | `OD-21` (cita textual); spec §2 |
| 11 | Alcance limitado «AREA → LOT ONLY» | Sin tocar otros maestros | spec §6; revisión de diff (solo lots/tenancy/LotForm) |
| 12 | Masters admin ≠ selector transaccional | Lista administrativa sigue mostrando inactivas | spec §12; regresión E2E masters (§68) |
| 13 | Anti-enumeración para ajena | «no encontrado» para ajena/inexistente; «Área inactiva» solo dentro del inquilino | spec §16; tests de contrato |
| 14 | No retroactividad | Sin migración ni limpieza masiva | spec §6; 0 migraciones |

## Los cuatro dominios distinguidos (GA-GOV-01 §13 → respuestas canónicas tras OD-21)

| Distinción | Antes (silencio) | Después (OD-21) |
|---|---|---|
| A · Display histórico de área inactiva | Sin regla | **Permitido** (historia válida) |
| B · Selección nueva | Sin regla | **Prohibido** |
| C · Asignación por API directa | Sin regla | **Prohibido** (referencia nueva) |
| D · Retención tras baja del área | Sin regla | **Garantizada** |
