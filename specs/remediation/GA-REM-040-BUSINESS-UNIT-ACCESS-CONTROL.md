# `GA-REM-040` · ACCESO POR UNIDAD DE NEGOCIO

| Campo | Valor |
|---|---|
| **ID** | `GA-REM-040` · `CROSS-CUTTING CAPABILITY SPEC` |
| **Prioridad** | **P0** · Estado **`SPEC_READY`** (2026-09-07) · sin implementar |
| **Requisito** | habilitación de unidades por empresa y acotamiento por usuario |
| **Decisiones** | `OD-09` (`a` `b` `c`) · `OD-10` (`a` `b` `c`) · marco `ENV-01` |
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
CONCESIÓN POR USUARIO       ¿tiene este usuario concesión operativa sobre ella?
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

## 22. Hoja de ruta

```
FASE  1   fundamento          catálogo · habilitación · concesión · resolutor       T-040-01…05
FASE  2   seguridad central   clasificación de rutas · guarda · fail closed         T-040-06…08
FASE  3   filtro por fila     lotes y listas compartidas · detalle · buscadores     T-040-09…10
FASE  4   agregados           contadores · KPI · paneles · reportes · exportación   T-040-11…12
FASE  5   contratos           los siete flujos · destino del despacho               T-040-13…15
FASE  6   clasificación       estado · bandeja · acción · auditoría                 T-040-16…17
FASE  7   API de administración                                                     T-040-18…19
FASE  8   sesión                                                                    T-040-20
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
