# SAP-0P · SAP0P_PERMISSION_ASSESSMENT

Fecha: 2026-09-17 · Resultado: **cuenta técnica READ-ONLY no provisionada** → verificación de permisos no ejecutable. Sin inventar resultados (§9).

---

## 1 · Estado de la cuenta técnica

| Aspecto | Estado | Evidencia |
|---|---|---|
| Cuenta READ-ONLY entregada al ejecutor | **NO** | 0 env `HANA_*/SAP_*`; 0 claves SAP/HANA en `.env` (solo conteos) |
| Canal seguro para secretos | no disponible | `SAP_ADMIN_BASIS_ACTION_REQUIRED.md` lo exige |
| `SAP_USER_PRESENT` | **NO** | P0/P1 logs |
| Password de prueba | `REDACTED` (no existe; nunca se imprimió ninguno) | — |

## 2 · Verificación que quedó pendiente (P3 — no ejecutada)

1. `SELECT` permitido sobre los objetos necesarios (los 12 inbound + 9 tablas legacy).
2. Ausencia de privilegios de escritura **por metadata de autorizaciones** (`NO WRITE TEST BY WRITING`).
3. Scopes mínimos por objeto; revisión de autorizaciones excesivas → `FAIL_LEAST_PRIVILEGE` + gap.

Estas verificaciones requieren la cuenta provisionada y el canal autorizado; hoy: `NOT_VERIFIED` / `BLOCKED_EXTERNAL`.

## 3 · Requisitos exigidos a la cuenta (para la acción Basis)

- Usuario técnico dedicado, **solo lectura**, sin roles de escritura ni de administración.
- Autorización de lectura limitada a: `T001W, T001L, EKKO, EKPO, EKBE, LFA1, MATDOC, MAKT, T156HT` (+catálogo de metadata), y a los objetos de servicios (OData/CDS) que Basis habilite para discovery.
- Sin permisos sobre procedimientos con efectos; sin RFC/BAPI de escritura.
- Rotación y custodia por canal seguro (nunca en repo/chat).

## 4 · Riesgo declarado

| Riesgo | Estado |
|---|---|
| Verificación de privilegios | **PENDIENTE** hasta provisión |
| Uso de privilegio excesivo | no aplica hoy (no hay cuenta) |
| `LEAST_PRIVILEGE` | `NOT_VERIFIED` (no evaluado todavía) |

**No se usó, probó ni intentó ningún privilegio** — consistente con `SAP_WRITES_EXECUTED = 0`.
