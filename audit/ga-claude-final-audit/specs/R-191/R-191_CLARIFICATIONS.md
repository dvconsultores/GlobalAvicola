# R-191 · CLARIFICACIONES

Fecha: 2026-09-13 · HEAD `c0b4afc` · Resolver antes de C2.

| # | Pregunta | Supuesto por defecto | Fuente | Decisión |
|---|---|---|---|---|
| C-01 | ¿Cuál es el código canónico de la fase de producción? | `PROD` (nombre «Producción»), presente en las tres semillas (`baseline_seeds.py:125`, `dev_seeds.py:528`, `integration_seeds.py:385`). La UI resuelve por `code === 'PROD'` y, como respaldo, por nombre `/producc/i` (misma expresión que `resolveStageKey`) | semillas | técnica |
| C-02 | ¿Cómo obtiene el cliente el `phase_id`? | **A (por defecto)**: `GET /masters/productive-phases?limit=100` (permiso `masters:read`; el rol operador de semillas lo tiene, `seeds/test_seeds.py:126-134`; verificar en C1 los roles reales de la empresa 1). **B (respaldo, sin permiso nuevo)**: `LotPhaseCreate.phase_code: Optional[str]` resuelto en servidor cuando `phase_id` falta. Se implementa A; B sólo si C1 detecta un rol con `lots:create` sin `masters:read` | `masters/router.py:36,115` | técnica |
| C-03 | ¿Debe `add_phase` cerrar la fase anterior? | Sí: exactamente una fase activa por lote (`is_active`), `end_date` de la anterior = `start_date` de la nueva si estaba vacío. Hoy no lo hace (`lots/service.py:685-697`) | modelo `lots/models.py:26` | técnica; ratificar con dominio |
| C-04 | ¿Se exige que la nueva fase sea la «siguiente» (`order`)? | No en este paquete: sólo se rechaza repetir la fase activa. El orden (`productive_phases.order`) se documenta como residual | `masters/models.py:265` | técnica |
| C-05 | Poblaciones de inicio de fase: ¿las escribe el operador o se derivan? | Si el operador las escribe, se respetan; si el cuerpo las omite (o son 0/0), el servidor las deriva del **saldo neto por sexo** (Σ `bird_movements` entradas − salidas, semántica `_suma_neta`). La UI muestra los valores derivados como placeholder | `validators.py:21-46,49-88` | técnica; **ratificar en UAT** (el propietario confirma que la población de inicio de producción es el saldo vivo del día) |
| C-06 | Lotes con dos fases activas creadas por API antes de R-191 | Se listan en C3 (consulta de reconciliación `SELECT lot_id, count(*) FROM lot_phases WHERE is_active GROUP BY lot_id HAVING count(*) > 1`) y se reportan; no se corrigen automáticamente | — | **`OWNER_DECISION_REQUIRED`** sólo si la consulta devuelve filas en producción (corregir a mano o dejar) |
| C-07 | Códigos divergentes de engorde/incubación entre semillas (`ENG`/`INC` vs `ENGORDE`/`INCUB`) | Fuera de alcance (no afecta a `PROD`); residual anotado para GA-GOV-03 / semillas | semillas | técnica |
| C-08 | ¿La transición debe validar `start_date` contra `lot.start_date`? | Sí (400 si anterior); BR-19 (periodo cerrado) no aplica a fases | `lots/service.py` | técnica |
| C-09 | ¿Se audita `PHASE_STARTED`? | No aquí: P1-12 REAPERTURA fija un único productor de auditoría y añade `add_phase`; R-191 deja el punto documentado | `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md` G-18 | técnica |
| C-10 | ¿Qué ocurre con las acciones rápidas del detalle tras la transición? | Cambian al catálogo de producción (`STAGE_OPERATIONS.*_production`) porque `resolveStageKey` recibe el código real; sin cambio de catálogo | `processCatalog.ts:205-240,312-321` | técnica |

Sin decisiones bloqueantes para C2. **C-06** sólo requiere al propietario si hay datos históricos afectados.
