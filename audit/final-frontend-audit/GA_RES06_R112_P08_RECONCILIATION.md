# RES-06 / R-112 · RECONCILIACIÓN — CONTRATOS SAP Y P-08

Fecha: 2026-09-11 · Fila: **FVA-32** (BLOCKED_EXTERNAL) · RFC: `REMEDIATION_BACKLOG.md:550`, `audit/frontend-runtime/BACKEND_CAPABILITY_MAP.md:47`, `PHASE_9_DEPENDENCY_PREFLIGHT.md:149`.

## 1 · Qué es R-112 (canónico)

```
R-112  ocho superficies SAP sin proyección declarada (contrato de respuesta no declarado)
SEVERIDAD P2 · descubierto por mutación de sensibilidad de OD-12 · ESTADO: 1 de 9 corregida · 8 registradas.
```

- Deuda **técnica de contrato** (response_model/proyección) en 8 rutas `/sap/*`; se solapa con `OD-12` (verificar cierre conjunto).

## 2 · Determinaciones

| Pregunta | Respuesta |
|---|---|
| Estado | **ABIERTO** registrado (8 superficies); sin cambio desde su registro |
| ¿Qué puede certificarse sin SAP real? | La **UI SAP de referencias/consolidación** (`/sap`, permisos `sap:read`/`sap:send_sap`) sobre datos internos existentes — hoy ya verificada en runtime (S20); el batch de certificación de FVA-32 no forma parte de las 19 (está en BLOCKED_EXTERNAL) |
| ¿Qué queda externo? | La **integración real** (conector, HANA, credenciales, payload mapeable, confirmaciones entrantes) — **P-08 `BLOCKED_EXTERNAL`** |
| ¿El cierre frontend debe clasificarlo BLOCKED_EXTERNAL en vez de residual funcional? | **SÍ** — así está ya clasificada FVA-32 (BLOCKED_EXTERNAL); R-112 es deuda de contrato **dentro del dominio externo-bloqueado**, no un gap funcional de frontend |

## 3 · Dedup y disposición

R-112 **no se duplica**. Queda como **item técnico a programar con la preparación SAP/Wave C** (junto a OD-12). No bloquea el cierre frontend ni la preparación de Wave B (es trabajo SAP-futuro). No se crea ningún conector ni migración (`sap_config` intacto).
