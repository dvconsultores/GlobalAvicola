# GA-REQ-061 · PLAN E2E (futuro — NO ejecutar en esta fase)

Regla: **no certificar BU por transitividad** — una corrida E2E específica por BU con artefactos (journal + PNG/JSON) y 0 `pageerror`. Escenario transversal primero (batch+apply+reconciliación), y después el recorrido operativo de cada BU sobre el lote migrado.

## Transversal (común)

1. Batch por BU (company X) con plantilla de la BU; subir; validar; preview; submit; aprobar (actor distinto); apply.
2. Reconciliación del batch: source/checksum/cutover/items/UNKNOWN count.
3. Sondas negativas: cross-company 404, BU OFF 403, re-apply 409, apply con errores bloqueado.
4. Auditoría: eventos CREATE→…→APPLY presentes con actor/empresa/BU.

## GRANDPARENT (Progenitoras)

Lote migrado con aves vivas al corte + mortalidad histórica; mortalidad post-cutover; estado actual; reconciliación. Verifica que el lote sigue OPERANDO como nativo (motor normal).

## BREEDER (Reproductoras)

Lote migrado; aves vivas; mortalidad histórica; producción histórica acumulada; producción post-cutover; reporte acumulado (Opening/Post/Lifetime) coherente; UNKNOWN no fabricado si faltara histórico.

## HATCHERY (Incubadora)

Proceso **ya comenzado**: huevos recibidos/cargados/en proceso, etapa de incubación, fecha prevista; transferencia posterior y nacimientos **dentro de GA**; reconciliación. Sin recepción SAP fabricada; sin asumir modelado solo-Lot (ver arquitectura §4).

## BROILER (Engorde) — caso numérico obligatorio (mandato §53)

Datos: aves vivas 10.000 · mortalidad histórica 500 · **alimento histórico UNKNOWN** · peso 1.550 kg · post mortalidad 35 · post peso 1.620 kg.

| Salida | Esperado |
|---|---|
| current live | **9.965** |
| mortality post | 35 |
| mortality lifetime | **535** |
| historical feed | **UNKNOWN** (visible, ≠ 0) |
| lifetime FCR | **UNKNOWN** (componente histórico ausente) |
| post-cutover KPIs | calculados con datos post (p.ej. ADG post con pesos disponibles) |

Además: nunca mostrar “Total mortality = 35” ni “0 kg” para el alimento histórico (AC77).

## Criterios de cierre E2E de la capacidad

- 4/4 BUs con corrida propia y artefactos.
- Sondas negativas en verde (denegaciones correctas).
- Reconciliación reproducible (mismas entradas ⇒ mismo reporte).
- 0 fabricaciones: sin recepciones/eventos SAP/documentos inventados (verificación por listado de eventos creados durante el E2E).
