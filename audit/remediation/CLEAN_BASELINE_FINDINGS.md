# HALLAZGOS DEL BASELINE LIMPIO

**`GA-REM-025`** · 2026-09-04 · `R-63` … `R-68`

Seis hallazgos que aparecieron al construir y recorrer una instalación desde cero. Cinco
eran invisibles mientras el entorno arrastraba historia sembrada: no es que nadie los
hubiera buscado, es que los datos acumulados los tapaban.

Ninguno se corrige aquí. `NO FIX OUTSIDE ACTIVE SPEC`: el alcance de `GA-REM-025` es el
entorno y su baseline, no la lógica de negocio ni la capa transaccional.

---

## `R-68` — Una escritura no es visible para la petición inmediatamente siguiente

**P0** · intermitente · afecta a **todos** los endpoints de escritura · **`CERTIFIED` 2026-09-04**

`get_db` confirma la transacción en el cierre de la dependencia
(`app/database.py:24-33`), y FastAPI ejecuta ese cierre **después** de enviar la respuesta.
Un cliente que actúe sobre un `201` al instante puede encontrarse con que la fila todavía
no está.

Reproducido de forma determinista, cinco altas seguidas de su login inmediato:

```
race_0: alta 201 -> login inmediato 200
race_1: alta 201 -> login inmediato 200
race_2: alta 201 -> login inmediato 401  | reintento tras 0,5 s: 200
race_3: alta 201 -> login inmediato 401  | reintento tras 0,5 s: 200
race_4: alta 201 -> login inmediato 401  | reintento tras 0,5 s: 200

logins inmediatos fallidos: 3/5
```

Por qué importa más de lo que parece: **produce fallos intermitentes que parecen defectos
de otra cosa.** Durante esta misma certificación creó un `BR-07 «Farm no encontrado»` justo
después de crear la granja, y el primer diagnóstico —resetear con el backend en marcha— era
equivocado. Un test E2E que crea un recurso y lo consulta a continuación fallará una de cada
tres veces sin motivo aparente.

Conexión probable con `R-62`: conviene descartarlo antes de clasificar los 23 fallos
heredados de Playwright.

**Resuelto** por `GA-REM-026`: la confirmación pasa a la capa de ruta, que se ejecuta dentro del manejo de excepciones y antes de que la respuesta salga. Certificación en [`R-68-TRANSACTION-CERTIFICATION.md`](R-68-TRANSACTION-CERTIFICATION.md).

---

## `R-67` — El saldo de apertura no alimenta el saldo de aves

**P1** · afecta a la instalación de un cliente nuevo · **`CERTIFIED` 2026-09-04**

`POST /lots/activate-manual` guarda un `OpeningBalance` con la población inicial, y
`get_current_bird_balance` (`app/operations/validators.py:21-52`) **no lo consulta**: suma
únicamente movimientos de eventos de entrada. Ningún otro sitio lo lee tampoco.

Consecuencia: un lote activado manualmente con 5.000 aves tiene saldo 0, y `BR-01` rechaza
toda mortalidad, descarte y salida sobre él.

```
activate-manual → 201, initial_male=1000 initial_female=4000
mortalidad de 12 → 400 «Mortalidad (12) excede el saldo de aves disponibles (0)»
```

La activación manual es el camino previsto para incorporar lotes que ya están en marcha
cuando se instala el sistema. Es decir: **es exactamente lo que hará el primer cliente
real**, y produce lotes inservibles. Era invisible porque todos los lotes del entorno
compartido venían de eventos de recepción sembrados.

**Resuelto** por la enmienda `R-67` de `GA-REM-005`, con `RC-08`/`RR-08` fijando qué significa «saldo inicial». Certificación en [`R-67-OPENING-BALANCE-CERTIFICATION.md`](R-67-OPENING-BALANCE-CERTIFICATION.md).

---

## `R-65` — `GET /api/v1/audit/{log_id}` devuelve 500 con un identificador no-UUID

**P2** · robustez

`log_id: str` (`app/audit/router.py:40`) llega sin validar a una comparación contra una
columna UUID, y asyncpg lanza `DataError`. Cualquier ruta mal formada bajo `/audit/`
produce un 500 en vez de un 404 o un 422.

```
GET /api/v1/audit/logs → 500
```

Misma familia que `R-38`: una ruta que atrapa lo que no debería. Destino: `GA-REM-019`.

---

## `R-64` — `seeds/integration_seeds.py` está roto

**P2** · herramienta de desarrollo

```
File "seeds/integration_seeds.py", line 230, in seed_users
    role = roles.get(udef["role_name"])
KeyError: 'role_name'
```

Falla en el primer bloque de usuarios y deja la base a medio sembrar. No afecta a
producción ni a la suite —que usa `test_seeds.py`—, pero es una trampa para quien intente
poblar un entorno con él. Destino: `GA-REM-019`.

---

## `R-63` — `seeds/dev_seeds.py` imprime una tabla de credenciales que ya no es cierta

**P2** · residuo de `GA-REM-004`

El seed dejó de sembrar contraseñas literales —las lee del entorno, correctamente— pero
sigue imprimiendo al final una tabla con parejas usuario/contraseña del código anterior:

```
│ operador         │ oper123         │
│ aprobador        │ aprob123        │
```

Doble problema: la tabla **es falsa** —esas contraseñas ya no funcionan— y tiene forma de
secreto, que es justo lo que `GA-REM-004` quería quitar del repositorio. Destino:
`GA-REM-019`.

---

## `R-66` — `/me` devuelve la empresa persistida, no la de la sesión activa

**P3** · inconsistencia documental

Tras `POST /switch-company`, el token queda alcanzado a la empresa nueva pero `GET /me`
sigue devolviendo el `company_id` de la fila del usuario, nulo para un Super Administrador.

**No rompe la interfaz**: el frontend guarda la empresa activa de la respuesta del propio
`switch` (`company.store.ts:56`) y no de `/me`. Pero deja dos fuentes de verdad sobre «en
qué empresa estoy», y quien escriba una prueba contra `/me` medirá lo que no cree estar
midiendo —le ocurrió a esta certificación—. Destino: `GA-REM-019`, documental.

---

---

## `R-70` — `activate-manual` devuelve 500 con una fase productiva inexistente

**P2** · robustez · descubierto al certificar `R-67`

`phase_at_activation_id` viaja sin comprobar que exista, y la violación de clave foránea
sale como `500`. Misma familia que `R-65`: entrada no validada que termina en error del
servidor en vez de en un `400` o `422`. Destino: `GA-REM-019`.

---

## `R-69` — La validación del saldo de apertura rechaza datos legítimos

**P2** · regla de negocio · descubierto al resolver `RC-08`

`lots/service.py:209` exige `accumulated_mortality_* ≤ initial_*_count`. Bajo `RR-08`
—donde `initial_*_count` es el saldo vivo y los acumulados son histórico— esa comprobación
rechaza un caso perfectamente real: un lote reproductor con 5 000 aves vivas que acumuló
6 000 bajas a lo largo de su ciclo, habiendo empezado con 11 000.

No se corrige dentro de `R-67`: cambiar una validación de negocio merece su propia
decisión, y el propietario puede haber querido exactamente esa restricción. Destino:
`GA-REM-019`.

---

## `R-71` — El proxy resolvía el backend una sola vez, al arrancar

**P0** · dejó la API inalcanzable ocho horas · **`PARTIAL` 2026-09-05**

No lo descubrió el baseline limpio sino el incidente del `502`, pero se registra aquí por
continuidad del numerado.

`frontend/nginx.conf` hacía `proxy_pass http://backend:8000` sin directiva `resolver`, de
modo que nginx resolvía el nombre al arrancar y conservaba esa IP mientras viviera el
proceso. Watchtower recrea el backend en cada publicación de imagen; cuando el contenedor
recreado no recupera su dirección anterior, nginx apunta a una IP inexistente y toda la API
responde `502` de forma permanente **con el backend perfectamente sano**.

```
http://<host>:8002/health                → 200 {"status":"ok"}
https://avicola.globaldv.net/api/v1/...  → 502
```

Llevaba ahí desde que existe el despliegue automático. Lo tapaba la suerte: si Docker
reasigna la misma IP, la caché sigue siendo válida por casualidad — que es lo que ocurrió en
la publicación inmediatamente anterior, con un `502` de cuatro minutos que se resolvió solo.

**Corregido** por `GA-REM-027`, con la corrección desplegada y un ciclo de recreación
observado: el backend se destruyó y recreó, el frontend siguió intacto y la API se recuperó
sola. Queda `PARTIAL` porque el cambio efectivo de IP no es observable sin acceso al host, y
sin eso no se puede afirmar que el ciclo demostrara el arreglo y no una reasignación
afortunada. Detalle en
[`GA-REM-027-PROXY-RESOLUTION-CERTIFICATION.md`](GA-REM-027-PROXY-RESOLUTION-CERTIFICATION.md)
y [`SHARED_BACKEND_502_INCIDENT.md`](SHARED_BACKEND_502_INCIDENT.md).

---

## `R-72` — Doce tests heredados pasaban sin poder fallar

**P2** · credibilidad de la suite · **`RESUELTO` 2026-09-05**

De los 26 casos de `tests/operations.spec.ts`, doce figuraban como `PASS` en el baseline
congelado. Ninguno se autenticaba, igual que los catorce que fallaban. La diferencia era que
sus afirmaciones no podían fallar:

```ts
expect(progressBar).toBeTruthy()          // un Locator siempre es truthy
expect(focusedElement).toBeTruthy()       // ídem
expect(count).toBeGreaterThanOrEqual(0)   // un recuento nunca es negativo
```

Los demás medían la pantalla de login: su `h1`, su tiempo de carga, sus traducciones.

**Doce de los quince `PASS` del baseline eran ilusorios.** La suite heredada no cubría
quince requisitos, cubría tres. Retirados bajo `GA-REM-016` con la disposición
`RETIRED_VACUOUS`; lo que sí querían comprobar vive en los diez casos reescritos, ahora con
afirmaciones que fallan cuando deben.

Deja una regla: un test que pasa no es evidencia hasta que se demuestra que puede fallar.
Es la razón de `AC12`.

---

## `R-73` — El cierre de lote nunca ha funcionado

**P1** · descubierto al certificar `R-47`

`POST /lots/{id}/close` responde **500 siempre**, por dos causas independientes:

```
1) TypeError: unsupported operand type(s) for -: 'date' and 'datetime'
   lots/service.py → age_days = (date.today() - lot.start_date).days
   `start_date` nunca es nulo, de modo que la rama se ejecuta siempre.

2) El modelo de respuesta de la ruta no encaja con el resumen que devuelve el
   servicio: faltan `created_at` y `updated_at`.
```

La primera **queda resuelta** dentro de `GA-REM-028`: es la misma confusión entre fecha de
negocio y marca temporal que originó `R-47`, y `AC07` no podía comprobarse sin ella.

La segunda **sigue abierta**: es un desajuste de contrato, no de semántica temporal, y
merece su propia decisión —qué debe devolver el cierre, el lote o el resumen—. Destino:
`GA-REM-019`.

Afecta al paso `lot_closure` de las cadenas de `P-06` y `P-07`.

---

## Resumen

| ID | Título | Prior. | Estado |
|---|---|:--:|---|
| `R-71` | El proxy resolvía el backend una sola vez, al arrancar | **P0** | **`PARTIAL`** — `GA-REM-027`, corregido y desplegado |
| `R-68` | Escritura no visible para la petición inmediata | **P0** | **`CERTIFIED`** — `GA-REM-026` |
| `R-67` | El saldo de apertura no alimenta el saldo de aves | **P1** | **`CERTIFIED`** — `GA-REM-005` enmienda |
| `R-65` | 500 en `/audit/{log_id}` no-UUID | P2 | abierto → `GA-REM-019` |
| `R-64` | `integration_seeds.py` roto | P2 | abierto → `GA-REM-019` |
| `R-63` | Tabla de credenciales falsa en `dev_seeds.py` | P2 | abierto → `GA-REM-019` |
| `R-66` | `/me` no refleja la empresa activa | P3 | abierto → `GA-REM-019` |
| `R-69` | La validación del saldo de apertura rechaza datos legítimos | P2 | abierto → `GA-REM-019` |
| `R-70` | 500 en `activate-manual` con una fase inexistente | P2 | abierto → `GA-REM-019` |
| `R-72` | Doce tests heredados pasaban sin poder fallar | P2 | **`RESUELTO`** — `GA-REM-016` |
| `R-73` | El cierre de lote responde 500 siempre | P1 | **parcial** — causa temporal resuelta en `GA-REM-028`; modelo de respuesta abierto → `GA-REM-019` |
