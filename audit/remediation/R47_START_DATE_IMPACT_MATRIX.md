# MATRIZ DE IMPACTO — `start_date` DEL LOTE

**`R-47` · `GA-REM-028`** · 2026-09-05 · inventario previo a tocar código

---

## 1. La pregunta

No era «¿se guarda el campo?» sino «¿qué significa esa fecha y quién depende de ella?».
Corregir la asignación sin responder lo segundo habría dejado `P-11` igual de roto.

## 2. La matriz

| Capa | ¿Lee? | ¿Escribe? | Efecto esperado | Estado anterior |
|---|:--:|:--:|---|---|
| Columna `lots.start_date` (`masters/models.py:209`) | — | — | `DateTime(timezone=True)`, nullable | **correcta** — sin migración |
| Columna `lots.created_at` (`masters/models.py`) | — | servidor | instante real del alta | correcta |
| `LotCreate` (`lots/schemas.py:46`) | — | — | acepta `start_date` opcional | **aceptaba y se descartaba** |
| `LotRead` (`lots/schemas.py:54,56`) | sí | — | expone `start_date` **y** `created_at` | correcta |
| `POST /lots` → `create_lot` (`lots/service.py:86`) | **no** | **sí** | persistir lo recibido | **`start_date=date.today()`** ← `R-47` |
| `PUT /lots/{id}` | — | — | la spec no exige modificarla | sin cambio |
| `activate_manual` (`lots/service.py:275`) | — | sí | fija la «fecha real de inicio» declarada | correcto (`docs/02 §3.9`) |
| `get_lot` → `age_days` (`lots/service.py:162`) | **sí** | — | `(hoy − start_date).days` | correcto, pero alimentado con hoy |
| `BR-06` (`operations/validators.py:279`) | **sí** | — | ninguna operación anterior al inicio | correcto, pero anclado a hoy |
| Informe de lote (`reports/service.py:190`) | sí | — | lo expone | correcto |
| Índice productivo (`reports/service.py:434`) | **sí** | — | `(peso × viabilidad) / (age_days × conversión)` | **valor falso** con edad 0 |
| Ganancia diaria (`reports/service.py:479`) | **sí** | — | `peso / age_days` | **valor falso** |
| `LotPhase.start_date` (`lots/models.py:21`) | — | — | fecha de la **fase**, no del lote | campo distinto, no confundir |
| Formulario de alta del frontend | ver §5 | — | permitir declararla | **hueco anotado** |

## 3. El daño real

Un lote incorporado con veinte semanas de vida quedaba con:

```
start_date  = hoy            ← falso
age_days    = 0              ← falso
BR-06       = rechaza todo evento anterior a hoy
índice productivo, ganancia diaria = calculados sobre edad 0
```

Tres consumidores devolvían cifras equivocadas y una regla bloqueaba el registro
retroactivo. Guardar el campo no era cosmética.

## 4. `created_at` no es sustituto

Para un lote ya en marcha, las dos fechas **difieren legítimamente**:

```
inicio del ciclo (negocio)   start_date  = hace 140 días
alta en el software          created_at  = hoy
activación manual            evento de auditoría, hoy
```

El modelo de dominio (`docs/03`) las declara como campos distintos, y el contrato de
lectura ya las expone por separado. Confundirlas es lo que producía `R-47`.

## 5. Hueco anotado: el formulario del frontend

Si la interfaz de alta de lotes no permite declarar la fecha, `P-11` seguirá sin poder
ejecutarse **desde la aplicación** aunque la API lo admita. Se verifica y, si falta, se
registra como hallazgo con destino propio — no se corrige en silencio dentro de esta spec.

## 6. Lo que deliberadamente no se decide

| Cuestión | Por qué se deja abierta |
|---|---|
| ¿Se admite una fecha futura? | ninguna fuente normativa se pronuncia. `§21` prohíbe decidirlo por cuenta propia |
| ¿Hay antigüedad máxima? | ídem, y `P-11` exige explícitamente fechas antiguas. `BR-19` acota **eventos**, no el inicio del lote |

Se anotan como huecos de requisito, no se rellenan con criterio técnico.
