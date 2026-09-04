# WAVE 2 — EXECUTION REPORT

**Global Avícola** · Remediación de defectos de runtime · Integridad del dato · Seguridad ·
Flujos críticos de negocio

**Fecha** 2026-09-04 · **Commit base** `bfccdfb` · **Estado** `COMPLETE`

---

# 1. Executive Summary

```
STAGE 0  R-28  determinismo temporal ............ CERTIFIED
STAGE 1  P0-14 persistencia de operaciones ...... CERTIFIED  (GA-REM-023)
STAGE 2  R-26  contrato de error de negocio ..... CERTIFIED  (GA-REM-023)
STAGE 3  P0-13 cambio de contraseña ............. CERTIFIED  (GA-REM-012)
STAGE 4  GA-REM-005 mortalidad .................. PARTIALLY CERTIFIED
STAGE 5  GA-REM-002/003 seguridad ............... IMPLEMENTED ⚠ prerrequisito R-44
STAGE 6  GA-REM-006 correcciones ................ CERTIFIED
STAGE 7  GA-REM-007 BR-14 ....................... CERTIFIED
STAGE 8  GA-REM-008 trazabilidad ................ CERTIFIED
STAGE 9  regresión completa ..................... 211 / 211
STAGE 10 certificación de la Wave ............... este documento

Suite backend    74 PASS / 26 FAIL   ->   211 PASS / 0 FAIL
P0 abiertos      10                  ->   0
P1 abiertos      16                  ->   4
Rutas con autorización declarada   0/78   ->   177/177
Hallazgos nuevos descubiertos en runtime ......... 16
Regresiones introducidas por la Wave 2 ........... 0
git push / release / deploy / tag ................ 0
```

**La suite backend está entera en verde por primera vez en la historia del proyecto**, y lo
está con el calendario adelantado dos años, no solo hoy.

Lo más importante de esta Wave no son los defectos corregidos sino **los que aparecieron al
corregirlos**. Tres P0 —el 25.º tipo de evento inutilizable, los lotes de incubadora
imposibles de crear, y la renovación de sesión que nunca funcionó— llevaban meses en el
producto y ninguna lectura de código los habría encontrado. Aparecieron porque la suite por
fin ejercita el sistema.

---

# 2. Baseline de la Wave 1.5

```
26 failed · 74 passed · 1 skipped        (RUN 05, congelado)
P0 abiertos ..... 10
P1 abiertos ..... 16
RC abiertos ..... 2   (RC-04 técnico · RC-07 acotado)
```

El orden de la Wave 2 no se tomó de la numeración `GA-REM` sino del riesgo: tiempo →
integridad → seguridad → defecto transversal → criticidad de negocio.

---

# 3. `R-28` — determinismo temporal · Stage 0

**Por qué primero:** era el único trabajo con fecha límite dura. `BR-19` cierra los períodos
a 90 días y la suite fijaba fechas literales de junio de 2026; a partir del **2026-09-21**
decenas de tests en verde habrían empezado a fallar solos, y la línea base habría dejado de
ser reproducible.

**Qué se hizo:** un reloj de referencia único (`tests/time_reference.py`) del que derivan las
31 fechas literales que había; cobertura de `BR-19` en sus tres regiones, que **no existía**;
y una simulación honesta del calendario (`tests/simulated_clock.py`) que adelanta el reloj
de **todo el proceso**, aplicación incluida.

Se descartó una primera solución que solo desplazaba las fechas del lado del test: con la
referencia a `hoy − 30` los tests de frontera fallaban porque `BR-19` seguía midiendo contra
el día real. Un override así no prueba nada y permite ejecuciones engañosas.

**Resultado:** la suite da el mismo resultado con el calendario en 2026, 2027, 2028 y 2031.

`BR-19` no se tocó. El defecto estaba en los tests.

---

# 4. `P0-14` — persistencia de operaciones · Stage 1

**El defecto:** `create_event` construía el modelo con una lista escrita a mano de 11 campos
frente a los 22 que el contrato declara. Los otros 14 se aceptaban, se devolvían como `null`
y **nunca se guardaban**. Entre ellos `cause_id`, la causa de la mortalidad que el cliente
exige literalmente («Mortalidad — Cantidad, causa»), y también proveedor, vacuna, vía de
aplicación, medicamento, destino y transporte.

**La corrección no fue añadir 14 asignaciones.** El defecto no era que faltaran: era que
*fuera posible* que faltaran. Cualquier campo añadido después se habría perdido igual y en
silencio. La asignación se deriva ahora del propio contrato, y dos tests estructurales
impiden que la clase de fallo reaparezca.

**Hallazgos nuevos del Stage 1:**

| ID | Hallazgo | Sev. |
|---|---|---|
| **`R-32`** | `PUT /operations/{id}` permitía fijar `status`: cualquier usuario autenticado aprobaba cualquier evento, sin revisión, sin segregación y dejando `approved_by_id` **nulo** — un evento aprobado sin aprobador | **P0** |
| `R-34` | Los campos operativos tampoco eran editables antes de enviar a revisión | P1 |

Matriz completa: `OPERATION_FIELD_PERSISTENCE_MATRIX.md`.

---

# 5. `R-26` — contrato de error de negocio · Stage 2

Ocho de las trece reglas que puede violar una creación de evento se evaluaban **fuera** del
único `try/except` que las traducía. Salían sin manejar y llegaban al cliente como
`500 Internal Server Error`:

```
bird_reception sin farm_id       -> HTTP 500  Internal Server Error
mortality_recording sobre saldo  -> HTTP 400  {"detail":"Mortalidad (999999) excede..."}
```

El operador que olvidaba la granja veía «Internal Server Error» en lugar del motivo, y las
reglas contaminaban cualquier métrica de 5xx.

**Se resolvió con un manejador tipado**, no con siete parches ni con `except Exception`:
capturar de más habría escondido defectos reales, que es peor que el problema original. El
`try/except` local se retiró para que exista **un solo** contrato `{detail, rule}` para las
23 reglas y para las que se añadan.

`T-028-03b`, el test que el Stage 0 dejó deliberadamente en rojo con la aserción correcta,
pasó a verde aquí. Era su propósito.

---

# 6. `P0-13` — cambio de contraseña · Stage 3

`PUT /users/{id}` con `{password}` devolvía `200`, la interfaz mostraba «contraseña
actualizada» y **la anterior seguía autenticando**. Toda rotación de credencial tras una
sospecha de compromiso era ficticia.

Endpoint dedicado `POST /users/{id}/password`, con dos caminos deliberadamente distintos: el
titular aporta su contraseña actual; un administrador restablece sin conocerla. `UserUpdate`
declara ahora `extra="forbid"`, de modo que enviar `password` allí produce un `422`
explícito en lugar de un `200` que no hace nada — la misma clase de fallo silencioso que
`P0-14`, cerrada por contrato.

Política `RR-05` aplicada de forma única: longitud mínima **8** en alta, cambio y
restablecimiento. El frontend pasó de 6 a 8 y envía ahora la contraseña actual, que ya
recogía y no usaba.

`T-012-08` documenta un comportamiento que conviene no descubrir en producción: los JWT son
sin estado y **las sesiones previas siguen vivas hasta expirar**. Un usuario que rota su
contraseña tras una sospecha espera lo contrario. La revocación pertenece a `GA-REM-003`; el
test fija el comportamiento actual para que el cambio sea visible cuando llegue.

---

# 7. `GA-REM-005` — mortalidad · Stage 4

`P0-1` impedía registrar **cualquier** mortalidad válida: `get_current_bird_balance` no
estaba importada y se la llamaba con tres argumentos en lugar de dos. El `NameError` salía
como 500 después de haber persistido el evento. La suite no lo veía porque su único test de
mortalidad usaba una cantidad desorbitada que `BR-01` rechazaba antes.

Se reconstruyó el flujo completo, y en el camino aparecieron cuatro defectos más:

| ID | Hallazgo | Sev. |
|---|---|---|
| **`R-40`** | `EGG_RECEPTION_CLASSIFICATION` estaba en el enum de Python desde junio y **no en el tipo `eventtype` de PostgreSQL**. El 25.º tipo de evento era inutilizable | **P0** |
| **`R-41`** | `birdtypeenum` tenía `'hatchery'` en minúsculas mientras SQLAlchemy persiste el nombre del miembro, `'HATCHERY'`. **Ningún lote de incubadora podía crearse** | **P0** |
| `R-38` | `GET /operations/alerts` era **inalcanzable**: se declaraba después de `/{event_id}`, que lo capturaba. El frontend lo usa en dos pantallas, de modo que las alertas nunca se mostraron | P1 |
| `R-39` | Una mortalidad de **cero aves se aceptaba con 201**: `validate_mortality` solo se invocaba `if total_qty > 0` | P1 |

`R-40` y `R-41` compartían escondite: **la comprobación de deriva de esquema comparaba
tablas y columnas, no valores de tipos enumerados**. Se amplió, y el comprobador ampliado
encontró `R-41` inmediatamente después de corregir `R-40`.

`AC08` (umbral de mortalidad configurable por empresa) queda **diferido con motivo**: exige
una columna nueva y ningún hallazgo lo requiere. Por eso el estado es `PARTIALLY CERTIFIED`
y no `CERTIFIED`.

---

# 8. Cluster de seguridad · Stage 5

Las 78 rutas del backend comprobaban únicamente que hubiera sesión. El modelo de permisos
existía, los roles se sembraban con sus permisos, y **nada los leía**. El único control
efectivo era que la interfaz no mostrara el botón.

- **170 de 177 rutas** declaran ahora su permiso; las 7 restantes son públicas con motivo.
- **`AC08`**: una comprobación al arrancar aborta si alguna ruta no ha decidido su
  autorización. Localizó dos rutas que se habían escapado en cuanto se activó.
- **`R-36`**: el filtro de compañía era `and self.company_id` — un usuario **sin** compañía
  no recibía filtro y veía los eventos de todas las empresas. Fail-open.
- **`R-43`** *(P0 nuevo)*: `refresh_token` comparaba `sub` (cadena) con `User.id` (entero).
  PostgreSQL rechazaba la comparación y **el refresco nunca funcionó**: toda sesión moría a
  los 30 minutos sin posibilidad de renovarla.
- **`GA-REM-003`**: `login` y `refresh` comparten ahora un único constructor de claims que
  **reconstruye desde la base**. La renovación recoge así los cambios de rol o compañía en
  vez de arrastrar el estado del login.

## ⚠ `R-44` — prerrequisito de despliegue, bloqueante

Al contrastar lo que exigen las rutas con lo que conceden los roles reales:

```
pares exigidos por rutas .................. 29
concedidos por los roles reales ........... 16
exigidos que NINGÚN rol concedía .......... 18
```

Entre ellos **`masters:read`, requerido por 40 rutas**. Mientras nada comprobaba los
permisos, las definiciones de rol podían estar incompletas sin que se notara; con el
enforcement activo, **la aplicación quedaría inservible para todo usuario que no sea Super
Admin**.

Las definiciones se completaron en las semillas y un test impide que la brecha reaparezca,
pero **la base de producción conserva los permisos antiguos**. Desplegar el enforcement sin
actualizarla primero dejaría fuera a todos los operadores. Por eso `GA-REM-002` queda
`IMPLEMENTED` y no `CERTIFIED`: el código está completo y verificado; la condición del
entorno, no.

---

# 9. `GA-REM-006` — correcciones · Stage 6

`P0-2`: se creaba el registro de corrección, se cambiaba el estado a `CORRECTED` y **no se
escribía nada**. El dato erróneo era el que se aprobaba, el que alimentaba los KPI y el que
se consolidaba hacia SAP.

Dos decisiones merecen mención:

- **Lista blanca** de 20 campos corregibles. `field_name` lo elige el cliente: un `setattr`
  sobre lo que llegue permitiría corregir `status` o `approved_by_id` — la misma escalada
  que `R-32`.
- **`original_value` lo lee el servidor** del propio dato, ignorando el del *payload*. Si lo
  aporta quien corrige, la auditoría deja de ser evidencia y pasa a ser una declaración. Un
  test lo comprueba enviando una mentira deliberada.

---

# 10. `GA-REM-007` — `BR-14` · Stage 7

Tres vías de saltarse la segregación de funciones: `complete_review` no la comprobaba,
`approve` ignoraba la bandera de configuración, y `PUT /operations/{id}` permitía fijar el
estado sin pasar por ninguna (`R-32`, ya corregido).

Extraída a `SegregacionMixin`. **Una regla de control interno aplicada en un sitio y ausente
en otro no es un control: es una casualidad.**

`test_f4_approve_event` registraba y aprobaba con el mismo cliente. Al aplicarse la regla,
falló. La lectura correcta no es que la regla estorbe: es que el test **comprobaba que la
regla no existiera**. Se corrigió usando dos identidades reales; la regla quedó intacta.

---

# 11. `GA-REM-008` — trazabilidad · Stage 8

El emparejamiento exigía que despacho y recepción compartieran `lot_id`. Por definición del
dominio no lo comparten. **Nunca se creaba ningún vínculo**, y de coincidir se habría creado
un lote enlazado consigo mismo.

**`RC-04` resuelto por evidencia estructural** (`RR-04`): `EggBatch` tiene **dos** columnas
de lote porque son dos lotes distintos; «el mismo lote de huevos» designa el lote físico, no
un identificador compartido. Mismo argumento que resolvió `RC-02`.

El emparejamiento usa ahora el **destino que el operador declaró**
(`destination_farm_id` / `destination_plant_id`) — utilizable solo desde que `P0-14` lo
persiste. Sin destino declarado no se crea vínculo: `spec.md §4.9` ya contempla el enlace
manual, y adivinar la correspondencia sería peor que no establecerla.

---

# 12. Hallazgos nuevos de runtime

| ID | Hallazgo | Sev. | Estado |
|---|---|---|---|
| `R-32` | `PUT /operations/{id}` aprobaba sin flujo ni aprobador | **P0** | **corregido** |
| `R-40` | 25.º tipo de evento ausente del enum de PostgreSQL | **P0** | **corregido** |
| `R-41` | `birdtypeenum` con `'hatchery'` en minúsculas | **P0** | **corregido** |
| `R-43` | El refresco de sesión nunca funcionó | **P0** | **corregido** |
| `R-26` | 7 reglas de negocio devolvían 500 | P1 | **corregido** |
| `R-36` | Filtro de compañía fail-open | P1 | **corregido** |
| `R-38` | Endpoint de alertas inalcanzable | P1 | **corregido** |
| `R-39` | Mortalidad de cero aves aceptada | P1 | **corregido** |
| `R-34` | Campos operativos no editables antes de revisión | P1 | **corregido** |
| `R-27` | Configuración ausente reportada como 500 | P2 | **corregido** |
| `R-30` | `BR-19` admitía fechas futuras | P2 | **corregido** |
| **`R-44`** | Catálogo de permisos de producción incompleto | **bloqueante** | **abierto** — prerrequisito de despliegue |
| `R-42` | `get_current_bird_balance` no filtra por compañía | P1 | abierto → `GA-REM-019` |
| `R-45` | Corregir `event_date` no revalida `BR-19` | P2 | abierto → `GA-REM-016` |
| `R-46` | No se puede corregir un submovimiento | P2 | abierto → `GA-REM-019` |
| `R-47` | `POST /lots` ignora el `start_date` recibido | P1 | abierto → `GA-REM-019` |
| `R-33`, `R-35`, `R-24`, `R-25` | `extra_data` sin forma, 201 en deduplicación, transferencia sin validar galpón, edición del perfil propio | P2/P3 | abiertos → `GA-REM-019` |

**Distinción exigida por el encargo:** los 16 son
`NEWLY_DISCOVERED_EXISTING_DEFECT`. **`REGRESSION_INTRODUCED_BY_REMEDIATION`: 0.**

---

# 13. Backend test baseline vs final

| Metric | Baseline Run 01 | Wave 2 Final | Delta |
|---|---:|---:|---:|
| Collected | 101 | **211** | +110 |
| PASS | 29 | **211** | +182 |
| FAIL | 6 | **0** | −6 |
| ERROR | 66 | **0** | −66 |
| SKIP | 0 | **0** | — |

Detalle en `BACKEND_TEST_WAVE_2_FINAL.md`. `BACKEND_TEST_BASELINE_RUN_01.md` **no se
sobrescribió**.

Determinismo comprobado con tres calendarios: `211 passed` en los tres.

---

# 14. Frontend regression

```
TypeScript (tsc) ....... PASS
Vitest ................. PASS  61/61
Paridad i18n ........... PASS  ES=866  EN=866  faltantes=0
```

Cambios en el frontend, todos derivados de `P0-13`: `ProfilePage` usa el endpoint dedicado,
envía la contraseña actual que ya recogía y aplica la política de 8; `UsersPage` deja de
mandar la contraseña en el cuerpo de edición y de propagar el usuario entero en el
interruptor de activación.

---

# 15. Database integrity

```
Cadena Alembic ......... 1 head (k1l2m3n4o5p6) · 1 base
Deriva de tablas ....... 0   (modelo 47 = migraciones 47)
Deriva de enums ........ 0   (16 enums, comprobación NUEVA)
Migraciones creadas .... 2   ambas necesarias y verificadas antes de escribirlas
```

Las dos migraciones (`R-40`, `R-41`) son aditivas e idempotentes. `P0-14` **no requirió
ninguna**: los 14 campos ya existían en el modelo y en la base, verificado contra
`information_schema` antes de tocar código.

---

# 16. P0 — antes y después

| Momento | P0 abiertos |
|---|---:|
| Auditoría inicial | 12 |
| Tras Wave 1 | 8 |
| Tras Wave 1.5 | 10 |
| **Tras Wave 2** | **0** |

La Wave 2 cerró los 10 que había y los 3 que descubrió. El repunte de la Wave 1.5 no fue un
retroceso sino mejor detección; el descenso de ahora tampoco es cosmético: cada cierre tiene
test que lo respalda.

# 17. P1 — antes y después

| Momento | P1 abiertos |
|---|---:|
| Auditoría inicial | 16 |
| Tras Wave 1 | 13 |
| Tras Wave 1.5 | 16 |
| **Tras Wave 2** | **4** — `R-42`, `R-44`, `R-45`, `R-47` |

---

# 18. Requirement conflicts abiertos

| RC | Estado |
|---|---|
| `RC-01`, `RC-02`, `RC-03`, `RC-05` | resueltos por evidencia en la Wave 1.5 |
| **`RC-04`** | **resuelto por evidencia en la Wave 2** (`RR-04`) |
| `RC-07` | `OWNER_DECISION_REQUIRED`, acotado por `RR-07`: bloquea solo el mapeo SAP de mortalidad dentro de `GA-REM-017` |

**No queda ningún `RC` bloqueando trabajo técnico.**

---

# 19. Bloqueos externos que continúan

| Bloqueo | Afecta | Acción |
|---|---|---|
| Contrato técnico SAP | `GA-REM-017` | solicitar al cliente |
| `OD-02` (`RC-07`) | mapeo SAP de mortalidad | decisión contable del propietario |
| **`R-44`** | despliegue del enforcement RBAC | completar el catálogo de permisos en producción |

---

# 20. E2E readiness

**No se ejecutó E2E y la cobertura no se movió**: sigue en `12 / 60 = 20 %`. El encargo lo
prohíbe expresamente y aumentarla sin certificación real sería falsear el indicador.

```
BACKEND TEST PASS  ≠  E2E CERTIFIED
```

Lo que sí cambió es la base sobre la que apoyarse: los flujos que `GA-REM-016` debe
certificar —registrar, revisar, corregir, aprobar, consolidar— **funcionan y están cubiertos
por test de integración** por primera vez. Antes de esta Wave, tres de ellos no podían
completarse en absoluto.

**Veredicto: listo para iniciar `GA-REM-016`**, con una condición: `R-44` debe resolverse
antes, o la certificación E2E se haría contra un sistema que en producción no dejaría entrar
a los roles que los procesos requieren.

---

# 21. Recomendación para la Wave 3

| # | Trabajo | Motivo |
|---|---|---|
| 1 | **`R-44`** — catálogo de permisos en producción | bloqueante de despliegue y de la certificación E2E |
| 2 | `GA-REM-016` — certificación E2E y de procesos | es el único camino al nivel de madurez 4 |
| 3 | `GA-REM-011` — 8 desajustes de contrato restantes | diferidos por alcance desde la Wave 1 |
| 4 | `GA-REM-021` (agua) · `GA-REM-022` (KPI) | reevaluados: ya no compiten con ningún P0 |
| 5 | `GA-TD-039` / `GA-TD-040` — observabilidad y respaldo | **prioridad al alza.** Con `EX-01` (despliegue automático aceptado), la ausencia de observabilidad es lo que hace que un despliegue defectuoso pase inadvertido. `R-26` demuestra el punto: siete reglas devolvían 500 y nadie lo supo |
| 6 | `GA-REM-019` — deuda P2/P3 | acumula 9 hallazgos nuevos de esta Wave |
| 7 | `GA-REM-017` — SAP real | sigue `BLOCKED_EXTERNAL` |

---

# 22. Evidence index

| Documento | Contenido |
|---|---|
| `R-28-CERTIFICATION-REPORT.md` | determinismo temporal |
| `OPERATION_FIELD_PERSISTENCE_MATRIX.md` | matriz schema → model → service → DB → response |
| `GA-REM-023-CERTIFICATION-REPORT.md` | `P0-14`, `R-26`, `R-27`, `R-30`, `R-32`, `R-34` |
| `GA-REM-012-CERTIFICATION-REPORT.md` | `P0-13` |
| `GA-REM-005-CERTIFICATION-REPORT.md` | mortalidad, `R-38`…`R-41` |
| `GA-REM-002-003-CERTIFICATION-REPORT.md` | cluster de seguridad, `R-43`, `R-44` |
| `GA-REM-006-007-CERTIFICATION-REPORT.md` | correcciones y `BR-14` |
| `GA-REM-008-CERTIFICATION-REPORT.md` | trazabilidad, `RC-04` |
| `BACKEND_TEST_WAVE_2_FINAL.md` | comparativa contra la línea base |
| `BACKEND_TEST_BASELINE_RUN_01.md` | **congelado, no sobrescrito** |
| `REQUIREMENT_CONFLICT_RESOLUTION.md` | `RR-01`…`RR-05`, `RR-07`, **`RR-04`** |
| `MASTER_REMEDIATION_MATRIX.md` · `DEPENDENCY_MAP.md` · `REMEDIATION_BACKLOG.md` | actualizados |

---

# 23. Verificación de alcance — `EX-01`

| Elemento | Estado |
|---|---|
| `watchtower` | **6 referencias, intactas** |
| `pull_policy: always` | **3 referencias, intactas** |
| Etiqueta `:latest` | **3 referencias, intactas** |
| Workflows de despliegue | **5, sin cambios** |
| `git push` / `release` / `deploy` / `tag` | **0** |

El único cambio en `docker-compose.yml` es el de la Wave 1 (`GA-REM-004`, `GA-REM-009`): no
toca ni Watchtower, ni `:latest`, ni `pull_policy`.

---

# 24. Lo que esta Wave costó y lo que compró

**Costó:** dos migraciones de esquema, un cambio de contrato de error que altera códigos HTTP
de 500 a 400, y un enforcement de autorización que **no puede desplegarse hasta completar el
catálogo de permisos en producción**.

**Compró:** la mortalidad se puede registrar —no se podía—; el 25.º tipo de evento y los
lotes de incubadora existen —no existían—; las sesiones se pueden renovar —no se podían—;
la contraseña cambia cuando dice que cambia; la corrección corrige; las reglas de negocio se
explican en lugar de romperse; y 177 rutas deciden quién puede hacer qué.

Y una cosa más, difícil de medir: **la suite ahora encuentra defectos.** Cinco de los
dieciséis hallazgos nuevos los destapó un test escrito para otra cosa.
