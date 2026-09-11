# GA-GOV-01 · DECISIONES DE CLASIFICACIÓN

Regla de la tranche: **implementación autorizada = NO** para todos los ítems (§22).

---

## OBS-UAT-01 · Descubrimiento del módulo Lotes

| Campo | Valor |
|---|---|
| Observación | No existe entrada de menú para el flujo de Lotes; en GA-UAT-04 se facilitó enlace directo; aceptado con observación |
| Decisión | **UX_ENHANCEMENT_ONLY** (mejora de descubrimiento de navegación) |
| Clasificación §10 | `UX_ENHANCEMENT` |
| Severidad | **P2** (flujo usable pero poco descubrible) — no P1: la navegación sin entrada de `/lots*` es estado **inventariado y decidido** en GA-FE-03 (aceptado en GA-UAT-01), no una contradicción de AC |
| ¿Dueño existente? | No finding que lo posea; documento gobernante: `GA_FE_03_NAV_SOURCE_INVENTORY.md §34` |
| ¿Nuevo R? | **NO** (falla §23.4/§23.5: diseño de alcance aceptado + preferencia de mejora) |
| ¿Decisión del propietario? | No (registrado como mejora; puede priorizarse cuando el programa abra la iteración de navegación) |
| Implementación autorizada | **NO** |
| Hogar canónico | Backlog → GA-GOV-01 «Mejoras de navegación P2 (sin R)» |

---

## OBS-UAT-04 · Elegibilidad de áreas en baja lógica

| Campo | Valor |
|---|---|
| Observación | El selector de Área mostró un área propia en baja lógica; aceptado con observación |
| Decisión | **OWNER_DECISION_REQUIRED** |
| Clasificación §14 | `OWNER_DECISION_REQUIRED` (silencio canónico verificado: R-179 solo tenencia; CRUD sin filtro de estado; GA-FE-06-A §29 se negó expresamente a inventar la regla de «activa») |
| Severidad | **P3** (propuesta; la decisión puede elevarla a P2 si el propietario elige la opción C) |
| ¿Nuevo R? | **NO** (falla §23.6: requiere decisión previa del propietario) |
| Implementación autorizada | **NO** |

### Pregunta al propietario (§26)

**¿Debe impedirse usar recursos dados de baja (p. ej., un Área inactiva) al crear NUEVAS referencias —manteniendo intactas las referencias históricas?** (Hoy: no existe regla en ninguna fuente; el backend acepta el área inactiva y la interfaz la muestra en el selector.)

| Opción | Contenido | Consecuencia técnica | Coste |
|---|---|---|---|
| **A** | **Estatus actual**: la baja lógica no restringe referencias nuevas; el selector seguirá mostrando áreas inactivas | Cero trabajo; persiste el ruido de selección | 0 |
| **B (recomendada como default neutro)** | **Filtro de selección en la interfaz**: ocultar áreas inactivas en los selectores de altas nuevas (filtro cliente por `is_active`), sin tocar backend ni referencias históricas | Mejora UX acotada; ninguna migración; ninguna regla de dominio nueva | Bajo (tranche UX/navegación) |
| **C** | **Regla de dominio completa**: además del filtro UI, el backend rechaza referencias nuevas a recursos inactivos (contrato de denegación gobernado) y se define política de baja para recursos con histórico (p. ej., condicionar la baja si hay lotes activos) | Cambio backend + AC + pruebas PG; coherente y completo; tranche propia | Medio |

- **Default neutral sugerido:** **B** (mejora visible con riesgo mínimo), reservando **C** para una decisión explícita de política de dominio.
- **Por qué el repositorio no puede resolverlo:** ninguna fuente canónica define elegibilidad por estado (`is_active`); inventarla violaría la disciplina de alcance ya aplicada en GA-FE-06-A §29.

---

## OBS-UAT-06 · Área ausente del detalle

| Campo | Valor |
|---|---|
| Decisión | **ACCEPTED_DESIGN** |
| Fundamento | Ninguna spec la exige; API `LotRead` expone el dato; decisión de alcance GA-FE-06-C15 registrada; propietario aceptó |
| ¿Nuevo R? | **NO** |
| Nota futura | P3 opcional: mostrar el nombre del Área en el detalle (junto a la Fecha prevista) cuando se aborde una mejora de la ficha del lote |
| Implementación autorizada | **NO** |

---

## UAT-11 · Consecuencia visible del SLA

| Campo | Valor |
|---|---|
| Decisión | **NOT_A_DEFECT** (`N/A_BY_DESIGN`) |
| Fundamento | `docs/02 §3.14`/`OD-08`: el aviso es una notificación evaluada por tarea interna; la campana es el consumidor; ninguna fuente exige superficie a demanda |
| ¿Nuevo R? | **NO** |
| Implementación autorizada | **NO** |

---

## R-184 · Chequeo de relación

| Campo | Valor |
|---|---|
| Relación con las observaciones | **NINGUNA** (no tocan `reports/kpi/ipe`) |
| Estado | SEPARATE_OPEN (sin cambio) |
| Implementación autorizada | **NO** (fuera de alcance de esta tranche) |

---

## Resumen de decisiones

| Ítem | Clasificación | Severidad | ¿R nuevo? | ¿Owner? | ¿Implementar? |
|---|---|---|---|---|---|
| OBS-UAT-01 | UX_ENHANCEMENT_ONLY | P2 | NO | No | NO |
| OBS-UAT-04 | OWNER_DECISION_REQUIRED | P3 | NO | **SÍ** | NO |
| OBS-UAT-06 | ACCEPTED_DESIGN | P3 (nota) | NO | No | NO |
| UAT-11 | NOT_A_DEFECT (N/A_BY_DESIGN) | — | NO | No | NO |
| R-184 | SEPARATE_OPEN | P2 (existente) | Ya existe | No | NO |

**Implementación autorizada global: NO — en todas las filas.**
