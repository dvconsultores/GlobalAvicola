# GA-UAT-09 · NOTA DE PREFLIGHT DE GOBERNANZA — R-153 / OD-25

Fecha: 2026-09-12 · Commits del tranche: `9651550` (C1) · `47ea484` (C2) · `db8ae21` (C2b) · `8564364` (C3).

## G-01 · Secuencia de la enmienda C2b — `SPEC_DEVELOPMENT_SEQUENCE_DEVIATION`

**Determinación: NO — la spec/AC58-59 no se enmendó antes de la implementación.** Cronología verificada en git:

1. `9651550` (C1): spec + AC01-57 + clarificaciones C01-25 + RED. **No contiene AC58/59**.
2. `47ea484` (C2): producto (gate, hook, generador, frontend). Sin cambios de clasificación.
3. **`db8ae21` (C2b)**: implementación del tercer origen de derivación (`classification.py`) **junto con** sus tests — descubierto durante el E2E runtime de certificación (el evento sin lote era inalcanzable; sin esto, OD-25 (B) resultaba inoperable).
4. `8564364` (C3): enmienda documental **posterior** — anexo AC58/59 en la spec, clarificación C26, checklist, evidencia y certificación.

Declaración: la desviación es **de secuencia documental**, no de comportamiento: el contrato del cambio quedó escrito y probado (AC58/59), pero **después** de implementarlo. Se registra aquí y en el historial de certificación. **No se modifica producto por esta causa.**

## G-02 · Significado de «reparado» en OBS-1 — `DATA_RESTORATION_ONLY`

**Determinación: restauración de datos, sin cambio de producto.**

- `GET /roles` no define `search` (`auth/router.py:178`); el guion de limpieza lo asumió y desactivó 14 roles legítimos. La reparación fue `PUT /roles/{id}` con `is_active:true` (mismo endpoint, solo datos).
- Ningún archivo de `auth`/roles (backend o frontend) aparece en `--stat` de los cuatro commits del tranche.
- Verificación viva posterior: 14 legítimos activos · 0 inactivos · 0 roles sintéticos visibles.

Conclusión: **no hay hotfix oculto**; UAT-09 no queda bloqueada por este punto.
