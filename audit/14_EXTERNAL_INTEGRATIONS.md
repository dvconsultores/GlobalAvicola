# 14 — INTEGRACIONES EXTERNAS

| Servicio | Propósito | Entrada | Salida | Credenciales | Código | Consumidor | Estado |
|---|---|---|---|---|---|---|---|
| **SAP S/4HANA** | Sistema administrativo principal; recibe movimientos consolidados y provee referencias (OC, órdenes de traslado, centros, materiales, proveedores, lotes) | `POST /sap/references/import` (JSON) | `POST /sap/export` | ninguna configurada (`SAP_API_URL`, `SAP_USERNAME`, `SAP_PASSWORD`, `SAP_CLIENT` comentadas en `.env.example`) | `backend/app/integrations/sap/` (adapter, service, models, router, schemas) | `SapManagerPage`, `OperationFormPage` (SearchSelect de órdenes) | **NO CONFIGURADA / SIMULADA** |
| **Telegram Bot API** | Lanzador de la Mini App | `/start` | mensaje con botón `web_app` | `TELEGRAM_API_KEY` en `.env` | `backend/app/integrations/telegram/bot.py` (73 LOC) | contenedor `telegram-bot` | **CONFIGURADA** |
| **Telegram Mini App SDK** | Integración nativa en el frontend (color de cabecera, expansión, botón atrás, confirmación de cierre) | eventos del SDK | navegación SPA | — | `frontend/src/hooks/useTelegram.ts` (285 LOC) | `App.tsx`, `main.tsx`, `auth.store.ts` | **CONFIGURADA** |
| **Docker Hub** | Registro de imágenes | push de CI | `:latest` y `:sha-…` | `DOCKER_USERNAME`/`DOCKER_PASSWORD` (secrets de GitHub) | `.github/workflows/docker-push-*.yml` | Watchtower | **CONFIGURADA** |
| **AWS SES (SMTP)** | Envío de correo — **declarado y no usado** | — | — | `SMTP_USER`/`SMTP_PASSWORD` presentes en el `.env` de la raíz | **ninguno** | ninguno | **NO IMPLEMENTADA** |
| **PostgreSQL en la nube** | Persistencia | — | — | `DATABASE_URL` | `backend/app/database.py` | todo el backend | **CONFIGURADA** (fuera del compose) |

## 1. SAP — análisis detallado

### 1.1 Lo que sí está construido

- **Contrato desacoplado correcto:** `SapIntegrationAdapter` (ABC) con `export_consolidated`, `check_connection`, `get_adapter_name` y DTOs (`SapExportPayload`, `SapExportResult`, `SapImportData`) sin acoplamiento a SAP. Es un buen diseño y no requiere cambios.
- **Modelo de datos completo:** `sap_references`, `consolidated_movements`, `sap_sync_jobs`, `sap_payloads`, `sap_responses` (5 tablas, 62 columnas).
- **Idempotencia real:** clave SHA-256 sobre `lot_id|event_type|fecha|referencia|event_ids` (`adapter.py:169-172`) y comprobación de `SapPayload` ya `CONFIRMED` antes de reenviar (`service.py:249-259`).
- **Bitácora completa:** job → payload → response, con `retry_count`, `max_retries`, `next_retry_at` y `error_message`.
- **BR-13 respetado:** la consolidación solo toma eventos en estado `APPROVED`.
- **10 endpoints** y una pantalla (`SapManagerPage`) que muestra referencias, jobs, payloads y estado de conexión.

### 1.2 Lo que no existe

```python
def get_adapter(self) -> SapIntegrationAdapter:
    if self._adapter is None:
        # TODO: read from config/env which adapter to use
        self._adapter = ManualSapAdapter()
    return self._adapter
```
`backend/app/integrations/sap/service.py:34-38` — **el único `TODO` de todo el backend**, y es el que decide si el producto se integra o no con SAP.

| Adaptador | Declarado en la spec §14.4 | Estado real |
|---|---|---|
| `OFF` | rutas SAP no cargadas | funciona (feature flag) |
| `MOCK` | `MockSapAdapter` para pruebas | **existe pero no se usa**; además hay un segundo `mock_adapter.py` que **no compila** (`from .interface import SapAdapter` → módulo inexistente) |
| `MANUAL` | genera archivos para carga manual del analista | **es el único activo**, y siempre |
| `REAL` | conexión OData/REST a S/4HANA | **NO IMPLEMENTADO** (tarea T-085, marcada "🔴 Crítica, bloquea prod") |

### 1.3 Consecuencias operativas

`FEATURE_SAP_ENABLED=true` está activo en producción desde `bfccdfb` (2026-07-08). Con esa configuración:

1. `POST /sap/export` escribe `/tmp/sap_exports/<sha256>.json` **dentro del contenedor**, sin volumen → el archivo desaparece en el siguiente despliegue de Watchtower.
2. El servicio marca los eventos como `SENT_TO_SAP` con `sap_document_ref = "MANUAL-<12 hex>"` — un identificador que **no existe en SAP**.
3. A partir de ese momento **BR-15 impide editar esos registros** (`validate_sap_edit_lock`), aunque nunca hayan llegado a SAP.
4. `GET /sap/connection-check` devuelve siempre `connected: true`, porque `ManualSapAdapter.check_connection()` es `return True`.
5. Ningún estado `SAP_CONFIRMED` es alcanzable: no hay quien confirme.

**Riesgo neto:** los datos operativos quedan bloqueados como "enviados a SAP" sin que exista ninguna contrapartida en SAP y sin archivo recuperable.

### 1.4 Integración SAP en las operaciones — brecha estructural

`CERTIFICACION_FUNCIONAL.md` declara "**14 operaciones con integración SAP**". La verificación muestra que la integración es **solo de interfaz**:

- El formulario ofrece `SearchSelect` de órdenes SAP en 9 tipos de operación (importación de abuelas, recepción de aves, salida de aves, despacho y recepción de huevos, despacho de pollitos, registro de alimento).
- El valor elegido se guarda en **`extra_data.sap_order_ref`**, un JSONB libre.
- El campo tipado del modelo, **`sap_document_ref`, nunca se envía** (búsqueda en `frontend/src`: 2 apariciones, ambas de lectura).

Consecuencias verificadas:

| Mecanismo | Efecto real |
|---|---|
| `validate_sap_document_unique` (BR-11) | nunca se ejecuta (`if data.sap_document_ref and data.lot_id`) |
| `validate_oc_limit` (BR-18: cantidad ≤ OC) | nunca se ejecuta |
| `GET /reports/sap-comparison` | filtra `sap_document_ref != NULL` → **siempre vacío** |
| `OperationDetailPage` / `ReviewDetail` | el campo "Referencia SAP" nunca muestra nada |
| `SapExportPayload.sap_reference` | se toma de `ConsolidatedMovement.sap_reference`, que se agrega desde `evs[0].sap_document_ref` → **siempre nulo** |

**Clasificación: la integración SAP a nivel de operación es `FRONTEND_ONLY`.** El dato se captura y se almacena, pero desconectado de toda la lógica que debía consumirlo.

### 1.5 Importación de referencias

`POST /sap/references/import` acepta un JSON con la lista de referencias y crea un `SapSyncJob` de auditoría. **No existe interfaz de carga**: `SapManagerPage` solo lista. El modo "manual (upload CSV/JSON)" que anuncian `README.md` y `docs/10` no tiene UI. Los datos actuales provienen de los seeds (`e17d160`, `a6a6b3e` "ensure SAP order coverage across all stages").

## 2. Telegram

| Aspecto | Estado |
|---|---|
| Bot (`/start` → botón Mini App) | **funcional**; evita exponer una URL externa plana |
| SDK en el frontend | **funcional**: `initTelegramEarly`, color de cabecera, expansión, `enableClosingConfirmation`, gestión del botón atrás nativo con navegación SPA |
| Persistencia de sesión en Mini App | `localStorage` en lugar de `sessionStorage` (decisión razonable y documentada en el código) |
| Autenticación por `initData` | **no implementada**: se usa usuario/contraseña |
| Cobertura documental | **cero**: ninguna mención en `spec.md` ni en los 16 documentos de `docs/` |
| Variable `TELEGRAM_API_KEY` en `Settings` | declarada en `config.py:112` pero **no usada**: `bot.py` lee `os.getenv` directamente |
| `FEATURE_TELEGRAM_ENABLED` | inyectada por `docker-compose.yml` y **no declarada** en `Settings` → descartada por `extra="ignore"`; el bot arranca siempre |

Clasificación: **CONFIGURADA e IMPLEMENTED_WITHOUT_SPEC.** Es un canal de producto nuevo (8 commits entre el 2026-06-29 y el 2026-07-08) introducido sin ninguna especificación.

## 3. Correo / notificaciones

`.env` de la raíz contiene credenciales SMTP reales de AWS SES y `.env.example` las declara como "futuro". **No hay ni una línea de código de envío de correo.** El módulo 14 de `docs/02` (Notificaciones y Alertas) depende de este canal y está `NO IMPLEMENTADO`.

## 4. Resumen de estados

```
CONFIGURADA ........ 4   (Telegram bot, Telegram SDK, Docker Hub, PostgreSQL)
PARCIAL ............ 1   (SAP: modelo y bitácora sí, transporte no)
MOCK ............... 1   (SAP connection-check siempre true)
NO CONFIGURADA ..... 1   (SAP real: sin URL, sin credenciales, sin adaptador)
NO IMPLEMENTADA .... 1   (SMTP / notificaciones)
ROTA ............... 1   (mock_adapter.py: ModuleNotFoundError)
```
