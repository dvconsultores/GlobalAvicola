# CERTIFICACIÓN · `R-76` — APROBACIÓN ANTES DEL CIERRE

**`GA-REM-036`** · `docs/12 §6 R7` · 2026-09-06

```
R-76 = CERTIFIED
```

---

## 1. La regla, acotada antes de programar

> **R7** — Un lote no puede cerrarse si tiene registros sin aprobar.

Dos palabras había que definir, y ninguna se resolvió por atajo.

**«Registro»** = `OperationalEvent` del lote. `docs/12 §4` se titula «Estados del registro
operativo» y el documento entero trata de esa entidad. **No** se generalizó a «nada pendiente
en ningún sitio»: correcciones y acciones de aprobación son artefactos del propio flujo, y los
lotes de trazabilidad, las fases o el saldo de apertura no tienen estado que aprobar.

**«Sin aprobar»** = los siete estados anteriores a la aprobación, más el rechazo. `docs/12 §4`
enumera trece y la aprobación es el séptimo, de modo que todo lo posterior la presupone.

| Bloquean (7) | No bloquean (6) |
|---|---|
| `draft` · `registered` · `pending_review` · `in_review` · `returned` · `corrected` · `rejected` | `approved` · `consolidated` · `sent_to_sap` · `sap_confirmed` · `sap_error` · `cancelled` |

## 2. Los dos casos que hubo que razonar

**`rejected` bloquea.** No está aprobado. Y no atrapa el lote: `docs/12 §4` muestra que no es
terminal —«Operador → Reenvía corregido», y el diagrama confirma `Rechazado → Registrado`—.

**`sap_error` no bloquea.** Solo se alcanza desde `sent_to_sap`, que solo se alcanza desde
`consolidated`, que solo se alcanza desde `approved`. **Un registro en error de SAP ya fue
aprobado**, y `R7` está en la sección «Reglas de aprobación», no en la de integración.

> Aquí me aparté del conjunto que el código usa en otros sitios —el de los indicadores de
> `P-15` omite `sap_error`— y a propósito: aquél cuenta eventos **para mostrar**; éste decide
> si algo **está aprobado**. Son preguntas distintas y merecen conjuntos distintos.

**`cancelled` no bloquea.** Un registro anulado no representa operación alguna, y es lo que
excluyen los ocho saldos de `operations/validators.py` sin excepción.

## 3. `BR-05` y `R7` no se fusionaron

Comparten el momento de ejecución y nada más:

| | `BR-05` | `R7` |
|---|---|---|
| Fuente | `spec.md:266` · `docs/02:545` | `docs/12 §6` |
| Pregunta | ¿hay base para el resumen final? | ¿está todo aprobado? |

La regla se cita como **`R7`**, que es como la norma la llama. No se amplió `BR-05` ni se
inventó un `BR-` nuevo, y `AC09` comprueba que `BR-05` sigue vigente por su cuenta.

## 4. Evidencia

### El control, primero

`AC01`: el mismo lote, con todo aprobado, **cierra con 200**. Sin ese control, cualquier
rechazo posterior no probaría nada.

### Fase roja

Con el código anterior, el lote cerraba (`200`) teniendo un registro en cada uno de los siete
estados bloqueantes. **Ocho pruebas en rojo, aisladas a `R7`**: el lote estaba activo, `BR-05`
satisfecho —pesaje y alimento aprobados— y el evento que se movía era una inspección, elegida
precisamente porque anular el pesaje habría roto `BR-05` y el rechazo habría llegado por la
causa equivocada.

### Fase verde

| `AC` | Prueba | Resultado |
|---|---|---|
| `AC01` control | `test_t_076_01` | PASS |
| `AC02` `AC03` `AC05` `AC06` | `test_t_076_02` ×7 estados | PASS |
| `AC04` | `test_t_076_03` ×6 estados | PASS |
| `AC08` aprobar desbloquea | `test_t_076_04` | PASS |
| `AC07` pertenencia | `test_t_076_05` | PASS |
| `AC09` `BR-05` vigente | `test_t_076_06` | PASS |

`AC04` merece subrayarse: **una regla que bloquea de más es tan defectuosa como una que no
bloquea**. Los seis estados no gobernados se comprueban uno a uno.

### Puerta de sensibilidad

| Mutación | Efecto | Restaurado |
|---|---|:--:|
| se retira la guarda | **8 de `R-76` fallan**; el cierre certificado sigue verde | 17/17 |
| `sap_error` pasa a contar como no aprobado | **1 falla** — el caso parametrizado de ese estado | 17/17 |

La segunda demuestra que la decisión de alcance está bajo prueba y no es una opinión escrita
en un comentario.

`git diff` tras revertir: solo lo previsto.

## 5. Fixtures reparadas, aserciones intactas

La guarda cambió una **precondición** del cierre, así que varias pruebas ya certificadas
dejaron de poder cerrar sus lotes: `test_lot_closure.py` (`GA-REM-029`) y
`test_lot_start_date.py` (`GA-REM-028`).

Se repararon **las fixtures**, no las afirmaciones: aprueban sus eventos antes de cerrar. Lo
que esas pruebas miden —el resumen, `BR-05`, la fecha, la edad— no cambió.

Un caso mereció más cuidado. `test_t_073_01` distinguía `approved_events` de `total_events`
dejando un evento **sin aprobar**, y eso ahora impide cerrar. La distinción se consigue ahora
con un evento **anulado**, que `R7` no gobierna: la intención de la prueba —que los dos
contadores son consultas distintas— se conserva intacta.

### Regresiones del cierre certificado

| | |
|---|---|
| `BR-05` | **PASS** |
| `R-73` resumen · `R-74` puerta real · `R-75` fecha | **PASS** — 8/8 |
| `R-68` lectura inmediata | **PASS** — `AC08` cierra sin esperas tras aprobar |

## 6. Veredicto

```
R-76 = CERTIFIED   ·   11 de 11 criterios de GA-REM-036
```
