# OD-11 — LA EMPRESA EFECTIVA DE UNA PETICIÓN

## Metadata
| Campo | Valor |
|---|---|
| ID | `OD-11` |
| Tipo | **Decisión normativa** (no es una remediación) |
| Fecha | 2026-09-07 |
| Origen | Resolución explícita del propietario del producto |
| Estado | **VIGENTE** |
| Alcance | Contexto de inquilino: `GA-REM-040` fase 2 y todo lo que lo consuma |
| Complementa | `OD-09` · `OD-10` · `GA-REM-002` (`RBAC`) |
| Preserva | `R-48` · el aislamiento multiempresa certificado |

---

## 0. Por qué un `OD` aparte

`OD-09` declara que **visibilidad de control y acceso operativo son capacidades distintas**, y
`OD-10` que **entre unidades solo pasa el contrato**. Las dos tratan de la unidad de negocio.

Ésta trata de otra cosa: de **en qué empresa se está evaluando una petición**, que es anterior a
la unidad y anterior al permiso. Meterla en cualquiera de las otras dos mezclaría tres ejes que
esta misma decisión existe para separar.

```
CONTEXTO DE INQUILINO   ≠   ACCESO A UNIDAD   ≠   PERMISO RBAC
```

---

## 1. Declaración

```
LA EMPRESA EFECTIVA DE UNA PETICIÓN
    =  la empresa persistida del usuario

    SALVO que haya un contexto de cambio de empresa
           EXPLÍCITAMENTE AUTORIZADO y válido
```

Y, en negativo, que es la mitad que importa:

```
UNA RECLAMACIÓN DE EMPRESA EN EL TOKEN NO ES AUTORIDAD
POR EL HECHO DE EXISTIR
```

---

## 2. `OD-11.a` — El usuario normal

```
empresa efectiva  =  users.company_id
```

Si el token declara otra:

```
reclamación ≠ empresa persistida   →   la reclamación se IGNORA
```

El aislamiento multiempresa se sostiene precisamente sobre esto: un token no reclama compañías
ajenas. Es lo que `R-48` ya estableció y esta decisión ratifica, no cambia.

## 3. `OD-11.b` — El contexto autorizado

Existe `POST /auth/switch-company`, reservado al Super Administrador, que emite un token con la
empresa desplazada **sin tocar `users.company_id`**.

Ese contexto se honra, y **solo tras comprobar en el servidor**:

```
el actor puede cambiar de empresa
la empresa de destino existe
la empresa de destino está activa
```

Las tres, **en cada petición** y no solo al emitir el token: una empresa puede desactivarse
mientras la sesión sigue viva, y un contexto que se validó hace media hora no prueba nada sobre
ahora.

## 4. `OD-11.c` — Sin contexto válido no hay acceso productivo

```
sin empresa persistida  y  sin contexto autorizado válido
    →  NO HAY EMPRESA EFECTIVA
    →  acceso productivo DENEGADO
```

**No se resuelve «todas las empresas».** Un actor global sin contexto elegido no opera en
ninguna; elegir es un acto, no un valor por defecto.

## 5. Las tres dimensiones no se contaminan

```
CONTEXTO DE INQUILINO     ¿en qué empresa se evalúa esta petición?
ACCESO A UNIDAD           ¿qué cadenas productivas puede ver?        `OD-09` · `OD-10`
PERMISO RBAC              ¿qué acción puede ejecutar?                `GA-REM-002`
```

Una empresa efectiva válida responde a la primera y **a ninguna de las otras dos**. En concreto:

```
CAMBIAR DE EMPRESA CON ÉXITO   no concede ninguna unidad de negocio
                               no concede ningún permiso RBAC
```

El Super Administrador que se sitúa en una empresa obtiene **contexto**, no autoridad operativa
sobre sus cadenas: sus unidades efectivas se resuelven aparte y, si nadie se las concedió, son
ninguna.

## 6. El cambio de contexto deja rastro

```
quién · desde qué contexto · hacia qué empresa · cuándo
```

En **`P-09`**, con el mecanismo que ya existe, no en un registro paralelo. Situarse en otra
empresa es un acto de administración con consecuencias sobre qué datos se tocan, y hoy no queda
constancia de que ocurriera.

## 7. Lo que esta decisión NO cambia

- **`get_company_filter`** y el filtro de listados de `GA-REM-002` siguen como están. Su
  semántica está certificada y esta decisión no la reabre.
- **`RBAC`** no se sustituye ni se altera.
- **`P-14`**, `P-08`, `BU-D10`: sin tocar.
- **No hay esquema nuevo.** El contexto vive donde ya vive; lo que se añade es validarlo.

## 8. Trazabilidad

| Parte | Regla | `AC` de `GA-REM-040` |
|---|---|---|
| `OD-11.a` | usuario normal → empresa persistida | `AC-C09` · `AC-C10` |
| `OD-11.b` | contexto autorizado, validado en cada petición | `AC-C11` · `AC-C12` |
| `OD-11.c` | sin contexto no hay acceso productivo | `AC-C13` |
| `§5` | cambiar de empresa no concede unidades ni permisos | `AC-C14` |
| `§6` | el cambio se audita en `P-09` | `AC-I06` |
