# GA-UAT-04 · EVIDENCIA — GA-FE-06 (secciones A–F)

## A · PRECONDICIONES DE INGENIERÍA

| Elemento | Valor |
|---|---|
| Baseline | `main` · HEAD `7ec8903` == remoto · worktree limpio |
| Producto frontend | último commit de producto `23ca59a` — **sin cambios desde la certificación** |
| Producto backend | último commit de producto `69d0c95` — **sin cambios desde la certificación** |
| Frontend bundle | `index-DcqmSs-R.js` (LM 13:57:59 GMT · ETag `"6aa408e7-13cfbd"`) |
| Runtime | saludable (frontend 200; API responde; login verificado) |
| Smoke | tsc **PASS** · build **PASS** · Vitest **278/278** · GA-FE-06 dirigido (lots) **7/7** |
| Certificación técnica | GA-FE-06 = FUNCTIONALLY_CERTIFIED (incl. seguridad GA-FE-06-A) |

**Medidas de referencia (§34):** planned date visible **PASS** · selector Área **PASS** · nombres de Área **PASS** · IDs crudos de Área **0** · creación **PASS** (UAT-LOTE-01 id 37, 201) · detalle fresco **PASS** · recarga dura **PASS** · relogin **PASS** · móvil **PASS** (UAT-LOTE-02 id 38, sin desborde horizontal) · ES **PASS** · EN **PASS** · consola fatal **0** (ruido preexistente N-3: 403 de KPIs, invisible en uso normal).

Descubrimiento (UAT-01): enlace «Lotes» en menú — **no existe** (pre-existente); CTA «Nuevo Lote» en la lista — **encontrado**; acceso facilitado por URL directa para la sesión.

## B · FIXTURES UAT

- Empresa: **Avícola Global C.A.** (empresa 1, entorno de prueba controlado).
- Ventana operativa: cadena **Engorde (broiler) habilitada** durante la sesión.
- Áreas propias activas: «Nave Norte (GA-FE-06)» (1) y «Nave Sur (GA-FE-06)» (2).
- Operador UAT: `uat.lotes` (usuario 123, rol 56 «Operador Lotes UAT GA-FE-06»: inicio, lotes lectura/creación, maestros lectura; concesión de ventana). Credenciales efímeras fuera del repositorio.
- Lotes: **UAT-LOTE-01** (id 37, Área Nave Norte, cierre previsto 2026-09-25 — creado por el operador en el walkthrough de referencia) · **UAT-LOTE-02** (id 38, Área Nave Sur, 2026-10-02 — móvil). El propietario creará el suyo (sugerido `UAT-LOTE-03`).

## C · CASOS DEL PROPIETARIO

Resultados del propietario: **PENDIENTES** (se completan en la sesión; ver `GA_OWNER_UAT_GA_FE_06_OBSERVATIONS.md`).
Resultados de referencia de ingeniería (no sustituyen aceptación): ver §Medidas arriba y `evidence/reference-walkthrough.json`.

## D · OBSERVACIONES DEL PROPIETARIO

Ver registro dedicado (PENDIENTE). Pre-detectadas (honestidad): descubrimiento de Lotes (UAT-01, candidato P2), Área no visible en detalle (UAT-06, a juicio), opción de área dada de baja en selector (P3).

## E · DECISIÓN DEL PROPIETARIO

**NO PREFIJADA.** Se registrará exactamente la respuesta del propietario:
A) ACEPTO · B) ACEPTO CON OBSERVACIONES · C) RECHAZO.

## F · LIMPIEZA

Pendiente de la decisión: restaurar BU a OFF (estado de entrada), retirar concesión, desactivar usuario 123, desactivar rol 56, dar de baja áreas 1/2 (volver a su estado previo de baja lógica), retener/archivar lotes UAT según ledger, destruir credenciales y tokens, cerrar sesiones. La auditoría se preserva. Ningún usuario humano se modifica.
