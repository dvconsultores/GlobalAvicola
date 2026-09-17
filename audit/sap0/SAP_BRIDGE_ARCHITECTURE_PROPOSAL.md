# SAP-0 · SAP_BRIDGE_ARCHITECTURE_PROPOSAL

Fecha: 2026-09-17 · Fase SAP-0 (SPEC ONLY) · **DEFINIDA, NO IMPLEMENTADA**
Estado: `PROPOSAL` — ninguna pieza se crea en esta fase (mandato §23: «SAP Bridge se define, no se implementa»).

---

## 1 · Problema a resolver

El legacy resolvía la integración embebiendo **VPN + driver HANA + SQL + hardcodes** dentro de la aplicación. El producto actual tiene prohibido ese patrón (§3 del mandato). La frontera nueva necesita un lugar **aislado** donde vivan la red SAP, los secretos y el dialecto de integración, sin contaminar backend/frontend/dominio.

## 2 · Definición: SAP Bridge

**SAP Bridge** = servicio separado (contenedor/grupo de procesos propio) que:

| Responsabilidad | Detalle |
|---|---|
| Red | Único componente con acceso a la red SAP (VPN dedicada o Cloud Connector). **Ni backend ni frontend** tienen ruta a SAP. |
| Credenciales | Único componente que custodia secretos SAP (modelo a definir en `AOD-12`). |
| Protocolos | Habla OData/CDS/SOAP/SQL-RO según decisión `SAP-CONN-01`; expone hacia GA **solo un contrato interno** (`/bridge/v1/...`). |
| Contrato | Solo RAW PAKS normalizados (JSON tipado) + estado de job. No conoce el dominio avícola. |
| Extracción | Ejecuta lecturas (snapshot/delta/watermark) y las deposita en **RAW** (§`SAP_RAW_STAGING_SPEC.md`). |
| Nunca | ❌ escribe en SAP · ❌ promueve datos a STAGING/canónico · ❌ conoce tablas del producto |

## 3 · Posición en la arquitectura

```
[SAP] ⇄ (red SAP) ⇄ [ SAP BRIDGE (aislado) ] --contrato interno--> [ RAW SAP (Postgres GA) ]
                                                                    │
                                                     [ STAGING + validación ]
                                                                    │
                                                     [ PROMOCIÓN controlada ] → dominios GA
Frontend → Backend GA (sin acceso SAP) · NO existe ruta Backend→SAP
```

- El **backend GA** conserva el patrón adaptador actual (`manual`/`mock`; `real` sigue `NO IMPLEMENTADO` — GA-REM-017) y en el futuro delegará en el Bridge solo si el Owner lo aprueba.
- La **promoción** a tablas canónicas es propiedad del producto (job auditado), no del Bridge (§22: nada escribe directo a dominio).

## 4 · Límites de confianza y least privilege

| Control | Regla |
|---|---|
| Superficie de red | El Bridge es el único con ruta hacia SAP; el resto del stack no resuelve la red SAP. |
| Identidad | Cuenta técnica SAP **read-only**, scopes mínimos por objeto (12 inbound), sin acceso a escritura. |
| Secretos | Gestión dedicada (vault/env del Bridge); rotación; **nunca** en el repo ni en logs. |
| Datos | El Bridge transfiere RAW + metadata; los datos sensibles se marcan y se excluyen del contrato si SAP los expone sin necesidad. |
| Observabilidad | Cada extracción genera `sync_job_id`, métricas, errores saneados; trazabilidad RAW (§7). |
| Fail-closed | Si el Bridge cae o la validación falla: **no hay promoción**; el producto mantiene su último estado consistente (multi-compañía: ninguna empresa mezcla datos de otra). |

## 5 · Alternativas descartadas (y por qué)

| Alternativa | Veredicto |
|---|---|
| VPN + hdbcli embebidos en backend (patrón legacy) | ❌ Prohibido (§3); acopla dominio a DB SAP; superficie de seguridad enorme. |
| ETL legacy multifunción (`app.py` + `querysHana.py`) | ❌ `DO_NOT_REUSE`: hardcodes, temp tables, sin idempotencia, sin RAW. |
| Conexión directa Backend→SAP por API | ❌ Mezcla secretos/red SAP con el producto; rompe adaptador único. |
| Solo archivos manuales (statu quo) | ◁ Válido como fallback (modo `manual` ya existe) pero no escala a integración diaria. |

## 6 · Interfaces conceptuales (sin implementar)

| Interfaz | Dirección | Contenido |
|---|---|---|
| `sync_jobs` | GA → Bridge (o Bridge interno) | solicitud de extracción por objeto (`object_type`, `mode=snapshot/delta`, `watermark`) |
| RAW batch | Bridge → RAW | lote de registros normalizados + `payload_hash` + `extracted_at` + `sync_job_id` |
| `job_status` | Bridge → GA | OK/ERROR por job, contadores, errores saneados |
| check de conectividad | operación del Bridge | usado **solo** en probes autorizados (P0), nunca desde backend |

## 7 · Estado y siguientes pasos

- `SAP_BRIDGE_STATUS = DEFINED_NOT_IMPLEMENTED`.
- La implementación (si el Owner la aprueba) ocurriría **después** de: SAP-CONN-01 (decisión) + SAP-BASIS-01 (respuesta técnica) + gate de implementación. **No en SAP-0.**
