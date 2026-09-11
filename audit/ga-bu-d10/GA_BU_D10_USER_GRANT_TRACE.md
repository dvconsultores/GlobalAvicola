# GA-BU-D10 · TRAZA DE CONCESIÓN / REVOCACIÓN DE USUARIO

Fuente: `backend/app/business_units/admin.py::conceder` (`:286-358`), `revocar` (`:363-…`), `candidatos_de_concesion` (`:234-283`); `service.py::conceder_unidad` (`:201`), `revocar_unidad` (`:353`); `router.py:167-227`.

## 1 · Conceder (`POST /users/{id}/business-units`, permiso `business_units:create`)

Cuatro puertas, en orden deliberado:

```
1  self-grant        actor == target ⇒ SegregacionDeFunciones (OD-15.a)   ← comprobada PRIMERO
2  misma empresa     usuario activo de la empresa efectiva ⇒ si no, 404   ← anti-enumeración (no dice si existe en otra)
3  habilitación      la empresa debe TENER la unidad: sin fila ⇒ 404
                     y debe estar HABILITADA: si está apagada ⇒ 400
                     «la empresa no tiene habilitada la unidad 'X'; habilítela primero»
                     ⇒ CONCEDER NO HABILITA (nunca enciende por la puerta de atrás)
4  concesión viva    si ya existe viva ⇒ devuelve la existente, SIN auditar
                     (idempotente; un registro por repetición inflaría la auditoría)
```

- Escritura por el camino sancionado `conceder_unidad` (valida que la habilitación sea de la empresa del usuario — OD-09.d).
- Auditoría de la concesión **real**: `PERMISSION_CHANGE` / `users`, `previous_state=none → granted`, `new_values={target_user_id, business_unit}`.
- **Mientras la unidad está apagada no se puede conceder** — relevante para Option B: el flujo de re-autorización siempre pasa por encender primero.

## 2 · Revocar (`DELETE /users/{id}/business-units/{code}`, permiso `business_units:delete`)

- **Marca, no borra** (`AC-B11` / OD-09.e): `revoked_at = now()`. Efecto inmediato (el resolutor exige `revoked_at IS NULL`) sin perder historia.
- Revocar lo que no está vivo ⇒ **404** explícito («no es un éxito silencioso»).
- Auditoría `PERMISSION_CHANGE`, `granted → revoked`.
- No toca lo que el usuario registró mientras tuvo la unidad (§6.3: retirar acceso ≠ borrar trabajo).

## 3 · Candidatos (`GET /business-units/{code}/grant-candidates`, permiso `business_units:create`)

- Refleja las puertas del POST: unidad conocida ∧ habilitación **habilitada** (si no ⇒ 400 — «no hay a quién concederla»).
- Lista usuarios **activos de la empresa efectiva**; excluye al actor (cortesía sobre OD-15.a). Sin parámetros de búsqueda ⇒ sin oráculo.
- Solo lectura; sin auditoría de éxito. Es la superficie normal del «Administrador de Accesos» (OD-15 §6: cuatro permisos exactos; no requiere `users:read`).

## 4 · Duplicados y concurrencia básica

- Índice único **entre vivas** `(user_id, company_business_unit_id) WHERE revoked_at IS NULL` ⇒ imposible duplicar una concesión viva; revocar y reconceder crea fila nueva (historia completa).
- Carrera grant/grant: la segunda transacción retorna la viva existente (sin auditoría duplicada) o falla por el índice y reintenta el camino idempotente.
- Carrera grant/revoke simultáneos: el orden transaccional decide; el resolutor lee el estado persistido en cada petición ⇒ nunca hay «autocuración» de acceso.

## 5 · La regla de transferencia de empresa (comparador — NO es BU-D10)

- `revocar_concesiones` (`service.py:321-350`): marca **todas** las concesiones vivas del usuario con `revoked_at=now()`. Docstring: «**Debe invocarse cuando un usuario cambia de empresa»… «volver no prueba el mismo cargo ni la misma necesidad operativa» (OD-09.e).
- Pruebas: `test_una_concesion_de_la_empresa_anterior_no_se_lista_como_actual` (`test_business_unit_admin.py:703`) y `test_volver_a_la_empresa_anterior_no_reactiva_la_concesion` (`:727`, `AC-B12`): regresa a A ⇒ `efectivas == []`; con concesión **nueva** ⇒ `["hatchery"]`.
- **Estado real hoy (declarado en el código)**: *«Hoy no hay ningún camino que cambie la empresa de un usuario: `UserUpdate` no acepta `company_id`, y `switch-company` desplaza el contexto sin tocar `users.company_id`. Esta función existe antes que su llamador…»*. Es decir: la regla está **modelada y probada en el modelo/servicio**, pero **no hay API viva que transfiera de empresa** — no hay exposición al usuario.
- Conclusión comparadora: la política «volver no reactiva; hace falta otorgar de nuevo» **ya existe en este producto** para el cambio de empresa (ratificada en OD-09.e), pero **no gobierna** BU-D10 por analogía automática: el propietario debe decidir si esa analogía se aplica al ciclo apagar/encender.

## 6 · Superficie de UI

- `frontend/src/pages/admin/UnitAccessPage.tsx` (control-plane) + `UserBusinessUnitsButton` (`frontend/src/pages/users/`) que muestra por concesión: «Concedida» y `is_effective` (viva ∧ habilitada ∧ activa) — `businessUnits.service.ts:22`.
- La nav productiva y guards usan `effective_business_units` de `/me` (GA-FE-03/04 certificados). Cualquier cambio de política B se refleja en estas superficies sin rediseño: usan el estado efectivo, no el histórico.
