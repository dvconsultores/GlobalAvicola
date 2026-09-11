# GA-FE-04 · LEDGER DE DATOS DE PRUEBA

Provisionados y retirados en la misma sesión (2026-09-11). Credenciales efímeras nunca en el repo; destruidas al cierre.

## Roles

| Id real | Nombre | Permisos | Estado final |
|---|---|---|---|
| 41 | GA-FE04 TEST READ-ONLY ADMIN | dashboard:read · masters:read · users:read | `is_active=false` |
| 42 | (duplicado del anterior, creado por reintento) | — | `is_active=false` (desactivado en provisión) |
| 43 | GA-FE04 TEST PRODUCTIVE CREATE | dashboard:read · lots:read+create · operations:read+create | `is_active=false` |
| 44 | GA-FE04 TEST CBU ADMIN | dashboard:read · business_units:read+update | `is_active=false` |
| 45 | GA-FE04 TEST CORE ONLY | dashboard:read | `is_active=false` |
| 35 | **Administrador de Accesos (canónico)** | business_units:* | **INTACTO — nunca modificado** |

Nota de reconciliación: el borrador preveía `41=C / 42=R`; la asignación real fue `41=R`, `42=duplicado (off)`, `43=C`, `44=A`, `45=D/Z/P`. La matriz de actores quedó reconciliada con los ids reales.

## Usuarios

| Usuario | Id | Rol | Vista | Autoridad observada | Estado final |
|---|---|---|---|---|---|
| ga-fe04-r | 98 | 41 | web | lectura admin | baja (204) |
| ga-fe04-a | 99 | 44 | web | CBU update | baja (204) |
| ga-fe04-b | 100 | 35 | web | acceso por unidad (canónico) | baja (204) |
| ga-fe04-c | 101 | 43 | web | productivo con escritura | baja (204) |
| ga-fe04-d | 102 | 45 | web | solo dashboard | baja (204) |
| ga-fe04-z | 103 | 45 | web | solo dashboard (cero unidades) | baja (204) |
| ga-fe04-p | 104 | 45 | web | RBAC-negativo con concesión | baja (204) |

## Concesiones (unidades)

| Usuario | Unidad | Acciones | Resultado |
|---|---|---|---|
| ga-fe04-c | broiler | POST concesión (201, `is_effective=true`) → DELETE revocación (200, `revoked_at` fijado) | propagación UI verificada (nav/páginas) |
| ga-fe04-p | broiler | POST concesión (201, `is_effective=true`) → DELETE revocación (200) | sin efecto en acciones (RBAC ausente) — caso 3D 3 |

## Unidades de empresa (ventana 3D)

| Unidad | Antes | Durante ventana | Restauración |
|---|---|---|---|
| broiler | OFF | ON (PATCH enable 200) | **OFF** (PATCH disable 200) |
| breeder / grandparent / hatchery | OFF | OFF (no tocadas) | OFF |

Estado final: **4 × OFF** (idéntico al inicio).

## Verificación de cierre

- `/users` (admin): ninguna cuenta `ga-`/`ga_` visible → 0 residuos.
- `/roles` (admin): ningún rol `GA-FE04` activo; rol 35 activo.
- Credenciales: `/tmp/ga4_creds.json`, `/tmp/ga4_r_creds.json` destruidos.

---

## GA-FE-04-A · Fixtures self/cross (2026-09-11, misma sesión)

| Alias | Usuario | Id | Rol | Empresa | Estado final |
|---|---|---|---|---|---|
| B | ga-fe04a-b | 105 | **35 canónico (reutilizado)** | 1 «Avícola Global C.A.» | baja 204 |
| T | ga-fe04a-t | 106 | 3 «Operador de Granja» | 1 | baja 204 |
| X | ga-fe04a-x | 107 | 3 «Operador de Granja» | 3 «Avícola Del Sur C.A.» | baja 204 |

Roles nuevos: **ninguno**. Ventana controlada: `broiler` ON en empresa 1 (solo para cargar candidatos) → restaurado **OFF** (4×OFF).
Concesiones creadas: **ninguna** (self 403 · cross 404 · concesiones de X en empresa 3 = `[]`).
Verificación de residuos: empresa 1 `[]` · empresa 3 `[]` · rol 35 intacto · credenciales `/tmp/ga4a_creds.json` destruidas.
