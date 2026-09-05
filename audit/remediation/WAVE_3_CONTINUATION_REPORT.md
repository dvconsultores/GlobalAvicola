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

## 8. `R-72` — doce tests pasaban sin poder fallar

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
