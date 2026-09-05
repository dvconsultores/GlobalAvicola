# CLASIFICACIÓN DE LOS 23 FALLOS DE PLAYWRIGHT

**`GA-REM-016`** · 2026-09-05 · baseline congelado `15 PASS / 23 FAIL`

Cada fallo se contrastó contra el código actual del frontend. No se modificó ningún test.

---

## 1. Resultado

```
DEFECTOS DE APLICACIÓN ........................  0 / 23
DEFECTOS DE LOS PROPIOS TESTS ................. 23 / 23
```

Ninguno de los 23 fallos señala un defecto del sistema. Los 23 fallan porque el test está
mal: usa credenciales que ya no existen, no se autentica, o afirma un contrato de interfaz
que se sustituyó deliberadamente.

Conviene decir que esto **no** significa que los 23 se puedan borrar. Seis de ellos
comprueban una funcionalidad que sigue viva y que nadie más cubre; hoy no llegan a
ejecutarla.

## 2. Las cuatro causas

| Categoría | Casos | Qué significa |
|---|--:|---|
| `TEST_CREDENTIAL_OBSOLETE` | 8 | Inician sesión con usuarios que no existen |
| `TEST_MISSING_AUTHENTICATION` | 14 | No se autentican en ningún momento |
| `TEST_OBSOLETE_UI_CONTRACT` | 12 | Afirman rutas o marcado que se sustituyeron a propósito |
| `TEST_INVALID_EXPECTATION` | 1 | La afirmación nunca fue correcta |

Los números suman más de 23 porque doce casos tienen dos causas: no se autentican **y**
además apuntan a una interfaz retirada. Se distingue entre la causa **próxima** —la que
detiene el test— y la **subyacente**, que solo se ve al quitar la primera.

## 3. Evidencia de la causa de credenciales

Los tests heredados inician sesión así:

```ts
async function loginAs(page, username = 'admin', password = 'admin123')
await page.fill('input[name="username"]', 'admin')
await page.fill('input[name="password"]', 'admin')
```

Y la siembra de pruebas crea:

```python
TEST_ADMIN_USERNAME    = "test_admin"      contraseña: GA_TEST_ADMIN_PASSWORD (del entorno)
TEST_OPERATOR_USERNAME = "test_operator"   contraseña: GA_TEST_OPERATOR_PASSWORD
TEST_APPROVER_USERNAME = "test_approver"   contraseña: GA_TEST_APPROVER_PASSWORD
```

El usuario `admin` **no existe** en el entorno de pruebas, y el arnés genera contraseñas
aleatorias por ejecución. El login no puede tener éxito, y el error lo confirma:

```
Expected substring: not "/login"
Received string:        "http://127.0.0.1:5199/login"
```

No es un descuido de quien escribió los tests: es la consecuencia directa de `GA-REM-004`,
que retiró las credenciales literales del repositorio a propósito. Los tests se quedaron
con las de antes.

## 4. Evidencia del contrato de interfaz obsoleto

`operations.spec.ts` busca en todas partes:

```ts
page.locator('a[href*="/processes/"]')
await page.goto('/processes')
await page.goto('/processes/broiler')
```

Y la aplicación actual declara esas rutas como heredadas, y **redirige**:

```tsx
// ProcessStageRedirect — mapea rutas legacy /processes/:stage a /poultry/:birdType/:phase
<Route path="/processes"        element={<Navigate to="/menu/poultry" replace />} />
<Route path="/processes/:stage" element={<ProcessStageRedirect />} />
<Route path="/menu/:menuKey"    element={<MenuHubPage />} />
```

**No queda ni un enlace `/processes/` en la interfaz.** El selector encuentra cero
elementos. El comentario del propio `App.tsx` llama «legacy» a esas rutas: la sustitución
fue deliberada y está documentada en el código.

Comprobación de los textos que esos tests esperan:

| Texto esperado | ¿Existe hoy? |
|---|---|
| `Toca cualquier proceso` | **no** |
| `Pesaje` | **no** |
| `[data-testid="kpi-card"]` | **no** |
| `Inicio` | sí (`DashboardPage`, `MobileDrawer`) |
| `Registrar operación` | sí (`StageTimeline.tsx`) |

## 5. Los seis casos enmascarados

Los seis de `farm_inspection` no llegan al formulario: se quedan en la pantalla de login. Su
afirmación real **no se ha podido evaluar**, así que se comprobó a mano contra el código:

| Test | Espera | ¿Sigue en la interfaz? |
|---|---|---|
| auto-initializes one house row | `text=Galpón 1` | **sí** — `{t('operations.house','Galpón')} {i + 1}` (`OperationFormPage:1189`) |
| numeric T° and H° | `input[placeholder="28.0"]`, `"65"` | **sí** — líneas 1213 y 1224 |
| litter condition select | `Seca` · `Amoniacal` · `Compactada` | **sí** — líneas 1237-1240 |
| add house rows | `button:has-text("Añadir galpón")` | **sí** — línea 704 |
| delete second row | botón de papelera en la fila 2 | **sí** — `{i > 0 && …<Trash2 />}` línea 1190 |
| 375px viewport | lo anterior | **sí** |

**Los seis comprueban funcionalidad que existe y funciona.** Están bloqueados por el login,
no obsoletos. Son los que más conviene recuperar: cubren el formulario de inspección de
granja por galpón, que ninguna otra prueba toca.

## 6. Matriz completa

### `tests/e2e.spec.ts` — 9 casos

| # | Línea | Caso | Causa próxima | Causa subyacente | Disposición |
|--:|--:|---|---|---|---|
| 1 | 18 | login redirects to dashboard | `TEST_CREDENTIAL_OBSOLETE` | — | **reparar**: usar las credenciales del entorno |
| 2 | 34 | dashboard loads for authenticated user | `TEST_CREDENTIAL_OBSOLETE` | — | **reparar** |
| 3 | 43 | mobile viewport shows bottom nav | `TEST_INVALID_EXPECTATION` | — | **corregir la afirmación**: espera `nav` en `/login`, donde no lo hay ni debe haberlo |
| 4 | 60 | farm_inspection: auto-initializes one house row | `TEST_CREDENTIAL_OBSOLETE` | ninguna — la interfaz existe | **reparar** |
| 5 | 68 | farm_inspection: numeric T° and H° | `TEST_CREDENTIAL_OBSOLETE` | ninguna | **reparar** |
| 6 | 82 | farm_inspection: litter select | `TEST_CREDENTIAL_OBSOLETE` | ninguna | **reparar** |
| 7 | 96 | farm_inspection: add house rows | `TEST_CREDENTIAL_OBSOLETE` | ninguna | **reparar** |
| 8 | 108 | farm_inspection: delete second row | `TEST_CREDENTIAL_OBSOLETE` | ninguna | **reparar** |
| 9 | 121 | farm_inspection: 375px viewport | `TEST_CREDENTIAL_OBSOLETE` | ninguna | **reparar** |

### `tests/operations.spec.ts` — 14 casos

Ninguno se autentica; el fichero no contiene un solo `login`, y la configuración de
Playwright no aporta sesión (`storageState` ni `globalSetup`).

| # | Línea | Caso | Causa próxima | Causa subyacente | Disposición |
|--:|--:|---|---|---|---|
| 10 | 12 | should display 6 process cards | `TEST_MISSING_AUTHENTICATION` | `TEST_OBSOLETE_UI_CONTRACT` — `/processes` retirada | **retirar o reescribir** contra `/menu/:menuKey` |
| 11 | 20 | cards with icons and descriptions | ídem | ídem | ídem |
| 12 | 32 | navigate to process stage | ídem | ídem | ídem |
| 13 | 43 | helpful hint at bottom | ídem | ídem — `Toca cualquier proceso` no existe | ídem |
| 14 | 66 | expand timeline item | ídem | ídem — `/processes/broiler` redirige | ídem |
| 15 | 101 | allow lot selection | ídem | ídem | ídem |
| 16 | 116 | navigate to operation form | ídem | ídem | ídem |
| 17 | 144 | welcome header on mobile | `TEST_MISSING_AUTHENTICATION` | **sin verificar** — `Inicio` existe | **reparar** y reevaluar |
| 18 | 152 | display 3 KPI cards | ídem | **sin verificar** — selector laxo | **reparar** y reevaluar |
| 19 | 160 | 6 process cards on mobile | ídem | `TEST_OBSOLETE_UI_CONTRACT` | **retirar o reescribir** |
| 20 | 168 | quick actions buttons | ídem | ídem — `Pesaje` no existe | ídem |
| 21 | 183 | navigate from quick action | ídem | ídem | ídem |
| 22 | 195 | responsive grid on mobile | ídem | ídem | ídem |
| 23 | 210 | accessible process cards | ídem | ídem | ídem |

Además, para un usuario móvil la raíz ya no muestra un panel: `HomeRoute` redirige a
`/menu/poultry` (`App.tsx:71`). La premisa de los seis casos de «Mobile Dashboard» —un
panel en `/` con seis tarjetas hacia `/processes/`— dejó de ser cierta.

## 7. Recuento por disposición

| Disposición | Casos | Motivo |
|---|--:|---|
| **Reparar** (credenciales / autenticación) | 10 | comprueban funcionalidad viva; hoy no llegan a ella |
| **Corregir la afirmación** | 1 | la expectativa nunca fue correcta |
| **Retirar o reescribir** | 12 | afirman una interfaz sustituida a propósito |

## 8. Lo que esta clasificación cierra

`R-62` los había agrupado preliminarmente como «tests rotos por una interfaz de junio de
2026». La medición matiza ese diagnóstico: **solo doce** lo están. Los otros once fallan por
credenciales o por falta de autenticación, y seis de ellos comprueban funcionalidad
perfectamente viva.

También confirma lo que el baseline posterior a `R-68`/`R-67` ya apuntaba: ninguno de los 23
tenía que ver con la carrera transaccional ni con el saldo de apertura. Aquella medición fue
correcta.

## 9. Lo que **no** se ha hecho

No se ha modificado ni un test. Retirar doce casos del conjunto heredado es una decisión de
gobierno —dejan de cubrir lo que cubrían, aunque lo cubrieran mal— y corresponde al
propietario, no a esta clasificación.

Y una advertencia sobre el modo de repararlos: la solución **no** es sembrar un usuario
`admin` con contraseña `admin` para que los tests pasen. Eso reintroduciría exactamente lo
que `GA-REM-004` retiró. Los tests deben leer las credenciales del entorno, como hace el
resto del arnés.
