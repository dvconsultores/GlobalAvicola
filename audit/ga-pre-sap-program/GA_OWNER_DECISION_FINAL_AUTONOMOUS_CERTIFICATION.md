# GA · OWNER DECISION — **CERTIFICACIÓN FINAL AUTÓNOMA PRE-SAP** (host N/A + UAT técnica delegada)

| Campo | Valor |
|---|---|
| **ID** | Owner Decision — T13 · Certificación final autónoma |
| **Fecha de decisión** | **2026-09-16** (canal chat; texto íntegro en el Anexo) |
| **Autoridad** | Propietario de Global Avícola |
| **Estado** | **RESUELTA — POLÍTICA VIGENTE** |

## 1 · Campos registrados

```
HOST_ADMIN_REVIEW_REQUIRED      = FALSE
HOST_INSPECTION_GATE            = NOT_APPLICABLE_BY_OWNER_DECISION
DEPLOYMENT_TOPOLOGY             = SINGLE_DOCKER_COMPOSE_APPLICATION_RUNTIME

OWNER_UAT_HUMAN_EXECUTION       = WAIVED_BY_OWNER_DECISION
TECHNICAL_FUNCTIONAL_UAT_AUTHORITY = DEEPSEEK_AGENT
OWNER_DID_NOT_EXECUTE_UAT       = TRUE
```

- **Topología declarada**: el host sólo ejecuta el artefacto/aplicación Docker
  Compose. Para la certificación Pre-SAP **no** se requiere SSH, inspección del
  filesystem, intervención de administrador, revisión manual de Docker ni
  evidencia administrativa del host.
- La certificación se realiza sobre: **SPEC + código + migraciones +
  compose/configuración versionada + tests + E2E + runtime público desplegado +
  API + UI + evidencia funcional + evidencia de seguridad + evidencia de
  procesos**.
- **No se inventa** evidencia del host. Los controles diseñados exclusivamente
  para inspección administrativa se reclasifican
  `NOT_APPLICABLE_BY_OWNER_DECISION` **con justificación explícita por gate**.
- **UAT humana**: el Owner delega la ejecución de aceptación funcional en el
  agente para este ciclo. **Nunca** se escribirá «Owner probó/confirmó/aceptó»
  si no ocurrió. La semántica correcta es:
  `OWNER_UAT_HUMAN_EXECUTION = WAIVED_BY_OWNER_DECISION` ·
  `TECHNICAL_FUNCTIONAL_UAT = EXECUTED_BY_DEEPSEEK_AGENT` ·
  `TECHNICAL_ACCEPTANCE = PASS | PASS_WITH_OBSERVATIONS | FAIL`.
- **G-03 es obligatorio y no N/A**: se verifica contra el runtime público
  (`401×5 → 429`). Debe resolverse desde el artefacto versionado, sin depender
  de intervención manual en el servidor.
- **SAP real** permanece fuera de alcance (`BLOCKED_EXTERNAL / FUTURE PROJECT`);
  no se fabrica evidencia SAP.
- **Estados de gate permitidos** tras la reconciliación: `PASS` ·
  `NOT_APPLICABLE_BY_OWNER_DECISION` · `FAIL`. Sin `BLOCKED_EXTERNAL` por
  ausencia de administrador.
- Al cerrar los requisitos aplicables: `HOST_ADMIN_DEPENDENCY =
  REMOVED_BY_OWNER_DECISION` · `DEPLOYMENT_GATE = PASS` (solo con evidencia).

## 2 · Delegación de UAT (semántica obligatoria)

```
OWNER_UAT_HUMAN_EXECUTION = WAIVED_BY_OWNER_DECISION
TECHNICAL_FUNCTIONAL_UAT  = EXECUTED_BY_DEEPSEEK_AGENT
AUTOMATED_TECHNICAL_UAT   = TRUE
```

Prohibido: `OWNER_UAT = PASS` · `OWNER_ACCEPTED = TRUE` · «Owner probó». La
certificación debe decir: *functional acceptance executed by autonomous
technical agent under explicit Owner delegation*.

## 3 · Orden de ejecución (mandato §27)

1. Formalizar esta Owner Decision. **2.** Reconciliar/eliminar dependencia
administrativa del host (G-02/G-04/G-05 → PASS o N/A justificado). **3.** Resolver
G-03 completamente (≠ `BLOCKED_EXTERNAL`; desde el artefacto; runtime `401×5→429`).
**4–12.** U1 · U2 · U3 · U4 · U5 · U6 · U7 · U8 técnicos. **13.** Corregir defectos
(cadena SPEC→…→push→runtime, sin parar). **14.** Suites finales sobre el último
árbol. **15.** Sensitivity/mutation final. **16.** Matriz 17 procesos.
**17.** P0/P1/P2 + deferred. **18.** SAP boundary. **19.** Certificación final.
**20.** Veredicto (solo 3 resultados posibles). **21–22.** Commit/push final +
`REMOTE_SHA_VERIFY`. **23.** Reporte final único.

## 4 · Registro

- `GA_AUTONOMOUS_EXECUTION_LEDGER.md` AE-67.
- Reconciliación de gates: `GA_T13_HOST_GATES_RECONCILIATION.md` (G-02/G-04/G-05).
- Certificación final: `GLOBAL_AVICOLA_PRE_SAP_FINAL_CERTIFICATION.md`.

---

## Anexo · Texto íntegro de la decisión del propietario (2026-09-16, canal chat)

```text
GLOBAL AVÍCOLA — T13
MANDATO FINAL DE EJECUCIÓN AUTÓNOMA Y CERTIFICACIÓN PRE-SAP

OWNER DECISION
AUTORIZACIÓN PARA CIERRE COMPLETO POR DEEPSEEK

[§0 OBJETIVO — completar AUTÓNOMAMENTE todo T13 hasta la certificación Pre-SAP
final; no detenerse por ausencia del administrador del host, UAT humana
pendiente, microdecisiones técnicas, evidencia producible técnicamente,
defectos deducibles del código/spec, necesidad de ejecutar pruebas, preparar
fixtures, fallos reparables o documentación pendiente. STOP solo ante:
(1) credenciales externas realmente imprescindibles que no existan;
(2) operación destructiva irreversible no especificada; (3) contradicción
funcional que requiera nueva decisión de negocio del Owner; (4) integración
SAP real.]

[§1 NUEVA DECISIÓN DEL OWNER — TOPOLOGÍA DEL HOST:
HOST_ADMIN_REVIEW_REQUIRED = FALSE; HOST_INSPECTION_GATE =
NOT_APPLICABLE_BY_OWNER_DECISION; DEPLOYMENT_TOPOLOGY =
SINGLE_DOCKER_COMPOSE_APPLICATION_RUNTIME. No se requiere SSH, inspección de
filesystem, intervención de administrador ni evidencia administrativa del
host. Certificación sobre SPEC + código + migraciones + compose/configuración
versionada + tests + E2E + runtime público desplegado + API + UI + evidencia
funcional/seguridad/procesos. NO inventar evidencia del host. Controles
diseñados solo para inspección administrativa ⇒ NOT_APPLICABLE_BY_OWNER_DECISION
con justificación explícita. No marcar N/A arbitrariamente.]

[§2 G-02/G-04/G-05: reconciliar contra la arquitectura real; identificar
requisito pretendido, parte demostrable desde repo/compose/config versionada/
tests/migraciones/app/runtime público; ejecutar comprobaciones posibles;
clasificar PASS / NOT_APPLICABLE_BY_OWNER_DECISION / FAIL (sin
BLOCKED_EXTERNAL). Requisito funcional real ⇒ resolverlo, no N/A.]

[§3 G-03 OBLIGATORIO: verificable contra el runtime público; estado conocido
FAIL_OBSERVED (401×12 sin 429). Objetivo: intentos 1–5 = 401, 6º = 429.]

[§4 RESOLVER G-03 SIN DEPENDER DEL HOST: desde el artefacto
versionado/desplegable; si es configuración versionada → hacerlo; si requiere
cambio de producto → cadena completa SPEC→AC→RED→IMPL→GREEN→REGRESIÓN→
COMMIT→SENSIBILIDAD→RESTORE EXPLÍCITO→POST-MUTACIÓN→EVIDENCIA→PUSH→REMOTE
SHA VERIFY→RUNTIME VERIFY. Sin hacks. Configuración final determinista para
SHARED UAT; sin activaciones manuales en servidor. Después del despliegue:
repetir G-03 contra https://avicola.globaldv.net/api/v1/login exigiendo
401×5→429; evidencia real; solo entonces G-03 = PASS.]

[§5 DESPLIEGUE: mecanismo vigente autorizado (DEPLOYMENT_MECHANISM = B;
docker-push-backend/frontend); la certificación sigue siendo local + runtime;
registrar SOURCE_COMMIT, WORKFLOW_RUN, IMAGE_TAG, IMAGE_DIGEST, RUNTIME_EVIDENCE.]

[§6 UAT HUMANA: el Owner delega la aceptación funcional en el agente;
OWNER_UAT_HUMAN_EXECUTION = WAIVED_BY_OWNER_DECISION;
TECHNICAL_FUNCTIONAL_UAT_AUTHORITY = DEEPSEEK_AGENT; OWNER_DID_NOT_EXECUTE_UAT
= TRUE; nunca escribir «Owner probó/confirmó/aceptó».]

[§7 EJECUTAR U1–U8 COMPLETAMENTE: sin simular; pruebas reales (navegador,
API, E2E, Playwright, requests, fixtures reales, base compartida, auditoría,
runtime). Por UAT: UAT_ID, PROCESS, OBJECTIVE, PRECONDITIONS, ROLE, COMPANY,
BUSINESS_UNIT, FIXTURE, STEPS_EXECUTED, EXPECTED_RESULT, ACTUAL_RESULT,
EVIDENCE, DEFECTS, FINAL_TECHNICAL_UAT_STATUS (PASS/PASS_WITH_OBSERVATIONS/
FAIL/NOT_APPLICABLE; nunca OWNER_ACCEPTED).]

[§8 U1 y §9 U2 — alcances detallados según fichas; U1 incluye G-03 corregido
como subcaso de seguridad; U2 recorrido C1/C2/C3 completo con población final
100 una sola vez y «Nuevo lote» disponible.]

[§10 U3–U8 sin esperar instrucciones; §11 evidencia REAL (prohibido inventar/
simular); AUTOMATED_TECHNICAL_UAT = TRUE; §12 matriz completa 17 procesos sin
transitividad (campos PROCESS_ID…STATUS; estados CERTIFIED/
CERTIFIED_WITH_NON_BLOCKING_OBSERVATIONS/PARTIAL/BLOCKED/NOT_APPLICABLE);
§13 reconciliación total P0/P1/P2 + R-*/OD-*/AOD-* (incl. R-133/R-134/R-142/
AOD-17/AOD-18/AOD-29+addendum/GA-REQ-061/R-67/R-131/R-132/R-141/OD-04/06/09/
10/14/15/16/21/22/23/25/Wave C/SAP); §14 suites finales completas sobre el
último árbol con counts exactos; §15 sensitivity con git restore
--source=$IMPL_COMMIT exclusivamente; §16 SAP boundary sin fabricación;
§17 Cutover/Opening (OPENING + POST-CUTOVER = CURRENT; golden 9.965/535;
UNKNOWN≠0; applied immutable); §18 KPI (R-131/132/141/133/134, OD-22 bandas);
§19 seguridad/multiempresa/BU (OD-16/09/10/23/14/15, R-121); §20 certificación
final GLOBAL_AVICOLA_PRE_SAP_FINAL_CERTIFICATION.md (21 secciones); §21
veredicto único (PRE_SAP_GO / PRE_SAP_GO_WITH_NON_BLOCKING_OBSERVATIONS /
PRE_SAP_NO_GO); §22 semántica de aceptación (sin falsas declaraciones);
§23 host gates eliminados del bloqueo artificial (G-03 = PASS obligatorio;
HOST_ADMIN_DEPENDENCY = REMOVED_BY_OWNER_DECISION; DEPLOYMENT_GATE = PASS solo
con requisitos aplicables satisfechos); §24 defectos resueltos
automáticamente; §25 git (stage explícito, push y REMOTE_SHA_VERIFICATION
obligatorios); §26 autonomía total; §27 orden de ejecución (23 pasos);
§28 reporte final único con todos los campos; §29 principio final
(transparencia: el agente ejecutó las pruebas; el Owner delegó; no se fingió
evidencia ni aceptación humana).]

EJECUTA TODO AHORA HASTA EL VEREDICTO FINAL.
```
