# SAP-0P · SAP ADMIN / BASIS ACTION REQUIRED

**Acción única y bloqueante emitida por SAP-0P** (mandato §9): el probe no pudo iniciarse porque el entorno de ejecución no dispone de acceso autorizado al landscape SAP. Este es **el único requerimiento externo** para desbloquear SAP-0P.

**Estado**: `OPEN` · **Emisión**: 2026-09-17 · **Dirigido a**: SAP Basis / SAP Administración (Lider Pollo) con copia al Owner de Global Avícola.
**Prohibido incluir en la respuesta por canales no seguros**: passwords, PSK, claves privadas. Los secretos se entregan por canal seguro acordado y **nunca** en este documento, repo o chat.

---

## 1 · Evidencia del bloqueo (resumen saneado)

| Check (2026-09-17, entorno de ejecución SAP-0P) | Resultado |
|---|---|
| Herramientas VPN legacy (`ipsec`, `xl2tpd`) | ausentes |
| Interfaces `ppp*`/`tun*` | 0 |
| Configuración VPN local | ausente |
| Variables de entorno `HANA_*`/`SAP_*` | 0 |
| Claves HANA/SAP en `.env` | 0 |
| DNS de `vhemsds4ci.sap.liderpollo.com` | 0 resoluciones |
| Conexión intentada a SAP | **ninguna** (prohibido desde red no autorizada) |

Referencias: `SAP0P_CONNECTIVITY_FINDINGS.md` · `evidence/P0_PREFLIGHT_CHECK.log` · `evidence/P1_NETWORK_LOCAL_CHECK.log`.

## 2 · Requisitos exactos para desbloquear (checklist a completar por Basis)

| # | Requisito | Formato de entrega | ¿Completado? |
|---|---|---|---|
| A1 | **Canal de red autorizado vigente** hacia el landscape: tipo de VPN actual (o Cloud Connector) y ruta exacta hacia el host de datos, provista al entorno de ejecución de SAP-0P | Descripción técnica (sin PSK) + provisión efectiva del canal | ☐ |
| A2 | **Host y puerto vigentes** de HANA (o endpoint del servicio autorizado para discovery) | Valores (no sensibles por sí solos) | ☐ |
| A3 | **SID + mandante(s)** del sistema objetivo (confirmación de identidad; p. ej. ¿el `120` histórico sigue vigente?) | Texto | ☐ |
| A4 | **Cuenta técnica READ-ONLY dedicada** con `SELECT` limitado a: `T001W, T001L, EKKO, EKPO, EKBE, LFA1, MATDOC, MAKT, T156HT` (+ catálogo de metadata). Sin roles de escritura/administración | Usuario + secreto **por canal seguro** (no en este documento) | ☐ |
| A5 | **Ventana autorizada** para ejecutar el probe read-only (P0–P7, sin impacto productivo esperado) | Fecha/hora y contacto de guardia | ☐ |
| A6 | **Endpoints de discovery no mutante** habilitados (si existen): `GET $metadata` OData, catálogo CDS, WSDL de servicios Z vigentes (p. ej. `ZwsTasaMortalidad` ¿sigue desplegado?) | Lista de URLs/servicios (sin credenciales) | ☐ |
| A7 | **Contactos** Basis + Seguridad para incidencias durante la ventana | Nombres/canales | ☐ |

## 3 · Qué hará Global Avícola al recibirlo (sin intervención adicional de Basis)

1. Ejecutar P0 (preflight) en el entorno autorizado con el canal provisto.
2. Ejecutar P1–P7 estrictamente **read-only** (LIMIT ≤10 por query; sin escrituras; evidencia saneada).
3. Actualizar la certificación (`SAP0P_READONLY_PROBE_CERTIFICATION.md`) y la evaluación `GL-OD-06` con evidencia real.
4. Emitir addenda documental mínima; **ninguna** implementación de producto (SAP-1/G1/G2 no se inician aquí).

## 4 · Qué NO se solicita (límites explícitos)

- ❌ Permisos de escritura de ningún tipo (se rechazaría por diseño).
- ❌ Passwords/PSK en texto plano por este documento o cualquier canal no seguro.
- ❌ Cambios en el sistema SAP (el probe no necesita ninguna modificación).
- ❌ Acceso a datos de negocio más allá de muestras estructurales ≤10 filas.

**RESPUESTA REQUERIDA**: completar A1–A7 y responder al Owner. Hasta entonces: `SAP0P_STATUS = BLOCKED_EXTERNAL` y **STOP** (sin improvisar rutas alternativas).
