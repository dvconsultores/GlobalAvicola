# SAP-0 · SAP_DISCOVERY_EXECUTION_PLAN

Fecha: 2026-09-17 · Fase SAP-0 (SPEC ONLY) · **Nada de este plan se ejecutó**: `SAP_CONNECTION_ATTEMPTS = 0`.
Este documento es el guion para el futuro probe autorizado (fase posterior, con gate del Owner) y contiene la **solicitud formal de información a SAP Basis (§36)**.

---

## 1 · Principios del probe

1. **Solo lectura**, jamás escritura ni transacción de negocio.
2. **Sin VPN embebida** en el producto: la ruta (VPN dedicada del lado SAP o Cloud Connector) se acuerda con Basis.
3. **Credenciales fuera del repo y del chat**: entrega por canal seguro; rotación; cuenta técnica dedicada.
4. **Evidencia por fase**: comandos ejecutados, salidas **saneadas** (sin secretos, sin datos personales), timestamps.
5. **Stop inmediato** si cualquier condición de parada (§6) se cumple.
6. Entorno **no productivo** por defecto; si solo existe productivo, el probe se limita a P0–P3 (catálogo/metadata).

## 2 · Fases P0–P6

| Fase | Objetivo | Allowed | Forbidden | Evidencia requerida | Stop conditions |
|---|---|---|---|---|---|
| **P0 NETWORK** | Verificar ruta extremo a extremo | `ping/tcp connect` al host/puerto documentado por Basis; inspección TLS (`openssl s_client`) | escaneos de puertos, traceroute agresivo, usar credenciales, VPN no aprobada | salida de conectividad + certificado TLS observado (fingerprint) | host/puerto no documentado; ruta no autorizada |
| **P1 SYSTEM IDENTITY** | SID, producto, versión (SAP/S4/HANA), mandantes | consultas de metadata estándar autorizadas (p. ej. endpoint raíz OData/SOAP metadata, `SELECT VERSION` en cuenta RO si aplica) | cualquier lectura de datos de negocio | identificación capturada (producto, versión, SID, mandantes) | identificación no autorizada; datos inesperados |
| **P2 PERMISSIONS** | Verificar alcance real de la cuenta read-only sobre los 12 objetos | catálogo de autorizaciones expuesto por el propio servicio (403/401 en endpoints prohibidos) | elevar permisos, probar escritura, adivinar scopes | matriz objeto→permitido/denegado | la cuenta puede escribir o ve más de lo previsto |
| **P3 METADATA/CATALOG** | Qué servicios existen (OData/CDS/SOAP), esquema de campos de cada objeto | `$metadata`, WSDL, HAL links, catálogo de tablas/vistas expuestas | descargar datos reales de negocio | metadata por objeto; mapeo campos SAP↔contrato inbound | exposición de datos no catalogada |
| **P4 TINY READ-ONLY SAMPLES** | Confirmar campos y semántica con muestras mínimas | lecturas con `LIMIT 10` por objeto (o `$top=10`), datos enmascarados si aplica | volúmenes grandes; filtros con datos personales; exportes | muestra por objeto + campos presentes/ausentes vs contrato | impacto en performance; datos sensibles no acordados |
| **P5 RECONCILIATION** | Conteos, watermarks, deltas viables | conteos agregados (`COUNT`), max(timestamp) de columnas candidatas | traer datasets completos | tablas de conteo; columnas de cambio detectadas; viabilidad snapshot/delta por objeto | consultas costosas; falta de columnas de cambio |
| **P6 DISCONNECT** | Cierre limpio y saneado | teardown de sesión/ruta; archivar evidencia saneada; destruir artefactos temporales con credenciales | dejar rutas/túneles activos; persistir secretos | acta de cierre + evidencia archivada + confirmación sin secretos | cualquier residuo de credenciales → remediar antes de cerrar |

## 3 · Secuencia y prerrequisitos

```
GATE SAP0_PROBE_AUTHORIZATION (Owner)
   → SAP-BASIS-01 (respuesta a §4 de este documento)
   → entorno y cuenta RO confirmados (canal seguro)
   → P0 → P1 → P2 → P3 [→ P4 → P5] → P6
```

Sin `SAP-BASIS-01` y el gate, el probe **no comienza**. El resultado alimenta `SAP_LANDSCAPE_DISCOVERY_SPEC.md` (campos UNKNOWN→VERIFIED) y `SAP_CONNECTIVITY_OPTIONS_ANALYSIS.md` (decisión `SAP-CONN-01`).

## 4 · Solicitud formal de información a SAP Basis (§36) — **sin passwords**

> Texto a enviar al equipo SAP Basis/Integración. Ningún ítem requiere credenciales: los secretos se gestionan aparte por canal seguro una vez acordado.

| # | Pregunta | Respuesta | Quién |
|---|---|---|---|
| 1 | Producto SAP exacto (S/4HANA, ECC, otro) y edición | | Basis |
| 2 | SID(s) y mandantes accesibles (¿`120` sigue activo?) | | Basis |
| 3 | Versión SAP y versión S/4HANA / componente | | Basis |
| 4 | Versión de base de datos (HANA, versión) | | Basis |
| 5 | ¿Existe ruta de red desde nuestro entorno? ¿Cuál (VPN dedicada, Cloud Connector, endpoint expuesto)? | | Basis + Seguridad |
| 6 | ¿Se requiere VPN? Si sí, ¿la provee SAP o nosotros? Especificación | | Basis + Seguridad |
| 7 | Host y puerto de HANA (si aplica SQL read-only) | | Basis |
| 8 | ¿Es posible una cuenta técnica **read-only** para los 12 objetos? ¿Perfiles/autorizaciones? | | Basis + Seguridad |
| 9 | Rango de IPs de origen permitido | | Seguridad |
| 10 | ¿OData disponible? ¿Gateway configurado? ¿Qué servicios estándar aplican (API_PURCHASEORDER, API_MATERIAL_DOCUMENT, API_BUSINESS_PARTNER, …)? | | Basis/Integración |
| 11 | ¿CDS views disponibles/exponibles (analytics)? | | Basis/ABAP |
| 12 | ¿SOAP disponible? ¿Existen los Z-servicios conocidos (`ZwsTasaMortalidad`)? ¿Se mantienen? | | Basis/ABAP |
| 13 | ¿IDoc disponible para recepción de documentos? | | Basis |
| 14 | ¿RFC/BAPI permitido? ¿Restricciones de red (sapgw)? | | Basis/Seguridad |
| 15 | ¿SAP Cloud Connector / BTP disponible como alternativa de túneles? | | Basis/Arquitectura |
| 16 | Listado de servicios/servicios custom Z vigentes y propietario funcional | | Basis/ABAP |
| 17 | Company Codes existentes y activos | | Basis/FI |
| 18 | Plants existentes y su clasificación funcional (granja / incubadora / planta / administrativa) | | Basis/PP + Negocio |
| 19 | Contacto Basis formal + horario de ventana para un probe read-only | | Basis |
| 20 | Contacto de Seguridad/Integración para aprobar cuenta y ruta | | Seguridad |

## 5 · Evidencia y trazabilidad

- Cada fase produce un artefacto `verification/P<N>_*.log` (saneado) en la fase de ejecución futura (no en SAP-0).
- Los resultados actualizan `SAP_LANDSCAPE_DISCOVERY_SPEC.md` con `VERIFIED` + fuente (no se reescriben: se añade evidencia).
- Todo hallazgo se clasifica `CONFIRMED_CURRENT_FACT` / `PARTIAL` / `STILL_UNKNOWN`.

## 6 · Condiciones globales de parada

1. Ausencia del gate `SAP0_PROBE_AUTHORIZATION` o de `SAP-BASIS-01`.
2. Cualquier indicio de permisos de escritura en la cuenta de probe.
3. Exposición de secretos o datos personales en logs.
4. Impacto observable en el sistema SAP (latencias, avisos de Basis).
5. Entorno productivo sin autorización explícita para P4/P5.

## 7 · Estado

`SAP_DISCOVERY_EXECUTION = PLANNED_NOT_EXECUTED` · `SAP_CONNECTION_ATTEMPTS = 0` · `VPN_SESSIONS = 0`.
