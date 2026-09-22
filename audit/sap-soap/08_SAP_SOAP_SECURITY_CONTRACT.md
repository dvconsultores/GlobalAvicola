# SAP-SOAP · 08_SAP_SOAP_SECURITY_CONTRACT

Fecha: 2026-09-22 · Seguridad del canal SOAP inbound (§29) · SIN credenciales reales en ningún artefacto

---

## 1 · Requisitos duros (no negociables)

| # | Requisito |
|---|---|
| S-01 | **HTTPS/TLS obligatorio** (TLS 1.2+; certificado válido de CA; sin excepciones de validación) |
| S-02 | Prohibido `verify=False` equivalente en cualquier cliente (lección del legacy: `session.verify=False` = `DO_NOT_REUSE`) |
| S-03 | Prohibido password en XML custom/URL/querystring; las credenciales **solo** por el mecanismo auth acordado (WSS/mTLS/Basic-over-TLS) |
| S-04 | Credenciales **nunca** en repo, logs, evidencia ni mensajes de error |
| S-05 | Secretos custodiados según modelo de custodia (`AOD-12`/`SAP-CUSTODY-01`, pendiente Owner) |
| S-06 | Rotación de credenciales soportada sin cambio de código |
| S-07 | Sin datos personales innecesarios en payloads ni evidencia |

## 2 · Opciones de autenticación a acordar con el proveedor (§29)

| Opción | Pros | Contras | Evaluación GA |
|---|---|---|---|
| **Basic Auth sobre TLS** | simple, ya usado por el legacy | credencial viaja en cada request (protegida por TLS); rotación manual | Aceptable como mínimo |
| **WS-Security UsernameToken** (PasswordDigest) | estándar WS; no expone password en claro | complejidad ABAP/WSS4J; reloj/servidor ajustado | **Recomendada si ABAP la soporta** |
| **mTLS (certificado cliente)** | sin password; fuerte identidad | gestión de certificados/rotación | **Preferida si la infraestructura lo permite** |
| **IP allowlist** (complemento) | reduce superficie | no autentica por sí sola | Complemento recomendado |

**Decisión**: opción final en la próxima reunión (OI-06, `13_…`). GA acepta cualquiera de las tres primeras **con TLS obligatorio**; la elección no puede violar S-01…S-07.

## 3 · Alcance de red (postura GA)

- El servicio SAP será consumido **desde el entorno autorizado designado** (servicio de integración/worker de GA), nunca desde el navegador ni desde el backend de usuario final.
- No se embebe VPN en la aplicación (lección legacy); la conectividad corporativa se resuelve en la capa de infraestructura que corresponda (decisión futura, fuera de esta SPEC).
- Firewall/allowlist mutuos documentados en el handshake operativo (no en este contrato funcional).

## 4 · Controles por artefacto

| Artefacto | Regla |
|---|---|
| WSDL/servicios | solo esquema; sin credenciales ni endpoints internos sensibles |
| Evidencia (RAW/auditoría) | headers de seguridad **jamas** persistidos; `Authorization` scrubbed |
| Logs | scrubbing de secrets; `CorrelationId` visible |
| Ejemplos del contrato | placeholders (`X-AUTH-PLACEHOLDER`), nunca valores reales |

## 5 · TLS: requisitos concretos

1. Cadena válida; hostname verificado; sin self-signed en producción (en sandbox: excepción **explícita y documentada**, nunca silenciosa).
2. Cifrados modernos (deshabilitar TLS < 1.2).
3. Pinning no requerido, pero fingerprint registrado en el acta de activación (fase SOAP-5+).

## 6 · Criterios de aceptación de seguridad (fases futuras)

| ID | Criterio |
|---|---|
| SEC-A1 | Handshake TLS válido contra el entorno real (sandbox) |
| SEC-A2 | Mecanismo auth acordado funciona y **no** aparece en logs |
| SEC-A3 | Rotación probada (procedimiento documentado) |
| SEC-A4 | Allowlist activa y verificada |
| SEC-A5 | Evidencia sin secretos (revisión estilo SAP-0P `SECRETS_IN_EVIDENCE=0`) |
