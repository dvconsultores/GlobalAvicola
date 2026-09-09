# GLOBAL AVÍCOLA — AUDITORÍA MAESTRA DE SPEC / PRODUCTO

2026-09-08 · `HEAD = e245157` · **sin cambios de código**

---

## Resumen ejecutivo

**¿Estamos avanzando de verdad? PARCIALMENTE.**

El backend de procesos operativos es sólido y está genuinamente certificado. Tres guardas de
arranque impiden servir una ruta sin permiso, sin clasificación de unidad o fuera de
transacción, y las 207 rutas las cumplen. `GA-REM-040` construyó en siete fases un control de
acceso por cadena productiva con 179 pruebas y sensibilidad demostrada. Eso es trabajo real y no
está en discusión.

**Y aun así el producto no está donde las certificaciones sugieren**, por tres razones
distintas que conviene no mezclar:

**1 · Hay contradicciones con la spec en la superficie de administración.** `docs/02 §3.1.4`
declara el aislamiento multicompañía **CRÍTICO** y exige `WHERE company_id = ?` en *todas* las
consultas. `/users` no lo aplica —ni al listar, ni al leer, ni al editar—, y `/masters/companies`
tampoco, porque `Company` no tiene columna `company_id` y el filtro genérico es un no-op sobre
ella. Cuatro hallazgos `P0`. Ninguno estaba registrado; ninguno tiene test.

**2 · El frontend no implementa autorización en absoluto.** Cero comprobaciones de permiso en
28 pantallas. El menú es un array estático. `docs/02 §3.1.3` pide que el rol determine los
módulos accesibles y no ocurre. No es un agujero de seguridad —el backend deniega— pero sí un
producto que enseña a todos puertas que casi nadie puede abrir, y que confunde una denegación
con una lista vacía.

**3 · Tres de las diez preocupaciones del propietario no son defectos: son requisitos que nunca
se escribieron.** Compañías desde SAP, granjas desde SAP y módulos activables por empresa tienen
**cero** presencia en `docs/` y en `specs/`. El código hace exactamente lo que `docs/02 §3.2.1`
manda. No se puede acusar al software de incumplir una norma inexistente.

**¿Qué está técnicamente listo?** Aislamiento por fila y por agregado, contratos de traspaso,
clasificación pendiente, `RBAC` con guarda de cobertura, auditoría `P-09`, y las `API` de
administración de unidades.

**¿Qué está listo como producto?** Los procesos operativos de registro, revisión y aprobación.
La administración —usuarios, empresas, módulos, unidades— **no**.

**¿Debe continuar la fase 8?** **No todavía.** Ver la decisión al final.

---

## 1. La pregunta central, contestada

> ¿El software implementa la arquitectura de negocio de las specs, o hemos certificado
> componentes aislados mientras el producto integrado sigue incompleto?

**Las dos cosas, y en proporciones distintas según la capa.**

```
CAPACIDAD TÉCNICA     alta      lo certificado es cierto en su dimensión
CAPACIDAD DE PROCESO  alta      14/15 procesos funcionales certificados
CAPACIDAD DE PRODUCTO media     falta toda la administración multiempresa
CAPACIDAD DE UI       baja      sin autorización, sin pantallas de administración
CAPACIDAD DE RUNTIME  media     lo operativo funciona; lo administrativo no se puede usar
```

Las certificaciones históricas **no se invalidan**. `GA-REM-040` fase 3 certificó aislamiento
por fila y eso sigue siendo cierto. Lo que faltaba era alguien preguntando si la **suma** de
esas dimensiones era un producto, y esa pregunta no la hacía ninguna matriz.

**La causa raíz es de método, no de ejecución.** Cuarenta remediaciones contra dieciséis
documentos de producto. El trabajo se organizó alrededor de defectos encontrados en el código, y
nadie estaba recorriendo `docs/02` y `docs/10` renglón por renglón para ver qué no se había
construido nunca. Un defecto se ve; una ausencia, no.

---

## 2. Los quince gaps críticos

### `F-A` · `P0` · `/users` no filtra por empresa
- **Requisito:** `RQ-03` — `02 §3.1.4`, marcado CRÍTICO
- **Evidencia:** `AuthService.get_users` → `select(User)` sin `where` de empresa; `get_user` y
  `update_user` tampoco
- **Comportamiento actual:** quien tenga `users:read` enumera usuarios de todas las empresas
- **Esperado:** solo los de la empresa efectiva
- **Remediación existente:** ninguna · **Acción:** `GA-REM` nueva de aislamiento de `/users`

### `F-H` · `P0` · `update_user` cruza inquilinos y reasigna rol
- **Requisito:** `RQ-19`
- **Evidencia:** `select(User).where(User.id == user_id)` sin empresa; `UserUpdate.role_id` se
  aplica con `setattr` en bucle
- **Comportamiento:** con `users:update` se asigna a cualquier usuario de cualquier empresa un
  rol con comodín `("*", ...)` → Super Administrador
- **Esperado:** objetivo del propio inquilino; cambio de rol acotado
- **Acción:** misma `GA-REM` que `F-A`, prioridad máxima

### `F-B` · `P0` · `/masters/companies` no acota y expone `sap_config`
- **Requisito:** `RQ-03` · `RQ-07`
- **Evidencia:** `hasattr(Company, "company_id")` es falso → filtro no-op; `CompanyRead` incluye
  `sap_config`; `masters:read` lo tienen los cinco roles sembrados
- **Acción:** acotar por identidad (`Company.id == empresa efectiva`) y revisar la proyección

### `F-C` · `P0` · usuario sin empresa ve todos los maestros
- **Evidencia:** `if not self.user_company_id: return query` — el comentario del propio código
  admite que no se decidió («return empty or filter by id»)
- **Contraste:** `GA-REM-040` resolvió el mismo dilema **fail-closed** (`unidades_efectivas` → `[]`)
- **Acción:** decidir y cerrar en la misma remediación

### `F-G` · `P1` · `create_user` acepta `company_id` del cliente
- **Evidencia:** el router obtiene `current_user` y **no lo pasa** al servicio
- **Acción:** resolver la empresa, no recibirla — el patrón ya existe en `GA-REM-040` fase 7

### `F-D` · `P1` · el frontend no comprueba permisos
- **Requisito:** `RQ-25` — `02 §3.1.3`
- **Evidencia:** 0 ocurrencias de `hasPermission`/`usePermission` en `frontend/src`;
  `navigationConfig.ts` sin campo de permiso
- **Acción:** `GA-REM` de gating de navegación; depende de la fase 8 (`/me` con capacidades)

### `F-E` · `P1` · el error se traga y la tabla queda vacía
- **Evidencia:** `Promise.all` de cuatro llamadas + `catch { console.error }`
- **Consecuencia:** *«no tienes permiso»*, *«el backend cayó»* y *«no hay datos»* son idénticos
  en pantalla. **Es la explicación del `/users` vacío observado**
- **Acción:** contrato de error en la UI; barato y de alto retorno

### `F-I` · `P1` · los roles no se acotan por empresa
- **Evidencia:** `Role.company_id` existe; `get_roles` y `create_role` no lo usan
- **Acción:** decidir si el catálogo de roles es global (producto) o por inquilino

### `F-F` · `P1` · `OWNER_DECISION_REQUIRED` · origen de Empresas y Granjas
- **Evidencia:** `docs/10 §3.1` importa Centros, Almacenes, Materiales, Proveedores, Lotes;
  `docs/02 §3.2.1` lista Empresas y Granjas como catálogos base **locales**
- **Estado:** el código cumple la spec; **la spec no cumple la expectativa del propietario**
- **Acción:** decisión de propietario → nueva `OD` → luego spec → luego código

### `F-L` · `P1` · `OWNER_DECISION_REQUIRED` · módulos por empresa
- **Evidencia:** cero coincidencias en `docs/` y `specs/`; no existe `CompanyModule`
- **Aviso:** `RBAC` **no** lo sustituye. `Permission.module` dice qué hace una persona, no qué
  ha contratado una empresa
- **Acción:** decisión de propietario antes de cualquier diseño

### `R-113` · `P1` · `OWNER_DECISION_REQUIRED` · quién administra el acceso
- Abierto en la fase 7. **Su respuesta activa `F-A`, `F-G` y `F-H` el mismo día**, porque hoy
  esos defectos están latentes solo porque ningún rol sembrado concede `users:*`

### `F-J` · `P2` · falta la columna Empresa en `/users`
- `02 §3.1.2` la exige. El formulario sí la tiene; la tabla no

### `F-K` · `P2` · `Permission.scope_type` no se evalúa
- `tiene_permiso` compara `(módulo, acción)` y descarta el alcance salvo para detectar Super
  Admin. `02 §3.1.4` pide `all` / `company` / `farm`

### `R-112` · `P2` · ocho rutas `SAP` sin `response_model`
- Registrado y **no tocado**, según la orden de esta auditoría

### `BU-D10` · `OWNER_DECISION_REQUIRED`
- Sigue `PENDING_RATIFICATION`. **No tocado**

---

## 3. Reconciliación de certificaciones

**Ninguna certificación histórica se invalida.** Todas medían capacidad técnica o de proceso en
su dimensión, y siguen siendo ciertas ahí.

| Afirmación | ¿Sigue válida? | Matiz que faltaba |
|---|---|---|
| `GA-REM-040` fases 1–7 `COMPLETE` | **sí** | backend; fases 8 y 9 sin empezar → sin producto |
| Certificación funcional `14 / 15` | **sí** | mide procesos operativos, no administración |
| Acceso por unidad `0 / 15` | **sí** | y se mantiene en `0` |
| `GA-REM-002` cobertura de autorización | **sí** | garantiza que la ruta **declara** permiso, no que el filtro de empresa exista |
| `P-14` certificado | **sí** | no cubre `/users` |

**La lección de método:** las guardas verifican lo que se les pidió verificar. Ninguna vigila el
filtro de empresa, y por eso cuatro defectos `P0` convivieron con tres guardas de arranque y 687
pruebas en verde. Un guardián que asegura *«la ruta declara permiso»* no asegura *«la consulta
acota por inquilino»*.

---

## 4. Topología de las pruebas

```
ficheros de prueba backend      53      687 pruebas · 49 omitidas
ficheros de prueba frontend     11
E2E de navegador                 0
E2E de flujo por API             2      run_e2e_audit.py · test_full_workflow_audit.py
```

Las pruebas se concentran donde el producto ya era fuerte. **No hay una sola prueba de
aislamiento multiempresa sobre `/users`**, que es donde están tres de los cuatro `P0`.


---

## 5. Cierre de los cuatro `P0` (2026-09-08) — no reescribe lo anterior

**Qué cambió.** `GA-REM-002` enmienda B: `AC13` acota listado y detalle en la consulta, `AC14`
fija que el objetivo se resuelve dentro de la empresa antes de mutar, `AC15` impide fabricar
autoridad global desde una superficie de empresa, `AC16` hace que una denegación se vea como
tal. Rojo demostrado antes del código —9 de 13—, 9 mutaciones de sensibilidad, `E2E` de ataque
completo. Backend 708 · frontend 87. Sin migración.

**Por qué escapó, con precisión.** No fue descuido de quien implementó `AC05`: fue que
`TENANT_RESOURCE_CLASSIFICATION.md` —la lista que convierte esa `AC` en sitios concretos— se
construyó desde el modelo operativo y **`users` nunca entró**. Una `AC` correcta con una lista
de aplicación incompleta abre exactamente el mismo agujero que no tener la `AC`.

**Qué queda abierto, y no se cierra por vecindad.**

```
R-115   `/masters/companies` sin acotar · expone `sap_config` · P0 · ABIERTO
R-116   `MasterService` fail-open sin empresa · cerrado en `/users`, ABIERTO en maestros
R-119   el frontend sigue sin comprobar permisos en 27 de 28 pantallas
R-120   generalizar los cinco estados al resto de pantallas
R-121   qué roles ordinarios puede asignar un administrador · OWNER_DECISION
R-126   ¿debe `switch-company` acotar también a la autoridad global? · OWNER_DECISION
```

`RQ-03` sigue `PARTIAL` por `R-115` y `R-116`. Arreglar `/users` no certifica «todas las
queries».

**Lo que sí se corrigió del método.** Dos mutaciones me corrigieron a mí: una estaba rota
—referenciaba un parámetro inexistente y fallaba por `NameError`, no por la mutación— y otra
sobrevivió dos veces porque la prueba que escribí para detectarla prometía en su descripción
algo que su código no hacía. Las dos quedan contadas en la evidencia. Sin ese rigor, `§41`
habría quedado afirmado y no demostrado.


---

## 6. `R-115` y `R-116` cerrados · `RQ-03` sigue `PARTIAL` (2026-09-08)

**Qué cambió.** `MasterService._apply_company_filter` cubre sus dos huecos: `Company` se acota
por su propia clave primaria —es el inquilino— y el actor sin empresa efectiva recibe cero
filas. Un solo punto cierra listado, detalle, edición y baja. Sin `GA-REM` nueva: `RQ-03` y
`AC05` ya lo gobernaban.

**Lo que se corrigió del método.** `TENANT_RESOURCE_CLASSIFICATION.md` se ha rehecho **desde
`Base.metadata`**, no desde la lista anterior: 54 recursos, cero sin clasificar, con un paso
final que **falla ruidosamente** si aparece una tabla que no encaja. Ésa es la diferencia entre
una lista de lo que alguien miró y una del universo.

**Y una corrección a esta misma auditoría.** `R-115` afirmaba que `/masters/companies` exponía
`sap_config`. La exposición estaba **latente detrás de un 500** —columna `String` validada como
`dict`—, de modo que el campo nunca llegaba a viajar. Lo alcanzable era la fuga de la fila
entera. Queda `R-127` registrado y la redacción corregida en el backlog.

**`RQ-03` no pasa a `COMPLETE`.** Faltan `roles` y `permissions`, bloqueados por `R-121`, que es
decisión de propietario: si el catálogo de roles es de producto, no filtrar es correcto; si es
de inquilino, hay que acotarlo.

**`R-126`** queda documentado como expediente de decisión, sin una línea de código. La
incoherencia que lo justifica es concreta y no estética: la administración de unidades de la
fase 7 **sí** exige empresa efectiva, mientras `/users` y `/masters` no. Dos superficies del
mismo plano de control con dos respuestas a la misma pregunta.


---

## 7. `R-121` y `R-126` cerrados · `RQ-03` = `COMPLETE` (2026-09-08)

**`OD-13`** decide que el permiso es capacidad de producto y el rol tiene alcance. La columna
`Role.company_id` existía desde el principio, nulable: lo que faltaba no era poder expresar el
alcance, era usarlo. Sin migración.

**`OD-14`** decide que cada superficie declara su clase, sin clase por omisión. Cambia el
comportamiento del Super Administrador —ahora elige empresa para operar sobre datos de
inquilino— y preserva `docs/02 §3.1.4` donde la frase tenía sentido: el catálogo de empresas.

**Tres pruebas certificadas cambiaron de expectativa, deliberadamente y documentadas.** Las tres
eran el mismo patrón: aprovisionar en la empresa 2 estando situado en la 1. Ahora usan
`switch-company`. Ninguna se debilitó — y arreglar `_usuario` en origen destapó que los usuarios
«de la empresa ajena» nacían en la propia, un defecto de fixture que se presentaba como fuga de
notificaciones.

**`RQ-03` pasa a `COMPLETE`** tras recorrer los 54 recursos, no por transitividad. Las cinco
excepciones están nombradas y justificadas.

**Lo que sigue abierto** —`R-127`, `R-119`, `R-120`, `R-112`— no es aislamiento de inquilino, y
se enumera para que `COMPLETE` no se lea como «no queda nada».

**`R-113` queda `READY_TO_RESUME`** con una pregunta de segregación abierta: quien reparte
accesos puede dárselos a sí mismo dentro de su empresa. Acotado, visible y auditado — pero es
decisión de propietario, no cambio silencioso.


---

## 8. Fase 8 cerrada · `R-129` cerrado · la fase 9 tiene un bloqueo con nombre (2026-09-09)

**Lo que se cerró.** La sesión entrega los cuatro conceptos de `§14.1` compuestos desde los
resolutores centrales, con `is_super_admin` canónico y sin sinónimo. Y el `Administrador de
Accesos` ya puede saber a quién conceder sin `users:read` — con prueba de que sigue sin poder
listar usuarios, que es el contraste que hace honesta la superficie.

**Lo que el preflight destapó.** La fase 9 no puede empezar. No por acumulación de riesgos, sino
por una causa exacta: el selector de empresa del frontend lee de `GET /masters/companies`, esa
ruta devuelve `500` en cuanto una empresa tiene SAP configurado (`R-127`), y la sesión no expone
empresas a propósito porque `§14.1` no lo pide. La decisión correcta de la fase 8 hace visible
el hueco en vez de taparlo.

**Lo que no se hizo con `R-127`.** Ni ignorar `sap_config`, ni capturar el `500`, ni ocultar las
empresas configuradas, ni meter la lista en la sesión sin norma. Todo eso escondería el defecto.
`R-127` necesita tanda propia y una decisión pequeña pero real del propietario.

**Un error de método, corregido a la vista.** Un commit de `R-129` se hizo con la regresión en
rojo por un conteo de rutas desactualizado —mío, de la fase 7— y con una cifra falsa en el
mensaje. Se rectificó en un commit posterior en lugar de reescribir historia, y la regresión se
repitió entera antes del push. Leer antes de escribir.
