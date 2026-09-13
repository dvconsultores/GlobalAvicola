# CERTIFICACIÓN — P-05 · Incubación

> **Vigencia — anotación `GA-GOV-03` (T1, 2026-09-13). Estado: `NOT_REPRODUCIBLE_EN_HEAD (pre-GA-GOV-03)`.**
> Este informe histórico no cita commit certificado ni artefacto de corrida (regla «no GREEN por declaración», §52) y varias suites de proceso (P-03/P-04/P-05/P-10/P-11/P-15) contenían TEST_DEFECT rojos hasta la T1 de GA-GOV-03. El contenido no se reescribe; la recertificación E2E de cada proceso corresponde a la T12 del programa pre-SAP (`audit/ga-pre-sap-program/GA_PRE_SAP_REMEDIATION_MASTER_ROADMAP.md`).

**`GA-REM-016`** · 2026-09-05 · **`CERTIFIED`**

---

## 1. Requisitos

`spec.md §4.7` · cadena documentada en `audit/06_PROCESS_COVERAGE.md` · regla de negocio
**`BR-03`**.

La unidad de certificación es el **proceso de negocio**, no la pantalla ni el endpoint
(Art. IV de la constitución). Que sus capacidades compartidas —recepción, control diario,
balances— estén certificadas **no** certifica este proceso: §48 lo prohíbe expresamente, y
por eso se ejecuta su cadena completa de **8 pasos** y no solo su tramo distintivo.

## 2. Casos ejecutados

`8 / 8` en verde, sobre lote de tipo `hatchery`.

| Tipo de caso | Resultado |
|---|---|
| `CADENA COMPLETA` — los 8 pasos documentados | **PASS** |
| `HAPPY PATH` | **PASS** |
| `NEGATIVE PATH` — `BR-03` | **PASS** |
| `VALIDATION` | **PASS** |
| `AUTHORIZATION` — sin sesión | **PASS** |
| `RBAC` — rol sin permiso de registro | **PASS** |
| `TENANT ISOLATION` — control y tratamiento | **PASS** |
| `FK OWNERSHIP` | **PASS** |
| `AUDIT` | **PASS** |
| `PERSISTENCE` / `DERIVED STATE` | **PASS** — saldo derivado 100 |

## 3. Fixtures

Cada caso crea sus precondiciones: granja, galpón, lote y catálogos propios, con sufijo
único por ejecución. **No se apoya en datos residuales** del entorno ni en identificadores
de la siembra. Nada permanente se inserta.

## 4. Aislamiento entre empresas

Se comprueba con **control y tratamiento**, y esa forma es deliberada:

```
CONTROL      el sujeto registra sobre SU lote          → 201
TRATAMIENTO  el mismo cuerpo sobre el lote ajeno       → denegado
```

El sujeto es un operador de la segunda empresa que **sí** tiene `operations:create`. Sin el
control, un rechazo por falta de permiso o por un campo mal formado se leería como
aislamiento y el test no probaría nada — la lección de `T-067-11`, y la de `R-72`.

## 5. Validez de la evidencia

Todos los casos atraviesan el filtro de
[`PROCESS_E2E_VALIDITY_MATRIX.md`](PROCESS_E2E_VALIDITY_MATRIX.md).

Sensibilidad demostrada por mutación controlada de la aplicación, revertida en el acto: al
anular `BR-03` y las guardas de pertenencia, los casos correspondientes **fallan**. Un
test que no puede fallar no es evidencia.

## 6. Verificación de base y estado derivado

El saldo se recalcula desde los eventos persistidos —no desde la respuesta del último
registro— y se compara con el esperado por la cadena entera. La auditoría del evento
comprueba empresa, autor, estado y submovimientos.

## 7. Veredicto

```
P-05 = CERTIFIED
```

Sin certificación por transitividad: ningún AC se da por cumplido porque otro proceso lo
cumpla.
