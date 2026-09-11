# GA-FE-05 · LEDGER DE DATOS DE PRUEBA

Provisionados y retirados en la misma sesión (2026-09-11). Credenciales efímeras fuera del repo; destruidas al cierre.

## Roles

| Id real | Nombre | Permisos | Estado final |
|---|---|---|---|
| 46 | GA-FE05 TEST OPERATOR | dashboard:read · lots:read · operations:read+create | `is_active=false` |
| 47 | GA-FE05 TEST CORE ONLY | dashboard:read | `is_active=false` |
| 48 | GA-FE05 TEST REVIEWER | dashboard:read · operations:read · review:read+review · approvals:approve | `is_active=false` |
| 49 | GA-FE05 TEST READ ONLY OPS | dashboard:read · lots:read · operations:read | `is_active=false` |
| 35 | **Administrador de Accesos (canónico)** | business_units:* | **INTACTO** |

## Usuarios

| Usuario | Id | Rol | Concesión (ventana) | Estado final |
|---|---|---|---|---|
| ga05-c | 109 | 46 | broiler | baja 204 · revoke 200 |
| ga05-z | 110 | 46 | — | baja 204 |
| ga05-p | 111 | 47 | broiler | baja 204 · revoke 200 |
| ga05-d | 112 | 47 | — | baja 204 |
| ga05-v | 113 | 48 | broiler | baja 204 · revoke 200 |
| ga05-r | 114 | 49 | broiler | baja 204 · revoke 200 |

## Unidades de empresa (ventana)

| Unidad | Antes | Durante | Final |
|---|---|---|---|
| broiler | OFF | ON (fixtures/E2E) → OFF (E2E-02) | **OFF** |
| breeder/grandparent/hatchery | OFF | OFF | **OFF** |

Estado final: **4×OFF**.

## Fixtures de operación (retenidos como evidencia; flujo oficial, sin SQL)

| Evento | Lote | Cómo | Estado final |
|---|---|---|---|
| 44 | 11 (L-BO-2026-05) | create C → submit **UI** (E2E-01) | `pending_review` |
| 45 | 11 | create C → submit API | `pending_review` |
| 46 | 11 | create C → submit API → start V → return V → **UI resubmit** (E2E-07) | `pending_review` |
| 47 | 11 | create C → submit API → start V → approve V | `approved` |
| 48 | 11 | create C → submit **doble clic UI** (E2E-09) | `pending_review` |
| 49 | 11 | create C (negativos/fallo; nunca mutado) | `registered` |
| 50 | 11 | create E (CBU OFF) | `registered` |
| 51 | 11 | create C → submit **UI EN** | `pending_review` |
| 52 | 11 | create C → submit **UI móvil** | `pending_review` |

## Verificación de cierre

- Residuos `ga05-*` en `/users`: **0** · roles GA-FE05 activos: **0** · rol 35 activo.
- Revokes: 4/4 (200). Bajas: 6/6 (204). BU: 4×OFF.
- Credenciales: `/tmp/ga05_creds.json` destruido.
- Auditoría conservada (append-only); fixtures en estados legítimos de producto.
