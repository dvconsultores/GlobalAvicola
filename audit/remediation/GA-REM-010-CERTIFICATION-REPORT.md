# GA-REM-010 — CERTIFICATION REPORT

| | |
|---|---|
| **GA-REM** | `GA-REM-010` — Semántica de estados SAP · **Wave** 1 · 2026-09-03 |
| **Estado final** | **`CERTIFIED`** — la falsa representación de integración queda eliminada |

## Finding
**P0-7** — Un adaptador manual producía el efecto de una integración confirmada: `POST /sap/export` escribía un JSON efímero en `/tmp`, devolvía siempre éxito con un identificador ficticio `MANUAL-<12 hex>`, y el servicio marcaba los eventos como `SENT_TO_SAP` con esa referencia. A partir de ahí **BR-15 impedía editarlos**, dejando registros bloqueados como «enviados a SAP» que nunca llegaron a SAP.

Ampliado por **R-21** (`GA-REM-020`): `SapPayload` declara `external_transaction_id`, `source_system` y `sap_reference_item` —los tres campos que `Recomendación central §19` exige para evitar duplicados— y **ninguno se poblaba jamás**.

## Regla aplicada

```
NO VERIFIED SAP DELIVERY = NO TRUE sent_to_sap
```

## Implementation

| Archivo | Cambio |
|---|---|
| `app/integrations/sap/adapter.py` | Atributo **`delivers_to_sap`** en la interfaz abstracta: declara si el adaptador realiza una entrega **verificada**. `ManualSapAdapter` y `MockSapAdapter` → `False`. `ManualSapAdapter` deja de devolver `sap_document_id` ficticio y devuelve `raw_response={"artifact_path": …, "delivery": "manual_pending"}`. `check_connection()` pasa de `return True` a `return False`: el modo manual **no finge conectividad**. Corregido el `NameError` de `random` en `MockSapAdapter`. |
| `app/integrations/sap/service.py` | **`get_adapter()` selecciona por configuración** (`SAP_ADAPTER`), eliminando el `# TODO`. `"real"` responde 501 citando `GA-REM-017`. En `export_to_sap`, los eventos solo pasan a `SENT_TO_SAP` **si `adapter.delivers_to_sap` y hay `sap_document_id` real**; en caso contrario el payload queda `PREPARED` y **los eventos no cambian de estado ni reciben referencia SAP**. Se pueblan `external_transaction_id` y `source_system` (**R-21**, `GA-REQ-059`). Backoff con `timedelta` en lugar de `(minuto+n)%60`, que podía producir una fecha pasada (`GA-TD-038`). |
| `app/integrations/sap/router.py` | `GET /sap/connection-check` devuelve además `delivers_to_sap` y `mode` |
| `app/config.py` | `SAP_ADAPTER: str = "manual"` documentado |
| `app/integrations/sap/mock_adapter.py` | **eliminado** — no compilaba (`ModuleNotFoundError: app.integrations.sap.interface`) y tenía 0 importadores |

## AC — verificación

| AC | Criterio | Resultado |
|---|---|---|
| AC01 | El modo manual no simula integración | ✅ ningún evento pasa a `sent_to_sap`; ninguno recibe referencia `MANUAL-*` |
| AC02 | El artefacto manual persiste | ✅ `SAP_EXPORT_DIR` → `/app/media/sap_exports`, dentro del volumen de `GA-REM-009` |
| AC03 | El estado refleja la realidad | ✅ el payload queda `PREPARED`; los eventos permanecen en `CONSOLIDATED` |
| AC04 | Los registros no enviados siguen siendo corregibles | ✅ al no pasar a `sent_to_sap`, `validate_sap_edit_lock` (BR-15) **no los bloquea** |
| AC05 | El chequeo de conexión es honesto | ✅ `check_connection()` → `False`; nombre: «ManualSapAdapter (archivo, sin entrega verificada a SAP)»; el endpoint expone `delivers_to_sap: false`, `mode: "manual"` |
| AC06 | El adaptador se selecciona por configuración | ✅ `SAP_ADAPTER` con validación; **0 `TODO` en todo el backend** |
| AC07 | Inventario de registros afectados | ⚠ **`DEFERRED`** — requiere consulta contra la base productiva |
| AC08 | Código muerto retirado | ✅ los 5 módulos del paquete SAP importan sin error |
| AC09 | **El deployment NO ha sido modificado** | ✅ 0 workflows tocados; `watchtower`, `pull_policy` y `:latest` intactos |

## Decisión sobre el estado
Se **reutiliza `CONSOLIDATED`** en lugar de introducir un valor nuevo en el enum `EventStatus`.

**Justificación:** evita una migración de enum en PostgreSQL, preserva el baseline protegido (47 tablas · 21 migraciones · 1 head · **0 deriva**) conforme al §17 del encargo, y `CONSOLIDATED` ya significa exactamente «agrupado y listo para enviar». El estado del `SapPayload` (`PREPARED` vs `CONFIRMED`) aporta el detalle de si el artefacto está pendiente de carga.

**Sin migración. Sin cambio de esquema.**

## Decisión ejecutiva sobre `FEATURE_SAP_ENABLED`
Se **mantiene activo**. Con la semántica corregida, tener SAP habilitado ya no es peligroso: genera un artefacto persistente, no marca nada como confirmado y no bloquea registros. Desactivarlo dejaría a los analistas sin la funcionalidad de consolidación, que sí es correcta.

## Regression
`compileall` OK · **176 operaciones OpenAPI** · 0 deriva de esquema · `tsc` y `vitest` en verde · los 5 módulos SAP importan.

## Final status
**`CERTIFIED`.** El sistema deja de afirmar algo falso. AC07 (saneamiento de los registros ya marcados con `MANUAL-*`) se difiere: requiere acceso a la base productiva.
