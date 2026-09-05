# CERTIFICACIÓN — `R-47` · FECHA DE INICIO DEL LOTE

**`GA-REM-028`** · 2026-09-05 · **`CERTIFIED`**

---

## 1. El hallazgo

`POST /lots` no persistía la fecha de inicio. El lote nacía siempre iniciado hoy.

## 2. Lo que significa esa fecha

`RC-09`, resuelto por evidencia de **nivel 3**, no por criterio técnico:

| Fuente | Qué dice |
|---|---|
| `docs/03-domain-model.md` | el agregado `Lot` declara **`start_date`**, **`created_at`** y **`age_days: int (calculado)`** como campos distintos |
| `docs/02 §3.5.1` | «**Fecha de inicio**» figura entre los campos del registro de lote |
| `docs/02 §3.9.1` | al incorporar un lote existente se captura la «**fecha real de inicio**» |

> **`RR-09`.** `start_date` es el inicio del ciclo productivo según el negocio, lo aporta
> quien registra el lote y de él deriva su edad. `created_at` es el alta en el software.
> Para un lote ya en marcha difieren legítimamente y ninguno sustituye al otro.

## 3. Causa raíz — no era la que decía el enunciado

`R-47` se registró como «acepta `start_date` y la ignora». La realidad es peor: **el
contrato de creación no declaraba el campo.**

```python
class LotCreate(LotBase):
    pass                       # ← sin start_date
```

Pydantic lo descartaba en la capa de esquema. El cliente lo enviaba —el formulario del
frontend tiene el campo y lo manda—, recibía `201`, y la fecha no llegaba a ninguna parte.
Mismo patrón que `P0-14`, donde catorce campos de evento se aceptaban y se perdían en
silencio.

## 4. El daño

| Consumidor | Con la fecha descartada |
|---|---|
| `age_days` | 0 para un lote de veinte semanas |
| `BR-06` | rechaza todo evento anterior a hoy → **imposible registrar un lote en marcha** |
| Índice productivo | `(peso × viabilidad) / (age_days × conversión)` sobre edad 0 |
| Ganancia diaria | `peso / age_days` sobre edad 0 |

## 5. La corrección

**Tres cambios, todos mínimos.**

`LotCreate` declara el campo, de modo que deja de descartarse en el esquema.

`create_lot` persiste lo recibido y, si se omite, mantiene el comportamiento de siempre.

Y una normalización de serialización que el propio arreglo destapó: la columna es
`DateTime(timezone=True)` y la base corre en `CET`, así que una fecha sin zona se guardaba a
medianoche local y **volvía como el día anterior** en UTC. Afectaba también al valor por
omisión: un lote creado hoy se leía como iniciado ayer. Se ancla el día declarado a
medianoche UTC para que petición, persistencia y respuesta hablen del mismo día. No se
cambia el tipo de la columna: eso sería una migración que `R-47` no necesita.

## 6. `R-73` — el cierre de lote nunca funcionó

Al comprobar `AC07` apareció que `POST /lots/{id}/close` responde **500 siempre**:

```
TypeError: unsupported operand type(s) for -: 'datetime.date' and 'datetime.datetime'
    lots/service.py:190 → age_days = (date.today() - lot.start_date).days
```

`start_date` nunca es nulo, de modo que la rama se ejecuta siempre. **Es la misma confusión
entre fecha de negocio y marca temporal que originó `R-47`**, y `AC07` no puede comprobarse
sin resolverla, así que se corrige aquí.

El cierre arrastra además un **segundo** defecto, ajeno a la fecha: el modelo de respuesta
de la ruta no encaja con el resumen que el servicio devuelve —faltan `created_at` y
`updated_at`—. Eso **no** se corrige aquí: es un desajuste de contrato, no de semántica
temporal. Queda como `R-73` con destino propio.

Por eso `AC07` se verifica llamando al servicio y no por HTTP: es el mismo código, y no se
disfraza el hecho de que el endpoint sigue roto.

## 7. Criterios de aceptación

| AC | Criterio | Prueba | Resultado |
|---|---|---|---|
| **AC01** | La fecha declarada se persiste | `T-047-01` | **PASS** |
| **AC02** | La respuesta la expone | `T-047-01` | **PASS** |
| **AC03** | Lectura inmediata, sin esperas | `T-047-01` | **PASS** |
| **AC04** | Distinguible de `created_at` | `T-047-01` | **PASS** — difieren |
| **AC05** | La activación manual no la pisa con hoy | `T-047-05` | **PASS** |
| **AC06** | El saldo de apertura de `R-67` sigue correcto | `T-047-05` | **PASS** — 5 000 |
| **AC07** | La edad deriva del inicio declarado | `T-047-03` | **PASS** — 140 días |
| **AC08** | Omitirla mantiene el flujo normal | `T-047-02` | **PASS** |
| **AC09** | `BR-06` usa el ancla correcta | `T-047-04` | **PASS** — acepta lo posterior, rechaza lo anterior |
| **AC10** | El aislamiento no se debilita | `T-047-06` | **PASS** — control y tratamiento |
| **AC11** | `created_at` sigue siendo veraz | `T-047-01`, `T-047-05` | **PASS** |
| **AC12** | Regresión en verde | suite | **PASS** |
| **AC13** | Sensibilidad demostrada | mutación | **PASS** |

`6 / 6` pruebas, **sin omisiones**. La que dependía de una fase productiva la crea ella
misma en lugar de saltarse: una omisión no es evidencia.

## 8. Sensibilidad

Se restauró el comportamiento defectuoso —volver a ignorar lo recibido— y **tres pruebas
fallaron**: la de persistencia, la de la edad y la del ancla de `BR-06`. Código revertido en
el acto; `git diff` sin la mutación.

## 9. Sin falsificar historia

No se genera ningún evento histórico para cuadrar cálculos. Solo se guarda la fecha que el
usuario declara. Las tres marcas siguen separadas:

```
inicio del ciclo (negocio)   start_date  = declarado
alta en el software          created_at  = hoy, lo fija el servidor
activación manual            evento de auditoría, hoy
```

## 10. Interfaz

`LotFormPage.tsx` ya tiene el campo y lo envía, y `lots.service.ts` lo declara obligatorio
al crear. **La cadena entera lo esperaba**; solo el backend lo descartaba. No hay hueco de
interfaz que registrar.

## 11. Regresión

```
Backend ............ 313 pasados · 49 omitidos · 0 fallos   (307 antes + 6 nuevas)
Deriva de esquema .. 0   ·  Alembic: 1 head, 1 base
TypeScript ......... PASS  ·  Vitest 61/61  ·  i18n 866 = 866
```

Sin migración: la columna ya existía con el tipo correcto.

## 12. Veredicto

```
R-47 = CERTIFIED
```

Y no por «el campo se guarda»: se demostró que la edad deriva de él, que `BR-06` cambia de
ancla —que es lo que desbloquea el registro retroactivo—, y que el saldo de apertura y el
aislamiento siguen intactos.

**Hallazgo abierto**: `R-73`, el cierre de lote. Su causa temporal queda resuelta; el
desajuste del modelo de respuesta, no.
