# OD-09 — PLANO DE CONTROL FRENTE A UNIDAD DE NEGOCIO

## Metadata
| Campo | Valor |
|---|---|
| ID | `OD-09` |
| Tipo | **Decisión normativa** (no es una remediación) |
| Fecha | 2026-09-07 |
| Origen | Resolución explícita del propietario del producto |
| Estado | **VIGENTE** |
| Alcance | Acceso por unidad de negocio: `GA-REM-040` y sus derivados |
| Antecedente | `audit/remediation/BU_DECISION_BRIEF_D11_D12_D09.md` |
| Resuelve | `BU-D11 = C` · `BU-D12 = B` · `BU-D09 = B` · **enm. A** alcance · **enm. B** regreso |
| Preserva | `OD-08` · `P-14` `CERTIFIED` |

---

## 0. Por qué las tres en un solo `OD`

Se formalizan juntas porque son **una sola resolución** contestada en un solo acto: las tres
responden a la misma pregunta desde tres sitios —qué parte del producto no depende de la línea en
la que uno trabaja—. Separarlas en tres identificadores sugeriría que pueden evolucionar por
separado, y no pueden: cambiar una obligaría a revisar las otras dos.

Es el mismo patrón de `OD-08`, que resolvió destinatarios, modelo de área y «próximo a cierre»
bajo un identificador.

---

## 1. Vocabulario vinculante

```
MÓDULO RBAC          un permiso.   operations · lots · masters · users · reports …
                     EXISTE y está certificado.

UNIDAD DE NEGOCIO    una línea.    Progenitoras · Reproductora · Incubadora · Engorde
                     NO EXISTE todavía.
```

**No son sinónimos y no se llaman igual.** Un documento que use «módulo» para las dos cosas
incumple este `OD`.

`BirdTypeEnum` sigue siendo un **enum de dominio** y no se convierte en control de acceso.

**La unidad de negocio no es el área.** `Area` (`GA-REM-039`) es pertenencia organizativa dentro
de la empresa y sirve a los destinatarios de `P-14`. Son dos ejes distintos y no se mezclan.

---

## 2. Declaración

```
CONTROL VISIBILITY  y  OPERATIONAL ACCESS  SON CAPACIDADES DISTINTAS
```

De esa frase salen las tres partes.

---

## 3. `OD-09.a` — Contraloría y control · resuelve `BU-D11` con la opción `C`

```
COMPANY-WIDE CONTROL READ      = PERMITIDO
BUSINESS-UNIT OPERATION        = ACOTADO a las unidades efectivas concedidas
```

Un rol de control **puede ver** todas las unidades habilitadas **de su propia empresa** cuando su
función lo requiera:

```
supervisión · control · auditoría · reportes · indicadores · notificaciones
consulta requerida por su función
```

Y **solo puede**:

```
CREAR · MODIFICAR · APROBAR · EJECUTAR · OPERAR
```

sobre unidades para las que tenga **acceso operativo efectivo** *y* el permiso `RBAC`
correspondiente, salvo que exista otro permiso transversal explícito y normativamente definido.

### 3.1 La transversalidad se concede; no se deduce

```
PROHIBIDO      if "admin" in role.name:  saltar el filtro
```

El nombre de un rol es texto editable, y `GA-REM-034` permite crear roles. Un rol llamado
«Administrativo de almacén» no hereda la visibilidad de la empresa por parecerse a otro. La
transversalidad de control es una **autorización explícita** que alguien concede y que se puede
retirar.

### 3.2 Nunca cruza la empresa

```
ALCANCE = LA MISMA EMPRESA, SIEMPRE
```

Nunca entre empresas, nunca entre inquilinos. El `Super Administrador` global —sembrado sin
empresa— **no se convierte automáticamente en contraloría operativa** de ninguna empresa. Es la
misma cautela que `OD-08` ya había impuesto a los destinatarios.

### 3.3 `P-14` y `OD-08` se preservan

`OD-08` sigue vigente y `P-14` sigue `CERTIFIED`. Contraloría y administración continúan
recibiendo los avisos **de toda su empresa** cuando la regla de `P-14` las define como
destinatarias transversales.

```
PROHIBIDO   filtrar en silencio esas notificaciones por concesión de unidad
```

Recibir un aviso es visibilidad de control, no autoridad operativa: que a un contralor le llegue
la alerta de un lote de incubadora **no** le da permiso para modificarlo.

---

## 4. `OD-09.b` — El plano de control · resuelve `BU-D12` con la opción `B`

```
ADMINISTRACIÓN DEL ACCESO   ≠   ACCESO OPERATIVO A LOS DATOS
```

Administrar usuarios, roles, permisos, asignación de unidades y configuración de la empresa es
**plano de control de la empresa**. No pertenece a Progenitoras, Reproductora, Incubadora ni
Engorde como unidad productiva.

```
PLANO DE CONTROL      acceso · perfil · usuarios · roles · empresa · áreas · unidades
   transversal        auditoría y avisos, según `OD-09.a`
                      los maestros que no son de una línea concreta

PLANO OPERATIVO       lotes · operación · reportes · paneles · trazabilidad · SAP
   por unidad         los maestros que sí son de una línea
```

Un administrador autorizado gestiona esas capacidades **según su `RBAC`**, aunque él mismo no
tenga acceso operativo a todas las unidades productivas.

### 4.1 El ejemplo que fija el significado

```
Un administrador de empresa PUEDE            asignar Incubadora a otro usuario
                            NO POR ELLO      consultar ni modificar lotes de Incubadora
```

Si además necesita operar incubadora, se le concede la unidad. Administrar el acceso y usar el
acceso son dos cosas.

### 4.2 Sin atajo de administrador

```
PROHIBIDO      if role == admin:  allow everything
```

El plano de control tiene **permisos propios**. La operación productiva conserva sus tres
condiciones a la vez:

```
unidad de negocio  +  permiso RBAC  +  regla de negocio del recurso
```

### 4.3 Los veintidós maestros se clasifican una vez

`PROCESS_MODULE_MATRIX.md` registra `P-12` como **mixta**: los parámetros de incubadora son de la
incubadora; los proveedores, las causas de mortalidad y los transportes son de toda la empresa.

La clasificación se hace **en el catálogo, una sola vez**, y no pantalla por pantalla. Dejarla a
la implementación reintroduciría por la puerta de atrás la opción que se descartó.

---

## 5. `OD-09.c` — El usuario sin unidades · resuelve `BU-D09` con la opción `B`

```
USUARIO CON CERO UNIDADES DE NEGOCIO

    PUEDE AUTENTICARSE                 el usuario es válido
    PUEDE USAR LO TRANSVERSAL          lo que su rol permita, según `OD-09.b`
    NO TIENE ACCESO PRODUCTIVO         ni ve ni opera dato de producción
```

### 5.1 No se deniega el acceso

```
PROHIBIDO     401 · «usuario inválido» · «cuenta deshabilitada»
```

Ausencia de unidad **no es** un problema de credenciales. La contraseña es correcta y el usuario
existe. Lo que ocurre es, literalmente:

```
effective_business_units = []
```

Esto no es una comodidad: es lo que permite que **el primer administrador de cada empresa
cliente pueda entrar a configurarla**. El primer día nadie tiene unidades todavía; denegar el
acceso dejaría la empresa nacida bloqueada y obligaría a inventar una excepción para el primer
usuario.

### 5.2 Cero unidades no significa toda la empresa

```
PROHIBIDO     sin unidad → devolver todo el dato de la empresa
REGLA         SIN UNIDAD DE NEGOCIO = SIN DATO PRODUCTIVO
```

Lo desconocido o no concedido **deniega**. Nunca se retrocede a «toda la empresa» como valor por
defecto.

### 5.3 Lo que debe ver

Las zonas productivas aparecen **vacías o no disponibles**, con un mensaje comprensible, del
tipo:

```
No tienes unidades de negocio asignadas.
Contacta al administrador de tu empresa.
```

Por `i18n`, con las dos lenguas del proyecto. **No se codifica todavía**: el texto se fija cuando
se escriba la spec.

La diferencia con denegar el acceso no es cuánto se ve —en lo productivo, nada en ambos casos—
sino si el usuario **puede entender por qué no ve nada**.

---

## 5 bis. `OD-09.d` — La concesión pertenece a una empresa · **enmienda A** (2026-09-07)

```
UNA CONCESIÓN DE UNIDAD DE NEGOCIO PERTENECE A
    USUARIO  +  EMPRESA  +  UNIDAD
```

Significa:

> «La empresa A concedió al usuario U acceso a la unidad X **dentro de la empresa A**.»

Y **no**:

> ~~«El usuario U tiene acceso a la unidad X.»~~

### 5 bis.1 Por qué se añade, y por qué aquí

No es una decisión nueva: es lo que `OD-09.b` ya implicaba. Si administrar el acceso es un acto
del **plano de control de una empresa**, entonces lo concedido pertenece a esa empresa. Lo que
faltaba era decirlo, y esa omisión tenía consecuencia observable.

La fase 1 de `GA-REM-040` construyó la concesión apuntando al **catálogo** de unidades, no al
contexto de la empresa. La consecuencia se comprobó ejecutando:

```
empresa A con `breeder` habilitada · usuario U en A · concesión de `breeder`   → efectiva
se mueve U de la empresa A a la empresa B, que también tiene `breeder`
sin que nadie le conceda nada en B                                             → ['breeder']
```

La concesión **viajó con el usuario**. No por un fallo del resolutor —comprueba la empresa
actual— sino porque la fila no dice de qué empresa venía, y `breeder` en A y `breeder` en B eran
indistinguibles para él.

### 5 bis.2 La regla al cambiar de empresa

```
MOVER USUARIO   empresa A → empresa B

    concesiones de A     quedan como HISTORIA · dejan de ser efectivas
    concesiones en B     NINGUNA, por defecto
```

**No se copian automáticamente.** Que la unidad exista en la empresa de destino no es un motivo
para concederla: es la misma cadena productiva, pero es otra empresa, con otros lotes, otras
granjas y otra gente.

### 5 bis.3 El mismo código de unidad en dos empresas son dos contextos distintos

```
empresa A / breeder   y   empresa B / breeder
```

son **dos contextos de autorización separados**. Una concesión en uno **nunca** satisface el
otro. Es la consecuencia directa de `§3.2`: nada de esto cruza la empresa.

### 5 bis.4 Historia no es acceso

```
PROHIBIDO   existe la fila de concesión  →  acceso permitido

REGLA       la concesión existe y está viva
       AND  la unidad está habilitada para la empresa
       AND  el usuario pertenece HOY a esa empresa
            → entonces, y solo entonces, puede ser efectiva
```

### 5 bis.5 No se borra historia

```
PROHIBIDO   cambiar de empresa  →  BORRAR las concesiones anteriores
```

Quedan registradas e inefectivas. Borrarlas haría imposible reconstruir quién tuvo acceso a qué
y cuándo, que es justo lo que un control de acceso tiene que poder responder.

### 5 bis.6 Lo que esta enmienda NO decide

**Si el usuario vuelve a la empresa A, ¿revive su concesión anterior?** Ninguna fuente lo dice, y
no se inventa.

```
SPEC DECISION REQUIRED     antes de implementar ese comportamiento
```

Es distinto de `BU-D10` —que trata de qué pasa cuando la **empresa** apaga una unidad— y no se
resuelve arrastrando aquella. `BU-D10` sigue `PENDIENTE DE RATIFICACIÓN`.

Hasta que se decida, el comportamiento es el conservador: volver a la empresa A **no** reactiva
nada por sí solo; hace falta una concesión explícita.

---

## 5 ter. `OD-09.e` — Volver no restaura · **enmienda B** (2026-09-07)

```
VOLVER A UNA EMPRESA ANTERIOR   ≠   RECUPERAR LA AUTORIZACIÓN ANTERIOR
```

`OD-09.d` dijo que la concesión no viaja al **salir** de una empresa. Faltaba el caso espejo:
qué pasa al **volver**.

```
U tiene A / Reproductora concedida
U pasa de A a B          →  la concesión de A queda como historia, inefectiva
U vuelve de B a A        →  SIGUE siendo historia, SIGUE inefectiva
```

Hasta que un administrador autorizado otorgue una **concesión nueva y explícita**.

### 5 ter.1 Por qué no se reactiva sola

Volver a una empresa no prueba nada de lo que la concesión daba por supuesto:

```
el mismo cargo · las mismas responsabilidades · el mismo jefe
la misma necesidad operativa · la misma autorización
```

Alguien que se fue de producción y vuelve a administración no debería recuperar el acceso a los
lotes porque el sistema recuerde que un día lo tuvo. Una autorización que revive sola es una
autorización que nadie concedió.

### 5 ter.2 La historia se conserva

```
PROHIBIDO   volver  →  borrar o revivir las concesiones anteriores
```

Quedan registradas, auditables e **inefectivas**. Existir no es autorizar.

### 5 ter.3 Y con ello `BU-D09` sigue en pie

Al volver, mientras nadie conceda nada:

```
unidades efectivas  =  []
```

Que es el estado que `OD-09.c` ya declaró correcto: se entra, se usa lo transversal, no se ve
dato productivo.

### 5 ter.4 Esto no es `BU-D10`

```
OD-09.e    qué pasa con la concesión cuando el USUARIO cambia de empresa
BU-D10     qué pasa con la concesión cuando la EMPRESA apaga una unidad
```

Dos ciclos de vida distintos. `BU-D10` sigue **`PENDIENTE DE RATIFICACIÓN`** y no se resuelve
arrastrando ésta.

---

## 6. Lo que esta decisión NO autoriza

- **No crea** `BusinessUnit`, `CompanyBusinessUnit` ni `UserBusinessUnitAccess`.
- **No crea** `GA-REM-040`, ni tablas, ni migraciones, ni guardas.
- **No modifica** `BirdTypeEnum`, ni el `RBAC`, ni ninguna de las 198 rutas.
- **No reabre** `P-14` ni ninguna certificación. `FUNCIONAL 14/15` sin cambios.
- **No toca** `P-08`, `GA-TD-014`, `R-98`, `R-99` ni el despliegue automático.
- **No resuelve** `BU-D01` ni `BU-D02`, que siguen pendientes.
- **No resuelve** `BU-D05`, que `ENV-01` sitúa en el alta del primer cliente real.
- **No resuelve** `OD-05`, del que depende quién puede conceder qué.

## 7. Trazabilidad

| Dosier | Decisión | Opción | Parte de este `OD` |
|---|---|:--:|---|
| `BU-D11` | Contraloría y administración | **C** | `OD-09.a` |
| `BU-D12` | Qué queda fuera del filtro | **B** | `OD-09.b` |
| `BU-D09` | Alguien sin ninguna línea asignada | **B** | `OD-09.c` |

Los identificadores `BU-Dxx` conservan su significado y no se renumeran: son los del dosier de
análisis. Este `OD` es su formalización normativa.

## 8. Consecuencia sobre la preparación de la spec

```
BLOQUEANTES DE LA SPEC     5  →  2        quedan BU-D01 y BU-D02
```
