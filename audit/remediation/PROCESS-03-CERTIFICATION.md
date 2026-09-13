# `P-03` · REPRODUCTORAS — CRÍA — INFORME DE CERTIFICACIÓN

> **Vigencia — anotación `GA-GOV-03` (T1, 2026-09-13). Estado: `NOT_REPRODUCIBLE_EN_HEAD (pre-GA-GOV-03)`.**
> Este informe histórico no cita commit certificado ni artefacto de corrida (regla «no GREEN por declaración», §52) y varias suites de proceso (P-03/P-04/P-05/P-10/P-11/P-15) contenían TEST_DEFECT rojos hasta la T1 de GA-GOV-03. El contenido no se reescribe; la recertificación E2E de cada proceso corresponde a la T12 del programa pre-SAP (`audit/ga-pre-sap-program/GA_PRE_SAP_REMEDIATION_MASTER_ROADMAP.md`).

`spec.md §4.4` + `§4.5` · `docs/02 §3.5` · `GA-REM-037` · `OD-06` · 2026-09-06

```
P-03        = CERTIFIED     ← tras cerrar R-96 y R-97, ver ADDENDUM B
GA-REQ-037  = CERRADO       OD-06 = RESOLVED
```

> **`ADDENDUM A` (2026-09-06).** Este informe declaró `P-03 = CERTIFIED` cuando solo el backend
> lo estaba. La declaración era **prematura**; se corrigió y el proceso volvió a `PARTIAL`.
>
> **`ADDENDUM B` (2026-09-06).** Cerrados `R-96` y `R-97`, `P-03` vuelve a `CERTIFIED` — esta
> vez con la capacidad en el producto y no solo en la API.

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


---

# ADDENDUM A · la certificación era prematura (2026-09-06)

## Lo que este informe concluyó mal

En su §8 —«Lo que queda fuera, dicho»— este informe declaró:

> *No hay pantalla de administración de curvas. `GA-REM-037` no tiene ningún criterio de
> frontend y la modalidad de evidencia es `API_E2E`, de modo que construirla sería trabajo sin
> spec.*

El razonamiento va al revés. `OD-06` dice que cada línea genética puede tener su tabla y que
**esa tabla debe poder cargarse dentro de Global Avícola**. Que `GA-REM-037` no desarrollara
ese punto no elimina el requisito del propietario: demuestra que la spec estaba incompleta.

```
OWNER REQUIREMENT  >  INCOMPLETE SPEC
```

Y `GA-REM-016 AC05` ya daba el criterio de proceso: *«ninguna unidad certificada es una
pantalla, un endpoint o un componente»*. Certificar `P-03` porque
`POST /masters/weight-curves` responde `201` es certificar un endpoint.

```
P-03 = PARTIAL
R-96 = MISSING PRODUCT CAPABILITY + SPEC COVERAGE GAP     (era P2 "backlog"; se reclasifica a P1)
```

## Y un hueco que apareció al mirar de cerca

Al derivar el contrato de esa pantalla —`R96_WEIGHT_CURVE_FRONTEND_CONTRACT_MATRIX.md`— salió
`R-97`: el motor de evaluación tiene un solo consumidor, el generador de alertas, y solo actúa
cuando el peso queda fuera de rango. `WITHIN_STANDARD` y `NO_REFERENCE` **no son distinguibles**
desde fuera: los dos se ven como «ninguna alerta».

## Qué se conserva y qué no

**Se conserva toda la evidencia.** Los 38 tests de backend, los 5 `API_E2E` y las diez
mutaciones siguen en verde y siguen siendo válidos. Nada de lo medido era falso.

**Se retira la conclusión.** Lo que estaba mal no era ninguna medición: era el salto de
«el backend hace lo que `OD-06` describe» a «el proceso está certificado».

Los dos hallazgos se cierran por la **enmienda A de `GA-REM-037`**, que añade `AC26`…`AC28` de
backend y `AC-FE01`…`AC-FE20` de producto.


---

# ADDENDUM B · ahora sí, y por qué la diferencia importa (2026-09-06)

## Qué faltaba

`ADDENDUM A` dejó `P-03` en `PARTIAL` porque `OD-06` exige que la tabla de curva pueda cargarse
**dentro de Global Avícola**, y solo podía cargarse llamando a la API a mano. Al derivar el
contrato de esa pantalla apareció además `R-97`: la evaluación de curva no era observable salvo
cuando generaba alerta, de modo que «dentro de norma» y «sin referencia» se veían igual —sin
nada—.

## Qué se hizo

```
GA-REM-037 enmienda A
  ├─ AC26…AC28      la evaluación se lee, sin duplicar el motor
  └─ AC-FE01…FE20   la capacidad existe en el producto, sobre el maestro GeneticLine
```

Cinco superficies nuevas y ninguna arquitectura nueva: la pantalla de curvas cuelga de la línea
genética, reutiliza el patrón que `P-12` certificó, y el veredicto del pesaje lo calcula el
backend y lo pinta React sin recalcular nada.

Detalle completo en `R-96-WEIGHT-CURVE-CAPABILITY-CERTIFICATION.md`.

## La cadena de `§4.5`, ahora completa

| # | Paso | Nivel | Estado |
|:--:|---|---|:--:|
| 1–11 | Cadena operativa de cría | `API_E2E` | **PASS** |
| 12 | Alerta por mortalidad sobre umbral | `API_E2E` | **PASS** |
| 13 | Alerta por peso fuera de curva | `API_E2E` | **PASS** |
| 14 | Aislamiento entre empresas | `API_E2E` | **PASS** |
| 15 | **La curva se carga desde el producto** | **`UI_E2E`** | **PASS** — `R-96` |
| 16 | **El veredicto del pesaje se lee en pantalla** | **`UI_E2E`** | **PASS** — `R-97` |

```
16 pasos · PASS 16 · FAIL 0
```

## Evidencia acumulada

| Nivel | Resultado |
|---|:--:|
| `backend/tests/test_genetic_curves.py` | 16/16 |
| `backend/tests/test_weight_curve_evaluation.py` | 14/14 |
| `backend/tests/test_weight_alert.py` | 8/8 |
| `backend/tests/test_weight_evaluation_endpoint.py` | 10/10 |
| `e2e/proceso-p03-reproductoras-cria.spec.ts` | 5/5 `API_E2E` |
| `e2e/proceso-p03-curvas-ui.spec.ts` | 13/13 `UI_E2E` |
| `vitest` de curvas y evaluación | 13/13 |
| Regresión backend | 449 passed · 49 skipped |
| Regresión `E2E` | 124 passed |
| Regresión `vitest` | 74 passed |
| Sensibilidad | 10 + 7 mutaciones, revertidas |

## Lo que sigue fuera, dicho

`R-98`: ninguna pantalla de esta aplicación oculta acciones de escritura según el permiso del
usuario —no hay modelo de permisos en el frontend—. Es transversal y pertenece a `P-13`. Lo que
sí se verificó es que el backend niega y la interfaz presenta la negativa, que es lo que impide
el acceso de verdad.

`P-14` intacto. `RC-07` sin tocar.
