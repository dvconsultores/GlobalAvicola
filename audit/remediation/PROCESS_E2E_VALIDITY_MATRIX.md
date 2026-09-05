# MATRIZ DE VALIDEZ DE LOS E2E DE PROCESO

**`GA-REM-016`** · 2026-09-05 · derivada de `R-72`

`R-72` demostró que un `PASS` no es evidencia: doce tests heredados pasaban sin poder
fallar. Desde entonces, ningún E2E cuenta como evidencia de certificación por el solo hecho
de estar en verde. Debe atravesar este filtro.

---

## 1. El filtro

| # | Criterio |
|--:|---|
| 1 | Se autentica si el flujo lo exige |
| 2 | Está autorizado si el flujo lo exige |
| 3 | Alcanza la pantalla o el endpoint previstos |
| 4 | Alcanza el **estado de negocio** previsto |
| 5 | La afirmación comprueba un requisito observable |
| 6 | La afirmación **puede fallar** |
| 7 | No pasa apoyado en login, error o estado vacío |
| 8 | El fixture crea de verdad las precondiciones |
| 9 | El contexto de empresa es el correcto |
| 10 | El resultado corresponde a un AC |

## 2. `P-02` · Progenitoras — producción de huevo

| Test | Requisito | ¿Alcanza el flujo? | ¿No vacía? | ¿Sensibilidad probada? | ¿Evidencia válida? |
|---|---|:--:|:--:|:--:|:--:|
| CADENA COMPLETA · diez pasos | `§4.4` cadena documentada | sí — 11 registros con `201` | sí — lista de fallidos vacía | derivada: el saldo final 340 depende de la cadena | **sí** |
| HAPPY PATH · recolección → clasificación → despacho | `§4.4` · `BR-02` | sí | sí — saldo 0 → 1000 → 300 | aritmética sobre datos reales | **sí** |
| NEGATIVE PATH · `BR-02` | `BR-02` | sí | sí — exige `rule` y el saldo en el mensaje | **sí** — mutada la regla, el test falla | **sí** |
| VALIDATION · despacho de cero | `BR-02` | sí | sí — el saldo no se mueve | — | **sí** |
| AUTHORIZATION · sin sesión | `GA-REM-002` | sí — `401` | sí | — | **sí** |
| RBAC · rol sin permiso | `GA-REM-002` | sí — control `201`, tratamiento `403` | sí | control y tratamiento | **sí** |
| AISLAMIENTO · empresa ajena | `R-42` · `R-59` | sí — control `201`, tratamiento denegado | sí | **sí** — anuladas las guardas, el test falla | **sí** |
| FK OWNERSHIP · granja y galpón | `R-42` | sí — control `201`, dos tratamientos | sí | **sí** | **sí** |
| AUDIT · autor y empresa | `docs/13` | sí | sí — comprueba empresa, autor, estado y submovimientos | — | **sí** |

**9 / 9 válidos.**

## 3. `P-04` · Reproductoras — producción de huevo fértil

Mismo conjunto de casos, ejecutado con evidencia propia sobre lotes `breeder`.
**9 / 9 válidos**, con la misma prueba de sensibilidad: mutadas `BR-02` y las guardas de
pertenencia, los tres casos correspondientes fallan.

## 4. `P-05` · Incubación

| Test | Requisito | ¿Alcanza el flujo? | ¿No vacía? | ¿Sensibilidad probada? | ¿Evidencia válida? |
|---|---|:--:|:--:|:--:|:--:|
| CADENA COMPLETA · ocho pasos | `§4.7` | sí — 8 registros con `201` | sí | derivada del saldo 100 | **sí** |
| HAPPY PATH · recepción → carga → ovoscopia | `§4.7` · `BR-03` | sí | sí — 0 → 1000 → 200 | aritmética real | **sí** |
| NEGATIVE PATH · `BR-03` | `BR-03` | sí | sí — exige `rule` y lo disponible | **sí** | **sí** |
| VALIDATION · carga sin recepción previa | `BR-03` | sí | sí | **sí** | **sí** |
| AUTHORIZATION · sin sesión | `GA-REM-002` | sí | sí | — | **sí** |
| RBAC · rol sin permiso | `GA-REM-002` | sí — control y tratamiento | sí | control y tratamiento | **sí** |
| AISLAMIENTO · empresa ajena | `R-42` · `R-59` | sí — control y tratamiento | sí | **sí** | **sí** |
| AUDIT · parámetros de incubación | `docs/13` | sí | sí — comprueba `quantity_loaded` y temperatura | — | **sí** |

**8 / 8 válidos.**

## 5. Pruebas de sensibilidad ejecutadas

Mutación controlada de la aplicación, revertida en el acto y con `git diff` limpio:

| Mutación | Efecto esperado | Resultado |
|---|---|---|
| `validate_egg_dispatch`: se anula la comparación con el saldo | fallan los `NEGATIVE PATH` de `BR-02` | **fallaron** (`P-02`, `P-04`) |
| `validate_incubation_load`: ídem | fallan `NEGATIVE PATH` y `VALIDATION` de `BR-03` | **fallaron** (`P-05`) |
| `validate_lot_active`: se anula el filtro por compañía (`R-42`) | fallan los de aislamiento | **fallaron** (los tres) |
| `verificar_pertenencia`: se convierte en no-operación | falla `FK OWNERSHIP` | **falló** |

```
9 tests fallaron con las mutaciones · 14 siguieron pasando (no dependen de esas reglas)
```

## 6. Dos correcciones que este filtro forzó

**La primera afirmación de aislamiento que escribí no valía.** Decía `not.toBe(201)`, que
pasa con **cualquier** rechazo —un campo obligatorio, una regla ajena— y no demuestra
pertenencia. Es el mismo vicio de `R-72`, en un test nuevo. Se reescribió con **control y
tratamiento**: el mismo cuerpo se acepta en la empresa propia y se rechaza en la ajena.

**Y `R-66` mordió al montar los fixtures.** `crearEscenario` leía la empresa de `/me`, que
devuelve la persistida y no la activa de la sesión; con un administrador que había cambiado
de compañía, el escenario se creaba en la empresa equivocada y producía un
`Farm no encontrado` desconcertante. Ahora la empresa activa se lee del token, que es lo que
el backend usa. El hallazgo estaba registrado como P3 documental; en la práctica cuesta
tiempo de diagnóstico.
