# GA-FE-07 · FINDING **R-185** — Referencia nueva a Área inactiva (registro canónico)

```
ID            R-185 (siguiente libre verificado: el catálogo llega a R-184; sin R-185 previo)
FECHA         2026-09-11
ORIGEN        OBS-UAT-04 (GA-UAT-04) → GA-GOV-01 (OWNER_DECISION_REQUIRED) → OD-21 (decisión)
SEVERIDAD     P2 (deuda de integridad de dominio post-R-182; no reabre R-182)
ESTADO        OPEN → (se cierra al completar GA-FE-07)
CLASE         integridad funcional de dominio — no solo UI, no solo seguridad
```

## Título

**Un área inactiva (baja lógica) puede seleccionarse/asignarse como referencia nueva de un lote.**

## Causa raíz

`GA-REM-039` añadió `lots.area_id` y `GA-FE-06-A` cubrió la **pertenencia** (empresa). Ninguna capa —UI ni backend— aplicaba la **elegibilidad por estado**: el listado de maestros devuelve todas las áreas (sin filtro `is_active`) y el validador de referencias (`verificar_catalogo_de_empresa`, R-179) solo mira tenencia. Antes de OD-21 el comportamiento esperado no estaba definido (por eso GA-GOV-01 clasificó `OWNER_DECISION_REQUIRED`); con OD-21 queda definido y el defecto, tipificado.

## Superficie afectada

- Alta de lote (`POST /lots`) — acepta área inactiva (201, persistida).
- Edición de lote (`PUT /lots/{id}`) — cambia la referencia a un área inactiva (200).
- Selector de área del formulario de lote (muestra inactivas).

## Expectativa canónica (OD-21)

Área inactiva: no seleccionable, no asignable en referencia nueva (alta o cambio); histórico preservado; ediciones no relacionadas de lotes con área inactiva siguen permitidas; cambio de área solo a áreas **activas** de la **misma empresa**.

## Evidencia

RED (pre-fix, generación backend `69d0c95`): `audit/ga-fe-07/evidence/red/` — alta con inactiva → **201** (lote 41); edición a inactiva → **200** (fresh `area_id=7`); selector con inactivas presentes. Controles: histórico legible; update no relacionado 200; NULL 201; área ajena 400 «no encontrado».

## Dedup

No duplica R-171 (catálogo incubadora), R-179 (tenencia), R-182 (contrato/captura/seguridad), R-98/R-119 (UI autorización/navegación). No existía finding de elegibilidad por estado. Detalle: `GA_FE_07_FINDING_DEDUP.md`.

## AC

`GA07-AC01…44` (ver spec §AC). Cierre condicionado a: denegación de alta/edición con inactiva, selector filtrado, preservación histórica, controles positivos, regresiones verdes.

## Dependencias

Ninguna externa. `OD-21` es la regla gobernante; implementación limitada a Área→Lote.

## Fuera de alcance

R-184 · OBS-UAT-01 · mostrar área en detalle · otros maestros (documentados como principio general, sin implementación) · migraciones · retro-invalidación.
