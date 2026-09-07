# `OD-08` · LOS TÉRMINOS DEL PROPIETARIO CONTRA LOS ROLES REALES

`OD-08` · `docs/02 §6.1` · migración `l2m3n4o5p6q7` · `GA-REM-038`

`OD-08` nombra **funciones** —administrador, contralor, gerente del área, supervisor—. Esta
matriz las contrasta con los roles que existen de verdad, antes de escribir una línea de
código. Ninguna fila se rellenó por intuición.

---

## 1. Los dos catálogos, que no coinciden

```
docs/02 §6.1 · catálogo NORMATIVO ......... 11 roles
migración l2m3n4o5p6q7 + baseline ......... 6 roles sembrados
```

| `docs/02 §6.1` | ¿Sembrado? |
|---|:--:|
| Super Administrador | sí (`baseline_seeds`) |
| **Administrador de Empresa** | **no** |
| Supervisor Avícola | sí |
| Aprobador | sí |
| Operador de Granja | sí |
| Operador de Incubadora | no |
| Operador de Engorde | no |
| Veterinario | no |
| Analista SAP | sí |
| Auditor | sí |
| Consulta / Reportes | no |

El desfase es **anterior** a este trabajo y no se corrige aquí: `GA-REM-034` dio administración
de roles, de modo que una empresa puede crear los que le falten. Lo que sí importa es que el
resolutor de destinatarios funcione con los que existan, sin exigir que estén todos.

## 2. La matriz

| Owner term | Actual role(s) | Evidence | Exists | Used |
|---|---|---|:--:|:--:|
| **Administrador** | `Administrador de Empresa` | `docs/02 §6.1` — **normativo** | catálogo sí · sembrado **no** | **sí**, por nombre |
| | `Super Administrador` | `seeds/baseline_seeds.py:65` | sí | **sí, pero solo si pertenece a la empresa** — ver §3 |
| **Contralor / Contraloría** | `Contralor Avícola` | `seeds/integration_seeds.py:137` — **nivel 5** | no sembrado en baseline | **sí**, por nombre |
| **Gerente del área** | — | **ninguna fuente** | **NO** | **no** — hueco declarado |
| **Supervisor** | `Supervisor Avícola` | `docs/02 §6.1` + migración `l2m3n4o5p6q7` | **sí** | **sí** |

## 3. `Super Administrador` no recibe por serlo

`OD-08` dice «usuarios administradores **de la empresa correspondiente**». El Super
Administrador del baseline se siembra con `company_id = None` —sin inquilino fijo—, de modo que
**no pertenece** a ninguna empresa.

Incluirlo por su rol produciría exactamente la fuga que `§6` del encargo advierte: un usuario
de plataforma recibiendo el detalle operativo de todas las empresas.

```
La condición es la pertenencia, no el rol:
    user.company_id == evento.company_id   Y   su rol es administrativo
```

Un Super Administrador **con** empresa asignada sí califica; uno sin ella, no. La regla se
aplica igual a todos los términos de `OD-08`, no solo a éste.

## 4. `Contralor`: por qué se usa una fuente de nivel 5

`docs/02 §6.1` no tiene rol de contraloría. La única aparición en el repositorio es
`Contralor Avícola` en un seed de escenario, que en la jerarquía de evidencia es
**implementación**, por debajo de una spec.

Se usa igualmente, y conviene decir por qué: **`OD-08` es una decisión del propietario, nivel
1**. La función «contraloría» está normativamente exigida por ella. Lo que falta no es el
requisito sino su nombre en el catálogo, y el nombre que este proyecto ya emplea es
`Contralor`. Inventar otro sería peor: crearía dos vocabularios para lo mismo.

Si una empresa no tiene ningún rol de contraloría, **no se avisa a nadie por ese concepto** y
nada falla — el mismo criterio que ya rige para `Analista SAP` en el aviso de error de SAP.

## 5. `Gerente del área`: hueco, y de dos clases a la vez

No hay rol de gerencia en `docs/02 §6.1`, ni en la migración, ni en ningún seed. Y tampoco hay
**área**:

```
tablas con área / departamento / unidad organizativa ....... ninguna
campos de User ....... id · company_id · nombres · email · username · phone
                       hashed_password · role_id · view_type · is_active
                       last_login · created_at · updated_at
```

El usuario no se asocia a granja, galpón, incubadora ni a nada operativo: solo a una empresa y
a un rol. Es el **`CASE C`** de `§12` del encargo —ni los roles identifican el área ni el
usuario la tiene asignada— y se declara en vez de taparse.

```
BLOCKED_BY_MODEL_GAP    gerente del área
```

## 6. `Supervisor`: existe, y el «correspondiente» no es ambiguo

`OD-08` dice «el supervisor **correspondiente**», que en un sistema con áreas significaría «el
de su área». Aquí no hay áreas, pero tampoco hay **más de un rol supervisor**: el catálogo
normativo tiene exactamente uno, `Supervisor Avícola`, y toda la operación es avícola.

De modo que «el correspondiente» no deja nada por decidir: son los supervisores de esa empresa.
No se está eligiendo entre varios ni ampliando a todos los de la plataforma —el filtro de
empresa sigue aplicándose—.

Si algún día existieran áreas, esta fila tendría que revisarse. Queda dicho.

## 7. Cómo se hace la correspondencia, en concreto

Por **nombre de rol**, sin distinguir mayúsculas ni acentos, sobre los usuarios activos de la
empresa del evento. No por identificador: los identificadores dependen del orden de siembra y
`GA-REM-034` permite crear roles nuevos, de modo que fijarlos sería frágil.

```
ADMINISTRADOR   nombre contiene «administrador»     → Administrador de Empresa, Super Administrador
CONTRALOR       nombre contiene «contralor»         → Contralor Avícola
SUPERVISOR      nombre contiene «supervisor»        → Supervisor Avícola
GERENTE         —                                    sin rol que buscar (§5)
```

Y sobre todos ellos, siempre: `user.company_id == evento.company_id` y `user.is_active`.

## 8. Resumen

| Término de `OD-08` | Estado |
|---|:--:|
| Persona que cargó el dato | **RESOLUBLE** — ver `P14_NOTIFICATION_RECIPIENT_MATRIX.md` |
| Administradores | **RESOLUBLE** |
| Contraloría | **RESOLUBLE** |
| Gerente del área | **BLOCKED_BY_MODEL_GAP** |
| Supervisor | **RESOLUBLE** |

```
Unresolved role mapping = 1 de 5   (gerente del área)
```
