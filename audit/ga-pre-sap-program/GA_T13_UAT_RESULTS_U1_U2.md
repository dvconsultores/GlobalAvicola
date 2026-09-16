# GA · PRE-SAP — T13 · RESULTADOS DE LA UAT TÉCNICA — LOTE U1 y U2

Fecha de ejecución: **2026-09-16** (~19:40–20:12 UTC) · Árbol: `4eb3222` (regla
de origen de artefacto) · Runtime: `https://avicola.globaldv.net` (entorno
compartido de UAT) · Backend desplegado: digest
`sha256:5c4824bd0c3d2bca887c77f561318e096762f0b520d70115fb45064de54cd219`
(commit de artefacto `d122e04`, workflow run `35142848385`) · Frontend
desplegado: `index-r36pBbNX.js` (sha256
`3047f5cdeb9cd9abf9310fd498755109f82e2f7a0e225e6bab1caf99ca9ab6f7`).

> **Atribución (mandato final autónomo).** `OWNER_UAT_HUMAN_EXECUTION =
> WAIVED_BY_OWNER_DECISION` · `TECHNICAL_FUNCTIONAL_UAT_AUTHORITY =
> DEEPSEEK_AGENT` · `OWNER_DID_NOT_EXECUTE_UAT = TRUE` ·
> `AUTOMATED_TECHNICAL_UAT = TRUE`. Ninguna sección de este documento
> constituye ni implica aceptación del propietario.

Evidencia bruta (logs, sanear secretos):
`evidence/t13-uat/u1-runtime-probes.log`,
`evidence/t13-uat/u2-runtime-flow.log`,
`evidence/t13-uat/u1u2-dedicated-suite-FINAL.log`,
`evidence/t13-ops/g03-fix-red-green-sensitivity.log`.

---

## U1 · Plataforma y seguridad (P-13 + X-BU)

| Campo | Valor |
|---|---|
| **UAT_ID** | U1 |
| **PROCESS** | P-13 (plataforma/seguridad, transversal) + X-BU (aislamiento empresa/BU) |
| **OBJECTIVE** | Verificar login/logout con revocación del *refresh* (AC04), refresh no usable como access, RBAC sin wildcard (R-199), aislamiento empresa/BU vía `switch-company`, rechazo de bearer inválido y rate-limit activo en el runtime real |
| **PRECONDITIONS** | Runtime desplegado (backend+frontend vigentes); credenciales del canal UAT-09 presentes (`~/ga_uat09_credentials.txt`, modo 600); suite dedicada verde en árbol final; G-03 resuelto (rate-limit activo en contenedor) |
| **ROLE** | Operador R-153 (`uat09-op-*`) y Aprobador R-153 — cuentas del canal de UAT |
| **COMPANY** | Compañía 1 (fixture del entorno compartido) |
| **BUSINESS_UNIT** | BU por defecto del usuario UAT-09 |
| **FIXTURE** | Usuarios UAT-09 (operador/aprobador); suite dedicada `u1u2-dedicated-suite` (82 casos: sesión, refresh, RBAC, tenancy) |
| **STEPS_EXECUTED** | 1) `POST /api/v1/login` operador → **200** · 2) `GET /me` con access → **200** · 3) `POST /logout` (body `{"refresh_token": …}` + bearer) → **204** · 4) `POST /refresh` con el refresh revocado → **401** (AC04: `jti` en *denylist*) · 5) re-login → **200** · 6) `GET /users`, `GET /roles/permissions-catalog`, `POST /switch-company` con rol acotado → **403** (sin wildcard, R-199) · 7) bearer inválido → **401** · 8) rate-limit: 5 intentos de login → `401×5` y sexto → **429** |
| **EXPECTED_RESULT** | Los 8 pasos con los códigos indicados; suite dedicada completa en verde |
| **ACTUAL_RESULT** | Los 8 pasos ejecutados con los códigos exactos esperados; suite dedicada **82 passed / 0 failed** (90.77 s, exit 0) sobre el árbol final; 429 re-verificado a las 19:52:55 UTC (`401,401,401,401,401,429`) |
| **EVIDENCE** | `u1-runtime-probes.log` (sondas runtime; secretos saneados) · `u1u2-dedicated-suite-FINAL.log` (82 passed, exit 0) · `g03-fix-red-green-sensitivity.log` (rate-limit: rojo→verde + sensibilidad por mutación con restauración desde el commit de implementación) |
| **DEFECTS** | Ninguno abierto. El comportamiento observado en el intento original del canal («el access previo seguía sirviendo tras logout») **no es un defecto**: AC04 revoca el *refresh* (`jti` a *denylist*); el access es stateless y caduca por TTL ≤30 min. Redacción del KIT corregida ese mismo día |
| **FINAL_TECHNICAL_UAT_STATUS** | **PASS_WITH_OBSERVATIONS** |

**Observaciones U1**
1. El KIT (`GA_T13_UAT_KIT.md` §U1) decía «el access previo deja de servir»;
   se corrigió a la semántica real de AC04 (revocación del refresh; access con
   TTL). Corrección documental, sin cambio de código.
2. Subcasos solo-admin (reset de contraseña en contexto, presencia
   `LOGIN`/`LOGOUT` en `audit_logs`): **N/A por decisión del Owner** (G-04,
   reconciliado en `GA_T13_HOST_GATES_RECONCILIATION.md`).

---

## U2 · Progenitoras — reintento GA-UAT-09 (P-01)

| Campo | Valor |
|---|---|
| **UAT_ID** | U2 |
| **PROCESS** | P-01 (progenitoras: importación → creación de lote → recepción → población) |
| **OBJECTIVE** | Verificar el recorrido de oro corregido en el runtime real: **C1** importación registrada **sin lote** · **C2** detalle pre-aprobación sin lote («se creará al aprobar») · **C3** la aprobación crea el lote (código, tipo, sexo, fecha) · recepción ♂40+♀60 y población exacta 100 (una sola vez) · vía manual intacta |
| **PRECONDITIONS** | Runtime desplegado; credenciales UAT-09; maestros sembrados (granjas/galpones/proveedores/transportes/causas); OC `PO-C001-GPR-0001` presente (confirmado: 39 referencias SAP, 1 OC GPR); logins espaciados (rate-limit 5/min) |
| **ROLE** | Operador R-153 (registro y submit) + Aprobador R-153 (review/approve) |
| **COMPANY** | Compañía 1 (fixture) |
| **BUSINESS_UNIT** | BU por defecto del usuario UAT-09 |
| **FIXTURE** | Importación `grandparent_import`: plan 110 compradas /105 embarcadas /100 recibidas /5 mortalidad de tránsito, país Francia, cuarentena 21 d, salida hoy−10 d, llegada hoy; granja 1 · galpón 1 · proveedor 1 · transporte 1 · OC `PO-C001-GPR-0001`; recepción ♂40 + ♀60; sondas de mortalidad 100 (pre-recepción) y 101 (post-recepción) |
| **STEPS_EXECUTED** | 1) login operador/aprobador → **200** · 2) descubrimiento de maestros → **200** (farms/suppliers/transports) · 3) `GET /sap/references` → **200** (`{references,total}`; OC GPR hallada) · 4) **C1** `POST /operations` (import, sin `lot_id`) → **201**, `lot_id=None` · 5) **C2** `GET /operations/{id}` → **200**, `lot_id=None`, `status=registered` · 6) submit (operador) → **200** · 7) review/start → **200** · 8) review/complete → **200** · 9) approvals/approve → **200** (`status=approved`) · 10) **C3** detalle post-aprobación → `lot_id=67`; `GET /lots/67` → **200**, `code=L-GP-2026-13`, `bird_type=grandparent`, `sex=mixed`, `start_date=2026-09-16`, `farm_id=1` · 11) mortalidad 100 pre-recepción → **400** «Mortalidad (100) excede el saldo de aves disponibles (0)» · 12) recepción ♂40+♀60 `POST /operations` → **201** (`registered`) y cadena P-07 completa (submit/start/complete/approve → **200**) → `approved` · 13) sonda de saldo: mortalidad 101 → **400** «…excede el saldo de aves disponibles (**100**)» ⇒ población exacta 100 · 14) `POST /lots` con cuerpo vacío → **422** (ruta manual «Nuevo lote» viva) |
| **EXPECTED_RESULT** | Import **201** sin lote; aprobación **200** y lote creado (`L-GP-{año}-NN`, grandparent, mixto, fecha=llegada); mortalidad pre-recepción rechazada (saldo 0); recepción 201; saldo exacto 100 (rechazo de 101 citando 100); ruta manual 422 |
| **ACTUAL_RESULT** | Todos los pasos con el resultado exacto esperado. Casos **C1/C2/C3 del ledger GA-R153 cerrados en el runtime real** con evidencia (evento import + lote 67 `L-GP-2026-13`) |
| **EVIDENCE** | `u2-runtime-flow.log` (recorrido completo + sondas adyacentes: forma de `/sap/references`, `opening-balance` 404-por-diseño) · `u1u2-dedicated-suite-FINAL.log` (contratos R153: import sin lote, creación al aprobar, recepción, saldo) |
| **DEFECTS** | Ninguno |
| **FINAL_TECHNICAL_UAT_STATUS** | **PASS** |

**Observaciones U2**
1. `GET /lots/67/opening-balance` → **404**: comportamiento **correcto por
   diseño** — un lote GP creado por importación no tiene fila de balance de
   apertura (el endpoint existe y responde 404 con detalle «Balance de apertura
   no encontrado» cuando no hay fila; el balance de apertura pertenece al flujo
   de corte/engorde, GA-REQ-061). La población del lote quedó evidenciada por
   las sondas 0→100.
2. La forma real de `GET /sap/references` es `{"references": [...], "total": N}`
   (39 referencias; la OC `PO-C001-GPR-0001` del contexto existe). El parser del
   script U2 se ajustó en consecuencia.
3. La recepción exige la cadena de aprobación P-07 (submit → review →
   approve); verificada completa en este recorrido.
4. Datos creados en el entorno compartido de UAT: evento de importación +
   evento de recepción + lote 67 (`L-GP-2026-13`). No se elimina: el entorno es
   compartido y los datos de UAT son evidencia.

---

**Cierre documental:** ambos lotes quedan con resultado técnico propio, sin
transitividad y sin lenguaje de aceptación del propietario. Continuación: lotes
U3–U8 en documentos sucesores.
