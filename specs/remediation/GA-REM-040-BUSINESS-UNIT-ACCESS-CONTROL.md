# `GA-REM-040` · ACCESO POR UNIDAD DE NEGOCIO

| Campo | Valor |
|---|---|
| **ID** | `GA-REM-040` · `CROSS-CUTTING CAPABILITY SPEC` |
| **Prioridad** | **P0** · Estado **`SPEC_READY`** · **fases 1 a 7 construidas** (2026-09-08) |
| **Requisito** | habilitación de unidades por empresa y acotamiento por usuario |
| **Decisiones** | `OD-09` (`a`…`e`) · `OD-10` (`a`…`d`) · `OD-11` contexto · **`OD-12`** contrato SAP · marco `ENV-01` |
| **Antecedente** | `audit/remediation/MODULE_ACCESS_ARCHITECTURE_AUDIT.md` y sus 21 matrices |
| **Procesos** | los quince, en una **dimensión nueva**; ninguno se reabre |
| **Dependencias** | `GA-REM-002` `GA-REM-034` (`RBAC`) · `GA-REM-039` (`Area`, que **no** es esto) |
| **Bloquea** | la certificación de acceso por unidad de los quince procesos |
| **No resuelve** | `BU-D05` (alta del primer cliente real) · `OD-05` · `P-08` |

---

## 1. Terminología obligatoria

Tres palabras que el proyecto usaba como si fueran una. Esta spec las separa, y **un documento
que las vuelva a mezclar la incumple**.

```
MÓDULO RBAC          un dominio de autorización del software
                     operations · lots · masters · reports · users · sap …
                     EXISTE · certificado · no se toca aquí

UNIDAD DE NEGOCIO    una cadena productiva del negocio
                     Progenitoras · Reproductora · Incubadora · Engorde
                     NO EXISTE · es lo que esta spec introduce

ÁREA FUNCIONAL       el organigrama interno de la empresa (`GA-REM-039`)
                     EXISTE · pertenencia organizativa, no cadena productiva
```

Y cuatro desigualdades que la spec debe dejar inequívocas:

```
EMPRESA        ≠  UNIDAD DE NEGOCIO
MÓDULO RBAC    ≠  UNIDAD DE NEGOCIO
ROL            ≠  CONCESIÓN DE UNIDAD
ÁREA           ≠  UNIDAD DE NEGOCIO
```

## 2. Las cuatro unidades

Verificadas contra `backend/app/masters/models.py`:

| Unidad de negocio | Código de dominio | Certeza |
|---|---|---|
| Progenitoras | `grandparent` | correspondencia exacta |
| Reproductora | `breeder` | correspondencia exacta |
| Incubadora | `hatchery` | exacta; además `Lot.hatchery_purpose` |
| Pollo de engorde | `broiler` | correspondencia exacta |

**`BirdTypeEnum` sigue siendo clasificación de dominio y no se convierte en control de acceso.**
Describe qué es un lote; no dice quién puede verlo. La unidad de negocio es un concepto de
seguridad y configuración, distinto, que **puede relacionarse** con esos códigos —y `AC-A01`
exige decidir cómo— pero no se sustituye por ellos.

## 3. Por qué esconder el menú no es la respuesta

```
Apagar una unidad de negocio  ≠  apagar un módulo funcional
```

Apagar «Incubadora» para una empresa **no** apaga `operations`, `reports` ni `review`: siguen
existiendo para las unidades que sí tenga. Lo que cambia es **qué filas** ve.

Por eso esta capacidad no se resuelve ocultando pantallas. Se resuelve **filtrando datos**, en el
backend, donde nadie puede saltárselo escribiendo una URL.

---

## 4. La regla central

```
ACCESO OPERATIVO EFECTIVO
    =  usuario autenticado
   AND  misma empresa
   AND  unidad de negocio HABILITADA para la empresa
   AND  unidad de negocio CONCEDIDA al usuario
   AND  permiso RBAC válido
   AND  regla de negocio del recurso satisfecha
```

Las seis condiciones, todas. Quitar una es una de las mutaciones que las pruebas deben detectar.

Y una segunda regla, para las funciones de control:

```
VISIBILIDAD DE CONTROL EFECTIVA
    =  usuario autenticado
   AND  misma empresa
   AND  autorización de control CONCEDIDA EXPRESAMENTE
```

que alcanza **toda la empresa** y **nunca la cruza**.

```
VISIBILIDAD DE CONTROL  ≠  AUTORIDAD OPERATIVA
```

### 4.1 Prohibido el atajo por nombre de rol

```
PROHIBIDO   if "admin" in role.name:      saltar el filtro
PROHIBIDO   if "contralor" in role.name:  saltar el filtro
```

`GA-REM-034` permite crear roles, y el nombre es texto editable. Un rol llamado «Administrativo
de almacén» no puede heredar la visibilidad de la empresa por parecerse a otro. La
transversalidad se **configura o se deriva de un permiso real**, y se puede retirar.

### 4.2 La empresa manda sobre la concesión

```
unidad OFF para la empresa  +  concesión ON al usuario  =  DENEGAR
```

### 4.3 El super administrador

No obtiene acceso operativo entre empresas por esta capacidad. El modelo de inquilino vigente se
preserva íntegro.

---

## 5. El plano de control

Derivado de `CORE_VS_BUSINESS_MODULE_MATRIX.md`, no inventado. La pregunta que lo ordena es
**¿tiene sentido apagar esto para una empresa?**

| Capacidad | Clasificación | ¿Se filtra por unidad? |
|---|---|---|
| Autenticación, sesión, `/me` | `CORE` | no |
| Usuarios, roles, permisos | `CORE` | no |
| Empresas | `CORE` | no |
| Auditoría (`P-09`) | `CORE` | no filtra; **la visibilidad** sí se decide |
| Notificaciones (`P-14`) | `CORE` | el canal no; **qué avisa**, sí |
| Áreas funcionales (`GA-REM-039`) | `CORE` | no |
| Administración de unidades de negocio | `CORE` | no |
| Progenitoras · Reproductora · Incubadora · Engorde | `BUSINESS` | **sí** |
| Revisión y aprobación (`P-07`) | `MULTI-MODULE` | el flujo no; las filas sí |
| Consolidación SAP (`P-08`) | `MULTI-MODULE` | excepción declarada |
| Trazabilidad generacional (`P-10`) | `MULTI-MODULE` | **cruza por diseño** — contrato |
| Reportes y KPI (`P-15`) | `SHARED` | **sí, y hoy no lo hace** |
| Datos maestros | `SHARED` | parcialmente — `§12` |

**Administrar el acceso no es acceder al dato.** Un administrador puede asignar Incubadora a otro
usuario sin poder consultar ni modificar sus lotes, si no tiene la concesión operativa.

```
PROHIBIDO   if role == admin:  allow everything
```

El plano de control tiene **permisos propios**.

---

## 6. El modelo, en concepto

Esta spec define **semántica**, no esquema. La implementación debe empezar por una auditoría de
reutilización (`T-040-01`) antes de crear una sola tabla.

```
CATÁLOGO DE UNIDADES        código estable · identidad presentable e `i18n` · activa/de sistema
HABILITACIÓN POR EMPRESA    ¿está la unidad habilitada para esta empresa?
CONCESIÓN POR USUARIO       ¿le concedió ESTA EMPRESA a este usuario esa unidad?
                            usuario + empresa + unidad — nunca solo usuario + unidad
ACCESO EFECTIVO             la intersección, resuelta en un solo sitio
```

### 6.1 Auditar antes de crear

```
PROHIBIDO crear tablas sin antes revisar
    tablas existentes de características o habilitaciones
    configuración de empresa existente
    tablas existentes de alcance de usuario
```

Si ya existe capacidad correcta, se reutiliza. Duplicarla crearía dos fuentes que acabarán
discrepando — el mismo error que `GA-REM-039` evitó al no guardar el gerente en el área.

### 6.2 Contratado y habilitado

El alcance de esta spec es **habilitar y deshabilitar por empresa**. Separar «contratado» de
«habilitado» queda registrado como **extensión futura** (`BU-D08`), no se construye ahora.

### 6.3 Retirar una unidad

Reglas fijadas por el propietario al autorizar esta spec; `BU-D10` sigue pendiente de
formalizarse como `OD`, y si se formaliza distinto lo que cambia son estos criterios, no el
diseño:

```
DESHABILITAR UNIDAD    ≠  BORRAR DATO          el histórico permanece
DESHABILITAR UNIDAD    ≠  BORRAR CONCESIONES   se conservan
REHABILITAR            →  la concesión previa vuelve a ser efectiva
REVOCAR AL USUARIO     ≠  BORRAR LO QUE CREÓ
REVOCAR AL USUARIO     →  efecto inmediato
```

### 6.4 Revocación inmediata

La autorización se lee de la base en cada petición, y por eso hoy la revocación es inmediata. Las
concesiones de unidad **no** pueden vivir solo en el `JWT` sin invalidación: eso convertiría una
revocación en algo que tarda lo que dure el token.

---

## 7. Dónde vive el filtro

### 7.1 No solo en las rutas

```
routers · servicios · repositorios · tareas de fondo
reportes · exportaciones · notificaciones · llamadas internas
```

Los servicios se invocan también desde tareas de fondo, que no tienen sesión: la comprobación de
**empresa y unidad** puede vivir en el servicio; la de **usuario**, solo donde hay sesión.

### 7.2 Un solo sitio

```
resolver_unidades_efectivas(...)
exigir_acceso_a_unidad(...)
```

o el equivalente que la arquitectura imponga. **No** repetir `if business_unit …` en 198 rutas:
sería la misma dispersión que hoy tiene el filtro de empresa —`MasterService` lo aplica, los
demás lo repiten a mano—, y merece la pena centralizar los dos a la vez.

### 7.3 Toda ruta queda clasificada

```
CORE · UNIDAD ÚNICA · MULTI-UNIDAD · CONTRATO ENTRE UNIDADES · PLANO DE CONTROL
```

La guarda de arranque que ya impide una ruta sin permiso declarado se extiende para impedir una
**ruta operativa sin clasificación**. Las rutas `CORE` se clasifican explícitamente como tales:
no se tratan como si fueran públicas.

### 7.4 Lo desconocido deniega

```
alcance no resuelto  →  DENEGAR
```

Nunca se retrocede a «toda la empresa» como valor por defecto.

---

## 8. Aislamiento por fila

**`company_id` no basta.** Es el hallazgo central de la auditoría: hoy `GET /lots` devuelve filas
de varias unidades dentro de la misma empresa.

```
misma empresa  +  alcance de unidad efectivo   o   contrato entre unidades
```

Y no basta con los listados:

```
listado · detalle · modificación · baja · acciones de flujo
búsqueda · autocompletado · desplegables de opciones
```

Un desplegable que ofrece un lote ajeno lo revela igual que un listado, y suele ser lo último que
alguien revisa.

---

## 9. Los agregados

```
PROHIBIDA LA FUGA POR AGREGADO
```

Un usuario restringido **no puede deducir** dato ajeno mediante:

```
contador · suma · promedio · ratio · KPI · panel · reporte · exportación
```

Un total calculado sobre filas que no puede ver no le enseña la fila: le enseña que existe y
cuánto pesa. **Es la única fuga que no deja rastro y que nadie reporta**, y por eso los agregados
son una fase temprana y no la última.

Alcance obligatorio: `CSV`, `XLSX`, `PDF`, analítica, reportes y exportaciones.

Los quince `KPI` de `P-15` conservan su certificación funcional y adquieren una prueba nueva de
alcance por unidad.

---

## 10. Los contratos entre unidades

Los siete flujos, enumerados literalmente de `CROSS_MODULE_FLOW_MATRIX.md`:

| # | Origen → Destino | Entidad puente |
|:--:|---|---|
| 1 | Progenitoras → Reproductoras | `egg_batches` |
| 2 | Reproductoras → Incubadora | `egg_batches` · `egg_dispatch` / `egg_reception_hatchery` |
| 3 | Incubadora → Engorde | `chick_batches` · `chick_dispatch` / `bird_reception` |
| 4 | Transferencia de aves entre granjas | `bird_movements` |
| 5 | Consolidación a SAP | `consolidated_movements` |
| 6 | Revisión y aprobación | `operational_events` |
| 7 | Trazabilidad generacional | `egg_batches` + `chick_batches` |

### 10.1 Las cuatro categorías

Para cada flujo, cada campo se clasifica en una y solo una:

```
A · PROPIO           dato de las unidades concedidas. Operación completa según RBAC.
B · TRASPASO         la fila puente y lo mínimo del lote de enfrente para actuar.
                     Solo lectura, ambos lados, solo en el contexto del traspaso.
C · INTERNO AJENO    todo lo demás del otro lado. DENEGADO.
D · AGREGADO         se calcula sobre A ∪ B. NUNCA sobre C.
```

Participar en un traspaso **no concede** acceso general a la unidad de enfrente.

### 10.2 Las entidades de traspaso conservan sus dos lados

```
egg_batches      source_lot_id   →  hatchery_lot_id
chick_batches    hatchery_lot_id →  destination_lot_id
```

**La fila es el traspaso.** No se les impone propiedad única y **no se les añade columna de
unidad** para forzarla: sus dos lados ya dicen a quién alcanza cada una.

### 10.3 El destino del despacho

```
EL DESTINO SE DECLARA AL CREAR EL DESPACHO      (OD-10.b)
```

La unidad destino ve **los traspasos dirigidos a ella** antes de recibirlos, y **no** todos los
despachos pendientes de la empresa.

**La columna no se decide en esta spec.** `T-040-14` debe auditar el modelo real
—`destination_farm_id`, `destination_plant_id`, la granja, la incubadora, el lote destino— y
determinar qué combinación existente satisface el contrato. Puede que el dato ya exista y solo
falte hacerlo obligatorio para este flujo.

```
PROHIBIDO   crear `destination_business_unit_id` por defecto, sin esa auditoría
```

**Hueco declarado.** Ninguna fuente dice si el destino puede cambiarse después de crear el
despacho. `SPEC DECISION REQUIRED` antes de implementar ese comportamiento: no se inventa edición
libre.

### 10.4 Anulación y reversión

El producto ya distingue `RETURNED`, `CORRECTED`, `REJECTED` y permite anular. Un traspaso
anulado sigue el contrato: el lado que lo veía **lo ve desaparecer con su motivo**, no evaporarse.

### 10.5 `P-10` se conserva

La **cadena** —qué lote vino de qué lote, con fechas y cantidades— es categoría `B` y se ve
entera. El **interior** de cada eslabón queda en `C`. Es la diferencia entre saber de dónde viene
y saber cómo le fue, y es lo que permite conservar la trazabilidad certificada sin abrir el
producto.

---

## 11. La clasificación pendiente

```
DATO NO CLASIFICABLE  =  PENDIENTE DE CLASIFICAR      (OD-10.c)
NO ADIVINAR · NO ABRIR · NO BORRAR · NO OCULTAR PARA SIEMPRE
```

El caso real y permanente: `operational_events.lot_id` es nulable **a propósito**, y las
inspecciones de granja se registran sin lote desde `i9j0k1l2m3n4`. No es legado: seguirá pasando.

### 11.1 Quién lo ve mientras está pendiente

```
SÍ     quien lo creó o registró
       la administración o el control de la empresa expresamente autorizados
NO     todos los usuarios de la empresa · todos los de una unidad
```

### 11.2 No es una quinta unidad

```
PROHIBIDO   crear una unidad falsa «SIN ASIGNAR»
```

Es un **estado de clasificación**. Las unidades productivas son cuatro.

### 11.3 El recorrido

```
SIN CLASIFICAR → PENDIENTE → clasificación autorizada → unidad o contrato → reglas normales
```

### 11.4 Explícita y auditada

No se auto-asigna por rol, por creador, por nombre de granja, por URL ni por conjetura, salvo
reglas deterministas ya certificadas. Y deja rastro en **`P-09`**, no en una auditoría paralela:

```
quién clasificó · cuándo · estado anterior · nueva clasificación · motivo u origen
```

### 11.5 Medible

Los pendientes deben poder **contarse, revisarse, clasificarse y auditarse**. Hoy nadie sabe
cuánto habría, porque no hay dónde mirarlo.

### 11.6 Reclasificar

Si un registro ya clasificado puede reclasificarse es **`SPEC DECISION REQUIRED`**. Preferencia:
operación de alto control, auditada. No se inventa si aparece norma.

---

## 12. Los datos maestros

`MASTER_DATA_MODULE_MATRIX.md` ya clasificó los veintidós. La spec los adopta y **no los
reclasifica pantalla por pantalla**:

```
CORE DE EMPRESA        companies · areas
GLOBAL DE PRODUCTO     productive_phases
COMPARTIDOS            farms · houses · genetic_lines · genetic_weight_curves · feed_types
                       vaccines · medications · mortality_causes · cull_causes · transports
                       rejection_reasons · correction_types · suppliers
DE UNA UNIDAD          hatcheries · incubators · hatchers      (Incubadora)
                       processing_plants                        (Engorde)
CON UNIDAD EXPLÍCITA   breeds  — el único maestro que ya lleva `bird_type`
MULTI-UNIDAD           sap_references
```

`farms` y `houses` son el caso delicado: **una granja puede alojar varias unidades**, de modo que
no se le asigna una.

```
PROHIBIDO   duplicar un maestro por unidad cuando el dato es realmente compartido
```

---

## 13. Auditoría, notificaciones y tareas de fondo

### 13.1 `P-09`

Se audita con el mecanismo existente, no con uno paralelo:

```
unidad habilitada a una empresa · unidad deshabilitada
concesión otorgada a un usuario · concesión revocada
registro clasificado · reclasificado, si se permite
```

La visibilidad transversal del historial para las funciones de control se conserva (`OD-09.a`).
La concesión operativa **no** se usa para destruir la función de control.

### 13.2 `P-14`

`P-14` conserva su certificación funcional y **no se reabre**. La dimensión nueva distingue:

```
DESTINATARIO OPERATIVO     recibe por su vínculo con el dato
                           → debe tener acceso efectivo a la unidad del evento,
                             salvo contrato entre unidades explícito

DESTINATARIO DE CONTROL    recibe por su función sobre la EMPRESA
                           → toda la empresa, sin filtrar por concesión de unidad
                             (`OD-08` · `OD-09.a`)
```

```
PROHIBIDO   filtrar en silencio los avisos de administración y contraloría
            por concesión de unidad
```

Sería incumplir `OD-08` sin que ninguna prueba lo detectara. **Recibir un aviso entera; no
autoriza.**

### 13.3 Tareas de fondo

Deben conocer la unidad. Si una unidad está deshabilitada para la empresa, una tarea operativa de
esa unidad **no produce efectos operativos**, salvo norma que diga otra cosa.

No se confunde con mantenimiento —retención de auditoría, limpieza del sistema—, que sigue
funcionando.

---

## 14. Sesión e interfaz

### 14.1 Lo que la sesión debe entregar

```
unidades habilitadas de la empresa
concesiones del usuario
unidades efectivas
capacidades del plano de control
```

o el equivalente que imponga la arquitectura. Hoy la sesión no lo entrega, y por eso el frontend
no tiene con qué decidir.

### 14.2 El frontend no es la autoridad

```
FRONTEND   visibilidad y experiencia
BACKEND    seguridad
```

Esa información sirve para menús, navegación y rutas. **El backend vuelve a validar siempre.**

```
MENÚ OCULTO  ≠  DATO SEGURO
```

### 14.3 Navegación

```
unidad OFF para la empresa                    → oculta
unidad ON, usuario sin concesión              → oculta
unidad ON, usuario con concesión              → visible
```

salvo `CORE` y plano de control, que dependen del rol.

### 14.4 Las dos pantallas de administración

```
EMPRESA  →  UNIDADES DE NEGOCIO     habilitar y deshabilitar
USUARIO  →  UNIDADES DE NEGOCIO     conceder, entre las habilitadas de su empresa
```

No se puede conceder operativamente una unidad **que la empresa no tiene habilitada**.

### 14.5 El usuario sin unidades

```
entra · usa `CORE` según su rol · no ve ni opera dato productivo   (OD-09.c)
```

```
PROHIBIDO   401 · «usuario inválido» · «cuenta deshabilitada»
PROHIBIDO   sin unidad → devolver todo el dato de la empresa
```

Y la pantalla debe **decirlo**: un panel vacío es indistinguible de una empresa sin producción.
Con `i18n`, en las dos lenguas.

---

## 15. Legado y entorno

`ENV-01` establece que no hay producción real desplegada y que los datos y usuarios actuales son
de prueba y certificación.

```
NO gastar esta implementación en migrar una producción que no existe
SÍ dejar los ganchos para el alta del primer cliente real
```

Las fixtures actuales pueden reiniciarse o clasificarse según las políticas vigentes; no se
tratan como dato de producción.

`BU-D05` queda como **gate separado** —`FIRST_REAL_CUSTOMER_READINESS`— y no bloquea esta spec ni
su implementación.

---

## 16. Los seis principios

Se escriben porque cada uno corresponde a un error que esta auditoría encontró cometido o a punto
de cometerse:

```
1   MISMA EMPRESA               no implica   MISMO ACCESO A UNIDAD
2   MENÚ OCULTO                 no implica   DATO SEGURO
3   ROL                         no implica   CONCESIÓN DE UNIDAD
4   VISIBILIDAD DE CONTROL      no implica   AUTORIDAD OPERATIVA
5   VISIBILIDAD DE TRASPASO     no implica   ACCESO A LA UNIDAD AJENA
6   SIN CLASIFICAR              no implica   VISIBLE PARA TODA LA EMPRESA
```

---

## 17. Criterios de aceptación

### Grupo `A` · catálogo y empresa

**`AC-A01`** · Las cuatro unidades existen como catálogo de plataforma, con código estable e
identidad presentable por `i18n`. Se decide y se documenta su relación con `BirdTypeEnum`, **sin
convertir el enum en control de acceso**.
**`AC-A02`** · La habilitación por empresa se persiste y se consulta.
**`AC-A03`** · Una empresa puede habilitar y deshabilitar las unidades permitidas.
**`AC-A04`** · Deshabilitar **no** borra dato de negocio ni concesiones de usuario.
**`AC-A05`** · Una unidad deshabilitada es operativamente inaccesible, aunque haya concesión.
**`AC-A06`** · Rehabilitar devuelve efectividad a las concesiones previas.
**`AC-A07`** · El aislamiento por empresa se preserva: nada de esto cruza inquilinos.

### Grupo `B` · acceso del usuario

**`AC-B01`** · A un usuario se le puede conceder un subconjunto de las unidades de su empresa.
**`AC-B02`** · No puede acceder efectivamente a una unidad que su empresa no tiene habilitada.
**`AC-B03`** · Un usuario sin ninguna unidad **puede autenticarse**.
**`AC-B04`** · Y no ve ni opera dato productivo, sin retroceso a «toda la empresa».
**`AC-B05`** · Conceder y revocar surten efecto **inmediato**, sin esperar a que caduque un token.
**`AC-B06`** · La concesión de unidad **no sustituye** al `RBAC`: hacen falta las dos.

**`AC-B07`** · **`OD-09.d` · enmienda A.** Una concesión pertenece a **usuario + empresa +
unidad**. La base puede decir, sin ambigüedad y sin mirar la empresa actual del usuario, **bajo
qué empresa se otorgó**.

**`AC-B08`** · Mover un usuario de empresa **no transfiere** sus concesiones. Las anteriores
quedan como historia y dejan de ser efectivas; en la nueva empresa no tiene ninguna hasta que
se le conceda explícitamente.

**`AC-B09`** · El mismo código de unidad en dos empresas son **dos contextos de autorización
distintos**. Una concesión otorgada por la empresa A **nunca** satisface a la empresa B, por
mucho que ambas tengan esa unidad habilitada.

**`AC-B10`** · Crear una concesión que cruce empresas —usuario de A sobre la habilitación de
B— se **rechaza** en el límite de servicio, y no queda escrita.

**`AC-B11`** · Cambiar de empresa **no borra** las concesiones anteriores: quedan registradas e
inefectivas.

**`AC-B12`** · **`OD-09.e` · enmienda B.** Volver a una empresa anterior **no reactiva** la
concesión que se tuvo allí. Sigue siendo historia inefectiva hasta que se otorgue una nueva y
explícita.

### Grupo `C` · seguridad de backend

**`AC-C01`** · Existe un resolutor central de acceso efectivo; no se repite la comprobación en
cada ruta.
**`AC-C02`** · Toda ruta operativa está clasificada, y la guarda de arranque **falla** si aparece
una sin clasificar. Las `CORE` se clasifican explícitamente.
**`AC-C03`** · Los listados devuelven solo filas autorizadas.
**`AC-C04`** · El detalle de una fila ajena de la misma empresa se deniega.
**`AC-C05`** · Las mutaciones sobre unidad no concedida se deniegan.
**`AC-C06`** · Una operación denegada **no produce efecto lateral alguno**.
**`AC-C07`** · Servicios, repositorios y llamadas internas quedan cubiertos, no solo los routers.
**`AC-C08`** · Alcance no resuelto **deniega**. Nunca abre.

**`AC-C09`** · **`OD-11.a`.** Para un usuario normal la empresa efectiva es la **persistida**.

**`AC-C10`** · Una reclamación de empresa en el token que no coincida con la persistida **se
ignora** para un usuario normal. No desplaza el inquilino.

**`AC-C11`** · **`OD-11.b`.** Un contexto de empresa desplazado solo se honra si el actor está
autorizado a cambiarla, y la empresa de destino **existe y está activa**.

**`AC-C12`** · Esas tres condiciones se comprueban **en cada petición**, no solo al emitir el
token: una empresa puede desactivarse con la sesión viva.

**`AC-C13`** · **`OD-11.c`.** Sin empresa persistida y sin contexto válido **no hay empresa
efectiva**, y el acceso productivo se deniega. No se resuelve «todas las empresas».

**`AC-C14`** · Cambiar de empresa con éxito **no concede** ninguna unidad de negocio ni ningún
permiso `RBAC`. Las unidades efectivas se resuelven aparte.

**`AC-C15`** · Toda ruta autenticada está **clasificada** por su relación con la unidad de
negocio, y la guarda de arranque **falla** si alguna no lo está.

**`AC-C16`** · La guarda de unidad es invocable desde una ruta, un servicio o una tarea, y no
depende de `Request`.

### Grupo `D` · agregados

**`AC-D01`** · Los contadores cuentan solo lo autorizado.
**`AC-D02`** · Los `KPI` se calculan solo sobre lo autorizado.
**`AC-D03`** · Los paneles, ídem.
**`AC-D04`** · Los reportes, ídem.
**`AC-D05`** · Las exportaciones —`CSV`, `XLSX`, `PDF`—, ídem.
**`AC-D06`** · Buscadores, autocompletados y desplegables, ídem.

### Grupo `E` · contrato entre unidades

**`AC-E01`** · Los siete flujos están documentados, con su entidad puente.
**`AC-E02`** · Cada campo de cada flujo está clasificado en `A`, `B`, `C` o `D`.
**`AC-E03`** · El destino del despacho se declara **al crearlo**, en el flujo que lo requiere.
**`AC-E04`** · La unidad destino ve **solo** los traspasos dirigidos a ella.
**`AC-E05`** · Ningún lado obtiene dato general de la unidad del otro.
**`AC-E06`** · Ningún lado obtiene agregados de la unidad del otro.
**`AC-E07`** · Anulación y reversión obedecen el contrato: se ve desaparecer con su motivo.
**`AC-E08`** · `P-10` sigue reconstruyendo la cadena completa bajo aislamiento.

### Grupo `E` bis · la transversalidad SAP · `OD-12`

**`AC-SAP01`** · Operar el contrato SAP exige una **capacidad SAP explícita** del catálogo
`RBAC`. Sin ella se deniega, por muchas cadenas que se tengan concedidas.

**`AC-SAP02`** · Solo alcanza recursos de la **misma empresa**. Nunca otra, por mucho que
coincidan la cadena, el código de lote o la referencia.

**`AC-SAP03`** · Con esa capacidad, el actor opera el contrato sobre registros de las **cuatro**
cadenas de su empresa.

**`AC-SAP04`** · Y lo hace **sin** tener concedidas esas cadenas: la capacidad no se sustituye
por concesiones ordinarias.

**`AC-SAP05`** · Operar el contrato **no crea** ninguna concesión de unidad.

**`AC-SAP06`** · **No habilita** ninguna unidad a la empresa.

**`AC-SAP07`** · El mismo actor, en las superficies **normales**, sigue acotado por sus unidades
efectivas. Conocer un identificador por el contrato SAP no abre su detalle.

**`AC-SAP08`** · La respuesta del contrato es una **proyección** declarada, no la entidad
completa del otro lado.

**`AC-SAP09`** · Ningún dato operativo interno ajeno viaja en ella.

**`AC-SAP10`** · La elegibilidad de negocio para SAP se conserva intacta: la capacidad autoriza
a **quién**, no a **qué**.

**`AC-SAP11`** · Una operación denegada no produce mutación, ni transición de estado, ni llamada
al límite externo, ni asiento de auditoría de éxito.

**`AC-SAP12`** · No hay atajo por nombre de rol. Se demuestra con un actor cuyo rol se llama
«Analista SAP» y **carece** del permiso.

### Grupo `F` · plano de control

**`AC-F01`** · La visibilidad de control puede alcanzar toda la empresa, para quien la tenga
concedida.
**`AC-F02`** · Y **no** concede autoridad operativa: operar sigue exigiendo unidad y `RBAC`.
**`AC-F03`** · La administración puede gestionar el acceso de toda su empresa.
**`AC-F04`** · Y **no** obtiene por ello acceso productivo implícito.
**`AC-F05`** · No existe atajo por nombre de rol. Se demuestra creando un rol cuyo nombre
contenga «admin» y comprobando que **no** atraviesa nada.

### Grupo `G` · clasificación

**`AC-G01`** · El dato no clasificable entra en pendiente de clasificar.
**`AC-G02`** · Quien lo creó conserva visibilidad limitada sobre él.
**`AC-G03`** · La administración o el control autorizados lo ven.
**`AC-G04`** · Los usuarios productivos normales **no**.
**`AC-G05`** · La clasificación se audita en `P-09`, con quién, cuándo, desde qué y hacia qué.
**`AC-G06`** · Tras clasificar, rigen las reglas normales de la unidad.
**`AC-G07`** · Nada queda abierto en silencio, y los pendientes se pueden contar.
**`AC-G08`** · «Pendiente» **no** es una quinta unidad de negocio.

**`AC-G09`** · **`OD-10.d`.** La edición ordinaria de un registro **no puede** cambiar su cadena
productiva. El campo no viaja en el contrato de edición.

**`AC-G10`** · Reclasificar exige **permiso explícito** y **motivo no vacío**. Sin cualquiera de
los dos se deniega y no queda escrito nada.

**`AC-G11`** · Un registro con **efectos productivos aguas abajo** —aprobado, consolidado o
enviado a SAP, participante en un traspaso, o con acciones de aprobación— **no** se reclasifica
en el sitio. Y si no se puede demostrar que no los tiene, tampoco.

**`AC-G12`** · La reclasificación deja rastro en `P-09` con actor, momento, cadena anterior,
cadena nueva y motivo. La historia anterior **se conserva**.

**`AC-G13`** · Reclasificar **no** concede la cadena a nadie, **no** habilita la unidad a la
empresa y **no** reasigna a los hijos en cascada.

**`AC-G14`** · Después de reclasificar manda el alcance normal: quien tenía la cadena anterior
deja de ver el registro, y quien tiene la nueva lo ve si su `RBAC` lo permite.

### Grupo `H` · interfaz

**`AC-H01`** · La sesión expone unidades habilitadas, concedidas, efectivas y capacidades de
control.
**`AC-H02`** · El menú se filtra en consecuencia.
**`AC-H03`** · Las rutas directas se protegen en el cliente **y** el backend sigue denegando.
**`AC-H04`** · Existe la pantalla de unidades por empresa.
**`AC-H05`** · Existe la de unidades por usuario, y solo ofrece las habilitadas de su empresa.
**`AC-H06`** · El usuario sin unidades ve un estado explícito, distinguible de «no hay producción».
**`AC-H07`** · La bandeja de clasificación existe si el diseño la requiere.
**`AC-H08`** · `i18n` en las dos lenguas, con paridad de claves.
**`AC-H09`** · Responsive, con el patrón existente.
**`AC-H10`** · El backend sigue siendo la autoridad: se demuestra llamando a la API directamente.

### Grupo `I` · `P-14`, `P-09` y tareas

**`AC-I01`** · Las notificaciones operativas respetan el acceso a la unidad.
**`AC-I02`** · Las de control de empresa se **preservan**: `OD-08` sigue cumpliéndose.
**`AC-I03`** · Los cambios de habilitación y concesión se auditan.
**`AC-I04`** · La clasificación se audita.
**`AC-I05`** · Las tareas operativas respetan el estado de la unidad en la empresa.

**`AC-I06`** · **`OD-11 §6`.** El cambio de contexto de empresa deja rastro en `P-09`: quién,
desde qué contexto, hacia qué empresa y cuándo.

### Grupo `J` · certificación

**`AC-J01`** · Caso positivo: unidad `ON`, concesión `ON`, permiso `ON` → funciona.
**`AC-J02`** · Empresa `OFF` con concesión histórica `ON` → **denegar**.
**`AC-J03`** · Unidad `ON` sin concesión → **denegar**.
**`AC-J04`** · Otra empresa → **denegar**.
**`AC-J05`** · Misma empresa, unidad ajena → **denegar**.
**`AC-J06`** · Contrato entre unidades: solo dato de contrato.
**`AC-J07`** · Agregado ajeno → **denegar**.
**`AC-J08`** · Usuario sin unidades: comportamiento de `AC-B03` y `AC-B04`.
**`AC-J09`** · Sensibilidad: cada mutación de `§19` rompe al menos una prueba.
**`AC-J10`** · La matriz de acceso por proceso está completa para los quince.

---

## 18. Los cinco casos de certificación

Por proceso aplicable:

```
CASO 1   unidad ON · concesión ON · permiso ON      →  el proceso funciona
CASO 2   unidad OFF · concesión histórica ON        →  DENEGAR
CASO 3   unidad ON · sin concesión · permiso ON     →  DENEGAR
CASO 4   otra empresa                                →  DENEGAR
CASO 5   traspaso entre unidades                     →  solo dato de contrato
```

Y en toda denegación:

```
0 mutación en base · 0 movimiento de inventario · 0 cambio de saldo
0 transición de flujo · 0 notificación con efecto · 0 envío a SAP
0 asiento de auditoría de éxito
```

Denegar **después** de haber escrito no es denegar.

---

## 19. Las mutaciones que deben romper una prueba

`GA-REM-016 AC13`: toda prueba invocada como evidencia debe ser demostrablemente capaz de fallar.

```
quitar la comprobación de habilitación por empresa
quitar la comprobación de concesión por usuario
quitar el filtro por fila
quitar el filtro del contrato entre unidades
quitar el filtro de los agregados
permitir que sin unidad se devuelva toda la empresa
quitar el filtro de inquilino
quitar la restricción de la clasificación pendiente
permitir el atajo global por nombre de rol
```

Nueve mutaciones, nueve roturas. Ninguna aserción vacua.

---

## 20. Trazabilidad

| Decisión | `AC` |
|---|---|
| `OD-09.a` visibilidad de control | `AC-F01` `AC-F02` `AC-F05` `AC-I02` |
| `OD-09.b` plano de control | `AC-F03` `AC-F04` `AC-A03` `AC-H04` `AC-H05` |
| `OD-09.c` usuario sin unidades | `AC-B03` `AC-B04` `AC-H06` `AC-J08` |
| `OD-10.a` contrato de traspaso | `AC-E01` `AC-E02` `AC-E05` `AC-E06` `AC-E08` `AC-D0*` |
| `OD-10.b` destino del despacho | `AC-E03` `AC-E04` |
| `OD-10.c` clasificación pendiente | grupo `G` completo · `AC-I04` |
| `ENV-01` | `§15` — sin migración productiva |

```
DECISIÓN DEL PROPIETARIO  →  AC  →  TAREA  →  PRUEBA FUTURA  →  EVIDENCIA FUTURA
```

## 21. Tareas

| Tarea | Qué hace |
|---|---|
| `T-040-01` | Auditar reutilización: ¿existe ya modelo de habilitación o de alcance de usuario? |
| `T-040-02` | Catálogo de unidades y su relación con `BirdTypeEnum`, decidida y escrita |
| `T-040-03` | Persistencia de habilitación por empresa |
| `T-040-04` | Persistencia de concesión por usuario |
| `T-040-05` | Resolutor central de acceso efectivo |
| `T-040-06` | Clasificar las 198 rutas · sin aplicar todavía |
| `T-040-07` | Extender la guarda de arranque a la clasificación de rutas |
| `T-040-08` | Guarda central en la capa de consultas: empresa **y** unidad a la vez |
| `T-040-09` | Filtro por fila en listados, detalle y mutaciones |
| `T-040-10` | Buscadores, autocompletados y desplegables |
| `T-040-11` | Agregados, contadores y `KPI` |
| `T-040-12` | Paneles, reportes y exportaciones |
| `T-040-13` | Clasificar campo por campo los siete contratos |
| `T-040-14` | **Auditar el modelo de destino** antes de proponer ninguna columna |
| `T-040-15` | Contrato de despacho con destino declarado |
| `T-040-16` | Estado de clasificación pendiente y su bandeja |
| `T-040-17` | Acción de clasificar, auditada en `P-09` |
| `T-040-35` | **`OD-10.d`** · reclasificación controlada, con efectos aguas abajo como barrera |
| `T-040-36` | Semillas de certificación: empresa configurada explícitamente |
| `T-040-37` | **`OD-12`** · política tipada del contrato SAP · flujo 5 · cierre de la fase 5 |
| `T-040-18` | API de administración: habilitación por empresa |
| `T-040-19` | API de administración: concesión por usuario |
| `T-040-20` | Capacidades en la sesión |
| `T-040-21` | Interfaz de unidades por empresa |
| `T-040-22` | Interfaz de unidades por usuario |
| `T-040-23` | Menú, rutas y estado sin unidades |
| `T-040-24` | Interfaz de clasificación pendiente |
| `T-040-25` | Notificaciones: operativo frente a control |
| `T-040-26` | Tareas de fondo conscientes de la unidad |
| `T-040-27` | Auditoría de habilitación, concesión y clasificación |
| `T-040-28` | Pruebas de seguridad `E2E` de los cinco casos |
| `T-040-29` | `E2E` de los siete contratos de traspaso |
| `T-040-30` | Mutaciones de sensibilidad y `PROCESS_BUSINESS_UNIT_ACCESS_MATRIX.md` |
| `T-040-31` | **Enmienda A** · acotar la concesión a la empresa que la otorgó · fase 1.1 |
| `T-040-32` | **Enmienda B** · empresa efectiva central y validada en cada petición · fase 2 |
| `T-040-33` | **Enmienda B** · volver a una empresa no reactiva la concesión · fase 2 |
| `T-040-34` | **Enmienda B** · auditar el cambio de contexto de empresa en `P-09` · fase 2 |

## 22. Hoja de ruta

```
FASE  1   fundamento          catálogo · habilitación · concesión · resolutor       T-040-01…05
FASE  2   seguridad central   clasificación de rutas · guarda · fail closed         T-040-06…08
FASE  3   filtro por fila     lotes y listas compartidas · detalle · buscadores     T-040-09…10
FASE  4   agregados           contadores · KPI · paneles · reportes · exportación   T-040-11…12
FASE  5   contratos           los siete flujos · destino del despacho               T-040-13…15
FASE  6   clasificación       estado · bandeja · acción · auditoría                 T-040-16…17
FASE  7   API de administración  ✔  habilitación · concesión · P-09       T-040-18…19
FASE  8   sesión               ✔  cuatro conceptos · empresa efectiva · actor global   T-040-20
FASE  9   interfaz                                                                  T-040-21…24
FASE 10   notificaciones, tareas y auditoría                                        T-040-25…27
FASE 11   certificación de acceso por unidad                                        T-040-28…30
```

**Dos puntos del orden no son negociables.** La fase 2 va antes que la 3 —filtrar filas sin
clasificar rutas deja huecos silenciosos—, y **la fase 4 no puede ir al final**: una fuga por
diferencia no deja rastro y nadie la reporta.

### Sin big bang

```
GA-REM-040 no exige modificar 198 rutas en un solo commit
```

Se clasifica primero **todo**, y después se aplica por lotes verificables, en orden de riesgo:
`P0` antes que `P1`, y así. Cada lote deja el árbol verde.

---

## 23. Certificación: la segunda dimensión

Los catorce procesos certificados **no se tocan**. Cuando se certificaron, este requisito no
existía; rebajarlos ahora sería reescribir la historia.

```
CERTIFICACIÓN FUNCIONAL                14 / 15    sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD      0 / 15    dimensión nueva
```

Un proceso queda **plenamente certificado** cuando pasa las dos. La matriz vive en documento
aparte —`audit/remediation/PROCESS_BUSINESS_UNIT_ACCESS_MATRIX.md`— y sus quince filas nacen en
`PENDIENTE`.

```
21/60 sigue siendo HISTÓRICO y no se recalcula.
```

## 24. Fuera de alcance

- **La migración de un cliente real.** `BU-D05`, gate `FIRST_REAL_CUSTOMER_READINESS`.
- **Separar contratado de habilitado.** `BU-D08`, extensión futura.
- **Resolver `OD-05`.** Quién puede conceder qué permiso sigue abierto; esta spec exige
  **permiso**, no rol codificado, precisamente para no prejuzgarlo.
- **`P-08` y el contrato SAP.** `BLOCKED_EXTERNAL`, intacto.
- **`R-98` y `R-99`.** Esta spec **aporta infraestructura** que `R-98` necesitará; eso **no** lo
  cierra. Se registra la dependencia y nada más.
- **Convertir `BirdTypeEnum` en `ACL`.**
- **Relacionar área con unidad.** Solo si el dominio lo exige, y documentado. Nunca inferido:
  «Área Producción» **no** es «Reproductora».
- **Duplicar maestros por unidad** cuando el dato es compartido.

## 25. Definición de terminado

- Los grupos `A` a `J` pasan.
- Las nueve mutaciones de `§19` rompen al menos una prueba cada una.
- Los cinco casos de `§18` están probados en los quince procesos aplicables.
- Ninguna denegación produce efecto lateral.
- Migración con cabeza única y tablas nuevas clasificadas para el baseline limpio (`T-025`).
- Regresión completa sin fallos nuevos: **la certificación funcional sigue en 14/15**.
- `PROCESS_BUSINESS_UNIT_ACCESS_MATRIX.md` completa, sin ningún `PASS` sobre capacidad
  inexistente.

---

# Enmienda A · la concesión se acota a la empresa que la otorgó (2026-09-07)

## A.1 El defecto

La fase 1 construyó la concesión apuntando al **catálogo** de unidades:

```
user_business_units  →  business_units
```

y el resolutor comprobaba la empresa **actual** del usuario. Parece suficiente, y no lo es: la
fila no dice de qué empresa venía, de modo que `breeder` de la empresa A y `breeder` de la
empresa B eran indistinguibles para ella.

Comprobado ejecutando, no razonando:

```
A y B tienen `breeder` habilitada · U está en A con concesión de `breeder`   → ['breeder']
se mueve U a B, sin que nadie le conceda nada allí                            → ['breeder']
                                                                                 ^^^^^^^^^^
                                                                                 debía ser []
```

**La concesión viajó con el usuario.** Y el resolutor no tenía forma de impedirlo: hacía todas
las comprobaciones que sabía hacer, sobre un dato que no contenía la respuesta.

## A.2 Por qué el modelo anterior parecía correcto

Se eligió apuntar al catálogo por una razón que sigue siendo buena: apuntar a la habilitación de
una empresa permitía escribir «usuario de A sobre habilitación de B», y apuntando al catálogo esa
fila no se podía ni expresar.

El error fue tratar **una** combinación inválida como si fueran todas. Al quitar la empresa de la
fila desapareció la combinación imposible, y con ella la información que distingue un contexto de
otro. La respuesta correcta no es quitar la empresa: es **ponerla y validarla**.

## A.3 El modelo corregido

```
user_business_units  →  company_business_units  →  companies
                                                └→ business_units
```

La concesión apunta a la **habilitación de una empresa concreta**, de modo que la fila responde
por sí sola a «¿bajo qué empresa se otorgó esto?».

Y como la combinación entre empresas vuelve a ser representable, se cierra por los dos lados:

```
EN LA ESCRITURA   el límite de servicio rechaza conceder a un usuario una habilitación
                  de otra empresa                                            (`AC-B10`)

EN LA LECTURA     el resolutor exige que la empresa de la habilitación sea la empresa
                  ACTUAL del usuario                                          (`AC-B08`)
```

Las dos hacen falta. La primera sola dejaría efectiva una concesión legítima de ayer cuando el
usuario se mueve hoy; la segunda sola permitiría escribir basura que nunca sirve.

## A.4 Lo que no cambia

- **`BU-D10` sigue `PENDIENTE DE RATIFICACIÓN`.** Qué pasa cuando la **empresa** apaga una unidad
  es otra pregunta, y esta enmienda no la toca ni la prejuzga.
- **No se borra historia.** Las concesiones anteriores se conservan; lo que pierden es la
  efectividad.
- **Ningún comportamiento destructivo nuevo.** Ni cascadas, ni borrados al mover de empresa.

## A.5 Lo que queda declarado y sin decidir

**Si el usuario vuelve a la empresa A, ¿revive su concesión anterior?**

```
SPEC DECISION REQUIRED
```

Ninguna fuente lo dice. Hasta que se decida rige lo conservador: volver no reactiva nada, hace
falta conceder de nuevo. Se registra aquí para que no se resuelva por accidente al implementar.

## A.6 Una observación para la fase 2

`POST /auth/switch-company` emite un token con la empresa **desplazada** en la reclamación, sin
tocar `users.company_id`, y es exclusivo del super administrador —que se siembra sin empresa y
por tanto no resuelve ninguna unidad—. Hoy no hay riesgo.

Pero la fase 2 tendrá que decidir de dónde toma la guarda la empresa efectiva de una petición:
de `users.company_id` o de la reclamación del token. Si son dos fuentes, hay que decir cuál
manda. Queda anotado, no resuelto.

---

# Enmienda B · la empresa efectiva y el regreso (2026-09-07)

## B.1 Qué faltaba

`§4` exigía «misma empresa» como una de las seis condiciones, y **no decía cómo se determina cuál
es**. Con un token que lleva una reclamación de empresa, eso no es un detalle: es la diferencia
entre un aislamiento que se sostiene y uno que se puede pedir.

Y `OD-09.d` resolvió que la concesión no viaja al **salir** de una empresa, sin decir qué pasa al
**volver**.

## B.2 Lo que ya existía y no se toca

`R-48` implementó desde antes de esta spec la regla correcta:

```
usuario normal    manda la base; un token no reclama compañías ajenas
Super Admin       se honra la empresa desplazada por `switch-company`
```

`OD-11` **ratifica** eso, no lo cambia. Lo que la fase 2 añade es lo que faltaba alrededor:

```
CENTRALIZARLO      hoy vive dentro de `get_current_user` y no es invocable desde
                   un servicio ni una tarea

VALIDARLO SIEMPRE  el contexto desplazado se comprobaba al emitirlo y no al usarlo;
                   una empresa puede desactivarse con la sesión viva

DEJAR RASTRO       situarse en otra empresa no quedaba registrado en ninguna parte
```

## B.3 Las tres dimensiones, y por qué se nombran

```
CONTEXTO DE INQUILINO   ≠   ACCESO A UNIDAD   ≠   PERMISO RBAC
```

Cambiar de empresa con éxito **no concede** ninguna unidad ni ningún permiso. El Super
Administrador que se sitúa en una empresa obtiene contexto; sus unidades efectivas se resuelven
aparte y, si nadie se las concedió, son ninguna.

## B.4 El regreso

```
U con A/Reproductora  →  pasa a B  →  vuelve a A
la concesión de A sigue siendo historia inefectiva
```

Volver no prueba el mismo cargo, ni las mismas responsabilidades, ni la misma necesidad
operativa. **Una autorización que revive sola es una autorización que nadie concedió.**

No es `BU-D10`: aquélla trata del ciclo de vida de la **unidad en la empresa**, y ésta del
**usuario entre empresas**. `BU-D10` sigue pendiente de ratificación.

## B.5 La clasificación de rutas

`T-040-06` y `T-040-07`. Toda ruta autenticada declara su relación con la unidad de negocio:

```
CORE                 no depende de ninguna unidad
CONTROL              plano de control de la empresa
UNIDAD_UNICA         pertenece a una cadena concreta
MULTI_UNIDAD         puede tocar varias — sus filas las acota la fase 3
CONTRATO             traspaso entre unidades — sus campos, la fase 5
```

Y la guarda de arranque **falla** si alguna queda sin clasificar, igual que ya falla si alguna no
declara permiso.

```
CLASIFICAR UNA RUTA   ≠   PROTEGER SUS FILAS
```

Que `/api/v1/lots` esté clasificada como `MULTI_UNIDAD` **no** significa que sus filas estén
acotadas. Eso es la fase 3, y hasta entonces sigue devolviendo lotes de todas las unidades de la
empresa.

---

# Enmienda C · las semillas configuran la empresa (2026-09-07)

## C.1 El hecho

Desde que el acceso se acota por cadena, un usuario sin concesiones no ve dato productivo — ni
siquiera el que él mismo registró. Las suites escritas antes de esta capacidad crean usuarios sin
concederles nada, y con razón: entonces no existía.

Medido retirando las concesiones de la semilla:

```
20 pruebas caen · 18 de notificaciones · 2 de auditoría y flujo completo
```

## C.2 La regla

```
UNA SEMILLA DE CERTIFICACIÓN VÁLIDA
    =  empresa con sus cadenas HABILITADAS explícitamente
    +  usuarios con sus cadenas CONCEDIDAS explícitamente
    +  RBAC
    +  dato de negocio
```

**Una precondición válida es parte de la validez de la prueba.** Una prueba que falla porque su
sujeto no tiene cadena concedida, cuando pretende medir otra regla, tiene una fixture inválida —
no revela una regresión.

## C.3 Lo que esto NO es

```
PROHIBIDO   sin concesiones  →  todas las cadenas de la empresa
```

Eso sería el `fail open` que toda esta capacidad existe para impedir, disfrazado de comodidad de
pruebas. La ausencia de concesión sigue significando **ninguna cadena productiva**, y hay prueba
que lo sujeta.

## C.4 Y no todo el mundo recibe las cuatro

Las suites que **miden** el aislamiento siguen construyendo sus propios sujetos —de una cadena,
de varias, de ninguna, de control— y concediendo a mano. Allí la concesión es el objeto de
estudio, no una precondición.

---

# Enmienda D · el flujo 5 deja de ser una ausencia (2026-09-07)

## D.1 Lo que había

Auditado antes de tocar nada, y conviene decirlo con precisión: **la seguridad del flujo 5 ya era
sustancialmente correcta.**

```
el permiso ya existía       `sap:read` · `sap:send_sap`, declarados en las diez rutas
la empresa ya se filtraba   incluidos los accesos por identificador — sin agujero de inquilino
la proyección ya era acotada `ConsolidatedMovementRead` no lleva el lote ni sus internos
```

Lo que faltaba no era un filtro. Era que la transversalidad existía **por ausencia**: nadie había
puesto el filtro por cadena, y eso funcionaba, pero

> una excepción que solo existe porque nadie puso el filtro es indistinguible de un fallo.

## D.2 Lo que la enmienda añade

Una **política tipada** que convierte la ausencia en declaración, y que por tanto puede romperse:

```
el contrato SAP es la ÚNICA transversalidad operativa autorizada
la autoriza una capacidad EXPLÍCITA del catálogo, no la ausencia de código
está acotada a SAP: no es una función genérica que otra superficie pueda reutilizar
```

`§37` del encargo lo pedía así, y es lo correcto: un `saltar_alcance_por_unidad()` genérico
acabaría llamándose desde donde nadie previó.

## D.3 Lo que sigue igual

```
elegibilidad de negocio SAP        intacta — la capacidad dice quién, no qué
superficies normales               acotadas por unidad, para el mismo actor
`P-08`                              BLOCKED_EXTERNAL
`unidades_efectivas`               no se toca ni se amplía
```

---

# Enmienda E · la sesión representa la autoridad, no la define (2026-09-09)

`T-040-20` · fase 8. `AC-H01` fijaba **qué** debe entregar la sesión; `OD-14` y `OD-15`
cambiaron después **qué hay que representar**, y esta enmienda cierra ese hueco.

```
LA SESIÓN REPRESENTA LA AUTORIDAD   ·   NO LA DEFINE
```

Ninguna decisión de seguridad se toma aquí. Todo campo sale de un resolutor que ya existe y ya
está certificado; si un campo necesitara lógica propia, sería señal de que la autoridad no está
donde debe.

## `AC-H11` · cuatro conceptos, cuatro campos

`§14.1` los nombra por separado y por separado se entregan. Reunirlos en una lista sería
volver a la confusión que `GA-REM-040` existe para deshacer:

```
unidades HABILITADAS   de la empresa efectiva      decisión comercial
unidades CONCEDIDAS    al usuario en esa empresa   decisión operativa
unidades EFECTIVAS     lo habilitado ∩ lo concedido ∩ activo en el producto
capacidades            los permisos `RBAC` del actor
```

Una concesión sobre una unidad deshabilitada aparece en **concedidas** y **no** en
**efectivas**. Que las dos listas puedan diferir es el punto: si nunca difirieran, una de ellas
sobraría.

## `AC-H12` · la empresa persistida no es la empresa efectiva

`OD-14`. Para la autoridad global situada con `switch-company`, son distintas, y la sesión las
entrega distintas:

```
company_id             la empresa PERSISTIDA del usuario — `users.company_id`
effective_company_id   sobre la que se opera AHORA — resolutor de `OD-11`
```

`company_id` se conserva por compatibilidad y **queda documentado** lo que significa: era
ambiguo desde `OD-14` y ahora deja de serlo por escrito, no por eliminación.

## `AC-H13` · el actor global es una propiedad del actor, no una empresa

```
is_super_admin     derivado de la capacidad real —`("*", …, "all")`—, nunca del nombre
                   del rol ni de que `company_id` sea nulo (`OD-13.b`)
```

**Corrección a esta misma enmienda.** Su primera redacción pedía un campo nuevo,
`is_global_actor`. Al implementarla quedó claro que habría sido un **sinónimo exacto** del
`is_super_admin` que ya existe y que ya se deriva de la capacidad, no del nombre. Dos campos
obligados a coincidir siempre acaban divergiendo, así que se conserva el que hay y se
documenta su significado — exactamente lo que `AC-H12` hace con `company_id`.

El nombre es histórico y suena a rol; lo que representa es una capacidad. Renombrarlo rompería
el contrato vigente sin ganar nada.

```
PROHIBIDO   una empresa ficticia `GLOBAL` · `company_id = 0` · `company_id = "*"`
PROHIBIDO   sin empresa seleccionada → la primera · o la unión de todas
```

Sin empresa efectiva, `effective_company_id` es **nulo** y las tres listas de unidades van
vacías. Un actor global sin contexto conserva su autoridad de control global y no obtiene dato
de ningún inquilino: es `OD-14.d` representado, no reinterpretado.

## `AC-H14` · administrar no aparece como acceder

El caso que esta fase debe hacer legible, y que `OD-15` volvió obligatorio:

```
Administrador de Accesos      capacidades de `business_units` PRESENTES
                              unidades efectivas                []
```

Las dos cosas a la vez, y **no** es una incoherencia que corregir: es `OD-09.b` por fin visible
en el contrato. Un cliente que reciba esto puede ofrecer la pantalla de administración sin
ofrecer dato productivo.

## Lo que esta enmienda **no** añade

```
NO  lista de empresas seleccionables — `§14.1` no la pide
NO  `users:read` para el Administrador de Accesos — `OD-15 §6` lo decidió al revés
NO  banderas de conveniencia derivadas dos veces
NO  módulos habilitados por empresa — no existe tal requisito
NO  una segunda lengua de permisos para el cliente
```

## Y lo que la sesión sigue sin ser

```
LA SESIÓN INFORMA AL CLIENTE   ·   NO SUSTITUYE AL BACKEND
```

`AC-H10` sigue vigente y se demuestra igual: llamando a la `API` directamente. Que la sesión
diga `capacidad ausente` no protege nada; lo que protege es que la ruta deniegue.

## Tareas

| Tarea | Qué |
|---|---|
| `T-040-20` | Capacidades y unidades en la sesión, por los resolutores centrales |
