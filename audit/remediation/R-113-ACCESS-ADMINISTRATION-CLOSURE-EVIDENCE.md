# `R-113` · LA FIGURA QUE ADMINISTRA EL ACCESO

`OD-15 §6` · `AC-S06`…`AC-S09` · 2026-09-09

```
R-113  =  CERRADO
```

---

## 1. La decisión: **CREAR**

Ninguno de los cinco roles sembrados podía extenderse sin cambiar lo que significa.

```
Supervisor Avícola   supervisa producción       ← explícitamente descartado
Operador de Granja   registra en campo
Aprobador            aprueba registros
Analista SAP         opera la integración
Auditor              lee
```

Se crea **«Administrador de Accesos»**, siguiendo la convención de nombres del catálogo.

## 2. Permisos · exactamente cuatro

```
business_units:read     ver la configuración y las concesiones
business_units:update   habilitar y deshabilitar cadenas para la empresa
business_units:create   conceder a un usuario
business_units:delete   revocar a un usuario
```

Y **nada más**. Ni `users:*` —el conjunto que mantuvo cuatro `P0` latentes—, ni comodín, ni
ninguna cadena productiva.

**Consecuencia asumida y escrita**: con solo esos cuatro no puede listar usuarios, porque
`users:read` es otra cosa. La interfaz necesitará ofrecerle candidatos por una superficie
propia. Se prefiere esa incomodidad a ampliar el rol.

`AC-S06` compara el conjunto **exacto** contra la constante sembrada: un quinto permiso rompe.

## 3. Dónde se siembra, y por qué no hace falta migración

En `baseline_seeds.py`, junto a `ACCIONES_COMODIN` y por el mismo motivo que aquél: la migración
de reconciliación `l2m3n4o5p6q7` solo cubre **roles operativos**, y éste es plano de control.
Sembrar un rol no justifica una migración nueva, y editar una ya aplicada no la volvería a
ejecutar.

```
MIGRACIÓN   ninguna · head sigue `s9t0u1v2w3x4`
```

## 4. `OD-09.b` demostrado con esta figura concreta

El par, sobre el mismo actor y la misma sesión:

```
CONTROL       sin ninguna cadena concedida (`efectivas == []`)
              lista · habilita · deshabilita · concede a otro · revoca a otro   200 / 201
TRATAMIENTO   `GET /lots/{id}` de un lote de incubadora                          404
              y el listado no lo trae
```

El actor tiene `lots:read`, de modo que el `404` **no puede venir de `RBAC`**: viene de no tener
la cadena concedida. Sin ese detalle la prueba mediría el permiso y no el alcance.

Y con `OD-15` encima: tampoco puede concedérsela.

## 5. `Supervisor Avícola` no cambia

Se comprueba por dos vías, y las dos hacen falta:

```
en la semilla     su bloque no menciona `business_units`
en ejecución      recibe 403 en las cuatro superficies de administración
```

La segunda importa más: el supervisor de la prueba **sí tiene Incubadora concedida**, de modo
que su negativa viene de no tener autoridad administrativa, no de no tener nada. Sin esa
concesión, el 403 sería compatible con un actor que no puede nada.

## 6. El guardián que tenía razón

`test_rbac.py` exige que todo permiso reclamado por una ruta lo conceda algún rol o conste como
exclusivo del Super Administrador. La fase 7 metió los cuatro en `SOLO_SUPER_ADMIN`, el segundo
guardián saltó por crecimiento, y **subí su tope de 15 a 17**.

Ahora las cuatro entradas **salen** y el tope vuelve a **15**.

```
Es la primera vez en este programa que esa lista BAJA.
La salida correcta de un guardián que se queja no es subirle el tope:
es contestar lo que está señalando. Señalaba que faltaba un rol.
```

## 7. Condiciones de cierre

| Condición | Estado |
|---|:--:|
| rol explícito existe | ✔ |
| permisos mínimos, conjunto exacto | ✔ |
| `Supervisor Avícola` no los recibe | ✔ |
| sin comodín ni autoridad global | ✔ |
| asignar el rol crea cero concesiones y cero habilitaciones | ✔ |
| administra una cadena que no puede operar | ✔ |
| administración entre empresas denegada | ✔ |
| auto-concesión denegada (`OD-15`) | ✔ |
| concesión a otro usuario funciona | ✔ |
| arranque por Super Administrador situado | ✔ |
| `P-09` audita concesión y revocación | ✔ |
| guarda transaccional en verde | ✔ |
| regresión completa | ✔ 754 |
