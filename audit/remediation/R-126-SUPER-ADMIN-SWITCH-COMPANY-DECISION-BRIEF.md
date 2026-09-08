# `R-126` · ¿QUÉ SIGNIFICA `switch-company` PARA EL SUPER ADMINISTRADOR?

Expediente de decisión de propietario · 2026-09-08 · **sin cambios de código**

```
CLASIFICACIÓN     OWNER_DECISION_REQUIRED — no es un defecto
ESTADO            PENDIENTE DE PROPIETARIO
CÓDIGO MODIFICADO NINGUNO
```

---

## 1. Cómo salió esta pregunta

Al cerrar los `P0` de `/users` escribí una prueba que afirmaba que un Super Administrador
situado en la empresa `A` con `switch-company` debía ver **solo** usuarios de `A`. Rompió dos
suites certificadas que aprovisionan usuarios entre empresas.

La prueba estaba equivocada, no el producto. Pero la pregunta que la motivó es legítima y nadie
la ha contestado nunca.

## 2. La norma vigente

`docs/02-functional-spec.md §3.1.4`:

> «Super Admin (rol con `module="*", scope_type="all"`) ve TODAS las compañías.»

Y, dos líneas antes:

> «Cada usuario pertenece a una compañía (`company_id` requerido, excepto Super Admin).»

**El código cumple exactamente esto.** Por eso `R-126` no es un defecto.

## 3. El comportamiento real, hoy

| Superficie | Actor de empresa | Super Administrador | Super Administrador tras `switch-company` |
|---|---|---|---|
| `get_company_filter` | su `company_id` | `None` (sin filtro) | `None` (sin filtro) |
| `/users` listar | solo su empresa | **todas** | **todas** |
| `/users` crear | empresa impuesta | declara la empresa | declara la empresa |
| `/masters/*` | solo su empresa | **todos** | **todos** |
| `/masters/companies` | solo la suya (`R-115`) | **todas** | **todas** |
| `/business-units` (fase 7) | su empresa | `403` sin contexto | **acotado a la empresa elegida** |
| `switch-company` | no autorizado | emite token con `company_id` | reemite |
| `P-09` | registra su empresa | registra | registra `CONTEXT_SWITCHED` (`OD-11 §6`) |

**Aquí está la incoherencia real, y es la que motiva el expediente**: la administración de
unidades de negocio de la fase 7 **sí** se acota al contexto elegido —deniega con `403` si no
hay empresa efectiva—, mientras que `/users` y `/masters` **no**. Dos superficies del mismo
plano de control con dos respuestas distintas a la misma pregunta.

No es un descuido de la fase 7: `OD-11` decidió que administrar unidades exige una empresa
concreta porque una unidad **pertenece** a una empresa. Lo que nunca se decidió es si esa regla
vale para todo el plano de control.

## 4. Los dos conceptos que hoy se confunden

```
VISIBILIDAD GLOBAL      qué puede LEER el actor con autoridad sobre todas las empresas
CONTEXTO SELECCIONADO   en qué empresa OPERA ahora mismo
```

No tienen por qué ser lo mismo. `docs/02 §3.1.4` habla de la primera y calla sobre la segunda.

---

## Opción A · el contexto restringe también la lectura

Situarse en `A` acota **todo** —lecturas y escrituras— a `A`. Sin contexto, el Super
Administrador no ve nada operativo.

```
SEGURIDAD    la mejor. Un actor global comprometido solo alcanza la empresa en la que está,
             y cada salto queda en `P-09`. Reduce el radio de una sesión robada.
PRODUCTO     coherente con la fase 7 y con `OD-11`. Un solo modelo mental.
             Pero un inventario global —«¿cuántas empresas hay?»— deja de existir sin
             una superficie nueva que lo devuelva.
PRUEBAS      rompe al menos `test_t_073_06` (`GA-REM-029 AC07`) y `test_t_039_11`
             (`GA-REM-039`), que provisionan entre empresas con el administrador sembrado.
             Habría que reescribirlas para que hagan `switch` primero.
CONTRADICE   `docs/02 §3.1.4` tal como está escrita. Exige enmendar la spec, no solo el código.
FASE 8       la sesión entregaría `empresa seleccionada` obligatoria y `es_global` como
             capacidad administrativa, no como alcance de datos.
COSTE        alto — toca `get_company_filter`, y con él todos los servicios.
```

## Opción B · el contexto define la operación; la lectura de control sigue global

Situarse en `A` fija dónde se **crea y se modifica**. Las lecturas de control —catálogo de
empresas, inventario de usuarios— siguen siendo globales.

```
SEGURIDAD    intermedia. Cierra la escritura accidental en la empresa equivocada, que es el
             riesgo operativo real, y deja la lectura global — que es una capacidad
             declarada, no un descuido.
PRODUCTO     es lo más cercano a lo que hoy hace el producto y a lo que la spec dice.
PRUEBAS      impacto mínimo: las suites certificadas siguen valiendo.
CONTRADICE   nada. Es la lectura natural de `docs/02 §3.1.4`.
FASE 8       la sesión entrega `es_global`, `empresa_seleccionada` y `empresas_disponibles`;
             el frontend muestra el selector y avisa de en qué empresa se está escribiendo.
COSTE        bajo — sobre todo formalizar la regla y aplicarla a la escritura.
DEBILIDAD    no resuelve la incoherencia con la fase 7 salvo que se declare que administrar
             unidades es «operación» y no «lectura de control». Es defendible, pero hay que
             escribirlo.
```

## Opción C · superficies explícitamente separadas

Dos familias de rutas declaradas: control **global** y operación **acotada**.

```
/admin/companies          global · exige autoridad global
/masters/companies        acotado · devuelve la empresa efectiva
/admin/users              global
/users                    acotado
```

```
SEGURIDAD    la más clara de auditar: lo global se ve en el nombre de la ruta, no en el rol
             de quien llama. Un revisor sabe qué mirar.
PRODUCTO     el modelo mental más limpio a largo plazo y el que mejor soporta un tercer
             tipo de actor si algún día existe.
PRUEBAS      alto impacto: rutas nuevas, clasificación de alcance, permisos, frontend.
CONTRADICE   nada, pero exige spec propia.
FASE 8       la más simple de representar: el actor declara en qué familia está operando.
COSTE        el más alto. Es una `GA-REM` completa, no un ajuste.
```

## Otra opción · `B` ahora, `C` como destino

Formalizar `B` para cerrar la incoherencia con la fase 7 sin romper nada, y registrar `C` como
dirección arquitectónica para cuando exista una segunda superficie global que lo justifique.
Evita pagar el coste de `C` antes de necesitarlo, y evita quedarse en el estado actual, que es
`B` **sin escribir** — que es como se llegó hasta aquí.

---

## 5. Las quince preguntas

| # | Pregunta | Hoy | A | B | C |
|:--:|---|---|---|---|---|
| 1 | ¿El contexto restringe la lectura? | no | **sí** | no | según familia |
| 2 | ¿Restringe la escritura? | solo fase 7 | **sí** | **sí** | según familia |
| 3 | ¿Solo recursos operativos? | — | no | **sí** | explícito |
| 4 | ¿Qué control sigue global? | todo | nada | catálogo de empresas y usuarios | el declarado |
| 5 | ¿Hace falta empresa para mutar? | solo fase 7 | **sí** | **sí** | en la familia acotada |
| 6 | ¿Y sin empresa elegida? | ve todo | no opera | lee, no escribe | solo rutas globales |
| 7 | `effective_company` para actor global | `None` | obligatoria | opcional en lectura | por familia |
| 8 | ¿Qué devuelve `get_company_filter`? | `None` | la elegida | `None` en lectura | por familia |
| 9 | `/users` | todas | la elegida | todas | dos rutas |
| 10 | `/masters/companies` | todas | la elegida | todas | dos rutas |
| 11 | Auditoría | global | acotada | global | por familia |
| 12 | Unidades de negocio | **acotado** | acotado | acotado | acotado |
| 13 | Sesión (fase 8) | no existe | empresa obligatoria | `es_global` + elegida + disponibles | familia + alcance |
| 14 | Frontend | no lo muestra | selector obligatorio | selector + aviso de escritura | rutas distintas |
| 15 | ¿Se audita el cambio? | **sí**, `CONTEXT_SWITCHED` | sí | sí | sí |

La fila 12 es la que prueba que hay una incoherencia que resolver, no una preferencia estética.

---

## 6. Dependencias

### Fase 8 · sesión y capacidades

`T-040-20` debe entregar el alcance del actor, y **su forma depende de esta decisión**:

```
A   empresa_seleccionada OBLIGATORIA · sin ella la sesión no opera
B   es_global · empresa_seleccionada · empresas_disponibles · alcance_de_escritura
C   familia_de_superficie · y el alcance dentro de ella
```

Construir la carga de sesión antes de decidir significa rehacerla después. **Ésta es la razón
concreta por la que la fase 8 sigue congelada**, y no una precaución genérica.

### `R-113` · quién administra el acceso por unidad

**No depende de `R-126`.** El Administrador de Accesos que `R-113` plantea es un actor
**acotado a una empresa**: no tiene autoridad global y por tanto ninguna de las tres opciones
cambia lo que puede hacer. Las rutas de la fase 7 ya exigen empresa efectiva para todo el mundo.

`R-113` sigue congelado por su propia razón —falta decidir qué figura administra— y ya no por
los `P0`, que están cerrados.

### `RQ-03`

`R-126` **no** bloquea `RQ-03`. Lo que la mantiene `PARTIAL` es `R-121` (`roles` sin acotar).

---

## 7. Recomendación de ingeniería

```
RECOMENDACIÓN DE INGENIERÍA — NO ES DECISIÓN DEL PROPIETARIO
Opción B, formalizada por escrito, con `C` registrada como dirección.
```

**Por qué.** Es la única que no contradice `docs/02 §3.1.4`, que es norma vigente y no una
casualidad del código. No invalida ninguna certificación. Cierra el riesgo real —escribir en la
empresa equivocada— sin retirar una capacidad que la spec concede explícitamente. Y su coste es
sobre todo de escritura: el producto ya se comporta casi así; lo que falta es que esté decidido
en lugar de heredado.

**Contra qué se decide.** `A` es más segura y yo la preferiría en un producto nuevo, pero exige
enmendar la spec, reescribir suites certificadas y quitarle al Super Administrador una capacidad
que hoy usa el aprovisionamiento. Eso es una decisión de producto, no una corrección técnica, y
no me corresponde.

**Lo que hay que escribir en cualquier caso**, gane la que gane: qué es «operación» y qué es
«lectura de control». Hoy la fase 7 responde una cosa y `/users` otra, y esa discrepancia
existirá igual hasta que alguien la nombre.

---

```
DECISIÓN DEL PROPIETARIO   PENDIENTE
```
