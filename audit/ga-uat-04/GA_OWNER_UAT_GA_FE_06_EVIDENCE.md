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

Resultados del propietario: **PASS** en los casos aplicables y **N/A** en UAT-11, según la **decisión explícita A) ACEPTO GA-FE-06** (2026-09-11) — sin observaciones adicionales reportadas. Detalle por caso y notas de ingeniería en `GA_OWNER_UAT_GA_FE_06_OBSERVATIONS.md`.

Resultados de referencia de ingeniería (no sustituyen aceptación): ver §Medidas arriba y `evidence/reference-walkthrough.json`.

## D · OBSERVACIONES DEL PROPIETARIO

Registro completo (CERRADO): `GA_OWNER_UAT_GA_FE_06_OBSERVATIONS.md`. Observaciones registradas: descubrimiento de «Lotes» sin entrada de menú (UAT-01, candidato UX P2, aceptado) · Área no visible en detalle (UAT-06, nota UX) · opción de área de baja lógica en selector (UAT-04, P3). Ninguna bloquea la aceptación.

## E · DECISIÓN DEL PROPIETARIO

**A) ACEPTO GA-FE-06** — decidida explícitamente por el propietario el 2026-09-11 en la sesión GA-UAT-04. Registro: `GA_OWNER_ACCEPTANCE_GA_FE_06_RECORD.md`.

## F · LIMPIEZA

**Ejecutada tras la decisión y verificada**: concesión `uat.lotes`→broiler revocada · usuario 123 dado de baja (204 → `is_active:false`) · rol 56 desactivado · BU `broiler` restaurada **OFF** (catálogo 4×OFF verificado) · áreas 1/2 **devueltas a su estado previo (baja lógica)** · credenciales `~/ga_uat04_credentials.txt` y tokens/scripts temporales **destruidos** (verificado inexistente) · lotes UAT-LOTE-01/02 **retenidos** como evidencia (ledger) · auditoría preservada · ningún usuario humano modificado · rol 35 y registros de aceptación GA-FE-02/03/04/05 intactos.
