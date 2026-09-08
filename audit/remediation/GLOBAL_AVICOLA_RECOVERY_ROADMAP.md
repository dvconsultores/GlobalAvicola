# HOJA DE RUTA DE RECUPERACIÓN

Auditoría maestra · 2026-09-08 · ordenada **por dependencia**, no por número de fichero

```
DECISIÓN B
CONGELAR GA-REM-040 FASE 8
EJECUTAR PRIMERO LA RECUPERACIÓN DE FUNDAMENTO
```

---

## Por qué B y no A

La fase 8 entrega **capacidades en la sesión**: `/me` diría qué unidades y qué permisos tiene el
usuario, para que la fase 9 dibuje la interfaz. Es buen trabajo y está bien situado en su propia
hoja de ruta.

Pero hay dos razones concretas para no empezarla ahora, y ninguna es de gusto:

**1 · La fase 8 alimenta a un frontend que no comprueba permisos.** Entregar capacidades a una
interfaz con cero `hasPermission` no cambia nada observable: el menú seguirá dibujándose entero.
Se construiría el contrato antes que su consumidor, y la fase 9 tendría que rehacerlo cuando se
decida el gating.

**2 · La respuesta a `R-113` activa cuatro `P0` el mismo día.** `F-A`, `F-G` y `F-H` están
latentes **solo** porque ningún rol sembrado concede `users:*`. `R-113` pregunta quién administra
en una avícola; en cuanto el propietario conteste y alguien cree ese rol, tendrá un
administrador capaz de enumerar todas las empresas, crear usuarios en cualquiera de ellas y
asignarse Super Administrador. Construir la fase 8 encima de eso es apilar sobre un cimiento que
ya sabemos roto.

---

## Orden

### `1` · Aislamiento de inquilino en la administración — **bloqueante, `P0`**

`F-A` · `F-B` · `F-C` · `F-G` · `F-H`. Una sola remediación: los cinco son la misma ausencia —el
filtro de empresa nunca llegó a la superficie de administración— y arreglarlos por separado
repetiría el análisis cuatro veces.

```
`/users` listar · leer · editar     acotar a la empresa efectiva
`create_user`                       resolver la empresa, no recibirla
`update_user`                       objetivo del propio inquilino · `role_id` acotado
`/masters/companies`                acotar por identidad de empresa
sin empresa y sin ser super admin   decidir explícitamente: fail-closed
```

Con pruebas de aislamiento y mutación de sensibilidad, como las siete fases anteriores. **El
patrón ya existe en la casa** — `GA-REM-040` fase 7 y `app/tenancy.py`—, así que esto es
aplicar una regla escrita, no inventarla.

### `2` · Las tres decisiones de propietario — **en paralelo, no bloquean el `1`**

```
F-F     ¿Empresas y Granjas vienen de SAP?  ¿Con qué objeto?  ¿Réplica o copia con extensión?
F-L     ¿El producto se vende por módulos contratables, o basta el `RBAC`?
R-113   ¿Quién administra el acceso por unidad?  ¿Puede concederse a sí mismo?
```

Sin `F-F` no se puede escribir la spec de maestros. Sin `F-L` no se puede diseñar el
entitlement. Sin `R-113` no hay a quién dar los permisos que el paso `1` acaba de acotar.

**Ninguna la decide quien implementa.**

### `3` · Contrato de error y columna de empresa en la interfaz — `P1`, barato

`F-E` y `F-J`. Que una denegación se vea como una denegación. Es lo que convirtió un `403` en
«no hay usuarios» y costó esta auditoría entera.

### `4` · `GA-REM-040` fase 8 — sesión y capacidades

Ahora sí: con el inquilino acotado y `R-113` contestado, `/me` puede decir qué unidades y qué
capacidades tiene el usuario **con la certeza de que esas capacidades están bien acotadas**.

### `5` · Gating de navegación en el frontend — `F-D`

Consume la fase 8. Antes de ella no hay contrato del que tirar.

### `6` · `GA-REM-040` fase 9 — interfaz de unidades y clasificación

`T-040-21`…`T-040-24`. Convierte en producto lo que las fases 1–7 dejaron en backend.

### `7` · Lo que quede de las decisiones del paso `2`

Origen de maestros y módulos por empresa, si el propietario los confirma. Modelo, migración,
guarda y pantalla — pero solo después de que exista la norma.

### `8` · `R-112`, `F-I`, `F-K` — `P2`

Proyecciones `SAP`, alcance de roles por empresa, y `scope_type`. Registrados, sin urgencia.

---

## Lo que esta hoja de ruta **no** cambia

```
P-08      BLOCKED_EXTERNAL          no depende de nosotros
BU-D10    PENDING_RATIFICATION      sigue esperando al propietario
14 / 15   certificación funcional   los procesos operativos siguen certificados
0 / 15    acceso por unidad         y sigue en cero
```

---

## Una nota sobre el método, que es lo que falló

El programa encontró y corrigió cuarenta remediaciones con un rigor que se sostiene: mutaciones
de sensibilidad, control y tratamiento, negativa a certificar por transitividad. Nada de eso
sobra.

Lo que faltó fue **una lectura de `docs/02` y `docs/10` renglón por renglón contra el código**.
El trabajo se organizó alrededor de defectos observados, y un defecto se ve mientras que una
ausencia no. Cuatro `P0` convivieron con tres guardas de arranque y 687 pruebas verdes porque
ninguna guarda vigila el filtro de empresa y ninguna prueba lo pedía.

La recomendación que sobrevive a esta auditoría concreta: **una guarda que exija filtro de
inquilino en toda consulta sobre modelo con `company_id`**, del mismo estilo que
`authorization_coverage` y `route_scope`. Es la clase de comprobación que habría convertido
`F-A` en un fallo de arranque el día que se escribió.
