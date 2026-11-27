# CERTIFICACIÓN LOCAL — GA-O28-FE02-USER-BU-PANEL-FLAKINESS

Spec: `specs/013-admin-rbac-uat/spec.md` §8 (Amendment O-28, AC-O28-01..04). Baseline `develop` = `ec84718`; IMPL = `906e198`; `main` = `1587073` (sin tocar). Rama `develop`; sin PR, sin `main`, sin producción. Incubadora, BR-03, Cutover y backend: sin cambios.

## 1. Clasificación

```text
O-28 = TEST_DEFECT (ASYNC_RACE en el punto de sincronización del test)
PRODUCT_DEFECT = NO · STATE_LEAK = NO · QUERY_CACHE_LEAK = N/A · FAKE_TIMER_LEAK = NO · ROUTER_LEAK = N/A
```

## 2. Tests exactos

| Archivo | Tests |
|---|---|
| `frontend/src/pages/users/__tests__/gaFe02.userBuPanel.test.tsx` (GA-FE-02, monta `UsersPage`) | AC-UBU-02/03/04 identidad y estados · AC-UBU-05/06 conceder · AC-UBU-08/09 revocar · AC-UBU-11 uno mismo · AC-UBU-19 fallo de carga · AC-NAV-03 sin permiso |
| `frontend/src/pages/users/__tests__/uatAdminRbac.userBuPanel.test.tsx` (SPEC 013 Lote F1, monta `UserBusinessUnitsButton`) | AC-UI-01 portal · AC-UI-02 concesión viva · AC-UI-03 empresa/usuario · AC-UI-04 confirmación |

Fallos observados: AC-UBU-02/03/04, AC-UBU-05/06, AC-UBU-08/09, AC-UI-01, AC-UI-03. Comparten el mismo helper `openPanel` y el mismo componente. Ningún otro test usa el panel.

## 3. Reproducción antes del fix (HEAD `ec84718`, `evidence/runs/pre_*`)

| Modo | Resultado |
|---|---|
| A · cada uno de los 10 tests por separado (`-t`), ×3 | 30/30 PASS |
| B · los dos archivos, ×10 | **8/10** (2 corridas con fallo: AC-UBU-02/03/04, AC-UBU-05/06) |
| C · subsuite SPEC 013 / GA-FE-02 (19 archivos, 197 tests), ×3 | **1/3** (AC-UBU-02/03/04 ×2) |
| D · vitest completa, ×2 | 2/2 (en las 4 corridas completas previas de BR-03: 4/4 con fallo) |
| F · orden aleatorio (`--sequence.shuffle`, semillas 1001..1010), ×10 | 10/10 PASS |

Mensajes: `Unable to find an element with the text: users.businessUnits.companyState | Engorde | Progenitoras`. **En los 4 fallos el DOM contenía el indicador `role=status` «common.loading»**: el panel aún cargaba.

## 4. Causa raíz

Cadena del componente (`UserBusinessUnitsButton.tsx`, estado local con `useState`, `fetch` vía `services/api`, sin React Query, Redux, Suspense ni router):

```text
click → setOpen(true) + load() → setLoading(true)   ⇒ render: título del Modal + «cargando»
Promise.all(GET /business-units, GET /users/{id}/business-units)
→ setUnits + setGrants + setLoading(false)          ⇒ render: cabeceras de estado + filas
```

`openPanel` daba el panel por abierto al ver el **título**, que existe desde el primer render, y luego consultaba filas con `getBy*` síncrono. Que las filas existieran dependía de que la carga ya se hubiera resuelto. Eso dependía del orden entre la tarea con la que Testing Library cierra `findBy*` y la tarea del planificador de React que pinta el resultado, que varía con la carga del proceso. Por eso el fallo es raro aislado, frecuente en la subsuite y cambia de test. El producto es correcto: indicador → contenido. La E2E P-17-B lo verifica en navegador real con esperas con reintento.

## 5. Fix (solo tests + spec)

Helper `esperarCargaDelPanel()` en los dos archivos, llamado al final de `openPanel`:

```text
waitFor: «common.loading» ausente  Y  cabecera users.businessUnits.companyState presente
```

Contrato asíncrono: «abrir el panel» = la carga terminó y el contenido se ve. Es el mismo hecho que espera el usuario. Sin `setTimeout`, sin promesas de pausa, sin `waitFor(() => true)`, sin timers falsos. El componente no cambia.

## 6. Aislamiento de estado (revisado, sin cambios necesarios)

| Elemento | Estado |
|---|---|
| Query cache | no aplica (no hay React Query) |
| Mocks | `get/post/del/put` y toasts con `mockReset` + `mockApi()` en `beforeEach`. `vi.mock` es por archivo. |
| Timers | ningún `useFakeTimers` en los archivos. El `setTimeout(focus, 10)` del Modal es inocuo. |
| Router | `UsersPage` y el botón no dependen de router en estos tests |
| Storage / stores | `useAuthStore` y `useCompanyStore` se reescriben con `setState` en `beforeEach`. No se usa storage. |
| DOM | limpieza automática de Testing Library (`globals: true`) |

El orden aleatorio 10/10 descarta dependencia de orden y fuga de estado.

## 7. Aserciones

```text
Removed: NONE · Relaxed: NONE · Skipped: NONE (único skip de la suite: condicional preexistente `skipIf(!treesEqual)` de SPEC 016)
```

## 8. Sensibilidad y falso verde (tras `906e198`, restauración `git restore --source=906e198`)

| Variante | Esperado | Resultado |
|---|---|---|
| S1 patrón anterior reintroducido, red instantánea, dos archivos ×20 | falla alguna | **0/20: NO_CUMPLE** (la carrera natural no aparece en ese modo) |
| S1b patrón anterior, red instantánea, subsuite SPEC 013 ×10 (modo de la reproducción C) | falla alguna | **1/10 con fallo: OK** (AC-UBU-05/06) |
| S2 patrón anterior + respuesta de unidades diferida 20 ms (red lenta) ×5 | falla siempre | **5/5: OK** (8 tests caen) |
| S3 control: patrón nuevo + misma respuesta diferida ×5 | pasa siempre | **0/5 con fallo: OK** |
| S4 falso verde: la API devuelve `[]` unidades ×3 | falla siempre | **3/3: OK** (6 tests que esperan unidades caen) |

S2 frente a S3 es la prueba determinista: el patrón anterior depende de la carrera; el nuevo espera la carga. S4 prueba que la espera no oculta la ausencia de datos. Las pausas de S2 y S3 fueron temporales y nunca se commitearon (`TREE=CLEAN`).

## 9. Estabilidad

| Campaña | Pre-commit (árbol de `906e198`) | Post-sensibilidad (HEAD `906e198`) |
|---|---|---|
| Archivos afectados ×20 | **20/20** | **20/20** |
| Subsuite SPEC 013 / GA-FE-02 ×10 (197 tests) | **10/10** | **10/10** |
| Vitest completa ×3 | **822/822 ×3** | **821 + 1 skip condicional, 0 fallos ×3** |
| `tsc -b` / `vite build` | RC 0 / OK | RC 0 / OK |

## 10. E2E

- Relevantes `--workers=1` (P-17 A..G, S2-01/P17e, P18c P1..P3): **14/14**. Cubren primer acceso y panel con una unidad (P-17-B: revocar → denegar → re-conceder), recarga y autoridad (P-17-A, P-17-E), re-entrada tras reactivación (P-17-C) y usuario sin unidades (P2b).
- Completa `--workers=1`: **239 passed, 0 failed**.
- Observación: ninguna E2E concede **varias** unidades al mismo usuario. Ese caso está cubierto en vitest (4 unidades, 2 concesiones con historia).
- La E2E se ejecutó sobre el árbol con el fix, antes del commit. El commit solo cambia archivos de vitest y la spec, que no entran en el build E2E.

## 11. Backend / runtime

`BACKEND_PRODUCT_CHANGE = NO` (sin migraciones ni schemas). Tampoco hay cambio de frontend productivo: el runtime de UAT solo cambia de SHA por el despliegue del monorepo. Paridad verificada tras el push.

## 12. Observaciones

- La E2E completa reescribe evidencia versionada de otras specs: restaurada con `git restore`, fuera de los commits.
- La evidencia versionada incluye los logs y resúmenes de cada corrida (`evidence/runs/*/run_*.log`, `summary.txt`, `rc.txt`). Los JSON de vitest (~7 MB) no se versionan.
- Desviación de rol: el parche literal, los scripts de campaña y sensibilidad y este documento los redactó Claude. DeepSeek aplicó el parche e hizo los commits. Las campañas las ejecutó Claude, como prevé el mandato §3.

## 13. Decisión local

`O-28 = CLOSED` · `GA-FE-02 = CERTIFIED` · `HATCHERY_V4 = CERTIFIED` · `BR03_UNKNOWN_SAFETY = CERTIFIED` · `OWNER_ACCEPTED = NO`.
