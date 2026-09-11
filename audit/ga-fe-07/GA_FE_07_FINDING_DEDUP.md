# GA-FE-07 · DEDUP DEL FINDING (R-185)

Re-evaluación de OBS-UAT-04 **después** de que OD-21 definiera la expectativa canónica (antes el silencio canónico impedía tipificarlo).

| Candidato | Relación | ¿Mismo root cause? | Veredicto |
|---|---|---|---|
| **R-179** (catálogos anulables; `verificar_catalogo_de_empresa`) | Familia referencias de catálogo | **NO**: R-179 gobierna **tenencia** (nulo=compartido; ajeno=inexistente). El estado `is_active` no participa allí. El validador de R-179 **se reutiliza** (extendido), pero el defecto de estado es nuevo y distinto | No duplicado |
| **R-182 / GA-FE-06-A** (contrato de área, tenencia, seguridad) | Superficie compartida (lote.area_id) | **NO**: R-182 cerró captura/envío/persistencia/tenencia. OD-21 añade una regla **nueva** de elegibilidad por estado, explícitamente **post-R-182**. No reabre R-182 | No duplicado; NO reabrir |
| **R-171** (catálogo incubadora) | Maestros | NO: catálogo de operaciones de incubadora; sin relación | No duplicado |
| **R-98 / R-119 / GA-FE-03/04** | UI autorización/navegación | NO: niveles de permiso/visibilidad de acciones/entradas; aquí es integridad de dominio | No duplicado |
| Findings «soft-delete» / «inactive-reference» | — | **No existía ninguno** (verificado en GA-GOV-01 y de nuevo ahora) | Sin dueño previo |
| OBS-UAT-01 | — | NO: descubrimiento de navegación; nada que ver | No duplicado |

**Conclusión:** con la regla definida por OD-21, el vacío pasa a ser un **defecto real de integridad funcional de dominio** sin dueño → se crea **R-185** (P2). Sin registros paralelos: hogar único = `GA_FE_07_FINDING_R185.md` + sección en backlog.

**Frontera con R-182:** R-182 permanece `CLOSED_OWNER_ACCEPTED`; R-185 es deuda posterior ratificada por el propietario.
