# LO QUE NO SE PUEDE ATRIBUIR

`GA-REM-040` fase 6 · `T-040-16` · `OD-10.c` · 2026-09-07

```
SIN CLASIFICAR  ≠  DE TODA LA EMPRESA
SIN CLASIFICAR  ≠  UNA QUINTA CADENA
SIN CLASIFICAR  ≠  BORRADO
```

---

## 1. Un campo nulable no es un pendiente

Lo primero que hubo que separar: **primero se deriva, y solo lo que no se puede derivar queda
pendiente.** Sin esa distinción la bandeja se habría llenado de registros que no necesitan a
nadie.

```
evento CON lote y el lote CON cadena   →  derived   se ve por derivación
evento con cadena fijada a mano        →  manual    alguien autorizado lo decidió
ninguna de las dos                     →  pending   ni se abre, ni se adivina, ni se borra
```

El estado **se deriva, no se guarda**. Guardar además un `status` daría dos fuentes que
discreparían el día que alguien rellene el lote sin tocar el estado.

## 2. La matriz

| Entidad | Derivación | Qué la deja pendiente | Ve el creador | Clasifica | Después de clasificar | Prueba |
|---|---|---|:--:|:--:|---|---|
| `operational_events` | `lot_id` → `Lot.bird_type` | sin lote, o el lote sin cadena | **sí**, los suyos | `masters:update` | alcance normal por cadena | `test_pending_classification.py` |
| `bird_movements` · `egg_movements` · `feed_movements` | vía el evento | hereda del padre | vía el evento | — | hereda del padre | ídem, por el evento |
| `inspection_details` | vía el evento | el evento puede no tener lote | vía el evento | — | hereda del padre | ídem |
| `hatchery_params` | vía el evento | ídem | vía el evento | — | hereda del padre | ídem |
| `approval_actions` · `correction_logs` | vía el evento | ídem | vía el evento | — | hereda del padre | ídem |
| `lots` con `bird_type` nulo | ninguna | el campo es nulable | — | **fuera de esta fase** | sigue denegado | `test_lot_row_scope.py` |

```
UN SOLO MECANISMO       el evento clasifica; los seis dependientes heredan
MOTORES INDEPENDIENTES  0        seis clasificaciones paralelas habrían acabado discrepando
```

**Los dependientes no tienen superficie propia.** Ninguna ruta expone `bird_movements`,
`egg_movements` ni `feed_movements`: viajan dentro del evento. Su alcance es el del padre por
construcción, no por una comprobación que alguien pueda olvidar — que es lo que `R-111` enseñó.

### 2.1 Los lotes sin cadena quedan fuera, y por qué

Clasificar un lote significaría rellenar `bird_type`, que es **dato de dominio**, no
configuración de acceso. Hacerlo desde aquí mezclaría los dos ejes que `GA-REM-040 §2` separa, y
la autoridad sobre ese campo es de los procesos de lote, no de esta capa.

```
REGISTRADO COMO HUECO   la vía para completar la cadena de un lote existente
                        pertenece a `P-03`/`P-06`, no a la clasificación de acceso
```

Mientras tanto siguen denegados, que es lo que la fase 3 dejó y sigue siendo lo seguro.

## 3. Quién ve un pendiente

```
quien lo registró          sus propios pendientes
el control autorizado      los de su empresa            `masters:update`
```

Y **nadie más**: ni un compañero de la misma cadena, ni un usuario de otra, ni otra empresa. No
es `fail open` — son dos partes nombradas, no «todos».

**La bandeja es superficie aparte.** Mezclar los pendientes en el listado operativo obligaría a
que cada consulta recordara la excepción del creador, y la que la olvidara abriría el sistema en
silencio.

## 4. Ver no es decidir

```
CREATOR VISIBILITY   ≠   CLASSIFICATION AUTHORITY
```

Quien registró el evento lo ve y **no puede clasificarlo**. Clasificar exige `masters:update`,
que es el permiso de administración de configuración: decidir a qué cadena pertenece un registro
no es producir, es configurar.

**Nunca por el nombre del rol.** `GA-REM-034` permite crear roles y el nombre es texto editable.

> Un permiso propio —`business-units:classify`— pertenece al catálogo de `GA-REM-034` y crearlo
> aquí sería ampliar el `RBAC` desde una fase que no lo gobierna. Queda anotado para la fase 7.

## 5. Clasificar no concede nada

```
NO concede la cadena a nadie          ni al creador, ni a quien clasifica
NO habilita la unidad a la empresa    eso es configuración comercial
NO toca `bird_type` del lote          el dato de dominio es de otro eje
NO cruza la empresa                   la habilitación tiene que ser del mismo inquilino
```

Y deja rastro en **`P-09`**, con el mecanismo que ya existe: quién, cuándo, desde qué estado y
hacia qué cadena. No en un registro paralelo, que daría dos historias del mismo hecho.

## 6. Después, manda el alcance normal

```
PENDING  →  CLASIFICADO  →  empresa + habilitación + concesión + RBAC + regla de negocio
```

**Haber creado el registro no es un salvoconducto permanente.** Si se clasifica como incubadora y
el creador solo tiene reproductora, deja de verlo. Es la propiedad que impide que
`created_by == user` se convierta en una puerta trasera permanente, y tiene prueba propia.

## 7. Lo que queda sin decidir

```
RECLASIFICAR UN REGISTRO YA CLASIFICADO     SPEC DECISION REQUIRED
```

No se implementa botón ni API: la primera clasificación está en alcance y la corrección
posterior no. Corregir una atribución después de que el registro haya circulado por un proceso
es una operación de alto control, y decidir su forma —edición auditada o anulación y rehacer— es
del propietario.

```
CLASIFICAR HACIA UNA UNIDAD APAGADA         se rechaza
```

Resuelto por la vía conservadora y con prueba: la clasificación **no enciende** lo que la empresa
apagó. Si el propietario quisiera permitir atribuir historia a una cadena ya retirada, es una
decisión suya y hoy no hace falta.
