# GA-BU-D10 · TRAZA DEL ACCESO EFECTIVO

## 1 · Resolutor central (fuente única)

`backend/app/business_units/service.py::unidades_efectivas_por_id` (`:97-124`). Una consulta, cuatro puertas:

```
empresa actual del usuario (company_id)         ← sin ella, un usuario sin empresa heredaría lo de otra
AND CompanyBusinessUnit.is_enabled = TRUE        ← habilitada por la empresa   (apagar prevalece)
AND UserBusinessUnit.user_id = usuario
AND UserBusinessUnit.revoked_at IS NULL          ← concesión VIVA              (revocar surte efecto)
AND BusinessUnit.is_active = TRUE                ← activa en el producto
```

**Se lee de la base en cada llamada, no de un token ni de una caché** (docstring explícito) ⇒ una revocación o un apagado surten efecto en la evaluación **siguiente**, sin esperar a que caduque ninguna sesión.

`unidades_efectivas(db,user)` (`:61`) y `tiene_acceso` (`:187`) delegan aquí (una sola política).

## 2 · Alcance productivo (OD-16)

`unidades_de_alcance_productivo` (`:126-147`):
- **actor de empresa** ⇒ `unidades_efectivas_por_id` (habilitada ∧ concesión viva).
- **autoridad global (`is_super_admin`)** ⇒ `unidades_habilitadas` — se le exime la **concesión de usuario**, **nunca la habilitación**. Con BU OFF, su alcance productivo es vacío (OD-16; probado en runtime GA-FE-02-D/E: global + OFF ⇒ DENY).

Salvedad documentada en `:... `: `unidades_concedidas` (`:149-184`) es **para contar, no para autorizar** — `/me` informa las dos listas (habilitadas/concedidas vs efectivas) para que un cliente distinga «nunca se lo dieron» de «se lo dieron y la empresa cerró esa línea» (AC-H11/A04).

## 3 · Puntos de aplicación (el resolutor no es decorativo)

| Capa | Punto | Archivo |
|---|---|---|
| Operar (escrituras) | `exigir_unidad_operativa` / `exigir_acceso_a_unidad` | `lots/service.py:90`, `operations/service.py:192` |
| Leer productivo | `unidades_de_alcance_productivo` | `lots/service.py:70`, `operations/service.py:106`, `reports/service.py:30`, `dashboard/service.py:29`, `review/service.py:139/432/644` |
| Predicados de consulta | `business_units.scope.predicado` / `lotes_alcanzables` | `masters/service.py:115`, `scope.py` |
| Presentación | `/me` compone (habilitadas/concedidas/efectivas) | `auth/router.py:45-78` |
| Navegación FE | `effective_business_units` + guards `requiresUnits` | `frontend/src/auth/navigation.ts:43`, `getNavItemsForViewType`, pruebas GA-FE-03 |
| Autoridad intra-pantalla FE | ActionGate por permisos | pruebas GA-FE-04 |

## 4 · Qué pasa cuando la empresa cambia el estado de una unidad

- **Apagar** (`is_enabled=False`): la consulta del resolutor deja de devolverla en la evaluación siguiente ⇒ `/me` deja de listarla como efectiva; navegación/deep-links caen en el guard; API directa ⇒ 404/403 gobernado (OD-16). **No hay invalidación de sesión necesaria** porque no hay estado cacheado: la regla se relee por petición.
- **Encender** (`is_enabled=True`): misma relectura. Si la concesión anterior sigue **viva** (hoy sí, apagar no toca concesiones), la evaluación siguiente la devuelve como efectiva ⇒ **comportamiento provisional A** hasta que el propietario decida.

## 5 · Límite y control-plane

- `OD-09.b` / `OD-15`: **administrar acceso ≠ acceder**. El módulo `admin.py` no consulta ni modifica `unidades_efectivas` del actor; un «Administrador de Accesos» sin concesión propia no ve dato productivo (control-plane puro).
- `OD-09.a` (contraloría) y permisos `*` son **otro resolutor** (visibilidad de control), no amplían BU productivas.
- RBAC sigue siendo una puerta **posterior** e independiente: unidad efectiva sin permiso ⇒ DENY (y viceversa).
