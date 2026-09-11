# GA-UAT-05 · EVIDENCIA — GA-FE-07 (secciones A–F)

## A · PRECONDICIONES DE INGENIERÍA

| Elemento | Valor |
|---|---|
| Baseline | `main` · HEAD `d5e7fbb` == remoto · worktree limpio (preflight) |
| Producto frontend | último commit de producto `5a5bb3f` — **sin cambios desde la certificación** |
| Producto backend | último commit de producto `5a5bb3f` — **sin cambios desde la certificación** |
| Frontend bundle | `index-BUthrUt9.js` (LM 2026-09-11 15:46:08 GMT · ETag `"6aa42240-13cfdb"`) |
| Runtime | saludable (frontend 200; API responde; login verificado con ambas cuentas UAT) |
| Smoke | tsc **PASS** · build **PASS** · Vitest **280/280** · GA-FE-07 dirigido (lots) **9/9** |
| Gate backend local | 7 passed (OD-16 boundary + migración BU catálogo; suites PG de elegibilidad corren en CI) |
| Certificación técnica | GA-FE-07 = FUNCTIONALLY_CERTIFIED · R-185 = CLOSED (técnico) · OD-21 implementado (opción C) — **ratificación del propietario pendiente de esta sesión** |

**Medidas de referencia (walkthrough de ingeniería, no sustituyen aceptación):**

| Medida | Resultado |
|---|---|
| Selector desktop: solo Área activa visible | **PASS** — lista = «Seleccionar área…» + «Nave Disponible (UAT GA-FE-07)» |
| Inactivas ausentes del selector (retirada e histórica) | **PASS** |
| IDs/códigos crudos en el selector | **0** |
| Creación por UI con Área activa | **PASS** — `UAT7-NUEVO-01` id **52**, área 14, HTTP 201 |
| Lote histórico consultable tras retirar su Área | **PASS** — `UAT7-HIST-01` id **51** (área 16, retirada después) abre con normalidad |
| Administración de maestros conserva áreas retiradas | **PASS** (presencia: «Nave Retirada» y «Nave Histórica» visibles; **sin marca visual de estado** — nota) |
| Móvil (390×844): misma lista (solo activa), sin desbordes | **PASS** |
| Consola: errores fatales | **0** (solo 403 de widgets KPI, clase N-3 preexistente) |

## B · FIXTURES UAT

- Empresa: **Avícola Global C.A.** (empresa 1, entorno de prueba controlado).
- Ventana operativa: cadena **Engorde (broiler) habilitada** durante la sesión.
- Áreas (creadas para esta sesión): «Nave Disponible (UAT GA-FE-07)» id **14** (ACTIVA) · «Nave Retirada (UAT GA-FE-07)» id **15** (retirada) · «Nave Histórica (UAT GA-FE-07)» id **16** (retirada **después** de crear el lote histórico).
- Cuentas UAT: `uat7.lotes` (usuario 127, rol 59 «Operador Lotes UAT GA-FE-07»: inicio, lotes lectura/creación, maestros lectura; concesión Engorde) · `uat7.consulta` (usuario 128, rol 60 «Consulta Maestros UAT GA-FE-07»: solo lectura en maestros/lotes). Credenciales efímeras fuera del repositorio.
- Lotes: **UAT7-HIST-01** (id 51, área 16, cierre previsto 2026-12-01 — creado por el operador y **luego** retirada su área; ejemplar del caso UAT-03) · **UAT7-NUEVO-01** (id 52, área 14 — creado por UI en el walkthrough). El propietario puede crear el suyo (`UAT7-OP-01` sugerido).

## C · CASOS DEL PROPIETARIO

**Pendientes de la sesión del propietario.** Resultados de referencia de ingeniería: ver §A (no sustituyen aceptación). Se completará con la decisión explícita A/B/C.

## D · OBSERVACIONES DEL PROPIETARIO

**Pendiente.** Observaciones de ingeniería pre-sesión: ver `GA_OWNER_UAT_GA_FE_07_OBSERVATIONS.md`.

## E · DECISIÓN DEL PROPIETARIO

**(vacía — se completará únicamente tras decisión explícita del propietario)**

## F · LIMPIEZA

**Pendiente (§36, se ejecuta tras la decisión):** revocar concesión `uat7.lotes`→Engorde · baja lógica usuarios 127/128 · desactivar roles 59/60 · BU `broiler` restaurada **OFF** (catálogo 4×OFF) · Área 14 (ACT) dada de baja lógica (15/16 ya en baja) · lotes **51 y 52 retenidos** como evidencia (ledger) · credenciales `~/ga_uat05_credentials.txt` y temporales `/tmp/ga05_*` destruidos · auditoría preservada · ningún usuario humano modificado.
