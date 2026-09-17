# SAP-0P · SAP0P_PROBE_PLAN

Fecha: 2026-09-17 · Fase SAP-0P · Plan de ejecución P0–P10 · **Ejecutado hasta P1 (local); P2–P7 BLOCKED_EXTERNAL**.

---

## 1 · Principios de ejecución

Solo lectura · sin efectos · query acotada (LIMIT ≤10) · evidencia saneada · stop antes que improvisar · una única acción externa si falta acceso (hoy activa).

## 2 · Fases

### P0 — PREFLIGHT / SAFETY ✅ EJECUTADO
1. Repo limpio en `0904330` (= SAP0_CLOSURE_SHA) ✔
2. Sin cambios de producto pendientes (diff `backend/frontend/e2e/.github` vacío) ✔
3. Entorno de ejecución autorizado: **NO IDENTIFICADO** (ver P1)
4. Presencia de configuración **sin imprimirla**: 0 env `HANA_*/SAP_*`; `.env` presente con 0 claves SAP/HANA ✔
5. Política READ ONLY confirmada (spec §6 del mandato) ✔
6. Límites sample: 1–10 filas; MATDOC máxima restricción ✔
7. Timeouts definidos (conexión ≤10 s; queries ≤30 s) ✔
8. Evidencia sanitizada definida (lista blanca §36) ✔
9. Stop conditions §38 establecidas ✔

### P1 — NETWORK / VPN ⛔ BLOQUEADO (demostrado localmente)
| Check | Resultado |
|---|---|
| `ipsec` / `xl2tpd` instalados | AUSENTES |
| Interfaces `ppp*`/`tun*` | 0 |
| Config VPN local (`vpn/`) | ausente |
| DNS host legacy `vhemsds4ci.sap.liderpollo.com` | 0 resoluciones |
| Reachability HANA | **NO INTENTADA** — conexión desde red no autorizada prohibida (fail-closed) |
- `NETWORK_ROUTE = BLOCKED` (canal autorizado ausente) · `VPN = BLOCKED` (no provisionada) · `HANA_PORT_REACHABILITY = NOT_ATTEMPTED (BLOCKED_EXTERNAL)`.

### P2 — SYSTEM IDENTITY / VERSION ⛔ NO INICIADO
Obtener (con canal + cuenta RO): HANA version, identidad DB, SID, schema, mandante(s). Sin procedimientos desconocidos. Sin elevar privilegios.

### P3 — PERMISSIONS ⛔ NO INICIADO
Verificar `SELECT` sobre objetos necesarios y ausencia de escritura **por metadata** (`NO WRITE TEST BY WRITING`). Exceso → `FAIL_LEAST_PRIVILEGE` + gap.

### P4 — METADATA / CATALOG ⛔ NO INICIADO
Para `T001W, T001L, EKKO, EKPO, EKBE, LFA1, MATDOC, MAKT, T156HT`: `EXISTS / SELECT_ALLOWED / KEY_COLUMNS_AVAILABLE / REQUIRED_FIELDS_AVAILABLE`.

### P5 — MINIMAL SAMPLE READS ⛔ NO INICIADO
Solo tras P0–P4 PASS; 1–10 filas; filtros por mandante/company/plant; sin datos personales; MATDOC acotadísimo.

### P6 — INBOUND OBJECT RECONCILIATION ⛔ NO INICIADO
Los 12 objetos: `AVAILABLE / SOURCE_VERIFIED / KEY_VERIFIED / MANDANT_SCOPE_VERIFIED / COMPANY_SCOPE_VERIFIED / DELTA_CANDIDATE / SAMPLE_VERIFIED / STATUS`. Hoy: 12/12 `NOT_VERIFIED`.

### P7 — SERVICE CAPABILITY DISCOVERY ⛔ NO INICIADO
OData `$metadata` / CDS catalog / WSDL de `ZwsTasaMortalidad` — solo discovery no mutante; **nunca** POST SOAP ni operación de negocio.

### P8 — EVIDENCE / SANITIZATION 🔶 PARCIAL (P0/P1)
Registrar por query: `QUERY_ID, PURPOSE, TARGET, READ_ONLY_JUSTIFICATION, START_TIME, END_TIME, ROW_LIMIT, RESULT_STATUS, SANITIZATION, EVIDENCE_FILE`. Ver `SAP0P_QUERY_REGISTER.md`.

### P9 — DISCONNECT / CLEANUP ⬜ N/A
No hubo sesión. Regla futura: cerrar sesión/ruta, cero persistencia de credenciales, acta de cierre.

### P10 — CERTIFICATION ✅ EJECUTADO
`SAP0P_READONLY_PROBE_CERTIFICATION.md`: certifica **solo** lo demostrado (P0/P1 local) y declara el bloqueo externo; nada se redondea hacia arriba.

## 3 · Secuencia de reanudación (cuando exista acceso)

```
SAP ADMIN / BASIS ACTION cumplida (único requisito externo)
→ P0 re-run en entorno autorizado
→ P1 real (VPN/route/HANA reachability)
→ P2 → P3 → P4 → [P5 → P6 → P7]
→ P8 evidencia completa → P9 cierre → P10 certificación real
```

## 4 · Stop conditions (resumen operativo, §38)
Cuenta no segura para RO · query que requiera write · privilegios elevados · riesgo de lock · query no acotable · cambio destructivo de red · credenciales faltantes · schema irreconciliable · datos sensibles expuestos · decisión Owner requerida.

## 5 · Estado actual
```
SAP0P_PROBE = BLOCKED_EXTERNAL
MOTIVO = canal autorizado no provisionado (VPN/ruta/cuenta/host-port vigentes)
ACCIÓN ÚNICA = audit/sap0p/SAP_ADMIN_BASIS_ACTION_REQUIRED.md
PRÓXIMA EJECUCIÓN = tras cumplirse la acción, desde P0 en el entorno autorizado
```
