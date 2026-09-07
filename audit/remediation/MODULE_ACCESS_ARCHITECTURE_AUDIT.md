# AUDITORÍA DE ARQUITECTURA DE ACCESO POR MÓDULO

`2026-09-07` · **AUDITORÍA · NO SE MODIFICÓ CÓDIGO**

Entregable principal. Las veinte matrices que lo sostienen se citan en cada sección.

---

## 0. La pregunta

No es «cómo ocultamos los módulos». Es:

> ¿cómo garantizamos que una empresa y cada uno de sus usuarios solo pueda **ver, consultar,
> modificar, reportar, exportar, recibir notificaciones y ejecutar procesos** de los módulos
> que realmente tiene habilitados?

Y la respuesta corta, medida sobre el código:

```
Hoy no se garantiza de ninguna manera.
No hay una sola comprobación por unidad de negocio en las 198 rutas de la API.
```

---

## 1. Lo primero: hay dos cosas llamadas «módulo»

```
MÓDULO RBAC (funcional)     approvals · audit · corrections · dashboard · lots
                            masters · operations · reports · review · sap · users
                            → qué PARTE DEL SOFTWARE toca el usuario

UNIDAD DE NEGOCIO           Progenitoras · Reproductoras · Incubadora · Engorde
                            → qué CADENA PRODUCTIVA ve
```

Son ejes ortogonales, y el sistema solo implementa el primero. En este informe se usa **unidad
de negocio** para lo que el propietario pide, precisamente para no arrastrar la ambigüedad al
esquema. Detalle en `MODULE_CATALOG_MATRIX.md §1`.

---

## 2. Las respuestas a las veinticinco preguntas

**1 · ¿Cuáles son los módulos reales?** Cuatro unidades de negocio, existentes solo como
`BirdTypeEnum`: `grandparent`, `breeder`, `hatchery`, `broiler`. Coinciden con los que el
propietario nombra. No hay tabla, no son administrables, y nada los liga a una empresa.

**2 · ¿Qué es CORE?** Autenticación, usuarios y roles, empresas, auditoría, notificaciones y
áreas. Seis capacidades que no tiene sentido apagar. Ver `CORE_VS_BUSINESS_MODULE_MATRIX.md`.

**3 · ¿Cómo restringe hoy una empresa sus módulos?** No lo hace. `Company` tiene diez columnas
y ninguna es de módulos, funcionalidades, plan ni capacidades.

**4 · ¿Y un usuario?** Tampoco. `User` tiene `company_id`, `role_id` y `area_id`. Nada de
módulos.

**5 · ¿Hay aislamiento por unidad dentro de la misma empresa?** **No.** Ninguna ruta, ningún
servicio, ninguna consulta lo aplica.

**6 · ¿Qué rutas pueden filtrar otra unidad?** Las 198 de `/api/v1`. Con tres patrones distintos
de fuga —listado, detalle por identificador y agregado— descritos en
`BACKEND_ROUTE_MODULE_MATRIX.md §4`.

**7 · ¿Qué tablas compartidas necesitarían filtro por fila?** Dieciséis. Solo dos de las 51
tablas tienen discriminador de unidad, y una de ellas es un catálogo. Ver
`SHARED_ENTITY_ROW_SCOPE_MATRIX.md`.

**8 · ¿Qué procesos son de una sola unidad?** Tres de quince: `P-01`, `P-03` y `P-13`. Los otros
doce cruzan. Ver `PROCESS_MODULE_MATRIX.md`.

**9 · ¿Qué flujos cruzados necesitan decisión?** Siete, y ninguno está especificado. Ver
`CROSS_MODULE_FLOW_MATRIX.md §3`.

**10 · ¿Qué paneles y KPI filtran datos?** Los dieciséis. Ver
`DASHBOARD_KPI_MODULE_MATRIX.md`.

**11 · ¿Qué reportes y exportaciones?** Ocho superficies. La exportación vive **en el cliente**,
de modo que arreglar la API la arregla — salvo el artefacto SAP, que se escribe en disco. Ver
`REPORT_EXPORT_MODULE_MATRIX.md`.

**12 · ¿Qué notificaciones necesitan filtro?** Los seis eventos de `P-14`. Y una excepción
normativa que alguien debe autorizar: el `Analista SAP` trabaja con las cuatro por definición.
Ver `NOTIFICATION_MODULE_MATRIX.md §3`.

**13 · ¿Qué tareas deben respetar el estado de módulo?** Las dos del evaluador periódico. No
son fuga —cada aviso va a su empresa— pero producirían sobre módulos apagados. Ver
`BACKGROUND_JOB_MODULE_MATRIX.md`.

**14 · ¿`/me` expone lo suficiente?** No. Ni módulos, ni permisos. Ver
`SESSION_CAPABILITY_GAP_MATRIX.md`.

**15 · ¿Se puede revocar el acceso al instante?** **Sí**, y es la mejor noticia de esta
auditoría: el token no lleva autorización y el contexto se lee de la base en cada petición. No
hay caché que invalidar.

**16 · ¿Qué datos existentes no se pueden clasificar?** Tres bloques: eventos sin lote,
inspecciones, y los lotes de huevo y pollito que cruzan por diseño. Ver
`LEGACY_DATA_MODULE_MAPPING_MATRIX.md §3`.

**17 · ¿Qué migraciones harían falta?** Catálogo de unidades, habilitación por empresa,
concesión por usuario, y —según la decisión de diseño— un discriminador en `operational_events`.

**18 · ¿Modelo recomendado para empresa?** Ver §5.

**19 · ¿Y para usuario?** Ver §5.

**20 · ¿Dónde va la guarda central?** Ver §6. **No** ruta por ruta.

**21 · ¿Qué debe seguir siendo del backend?** Todo lo que decide. La interfaz decide qué se ve.

**22 · ¿Qué cambia en la interfaz?** Dos pantallas de administración y el filtrado del menú.
Ver `MODULE_ADMIN_UI_MATRIX.md`.

**23 · ¿Qué queda para el propietario?** Ocho decisiones. Ver §8.

**24 · ¿Qué spec debería gobernarlo?** Ver §9.

**25 · ¿Cuál es la hoja de ruta más segura?** Ver §10.

---

## 3. Los hallazgos

Numerados siguiendo el registro vigente: el último hallazgo es `R-99`, de modo que estos serían
`R-100` en adelante. **No se dan de alta en el backlog**: esta tanda es auditoría, y darlos de
alta implicaría comprometer identificadores antes de que exista spec.

### `R-100` · No existe habilitación de módulos por empresa · **P1**

```
Evidencia:          Company = id · name · tax_id · country · currency · sap_config
                    approval_levels · is_active · created_at · updated_at
Comportamiento:     toda empresa tiene, de hecho, las cuatro unidades
Arquitectura:       nivel 2 de la pila de acceso
Riesgo:             no es fuga por sí solo; es la pieza sin la cual nada más se puede construir
Módulos:            los cuatro          Procesos: los quince
Destino:            spec nueva          Prioridad: P1
```

### `R-101` · No existe concesión de módulos por usuario · **P1**

```
Evidencia:          User = ... company_id · role_id · area_id · view_type ...
Comportamiento:     todo usuario ve las cuatro unidades de su empresa
Arquitectura:       nivel 3
Riesgo:             es el requisito central del propietario
Destino:            spec nueva          Prioridad: P1
```

### `R-102` · Los listados devuelven todas las unidades de la empresa · **P0**

```
Evidencia:          GET /lots y GET /operations filtran solo por company_id
                    ningún servicio consulta bird_type para acotar
Comportamiento:     un usuario de Reproductoras ve en SU PROPIA LISTA los lotes de Incubadora
Riesgo:             fuga entre unidades de la misma empresa, sin necesidad de truco alguno
Rutas:              /lots · /operations · /operations/alerts · /review · /approvals
Destino:            spec nueva          Prioridad: P0
```

### `R-103` · Los agregados suman las cuatro unidades · **P0**

```
Evidencia:          14 endpoints de KPI + 2 paneles, filtrados solo por empresa
Comportamiento:     la mortalidad total revela la de Incubadora por diferencia
Riesgo:             sobrevive a cualquier filtro de listado: es fuga por agregación
Procesos:           P-15 (funcionalmente certificado)
Destino:            spec nueva          Prioridad: P0
```

### `R-104` · `operational_events` no tiene unidad derivable cuando no tiene lote · **P0**

```
Evidencia:          OperationalEvent sin bird_type; lot_id NULABLE desde i9j0k1l2m3n4
Comportamiento:     las inspecciones no pertenecen a ninguna unidad computable
Riesgo:             bloquea el filtro por fila Y la clasificación del legado
Destino:            spec nueva + decisión del propietario      Prioridad: P0
```

### `R-105` · `lots.bird_type` es nulable · **P1**

```
Evidencia:          bird_type: Mapped[Optional[BirdTypeEnum]]
Comportamiento:     un lote puede no pertenecer a ninguna unidad
Riesgo:             con `fail closed` esas filas desaparecen para todos
Destino:            spec nueva          Prioridad: P1
```

### `R-106` · Los flujos entre unidades no tienen contrato · **P1**

```
Evidencia:          7 flujos cruzados, 0 especificados
Comportamiento:     hoy todos ven todo, de modo que el problema no se manifiesta
Riesgo:             filtrar sin contrato ROMPE P-02, P-04, P-05, P-06 y P-10, certificados
Destino:            DECISIÓN DEL PROPIETARIO antes que spec     Prioridad: P1
```

### `R-107` · Los buscadores revelan la estructura de otras unidades · **P2**

```
Evidencia:          22 endpoints con parámetro `search`
Comportamiento:     un autocompletado devuelve incubadoras a quien no tiene Incubadora
Riesgo:             no expone dato productivo; sí la estructura
Destino:            spec nueva          Prioridad: P2
```

### `R-108` · Las tareas de fondo producirían sobre módulos apagados · **P1**

```
Evidencia:          sla.py recorre todas las empresas y todos los lotes activos
Comportamiento:     correcto hoy; incorrecto en cuanto exista el interruptor
Riesgo:             avisos sobre unidades deshabilitadas
Destino:            spec nueva          Prioridad: P1
```

### `R-109` · `/me` no expone capacidades · **P2**

```
Evidencia:          UserRead sin `permissions`; el contexto interno sí los tiene
Comportamiento:     la interfaz no puede decidir coherentemente qué mostrar
Relación:           es el mismo hueco que `R-98`, que sigue abierto y NO se cierra aquí
Destino:            spec nueva          Prioridad: P2
```

### `R-110` · La ruta `/poultry/:birdType` no está protegida · **P2**

```
Evidencia:          App.tsx, ruta con la unidad en la URL, sin guarda
Comportamiento:     escribir /poultry/hatchery carga la pantalla
Riesgo:             P2 y no P0 porque la fuga real ya ocurre sin escribir nada (R-102)
Destino:            spec nueva          Prioridad: P2
```

```
P0 · 3     R-102 · R-103 · R-104
P1 · 5     R-100 · R-101 · R-105 · R-106 · R-108
P2 · 3     R-107 · R-109 · R-110
P3 · 0
```

---

## 4. Los tres riesgos mayores

**1 · El listado, no la URL.** La atención se va a `/poultry/hatchery`, pero la fuga real no
necesita destreza: `GET /lots` la sirve sola. Cualquier diseño que empiece por «proteger rutas»
llegará tarde.

**2 · La agregación.** Aunque se filtraran listados y detalles, catorce indicadores seguirían
sumando las cuatro unidades. La fuga por diferencia es silenciosa y no deja rastro.

**3 · El legado sin clasificar.** Tres bloques de datos no admiten unidad derivable. `fail
closed` los oculta a todos; `fail open` deja un agujero permanente. No hay tercera vía técnica:
hace falta decidir.

---

## 5. Modelo de datos recomendado

Sin implementarlo, y sin fijar códigos —fijarlos antes de resolver la colisión de vocabulario
grabaría el error en el esquema—:

```
BusinessUnit          catálogo de producto, administrable
  id · code · name · is_active

CompanyBusinessUnit   nivel 2 · qué tiene habilitado la empresa
  company_id · business_unit_id · is_enabled · enabled_at · disabled_at

UserBusinessUnit      nivel 3 · qué se le concedió a la persona
  user_id · business_unit_id · granted_at · revoked_at
```

Y la regla:

```
efectivo(usuario) = habilitado(empresa)  ∩  concedido(usuario)
```

**Dos hechos y una intersección**, no un campo. Es lo único que permite el caso de `§29`:
módulo apagado en la empresa, concesión histórica intacta, acceso denegado — y reactivación sin
reconstruir nada.

**Deshabilitar nunca borra**: ni datos ni concesiones.

---

## 6. Dónde va la guarda

```
require_company()            existe
require_company_module()     falta
require_user_module()        falta
require_permission()         existe, y con guarda de arranque
propiedad / regla de negocio parcial
```

**No ruta por ruta.** Con 198 rutas, copiar la comprobación garantiza el olvido, y el olvido es
silencioso — que es lo que `authorization_coverage.py` vino a impedir para `RBAC`.

El filtro por unidad tiene que vivir **donde vive el de empresa**: en la construcción de las
consultas. Y ahí hay un problema previo que esta auditoría deja señalado:

```
El filtro de empresa NO está centralizado.
`MasterService` lo aplica para maestros; los demás servicios lo repiten a mano.
```

Un filtro de unidad seguiría ese camino y heredaría el mismo riesgo. Merecería la pena
centralizar los dos a la vez.

**Y la capa de servicio, no solo la de ruta**: los servicios se invocan también desde tareas de
fondo, que no tienen sesión. La comprobación por **empresa** puede vivir en el servicio; la
comprobación por **usuario** solo tiene sentido con sesión.

---

## 7. Sobre las certificaciones vigentes

```
NINGUNA se modifica.
```

Los catorce procesos certificados hacen lo que sus specs exigen. Lo que se propone es una
**segunda dimensión**:

```
CERTIFICACIÓN FUNCIONAL      14 / 15     sin cambios
CERTIFICACIÓN DE MÓDULO       0 / 15     no existía el requisito
```

Rebajar lo certificado porque aparece un requisito nuevo sería reescribir la historia.

---

## 8. Decisiones que quedan para el propietario

```
1. Los siete flujos entre unidades: qué ve cada lado, antes y después de transferir.
   (CROSS_MODULE_FLOW_MATRIX.md §3)

2. Eventos sin lote —inspecciones—: ¿de quién son?

3. Auditoría: ¿se ven registros de unidades que no se tienen?

4. `Analista SAP`: ¿excepción normativa al filtro por unidad?

5. Usuarios existentes tras la migración: ¿todos los módulos, ninguno, o configuración manual?

6. Lotes sin `bird_type`: ¿se ocultan a todos, o se completan?

7. ¿Quién asigna módulos a una empresa, y quién los concede a un usuario?
   (misma familia que `OD-05`, todavía abierta)

8. ¿Conviene separar «contratado» de «habilitado» para uso comercial?
   Hoy no existe ninguno de los dos; separarlos ahora es barato y después, caro.
```

La 1 y la 5 son bloqueantes: sin ellas, implementar rompe procesos certificados o deja la
operación parada.

---

## 9. Spec recomendada

```
¿spec existente?          ninguna cubre esto
¿nueva GA-REM?            SÍ
ID libre verificado       GA-REM-040    (el último es GA-REM-039)
```

No se crea aquí. Su alcance debería cubrir: catálogo de unidades · habilitación por empresa ·
concesión por usuario · resolución del efectivo · guarda central · filtro por fila ·
capacidades en la sesión · navegación · KPI y reportes · notificaciones · tareas de fondo ·
contratos entre unidades · auditoría · migración del legado · pruebas de seguridad `E2E`.

Y probablemente **no una sola spec**: el contrato entre unidades (`R-106`) es diseño de
producto y merece separarse de la mecánica de acceso.

---

## 10. Hoja de ruta recomendada

```
FASE 0   decisiones 1 y 5 del propietario          ← bloqueante, no técnico
FASE 1   catálogo + modelo de datos + migración vacía
FASE 2   resolución del efectivo + capacidades en /me
FASE 3   guarda central en la capa de consultas (empresa Y unidad a la vez)
FASE 4   filtro por fila en las 16 entidades compartidas
FASE 5   listados y contadores          ← cierra R-102
FASE 6   agregados, KPI y paneles       ← cierra R-103
FASE 7   buscadores y desplegables      ← cierra R-107
FASE 8   API de administración
FASE 9   interfaz: empresa y usuario
FASE 10  navegación y rutas
FASE 11  notificaciones y tareas de fondo
FASE 12  contratos entre unidades       ← depende de la FASE 0
FASE 13  migración del legado
FASE 14  E2E de seguridad + certificación de la nueva dimensión
```

El orden no es negociable en dos puntos: **la fase 0 va primera** —implementar antes de decidir
rompe cinco procesos certificados— y **los agregados no pueden ir después de la puesta en
producción**, porque una fuga por diferencia no deja rastro y nadie la reporta.

---

## 11. Veredicto

```
¿La arquitectura actual soporta aislamiento por empresa y usuario a nivel de módulo?

NO.

Existen 2 de las 5 capas necesarias.
Las dos que faltan no existen en absoluto — no están incompletas: no están.
```

```
MODO                          AUDITORÍA
CÓDIGO MODIFICADO             NINGUNO
DESARROLLO AUTORIZADO AHORA   NO
SIGUIENTE ACCIÓN              DECISIÓN DEL PROPIETARIO (bloqueantes 1 y 5), luego SPEC
```

Lo que sí conviene decir en positivo: la base sobre la que se construiría es sólida. El
aislamiento por empresa está certificado y probado; la autorización se lee de la base en cada
petición, de modo que la revocación sería inmediata; y existe una guarda de arranque que impide
olvidar una ruta. Lo que falta es una dimensión nueva, no un arreglo.
