# GA-FE-03 · CONTRATO RUTA ↔ NAVEGACIÓN ↔ DATO

Tres capas **deliberadamente distintas** (§25). `NAV ⊆ ROUTE`; ambas ⊆ autoridad backend.
Notación: `P(x)` = permiso `x` en sesión (comodín global incluido); `BUeff` = unidad ∈
`effective_business_units`; `BUon` = unidad ∈ `company_business_units`; `G` = `is_super_admin`;
`CTX` = `effective_company_id != null`.

| Capacidad | NAV_VISIBLE_WHEN | ROUTE_ALLOWED_WHEN | PRODUCTIVE_DATA_ALLOWED_WHEN |
|---|---|---|---|
| Dashboard `/` | `P(dashboard:read)` | sesión + `P(dashboard:read)` | backend: alcance productivo vigente (0 filas si nada) |
| KPI `/kpi` | `P(dashboard:read)` | sesión + `P(dashboard:read)` | ídem |
| Poultry unidad `U` (`/poultry/U/*`) | `P(operations:read) ∧ (G ? CTX ∧ BUon(U) : BUeff(U))` | sesión + `P(operations:read) ∧ (G ? BUon(U) : BUeff(U))` | backend: tenant + BU ON + concesión/global + `operations:*`/`lots:*` + recurso |
| Review `/review*` | `P(review:read) ∧ anyBU` | sesión + `P(review:read)` | backend: ámbito de unidad (efectivas / habilitadas para global) |
| Approvals `/approvals` | `P(approvals:approve) ∧ anyBU` | sesión + `P(approvals:approve)` | ídem ámbito |
| Reports `/reports*` | `P(reports:read) ∧ anyBU` | sesión + `P(reports:read)` | backend: lote/unidad acotada + KPIs |
| SAP `/sap` | `P(sap:read)` | sesión + `P(sap:read)` | backend: inquilino (contrato SAP vigente) |
| Auditoría `/audit` | `P(audit:read)` | sesión + `P(audit:read)` | backend: inquilino |
| Maestros `/masters*` | `P(masters:read)` | sesión + `P(masters:read)` | backend: inquilino (contexto) |
| Usuarios `/users` | `P(users:read)` | sesión + `P(users:read)` | backend: inquilino |
| Roles `/roles` | `P(users:read)` | sesión + `P(users:read)` | backend: inquilino |
| Acceso por unidad `/admin/unit-access` | `P(business_units:read)` | sesión + `P(business_units:read)` + CTX (la superficie exige empresa efectiva) | backend: empresa efectiva (403 sin contexto) |
| Perfil `/profile` | sesión | sesión | backend: propio usuario |
| Selector de empresa (Header) | `G` | `G` (`is_super_admin` canónico) | `GET /masters/companies` CONTROL_GLOBAL; `switch-company` acto auditado |
| Lotes/Operaciones (sin menú) | N/A (sin entrada; enlaces contextuales) | sesión + `P(lots:read)` / `P(operations:read)` para listas | backend: ámbito completo (tenant+BU+RBAC+recurso) |

**anyBU** = `G ? (CTX ∧ company_business_units ≠ ∅) : effective_business_units ≠ ∅`.

**Por qué difieren (legítimamente)**: `poultry` exige BU en la ruta porque la URL **nombra** la
unidad; `review/reports` no la nombran (el backend acota por ámbito), pero su navegación exige
conjunto no vacío para no ofrecer una cola vacía como si fuera operable. Las guardas de ruta
**no** consultan estado del menú ni almacenan decisión: evalúan la misma sesión en el momento
del render. Un deep link con autoridad insuficiente se deniega con el mensaje fail-closed y el
backend responde 403/404 con independencia de la guarda.
