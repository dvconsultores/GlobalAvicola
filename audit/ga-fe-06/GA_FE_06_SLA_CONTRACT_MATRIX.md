# GA-FE-06 · MATRIZ CONTRATO SLA (derivada de la regla vigente, sin inventar)

Regla: ventana `0 <= faltan <= 3` días naturales · `status == active` · `planned_close_date NOT NULL` (ver `GA_FE_06_SLA_TRACEABILITY.md`).
Verificación runtime: el evaluador se ejecuta por su **mecanismo canónico** (`evaluar_lotes_proximos_a_cierre`) y el resultado se lee en la tabla `notifications` vía el **consumidor real** (`GET /notifications` del destinatario autorizado; la UI de notificaciones existe en el producto: campana).

| # | Lote fixture (creado por UI en E2E cuando aplique) | `planned_close_date` | Estado lote | BU | ¿Entra? (regla) | Verificación runtime | Resultado |
|---|---|---|---|---|---|---|---|
| S1 | `PLD=+10` | hoy+10 | active | broiler ON | NO | evaluación + lectura avisos del actor | (E2E-10) |
| S2 | `PLD=+3` (frontera) | hoy+3 | active | broiler ON | **SÍ** | íd. (`days_remaining=3`) | (E2E-11) |
| S3 | `PLD=+1` (dentro) | hoy+1 | active | broiler ON | **SÍ** | íd. (`days_remaining=1`) | (E2E-12) |
| S4 | `PLD=NULL` | — | active | broiler ON | NO (excluido) | íd., sin aviso | (E2E-13) |
| S5 | `PLD=−1` (pasada) | hoy−1 | active | broiler ON | NO | íd., sin aviso | extra |
| S6 | cualquiera dentro | hoy+2 | closed/final | broiler ON | NO (`status != active`) | **N/A** — no se fabrica lote cerrado solo para esto (cierre exige flujo completo y no aporta al cierre R-182; la condición está explícita en el código y cubierta por `test_lot_planned_close.py` en CI) |

## Mecanismo canónico de evaluación (verificado en código)

- El producto evalúa por una **tarea interna del proceso** (`vigilar_revisiones_pendientes`) configurada con `NOTIFICATION_SLA_SCAN_ENABLED=True` y `NOTIFICATION_SLA_SCAN_SECONDS=3600` ⇒ **ciclo horario**. No existe endpoint de disparo manual (verificado: rutas de `notifications/router.py` = listar/contar/marcar leído).
- El comentario de `main.py` fija la doctrina de prueba: la suite llama al evaluador directamente para determinismo; el vigilante se desactiva con `GA_TEST_ENV=1`.

### Certificación R-182 en tres capas (sin reimplementar la regla)

| Capa | Qué prueba | Cómo |
|---|---|---|
| **Datos de origen (runtime)** | Un lote creado **por UI** persiste `planned_close_date`/`area_id` exactos | E2E autenticado: fresh GET por API oficial tras alta UI |
| **Regla de dominio (canónica)** | Ventana `0..3`, frontera, NULL excluido, solo `active` | `tests/test_lot_planned_close.py` — suite canónica del repo para esta regla (CI con PG; local sin PG = skipped, declarado) |
| **Aviso real (oportunista)** | El scanner horario produce `lot_near_close` para el originador | Fixtures `+0/+1/+3` creados temprano; al cierre de la tranche se relee `notifications` del actor; si el ciclo horario ya corrió, se captura el aviso; si no, se registra `PENDING_SCAN_WINDOW` (el ciclo es horario por diseño; no se fuerza ni se reimplementa) |

- **Alcance de destinatarios**: `resolver_destinatarios(company_id, area_id, originadores)` ⇒ el aviso nunca cruza empresa (AC28); lectura de avisos respeta el inquilino del actor (consumidor existente).
- **Fechas de fixtures**: `reference_today()` (día local del servidor) — misma convención que `test_lot_planned_close.py`.

## Consumidor UI

Campana de notificaciones (`/notifications`): superficie real del producto (`notifications/unread-count` usado por la campana). La evidencia lee el aviso del destinatario autorizado; si el aviso no aparece en la campana por diseño de UI, la evidencia de persistencia (API del consumidor) es suficiente y se documenta.
