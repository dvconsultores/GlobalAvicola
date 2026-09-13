# R-201 · SPEC — PREDICADO SAP FAIL-CLOSED SIN CONTEXTO DE EMPRESA

Fecha: 2026-09-13 · Hallazgo canónico: **R-201** (P2 · bloquea fase SAP) · HEAD `c0b4afc` · Origen GAP-02 (informe D) · Registro G-12. Secciones §47.

## 1 · Contexto

El módulo `integrations/sap` sirve el contrato transversal `OD-12` (consolidación → payloads → export/retry) con adaptadores `manual`/`mock` (`config.py:131`). Toda la lectura/escritura debe respetar la empresa efectiva del actor; el resto del producto ya es fail-closed sin contexto (`_acotar_a_empresa`, `_apply_company_filter`). SAP quedó con la doctrina anterior.

## 2 · Evidencia

`R-201_FINDING.md §1`. Código: `sap/service.py:76-81,128-135,158-161,208,239-242,258,404-408,532-583`; `docker-compose.yml:26` (`FEATURE_SAP_ENABLED=true`); tests: ausencia de caso global sin contexto.

## 3 · Causa raíz

Predicado único `_company_filter` con rama comodín `true()`; ninguna ruta de escritura exige contexto **antes** de leer; `retry_failed` sin `_require_company_id`.

## 4 · Impacto de negocio

Metadatos de OC/STO, jobs, consolidados, errores y payloads de todas las empresas visibles/reintentables por una sesión sin contexto. Riesgo de acción externa (reenvío) sobre datos de terceros; incumple OD-14.d y el aislamiento del contrato SAP.

## 5 · Comportamiento actual

| Superficie | Sin contexto (hoy) | Debería |
|---|---|---|
| `GET /sap/references` | todas las empresas | vacío |
| `GET /sap/sync/jobs`, `/consolidated`, `/errors`, `/payloads` | todas | vacío |
| `POST /sap/consolidate`, `/export` | lee todas y falla al final (500/4xx tras lectura) | fallo cerrado sin leer |
| `POST /sap/retry` | reenvía `FAILED` de todas | fallo cerrado |

## 6 · Comportamiento esperado

1. `_company_filter` → **`false()`** cuando `company_id is None` (patrón `_acotar_a_empresa`).
2. `consolidate_approved`/`export_to_sap`/`retry_failed`: `_require_company_id` **antes** de cualquier `select` (consolidate/export ya lo tienen al final: moverlo al inicio).
3. Semántica de actor: la autoridad global **situada** (`switch-company`) opera normalmente sobre esa empresa; sin contexto, ninguna.
4. Sin cambio de contrato HTTP para el actor de empresa: mismos 200/`[]`, mismos 409/4xx de negocio.

## 7 · Alcance

- `backend/app/integrations/sap/service.py`: predicado + orden de guardas (consolidate/export/retry).
- Tests: `backend/tests/test_r201_sap_no_context.py` (nuevo) + ampliación de `test_sap_transversal.py` (frontera global sin contexto).
- `retry_failed` gana la guarda existente `_require_company_id` (reuso, sin permiso nuevo).

## 8 · Fuera de alcance

- Máquina de estados SAP (E-25/R-157), response_model (R-112), payload mapeable (GA-REM-017).
- Frontend (R-217 trata el panel SAP).
- Auditoría de transiciones SAP (queda en la fase SAP).

## 9 · Impacto frontend

Ninguno directo. `SapManagerPage` con autoridad global sin contexto mostrará listas vacías en vez de datos de todas las empresas (comportamiento correcto; el panel ya debe situarse con `switch-company`).

## 10 · Impacto backend

`integrations/sap/service.py` (6-8 líneas efectivas). Sin cambios en routers, esquemas, modelos ni migraciones.

## 11 · Contrato frontend↔backend

`GET /sap/*`: mismo esquema; cambia **el conjunto** devuelto sin contexto (∅). `POST /sap/consolidate|export|retry`: mismo contrato de error; el 4xx de «sin contexto» ocurre antes de leer (no revela existencia de filas).

## 12 · Impacto en datos

Ninguno. No se persisten cambios nuevos; el fix **evita** escrituras transversales futuras.

## 13 · Seguridad

Cierra el fail-open GAP-02: lectura y escritura acotadas a la empresa efectiva; sin contexto, denegado. Alineado con OD-14.d y con el patrón de `auth/security.py:170-178` (código legado sin consumidores que se recomienda retirar en la misma tranche como limpieza documentada).

## 14 · Inquilino

Es la corrección de aislamiento central del paquete. `SapReference`/`SapPayload` conservan su `company_id`; los filtros existentes de actor de empresa no cambian.

## 15 · Unidad de negocio

N/A (SAP es transversal por diseño; `OD-12`, `BU-D04`).

## 16 · RBAC

`require_permission("sap","read")` / `"send_sap"` sin cambio. La frontera es de **contexto**, no de permiso (la autoridad global ya pasa RBAC).

## 17 · Transacciones

Sin cambio (frontera por petición). Las guardas anticipadas solo evitan lecturas/escrituras que luego fallaban.

## 18 · Auditoría

Sin cambio en esta spec (el retry sigue sin auditar → E-25/GA-REM-017). Nota: al mover la guarda al inicio, un intento sin contexto ya no genera lecturas; no hay rastro nuevo que auditar.

## 19 · i18n

N/A (mensajes técnicos de API).

## 20 · Escritorio · 21 · Móvil

N/A.

## 22 · Manejo de errores

`403/409` de «sin contexto» (reuso de `_require_company_id`; mensaje existente); sin cambio para el actor situado. Sin 5xx nuevos.

## 23 · Impacto de migración

Ninguna.

## 24 · Impacto SAP

Es preparación directa de P-08: el contrato transversal queda cerrado antes de conectar el adaptador real. No se inicia integración SAP.

## 25 · Compatibilidad hacia atrás

- Actor de empresa: idéntico.
- Autoridad global **situada**: idéntico (opera sobre su empresa efectiva).
- Autoridad global **sin contexto**: cambia de «todas» a «ninguna» (corrección, no ruptura; mismo patrón que el resto del producto).

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| AC-R201-01 | Global sin contexto: `GET /sap/references` ⇒ `[]` (no filas de ninguna empresa) |
| AC-R201-02 | Global sin contexto: `/sap/sync/jobs`, `/sap/consolidated`, `/sap/errors`, `/sap/payloads` ⇒ `[]` |
| AC-R201-03 | Global sin contexto: `POST /sap/consolidate` ⇒ 4xx de contexto **sin** leer filas (criterio: ninguna transición de estado); ídem `/export` |
| AC-R201-04 | Global sin contexto: `POST /sap/retry` ⇒ 4xx de contexto; **cero** payloads reenviados (contador antes/después) |
| AC-R201-05 | Global **situada** en empresa A: ve y opera solo A (referencias, consolidate, export, retry) |
| AC-R201-06 | Actor de empresa: comportamiento intacto (`test_sap_transversal.py` verde) |
| AC-R201-07 | Empresas: fixtures en A y B; sin contexto ninguna ve a la otra; situada en A no ve B |
| AC-R201-08 | Sin migración, endpoint, permiso ni modelo nuevo |
| AC-R201-09 | `get_company_filter` legado retirado o marcado obsoleto con justificación (limpieza documentada) |
| AC-R201-10 | Regresión: `test_sap.py` (9), `test_sap_transversal.py` (15) verdes en PG local |

## 27 · Pruebas RED→GREEN

`R-201_RED_E2E_UAT_DESIGN.md §1`: `test_r201_01_referencias_sin_contexto_es_vacio` (rojo: devuelve filas), `test_r201_02_payloads_sin_contexto_es_vacio`, `test_r201_03_consolidate_sin_contexto_no_lee` (rojo: transiciona), `test_r201_04_retry_sin_contexto_no_reenvia` (rojo: reenvía), `test_r201_05_global_situada_opera_su_empresa` (control), `test_r201_06_actor_de_empresa_intacto` (control).

## 28 · E2E

API sobre pila local (`§2` del diseño): `R201-RT-01…06` con dos empresas y tres actores (global sin contexto, global situada, actor de empresa); artefacto `evidence/r201/runtime-{red,c3}.json`.

## 29 · UAT

**No requiere UAT del propietario** (superficie técnica sin cambio visible para usuarios de empresa; el actor global sin contexto es una situación de administración). Se informa en el acta si el propietario lo pide.

## 30 · Criterios de cierre

RED válida en HEAD · GREEN local (AC01-10) · sensibilidad (S1: restaurar `true()` ⇒ AC01-04 rojas; S2: mover la guarda de retry al final ⇒ AC04 roja) · regresión SAP verde · sin migración/endpoint/permiso · R-201 → `CLOSED` con GA-REM asignado.
