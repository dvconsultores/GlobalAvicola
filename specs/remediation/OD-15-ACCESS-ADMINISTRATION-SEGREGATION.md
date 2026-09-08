# `OD-15` · SEGREGACIÓN DE FUNCIONES EN LA ADMINISTRACIÓN DE ACCESO

Decisión de propietario · resuelve `R-128` · habilita el cierre de `R-113` · 2026-09-09 · **VIGENTE**

```
ADMINISTRAR EL ACCESO   ≠   ELEVAR EL PROPIO
```

---

## 1. `OD-15.a` · la decisión

Quien está autorizado a administrar el acceso por unidad de negocio **concede y revoca a otros
usuarios elegibles de su misma empresa efectiva**.

Esa autoridad **no** le permite concederse a sí mismo una unidad nueva.

```
actor == usuario objetivo   AND   operación == CONCEDER
→ DENEGADO
```

Aunque el actor tenga `business_units:create`. El permiso autoriza a **repartir**, no a
**recibir**.

## 2. `OD-15.b` · alcance exacto

Se aplica a la **auto-concesión de acceso a unidad de negocio**. Y a nada más.

```
NO ALCANZA   auto-revocación
NO ALCANZA   asignación de rol
NO ALCANZA   asignación de permisos
NO ALCANZA   cambio de empresa
NO ALCANZA   habilitar o deshabilitar unidades de la empresa
```

Auto-revocarse **no eleva privilegio**: lo reduce. Queda como política vigente, fuera de esta
decisión, y no se toca. Si alguien encuentra un riesgo independiente ahí, es un hallazgo nuevo,
no una extensión silenciosa de éste.

Habilitar una unidad para la empresa tampoco entra: es `business_units:update`, otra acción, y
habilitar no concede a nadie (`GA-REM-040` fase 7). Quien solo pueda habilitar no gana acceso, y
quien pueda conceder no puede dárselo a sí mismo. Las dos puertas quedan separadas.

## 3. `OD-15.c` · no hay excepción de arranque

```
PROHIBIDO   si el actor es el único administrador de accesos → permitirle auto-concederse
```

Existen dos vías legítimas para que un Administrador de Accesos reciba una unidad:

```
otro Administrador de Accesos de la misma empresa
Super Administrador situado en esa empresa       (`OD-14`)
```

Una excepción «si no hay nadie más» convertiría la regla en una sugerencia: bastaría con quedarse
solo. La segunda vía existe siempre, porque la autoridad global existe siempre.

## 4. `OD-15.d` · sigue siendo un acto explícito

Ninguna concesión se produce como efecto secundario:

```
asignar el rol de Administrador de Accesos   →  NO concede ninguna unidad
habilitar una unidad para la empresa         →  NO concede a nadie
crear un usuario                             →  NO concede nada
ser administrador y no tener concesiones     →  NO equivale a tenerlas todas
```

## 5. `OD-15.e` · el inquilino no cambia

Se preservan las tres condiciones de la fase 7, y `OD-15.a` **añade** la cuarta:

```
el usuario objetivo pertenece a la empresa efectiva
la habilitación pertenece a la empresa efectiva
la autoridad del actor es válida en esa empresa
el usuario objetivo NO es el actor                    ← nuevo
```

## 6. `R-113` · la figura que administra

Resuelto por la misma decisión, porque `R-128` era su bloqueo:

```
DECISIÓN            CREAR un rol propio · «Administrador de Accesos»
NO SE REUTILIZA     `Supervisor Avícola` supervisa producción, no reparte accesos
PERMISOS            `business_units:read` · `update` · `create` · `delete`
                    y NADA más — mínimo privilegio
NO RECIBE           comodín global · `users:*` · acceso productivo a ninguna cadena
AUTORIDAD           por permiso, nunca por nombre de rol
```

**Consecuencia asumida.** Con solo esos cuatro permisos, el Administrador de Accesos no puede
listar usuarios (`users:read` es otra cosa) y necesitará que la interfaz le ofrezca los
candidatos por una superficie propia. Se prefiere esa incomodidad a ampliar el rol: `users:*`
es justamente el conjunto que mantuvo cuatro `P0` latentes.

## 7. `P-09`

```
concesión con éxito       actor · empresa · objetivo · unidad · estado previo y nuevo
auto-concesión denegada   0 filas · 0 cambio de alcance efectivo · 0 auditoría de éxito
```

## 8. Trazabilidad

| `AC` | Qué |
|---|---|
| `AC-S01` | La auto-concesión de unidad se deniega en el servidor, con permiso válido y todo lo demás correcto |
| `AC-S02` | La concesión a otro usuario elegible de la misma empresa sigue funcionando |
| `AC-S03` | La denegación no deja fila, ni cambia el alcance efectivo, ni escribe auditoría de éxito |
| `AC-S04` | No existe excepción por ser el único administrador |
| `AC-S05` | El Super Administrador situado en la empresa puede conceder al Administrador de Accesos |
| `AC-S06` | Existe el rol «Administrador de Accesos» con exactamente cuatro permisos |
| `AC-S07` | `Supervisor Avícola` no los recibe |
| `AC-S08` | Asignar el rol no crea ninguna concesión ni habilita ninguna unidad |
| `AC-S09` | El rol no incluye `("*", …, "all")` |
