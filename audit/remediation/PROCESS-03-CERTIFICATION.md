# `P-03` · REPRODUCTORAS — CRÍA — INFORME DE CERTIFICACIÓN

`spec.md §4.4` + `§4.5` · `docs/02 §3.5` · `GA-REM-037` · `OD-06` · 2026-09-06

```
P-03        = CERTIFIED
GA-REQ-037  = CERRADO       OD-06 = RESOLVED
```

> Este archivo **sustituye** a la reevaluación del 2026-09-06 que declaraba
> `P-03 = PARTIAL — BLOCKED_BY_REQUIREMENT`. Aquel diagnóstico era correcto y su bloqueo se
> ha resuelto; su contenido se conserva en §1 en lugar de borrarse.

---

## 1. Qué bloqueaba, y por qué no era un defecto

`GA-TD-014` se cerró con `GA-REM-035` tras `OD-04`, y con él el paso `bird_reception`. Quedó
un solo renglón, el de `spec.md §4.5`:

> - **Alertas por desviaciones (peso fuera de curva estándar, mortalidad > umbral)**

La de mortalidad existía. La de peso no, y **no podía existir**: la *curva estándar* no era un
dato del sistema. No había tabla, ni versión, ni forma de que un lote apuntara a una. El
generador de alertas producía tres tipos y no podía producir el cuarto porque no tenía contra
qué comparar.

Eso no es un defecto de implementación, es un requisito sin resolver. Implementarlo por cuenta
propia habría exigido inventar un umbral —un ±10 %, un ±20 %— que ninguna fuente respalda, y
un umbral inventado produce veredictos con toda la apariencia de ser correctos y ninguna de
las garantías. Por eso se elevó como `OD-06` en lugar de codificarse.

La diferencia con `P-01` y `P-06`, que compartían el bloqueante de la OC y ya estaban
certificados, se verificó leyendo las tres secciones normativas y no arrastrando la anotación
de la matriz de bloqueantes:

| Proceso | Sección | ¿Exige alertas por desviación? |
|---|---|:--:|
| `P-01` | `§4.4` | no |
| **`P-03`** | **`§4.5`** | **sí** |
| `P-06` | `§4.8` | no |

## 2. La decisión del propietario

```
OD-06 = RESOLVED (2026-09-06)

  Global Avícola administra curvas estándar de peso configurables por línea genética.
  Líneas iniciales: Cobb 500, Ross 308, Hubbard — ampliables, sin enum fijo.
  Edad en días. Rango del mínimo al máximo de la tabla cargada.
  Interpolación lineal entre puntos. Sin tolerancia global.
  Versionado obligatorio; cada lote fijado a una versión exacta.
```

Cada una de esas cláusulas se implementó y ninguna se amplió. En particular:

- **Sin tolerancia global.** `target_weight` es referencia y **no interviene** en la
  clasificación: la decide `min_weight` y `max_weight` y nada más. Un peso un 1 % por debajo
  del mínimo está fuera, igual que uno un 40 % por debajo. No hay margen porque la decisión no
  lo concede.
- **Sin extrapolar.** Fuera del rango de edades de la tabla, el motor devuelve `NO_REFERENCE`
  y no se emite alerta. Prolongar la recta más allá del último punto daría un rango con
  apariencia de dato y ningún respaldo del proveedor.
- **Sin sembrar curvas.** La siembra crea los **nombres** de las tres líneas y nada más.
  `T-037-01` comprueba que tras `sembrar_baseline` hay cero curvas.

## 3. Lo que se construyó

Cinco piezas nuevas; seis capacidades preexistentes que **no** se rehicieron.

| Pieza | Archivo |
|---|---|
| Versión de curva y sus puntos | `backend/app/masters/models.py` · migración `m3n4o5p6q7r8` |
| Carga atómica con informe por fila | `backend/app/masters/curves.py` |
| Endpoints de curva | `backend/app/masters/router.py` |
| Motor de evaluación | `backend/app/operations/weight_curve.py` |
| Alerta `weight_deviation` | `backend/app/operations/service.py` · `_alertas_de_peso` |
| Referencia del lote a la versión | `backend/app/lots/service.py` · `_curva_del_lote` |

`GeneticLine` **ya era** un maestro con pantalla (`GA-REM-033`), de modo que el «debe ser
posible añadir líneas nuevas» de `OD-06` estaba satisfecho antes de empezar: introducir un
enum fijo habría sido una regresión. Lo mismo con `OperationalAlert`, cuyo propio comentario
ya nombraba `weight_deviation` como tipo previsto.

## 4. Dos decisiones que merecen constar

**El motor vive en un solo sitio.** `rango_esperado()` es la única implementación de la
interpolación en el proyecto. No se duplicó en el frontend.

**`version_label`, no `version`.** El identificador de la revisión lo escribe el
administrador —«2019», «rev. B»— y es el que publica el proveedor. `version` está reservado en
este proyecto para los campos que fija el servidor, y `R-32` barre los esquemas de escritura
buscando ese nombre exacto. La guarda disparó, con razón: dos conceptos opuestos no pueden
compartir palabra. Se renombró el campo en lugar de eximir la guarda, que es lo que habría
sido cómodo.

## 5. Evidencia

| Nivel | Archivo | Resultado |
|---|---|:--:|
| Cadena `API_E2E` | `e2e/proceso-p03-reproductoras-cria.spec.ts` | **5/5** |
| Modelo, carga, asignación, tenencia | `backend/tests/test_genetic_curves.py` | **16/16** |
| Motor de evaluación | `backend/tests/test_weight_curve_evaluation.py` | **14/14** |
| Alerta | `backend/tests/test_weight_alert.py` | **8/8** |
| Regresión backend | suite completa | **439 passed, 49 skipped** |
| Regresión `E2E` | 15 procesos | **111 passed** (antes 106) |

**Sobre la modalidad.** `§4.5` dice «alertas por desviaciones» sin exigir que el usuario las
vea en pantalla, de modo que la evidencia es `API_E2E`. No se fabrica `UI_E2E` por vocabulario.

## 6. Sensibilidad · `GA-REM-016 AC13`

Ninguna prueba se invoca como evidencia sin demostrar que puede fallar. Siete mutaciones sobre
el backend y tres sobre la cadena `E2E`, todas revertidas:

| # | Mutación | Rompe | Fallos |
|:--:|---|---|:--:|
| 1 | El rango deja de decidir: todo cae dentro | `AC13`…`AC15` | 6 |
| 2 | Bordes exclusivos en vez de inclusivos | `AC16` | 4 |
| 3 | `_interpolar` devuelve el punto inferior | `AC12` | 8 |
| 4 | Activar una versión arrastra los lotes existentes | `AC08`, `AC23` | 1 |
| 5 | Se omite la comprobación de línea genética | `AC10` | 1 |
| 6 | La carga deja de ser atómica | `AC05`, `AC06` | 5 |
| 7 | La curva deja de heredar la tenencia de su línea | `AC24` | 1 |
| B | *(E2E)* activar arrastra los lotes | cadena `§4.5` | 1 |
| C | *(E2E)* sin curva se inventa un ±20 % | cadena `§4.5` | 1 |
| D | *(E2E)* la alerta no se emite | cadena `§4.5` | 2 |

Las mutaciones 1 y 2 son las que interesan: la primera comprueba que el rango decide, la
segunda que decide **en el borde exacto**. Un test que solo probara 100 g contra `[135, 165]`
sobreviviría a las dos.

## 7. Tres guardas del proyecto que dispararon

Se registran porque cada una detuvo un defecto real de esta entrega, no porque estorbaran:

| Guarda | Qué detuvo |
|---|---|
| `test_r32_ningun_esquema_de_escritura_expone_campos_de_flujo` | el campo `version` en un esquema de escritura |
| `T-025-11` · clasificación de datos | dos tablas nuevas sin clasificar |
| `T-025-04` · cobertura de la purga | `genetic_weight_curves` se habría vaciado por `CASCADE` a espaldas del inventario |

## 8. Lo que queda fuera, dicho

**No hay pantalla de administración de curvas.** `GA-REM-037` no tiene ningún criterio de
frontend y la modalidad de evidencia es `API_E2E`, de modo que construirla sería trabajo sin
spec. Hoy la carga se hace por `POST /masters/weight-curves`. Queda registrado como `R-96`,
no resuelto en silencio ni implementado sin requisito.

**`P-14` sigue intacto.** La alerta es un registro en `operational_alerts`. No se introdujo
correo, ni push, ni centro de notificaciones. `T-037-24` lo comprueba sobre el esquema: una
tabla de notificaciones o de suscripciones sería la huella inevitable de haber empezado `P-14`
por la puerta de atrás.

**`RC-07` no se toca.** Mortalidad → SAP sigue abierta y es un asunto distinto.
