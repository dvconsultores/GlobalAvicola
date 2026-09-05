# MATRIZ DE MODALIDAD DE EVIDENCIA

**Gate A** · 2026-09-05 · `GA-REM-016`

Responde una pregunta: **¿la evidencia que sostiene cada certificación es de la clase que su
spec exige?** No «¿hay pruebas?», sino «¿son las que corresponden?».

---

## 1. Taxonomía

Hasta ahora todo se llamaba «E2E». No todo lo es del mismo modo:

| Clase | Qué atraviesa | Dónde vive |
|---|---|---|
| `UI_E2E` | navegador → SPA → proxy → API → dominio → base | `tests/` (proyecto `heredada`) |
| `API_E2E` | HTTP → autenticación → autorización → dominio → base → estado derivado | `e2e/` (proyecto `procesos`) |
| `INTEGRATION` | ASGI en proceso → dominio → base real | `backend/tests/` |
| `UNIT` | una función o componente aislado | `frontend/src/**/*.test.ts` |
| `STATIC` | el código sin ejecutarlo | `tsc` · paridad i18n · deriva de enums |
| `RUNTIME_E2E` | el entorno compartido en marcha, desde fuera | `runtime_connectivity_check.py` |
| `DB_E2E` | esquema y datos sobre PostgreSQL real | `certify_baseline.sh` |
| `MANUAL_RUNTIME` | requiere una persona con acceso al host | `GA-REM-027 AC08` |

## 2. Inventario real — medido, no supuesto

Contado por uso de fixture, no por nombre de fichero:

| Fichero | Casos | `{ request }` | `{ page }` | Clase |
|---|:--:|:--:|:--:|---|
| `e2e/proceso-01-recepcion-de-aves.spec.ts` | 7 | 6 | **2** | `API_E2E` + `UI_E2E` |
| `e2e/proceso-02-control-produccion-diario.spec.ts` | 7 | 7 | 0 | `API_E2E` |
| `e2e/proceso-03-revision-correccion-aprobacion.spec.ts` | 7 | 7 | 0 | `API_E2E` |
| `e2e/proceso-p02-progenitoras-produccion-huevo.spec.ts` | 9 | 9 | 0 | `API_E2E` |
| `e2e/proceso-p04-reproductoras-huevo-fertil.spec.ts` | 9 | 9 | 0 | `API_E2E` |
| `e2e/proceso-p05-incubacion.spec.ts` | 8 | 8 | 0 | `API_E2E` |
| `e2e/proceso-p06-pollo-de-engorde.spec.ts` | 5 | 5 | 0 | `API_E2E` |
| `e2e/proceso-p11-activacion-manual-de-lotes.spec.ts` | 6 | 6 | 0 | `API_E2E` |
| `tests/e2e.spec.ts` | 12 | 0 | 12 | `UI_E2E` |
| `tests/operations.spec.ts` | 10 | 0 | 10 | `UI_E2E` |
| `tests/integration-full.spec.ts` | 0 | — | — | sin casos |

```
80 casos  ·  UI_E2E = 24  ·  API_E2E = 56
```

Un caso de `proceso-01` usa ambos fixtures y cuenta en las dos columnas.

## 3. ¿Son `API_E2E` de verdad, o `INTEGRATION` con otro nombre?

La distinción no la da la herramienta sino el alcance. Los ficheros de `e2e/`:

| Atraviesa | Evidencia |
|---|---|
| frontera HTTP | corren contra `uvicorn` en `127.0.0.1:8099`, no sobre el ASGI en proceso |
| autenticación | `cabeceraAdmin` hace `POST /login` con credenciales reales del entorno |
| autorización | casos de aislamiento entre empresas y de permiso denegado |
| lógica de negocio | `BR-02` `BR-03` `BR-04` `BR-05` `BR-06` `BR-14` |
| base de datos | releen el recurso creado en una petición posterior |
| estado derivado | `saldoDeHuevos`, `saldoEnIncubadora`, resumen de cierre |
| auditoría | `P-07` comprueba la línea de tiempo del registro |

Recorren la cadena completa del proceso. **Son `API_E2E`**, no pruebas de integración.

### El límite honesto de esta modalidad

Los `API_E2E` apuntan al backend **directamente** (`:8099`). No atraviesan la SPA ni el proxy
nginx. La suite `UI_E2E` sí (`:5199`). Conviene tenerlo presente: un defecto que viva solo en
el proxy —`R-71` fue exactamente eso— no lo detecta un `API_E2E`.

## 4. Qué modalidad exige la norma

### La fuente que gobierna la certificación de procesos

`GA-REM-016` es la spec de certificación. Sus criterios obligatorios:

| `AC` | Texto | ¿Exige interfaz? |
|---|---|:--:|
| `AC01` | todos los ficheros de test son descubiertos y ejecutados | no |
| `AC02` | ninguno figura como `CERTIFIED` sin **E2E en verde** | no — dice «E2E», sin calificar |
| `AC03` | existen al menos happy path, negative path y autorización | no |
| `AC04` | el primer proceso del orden alcanza `CERTIFIED` con evidencia | no |
| `AC05` | **ninguna unidad certificada es una pantalla, un endpoint o un componente** | **lo contrario** |
| `AC06`…`AC12` | credenciales, intención funcional, disposición, sensibilidad | no |

`AC05` no es neutral respecto a la interfaz: **prohíbe** tomar la pantalla como unidad de
certificación. Exigir `UI_E2E` para certificar un proceso iría contra el criterio, no a favor.

### Dónde sí vive el requisito de interfaz

Existe, pero en otro sitio y con otro propósito:

| Fuente | Qué pide | Quién lo mide |
|---|---|---|
| `spec.md §6` | sistema de diseño, móvil y web, componentes obligatorios | `GA-REM-020` |
| `spec.md §7` | «Browser: certificado en 8+ navegadores» — **no funcional** | fuera de `GA-REM-016` |
| `spec.md §8.11-13` | diseño, bilingüe, viewports — criterios **del MVP del producto** | `GA-REM-020` |
| `docs/12 §7` | maquetas del Centro de Revisión Operativa | diseño, no criterio de aceptación |

La matriz de procesos ya separa las dos cosas en columnas distintas: **«Estado»** lo decide
`GA-REM-016`; **«Cobertura validada»** lo decide `GA-REM-020`. La existencia de la pantalla es
cobertura funcional, no modalidad de evidencia de la certificación.

## 5. Matriz por proceso certificado

| Proceso | `AC` obligatorio | Modalidad exigida | Modalidad disponible | ¿Válida? | Hueco |
|---|---|---|---|:--:|---|
| **P-02** | `GA-REM-016 AC02/AC03/AC05` · `BR-02` | `E2E` de proceso | `API_E2E` 9/9 | **sí** | — |
| **P-04** | `GA-REM-016 AC02/AC03/AC05` · `BR-02` | `E2E` de proceso | `API_E2E` 9/9 | **sí** | — |
| **P-05** | `GA-REM-016 AC02/AC03/AC05` · `BR-03` | `E2E` de proceso | `API_E2E` 8/8 | **sí** | — |
| **P-07** | `GA-REM-016 AC02/AC03/AC05` · `docs/12 R1`…`R9` | `E2E` de proceso | `API_E2E` 7/7 | **sí** | `R7` — ver §6 |
| **P-11** | `GA-REM-016 AC02/AC03/AC05` · `docs/02 §3.9.2` (6 reglas) | `E2E` de proceso | `API_E2E` 6/6 | **sí** | — |

### Las reglas de negocio, una a una

Ninguna de las reglas obligatorias de los cinco procesos menciona la interfaz:

- **`P-11` `docs/02 §3.9.2`** — marcado como activado manualmente · auditoría de quién, cuándo
  y con qué motivo · soporte documental · sin doble conteo · continuidad desde el saldo ·
  reporte de apertura. Las seis son de datos y comportamiento.
- **`P-07` `docs/12 R1`…`R9`** — segregación, motivo de rechazo, conservación del original,
  inmutabilidad tras SAP, consolidación atómica, idempotencia. Todas de comportamiento.
- **`P-02` `P-04`** — `BR-02`, saldo de huevo. **`P-05`** — `BR-03`, carga de incubadora.

## 6. Un hueco descubierto al leer la spec

`docs/12 R7` dice:

> Un lote no puede cerrarse si tiene registros sin aprobar.

**No se aplica en ninguna parte.** `close_lot` comprueba que el lote esté activo y que
`BR-05` se cumpla; nada impide cerrar con eventos en `registered`. Verificado por búsqueda en
`lots/service.py` y `operations/validators.py`.

```
R-76 · docs/12 R7 sin implementar: un lote se cierra con registros sin aprobar.
       Severidad P1 · afecta P-06 (cierre) y el conjunto de reglas de P-07.
```

Sale a la luz precisamente porque `GA-REM-029` acaba de trabajar en ese camino: el `API_E2E`
de `P-06` cierra lotes cuyos nueve eventos están sin aprobar y recibe `200`. Queda **abierto y
registrado**, no corregido: este checkpoint es documental.

No degrada `P-07`, cuya cadena —revisión, corrección, aprobación— sí está cubierta; `R7` es
una regla de cierre de lote que vive en el conjunto de `P-07` pero se ejecuta en `P-06`.

## 7. Veredicto del Gate A

```
P-02 = CERTIFIED    P-04 = CERTIFIED    P-05 = CERTIFIED
P-07 = CERTIFIED    P-11 = CERTIFIED

CERTIFIED = 5 / 15   (sin cambio)
```

**Ningún proceso se degrada.** La spec de certificación pide `E2E` de proceso y lo prohibido
es justamente lo contrario de lo que se temía: certificar por pantalla.

**No se crean pruebas de interfaz** para conservar una etiqueta: la interfaz no es requisito
de certificación, y fabricar `UI_E2E` por vocabulario sería trabajo artificial.

### Lo que sí se corrige

La afirmación **«UI E2E: PASS»** apareció en la salida de consola de un checkpoint anterior.
Es inexacta: esas suites son `API_E2E`.

Conviene precisar el alcance del error, porque yo mismo lo describí de más al corregirlo:
**ningún documento del repositorio dijo nunca «UI E2E»**; los informes de certificación dicen
textualmente *«la unidad de certificación es el proceso de negocio, no la pantalla ni el
endpoint»*, que es `AC05`. El fallo estuvo en la consola, no en la evidencia archivada.

## 8. Historia intacta

No se reescribe ningún informe. `PROCESS-02/04/05/11-CERTIFICATION.md`,
`WAVE_3_E2E_PROCESS_CERTIFICATION_REPORT.md` y las líneas base históricas quedan como están.
Esta matriz es la nota de corrección y el estado vigente.
