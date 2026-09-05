# INFORME DE CONTINUACIÓN — WAVE 3 · `GA-REM-016`

**2026-09-05** · recuperación de la suite heredada

---

## 1. Estado de entrada

```
GA-REM-027 .................. PARTIAL — hueco de verificación (AC08 abierto)
GA-REM-027 → GA-REM-016 ..... DEFERRED_VERIFICATION / no bloqueante
API pública compartida ...... SANA
Defecto activo de proxy ..... NO
R-58 ........................ PASS_BY_INFERENCE
R-67 · R-68 ................. CERTIFIED
GA-REM-025 herramienta ...... CERTIFIED · reset compartido NOT_VERIFIED
Playwright .................. 15 PASS / 23 FAIL (baseline congelado)
```

## 2. `GA-REM-027`, verificación diferida

No se promueve. `AC08` sigue abierto: demostrar un cambio efectivo de IP del backend exige
acceso al host. Se vigiló la condición de interrupción durante todo el trabajo —salud
directa del backend en verde con la ruta pública en fallo— y **no se disparó** en ningún
momento.

## 3. Enmienda de la spec, antes de tocar nada

El alcance §1 de `GA-REM-016` cubría «reparar la ejecutabilidad (config, ubicación, datos)»,
y `AC01` se cumplía: los 59 casos se descubrían y se ejecutaban. Pero **un test que se
ejecuta y falla sí es ejecutable**; `AC01` no dice nada sobre si su contenido sigue siendo
válido.

Reparar autenticación, reescribir contra el flujo vigente y retirar tests superados no
estaban autorizados. Se enmendó la spec con `AC06`…`AC12` y cinco disposiciones admitidas
**antes** de modificar un solo test, en commit propio (`ec4ca54`).

`AC07` protege lo esencial: reparar un test es quitarle el bloqueo, no reescribir lo que
comprueba.

## 4. Los seis casos de `farm_inspection`

Estaban **enmascarados**, no obsoletos. Entraban como `admin`/`admin123` —un usuario que no
existe— y se quedaban en la pantalla de login. Cubren el formulario de inspección por
galpón, que ninguna otra prueba toca.

Solo se cambió la precondición: `test-support/auth.ts` centraliza el mecanismo vigente
—usuarios `test_*`, contraseñas del entorno—. Las afirmaciones funcionales quedaron
intactas.

**Cinco pasaron a la primera.** El sexto reveló una suposición del propio test.

## 5. Recuperación de autenticación

`tests/e2e.spec.ts`: **3/12 → 12/12**.

Al quitar el bloqueo aparecieron dos causas que el fallo de login tapaba, y **ninguna es un
defecto de la aplicación**:

| Lo observado | Lo que era |
|---|---|
| `locator('h1')` resuelve a tres encabezados con sesión | ambigüedad de selector. El panel **sí** tiene `<h1>Dashboard</h1>` |
| «Galpón 2» sigue visible tras borrar | el formulario arranca con **dos** galpones; al añadir hay tres y al borrar quedan dos. El borrado funciona |

Sobre la primera conviene ser explícito: yo había cambiado esa afirmación por considerarla
obsoleta, tras leer solo el encabezado móvil. Era correcta. Se restauró y solo se acotó el
selector.

## 6. Corrección de la expectativa inválida

Un caso esperaba un `<nav>` en `/login`, donde no lo hay ni debe haberlo: aún no se ha
entrado. El requisito que quería expresar sí existe —`spec.md:286` y `docs/02:594` exigen
navegación inferior en la aplicación móvil— y se comprueba donde corresponde: con sesión y
usuario de vista móvil, que es cuando `AppLayout` monta `MobileNav`.

No se degradó a «la página existe» (`§25`).

## 7. Disposición de la interfaz heredada

Los 14 casos de `operations.spec.ts` apuntaban a `/processes`, hoy ruta heredada que
redirige. **Pero el requisito no se movió**: `processCatalog.ts` declara las mismas seis
etapas avícolas con sus rutas en `STAGE_PATH_MAP`, y `navigationConfig.ts` las expone como
cuatro categorías en `/menu/poultry`.

Doce se reescribieron contra el flujo actual conservando su intención. Dos se retiraron con
evidencia: esperaban accesos rápidos `Alimento` y `Pesaje` en un panel móvil que ya no
existe —`Pesaje` no aparece en ninguna parte del frontend— y su cobertura la absorbe el caso
reescrito que lleva de la etapa al formulario.

Al reescribir apareció una tercera suposición equivocada de los tests originales: la vista
por omisión de una etapa es una **rejilla** de operaciones, no la cronología.

## 8. Reinterpretación de la evidencia E2E histórica — `R-72`

```
Resultado histórico de Playwright:      15 PASS / 23 FAIL
Evidencia válida entre esos PASS:        3 con cobertura efectiva
                                        12 ilusorios / sin valor probatorio
Baseline histórico modificado:          NO
```

El fichero histórico **no se toca**: `15 PASS / 23 FAIL` es lo que la herramienta reportó, y
seguirá diciéndolo. Lo que se corrige es su **interpretación**, no el dato. Sustituirlo por
`3 PASS` sería falsificar evidencia.

```
RESULTADO DE LA HERRAMIENTA  =  15 PASS
VALOR DE CERTIFICACIÓN       =  3 PASS validados
```

Una nota sobre el 35 % anterior (`21 / 60`): **no estaba contaminado por `R-72`**. Aquellos
21 venían del proyecto `procesos` —`proceso-01`, `02`, `03`—, que sí se ejecutaban y pasaban
de verdad. `R-72` afectó únicamente a la suite `heredada`.

### El detalle

El hallazgo más incómodo de esta tanda.

De los 26 casos de `operations.spec.ts`, **doce figuraban como `PASS`**. No se autenticaban,
igual que los catorce que fallaban. La diferencia era que sus afirmaciones no podían fallar:

```ts
expect(progressBar).toBeTruthy()          // un Locator siempre es truthy
expect(focusedElement).toBeTruthy()       // ídem
expect(count).toBeGreaterThanOrEqual(0)   // un recuento nunca es negativo
```

Los demás medían la pantalla de login: su `h1`, su tiempo de carga, sus traducciones.

**Doce de los quince `PASS` del baseline eran ilusorios.** La suite heredada no cubría
quince requisitos: cubría tres. Se retiran como `RETIRED_VACUOUS`.

## 9. Nuevo baseline

```
43 / 43 PASS · 0 FAIL · 0 ERROR · 0 SKIP
```

Congelado en [`PLAYWRIGHT_RECOVERY_RUN_01.md`](PLAYWRIGHT_RECOVERY_RUN_01.md). Los
baselines anteriores **no se sobrescriben**.

El total baja de 59 a 43 porque se retiraron 16 casos que no cubrían nada: 14 fallaban sin
llegar a comprobar y 12 pasaban sin poder fallar, condensados en 10 equivalentes. Reducción
de recuento, no de cobertura.

## 10. Defectos de aplicación descubiertos al desenmascarar

```
0
```

La clasificación estimó `0 / 23` antes de ejecutar. Tras ejecutar de verdad, se confirma.
No se defiende el cero artificialmente: se buscaron, y las tres anomalías que aparecieron
resultaron ser suposiciones de los tests, verificadas una a una contra el código.

## 11. Cobertura de requisitos

**No se recalcula todavía.** La cobertura se mide en requisitos con evidencia E2E ejecutada,
no en tests verdes, y esta tanda ha cambiado la composición de la suite sin mapear aún cada
caso reescrito a su requisito. Inflar el porcentaje porque diez tests más están en verde
sería exactamente lo que `§42` prohíbe.

Lo que sí cambia, y a la baja, es la lectura del pasado: doce de los quince `PASS`
anteriores no cubrían nada.

## 12. Certificación de procesos

No se avanzó en esta tanda: la recuperación de la suite era su prerrequisito (`§54`). Estado
real de los quince:

| Proceso | Estado |
|---|---|
| `P-01` Progenitoras — Cría | `PARTIAL` |
| `P-02` Progenitoras — Producción de huevo | `READY_FOR_E2E` |
| `P-03` Reproductoras — Cría | `PARTIAL` |
| `P-04` Reproductoras — Producción de huevo fértil | `READY_FOR_E2E` |
| `P-05` Incubación | `READY_FOR_E2E` |
| `P-06` Pollo de engorde | `PARTIAL` |
| `P-07` Revisión → Corrección → Aprobación | **`CERTIFIED`** |
| `P-08` Consolidación y envío a SAP | `PARTIAL` — `GA-REM-017` `BLOCKED_EXTERNAL` |
| `P-09` Auditoría interna | `PARTIAL` |
| `P-10` Trazabilidad generacional | `PARTIAL` |
| `P-11` Activación manual de lotes | `READY_FOR_E2E` ⚠ `R-47` |
| `P-12` Gestión de datos maestros | `PARTIAL` |
| `P-13` Usuarios, roles y permisos | `PARTIAL` |
| `P-14` Notificaciones y alertas | `PARTIAL` |
| `P-15` Reportes y KPI | `PARTIAL` |

`P-11` mejora su posición: `R-67` dejó certificado que un lote activado manualmente puede
operar, que era el supuesto de fondo de ese proceso.

## 13. Evidencia multiempresa

Sin cambios en esta tanda. `R-42`, `R-59`, `R-48` y `R-54` siguen certificados por la suite
de aislamiento (33/33) y por el recorrido de instalación limpia.

## 14. Regresión

```
E2E ................. 43/43 PASS
Backend ............. 307 pasados · 49 omitidos · 0 fallos
TypeScript .......... PASS
Vitest .............. 61/61
Paridad i18n ........ 866 = 866
Deriva de esquema ... 0
```

## 15-16. Commits y publicaciones

| Commit | Contenido |
|---|---|
| `ec4ca54` | `docs(spec)`: autorizar la recuperación — **spec primero** |
| `4f71c8f` | `test(e2e)`: recuperar la cobertura de inspección de granja |
| `7b31599` | `test(e2e)`: reescribir la suite de operaciones contra el flujo vigente |

Empujados con el `ssh-agent` autorizado. Los dos últimos tocan `tests/`, `test-support/` y
`audit/`: no reconstruyen ninguna imagen.

## 17. Bloqueantes abiertos

| Bloqueante | Estado |
|---|---|
| `GA-REM-027 AC08` | requiere acceso al host Docker |
| `R-58` | `PASS_BY_INFERENCE`; requiere inspección dentro de la imagen |
| `GA-REM-025` reset compartido | `PENDING_EXTERNAL_ACCESS` |
| `GA-REM-017` SAP real | `BLOCKED_EXTERNAL`; bloquea `P-08` |
| `R-63`…`R-66`, `R-69`, `R-70` | abiertos → `GA-REM-019` |

## 18. Procesos restantes

Catorce de quince sin certificar. Tres en `READY_FOR_E2E` sin gaps conocidos (`P-02`,
`P-04`, `P-05`) y uno más con una advertencia (`P-11` ⚠ `R-47`).

## 19. `READY_TO_CONTINUE`

```
SÍ — la recuperación de la suite está completa y el siguiente paso es la
     certificación de procesos, empezando por los READY_FOR_E2E.
```

## 20. Índice de evidencias

| Documento | Contenido |
|---|---|
| [`PLAYWRIGHT_FAILURE_CLASSIFICATION.md`](PLAYWRIGHT_FAILURE_CLASSIFICATION.md) | los 23 fallos, causa verificada |
| [`PLAYWRIGHT_TEST_DISPOSITION_MATRIX.md`](PLAYWRIGHT_TEST_DISPOSITION_MATRIX.md) | disposición caso por caso + `R-72` |
| [`PLAYWRIGHT_RECOVERY_RUN_01.md`](PLAYWRIGHT_RECOVERY_RUN_01.md) | baseline nuevo, congelado |
| [`PLAYWRIGHT_POST_R68_R67_BASELINE.md`](PLAYWRIGHT_POST_R68_R67_BASELINE.md) | baseline anterior — **inmutable** |
| `specs/remediation/GA-REM-016*` | enmienda con `AC06`…`AC12` |
| `test-support/auth.ts` | mecanismo de autenticación centralizado |


---

# TRANCHE `P-02` · `P-04` · `P-05` (2026-09-05)

## 21. Resultado

| Proceso | Antes | Ahora | Casos | Cadena |
|---|---|---|:--:|:--:|
| `P-02` Progenitoras — producción de huevo | `READY_FOR_E2E` | **`CERTIFIED`** | 9/9 | 10 pasos |
| `P-04` Reproductoras — huevo fértil | `READY_FOR_E2E` | **`CERTIFIED`** | 9/9 | 10 pasos |
| `P-05` Incubación | `READY_FOR_E2E` | **`CERTIFIED`** | 8/8 | 8 pasos |

Cada uno con su cadena documentada completa, no solo su tramo distintivo. `§48` no admite
certificar un proceso porque sus capacidades compartidas estén certificadas, y aplicarlo
cambió el alcance de esta tanda: la primera versión de las specs cubría solo el segmento de
huevo y habría dado una certificación falsa.

## 22. Filtro de validez de los tests

Derivado de `R-72`. Ningún `PASS` cuenta como evidencia sin atravesarlo.

```
P-02   9 revisados · 9 válidos · 0 vacíos
P-04   9 revisados · 9 válidos · 0 vacíos
P-05   8 revisados · 8 válidos · 0 vacíos
```

Sensibilidad demostrada mutando `BR-02`, `BR-03` y las guardas de pertenencia: **nueve casos
fallaron**, código revertido en el acto con `git diff` limpio.

Y el filtro se cobró dos correcciones en mi propio trabajo. La primera afirmación de
aislamiento que escribí decía `not.toBe(201)`, que pasa con cualquier rechazo y no demuestra
pertenencia: el mismo vicio de `R-72`, en un test nuevo. Se reescribió con control y
tratamiento. La segunda: `R-66` —`/me` devuelve la empresa persistida y no la activa— hizo
que los fixtures se crearan en la empresa equivocada. Estaba registrado como P3 documental;
en la práctica cuesta tiempo de diagnóstico.

## 23. Defectos de aplicación descubiertos

```
P0: 0   ·   P1: 0   ·   P2/P3: 0
```

Ninguno. Los tres procesos operan conforme a su spec.

## 24. Cobertura

**Nivel de proceso** —la unidad de certificación que fija `GA-REM-016`:

```
Procesos certificados / procesos aplicables  =  4 / 15  =  26,7 %
Antes de esta tanda                          =  1 / 15  =   6,7 %
```

**Nivel de requisito**: no se recalcula el `21 / 60` anterior. Ese numerador no está
desglosado por requisito en ningún artefacto, de modo que sumarle los pasos de los tres
procesos sería aritmética inventada. `§59` exige mapeo `TEST → REQUIREMENT → AC → EVIDENCE`
y ese mapeo no existe todavía. Queda anotado como trabajo pendiente, no rellenado a ojo.

Lo que sí puede afirmarse: los tres procesos aportan **28 pasos documentados** con evidencia
E2E ejecutada y validada.

## 25. Siguiente candidato

`P-11` (activación manual de lotes) es el único que queda en `READY_FOR_E2E`. `R-67` mejoró
su posición —un lote activado manualmente ya puede operar—, pero arrastra **`R-47`**:
`POST /lots` ignora el `start_date` recibido, lo que impide registrar eventos retroactivos
en un lote recién creado. Para un proceso cuyo propósito es incorporar lotes **ya en
marcha**, eso es un bloqueo de fondo, no un detalle.

`R-47` vive en `GA-REM-019` y no se corrige aquí. **No se avanza sobre `P-11`** mientras siga
abierto.


---

# Recuperación de procesos `PARTIAL` — selección por evidencia

## Cómo se eligió el frente

Antes de tocar código se levantó `PARTIAL_PROCESS_BLOCKER_MATRIX.md`, con el alcance real de
cada bloqueante sobre los **10** procesos `PARTIAL` (no 9: `P-08` figura como `PARTIAL` con
bloqueo externo, no como categoría aparte).

Hizo falta depurar la fuente: `audit/06` es anterior a las Waves 1–3 y varios de sus huecos
ya no existen —`mortality_recording` 500, `LotDetailPage` rota, permisos sin enforcement—.
Contarlos habría inflado el alcance de bloqueantes ya resueltos.

**La hipótesis de partida no se sostuvo.** `lot_closure` figura como paso obligatorio en un
solo proceso (`spec.md §4.8`), así que `R-73` tiene **fan-out 1**. El de mayor alcance es
`GA-TD-014`, con **3**.

## Por qué no se eligió el de mayor alcance

`GA-TD-014` está diferido por `C-15` con una razón explícita: enviarlo activa `BR-11` y
`BR-18`, hoy inertes, lo que cambia el comportamiento para los operadores y depende de
`RC-07`, decisión del propietario que sigue abierta. Elegirlo habría sido tomar por mi cuenta
una decisión de negocio ya deliberada.

Entre los bloqueantes **accionables** todos tienen fan-out 1, así que decidió el criterio
siguiente: corrección y criticidad de ciclo. `R-73` era el único que dejaba un endpoint
devolviendo 500 siempre, en el paso terminal del ciclo productivo.

```
SELECTED_NEXT_BLOCKER = R-73   ·   por corrección, no por alcance
```

## Resultado

`R-73`, `R-74` y `R-75` certificados. Backend 321/0. E2E 80/80.

**Ningún proceso pasó a `CERTIFIED`.** `P-06` sigue `PARTIAL` por `GA-TD-014` y
`GA-REQ-037`. Se declara sin adornos: el trabajo cerró tres defectos reales —uno de ellos
llevaba roto desde siempre el único camino de cierre de lote del sistema— pero no movió la
cuenta de procesos, y la matriz de alcance ya lo anticipaba.

## Lo que conviene decidir ahora

`GA-TD-014` es el único bloqueante conocido con fan-out mayor que uno y su raíz no es
técnica. Mientras `RC-07` siga abierta, `P-01`, `P-03` y `P-06` no pueden certificarse por
mucho que se remedie a su alrededor.


---

# Gate A + Gate B · gobierno de la certificación (2026-09-05)

Checkpoint documental. **No se modificó código de aplicación.**

## Gate A · ¿la evidencia es de la clase que la spec exige?

`GA-REM-016 AC05` prohíbe certificar por pantalla. No pide interfaz: pide `E2E` de proceso.
Ninguna regla obligatoria de los cinco procesos certificados —`docs/12 R1`…`R9` para `P-07`,
`docs/02 §3.9.2` para `P-11`, `BR-02`/`BR-03` para los demás— menciona la interfaz.

```
CERTIFIED = 5 / 15   (sin cambio)
```

Corrección de etiqueta: `API_E2E`, no `UI_E2E`. Y una precisión sobre mi propia corrección
anterior, que fue más amplia de lo debido: **ningún documento del repositorio afirmó nunca
«UI E2E»**. El error estuvo en la consola. Los informes archivados dicen desde el principio
que la unidad es el proceso, no la pantalla.

## Gate B · ¿qué decisión falta exactamente?

La respuesta esperada era «`RC-07`». **Las fuentes dicen otra cosa.**

`RC-07` es la política de mortalidad frente a SAP, y `RR-07` la acotó por escrito al mapeo de
mortalidad dentro de `GA-REM-017`. No cubre la orden de compra. `docs/16` separa además las
cinco decisiones del cliente de la validación de cantidad contra la orden, y las pone en
fases distintas del plan. `GA-REM-010`, la otra dependencia citada por `C-15`, está
`CERTIFIED`.

La decisión que sí falta es más estrecha y se registra como `OD-04`: **¿existen entregas
parciales contra una misma orden de compra?** De eso depende activar una regla o dos.

```
RC-07  = OWNER_DECISION_REQUIRED   (mortalidad · sin cambio)
OD-04  = OWNER_DECISION_REQUIRED   (orden de compra · nueva)
```

## Tres correcciones a la matriz de ayer

Leer las fuentes una por una invalidó tres entradas propias: `GA-TD-014` no depende de
`RC-07`; el hueco de `PUT` de `P-12` ya estaba cerrado; y `R-60` no es el auto-enlace
—corregido por `GA-REM-008`— sino un endurecimiento P2 alcanzable solo por Super Admin.

## Dos hallazgos nuevos, salidos de leer la spec

```
R-76 · docs/12 R7 «un lote no puede cerrarse si tiene registros sin aprobar» no está
       implementado. P1. El E2E de P-06 cierra lotes con nueve eventos sin aprobar y
       recibe 200.

R-77 · la regla de no duplicar documentos SAP es BR-11 en la spec y BR-10 en el código;
       el contrato de error devuelve una regla equivocada. P2.
```

Ninguno se corrige aquí. Quedan abiertos y registrados.

## Siguiente frente

```
NEXT_ACTIONABLE_BLOCKER = P-10 · trazabilidad generacional
```

Único proceso `PARTIAL` con los defectos funcionales ya corregidos: le falta endurecer
`R-60` y **escribir su E2E de proceso**. Los demás exigen desarrollo de interfaz o
funcionalidad nueva, o no cierran su proceso aunque se resuelvan.


---

# `P-10` + `R-60` · `GA-REM-030` (2026-09-05)

## Resultado

```
R-60 = CERTIFIED          P-10 = PARTIAL — BLOCKED_BY_DEFECT (R-78)
CERTIFIED = 5/15          PARTIAL = 10/15        (sin cambio)
```

## `R-60`, en su forma real

No era «claves sin comprobar pertenencia» sino algo más ancho: los dos endpoints de enlace
manual construían la entidad **directamente desde el cuerpo**, sin pertenencia y sin
existencia. Como `EggBatch` y `ChickBatch` no declaran `company_id`, un vínculo entre
compañías produce un registro sin dueño posible — y es la puerta de escritura capaz de
fabricar el estado que `GA-REM-008 AC06`, ya certificado, promete imposible.

La regla se resolvió por norma: pertenencia del actor (patrón existente, con la exención del
Super Admin sin contexto intacta) **y** coherencia del par, que vincula a todo actor porque es
integridad del dato y no autorización. No se tocó el RBAC.

## Lo que la puerta de sensibilidad descubrió

La primera pasada de mutación **no rompió nada** al retirar dos de las tres reglas: mis
sujetos tenían empresa, de modo que la pertenencia del actor rechazaba antes y las otras dos
podían desaparecer sin que ninguna prueba lo notara. Se rehicieron con un Super Admin **sin
contexto**, el único actor para el que esa regla se abstiene. Ahora las tres son sensibles.

Vale la pena decirlo porque es el caso que justifica la puerta: nueve pruebas en verde no
probaban dos de las tres reglas que decían proteger.

## Por qué `P-10` no se certifica

Al recorrer la cadena entera —no un endpoint suelto— apareció `R-78`: el vínculo generacional
automático **no se crea en el orden natural**. La creación vive solo en la rama del despacho,
que exige una recepción previa; las dos ramas de recepción se limitan a actualizar un vínculo
que no existe. En la operación real se despacha antes de recibir, así que no se crea ninguno.

Y con él `R-79`: la prueba que certificaba `GA-REM-008 AC01` afirma
`"egg_batch" in crudo.lower()`, cierto siempre porque la respuesta contiene la clave
`egg_batches_sent`. Esa es la razón de que `R-78` sobreviviera a una certificación.

```
GA-REM-008 AC01 = NOT_EVIDENCED    (informe histórico conservado sin modificar)
```

## Sobre mi recomendación anterior

Señalé `P-10` como la menor distancia a la certificación porque sus defectos figuraban como
corregidos y certificados. Era correcto con la evidencia disponible y ha resultado falso. La
distancia real no era visible en ninguna matriz, y solo se supo ejecutando el proceso
completo. Es el argumento de por qué se certifica el proceso y no la capacidad.

## Regresión

```
backend  330 pasan · 49 omitidas · 0 fallos    (antes 321)
E2E       85/85                                 (antes 80)
frontend  no reejecutado — ningún cambio de frontend
```


---

# `P-10` certificado · `R-78` + `R-79` · `GA-REM-031` (2026-09-05)

```
R-78 = CERTIFIED    R-79 = CERTIFIED    P-10 = CERTIFIED (12 de 12 pasos)
CERTIFIED 6 / 15    PARTIAL 9 / 15
```

## El orden importó

`spec.md §4.9` dice que el vínculo se crea al registrar despacho **+** recepción. La
conjunción es simétrica; la implementación no lo era. La creación vivía solo en la rama del
despacho, que busca una recepción ya registrada, y las dos ramas de recepción se limitaban a
actualizar un vínculo previo. En el orden natural —se despacha antes de recibir— no se creaba
ninguno **nunca**.

## Por qué nadie lo había visto

`test_traceability.py` afirmaba `"egg_batch" in crudo.lower()`, cierto siempre porque la
respuesta contiene la clave `egg_batches_sent`. Esa prueba era la evidencia de
`GA-REM-008 AC01`. Un `PASS` que no puede fallar no es evidencia, y por eso el defecto
atravesó una certificación intacto.

Se corrigió **la prueba antes que la aplicación**, deliberadamente: reparada, se puso roja
por la causa exacta —«hay 0 vínculos»— y eso reprodujo `R-78` con evidencia fuerte.

## La sensibilidad certificó las dos cosas a la vez

Al desactivar la creación en recepción fallaron 3 pruebas de recepción **y la de
`GA-REM-008 AC01`**, que antes pasaba con el comportamiento ausente. Las 9 de pertenencia
siguieron verdes: la mutación era específica. No hizo falta una segunda mutación artificial.

## Un hallazgo aparecido al cruzar la medianoche

`R-80`: la fecha de negocio se ancla al día **local del servidor** y `created_at` se guarda
como instante **UTC**. Entre una medianoche y otra difieren, y un lote recién creado tiene
`start_date` posterior a su propio alta. Se manifestó como tres fallos de suite —dos en
backend, uno en E2E—, **verificados como previos a este cambio**. Las pruebas se repararon en
el marco de lo que cada una mira; el producto no se tocó y `R-80` queda abierto.

## Regresión

```
backend  335 pasan · 49 omitidas · 0 fallos    (antes 330)
E2E       85/85
frontend  sin cambios — no reejecutado
```
