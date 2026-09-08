# `R-113` · REEVALUACIÓN

2026-09-08 · **NO implementado en esta tanda**

```
ESTADO   READY_TO_RESUME  ·  con una pregunta de segregación abierta
```

---

## 1. Por qué estaba congelado

`R-113` planteaba crear la figura que administra el acceso por unidad de negocio. Se congeló
porque **otorgarle `users:*` habría convertido cuatro vulnerabilidades latentes en explotables**:
sin ningún rol sembrado que alcanzara esas superficies, los `P0` de `/users` eran teóricos. El
día que existiera un actor empresarial con esos permisos, dejarían de serlo.

## 2. Qué ha cambiado

| Superficie que preocupaba | Estado hoy | Cerrado por |
|---|---|---|
| listar usuarios de otra empresa | acotado | `AC13` |
| leer un usuario ajeno por identificador | `404` | `AC13` |
| editar un usuario ajeno | `404`, sin efectos | `AC14` |
| convertir a un ajeno en Super Administrador | `403` | `AC15` |
| ver o editar roles de otra empresa | acotado | `OD-13.d` |
| repartir autoridad global desde una empresa | `403` | `OD-13.c` |
| operar sobre un inquilino sin estar en él | `403` / cero filas | `OD-14.d` |

**El Administrador de Accesos es un actor acotado a una empresa.** Ninguna de las superficies
que va a tocar le deja salir de ella, y eso ya no depende de que se acuerde nadie: lo sostienen
27 mutaciones de sensibilidad.

## 3. La pregunta que queda, y que no decido yo

`business_units:create` autoriza a conceder unidades a **cualquier usuario de la empresa
efectiva, incluido uno mismo**. Está documentado desde la fase 7, probado y auditado con actor y
objetivo.

Con el aislamiento cerrado, el alcance de esa propiedad es exactamente:

```
PUEDE       concederse a sí mismo cualquier cadena que su empresa tenga habilitada
NO PUEDE    habilitar cadenas nuevas (`business_units:update` es otra acción)
NO PUEDE    salir de su empresa
NO PUEDE    fabricar autoridad global
QUEDA       registrado en `P-09` con actor y objetivo
```

Es un riesgo **acotado y visible**, no una escalada. Pero es una pregunta de segregación de
funciones legítima: *¿quien reparte accesos debe poder dárselos a sí mismo?*

```
OWNER_DECISION_REQUIRED   ·  no se cambia en silencio
```

Si el propietario quiere separarlo, la forma natural existe ya: `business_units:create` es una
acción propia, y una regla de «no sobre uno mismo» cabría en la misma capa donde vive `AC15`.
No se implementa sin decisión.

## 4. Veredicto

```
R-113   READY_TO_RESUME
```

Prerrequisitos satisfechos: `R-114`, `R-115`, `R-116`, `R-117`, `R-118`, `R-121`, `R-126`,
`RQ-03 = COMPLETE`.

Lo que falta para cerrarlo sigue siendo lo que faltaba desde el principio, y no es técnico:
**qué figura de una avícola administra el acceso por unidad**. Ninguno de los cinco roles
sembrados lo hace, y crear uno sin que el propietario diga cuál es sería inventar una figura que
ninguna fuente describe.
