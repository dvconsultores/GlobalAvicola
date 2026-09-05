# EJECUCIÓN DE RECUPERACIÓN DE PLAYWRIGHT — 01

**`GA-REM-016`, enmienda de recuperación** · 2026-09-05 · baseline nuevo, congelado

Los baselines anteriores **no se sobrescriben**. Son evidencia histórica y siguen donde
estaban: `PLAYWRIGHT_POST_R68_R67_BASELINE.md` (`15 PASS / 23 FAIL`) y
`BACKEND_TEST_BASELINE_RUN_01.md`.

---

## 1. Resultado

```
43 / 43 PASS · 0 FAIL · 0 ERROR · 0 SKIP
```

| Proyecto · fichero | Antes | Ahora |
|---|---|---|
| `e2e/proceso-01-recepcion-de-aves.spec.ts` | 7/7 | **7/7** |
| `e2e/proceso-02-control-produccion-diario.spec.ts` | 7/7 | **7/7** |
| `e2e/proceso-03-revision-correccion-aprobacion.spec.ts` | 7/7 | **7/7** |
| `tests/e2e.spec.ts` | 3/12 | **12/12** |
| `tests/operations.spec.ts` | 12/26 | **10/10** |
| **Total** | 36/59 | **43/43** |

## 2. Por qué el total baja de 59 a 43

Porque se retiraron 16 casos, y ninguno cubría nada:

```
14  fallaban sin llegar a comprobar nada  → reescritos en 10 casos equivalentes
12  pasaban sin poder fallar (R-72)       → retirados
```

Los 26 casos de `operations.spec.ts` se convierten en 10. Es una **reducción de recuento,
no de cobertura**: se conserva lo que esos tests querían comprobar y se descarta lo que no
comprobaba nada.

## 3. Disposición de los 23 fallos

| Disposición | Casos |
|---|--:|
| `REPAIR` — se quitó el bloqueo, las afirmaciones no se tocaron | 8 |
| `CORRECT_EXPECTATION` — la afirmación nunca fue correcta | 1 |
| `REWRITE` — el requisito vive, el flujo cambió | 12 |
| `RETIRED_SUPERSEDED` — con evidencia y cobertura sustituta | 2 |
| `BLOCKED_BY_SPEC_GAP` | 0 |

Y, fuera de los 23:

| `RETIRED_VACUOUS` (`R-72`) | 12 |
|---|--:|

Detalle caso por caso en [`PLAYWRIGHT_TEST_DISPOSITION_MATRIX.md`](PLAYWRIGHT_TEST_DISPOSITION_MATRIX.md).

## 4. Defectos de aplicación descubiertos al desenmascarar

```
0
```

La clasificación previa estimó `0 / 23`. Tras ejecutar de verdad los tests recuperados, se
confirma: **ninguno reveló un defecto del sistema.** Lo que apareció fueron tres suposiciones
equivocadas de los propios tests, y una mía:

| Hallazgo | Naturaleza |
|---|---|
| `locator('h1')` resuelve a tres encabezados con sesión iniciada | ambigüedad de selector; el panel **sí** tiene `<h1>Dashboard</h1>` |
| el formulario de inspección arranca con **dos** galpones, no uno | suposición sobre un estado que el test no controla; el borrado funciona |
| la vista por omisión de una etapa es una **rejilla**, no la cronología | el acceso al formulario está en los enlaces de la rejilla |
| *(mío)* cambié una afirmación correcta del panel por innecesaria | corregido: restaurada y solo acotado el selector |

## 5. Prueba de mortalidad (`AC12`)

Una afirmación que no puede fallar no certifica nada — lección que `R-72` deja bien
aprendida. Se comprobó con una mutación controlada de la aplicación:

```
placeholder="28.0"  →  "99.9"
test «farm_inspection: shows numeric T° and H° fields»  →  FALLA
```

Aplicación revertida; `git diff` limpio. Una segunda mutación resultó inefectiva —tocaba el
texto de reserva de i18n, que la traducción sobrescribe— y se descarta como prueba.

## 6. Cómo se reprodujo

```sh
bash scripts_e2e.sh
```

Base de pruebas aislada, esquema por el entrypoint real, semillas deterministas, backend en
8099 y frontend en 5199. El entorno compartido no interviene.

## 7. Lo que cambia en la lectura del baseline anterior

`PLAYWRIGHT_POST_R68_R67_BASELINE.md` registró `15 PASS / 23 FAIL`. Ese documento **no se
toca**: fue una medición correcta de lo que la suite hacía entonces.

Lo que cambia es su interpretación: **12 de aquellos 15 `PASS` eran vacíos**. La suite
heredada no cubría 15 requisitos; cubría 3. Se anota, no se reescribe.
