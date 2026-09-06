# `P-12` · CONTRATO DE PAGINACIÓN

Fase de análisis · 2026-09-06

---

## 1. Qué promete la etiqueta

`FilterPanel.tsx:47`

```tsx
{totalResults} {t('common.results', 'resultados')}
```

La clave existe en los dos idiomas: **«resultados» / «results»**. No dice «mostrando N», dice
cuántos resultados hay. Con filtro aplicado, lo normativo es el **total que casa con el
filtro** (`§34` del encargo).

## 2. Los dos lados

| Maestro | El backend pagina | El backend calcula el total | El backend **devuelve** el total | El frontend lo usa | ¿Correcto? |
|---|:--:|:--:|:--:|:--:|:--:|
| los 19, todos por el mismo CRUD genérico | `skip` · `limit` | **sí** | **no** | no puede | **no** |

```python
# masters/router.py:38
items, total = await service.get_all(skip=skip, limit=limit, search=search, ...)
return [read_schema.model_validate(item) for item in items]      # ← el total se descarta
```

## 3. Dónde está de verdad la causa

**No es un fallo del frontend.** `setTotal(response.data.length)` es lo único que puede hacer
con una lista pelada: el total no viaja en la respuesta.

El servicio lo calcula, el router lo tira.

## 4. El contrato de la casa dice lo contrario

Otros **cinco** listados paginados de la aplicación sí lo devuelven:

```
/audit         → {"logs": …,        "total": n}
/corrections   → {"corrections": …, "total": n}
/review/…      → {"events": …,      "total": n}   ×2
/review/batches→ {"batches": …,     "total": n}
```

Maestros es el **único** que no. No hay que inventar un contrato: hay que seguir el que ya
existe.

## 5. Hallazgo

```
R-89 · P2 · el listado de maestros descarta el total que su propio servicio calcula, de modo
            que la interfaz muestra el tamaño de la página donde promete «resultados». En un
            catálogo con más de una página el número es falso, y además la paginación se
            muestra u oculta a partir de ese número equivocado
            (`MasterListPage:147`, `total >= pageSize`).
```

**Severidad P2 y no P1**: induce a error pero no impide operar ni compromete datos. Se
clasifica por impacto, no por vistosidad.

## 6. Lo que hace falta para demostrarlo

Un conjunto con **más registros que el tamaño de página** (20). Con menos, el tamaño de la
página y el total coinciden y la prueba no podría fallar — sería exactamente la clase de
evidencia vacua que `AC13` prohíbe.
