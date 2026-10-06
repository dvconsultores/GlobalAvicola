# Implementation Plan: SPEC 005 — SAP HANA Cloud READ ONLY Inbound

**Feature**: `specs/005-sap-hana-cloud-readonly-inbound` · **Fecha**: 2026-10-06 · **Rama**: `main`
**Tipo**: implementación completa con certificación local · sin conexiones reales a SAP

---

## 1 · Technical Context

Python 3.11 · FastAPI · SQLAlchemy async · PostgreSQL · Alembic · `hdbcli` (síncrono, import lazy) · React + Vite + vitest · Playwright.

## 2 · Constitution / Safety Check

| Principio | Cumplimiento |
|---|---|
| NO SPEC = NO DEVELOPMENT | esta spec precede a todo código |
| NO AC = NO IMPLEMENTATION | AC-HANA-01…55 |
| Tests aislados, nunca contra producción (Art. 8) | fake HANA + pgserver de pruebas; 0 llamadas reales |
| Esquema solo por Alembic (Art. 19) | una migración con `downgrade` |
| Sin credenciales versionadas (Art. 20.3) | solo nombres de variable y placeholders |
| Integración que no aparenta estar completa (Art. 21) | `PENDING_CREDENTIALS`; `connected` solo tras conexión real |
| Sin auto-certificación (Art. 9) | certificación local = evidencia; cierre formal del Owner |
| `DO_NOT_CREATE_BRANCH` | trabajo directo en `main` |
| Mutation checkpoint | sensibilidad solo tras el commit de implementación, restaurando por SHA |

## 3 · Diseño

```
backend/app/integrations/sap/inbound/
  errors.py      ErrorCode (14) + SapInboundError + saneado de mensajes
  settings.py    HanaSettings: faltantes, política TLS, validación de identificadores
  sql_guard.py   assert_read_only(sql)
  registry.py    HanaObject · QueryDefinition · REGISTRY · render(schema)
  client.py      SapHanaReadOnlyClient: connect lazy, to_thread, semáforo, timeouts, clasificación de errores
  fake_hana.py   driver DB-API simulado (solo development/test)
  adapter.py     SapInboundAdapter (ABC) · HanaCloudReadOnlyAdapter · selección de driver
  models.py      4 tablas
  staging.py     normalización, validación, DTO de negocio, hash canónico
  mapping.py     resolución MANDT→BUKRS→WERKS→empresa
  promotion.py   upsert de sap_references
  service.py     readiness · connection check · sync · listados · mappings
  schemas.py · router.py · scheduler.py
```

**Sync por objeto** (dentro de un savepoint):

```
exigir empresa → readiness → sociedades mapeadas → advisory lock
 → por cada BUKRS: páginas (LIMIT/OFFSET, ventana) → contrato de columnas → RAW (hash/versión)
 → validación → mapping → staging (DTO normalizado) → promoción → watermark → auditoría
 fallo ⇒ rollback del savepoint · job failed · watermark intacto
```

**Rutas** (permiso · alcance):

| Ruta | Permiso | Alcance |
|---|---|---|
| `GET /sap/inbound/readiness` | `sap:read` | CONTROL |
| `GET /sap/inbound/objects` | `sap:read` | CONTROL |
| `GET /sap/inbound/mappings` | `sap:read` | CONTROL |
| `PUT /sap/inbound/mappings` | `sap:send_sap` | CONTROL |
| `DELETE /sap/inbound/mappings/{mapping_id}` | `sap:send_sap` | CONTROL |
| `POST /sap/inbound/sync` | `sap:send_sap` | CONTRATO |
| `POST /sap/inbound/sync/{object_type}` | `sap:send_sap` | CONTRATO |
| `GET /sap/inbound/jobs` | `sap:read` | CONTRATO |
| `GET /sap/inbound/records` | `sap:read` | CONTRATO |
| `GET /sap/inbound/errors` | `sap:read` | CONTRATO |

`sap:send_sap` autoriza operar el conector; **no** autoriza escribir en SAP.

## 4 · Fases

| Fase | Contenido | Commit |
|---|---|---|
| F0 | Spec, plan, tasks, research, data-model, quickstart; decisión y auditoría legacy; addenda | 1 |
| F1 | RED: suite `tests/test_sap_hana_*.py` (+ `sap_hana_fixtures.py`) fallando; evidencia | 1 |
| F2 | Configuración, errores, guard, registry, cliente, fake, adaptador | 2 |
| F3 | Modelos + migración; staging, mapping, promoción, servicio | 2 |
| F4 | Rutas, alcance, outbound deshabilitado, scheduler | 2 |
| F5 | Frontend + i18n + tests; E2E con fake HANA | 2 |
| F6 | Verde dirigido; regresión completa backend/frontend; `tsc -b`; build | 2 |
| F7 | Sensibilidad S1–S8 con restauración por SHA; regresión post-mutación | 3 |
| F8 | Evidencia, catálogo, runbook, certificación local, trazabilidad | 3 |
| F9 | Push `origin/main`; verificación de SHA remoto | — |

## 5 · Test plan

| Capa | Archivo | Cubre |
|---|---|---|
| Unit | `test_sap_hana_guard.py` | guard DML/DDL/CALL/multi-sentencia/comentarios; registry cerrado, binds, sin hardcodes legacy, sin scan abierto |
| Unit | `test_sap_hana_client.py` | credenciales ausentes, TLS, fake success/auth error, secretos, contrato de columnas, event loop |
| Integración (PG) | `test_sap_hana_sync.py` | 14 objetos, idempotencia, versión, watermark, mapping |
| Integración (PG) | `test_sap_hana_promotion.py` | OC, STO, BR-18, aislamiento entre empresas |
| Integración (HTTP) | `test_sap_hana_routes.py` | RBAC, alcance, transacción, R-201, readiness, outbound, sin SQL |
| Frontend | `pages/sap/__tests__/sapInbound.test.tsx` | estado, gates, export oculto, i18n |
| E2E | `e2e/sap-hana-inbound.spec.ts` | Analista SAP → sync → OC → recepción parcial → límite; STO disponible |
| Regresión | suites completas backend/frontend, navegación 8/8 | sin cambios de regla |

## 6 · Verificación y Git

Stage explícito (sin `git add .`). Commits: (1) spec + RED, (2) implementación + verde, (3) certificación + evidencia. Push a `origin/main` (AOD-29) y `git ls-remote` ⇒ `REMOTE_SHA_MATCH`. Sin tocar workflows.

## 7 · Criterios de parada

- `OPEN_TECHNICAL_CONTRADICTIONS > 0` en `/analyze` ⇒ no implementar.
- Regresión que solo pasaría cambiando una regla de negocio ⇒ parar y reportar.
- Sin acceso autorizado para el push ⇒ `PUSH_BLOCKED_BY_AUTH`; no se buscan credenciales.
- Cualquier llamada real a SAP ⇒ prohibida en esta fase.
