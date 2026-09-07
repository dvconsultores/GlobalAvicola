# TRES DECISIONES PARA EL PROPIETARIO

`BU-D11` · `BU-D12` · `BU-D09` · 2026-09-07

```
QUÉ ES ESTO       un documento para decidir
QUÉ NO ES         no es spec · no contiene tareas de implementación
                  no crea tablas · no cambia código · no cambia certificaciones
ESTADO            CONTESTADO el 2026-09-07
```

> ## Respondido
>
> ```
> BU-D11 = C     →  OD-09.a
> BU-D12 = B     →  OD-09.b
> BU-D09 = B     →  OD-09.c
> ```
>
> Las tres recomendaciones de este documento fueron las elegidas. La formalización normativa
> está en `specs/remediation/OD-09-CONTROL-PLANE-VS-BUSINESS-UNIT.md`, que es **la fuente
> vigente**; este documento se conserva como el análisis que llevó a ellas.

---

## 0. Las dos palabras, otra vez, porque toda la decisión depende de no confundirlas

```
MÓDULO RBAC        un permiso.  operations · lots · masters · users · reports …
                   YA EXISTE, ya está certificado.

UNIDAD DE NEGOCIO  una línea.   Progenitoras · Reproductora · Incubadora · Engorde
                   NO EXISTE todavía.
```

Y una tercera distinción, que es el corazón de `BU-D11`:

```
EL ROL CALIFICA A ALGUIEN COMO TRANSVERSAL
    «es contralor de la empresa» — una responsabilidad, la da el cargo

LA CONCESIÓN DE UNIDAD DICE DÓNDE TRABAJA
    «lleva incubadora y engorde» — un ámbito, se asigna una por una
```

Hoy solo existe lo primero. Lo segundo es lo que se va a construir. **La pregunta de `BU-D11` es
qué pasa cuando una persona tiene lo primero y no lo segundo.**

---

## 1. Y una distinción de planos, que evita la respuesta equivocada

```
PLANO DE CONTROL          configurar y vigilar la empresa
                          usuarios · roles · empresa · áreas · unidades
                          auditoría y supervisión, si el rol la autoriza

PLANO OPERATIVO           registrar y consultar la producción
                          lotes · mortalidad · consumo · incubación · movimientos
```

Que alguien administre la empresa **no implica** que pueda operar todas sus líneas. Son dos
permisos distintos y el producto puede darle uno sin el otro. Casi toda la dificultad de estas
tres decisiones desaparece cuando se separan.

---

# `BU-D11`

```
TÍTULO LITERAL    Contraloría y administración
PROBLEMA          si a un contralor se le conceden dos líneas de cuatro,
                  ¿deja de ver y de recibir avisos de las otras dos?
POR QUÉ DECIDE
EL PROPIETARIO    porque `OD-08` ya decidió lo contrario, y `P-14` está certificado
                  sobre esa decisión. No es una elección técnica: es cambiar —o
                  confirmar— una decisión suya anterior.
EVIDENCIA         `backend/app/notifications/recipients.py`
                  FUNCIONES_DE_EMPRESA  administrador · contralor  → sin filtro de alcance
                  FUNCIONES_DE_AREA     gerente · supervisor       → filtradas por área
PROCESOS          `P-14` notificaciones · `P-07` revisión → aprobación
                  `P-09` auditoría interna · `P-15` reportes y KPI
UNIDADES          las cuatro
```

## DECISIÓN

> **Un contralor de la empresa, ¿sigue viendo y recibiendo los avisos de las cuatro líneas,
> aunque solo se le hayan concedido dos?**

## POR QUÉ IMPORTA

Es la única de las doce decisiones que puede **romper algo que hoy está certificado**, y hacerlo
sin ruido.

`OD-08` estableció que administración y contraloría reciben los avisos de toda la empresa. Si al
construir el filtro por línea nadie se acuerda de esta excepción, un contralor con dos líneas
dejará de recibir los avisos de las otras dos **en silencio**: sin error, sin aviso y sin que
ninguna prueba actual lo detecte. Un aviso que no llega es indistinguible de un problema que no
ocurrió.

## SITUACIÓN ACTUAL

Contraloría y administración lo ven y lo reciben todo dentro de su empresa. Es lo que `OD-08`
pidió y lo que `P-14` certifica hoy.

## SI NO SE DECIDE

Se decidirá sola, al escribir el filtro, y probablemente en la dirección de restringir —porque es
la que parece más segura—. `P-14` dejaría de cumplir `OD-08` sin que conste en ninguna parte que
eso se eligió.

---

### OPCIÓN A · La concesión de unidad manda siempre

Contraloría y administración ven y reciben **solo las líneas que se les hayan concedido**, igual
que cualquier otro.

**Consecuencia de negocio.** Cambia la semántica de `OD-08`. El contralor deja de ser un control
de la empresa y pasa a ser un control de sus líneas. Si alguien olvida concederle una, esa línea
queda **sin control y sin que nadie lo note**.

**Consecuencia de seguridad.** La más restrictiva y la más uniforme: una sola regla, sin
excepciones que recordar. También la más fácil de probar.

**Consecuencia de uso.** La supervisión pasa a depender de que la configuración esté completa.
El fallo típico —conceder tres de cuatro— no produce ningún síntoma visible.

---

### OPCIÓN B · Los roles de control atraviesan el filtro

Determinados roles de control acceden a **todas las líneas habilitadas de su empresa**, y la
concesión de unidad no los limita.

**Consecuencia de negocio.** Conserva `OD-08` intacto y `P-14` sigue cumpliendo. La contraloría
sigue siendo de la empresa.

**Consecuencia de seguridad.** Concede de más. Un rol de control obtendría también **acceso
operativo** a las cuatro líneas —registrar, editar, aprobar—, aunque solo necesitara mirar. Es
más de lo que la responsabilidad requiere.

**Consecuencia de uso.** Simple de entender y de explicar.

---

### OPCIÓN C · Separar la visibilidad de control de la operación

Un rol puede ser transversal **para vigilar** sin serlo **para operar**:

```
ACCESO OPERATIVO           limitado por la concesión de unidad
lotes · producción ·       registrar · editar · aprobar
mortalidad · movimientos

VISIBILIDAD DE CONTROL     de toda la empresa, para los roles que lo tengan autorizado
auditoría · avisos ·       LEER · SUPERVISAR
supervisión · KPI          nunca escribir por ello
```

**Consecuencia de negocio.** `OD-08` se conserva donde importa —los avisos siguen llegando— y la
contraloría mantiene su responsabilidad sobre la empresa entera. `P-14` sigue cumpliendo.

**Consecuencia de seguridad.** Es la que menos concede de las que funcionan: la transversalidad
se limita a **leer y vigilar**, que es para lo que existe. Nadie obtiene permiso de escritura por
ser administrador.

**Consecuencia de uso.** Hay que explicar una distinción más —«ves todo, operas lo tuyo»—, pero
coincide con cómo la gente ya entiende un cargo de control.

---

### RECOMENDADA · **OPCIÓN C**

**POR QUÉ.** Es la única que satisface las tres cosas a la vez: conserva `OD-08` sin cambiarlo,
mantiene `P-14` cumpliendo, y no reparte permiso de escritura que nadie pidió. `A` deja líneas
sin vigilancia por un olvido de configuración; `B` convierte un cargo de control en acceso
operativo total.

Y encaja con lo que el producto ya hace: `OD-08` separó **capacidad** (el rol) de **pertenencia**
(el área) precisamente para no confundirlas. `C` aplica la misma separación al eje nuevo.

**CONDICIÓN, y no es negociable.** La transversalidad tiene que ser una **autorización explícita
y concedida**, nunca deducida del nombre del rol. Nada de «si el nombre contiene *admin*, salta
el filtro»: el nombre de un rol es un texto que cualquiera puede editar, y `GA-REM-034` permite
crear roles. Un rol llamado «Administrativo de almacén» no debe heredar la visibilidad de la
empresa por parecerse a otro.

```
OWNER ANSWER REQUIRED:    A / B / C / OTRA
```

---

# `BU-D12`

```
TÍTULO LITERAL    Qué queda fuera del filtro
PROBLEMA          administrar usuarios, roles, áreas y maestros generales,
                  ¿pertenece a alguna línea de producción?
POR QUÉ DECIDE
EL PROPIETARIO    porque define el reparto de responsabilidades dentro de la empresa
                  cliente, no una estructura de datos. Y porque de ella depende qué
                  significa «no tener líneas» en `BU-D09`.
EVIDENCIA         `PROCESS_MODULE_MATRIX.md`
                  `P-13` usuarios y roles   el único ajeno a la línea por completo
                  `P-12` datos maestros     MIXTA: 22 maestros, unos de línea y otros no
PROCESOS          `P-12` · `P-13` · `P-09` · `P-14` · y por contraste, los once operativos
UNIDADES          las cuatro, por definición del contorno
```

## DECISIÓN

> **Cuando a una persona se le da acceso a una o dos líneas, ¿qué sigue pudiendo hacer que no
> pertenezca a ninguna línea en concreto?**

## POR QUÉ IMPORTA

Afecta a **todos** los usuarios, no solo a los que no tienen línea asignada.

El caso que lo hace evidente: si administrar usuarios fuera «por línea», el administrador de una
empresa con cuatro líneas al que se le hayan concedido dos **administraría media empresa** —
crearía usuarios a medias, vería la mitad de los roles y no entendería por qué.

Y hay un caso de verdad ambiguo, que la matriz de procesos ya había marcado: **los datos maestros
son mixtos**. Los parámetros de incubadora son de la incubadora; los proveedores, las causas de
mortalidad y los transportes son de toda la empresa. Los veintidós no se comportan igual.

## SITUACIÓN ACTUAL

No hay ninguna frontera, porque no hay ningún filtro. Todo es transversal por omisión.

## SI NO SE DECIDE

Cada pantalla elegirá por su cuenta según quién la escriba, y acabarán discrepando: usuarios
filtrado en una, no filtrado en otra. Es la clase de incoherencia que no se detecta hasta que un
cliente pregunta por qué ve cosas distintas en dos sitios.

---

### OPCIÓN A · Frontera mínima — casi todo por línea

Solo entrar al sistema y ver el propio perfil quedan fuera. Usuarios, roles, maestros y auditoría
se filtran por línea como la operación.

**Consecuencia de negocio.** La administración de la empresa se fragmenta. Nadie tiene una vista
completa de su propia empresa salvo quien tenga las cuatro líneas.

**Consecuencia de seguridad.** Máximo aislamiento. También máxima probabilidad de que alguien
reciba las cuatro líneas «para que pueda trabajar», lo que anula el aislamiento por la puerta de
atrás.

**Consecuencia de uso.** Confusa: el administrador ve una empresa incompleta y no sabe por qué.

---

### OPCIÓN B · Frontera por planos

```
TRANSVERSAL      entrar · perfil · usuarios · roles · empresa · áreas · unidades
                 auditoría y avisos, según lo que decida `BU-D11`
                 los maestros que no son de una línea concreta

POR LÍNEA        lotes · operación · reportes · paneles · trazabilidad · SAP
                 los maestros que sí son de una línea
```

Los veintidós maestros se clasifican **una vez, en el catálogo**, y no pantalla por pantalla.

**Consecuencia de negocio.** El administrador administra su empresa entera; el operario opera sus
líneas. Coincide con cómo está organizada una empresa real.

**Consecuencia de seguridad.** Correcta, siempre que la clasificación de los maestros se haga con
cuidado: un maestro de línea clasificado como transversal filtra información de línea.

**Consecuencia de uso.** La más natural de explicar: «configuras la empresa, operas tus líneas».

---

### OPCIÓN C · Caso por caso

Cada capacidad decide por su cuenta si se filtra.

**Consecuencia de negocio.** Sin regla general, no hay forma de anticipar qué se verá.

**Consecuencia de seguridad.** La peor: no existe una afirmación que probar, de modo que no se
puede certificar «esto no se ve» de nada en particular.

**Consecuencia de uso.** Incoherente entre pantallas.

Es, además, **lo que ocurre si no se decide**: no es tanto una opción como el resultado por
omisión.

---

### RECOMENDADA · **OPCIÓN B**

**POR QUÉ.** Es la única que produce una frase comprobable —«el plano de control es de la
empresa, el operativo es de la línea»— y la única que un cliente puede explicarle a su propia
gente sin un diagrama.

**Con dos condiciones.**

La primera: los **veintidós maestros se clasifican explícitamente**, uno por uno y una sola vez,
como parte de esta decisión y no durante la implementación. La matriz de procesos ya avisó de que
son mixtos; dejarlo para después es reintroducir la opción `C` por la puerta de atrás.

La segunda: administrar el plano de control **no concede** operar ninguna línea. Es la misma
separación que `BU-D11`, aplicada aquí.

```
OWNER ANSWER REQUIRED:    A / B / C / OTRA
```

---

# `BU-D09`

```
TÍTULO LITERAL    Alguien sin ninguna línea asignada
PROBLEMA          se crea un usuario y nadie le asigna línea. Entra. ¿Qué pasa?
POR QUÉ DECIDE
EL PROPIETARIO    porque es la experiencia de la primera persona que entra en cada
                  empresa cliente, y porque la respuesta segura y la amable son
                  opuestas. No hay opción neutra.
EVIDENCIA         el alta de usuario no exigiría concesión de unidad: sería un campo
                  más, y los campos se olvidan. `GA-REM-039` ya aceptó que el área del
                  usuario sea opcional, con el mismo razonamiento.
PROCESOS          `P-13` alta de usuarios · y el efecto se nota en los quince
UNIDADES          ninguna — ése es exactamente el caso
```

## DECISIÓN

> **Una persona a la que se ha dado de alta pero a la que nadie ha asignado todavía una línea,
> ¿debe poder entrar?**

## POR QUÉ IMPORTA

No es un problema de migración, que fue como se leyó al principio. **Pasará todos los meses**:
cada alta que alguien deja a medias, cada persona nueva cuyo jefe todavía no ha dicho en qué
línea va a trabajar. Y es la primera impresión del producto para el primer usuario de cada
cliente nuevo.

## SITUACIÓN ACTUAL

No aplica: no hay líneas todavía. Todo usuario activo entra y ve toda su empresa.

## SI NO SE DECIDE

Se resolverá en el código, casi con seguridad denegando —porque denegar parece lo prudente—, y
nadie sabrá que se eligió. El síntoma será un usuario que llama diciendo que su contraseña no
funciona, cuando funciona perfectamente.

---

### OPCIÓN A · No puede entrar

**Consecuencia de negocio.** El alta queda incompleta y no se nota hasta que la persona intenta
trabajar. Alguien pierde una mañana.

**Consecuencia de seguridad.** La más estricta, y es real: sin línea no hay nada que pueda ver.

**Consecuencia de uso.** Mala, y de una forma concreta: el sistema dice «no puedes entrar»
cuando la verdad es «te falta configuración». Confunde un problema de permisos con uno de
credenciales, y el usuario no tiene forma de averiguar la diferencia. Genera llamadas al soporte
que nadie sabe diagnosticar.

---

### OPCIÓN B · Entra, y ve el plano de control que su rol le permita; la operación aparece vacía

Con un mensaje claro: *«todavía no tienes ninguna línea de producción asignada; pídesela al
administrador de tu empresa».*

**Consecuencia de negocio.** El administrador **puede entrar y configurarse la empresa** — que es
justo lo que hay que hacer el primer día, cuando por definición nadie tiene líneas todavía. Con
la opción `A`, el primer administrador de cada cliente no podría entrar a asignarse nada.

**Consecuencia de seguridad.** Equivalente a `A` en lo operativo: sin línea no ve ni un lote. Lo
que sí ve es lo que `BU-D12` haya declarado transversal **y su rol permita**, que para un
operario es prácticamente nada.

**Consecuencia de uso.** Diagnosticable. El usuario ve qué le falta y a quién pedírselo.

---

### OPCIÓN C · Entra y lo ve todo hasta que se le asigne alguna línea

**Consecuencia de negocio.** Cómodo, y peligroso: nadie asignará líneas nunca, porque sin
asignarlas todo funciona.

**Consecuencia de seguridad.** Inaceptable. Convierte «no configurado» en «acceso total», que es
la puerta abierta clásica. Y hace que la capacidad entera sea opcional en la práctica.

**Consecuencia de uso.** Excelente hasta el día del incidente.

**No se recomienda.**

---

### RECOMENDADA · **OPCIÓN B**

**POR QUÉ.** Porque `A` tiene un fallo que se ve al pensar en el primer día de un cliente: si un
usuario sin líneas no puede entrar, **el primer administrador no puede entrar a asignárselas**, y
la empresa nace bloqueada. Haría falta una excepción para el primer usuario — y una excepción es
exactamente lo que `B` evita al no necesitarla.

Y porque `B` no concede nada: sin línea no se ve ni un lote. La diferencia con `A` no es cuánto
se ve, sino si el usuario **puede entender por qué no ve nada**.

**Depende de `BU-D12`**, y por eso conviene decidirlas juntas: «lo transversal» es precisamente lo
que `BU-D12` defina. Si `BU-D12` fuera la opción `A` —frontera mínima—, entonces `B` aquí
significa entrar y ver únicamente el propio perfil.

```
OWNER ANSWER REQUIRED:    A / B / C / OTRA
```

---

# 2. Cómo se relacionan las tres

```
BU-D12  define QUÉ es transversal
   │
   ├──►  BU-D09  usa esa definición: sin línea, se ve lo transversal
   │
   └──►  BU-D11  decide QUIÉN, además, ve la empresa entera
                 y en la opción C, decide además PARA QUÉ:
                 vigilar sí, operar no
```

Las tres responden a la misma pregunta desde tres sitios: **qué parte del producto no depende de
la línea en que uno trabaje.** Por eso conviene contestarlas de una vez, y no de una en una.

Si las tres recomendaciones se aceptan, la regla que queda es una sola frase:

> El plano de control es de la empresa; el operativo es de la línea. Quien tiene un cargo de
> control ve toda la empresa para vigilarla, y opera solo sus líneas. Quien no tiene línea
> todavía, entra y ve el plano de control que su cargo permita.

# 3. Lo que este documento no toca

- **`BU-D01` y `BU-D02` no se trabajan aquí.** Siguen `PENDING`.
- **El dato nuevo del despacho** —que la incubadora vea el huevo antes de recibirlo— pertenece a
  **`BU-D01`, flujo 2**, verificado en `BUSINESS_UNIT_OWNER_DECISION_MATRIX.md §5`. **No es de
  esta tanda** y no se desarrolla.
- **`P-14` no se reabre.** Conserva su certificación funcional. `BU-D11` documenta el impacto; no
  lo aplica.
- **`P-08`, `R-98`, `R-99`, `GA-TD-014` y el despliegue automático**: sin tocar.
- **`GA-REM-040` no se crea.**
- **No se asigna ningún `OD-` definitivo.** Los `BU-Dxx` son identificadores de este dosier.
- **Ninguna decisión se marca como resuelta.** Las tres siguen `PENDING_OWNER` hasta que el
  propietario conteste `A`, `B`, `C` u otra cosa.
