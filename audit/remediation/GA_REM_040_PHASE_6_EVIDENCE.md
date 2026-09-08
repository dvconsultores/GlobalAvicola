# `GA-REM-040` FASE 6 · CLASIFICACIÓN PENDIENTE · EVIDENCIA

2026-09-07 · `T-040-16` · `T-040-17`

---

## 1. El inventario, y la primera distinción que hubo que hacer

```
UN CAMPO NULABLE NO ES UN PENDIENTE
```

`operational_events` es la **única** entidad con `lot_id`; las seis dependientes cuelgan de
`event_id`. Eso decidió la arquitectura: **un solo mecanismo, no siete**. Clasifica el evento y
los dependientes heredan, por construcción y no por una comprobación que alguien pueda olvidar —
que es lo que `R-111` enseñó.

| Entidad | Revisada | Derivable | Pendiente posible |
|---|:--:|:--:|:--:|
| `operational_events` | sí | vía `lot_id` → `bird_type` | **sí** |
| `bird_movements` · `egg_movements` · `feed_movements` | sí | vía el evento | hereda |
| `inspection_details` · `hatchery_params` | sí | vía el evento | hereda |
| `approval_actions` · `correction_logs` | sí | vía el evento | hereda |
| `lots` con `bird_type` nulo | sí | **no** | **fuera de esta fase** — §5 |

## 2. La arquitectura

```
DECISIÓN     CREATE, tras auditar reutilización
             no había cola de clasificación ni estado equivalente
```

Tres columnas en `operational_events` —`business_unit_id`, `classified_at`,
`classified_by_id`— y **ninguna en las seis dependientes**.

**El estado se deriva, no se guarda.** Persistir además un `status` daría dos fuentes que
discreparían el día que alguien rellene el lote sin tocar el estado: el mismo error que
`GA-REM-039` evitó al no guardar el gerente dentro del área.

**`business_unit_id` apunta a `company_business_units`**, no al catálogo, por la misma razón que
la concesión de un usuario (`OD-09.d`): la fila dice bajo qué empresa se clasificó, y la
combinación entre empresas no se puede ni escribir.

**No hay quinta unidad.** El catálogo sigue teniendo cuatro, con prueba dedicada.

## 3. Trazabilidad

```
PRUEBAS DE LA FASE 6     25 / 25
```

Cubren: creación en pendiente sin adivinar la cadena · el creador ve lo suyo · otro usuario de la
misma empresa no · otra cadena tampoco · el control autorizado sí · el control de otra empresa no
· el identificador no abre nada · el pendiente no aparece en el listado operativo · ver no es
decidir · el control clasifica · no se cruza la empresa · clasificar no concede ni habilita ·
rastro en `P-09` · el creador pierde su excepción · lo ve quien tiene la cadena · sigue denegado
a otra · el evento derivable no pasa por la bandeja · el nombre del rol no abre nada · clasificar
contra una unidad apagada se rechaza y no la enciende · la cola de revisión no muestra cadenas
ajenas.

## 4. Sensibilidad

| # | Mutación | Resultado | Cayeron |
|:--:|---|:--:|:--:|
| 1 | la bandeja muestra todo lo pendiente de la empresa | **RED** | 3 |
| 2 | el creador conserva su excepción tras clasificar | **RED** | 2 |
| 3 | adivinar la cadena en vez de reconocer el pendiente | **RED** | 1 |
| 4 | atajo por nombre de rol | **RED** | 1 |
| 5 | quitar el filtro de empresa de la bandeja | **RED** | 2 |
| 6 | clasificar concede la cadena al creador | **RED** | 2 |
| 7 | clasificar enciende la unidad apagada | **RED** | 1 |
| 8 | el pendiente entra en el listado operativo | **RED** | 1 |
| 9 | la cola de revisión vuelve a ser de toda la empresa | **RED** | 1 |

### 4.1 Dos sobrevivieron, y las dos eran culpa de mis pruebas

**La 7** usaba una habilitación **ya encendida**, de modo que un «enciéndela si hace falta» pasaba
inadvertido. Se añadió la prueba que clasifica contra una apagada y comprueba las dos cosas: que
se rechaza y que sigue apagada.

**La 9 pasaba en vacío.** `/api/v1/review/pending` devuelve `{"events": [...], "total": n}` y mi
aserción leía `items`, que no existe: comparaba contra un conjunto vacío y siempre acertaba. **Es
exactamente el mismo error de forma que la fase 4 cazó en el panel**, cometido otra vez. Corregida
la extracción, la mutación rompe.

```
MUTACIONES        9 / 9 detectadas (tras cubrir los dos huecos que ellas revelaron)
RESTAURACIÓN      los cuatro ficheros idénticos a su instantánea
```

## 5. Los lotes sin cadena quedan fuera, a propósito

Clasificar un lote significaría rellenar `bird_type`, que es **dato de dominio**, no configuración
de acceso. Hacerlo desde aquí mezclaría los dos ejes que `GA-REM-040 §2` existe para separar, y la
autoridad sobre ese campo es de los procesos de lote.

```
REGISTRADO COMO HUECO     completar la cadena de un lote existente es de `P-03`/`P-06`
ESTADO                    siguen denegados — lo que la fase 3 dejó, y sigue siendo lo seguro
```

## 6. Flujos 4 y 6

La fase 5 los aplazó explícitamente aquí. Resultado:

**Flujo 6 · revisión y aprobación — `IMPLEMENTADO`.** Tenía cuatro consultas propias sobre
`operational_events`, sin acotar. Una cola de revisión que muestre eventos de cadenas ajenas
revela su volumen y su ritmo aunque no se abra ninguno. Ahora las cuatro aplican el mismo
predicado, y hay prueba.

**Flujo 4 · transferencia entre granjas — `IMPLEMENTADO por construcción`.** `bird_movements`,
`egg_movements` y `feed_movements` **no tienen ninguna ruta propia**: viajan dentro del evento, y
los eventos quedaron acotados en esta fase. Su alcance no depende de una comprobación que alguien
pueda olvidar, sino de no existir como superficie independiente. Verificado enumerando las 200
rutas: cero coincidencias.

**Flujo 5 · consolidación SAP — sin tocar.** `BU-D04` sigue `PENDIENTE` y esta fase no la
resuelve ni la infiere.

```
FLUJOS IMPLEMENTADOS      6 / 7
EXCEPCIÓN DECLARADA       1 / 7     flujo 5 · BU-D04 PENDIENTE
```

**La fase 5 no pasa a `COMPLETE`.** Seis de siete están, y el séptimo depende de una decisión del
propietario que no es técnica. El estado honesto sigue siendo `PARTIAL`.

## 7. Las semillas ahora configuran la empresa

Diecinueve pruebas de notificaciones empezaron a fallar: sus sujetos son usuarios sembrados y no
tenían cadenas concedidas, de modo que desde esta fase no veían ni sus propios eventos.

Se resolvió **en las semillas**, no parcheando suite por suite: habilitan las cuatro cadenas a
cada empresa sembrada y se las conceden a sus usuarios. Es lo que hará un cliente real en su alta.

**No es un rodeo al control.** La alternativa —que la ausencia de concesión signifique acceso
total— es el `fail open` que toda esta capacidad existe para impedir. Las suites que **miden** el
aislamiento crean sus propios usuarios y conceden a mano.

## 8. Un acoplamiento que hubo que resolver en el modelo

La clave foránea nueva hacia `company_business_units` hacía fallar a cualquier suite que no
importara además ese módulo, y el fallo aparecía **lejos de su causa**. Se importa desde
`app/operations/models.py`, que es quien la referencia.

## 9. Regresión

```
BACKEND              623 passed · 49 skipped     (eran 621 · antes de la fase, 598)
FASE 5               verde · destino obligatorio, origen acotado, flujo validado
FASE 4               verde · el pendiente sigue sin contribuir a ningún agregado
FASE 3 · `R-111`     verdes
FASE 2 · FASE 1      verdes
P-10 · P-14 · P-07   verdes
INQUILINO · RBAC     verdes
MIGRACIÓN            cabeza única `s9t0u1v2w3x4` · `T-025` sin tablas nuevas
FRONTEND             0 archivos
```

## 10. Certificación

```
CERTIFICACIÓN FUNCIONAL              14 / 15   sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD    0 / 15   sin cambios
```

**Tener bandeja y acción de clasificar no certifica ningún proceso.** La unidad de certificación
sigue siendo el proceso completo, y ninguno tiene todavía todas sus superficies cubiertas: falta
la administración —fase 7—, la sesión —fase 8—, la interfaz —fase 9— y las notificaciones y
tareas de fondo —fase 10—.

## 11. Lo que queda sin decidir

```
RECLASIFICAR UN REGISTRO YA CLASIFICADO    SPEC DECISION REQUIRED
UN PERMISO PROPIO DE CLASIFICACIÓN         catálogo de `GA-REM-034` · fase 7
COMPLETAR LA CADENA DE UN LOTE EXISTENTE   `P-03`/`P-06`, no esta capa
BU-D04 · el analista de SAP                PENDIENTE · sin tocar
BU-D10 · retirar una unidad a una empresa  PENDIENTE DE RATIFICACIÓN · sin tocar
```

## 12. Siguiente

```
GA-REM-040 · FASE 7 — API DE ADMINISTRACIÓN     T-040-18 · T-040-19
NO INICIADA
```

---

# CIERRE DE LA FASE 6 (2026-09-07)

## 13. Una corrección de mi informe anterior

Informé **19** pruebas de notificaciones afectadas por la configuración de las semillas. El
número real, medido retirando las concesiones sembradas:

```
20 caen en total
   18  notificaciones      (9 + 9, no 19)
    2  auditoría y flujo completo
```

Esa misma medición **es** la sensibilidad que `§65` pedía: sin concesiones sembradas caen veinte
pruebas por la razón correcta —no hay acceso productivo sin concesión—, lo que demuestra que la
suite depende de configuración explícita y no de un retroceso escondido.

## 14. La semilla como precondición válida

```
UNA SEMILLA DE CERTIFICACIÓN VÁLIDA
    =  empresa con cadenas HABILITADAS explícitamente
    +  usuarios con cadenas CONCEDIDAS explícitamente
    +  RBAC  +  dato de negocio
```

Se resolvió **en la semilla compartida**, no con veinte parches locales: todas compartían la
misma precondición, y arreglarla veinte veces habría dejado veinte sitios donde olvidarla.

**Ninguna aserción se debilitó.** Lo que cambió fue el estado de partida: empresa configurada,
que es lo que hará un cliente real en su alta.

Y no todo el mundo recibe las cuatro: las suites que **miden** el aislamiento —`test_business_units`,
`test_lot_row_scope`, `test_kpi_scope`, `test_handoff_contract`, esta misma— siguen construyendo
sus propios sujetos de una cadena, de varias, de ninguna y de control.

```
sin concesiones  →  ninguna cadena productiva     y hay prueba que lo sujeta
```

## 15. Reclasificación controlada · `OD-10.d`

```
PRIMERA CLASIFICACIÓN   ≠   RECLASIFICACIÓN
```

| Regla | Cómo |
|---|---|
| la edición ordinaria no reclasifica | el campo no viaja en `OperationalEventUpdate`, que es `extra="forbid"` |
| permiso propio | `corrections:correct` — distinto del `masters:update` de la primera |
| motivo obligatorio | no vacío, no espacios; se guarda en `change_reason` |
| efectos aguas abajo | `409` **con la lista de cuáles**: una negativa sin motivo obliga a adivinar qué revertir |
| historia | `P-09`: cadena anterior, cadena nueva, actor, momento y motivo |
| sin cascada | los hijos no se reasignan en bloque |
| sin conceder ni habilitar | comprobado midiendo antes y después |
| no vuelve a «pendiente» | ni restaura la excepción de quien lo registró |

**El permiso es distinto a propósito.** Sacar un registro de «pendiente» y cambiar una atribución
que ya estaba puesta no son el mismo acto ni el mismo riesgo. `corrections:correct` es el permiso
que el catálogo ya reservaba para enmendar un registro.

### 15.1 Qué cuenta como efecto aguas abajo

Auditado sobre el dominio real, no inventado:

```
el registro está aprobado, consolidado, enviado a SAP o con error de SAP
participa en un traspaso de huevo o de pollito  (dispatch/reception)
tiene acciones de aprobación registradas
```

Ante la duda **se deniega**. Y la respuesta enumera los efectos encontrados, porque decir «no se
puede» sin decir qué hay que revertir no ayuda a nadie.

## 16. Sensibilidad del cierre

| # | Mutación | Resultado | Cayeron |
|:--:|---|:--:|:--:|
| 1 | sin concesiones → todas las cadenas | **RED** | 11 |
| 2 | la edición ordinaria acepta el campo | **RED** | 1 |
| 3 | el motivo puede ir en blanco | **RED** | 1 |
| 4 | ignorar los efectos aguas abajo | **RED** | 1 |
| 5 | no auditar la reclasificación | **RED** | 1 |
| 6 | reclasificar concede la cadena nueva | **RED** | 3 |
| 7 | reclasificar enciende la unidad apagada | **RED** | 1 |
| 8 | el permiso de reclasificar se ignora | **RED** | 1 |

### 16.1 Tres no salieron a la primera, y por razones distintas

**La 1 se corrió contra la suite equivocada.** Las pruebas de cero unidades viven en
`test_business_units`, `test_lot_row_scope` y `test_kpi_scope`, no en la de clasificación.
Repetida sobre ellas, cae once veces. Error mío de alcance, no de cobertura.

**La 6 era una mutación rota.** Llamaba a `conceder_unidad`, que no está importado en el ámbito
de ese módulo: lanzaba `NameError` y **mi propio `except Exception` lo tragaba**. Una mutación
que no ejecuta lo que dice ejecutar no demuestra nada. Rehecha con el import, cae tres veces.

**La 7 sí era un hueco de cobertura.** Las pruebas de reclasificación apuntaban siempre a una
habilitación encendida. Se añadió la que apunta a una apagada — y es **el mismo hueco que ya
había aparecido en la primera clasificación**, cometido otra vez en la operación hermana. Que se
repita en el par indica que conviene revisar estas dos operaciones juntas.

```
MUTACIONES        8 / 8 detectadas
RESTAURACIÓN      árbol limpio · patrones verificados uno a uno
```

## 17. Regresión del cierre

```
BACKEND                633 passed · 49 skipped     (eran 623)
P-14 · P-09 · P-10     verdes
FASE 5 · 4 · 3 · `R-111` · 2 · 1   verdes
INQUILINO · RBAC       verdes
MIGRACIÓN              ninguna nueva · FRONTEND 0
```

## 18. Estado de la fase 6

```
CLASIFICACIÓN PENDIENTE      READY
RECLASIFICACIÓN CONTROLADA   READY para `operational_events`
```

**Solo para `operational_events`.** Es la única entidad con clasificación propia; las seis
dependientes heredan y no tienen atribución que corregir. No se construye una API polimórfica de
reclasificación para entidades que no la necesitan.

## 19. Lo que sigue sin decidir

```
BU-D04 · el analista de SAP                PENDIENTE · sin tocar
BU-D10 · retirar una unidad a una empresa  PENDIENTE DE RATIFICACIÓN · sin tocar
UN PERMISO PROPIO DE CLASIFICACIÓN         catálogo de `GA-REM-034` · fase 7
COMPLETAR LA CADENA DE UN LOTE EXISTENTE   `P-03`/`P-06`, no esta capa
```
