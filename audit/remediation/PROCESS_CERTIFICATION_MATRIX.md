# PROCESS CERTIFICATION MATRIX

**Fecha** 2026-09-04 · **Wave** 3 · **Spec** `GA-REM-016`

La unidad de certificación es el **proceso de negocio según la taxonomía propia del
proyecto** (`processCatalog.ts`, 15 procesos en `audit/06_PROCESS_COVERAGE.md`). No la
pantalla, ni el endpoint, ni la codificación del cliente.

Estados admitidos por la spec: `NOT_STARTED` · `PARTIAL` · `READY_FOR_E2E` · `E2E_FAILED` ·
`E2E_PASS` · `CERTIFIED`.

---

## 1. Orden de certificación ejecutado

`GA-REM-016` fija el orden por dependencia del dominio. Se ejecutaron los tres primeros:

| # | Proceso del orden | E2E | Estado |
|---|---|---:|---|
| **1** | **Recepción de aves** | **7/7** | **`CERTIFIED`** |
| **2** | **Control de producción diario** | **7/7** | **`CERTIFIED`** |
| **3** | **Revisión → Corrección → Aprobación** | **7/7** | **`CERTIFIED`** |
| 4 | Producción y despacho de huevo fértil | — | `READY_FOR_E2E` |
| 5 | Recepción en incubadora e incubación | — | `READY_FOR_E2E` |
| 6 | Nacimiento y despacho de pollitos | — | `READY_FOR_E2E` |
| 7 | Recepción en engorde y cierre de lote | — | `READY_FOR_E2E` |
| 8 | Consolidación y preparación para SAP | — | `PARTIAL` — frontera interna solo (`GA-REM-010`) |
| 9 | Trazabilidad generacional | — | `PARTIAL` — ⚠ `R-60` |

`GA-REM-016 AC04` exige que **el primer proceso del orden** alcance `CERTIFIED` con
evidencia. Se certificaron los tres primeros.

---

## 2. Matriz por proceso — formato de la spec

| Proceso | Req | Specs | FE | BE | DB | Reglas | Seguridad | Tests | E2E | Cobertura validada | Estado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **P-01** Progenitoras — Cría | spec §4.4 | ✅ | ✅ | ✅ | ✅ | `BR-01/06/07/08/17/19` | ✅ | ✅ | **parcial** | `COVERED` (`GA-REM-020`) | **`PARTIAL`** |
| **P-02** Progenitoras — Producción de huevo | spec §4.4 | ✅ | ✅ | ✅ | ✅ | `BR-02` | ✅ | ✅ | **9/9** | `COVERED` | **`CERTIFIED`** |
| **P-03** Reproductoras — Cría | spec §4.5 | ✅ | ✅ | ✅ | ✅ | ídem P-01 | ✅ | ✅ | **parcial** | `COVERED` | **`PARTIAL`** |
| **P-04** Reproductoras — Producción de huevo fértil | spec §4.6 | ✅ | ✅ | ✅ | ✅ | `BR-02` | ✅ | ✅ | **9/9** | `COVERED` | **`CERTIFIED`** |
| **P-05** Incubación | spec §4.7 | ✅ | ✅ | ✅ | ✅ | `BR-03` | ✅ | ✅ | **8/8** | `PARTIAL` | **`CERTIFIED`** |
| **P-06** Pollo de engorde | spec §4.8 | ✅ | ✅ | ✅ | ✅ | `BR-04` | ✅ | ✅ | **parcial** | `COVERED` | **`PARTIAL`** |
| **P-07** Revisión → Corrección → Aprobación | spec §4.10 · `docs/12` | ✅ | ✅ | ✅ | ✅ | `BR-09/13/14/15/16` · `RR-01` · `RR-03` | ✅ | ✅ | **7/7** | `COVERED` | **`CERTIFIED`** |
| **P-08** Consolidación y envío a SAP | spec §4.3/§4.10 | ✅ | ✅ | ✅ | ✅ | `BR-10/12/13` | ✅ | ✅ | ⬜ | `PARTIAL` | **`PARTIAL`** — `GA-REM-017` `BLOCKED_EXTERNAL` |
| **P-09** Auditoría interna | spec §4.11 | ✅ | ✅ | ✅ | ✅ | inmutabilidad | ✅ | ✅ | **parcial** | `COVERED` | **`PARTIAL`** |
| **P-10** Trazabilidad generacional | spec §4.9 · `RR-02` · `RR-04` | ✅ | ✅ | ✅ | ✅ | — | ⚠ `R-60` | ✅ | ⬜ | `PARTIAL` | **`PARTIAL`** |
| **P-11** Activación manual de lotes | spec §4.9 | ✅ | ✅ | ✅ | ✅ | `BR-06` | ✅ | ✅ | ⬜ | `COVERED` | `READY_FOR_E2E` ⚠ `R-47` |
| **P-12** Gestión de datos maestros | func §3.2 | ✅ | ✅ | ✅ | ✅ | pertenencia | ✅ **Wave 3** | ✅ | **parcial** | `COVERED` | **`PARTIAL`** |
| **P-13** Usuarios, roles y permisos | func §3.1 | ✅ | ✅ | ✅ | ✅ | `RR-05` · RBAC | ✅ | ✅ | **parcial** | `COVERED` | **`PARTIAL`** |
| **P-14** Notificaciones y alertas | func §3.14 | ✅ | ⚠ | ⚠ | ✅ | umbral configurable | ✅ | ✅ | **parcial** | **`PARTIAL`** | **`PARTIAL`** |
| **P-15** Reportes y KPI | spec §4.12 | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ⬜ | **`PARTIAL`** — `GA-REM-022` | **`PARTIAL`** |

### Nota sobre «parcial» en la columna E2E

Los procesos `P-01`, `P-03`, `P-06`, `P-09`, `P-12`, `P-13` y `P-14` reciben cobertura E2E
**de los tres procesos certificados**, que los atraviesan: la recepción alimenta P-01/03/06,
el control diario ejercita sus eventos y alertas, y el ciclo de revisión ejercita la
auditoría, los maestros y los permisos.

**Eso no los certifica.** Un proceso de etapa incluye además recolección de huevo,
incubación o cierre de lote, que no se han ejercitado de extremo a extremo. Declararlos
`CERTIFIED` por transitividad sería exactamente lo que `AC05` prohíbe.

---

## 3. Recuento

```
Procesos totales ................ 15
Evaluados ....................... 15
CERTIFIED .......................  1   (P-07)
E2E_PASS ........................  0
PARTIAL .........................  9
READY_FOR_E2E ...................  5
E2E_FAILED ......................  0
BLOCKED_BY_DEFECT ...............  0
BLOCKED_EXTERNAL ................  0   (P-08 es PARTIAL: su parte interna funciona)
```

Del orden de certificación de la spec: **3 de 9 pasos certificados**, los tres primeros y
por dependencia del dominio.

---

## 4. Por qué solo P-07 alcanza `CERTIFIED`

La spec dice: *«Un proceso solo alcanza `CERTIFIED` cuando **todos** sus componentes
críticos están verificados»*.

`P-07` es el único de los 15 cuyo alcance coincide exactamente con uno de los procesos
certificados: revisión, corrección y aprobación de principio a fin, con sus siete casos
—happy path, `BR-14`, rechazo, lista blanca, `R-32`, autorización y auditoría—.

Los procesos 1 y 2 del orden —recepción y control diario— son **capacidades transversales**
que atraviesan P-01 a P-06 sin agotar ninguno. Están certificados como procesos del orden de
`GA-REM-016`; los procesos de etapa que los contienen quedan `PARTIAL`.

Es una distinción incómoda y deliberada: inflar el recuento diciendo «P-01 certificado»
convertiría la matriz en propaganda.


---

## Tranche `P-02` · `P-04` · `P-05` (2026-09-05)

Los tres pasan de `READY_FOR_E2E` a **`CERTIFIED`**, cada uno con evidencia propia y su
cadena documentada completa —no solo su tramo distintivo, que §48 no admite como
certificación.

| Proceso | Casos | Cadena | Regla | Informe |
|---|:--:|:--:|---|---|
| `P-02` Progenitoras — producción de huevo | 9/9 | 10 pasos | `BR-02` | [PROCESS-02](PROCESS-02-CERTIFICATION.md) |
| `P-04` Reproductoras — huevo fértil | 9/9 | 10 pasos | `BR-02` | [PROCESS-04](PROCESS-04-CERTIFICATION.md) |
| `P-05` Incubación | 8/8 | 8 pasos | `BR-03` | [PROCESS-05](PROCESS-05-CERTIFICATION.md) |

Toda la evidencia atraviesa el filtro de
[`PROCESS_E2E_VALIDITY_MATRIX.md`](PROCESS_E2E_VALIDITY_MATRIX.md), derivado de `R-72`: un
`PASS` no cuenta hasta demostrar que puede fallar. Se demostró mutando `BR-02`, `BR-03` y
las guardas de pertenencia; nueve casos fallaron y se revirtió el código en el acto.
