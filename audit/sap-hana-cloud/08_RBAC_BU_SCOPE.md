# SAP-HANA-CLOUD · 08_RBAC_BU_SCOPE

Fecha: 2026-10-06 · SPEC 005 · RBAC, alcance de unidad de negocio y aislamiento de contexto

---

## 1 · Permisos (OD-12 `REUSE`: ninguno nuevo)

| Permiso | Autoriza | No autoriza |
|---|---|---|
| `sap:read` | readiness, catálogo, jobs, registros, errores, mappings (lectura), `connection-check` | sincronizar, mapear |
| `sap:send_sap` | iniciar sync, configurar mapping | **escribir en SAP**: en esta fase no existe ninguna ruta que lo haga |

El nombre `send_sap` viene del diseño histórico; hoy es la capacidad explícita de operar la integración SAP.

## 2 · Rutas

| Ruta | Método | Permiso | Alcance | Transversal (`sap_contract`) |
|---|---|---|---|---|
| `/sap/inbound/readiness` | GET | `sap:read` | CONTROL | no |
| `/sap/inbound/objects` | GET | `sap:read` | CONTROL | no |
| `/sap/inbound/mappings` | GET | `sap:read` | CONTROL | no |
| `/sap/inbound/mappings` | PUT | `sap:send_sap` (+ autoridad global para `COMPANY_CODE`) | CONTROL | no |
| `/sap/inbound/mappings/{mapping_id}` | DELETE | `sap:send_sap` (+ autoridad global para `COMPANY_CODE`) | CONTROL | no |
| `/sap/inbound/sync` | POST | `sap:send_sap` | CONTRATO | sí |
| `/sap/inbound/sync/{object_type}` | POST | `sap:send_sap` | CONTRATO | sí |
| `/sap/inbound/jobs` | GET | `sap:read` | CONTRATO | sí |
| `/sap/inbound/records` | GET | `sap:read` | CONTRATO | sí |
| `/sap/inbound/errors` | GET | `sap:read` | CONTRATO | sí |

Estado, catálogo y mapping configuran la integración y no tocan filas de producción: plano de control. Sincronizar y leer lo sincronizado opera el contrato SAP, cuyos documentos cruzan las cuatro cadenas por definición (OD-12, BU-D04).

## 3 · Coberturas de arranque

| Cobertura | Módulo | Estado |
|---|---|---|
| Toda ruta declara permiso | `authorization_coverage.verificar` | PASS |
| Toda ruta que usa la base está bajo `RutaTransaccional` | `transaction.verificar` | PASS |
| Toda ruta declara su alcance de unidad | `business_units.route_scope.verificar` | PASS |
| Las rutas `CONTRATO` de SAP coinciden con `SUPERFICIES_TRANSVERSALES` | `test_sap_transversal.py` | PASS |

## 4 · R-201 · OD-14.d — sin empresa efectiva, nada

| Actor | Lecturas | Sync / mapping |
|---|---|---|
| Autoridad global **sin** contexto | ∅ (jobs, registros, errores, mappings) | 400, antes de leer la base o tocar HANA |
| Autoridad global **situada** en A | solo A | opera A |
| Actor de la empresa A | solo A | opera A |
| Actor de la empresa B | nada de A | no puede mapear claves de A (409) ni borrar sus mappings (404) |

## 5 · Aislamiento multiempresa

- El sync consulta únicamente las sociedades mapeadas a la empresa efectiva, una por consulta.
- Una fila cuya sociedad pertenece a otra empresa GA no se persiste.
- El mismo `EBELN` en dos sociedades produce dos referencias, una por empresa.
- Enlazar una sociedad con un inquilino exige autoridad global: un analista no puede atraer datos de otra sociedad a su empresa.
- `validate_oc_limit` sigue buscando la OC dentro de la empresa del actor.

## 6 · Pruebas

`test_sap_inbound_routes_rbac` · `test_sap_inbound_routes_exist_and_declare_authorization` · `test_sap_inbound_routes_scope_declared` · `test_sap_inbound_transaction_coverage` · `test_r201_global_authority_without_context_sees_nothing` · `test_r201_company_actor_only_sees_its_company` · `test_company_code_mapping_requires_global_authority` · `test_plant_mapping_stays_inside_the_company` · `test_purchase_order_cross_company_isolation` · `test_row_of_another_ga_company_is_not_persisted`.
