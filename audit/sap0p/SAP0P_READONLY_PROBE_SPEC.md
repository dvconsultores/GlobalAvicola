# SAP-0P · SAP0P_READONLY_PROBE_SPEC

Fecha: 2026-09-17 · Contrato operativo del probe · **Nada de este contrato se ejecutó contra SAP** (bloqueo externo demostrado en P0/P1).

---

## 1 · READ_ONLY_CONTRACT (invariante)

1. Toda operación debe ser **demostrablemente** de solo lectura; si no puede demostrarse → **NO se ejecuta**.
2. Prohibido cualquier efecto: `INSERT UPDATE DELETE MERGE UPSERT CREATE ALTER DROP TRUNCATE GRANT REVOKE CALL(con efectos) BAPI/RFC de escritura IDoc saliente SOAP de escritura OData POST/PUT/PATCH/DELETE MIGO MIRO MB1A MB1B` y cualquier movimiento/documento/cambio de maestro.
3. **NO WRITE TEST BY WRITING**: la ausencia de privilegios de escritura se verifica por metadata de autorizaciones, nunca probando a escribir.
4. Queries siempre acotadas: `LIMIT/TOP ≤ 10` salvo metadata; filtros por mandante/company/plant cuando existan; prohibido full scan (especialmente MATDOC).
5. Si la cuenta exhibe privilegios excesivos → `SAP_READ_ONLY_ACCOUNT = FAIL_LEAST_PRIVILEGE` + gap de seguridad (no usar el privilegio).

## 2 · ALLOWED_ACTIONS (lista blanca)

| Acción | Condición |
|---|---|
| DNS resolution / `tcp connect` acotado a host:puerto **autorizado** | solo desde canal autorizado (P1) |
| Metadata de catálogo (existencia, columnas, tipos) | sin leer datos de negocio |
| `SELECT` con LIMIT ≤10 sobre tablas/objetos acordados | P5, tras P0–P4 PASS |
| `GET $metadata` / WSDL / service registry | sin invocación de negocio (P7) |
| Lectura de autorizaciones efectivas | sin elevar privilegios |
| Conteos pequeños | justificados y acotados |

## 3 · FORBIDDEN_ACTIONS (lista negra — §6 del mandato, íntegra)

Toda operación que pueda `INSERT UPDATE DELETE MERGE UPSERT CREATE ALTER DROP TRUNCATE GRANT REVOKE CALL con efectos BAPI de escritura RFC de escritura IDoc de salida SOAP de escritura OData POST/PUT/PATCH/DELETE MIGO MIRO MB1A MB1B movimientos de inventario documentos de material documentos contables cambios de maestros` · queries sin límite · conexión desde red no autorizada · instalar túnel nuevo sin autorización · reconfigurar firewall/red · persistir para credenciales · modificar archivos de producto · importar datos al dominio.

## 4 · Evidencia y sanitización (§36–§37)

**Permitido**: timestamps · purpose · query hash · nombres de tabla/objeto · row counts pequeños · field names · muestra saneada · status · latencia · error code no sensible.
**Prohibido**: password/token/PSK/private key/connection string completa/datos personales/dumps/headers secretos.
**Credenciales**: `SAP_USER_PRESENT = YES|NO`; passwords `REDACTED` siempre; jamás valores.

## 5 · Stop conditions (§38 — vigentes)

Cuenta no segura para RO · operación que requiera write · privilegios elevados · riesgo de lock · query no acotable · cambio destructivo de red · credenciales faltantes · schema irreconciliable sin resolución técnica · exposición de datos sensibles · decisión Owner requerida.
**Activada hoy**: «credenciales/canal faltantes» → `BLOCKED_EXTERNAL` + acción Basis única → STOP.

## 6 · Rollback / limpieza (P9)

No hay estado que revertir (solo lectura). Cierre: terminar sesión/ruta, no persistir credenciales, verificar evidencia saneada, acta de cierre. Si alguna operación mutante ocurriera (violación): STOP inmediato + registro de incidente + remediación por Basis (fuera de autonomía del agente).

## 7 · Cumplimiento en esta ejecución

| Regla | Evidencia |
|---|---|
| 0 operaciones SAP (ninguna conexión) | P0/P1 logs; `SAP_CONNECTION_ATTEMPTS=0` |
| 0 escrituras SAP | idem |
| 0 escrituras dominio | sin tocar BD del producto |
| 0 secretos en evidencia | solo conteos/presencia; revisión en `SAP0P_SECURITY_REVIEW.md` |
| Queries acotadas / 0 unbounded | `SAP0P_QUERY_REGISTER.md` (QUERIES_UNBOUNDED=0) |
| Sin prueba de escritura | nunca se intentó |
