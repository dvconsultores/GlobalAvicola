# GA-GOV-02 · DEDUP — R-186

## 1 · Descripción del candidato

Defecto de fecha en `GET /reports/kpis/production-index` (G-05): `date.today() − lot.start_date` (date − datetime aware) ⇒ `TypeError` ⇒ HTTP 500 con todo lote con `start_date`. Capturado en runtime (`prodindex35` = 500) y verificado por inspección de código (expresión hermana de la que causó R-184).

## 2 · Chequeo de estatus formal

| Pregunta | Respuesta |
|---|---|
| ¿Existe registro formal OPEN previo? | **NO** — solo etiqueta «(propuesto)/(candidato)» dentro de artefactos R-184 |
| ¿ID legítimamente reservado? | **SÍ** — siguiente libre tras R-185 (R-183 fue absorbido sin entrada) |
| Formalidad previa | `INFORMAL_CANDIDATE_LABEL` |

## 3 · Comparación con findings existentes

| IDs revisados | Motivo de no-duplicidad |
|---|---|
| **R-184** (IPE, cerrado/aceptado) | Misma **clase** técnica (date−datetime en un KPI), pero **endpoint distinto** (G-06 vs G-05), **expresión distinta** (línea propia no tocada por el fix), **AC distintos**, **remediación distinta** (cada método tiene su propia expresión — el fix de IPE no altera G-05; verificado en diff C2). `RELATED_BUT_DISTINCT` → **no absorbido** |
| R-142/R-143/R-144/R-145/R-146 (revisión/SAP/idempotencia) | Síntoma/raíz/AC/proceso distintos. R-144 (cierre sin FCR, BR-05) menciona FCR pero en resumen de cierre, no en este endpoint |
| R-147 (constantes/tipos sin fuente normativa) | Meta-clase vecina (calidad normativa), dominio distinto (unidades/umbrales T°/H°, enums). Sin relación con el crash |
| R-148/R-149/R-150/R-151/R-152/R-153/R-154/R-155/R-156/R-157/R-158/R-159/R-160/R-161/R-162/R-163 | Dominios Wave B/auditoría/SAP/UX/estados. Sin mismo endpoint, misma fórmula ni misma raíz |
| R-164/R-165/R-166/R-167/R-168/R-169/R-170/R-171/R-172/R-173/R-174/R-175 | Lotes/plano de revisión/saldos/formularios/pruebas. Sin relación |
| R-176 (paridad de revalidación en edición) · R-177 · R-178 (linaje) · R-179 (validador de referencias) · R-180 · R-181 (submit/ActionGate) · R-182 (contrato de lote/PLD) | Sin mismo síntoma ni raíz; ninguno cubre `reports/kpis/*` |
| R-185 (elegibilidad por estado, cerrado/aceptado) | Dominio de referencia de áreas; sin relación |
| Findings de reportes/KPI previos | No existe ninguno que cubra `production-index` ni errores de tipo temporal en KPIs |

Comparación específica de ejes: **mismo síntoma** (500) solo con R-184 → pero distintos endpoints/expresiones; **misma raíz** (date−datetime) solo con R-184 → raíz compartida por clase, dueño distinto por línea; **mismo AC** ninguno; **mismo proceso** P-15 ambos (familia) pero distinto indicador; **misma remediación** — patrón idéntico (`_dia`) pero **línea/archivo-test distintos**.

## 4 · Resultado final

| Campo | Valor |
|---|---|
| Dedup | **DISTINCT_NEW_FINDING** (no duplicado de R-184 ni de ningún otro; no absorbible) |
| Dueño canónico | Nuevo finding **R-186** |
| ¿Por qué no `DUPLICATE_OF_R184`? | El cierre de R-184 fijó su alcance a `get_kpi_ipe`; extenderlo retroactivamente violaría la regla de alcance registrada y dejaría el endpoint G-05 sin dueño |
| ¿Por qué no `OWNER_DECISION_REQUIRED`? | No hay ambigüedad de política: un crash en entrada válida es defecto técnico con expectativa definida (precedente R-184 del propio propietario) |
| Estatus final | **FORMAL_OPEN_FINDING** — R-186 (P2, OPEN) |
| Registro de la corrección de estatus | Entrada OPEN formal creada en backlog; la etiqueta previa «candidato» queda histórica (no se borra) |
