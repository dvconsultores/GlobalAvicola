# GA-FE-02 · CUENTAS DE PRUEBA AUTORIZADAS REQUERIDAS

**Estado de credenciales**: NO se han recibido credenciales autorizadas del propietario en esta
tranche. Por diseño del encargo (§122 del prompt GA-FE-02): no se buscan credenciales en el
sistema de archivos ni en historial, no se usan credenciales sembradas conocidas (`admin/admin…`)
y no se adivinan. En consecuencia: `AUTHENTICATED E2E: BLOCKED_AUTH` (§123).

Este documento describe **qué cuentas se necesitan** para pasar la certificación funcional.
No contiene contraseñas — deben entregarse por el canal que el propietario designe.

## Actores requeridos

| # | Actor | Permiso requerido | Empresa requerida | Estado de unidades requerido | Por qué se necesita |
|---|---|---|---|---|---|
| A | **Administrador de Empresa con gestión de unidades** (o Super Administrador) | `business_units:read` · `business_units:update` (para habilitar/apagar) · `masters:read` si es super admin (selector) | Una empresa ACTIVA con al menos **una unidad de prueba apagada** (p.ej. breeder OFF) y una encendida | Mezcla ON/OFF para demostrar independencia | E2E-02/03 (habilitar/deshabilitar), AC-COMP-01/02 (contexto y selector), E2E-09 (ON sin concesión) |
| B | **Administrador de Accesos** (rol sembrado: 4 permisos `business_units:*`, sin `users:read`) | `business_units:read` · `update` · `create` · `delete` | La MISMA empresa que A | Al menos una unidad habilitada | E2E-04/05/06 (conceder/revocar/auto-concesión), E2E-08 (límites del rol), superficie de candidatos sin `users:read` |
| C | **Usuario objetivo operativo** (segundo usuario de la misma empresa) | Cualquier permiso operativo no relevante; sin `business_units:*` | La MISMA empresa que A/B | — | E2E-04/05 (efecto de la concesión/revocación en su sesión: relogin y acceso efectivo), E2E-09/10 |
| D | **Usuario de control negativo** (sin ningún permiso `business_units:*`) | Solo `lots:read` o similar | La MISMA empresa | — | E2E-08 (actor no autorizado: sin entrada de menú, ruta directa protegida, API denegada) |
| G *(opcional)* | **Super Administrador global** (sin empresa persistida o con contexto cambiado) | comodín `("*", …)` | — | — | E2E-01 (switch-company) y OD-14 (fail-closed sin contexto / contexto situado). Si no se dispone de credencial separada, se omite y se declara |

## Preparación recomendada del dato de prueba

```
1 empresa de prueba (o la ya existente) con:
   grandparent ON · breeder OFF · hatchery ON · broiler OFF   (estado mixto)
1 unidad candidata para encender/apagar en E2E-02/03 (breeder)
1 usuario objetivo C sin concesiones iniciales
1 usuario de control D sin permisos business_units
(la limpieza se hará al final de la sesión E2E: restaurar estados originales y
 revocar cualquier concesión creada con marcador GA_FE_02_E2E_<ts>)
```

## Qué se ejecutará cuando estén disponibles

`E2E-01` contexto/switch · `E2E-02` habilitar (+cero concesiones) · `E2E-03` deshabilitar
(+bloqueo productivo, plano de control disponible) · `E2E-04` conceder (+relogin del objetivo) ·
`E2E-05` revocar (+pérdida efectiva) · `E2E-06` auto-concesión denegada (UI+petición directa) ·
`E2E-07` usuario de otra empresa denegado · `E2E-08` actor no autorizado · `E2E-09` unidad ON sin
concesión ⇒ sin acceso · `E2E-10` concesión + unidad OFF ⇒ sin acceso productivo.

**Sin estas cuentas, la frontera certificable hoy es**: implementación completa desplegada +
paridad estática de marcadores; certificación funcional queda `BLOCKED_AUTH` (nunca
`FUNCTIONALLY_CERTIFIED` por anal(ogía).
