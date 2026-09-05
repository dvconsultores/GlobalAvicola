# `P-10` · TRAZABILIDAD GENERACIONAL — INFORME DE CERTIFICACIÓN

2026-09-05 · `spec.md §4.9` · `GA-REM-016`

```
P-10 = CERTIFIED     (2026-09-05, tras GA-REM-031)
```

> **Historia de este informe.** Su primera versión declaró `PARTIAL — BLOCKED_BY_DEFECT`
> porque al ejercitar la cadena entera apareció `R-78`. Se conserva la estructura y se
> actualiza el veredicto; el diagnóstico de entonces no se borra, porque es la razón de que
> este proceso se certifique de verdad y no por capacidad.

---

## 1. Alcance

Nombre normativo: **Generational Traceability (Trazabilidad Generacional)**, `spec.md §4.9`.

```
Reproductoras (producción)
  │ egg_dispatch                      ┐
  ↓                                   ├→ EggBatch
Incubadora   · egg_reception_hatchery ┘
  │ chick_dispatch                    ┐
  ↓                                   ├→ ChickBatch ──egg_batch_id──> EggBatch
Engorde      · bird_reception         ┘
```

12 pasos, detallados en `P10_PROCESS_CHAIN_MATRIX.md §3`.

## 2. Los criterios, uno a uno

| # | Paso | Estado | Evidencia |
|:--:|---|:--:|---|
| 1 | `egg_dispatch` | **PASS** | E2E `P-10` |
| 2 | `egg_reception_hatchery` | **PASS** | E2E `P-10` |
| 3 | `EggBatch` automático entre lotes distintos | **PASS** | `GA-REM-031 AC01` · E2E |
| 4 | La recepción completa el `EggBatch` | **PASS** | `GA-REM-031 AC04` |
| 5 | `chick_dispatch` | **PASS** | E2E `P-10` |
| 6 | `bird_reception` | **PASS** | E2E `P-10` |
| 7 | `ChickBatch` con `egg_batch_id` | **PASS** | `GA-REM-031 AC05` |
| 8 | Navegación bidireccional | **PASS** | E2E `P-10` |
| 9 | Ningún vínculo auto-referencial | **PASS** | E2E `P-10` |
| 10 | Sin destino declarado no se inventa | **PASS** | E2E `P-10` |
| 11 | Enlace manual + pertenencia | **PASS** | E2E + `R-60-CERTIFICATION.md` |
| 12 | Aislamiento por compañía | **PASS** | `GA-REM-008 AC06` + `R-60` |

```
PASS 7 · FAIL 1 · BLOCKED 3 · N/A 0
```

## 3. `R-78` · el vínculo automático no se crea en el orden natural

### Qué dice la spec

> Un `EggBatch` se crea **automáticamente** al registrar `egg_dispatch` +
> `egg_reception_hatchery`. — `spec.md §4.9`

### Qué hace la aplicación

El vínculo se crea **solo** en la rama del despacho, que busca una recepción **ya existente**
(`_recepcion_en_el_destino_declarado`). Las dos ramas de recepción se limitan a *actualizar*
un vínculo previo:

```python
elif event.event_type == models.EventType.EGG_RECEPTION_HATCHERY:
    dispatch = await self._despacho_dirigido_a_este_lote(...)
    if dispatch:
        batch = ...select(EggBatch).where(EggBatch.dispatch_event_id == dispatch.id)...
        if batch:                       # ← si no existe, no se crea: se ignora
            batch.quantity_received = ...
```

Idéntico en `BIRD_RECEPTION` (`operations/service.py:259-272`, `:296-307`).

En la operación real **se despacha antes de recibir**. En ese orden:

```
despacho  → busca recepción → no existe todavía → no crea vínculo
recepción → encuentra el despacho → busca el vínculo → no existe → no hace nada
RESULTADO: ningún vínculo, nunca
```

Medido en la pila real: la cadena completa de tres generaciones produce **0 vínculos**.

```
R-78 · P1 · abierto
```

### Por qué no se corrige aquí

`GA-REM-016 AC11`: un test que descubre un desajuste entre spec y aplicación **genera un
hallazgo, no una corrección dentro del mismo cambio**. Es además otra causa que `R-60`, con
otra spec de destino. Corregirlo dentro de `GA-REM-030` sería justo lo que el proceso prohíbe.

## 4. `R-79` · la evidencia que sostenía `GA-REM-008 AC01` no puede fallar

`backend/tests/test_traceability.py:67`:

```python
assert str(destino) in crudo or "egg_batch" in crudo.lower()
```

La respuesta de trazabilidad **siempre** contiene la clave `egg_batches_sent`, de modo que el
segundo término es cierto pase lo que pase. La aserción no puede fallar.

Esa prueba es la que certificaba `AC01` de `GA-REM-008` —«cadena de huevo creada entre lotes
distintos»—, y por eso `R-78` sobrevivió a una certificación: la prueba pasaba sin comprobar
que existiera vínculo alguno.

```
R-79 · P2 · abierto
GA-REM-008 · AC01 = NOT_EVIDENCED  (el informe histórico se conserva sin modificar)
```

Es la clase exacta de defecto que `R-72` describió y que la Puerta de Validez existe para
atrapar. Aquí la atrapó.

## 5. El negativo vuelve a significar algo

El paso 10 —«sin destino declarado no se inventa el vínculo»— pasaba mientras `R-78` estaba
abierto **por el motivo equivocado**: no se creaba ningún vínculo en ningún caso. Con el
positivo funcionando, la abstención que comprueba vuelve a ser una propiedad y no una
casualidad.

## 6. La cadena, marcada donde falla

`e2e/proceso-p10-trazabilidad-generacional.spec.ts` · 5 casos · `API_E2E`.

El caso de la cadena completa llevó `test.fail()` mientras `R-78` estuvo abierto, para que la
spec siguiera dicha en una aserción y no solo en prosa. Al corregirse pasó **inesperadamente**
—que es justo lo que se buscaba— y la marca se retiró.

## 7. Los tres hallazgos que costó certificar este proceso

| | |
|---|---|
| `R-60` | pertenencia y coherencia en los vínculos manuales · `GA-REM-030` · `R-60-CERTIFICATION.md` |
| `R-78` | el vínculo no se creaba desde la recepción · `GA-REM-031` |
| `R-79` | la evidencia de `GA-REM-008 AC01` no podía fallar · `GA-REM-016` enmienda F |

Los tres con sensibilidad demostrada por mutación controlada y revertida.

## 8. Modalidad de la evidencia

`API_E2E` de proceso, conforme a `GA-REM-016 AC05`: la unidad certificada es el proceso de
negocio, nunca una pantalla, un endpoint o un componente. `spec.md §4.9` no exige interfaz
para ninguna de sus reglas, así que **no se fabricaron pruebas de interfaz** para conservar
vocabulario.

## 9. Sobre la recomendación anterior

En el checkpoint previo señalé `P-10` como el proceso `PARTIAL` con menor distancia a la
certificación, porque sus defectos funcionales figuraban como corregidos y certificados.

**Era correcto según la evidencia disponible entonces, y ha resultado falso**: esa
certificación se apoyaba en una aserción que no podía fallar. La distancia real de `P-10` es
mayor de lo que cualquier matriz mostraba, y solo se supo al ejercitar la cadena completa.

Es, en sí mismo, el argumento de por qué se certifica el proceso y no la capacidad.
