# R-201 · FINDING — AUTORIDAD GLOBAL SIN CONTEXTO: LECTURA Y REINTENTO SAP TRANSVERSAL (FAIL-OPEN)

| Campo | Valor |
|---|---|
| **ID canónico** | **R-201** (asignado en `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §0`; máximo previo R-189) |
| **Título** | `_company_filter` devuelve `true()` cuando no hay empresa efectiva: la autoridad global sin contexto lee referencias/jobs/payloads/errores SAP de **todas** las empresas y `retry_failed` reenvía cargas de todas |
| **Severidad** | **P2** (§49: fuga transversal de lectura + escritura en la fase SAP; no bloquea la operación local, sí la definición de eventos fuente §55 y la doctrina OD-14.d) |
| **Clase** | `SECURITY` (fail-open sin contexto) / `DATA_INTEGRITY` (escritura transversal) |
| **Proceso** | P-08 (consolidación y envío a SAP; fase siguiente, tratada aparte en §56) |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` (== `origin/main`; runtime `avicola.globaldv.net`, bundle `index-DDCcWL76.js`) |
| **Familia** | GAP-02 del informe D (`evidence/D_security_tx.md` A.23); vecinos `R-112` (response_model), `OD-12` (contrato transversal), `OD-14.d` (fail-closed sin contexto) |
| **Paquete** | `audit/ga-claude-final-audit/specs/R-201/` (completo, 6 ficheros) |
| **GA-REM** | a asignar al autorizar; siguiente libre **GA-REM-043** |
| **Bloquea SAP** | **SÍ** (fase SAP: lectura/reintento transversal y contrato de eventos fuente; no bloquea la preparación local de otras tranches) |
| **UAT del propietario** | no (superficie técnica; verificación por API) |

## 1 · Evidencia

### 1.1 Código (verificado en HEAD)

- `backend/app/integrations/sap/service.py:76-81` — `_company_filter(company_id)`: «No filter for super admins — sees all companies» ⇒ devuelve `true()` cuando `company_id is None`.
- Consumidores del predicado:
  - `list_references` `:128-135` (catálogo de OC/STO para el asistente y el panel).
  - `consolidate_approved` `:158-161` (marca `CONSOLIDATED`), con `_require_company_id` `:208` **después** de leer filas ajenas.
  - `export_to_sap` `:239-242` (payloads), con `_require_company_id` `:258` posterior.
  - **`retry_failed` `:404-408`** — reenvía cargas de todas las empresas; sin `_require_company_id` (escritura).
  - `list_sync_jobs` `:532-537`, `list_consolidated` `:547-551`, `list_errors` `:564-567`, `list_payloads` `:582-583`.
- Contradicción normativa: `OD-14.d` (fail-closed sin contexto) y el patrón del resto del producto (`_acotar_a_empresa` → `false()`, `operations/service.py:93-102`; `_apply_company_filter`, `masters/service.py:54-97`).
- `FEATURE_SAP_ENABLED` por defecto **`true`** en `docker-compose.yml:26`.

### 1.2 Cobertura de tests

`tests/test_sap_transversal.py::test_ac_sap02_*` cubre actor de empresa; **ningún test** ejerce la autoridad global sin contexto en SAP (grep `global|super|sin contexto` en `tests/` → sin caso relevante). `R-112` registra los `response_model` ausentes; no cubre este predicado.

### 1.3 Contexto de dominio (E-25)

`E_domain_ledger.md §2 T16-T18`: `SAP_ERROR` sin productor; `retry_failed` lleva eventos a `SAP_CONFIRMED` saltando `SENT_TO_SAP` y **sin auditoría**; `SENT_TO_SAP`/`SAP_CONFIRMED` nunca auditados (`update()` masivo sin helper). El fix de R-201 no corrige la máquina de estados (R-157/GA-REM-017), pero el reintento transversal **escribe** en empresas ajenas al contexto del actor.

## 2 · Causa raíz

Doctrina antigua de «super admin ve todo» sobrevivió en el módulo SAP cuando el resto del producto migró a la doctrina contextual (OD-14): el predicado único `_company_filter` no distingue «actor de empresa» de «autoridad global sin empresa situada», y las dos superficies de escritura (`consolidate`/`export`) solo fallan **después** de leer, mientras `retry_failed` no falla nunca. No hay test de la frontera.

## 3 · Impacto

- **Lectura**: la autoridad global sin contexto (p. ej. sesión recién iniciada sin `switch-company`) ve OC/STO, jobs, consolidados, errores y payloads de todas las empresas — fuga de metadatos de negocio entre inquilinos en una superficie `CONTRATO` (OD-12).
- **Escritura**: `POST /sap/retry` reenvía cargas `FAILED` de cualquier empresa sin contexto ⇒ acción con efecto externo sobre datos de terceros.
- **Fase SAP**: la doctrina de aislamiento del contrato transversal queda incumplida; el veredicto de preparación exige cerrar este fail-open antes de integrar SAP (aunque P-08 siga `BLOCKED_EXTERNAL`).

## 4 · Dedup realizada (§48)

| Registro inspeccionado | Resultado |
|---|---|
| R-001…R-189 | `R-112` (response_model de `/sap/*`), `R-145`/`R-157` (payload/estados), `OD-12` (contrato) — ninguno cubre el predicado fail-open |
| GA-REM-001…042 | `GA-REM-010` (SAP interno) y `GA-REM-017` (integración real) no cubren la frontera de contexto |
| Informe D | GAP-02 documentado como candidato nuevo, sin registro previo (grep `_company_filter` en backlog → vacío) |

Conclusión: **nuevo**; ID asignado **R-201**.

## 5 · Propietario sugerido

Equipo backend (módulo `integrations/sap`). Sin dependencias de UI. Coordinar con la tranche de seguridad (R-199/R-200/R-203/R-204/R-221) para una única RED y un solo bloque de certificación por API.

## 6 · Bloquea SAP y por qué

**SÍ (fase SAP).** El contrato `OD-12` exige aislamiento por empresa en el plano transversal; una autoridad global sin contexto que lee y reintenta cargas de todas las empresas rompe la doctrina antes de que el adaptador real exista. La corrección no implementa SAP: solo cierra la frontera interna.

## 7 · Interdependencias

- **R-112** (response_model): misma superficie; pueden compartir tranche.
- **E-25/R-157**: la máquina de estados SAP (auditoría de transiciones, `SAP_ERROR`, salto de `SENT_TO_SAP` en retry) queda en `GA-REM-017`; aquí solo el predicado.
- **OD-14.d/OD-16.e**: doctrina de referencia; sin cambio de decisión.
