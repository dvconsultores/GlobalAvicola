# GA-FRONTEND · PLAN DE CERTIFICACIÓN DE LAS 19 (BATCHES)

Sin implementación: solo certificación (runtime autenticado dirigido + evidencia) y, donde aplique, UAT agrupada del propietario. Fuentes de AC: documentales (docs/02, docs/12, docs/13) + contratos ya certificados (BR-20/21/22, R-170/172/174, R-152, GA-FE-04/07).

| Batch | Filas | AC (fuente) | Actores (re-uso) | Fixture runtime | Tests que protege | Evidencia esperada | ¿UAT propietario? |
|---|---|---|---|---|---|---|---|
| **S** (Sesión) | FVA-02, 03 | docs/02 §3.1 (sesión/perfil); RR-05 (longitud) | usuario sintético web | credencial efímera | — | JSON: cambio 204→relogin 200→restore 204; perfil con datos reales | **NO** (técnico/plumbing) |
| **CP** (Control lectura) | FVA-06 + **FVA-07** (régimen provisional ratificado `OD-24`; certificación de gates/superficies/contrato **sin mutación** de maestros) | docs/02 §3.2.1 + `GA_OD_24_COMPANIES_FARMS_OWNERSHIP_DECISION.md` | admin de empresa | empresa 1 (1 fila) | suites masters | JSON + captura de listado; gates de create/update visibles y formulario abre | **NO** (decisión ya del propietario; superficie administrativa) |
| **M** (Maestros) | FVA-33, 34, 35 | docs/02 §3.2; OD-21 (elegibilidad áreas) | admin de empresa | áreas 14 / líneas genéticas | suites masters + GA-FE-07 | JSON: lista/alta/edición/inactivación; curvas: carga de tabla | **NO** (regla de áreas ya aceptada UAT-05; CRUD administrativo) |
| **Q** (Calidad) | FVA-36, 37, 38 | docs/13 (auditoría); docs/02 §8 (notificaciones); R-120/R-150 (patrón estados) | admin + usuario con/sin permisos | eventos reales | suites + NotificationBell | JSON: filtros con resultados; campana (no leídas→marcar leída); matriz denegado≠vacío≥3 casos | **NO** |
| **E** (Evidencias) | FVA-30 | docs/02 §7; GA-FE-04 | operador productivo | detalle de operación real | GA-FE-04 | JSON: adjuntar→descargar ida/vuelta (archivo testigo efímero) | **NO** (R-52 queda como item de ops) |
| **R** (Revisión) | FVA-26 | docs/12 §4-§6; R-181 (submit) ya aceptado | operador + revisor + aprobador | operación existente en estado válido | GA-FE-04/05 | JSON: submit→review→approve (ciclo completo con estados) | **NO** (envío aceptado UAT-03; gates UAT-02) |
| **OPS-GRANJA** | FVA-20, 21, 22 | docs/02 §3.4 (P-01), §3.6 (P-02), BR-20 | operador productivo (breeder+broiler) | lote existente | receptionFormContract + BR-20 | JSON: registro completo por tipo + valores capturados | **SÍ** (grupo UAT-1) |
| **OPS-INC** | FVA-23, 24, 25 | docs/02 §3.6/§3.7.3/§3.7.4, RR-11, R-170/172/174 | operador (hatchery+breeder) | lote incubación/breeder | contract tests + BR-21 | JSON: sanos/débiles; L de agua; despacho fila única | **SÍ** (grupo UAT-1) |
| **OPS-GP** | FVA-17, 18 | docs/02 §3.4.1/§3.4.2 (import), §3.7 (catálogo) | operador (grandparent+hatchery) | plan de importación | grandparentImportContract + R-152 | JSON: plan tipado capturado→visible en detalle | **SÍ** (grupo UAT-1) |

## UAT-1 (agrupada — 8 validaciones, máx. 5-8 §44)

**«Un día de operaciones: registrar y ver datos productivos»** — propietario valida SOLO resultado visible:
1. Recepción de aves: registrar y ver la operación listada. (FVA-20)
2. Recepción de reproductoras con cuadre (recibidas/mortalidad al arribo/rechazo). (FVA-21)
3. Control diario (alimento/agua/peso). (FVA-22)
4. Nacimiento en incubadora con sanos y débiles, sin fila «Total» duplicada. (FVA-23)
5. Consumo de agua visible en el reporte. (FVA-24)
6. Despacho: una sola fila fértil. (FVA-25)
7. Importación de abuelas: plan capturado y visible en el detalle. (FVA-17)
8. Catálogo de incubadora: datos de mortalidad/descarte por etapa. (FVA-18)

Tras certificación técnica por batch → estado intermedio `FUNCTIONALLY_CERTIFIED_OWNER_ACCEPTANCE_PENDING` en las 8; batch S/CP/M/Q/E/R pasan (si runtime verde) a `FUNCTIONALLY_CERTIFIED_UAT_NOT_REQUIRED`.

## Reglas de ejecución (§28/§42)

- Solo `CERT-PATH-B/C`, generación congelada `index-DtzHNDMG.js`, actores sintéticos re-utilizando el patrón del audit (limpieza posterior §45).
- Sin tocar producto ni tests existentes. Si una pasada falla → NO se corrige: hallazgo nuevo/dedup y STOP de esa fila (§28).
- Evidencia por fila (no por página): actor · pantalla · estado de negocio · API si aplica · desktop · móvil si aplica · tenant · BU · RBAC.
