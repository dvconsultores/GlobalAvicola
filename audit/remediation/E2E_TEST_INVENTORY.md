# E2E TEST INVENTORY

**Fecha** 2026-09-04 · **Wave** 3 · **Spec** `GA-REM-016 AC01`

---

## 1. Estado de partida

`GA-REM-016` describía el problema: *«~80 casos E2E escritos que **nunca se han ejecutado**,
y 1 065 LOC de ellos son directamente inejecutables por falta de configuración»*.

Había una configuración —`frontend/playwright.config.ts`— y dos suites. La de la raíz no
la cubría ningún ejecutor, de modo que su estado real era **desconocido**.

---

## 2. Lo que impedía ejecutarla

Dos causas, ninguna de ellas «falta de configuración» a secas:

| Causa | Detalle |
|---|---|
| **`tests/operations.spec.ts:137`** | `test.use({ ...test.use(), … })`. `test.use()` sin argumentos no devuelve la configuración vigente: devuelve `undefined`, y esparcirlo lanzaba `Cannot convert undefined or null to object` **al descubrir el directorio entero**. Un fichero tumbaba la suite completa |
| `tests/integration-full.spec.ts` · `tests/integration-test.ts` | **no son tests**: son scripts con un `main()` que lanza chromium a mano. El primero lleva sufijo `.spec.ts` sin serlo |

La primera se corrigió —una línea, autorizada por `AC01`—. Las otras dos se declaran como
scripts en la configuración, no se borran: no es limpieza lo que toca aquí.

---

## 3. Configuración

`playwright.config.ts` en la raíz, con tres proyectos, uno de ellos documentado como
excluido:

| Proyecto | `testDir` | Ficheros | Estado |
|---|---|---:|---|
| `procesos` | `./e2e` | 3 | certificación de la Wave 3 |
| `heredada` | `./tests` | 2 | descubierta por primera vez |
| ~~`frontend`~~ | `./frontend/tests` | 4 | **no incluida** — ver §5 |

```
Total descubierto por la configuración de la raíz: 59 tests en 5 ficheros
```

---

## 4. Inventario

| Test ID | Process | Scenario | Role | Company | Expected | Actual | Status |
|---|---|---|---|---|---|---|---|
| `E2E-01-01` | Recepción de aves | sin sesión no se expone | anónimo | — | redirige a login | ✅ | **PASS** |
| `E2E-01-02` | Recepción de aves | happy path UI + API + BD | admin | A | 201 y 1 000 aves persistidas | ✅ | **PASS** |
| `E2E-01-03` | Recepción de aves | `BR-08` exige granja | admin | A | 400 con `rule=BR-08` | ✅ | **PASS** |
| `E2E-01-04` | Recepción de aves | `BR-19` período cerrado | admin | A | 400 con `rule=BR-19` | ✅ | **PASS** |
| `E2E-01-05` | Recepción de aves | rol sin permiso | aprobador | A | 403 | ✅ | **PASS** |
| `E2E-01-06` | Recepción de aves | deja rastro en auditoría | admin | A | entrada presente | ✅ | **PASS** |
| `E2E-01-07` | Recepción de aves | lote de otra empresa | operador | A→B | rechazo | ✅ | **PASS** |
| `E2E-02-01` | Control diario | mortalidad con causa, saldo baja | admin | A | 201, causa y saldo −10 | ✅ | **PASS** |
| `E2E-02-02` | Control diario | `BR-01` sobre el saldo | admin | A | 400, nada persiste | ✅ | **PASS** |
| `E2E-02-03` | Control diario | mortalidad cero | admin | A | rechazo | ✅ | **PASS** |
| `E2E-02-04` | Control diario | umbral configurado dispara alerta | admin | A | alerta `critical` | ✅ | **PASS** |
| `E2E-02-05` | Control diario | consumo de alimento con su tipo | admin | A | 250,5 kg persistidos | ✅ | **PASS** |
| `E2E-02-06` | Control diario | pesaje con muestra | admin | A | peso y `sample_size` | ✅ | **PASS** |
| `E2E-02-07` | Control diario | mortalidad en lote ajeno | operador | A→B | rechazo | ✅ | **PASS** |
| `E2E-03-01` | Revisión→Corrección→Aprobación | ciclo completo | operador+admin+aprobador | A | dato cambiado y aprobado | ✅ | **PASS** |
| `E2E-03-02` | ídem | `BR-14` segregación | operador | A | 403 | ✅ | **PASS** |
| `E2E-03-03` | ídem | rechazo con motivo | aprobador | A | estado `rejected` | ✅ | **PASS** |
| `E2E-03-04` | ídem | lista blanca de corrección | admin | A | 400 en 3 campos | ✅ | **PASS** |
| `E2E-03-05` | ídem | `R-32` estado por `PUT` | admin | A | 422 | ✅ | **PASS** |
| `E2E-03-06` | ídem | operador no aprueba ni rechaza | operador | A | 403 ×2 | ✅ | **PASS** |
| `E2E-03-07` | ídem | auditoría del ciclo | admin | A | >1 acción, sin secretos | ✅ | **PASS** |

**21/21 PASS.**

---

## 5. Suite heredada — primera ejecución

```
15 passed · 23 failed  (4,8 min)
```

| Clasificación | Nº | Detalle |
|---|---:|---|
| `VALID` | 15 | pasan tal cual |
| `BROKEN_BY_OLD_ASSUMPTION` | 23 | esperan elementos de una interfaz de junio de 2026, y **navegan sin autenticarse**: `/processes` redirige a `/login`, de modo que ningún selector aparece |
| `NOT_A_TEST` | 2 ficheros | `integration-full.spec.ts`, `integration-test.ts` |

Los 23 fallos se concentran en `ProcessHubPage`, el tablero móvil y las tarjetas de KPI:
UI que cambió con la refactorización de navegación y el cambio de paleta que
`GA-REM-016` ya citaba como evidencia (`frontend/test-results/.last-run.json` del
2026-06-25).

**No se reescriben.** `GA-REM-016` no autoriza rehacer la suite heredada, y hacerlo sería
expansión de alcance. Su estado queda medido, que es lo que faltaba: llevaba tres meses sin
que nadie supiera si funcionaba.

Destino: `GA-REM-019`, como `R-62`.

---

## 6. Suite del frontend — no ejecutada, y por qué

`frontend/tests/` (4 ficheros, ~50 casos) tiene configuración propia desde junio. Desde la
configuración de la raíz aparece como «No tests found»:

```
raíz/node_modules/@playwright/test        1.61.0   ← el ejecutor
frontend/node_modules/@playwright/test    1.61.1   ← donde se registran los tests
```

Dos instalaciones distintas. Los ficheros de `frontend/tests` importan `@playwright/test`,
que desde su directorio resuelve a la copia anidada; los tests se registran en una
instancia y el ejecutor mira la otra.

No es un fallo de los tests. Unificar las instalaciones es deuda registrada como **`R-61`**
(P3) en `GA-REM-019`: tocarlo aquí sería modificar dependencias del frontend sin spec que
lo autorice.

---

## 7. Trazabilidad

Cada caso de la Wave 3 se relaciona con su requisito:

```
REQ (spec §4.x / docs)  →  SPEC (GA-REM-016 + dependientes)  →  AC  →  E2E  →  EVIDENCIA  →  ESTADO
```

| Proceso | Specs que lo gobiernan | AC verificados |
|---|---|---|
| Recepción de aves | `spec.md §4.4/4.5/4.8` · `GA-REM-002` · `GA-REM-023` | `BR-08`, `BR-19`, RBAC, aislamiento, auditoría |
| Control diario | `spec.md §4.x` · `GA-REM-005` (`AC01`…`AC09`) | `BR-01`, umbral configurable, persistencia de causa y peso |
| Revisión→Corrección→Aprobación | `spec.md §4.10` · `docs/12` · `GA-REM-006`, `GA-REM-007` · `RR-01`, `RR-03` | `BR-09`, `BR-14`, lista blanca, `R-32`, auditoría |

Ningún caso se usa para certificar sin AC relacionado.
