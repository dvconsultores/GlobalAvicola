# GA-GOV-01 · INFORME DE DEDUPLICACIÓN

Regla (§3): una observación **no** es un finding nuevo. Cadena aplicada: OBSERVACIÓN → EVIDENCIA → LECTURA CANÓNICA → DEDUP → CLASIFICACIÓN → SEVERIDAD → IMPACTO → DISPOSICIÓN. Sin implementación.

---

## OBS-UAT-01 · «No hay entrada de menú para Lotes»

**Candidatos comparados y por qué NO son dueños:**

| Candidato | Relación | ¿Mismo root cause? | Veredicto |
|---|---|---|---|
| **R-119** (P1, CLOSED) — «el frontend no comprueba permisos en ninguna pantalla»; su texto incluye «menú estático… las nueve entradas se dibujan para cualquiera» | Familia navegación | **NO**: R-119 trataba de **autorización** de entradas existentes (cerrado con GA-FE-03/04: evaluador de capacidades). Aquí no se dibuja **ninguna** entrada para `/lots*` — no es un problema de permiso | NO duplicado; NO se reabre |
| **R-98** (CLOSED) — autoridad de acción intra-pantalla | Familia UI | NO: acciones y gates; nada que ver con el punto de entrada del módulo | NO duplicado |
| **GA-FE-03** (`NAV_SOURCE_INVENTORY §34`) — «Rutas sin fuente de menú (12): /operations*, /my-pending, **/lots***, … Se rigen por guardas de ruta y backend; **sin entradas nuevas salvo Roles**»; `DYNAMIC_NAVIGATION_SPEC §4`: «No se crean entradas nuevas de producto más allá de Roles (descubribilidad de ruta activa existente)» | **Este es el registro canónico del estado** | N/A — el estado **está inventariado y decidido**, no es un residual olvidado | **Documento gobernante** (no es finding abierto; es decisión de alcance aceptada en GA-UAT-01) |
| **R-181 / R-135** (familia «vertical UI nunca cableada») | Analogía metodológica | **NO**: en R-181 la vertical **no existía** (0 call-sites). Aquí la vertical de Lotes **existe y funciona** (lista, alta con gates, detalle); lo ausente es solo el **punto de entrada de navegación** | NO duplicado |
| Lista móvil `prompt-arquitectura-navegacion.md` L179 (📝 Registrar · 🐔 Lotes · 📊 KPIs) | Referencia **legacy** de diseño | Política vigente posterior: la barra móvil quedó reducida a 2 pestañas (guardrail GA-FE-03 en `MobileNav` hardcodeado: `poultry`, `home`, `kpi`) | No contradice: el prompt legacy no es AC vigente |

**Conclusión:** sin finding existente que lo posea y **sin expectativa canónica violada** (la única fuente aplicable decidió «sin entradas nuevas salvo Roles» y el propietario aceptó GA-FE-03). Es una **mejora de descubrimiento**: `UX_ENHANCEMENT_ONLY`, severidad **P2**, **sin R nuevo** (§25: no inflar a finding).

**Dueño canónico final:** backlog → sección GA-GOV-01 «Mejoras de navegación (P2, sin R)», clase GA-FE-03; natural candidato a la próxima iteración de navegación del programa.

---

## OBS-UAT-04 · «El selector mostró un área en baja lógica»

**Candidatos comparados y por qué NO son dueños:**

| Candidato | Relación | ¿Mismo root cause? | Veredicto |
|---|---|---|---|
| **R-179** (catálogos anulables por empresa) | Familia referencias de catálogo | **NO**: R-179 resolvió **pertenencia de inquilino** (nulo = compartido; ajeno = inexistente). El **estado** (`is_active`) no interviene allí | NO duplicado |
| **R-171** (catálogo de operaciones incubadora) | Catálogo de operaciones | NO | NO duplicado |
| Findings «inactive-master/inactive-area filtering» | — | **No existe ninguno** (verificado por búsqueda exhaustiva en backlog + auditorías) | Sin dueño actual |
| GA-FE-06-A §29 («matriz de área»: *no inventar regla de activa*) | Confirma el silencio canónico | El defecto de seguridad solo cubría tenencia | Confirma que **nadie definió** la elegibilidad por estado |

**Comprobaciones de dominio (§13), cada una con su respuesta canónica actual:**

| # | Pregunta | Hoy |
|---|---|---|
| A | ¿Puede un área inactiva **mostrarse** en un lote existente? | Sin regla de estado; el detalle ni siquiera muestra Área (OBS-UAT-06) y el API la devuelve sin condicionar |
| B | ¿Puede un área inactiva **seleccionarse** para un lote nuevo? | **Sí** (UI la muestra; backend la acepta) — sin fuente que lo prohíba ni que lo exija |
| C | ¿Puede asignarse por **API directa**? | Sí (validación = solo tenencia, R-182/GA-FE-06-A) |
| D | ¿Puede un lote existente **retener** la referencia tras la baja del área? | Sí (FK intacta; baja lógica) — coherente con «histórico» del propio `AreaUpdate` |

**Conclusión:** el silencio canónico sobre **elegibilidad por estado** obliga a `OWNER_DECISION_REQUIRED` (§14: no inventar). No se crea R (§23.6: requiere decisión previa). Nota adicional registrada: el área observada era fixture de ingeniería retenida en baja lógica (ledger UAT-04) — la higiene de datos reduce el ruido, pero la pregunta de política es independiente y aplica a cualquier maestro con `is_active`.

**Dueño canónico final:** backlog → GA-GOV-01 «Decisión del propietario pendiente (P3)», con la pregunta A/B/C (ver `GA_GOV_01_CLASSIFICATION_DECISIONS.md §OBS-UAT-04`).

---

## OBS-UAT-06 · «El detalle no muestra el Área»

- **Candidatos:** GA-FE-06-C15 (decisión de alcance registrada: «mostrar PLD en detalle; área no en esta tranche — evita rediseño; contrato de lectura por fresh GET»).
- **Búsqueda de requisito:** ninguna spec (docs/ ni auditorías) exige Área en el detalle del lote.
- **Dedup:** ya gobernado por decisión documentada + aceptación del propietario; **no** es residual ni duplicado de R-182 (el contrato del API la expone íntegra).
- **Conclusión:** `ACCEPTED_DESIGN` (nota P3 opcional para el futuro). Sin R.

## UAT-11 · «SLA N/A»

- **Candidatos:** ninguno; `docs/02 §3.14`/`OD-08` definen el aviso como notificación (campana) evaluada por el ciclo interno; no existe requisito de superficie a demanda.
- **Conclusión:** `NOT_A_DEFECT` (`N/A_BY_DESIGN`). Sin R.

## Chequeo R-184

- Ninguna de las tres observaciones toca `reports/kpi/ipe` ni depende de su reparación. Relación: **NINGUNA**. R-184 queda SEPARATE_OPEN sin cambios ni subwork.

---

## Regla anti-duplicación aplicada (§21)

No se creó ningún registro paralelo: cada ítem tiene **un único hogar canónico** (backlog GA-GOV-01 + actualización del registro de observaciones UAT-04). La omisión de R nuevos fue deliberada y verificada contra las 6 condiciones de §23.
