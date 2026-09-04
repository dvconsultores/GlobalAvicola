# HALLAZGOS DEL BASELINE LIMPIO

**`GA-REM-025`** · 2026-09-04 · `R-63` … `R-68`

Seis hallazgos que aparecieron al construir y recorrer una instalación desde cero. Cinco
eran invisibles mientras el entorno arrastraba historia sembrada: no es que nadie los
hubiera buscado, es que los datos acumulados los tapaban.

Ninguno se corrige aquí. `NO FIX OUTSIDE ACTIVE SPEC`: el alcance de `GA-REM-025` es el
entorno y su baseline, no la lógica de negocio ni la capa transaccional.

---

## `R-68` — Una escritura no es visible para la petición inmediatamente siguiente

**P0** · intermitente · afecta a **todos** los endpoints de escritura

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

Destino: spec propia. Es un cambio en la capa transaccional, no un parche local.

---

## `R-67` — El saldo de apertura no alimenta el saldo de aves

**P1** · afecta a la instalación de un cliente nuevo

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

Destino: spec propia, relacionada con `GA-REM-005`.

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

## Resumen

| ID | Título | Prior. | Destino |
|---|---|:--:|---|
| `R-68` | Escritura no visible para la petición inmediata | **P0** | spec propia |
| `R-67` | El saldo de apertura no alimenta el saldo de aves | **P1** | spec propia |
| `R-65` | 500 en `/audit/{log_id}` no-UUID | P2 | `GA-REM-019` |
| `R-64` | `integration_seeds.py` roto | P2 | `GA-REM-019` |
| `R-63` | Tabla de credenciales falsa en `dev_seeds.py` | P2 | `GA-REM-019` |
| `R-66` | `/me` no refleja la empresa activa | P3 | `GA-REM-019` |
