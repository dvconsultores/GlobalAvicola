# GA-REM-028 — FECHA DE INICIO DEL LOTE

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-028` · **Tipo** `DOMAIN SEMANTICS + BUGFIX SPEC` |
| **Prioridad** | **P1** · bloquea `P-11` |
| **Estado** | `SPEC_READY` |
| **Origen** | `R-47`, detectado al certificar `GA-REM-008` |
| **Trazabilidad** | `GA-REM-019 AC03`: los `STILL_VALID` reciben spec propia. `GA-REM-019` **no define** `R-47` —cero menciones— y es una spec de reevaluación, no de dominio |
| **Detectado** | 2026-09-04 · **especificado** 2026-09-05 |

## Problema

`POST /lots` acepta `start_date` en su contrato y lo **descarta**:

```python
lot = Lot(..., start_date=date.today())     # lots/service.py:86
```

El valor que envía el cliente nunca llega a la base. El lote queda siempre iniciado hoy.

### Por qué no es un descuido menor

`start_date` no es un dato de adorno. De él dependen:

| Consumidor | Efecto |
|---|---|
| `age_days` (`lots/service.py:162`) | `(hoy − start_date).days` — la edad del lote |
| `BR-06` (`operations/validators.py:279`) | ninguna operación puede fecharse antes del inicio |
| Informe de lote (`reports/service.py:190`) | lo expone |
| Índice productivo (`reports/service.py:434`) | `(peso × viabilidad) / (age_days × conversión)` |
| Ganancia diaria (`reports/service.py:479`) | `peso / age_days` |

Un lote incorporado con veinte semanas de vida se presenta con **edad cero**, y sus dos
indicadores salen mal. Y `BR-06` rechaza cualquier evento anterior a hoy, que es
exactamente lo que impide registrar la operación retroactiva de un lote ya en marcha.

Por eso bloquea `P-11`: un proceso cuyo propósito declarado es incorporar **lotes ya en
proceso** (`docs/02 §3.9`) no puede funcionar si el sistema insiste en que todos empezaron
hoy.

## Qué significa `start_date` — resuelto por evidencia

`RC-09`. Se aplicó la jerarquía de `REQUIREMENT_CONFLICT_RESOLUTION.md §1`.

| Alternativa | Sostenida por | Nivel |
|---|---|:--:|
| **A** · Es la **fecha de negocio** del inicio del ciclo, que aporta el usuario | `docs/03-domain-model.md` declara en el agregado `Lot` los campos **`start_date`**, **`created_at`** y **`age_days: int (calculado)`** como cosas distintas · `docs/02 §3.5.1` lista «**Fecha de inicio**» entre los campos del registro de lote · `docs/02 §3.9.1` pide «**Fecha real de inicio**» al incorporar un lote existente | **3** |
| **B** · Es el instante de alta en el software | `lots/service.py:86` | 5 |

**A · `RESOLVED_BY_EVIDENCE`.** El nivel 5 no puede contradecir al nivel 3, y el modelo de
dominio ya separa explícitamente las dos fechas.

> **`RR-09`.** `start_date` es el **inicio del ciclo productivo del lote** según el negocio,
> lo aporta quien registra el lote, y es la fuente de la que deriva su edad. El instante en
> que el registro entra en Global Avícola es `created_at`, y son campos distintos: para un
> lote ya en marcha difieren legítimamente. Ninguno sustituye al otro.

## Alcance

1. Que `POST /lots` persista la fecha recibida.
2. Que la respuesta y la lectura inmediata la devuelvan.
3. Que `created_at` siga siendo veraz.
4. Que la activación manual y el saldo de apertura (`R-67`) sigan comportándose igual.

## Fuera de alcance

Añadir validación de fecha futura o de antigüedad máxima: **ninguna fuente normativa las
exige** y `§21`/`§22` del encargo prohíben decidirlo por cuenta propia. Se anota como hueco.
· Cambiar `BR-06` o `BR-19` · Reestructurar el agregado `Lot` · Añadir fechas nuevas ·
Migración: la columna ya existe con el tipo correcto.

## Acceptance Criteria

| AC | Criterio | Verificación |
|---|---|---|
| **AC01** | La `start_date` enviada al crear el lote se persiste | consulta a la base |
| **AC02** | La respuesta de creación expone esa fecha | cuerpo de la respuesta |
| **AC03** | Una lectura inmediata devuelve el mismo valor, sin esperas | `GET` acto seguido (`R-68`) |
| **AC04** | Una fecha histórica es distinguible de `created_at` | ambos campos, valores distintos |
| **AC05** | La activación manual no reemplaza la fecha por la de hoy | `activate-manual` conserva su semántica |
| **AC06** | El saldo de apertura de `R-67` sigue correcto | regresión |
| **AC07** | La edad del lote deriva de `start_date`, no del alta | `age_days` de un lote histórico > 0 |
| **AC08** | Omitir `start_date` mantiene el comportamiento actual: se toma hoy | creación sin el campo |
| **AC09** | `BR-06` acepta eventos posteriores a la fecha declarada y rechaza los anteriores | ambos sentidos |
| **AC10** | El aislamiento entre empresas no se debilita | control y tratamiento |
| **AC11** | `created_at` sigue siendo el momento real del alta | comparación |
| **AC12** | La regresión completa sigue en verde | suite |
| **AC13** | Se demuestra que las pruebas pueden fallar | mutación controlada |

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Que el flujo normal cambie | `AC08`: sin el campo, el comportamiento es el de siempre |
| Que la activación manual entre en conflicto | `AC05`: su semántica es normativa (`docs/02 §3.9`) y no se toca |
| Que se falsifique historia | no se genera ningún evento: solo se guarda la fecha declarada |
| Que `created_at` deje de ser veraz | `AC11`: lo fija el servidor y no se toca |

## Definition of Done

- `AC01`…`AC13` con evidencia · informe de certificación · `P-11` reevaluado.
