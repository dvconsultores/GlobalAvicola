# MATRIZ DE DISPOSICIÓN DE LOS TESTS HEREDADOS

**`GA-REM-016`, enmienda de recuperación** · 2026-09-05 · 23/23 con disposición razonada

---

## 1. Cómo se decidió cada caso

Para cada test se respondió una sola pregunta, en este orden:

```
¿el REQUISITO sigue vigente?
    sí  → ¿el flujo cambió?   sí → REWRITE     no → REPAIR
    no  → ¿hay evidencia normativa?  sí → RETIRED_SUPERSEDED   no → BLOCKED_BY_SPEC_GAP
```

Una ruta retirada **no** es un requisito retirado. `/processes` redirige hoy a
`/menu/poultry`, pero `processCatalog.ts` sigue declarando las mismas **seis etapas**
avícolas con sus rutas en `STAGE_PATH_MAP`. El requisito no se movió; la URL sí.

## 2. `tests/e2e.spec.ts` — 9 casos · **ejecutados y en verde**

| # | Caso | Requisito | Flujo anterior | Flujo vigente | ¿Cobertura necesaria? | Decisión | Sustituto |
|--:|---|---|---|---|:--:|---|---|
| 1 | login redirects to dashboard | autenticación | `admin`/`admin` | `test_admin` + entorno | sí | `REPAIR` | — |
| 2 | dashboard loads for authenticated user | el panel carga | ídem + `locator('h1')` | encabezado por nombre | sí | `REPAIR` | — |
| 3 | mobile viewport shows bottom nav | navegación inferior móvil (`spec.md:286`) | `nav` en `/login` | con sesión y vista móvil | sí | `CORRECT_EXPECTATION` | — |
| 4-9 | farm_inspection × 6 | inspección por galpón | bloqueados por login | mismos, autenticados | sí | `REPAIR` | — |

El caso 9 (`second house row can be deleted`) llevaba además una suposición oculta: que el
formulario arranca con una fila. Arranca con dos. Se comprueba por recuento, que expresa el
mismo requisito sin depender de un estado que el test no controla.

## 3. `tests/operations.spec.ts` — 14 casos

Ninguno se autenticaba. Además, todos apuntaban a `/processes`, sustituida por un menú
jerárquico: `/menu/poultry` → 4 categorías → 6 etapas en `/poultry/…`.

| # | Caso | Requisito | Flujo anterior | Flujo vigente | ¿Cobertura necesaria? | Decisión | Sustituto |
|--:|---|---|---|---|:--:|---|---|
| 10 | should display 6 process cards | las 6 etapas avícolas existen y son alcanzables | 6 `<a href="/processes/…">` | `/menu/poultry` jerárquico | **sí** | `REWRITE` | «las 4 categorías se muestran» + «las 6 etapas son alcanzables» |
| 11 | cards with icons and descriptions | cada opción se presenta con descripción | ídem | `MenuCard` con descripción | sí | `REWRITE` | «cada categoría muestra su descripción» |
| 12 | navigate to process stage when clicked | navegar de la categoría a la etapa | clic en `<a>` | clic en `MenuCard` | sí | `REWRITE` | incluido en «las 6 etapas son alcanzables» |
| 13 | helpful hint at bottom | orientación al usuario en el hub | `Toca cualquier proceso` | `Elige una opción` | sí | `REWRITE` | «el hub orienta sobre qué hacer» |
| 14 | expand timeline item when clicked | la etapa muestra su cronología de operaciones | `/processes/broiler` | `/poultry/broiler` | sí | `REWRITE` | «la etapa muestra su cronología» |
| 15 | allow lot selection | elegir el lote sobre el que se opera | ídem | ídem | sí | `REWRITE` | «la etapa permite elegir lote» |
| 16 | navigate to operation form when registering | desde la etapa se registra una operación | ídem | ídem | sí | `REWRITE` | «la etapa lleva al formulario» |
| 17 | welcome header on mobile | el usuario móvil aterriza donde debe | panel en `/` | `/` redirige a `/menu/poultry` | sí | `REWRITE` | «el usuario móvil aterriza en el menú avícola» |
| 18 | display 3 KPI cards | los KPI son accesibles | 3 tarjetas en `/` | ruta `/kpi` en la navegación inferior | sí | `REWRITE` | «los KPI son alcanzables desde la navegación» |
| 19 | 6 process cards on mobile | ídem que 10, en móvil | `a[href*="/processes/"]` | menú jerárquico | sí | `REWRITE` | cubierto por 10 + 17 |
| 20 | quick actions buttons | accesos rápidos `Alimento` · `Pesaje` | panel móvil | **no existe**: `Pesaje` no aparece en ninguna parte del frontend | **no** | `RETIRED_SUPERSEDED` | el registro se alcanza por el menú → etapa → formulario (caso 16) |
| 21 | navigate to form from quick action | ídem | ídem | ídem | **no** | `RETIRED_SUPERSEDED` | caso 16 |
| 22 | responsive grid on mobile | el hub se adapta a móvil | contaba `<a href>` | rejilla de `MenuCard` | sí | `REWRITE` | «el menú se muestra en viewport móvil» |
| 23 | accessible process cards | las opciones son alcanzables por teclado/rol | `<a>` con `href` | `MenuCard` como control | sí | `REWRITE` | «las opciones exponen un rol accesible» |

## 4. Los dos casos retirados

`quick actions buttons` y `navigate to operation form from quick action` esperaban un panel
móvil con accesos directos `Alimento` y `Pesaje`. `Pesaje` **no existe en ninguna parte del
frontend**, y para un usuario de vista móvil la raíz ya no muestra un panel: redirige a
`/menu/poultry` (`App.tsx:71`).

No es que el requisito se haya incumplido: **se sustituyó**. Registrar una operación se
alcanza hoy por menú → etapa → formulario, y ese camino queda cubierto por el caso 16
reescrito. Sin pérdida de cobertura obligatoria (`AC09`).

Se registra aquí y no se borran en silencio (`§32`): el test original, su requisito, el
motivo y la cobertura sustituta quedan documentados.

## 4-bis. Los 12 casos que «pasaban» — `R-72`

Al reescribir `operations.spec.ts` apareció algo que la clasificación no había mirado,
porque solo se ocupaba de los fallos: de los 26 casos del fichero, **12 pasaban**. Y
pasaban sin autenticarse, exactamente igual que los 14 que fallaban.

La diferencia no era el sistema. Era que sus afirmaciones **no podían fallar**:

| Caso | Afirmación | Por qué siempre pasa |
|---|---|---|
| should show progress bar | `expect(progressBar).toBeTruthy()` | un `Locator` de Playwright es un objeto; siempre es *truthy*, exista o no el elemento |
| should be keyboard navigable | `expect(focusedElement).toBeTruthy()` | ídem |
| should have aria labels on expandable items | `expect(count).toBeGreaterThanOrEqual(0)` | un recuento nunca es negativo |
| should display operations as timeline items | `count > 0` sobre `button` | la pantalla de login tiene botones |
| should show process header with color | `h1` visible y con clase | la pantalla de login tiene un `h1` con clase |
| ProcessHubPage should load quickly | tiempo de carga < 3 s | medía la carga del **login** |
| Timeline expansion should be instant | ídem | ídem |
| should display Spanish translations | textos genéricos | los de la pantalla de login |
| should have complete translations | ausencia de claves crudas | ídem |
| should work on mobile / tablet / desktop viewport | la página responde | la de login |

**Doce de los quince `PASS` del baseline congelado eran ilusorios.** No cubrían ningún
requisito: o afirmaban tautologías, o medían la pantalla de login.

Se retiran los doce. `AC09` exige no perder cobertura obligatoria, y aquí no había ninguna
que perder: una afirmación que no puede fallar no cubre nada. Lo que sí cubrían de verdad
—que la etapa presente sus operaciones, que sea accesible, que responda en móvil— está en
los casos reescritos, ahora con afirmaciones que pueden fallar.

Queda registrado como hallazgo **`R-72`**, y cambia cómo debe leerse el baseline histórico:
no se reescribe, se anota.

## 5. Recuento

| Disposición | Casos |
|---|--:|
| `REPAIR` | 8 |
| `CORRECT_EXPECTATION` | 1 |
| `REWRITE` | 12 |
| `RETIRED_SUPERSEDED` | 2 |
| `BLOCKED_BY_SPEC_GAP` | 0 |
| **Total de los 23 fallos** | **23** |
| `RETIRED_VACUOUS` (`R-72`, además de los 23) | 12 |

El fichero `operations.spec.ts` pasa de 26 casos a 10. No es una pérdida de cobertura: 14
fallaban sin llegar a comprobar nada y 12 pasaban sin poder fallar. Los 10 que quedan
comprueban requisitos vigentes y se ha verificado que fallan cuando deben.

## 6. Lo que apareció al desenmascarar

La clasificación previa dijo `0 / 23` defectos de aplicación. Tras ejecutar los tests
recuperados, **se mantiene**: ninguno de los casos desbloqueados reveló un defecto del
sistema. Los dos hallazgos nuevos son de los propios tests:

| Hallazgo | Naturaleza |
|---|---|
| `locator('h1')` resuelve a tres encabezados una vez dentro | ambigüedad del selector; el panel sí tiene `<h1>Dashboard</h1>` |
| el formulario de inspección arranca con **dos** galpones, no uno | suposición del test sobre un estado que no controla |

Ninguno exige tocar código de negocio (`AC11`).
