# `P-10` · TRAZABILIDAD GENERACIONAL — INFORME DE CERTIFICACIÓN

2026-09-05 · `spec.md §4.9` · `GA-REM-016`

```
P-10 = PARTIAL — BLOCKED_BY_DEFECT (R-78)
```

**No se certifica.** El proceso tiene un defecto que impide su requisito central, descubierto
precisamente al ejercitar la cadena entera en vez de un endpoint suelto.

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
| 3 | `EggBatch` automático entre lotes distintos | **FAIL** | **`R-78`** |
| 4 | La recepción completa el `EggBatch` | **BLOCKED** | depende del 3 |
| 5 | `chick_dispatch` | **PASS** | E2E `P-10` |
| 6 | `bird_reception` | **PASS** | E2E `P-10` |
| 7 | `ChickBatch` con `egg_batch_id` | **BLOCKED** | depende del 3 |
| 8 | Navegación bidireccional | **BLOCKED** | sin vínculos que navegar |
| 9 | Ningún vínculo auto-referencial | **PASS** | E2E `P-10` |
| 10 | Sin destino declarado no se inventa | **PASS**, pero sin valor hoy (§5) | E2E `P-10` |
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

## 5. Una prueba que hoy pasa por el motivo equivocado

El paso 10 —«sin destino declarado no se inventa el vínculo»— pasa, pero mientras `R-78` siga
abierto **no demuestra nada**: no se crea ningún vínculo en ningún caso. Vuelve a ser
significativa en cuanto el positivo funcione. Se conserva y se anota, en lugar de contarla
como evidencia.

## 6. La cadena, marcada donde falla

`e2e/proceso-p10-trazabilidad-generacional.spec.ts` · 5 casos · `API_E2E`.

El caso de la cadena completa lleva `test.fail()`: dice lo que la spec exige y hoy no ocurre.
No se borra ni se suaviza. El día que `R-78` se corrija, pasará **inesperadamente** y obligará
a revisar esta certificación en lugar de dejarla envejecer en silencio.

## 7. Lo que sí queda certificado

```
R-60 = CERTIFIED
```

Pertenencia y coherencia en los vínculos manuales, con sensibilidad demostrada sobre las tres
reglas. Detalle en `R-60-CERTIFICATION.md`.

## 8. Qué falta para certificar `P-10`

1. `R-78` — que el vínculo se cree también desde la recepción. Necesita spec propia.
2. Reejecutar la cadena y retirar el `test.fail()`.
3. Cubrir los pasos 4, 7 y 8, hoy bloqueados.

## 9. Sobre la recomendación anterior

En el checkpoint previo señalé `P-10` como el proceso `PARTIAL` con menor distancia a la
certificación, porque sus defectos funcionales figuraban como corregidos y certificados.

**Era correcto según la evidencia disponible entonces, y ha resultado falso**: esa
certificación se apoyaba en una aserción que no podía fallar. La distancia real de `P-10` es
mayor de lo que cualquier matriz mostraba, y solo se supo al ejercitar la cadena completa.

Es, en sí mismo, el argumento de por qué se certifica el proceso y no la capacidad.
