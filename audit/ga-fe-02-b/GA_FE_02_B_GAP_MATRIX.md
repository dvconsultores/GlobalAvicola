# GA-FE-02-B · GAP MATRIX (F1–F4)

**2026-09-11 · Baseline `0dfa20b` · Runtime `index--DbCa8Hk.js` · Toda fila con evidencia o
marcada como pendiente de ejecución.**

| ID | SYMPTOM | SOURCE REQUIREMENT | OWNER DECISION | ROOT CAUSE | ENV/CODE/DATA | SECURITY IMPACT | PRODUCT IMPACT | REQUIRES SOURCE CHANGE? | REQUIRES ENV MUTATION? | NEW R-ID? | EXISTING FINDING? | AC | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **F1** | `GET /business-units` → `[]`; 4 códigos → 404 en candidatos. La administración de unidades y concesiones es inerte en ENV-01 | `GA-REM-040 §2` · `OD-16.a` (4 unidades = catálogo de plataforma) · `baseline_seeds.UNIDADES_DE_NEGOCIO` | **A** (sembrar el catálogo) — `GA-FE-02-B §1` | ENV-01 fue sembrado antes de que existiera el seed del catálogo; `sembrar_unidades_de_negocio` nunca corrió; **no existe API de catálogo** (server-side only) | **ENV** (data de plataforma) | Bajo (inercia, no exposición) | Bloquea E2E-02…10 + consolas de acceso | NO | **SÍ** (server-side; agente sin acceso ⇒ `BLOCKED_SERVER_ACCESS_F1`) | NO (inicialización de modelo gobernado) | — (no; registrar como bloqueo operativo de ENV-01) | AC-F1 (spec §4) | `BLOCKED_SERVER_ACCESS_F1` — comando canónico exacto entregado al propietario |
| **F2** | 13 roles activos; **ninguno** con `business_units:*`; el rol canónico «Administrador de Accesos» no existe ⇒ Actor B imposible | `OD-15 §6` / `R-113` (rol canónico, exactamente `read·update·create·delete`, sin `users:*`, sin comodín) | **B + C** (crear/configurar el rol canónico con permisos existentes) | ENV-01 sembrado antes de `R-113`; seeds posteriores nunca re-ejecutados en el entorno | **ENV** (RBAC de plataforma) | Nulo si se crea exacto (mínimo privilegio; sin comodín) | Bloquea concesión/revocación/candidatos y E2E-04…08 | NO (API oficial `POST /roles`) | **SÍ** (rol; ejecutable por el agente, API oficial) | NO | **SÍ (relacionado)** — la ausencia ya fue registrada como fixture-blocker en GA-FE-02-A; ahora con autorización explícita de creación | AC-F2 (spec §5) | `IN_EXECUTION` (API oficial, plantilla de sistema) |
| **F3** | `GET /users` 500 desde la 10.ª fila; ids 57–70 → 500 individuales (14 filas) | Invariante documentado en `baseline_seeds` («EmailStr rechaza .test/.example/.local… el usuario resultaría ilegible por la API») · `UserRead.email: Optional[EmailStr]` | **D** (diagnosticar y remediar tras probar causa raíz; prohibido borrar filas) | `integration_seeds.USERS_DEF` (14 usuarios: 7 móvil + 7 web) generó `email=f"{username}@testing.local"`; pydantic/email-validator rechaza el dominio reservado `.local` al serializar `UserRead` ⇒ `ValidationError` ⇒ 500. Probado localmente con el venv del backend | **DATA** (fixture malformada) + guardas de fixture (seed) | Nulo (fallo de lectura; no eleva ni expone) | `UsersPage` y listados dependientes caen; candidatos no hereda el fallo (proyección por columnas) | **SÍ — solo seeds/regresión** (endurecer `integration_seeds`), sin cambio de runtime de producto | **SÍ** (reparar 14 emails por API oficial `PUT /users/{id}`; reversible) | NO | **SÍ (parcial)** — los 500 fueron registrados como observación runtime en GA-FE-02-A resume 3 (F3/`RUNTIME`) | AC-F3 (spec §6) | `IN_EXECUTION` (cadena de evidencia completa; reparación API por fila) |
| **F4** | Autoridad global sin contexto: sin control visible para elegir empresa; `/admin/unit-access` fail-closed correcto pero **sin camino de recuperación en la UI** | `OD-14` (elegir empresa es un acto; autoridad global puede y debe situarse) · `GA-FE-02` AC de contexto de empresa | **E** (exponer el mínimo exigido por OD-14) | `Header.tsx` renderiza el bloque selector+badge solo si `(activeCompanyName || user?.company_name)`; el bootstrap admin nace sin empresa persistida ni contexto ⇒ nada que mostrar ⇒ circularidad (no se puede elegir sin nombre, y el nombre aparece solo al elegir) | **CODE** (frontend; gating mínimo) | Bajo (exposición solo para `is_super_admin`; nunca para actor sin autoridad) | Bloquea el camino de contexto de la UI (E2E-01b) para la autoridad global | **SÍ** (fix mínimo `Header` + resolución de nombre post-refresh en `auth.store`) | NO | **NO** — root ya registrado | **SÍ — `CAP-SES-05`** «Selector de empresa (actor global)», `IMPLEMENTED_BUT_NOT_EXPOSED` (`audit/frontend-runtime/`); condición de render idéntica. **Se reutiliza; no se crea R-ID** | AC-F4 (spec §7) | `IN_EXECUTION` (RED→fix→gates→deploy) |

## Dedup explícito (§7 / §24)

- **F4**: deduplicado contra `CAP-SES-05` (auditoría frontend runtime) — **mismo root** («condición
  de render `activeCompanyName || company_name`»). No se asigna `R-183` ni ningún R-ID.
- **R-98** (frontend sin modelo de permisos global) y **R-119** (navegación por permisos/unidades):
  **intactos** — el fix F4 no toca navegación global.
- **F2**: no duplica `R-113` (figura cerrada); es inicialización del entorno para la figura
  existente, ahora autorizada.
- **F1**: no duplica hallazgos; es inicialización de entorno del modelo `OD-16.a`.
- **F3**: los 500 ya constaban como evidencia runtime; esta tranche añade causa raíz probada y
  remediación gobernada.

## Registro de bloqueo operativo

`BLOCKED_SERVER_ACCESS_F1` — el agente no dispone de ejecución server-side autorizada en esta
estación (sin `docker` local; runtime en host remoto; sin shell/SSH entregado; prohibido buscar
credenciales). Comando canónico exacto: spec §4 (owner/ops). Todo lo demás (F2/F3/F4) es
ejecutable por mecanismos oficiales desde el cliente.
