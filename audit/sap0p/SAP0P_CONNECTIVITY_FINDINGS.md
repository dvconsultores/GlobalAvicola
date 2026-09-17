# SAP-0P · SAP0P_CONNECTIVITY_FINDINGS

Fecha: 2026-09-17 · Resultado: **canal autorizado ausente en el entorno de ejecución** → `NETWORK_ROUTE=BLOCKED`, `VPN=BLOCKED`, `HANA_CONNECTIVITY=NOT_VERIFIED` (probe no iniciado). Sin conexiones no autorizadas.

---

## 1 · Verificación P1 ejecutada (solo local, no invasiva)

| Check | Resultado | Evidencia |
|---|---|---|
| Interfaz/ruta requerida (ppp0/tun) | **0** interfaces | `evidence/P1_NETWORK_LOCAL_CHECK.log` |
| Herramientas VPN legacy (`ipsec`, `xl2tpd`) | **AUSENTES** | idem |
| Configuración VPN local (`vpn/`) | ausente | idem |
| Resolución DNS de destino legacy `vhemsds4ci.sap.liderpollo.com` | **0 resoluciones** | idem |
| Reachability al puerto HANA (30241 histórico / endpoint WS 44300) | **NO INTENTADA** | ver §2 |

## 2 · Decisión de no conectar (fail-closed, §9/§18 del mandato)

La única ruta disponible sería desde una **red no autorizada**:
1. El contrato del probe exige ejecutar **desde el canal autorizado** (VPN/ruta acordados con SAP/Basis).
2. Un intento de `tcp connect` desde aquí sería tráfico a un sistema de tercero fuera del canal acordado → **prohibido** por seguridad (no «reachability informativa» legítima).
3. Aunque un endpoint público respondiera, **no existiría cuenta técnica** para el probe: el resultado no sería verificable ni autorizado.

Por tanto: no se ejecutó ningún `tcp connect` a SAP. `SAP_CONNECTION_ATTEMPTS = 0`.

## 3 · Registros exigidos (§18)

```
NETWORK_ROUTE = BLOCKED        (canal autorizado ausente; sin intento por ruta no autorizada)
VPN = BLOCKED                  (no provisionada en el entorno de ejecución; legacy 'L2TP-PSK/LP' es LEGACY_CONFIRMED)
HANA_PORT_REACHABILITY = NOT_ATTEMPTED (BLOCKED_EXTERNAL)   [enumeración PASS|FAIL reservada a intento real]
```

## 4 · Trazabilidad con SAP-0

- SAP-0 dejó el plan P0–P6 conceptual con las mismas reglas (`SAP_DISCOVERY_EXECUTION_PLAN.md` §2 y §6); SAP-0P hereda los stop conditions y añade la decisión de no conexión desde red no autorizada.
- El descubrimiento de disponibilidad OData/CDS/SOAP queda en `NOT_VERIFIED` técnico (owner-confirmed sin cambios, §30).

## 5 · Condición de desbloqueo (ver acción Basis)

Provisión por SAP/Basis de: ruta/VPN operativa hacia el entorno, host/puerto vigentes, y ventana autorizada; y entrega segura de la cuenta RO. Con eso, P1 real se ejecuta y este documento se actualiza con resultados de `reachability` (PASS/FAIL reales).
