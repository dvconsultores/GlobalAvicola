# R-188 · P2 · OPEN — BU-D10: AUTO-REACTIVACIÓN DE CONCESIONES AL RE-ENCENDER UNA UNIDAD DE EMPRESA (vs. OD-23 = B)

## Identificación

- **Finding**: **R-188** (siguiente libre tras R-187 CLOSED_OWNER_ACCEPTED; disponibilidad verificada).
- **Severidad**: **P2** — defecto funcional/de política de seguridad (acceso productivo se «resucita» sin acto explícito), sin pérdida de datos, sin fuga cross-tenant.
- **Tipo**: Brecha de implementación vs regla de negocio ratificada (OD-23); la conducta actual era provisional declarada, no un defecto de código.
- **Hogar**: `audit/ga-bu-d10/`.

## Contexto

Producto actual (provisional A, probado): apagar una BU de empresa no toca concesiones (`AC-A04`); al re-encender, las concesiones previas **vuelven a ser efectivas automáticamente** (`AC-A06`; `test_deshabilitar_no_borra_las_concesiones_y_rehabilitar_las_devuelve`).

**OD-23 (2026-09-11, propietario) = B**: apagar **termina** las concesiones vivas del ciclo (marcadas, no borradas); el re-encendido **no** devuelve efectividad; cada usuario requiere concesión nueva explícita; transferencia de empresa intacta; sin migración.

## Decisión que lo gobierna

`OD-23` — `GA_OD_BU_D10_OWNER_DECISION.md` (RATIFIED). Reemplaza la nota «provisional A» de `BUSINESS_UNIT_OWNER_DECISION_MATRIX.md §7` (que ya no aplica como conducta objetivo).

## Alcance del trabajo pendiente (SPEC → RED → impl → runtime → UAT)

1. SPEC + AC + matriz L1-L16 (`.md` en este hogar) — incluye semántica de sesión (relectura por petición), auditoría (§4 de OD-23) y concurrencia básica.
2. Implementación mínima: al **apagar** (`fijar_habilitacion`, `admin.py`), marcar `revoked_at` de las concesiones vivas de ESA habilitación + auditoría individual (causa declarada) + docstrings alineados; resolver intacto (ya exige `revoked_at IS NULL`).
3. Actualización de las pruebas de la conducta provisional (`AC-A04` conserva «no borra»; `AC-A06` pasa a «no reviven; concesión nueva restaura»).
4. Runtime autenticado E2E (BU ON/OFF/re-enable, sesión activa, refresh/relogin, Access Admin, self-grant, cross-company, zero-BU, RBAC-neg, global+OFF, auditoría, persistencia).
5. **UAT del propietario REQUIRED** (cambia comportamiento visible de acceso).

## Dedup

- **Distinto** de R-185/OD-21 (referencias inactivas), R-187/OD-22 (escala IPE), R-163 (guarda de escritura), R-113/R-121/R-128 (cerrados vía OD-13/OD-15), R-98 (cerrado).
- **Sin dueño previo**: BU-D10 era decisión pendiente sin finding (patrón de gobernanza); la brecha se abre ahora.
- **No reabre** OD-16 (absoluto se preserva) ni OD-09.e (transferencia se preserva).

## Estado

**`CLOSED_OWNER_ACCEPTED`** (2026-09-11 — tranche GA-UAT-08: decisión **A) ACEPTO R-188 / BU-D10 / OD-23**; UAT del propietario 5/5 PASS; registro `audit/ga-uat-08/GA_OWNER_ACCEPTANCE_R188_BU_D10_RECORD.md`). OD-23 = **RATIFIED_IMPLEMENTED_OWNER_ACCEPTED** · **BU-D10 = RESOLVED_OWNER_ACCEPTED**. Implementación C3 `bee33f5` (+C3b `399751c`); runtime E2E-01…14 + UI PASS; evidencia `audit/ga-bu-d10/` + `audit/ga-uat-08/`.
