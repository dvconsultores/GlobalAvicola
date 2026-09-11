# GA-GOV-02 · ANÁLISIS — OBSERVACIÓN DE NEGOCIO (ESCALA DEL IPE)

## 1 · Redacción exacta y evidencia

Ver `GA_GOV_02_BUSINESS_OBSERVATION_SOURCE_RECONSTRUCTION.md` (§1). Evidencia: cálculo independiente documentado (constantes del fixture: 2000 g · 19 d · 95 % · FCR 3.0 → fórmula implementada = 33333.3; bandas del contrato = >300/250-300/200-250; estándar EPEF = `ADG × viabilidad% / (FCR × 10)`).

## 2 · Significado de negocio

El **IPE (Índice Productivo Europeo, G-06)** es el índice compuesto de eficiencia productiva del lote (combina viabilidad, ganancia diaria y conversión). Su valor se muestra al usuario **con una clasificación** (Excelente/Bueno/Regular) derivada de las bandas `reference` del propio contrato. Para que la clasificación sea informativa, la escala del número y la escala de las bandas deben ser la **misma** unidad de medida.

## 3 · Comportamiento actual del producto

| Hecho | Estado |
|---|---|
| Fórmula implementada | `(Viabilidad%_numérico × Ganancia_Diaria_g × 100) / (FCR × 10)` (viabilidad como 95.0, no 0.95) |
| Bandas del contrato | `>300` excelente · `250-300` bueno · `200-250` regular (escala EPEF estándar) |
| Efecto | Para rangos típicos de engorde, el número cae ~100× por encima de las bandas ⇒ la clasificación resulta **sistemáticamente favorable** (p. ej. el fixture aceptado muestra 556.6 «Excelente» con una conversión simplificada desfavorable de 24.5) |
| FCR | Simplificado por contrato propio («kg feed / kg weight (estimado)», «requiere datos de pesaje para FCR real») — condiciona la interpretabilidad del índice con datos heredados |
| Persistencia | NINGUNA: el KPI se calcula en vivo por vista; no hay datos históricos que migrar |

## 4 · ¿Existe definición canónica dirimente?

| Fuente | Qué dice | Nivel |
|---|---|---|
| Router + servicio (`reports`) | Fórmula con `× 100` (los mismos docstrings que definen las bandas) | 4 |
| Bandas `reference` del contrato | Escala EPEF estándar (>300/…) | 4 |
| `docs/02 §3.12.1` | Enumera indicadores funcionales; **no define** el IPE ni su escala | — |
| `specs/` | Sin definición del IPE | — |
| Estándar EPEF externo (referencia del propio nombre «Europeo») | Escala ~200-400; `ADG × viabilidad% / (FCR × 10)` | 6 (convención) |
| Owner Decisions | Ninguna cubre escala/umbrales del IPE | — |

⇒ **Dos reglas de nivel 4 en conflicto mutuo y sin fuente superior que dirima.** No es un defecto de implementación (el código hace lo que su docstring dice); es una **ambigüedad de definición de negocio**.

## 5 · Interpretaciones legítimas posibles

1. **Escala estándar**: el `× 100` es un artefacto (viabilidad porcentual vs fraccionaria) y el valor debe vivir en la escala de las bandas; las bandas permanecen.
2. **Escala implementada**: el número actual es el «índice interno» y las **bandas** deben reescalarse ×100 (Excelente >30000, etc.) para ser coherentes.
3. **Estatus actual + documentación**: mantener número y bandas como están, declarando explícitamente que el índice no es comparable con el EPEF estándar (la clasificación actual queda poco informativa).

Las tres son decisiones de **política de negocio**; el repositorio no elige por sí solo.

## 6 · Requerimiento de decisión del propietario

- Test §21: ¿regla no determinable por canónicas? **SÍ** · ¿múltiples conductas legítimas? **SÍ** · ¿elegir cambia el significado de negocio? **SÍ** ⇒ **OWNER_DECISION_REQUIRED**.
- Paquete preciso: `GA_GOV_02_OWNER_DECISION_PACKET.md` (una decisión; opciones A/B/C; recomendación razonada; no se decide por el propietario).
- Secuencia correcta (§40): **OBSERVACIÓN → DECISIÓN → SPEC → (finding solo si la implementación deja brecha) → AC → IMPLEMENTACIÓN**. No se abre finding de implementación antes de la decisión.

## 7 · Relación con R-184 y con R-186

| Pregunta | Respuesta |
|---|---|
| ¿Causada por el fix de R-184? | **NO** (la fórmula no se tocó; la tensión existía desde la definición original) |
| ¿Revelada durante R-184? | **SÍ** (paso de traza de negocio obligatorio) |
| ¿Invalida R-184 técnicamente? | **NO** (R-184 cerró un crash de tipos; la escala es semántica ajena a ese AC) |
| ¿Reabre R-184? | **NO** (no hay regla canónica preexistente que la conducta aceptada incumpla — test §38) |
| ¿Altera el caso aceptado 556.6? | **NO como hecho histórico** (el valor aceptado sigue siendo el comportamiento documentado de esa generación; una eventual decisión futura sería otra tranche con su propia aceptación) |
| ¿Contradice algún AC de R-184? | **NO** |
| Relación con R-186 | **INDEPENDIENTE** (el crash de fecha es ortogonal a la escala; cada uno tiene su vía) |

## 8 · Clasificación final

**OWNER_DECISION_REQUIRED** (decisión de política de negocio, candidata a OD siguiente libre tras OD-21 — numeración a ratificar). Implementación autorizada: **NO**. Hogar: backlog GA-GOV-02 (decisión pendiente).
