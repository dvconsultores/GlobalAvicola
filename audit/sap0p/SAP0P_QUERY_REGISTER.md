# SAP-0P · SAP0P_QUERY_REGISTER

Fecha: 2026-09-17 · Registro de **todo** lo ejecutado por SAP-0P (P0/P1 local).
**REAL_SAP_READS = 0 · SAP_QUERIES = 0 · QUERIES_UNBOUNDED = 0 · SAP_WRITES = 0** — no existió sesión SAP (bloqueo externo).

Formato (§37): `QUERY_ID · PURPOSE · TARGET · READ_ONLY_JUSTIFICATION · START · END · ROW_LIMIT · RESULT · SANITIZATION · EVIDENCE_FILE`

| QUERY_ID | PURPOSE | TARGET | READ_ONLY_JUSTIFICATION | START (UTC) | END (UTC) | ROW_LIMIT | RESULT | SANITIZATION | EVIDENCE_FILE |
|---|---|---|---|---|---|---|---|---|---|
| CHK-001 | Repo limpio + SHA (P0) | git local | comando de lectura de metadatos git | 2026-09-17T00:37:20Z | 2026-09-17T00:37:27Z | n/a | PASS (clean, `HEAD=0904330`) | solo salida textual git | `evidence/P0_PREFLIGHT_CHECK.log` |
| CHK-002 | Diff de producto vacío (P0) | git local | `git diff --name-only` (lectura) | idem | idem | n/a | PASS (0 archivos) | lista vacía | idem |
| CHK-003 | Presencia config HANA/SAP (P0) | env local | conteo de nombres — **no valores** | idem | idem | n/a | 0 env vars | **solo conteo** | idem |
| CHK-004 | Presencia claves en `.env` (P0) | `.env` local | `grep -c` de nombres de clave — **no valores** | idem | idem | n/a | 1 archivo / 0 claves SAP-HANA | **solo conteo** | idem |
| CHK-005 | Herramientas VPN legacy (P1) | host local | `command -v` (lectura) | idem | idem | n/a | ipsec AUSENTE · xl2tpd AUSENTE | n/a | `evidence/P1_NETWORK_LOCAL_CHECK.log` |
| CHK-006 | Interfaces ppp/tun (P1) | host local | `ip -brief link` (lectura) | idem | idem | n/a | 0 | n/a | idem |
| CHK-007 | DNS host legacy (P1) | resolver local | `getent hosts` (resolución, no conexión a SAP) | idem | idem | n/a | 0 resoluciones | n/a | idem |
| CHK-008 | Tooling local (P0) | host local | import check (lectura) | idem | idem | n/a | hdbcli AUSENTE · requests PRESENTE | n/a | idem |

## Declaraciones

- **Ninguna** de las entradas anteriores tocó SAP, ni la red SAP, ni credenciales.
- **No se intentó** `tcp connect` al host SAP: la única ruta disponible sería no autorizada (prohibido; fail-closed). Se registrará como P1 real tras provisionarse el canal (`HANA_PORT_REACHABILITY`).
- **No hay** queries a HANA/OData/SOAP: `REAL_SAP_READS = 0`.
- Cada query futura (P2–P7) se añadirá aquí con `READ_ONLY_JUSTIFICATION` explícita y `ROW_LIMIT` visible.
- Passwords/PSK/keys: **0 en evidencia** (nunca se imprimieron ni se buscaron valores).
