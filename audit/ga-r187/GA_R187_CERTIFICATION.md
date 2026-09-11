# GA-R187 · CERTIFICACIÓN

Fecha: 2026-09-11 · Tranche: R-187 (implementación de OD-22) · Commits: C1 `5a32a6c` · C2 `f755baa` · Evidencia C4 (este paquete).

## Veredicto técnico

```
R-187:
CLOSED

Technical:
FUNCTIONALLY_CERTIFIED

OD-22:
RATIFIED_IMPLEMENTED

OWNER_UAT_REQUIRED:
YES        (G-06 es USER_VISIBLE; el número mostrado cambia por decisión de negocio)

OWNER_UAT_READY:
YES

Owner acceptance:
PENDING     (no se auto-aprueba; §69)
```

## Alcance certificado

- **Fórmula**: `(viabilidad% × ganancia_diaria_g) / (fcr × 10)`; `× 100` retirado; guardas y redondeos intactos.
- **Bandas/labels/umbrales**: sin cambios; fronteras 249.9/250.0/300.0 verificadas exactas.
- **Fechas**: R-184 técnico preservado (`_dia()`, sin ±1 día, sin 500); valor 556.6 superseded (los mismos insumos → 5.6).
- **G-05/R-186**: intacto (5.1 estable). **GA-FE-07**: spot 400 correcto. **GA-FE-02/03**: cubiertos por matriz de seguridad/UI.
- **Seguridad**: ajeno/sin concesión/BU OFF (incl. actor global)/RBAC → denegado como estaba.
- **Datos**: sin migración/backfill; cálculo en vivo; frontend 0 diffs.

## Límites y declaraciones honestas

- Suites PG (R-184/R-186/R-187) quedan `skipped` en local (declarado; corren en CI); la validación ejecutada de esta tranche es el **runtime autenticado** (E2E-01…14) + gates locales ejecutables.
- 15 errores de `test_kpi_scope` en local son **pre-existentes** (PG) — no atribuibles a R-187.
- Fixtures sintéticos de lotes **retenidos** (documentados); actores/roles/concesiones/credenciales **destruidos**.

## No reapertura

R-184 (CLOSED_OWNER_ACCEPTED) y R-186 (CLOSED) sin reapertura; GA-FE-02..07 / R-181/182/185 / OD-21 intactos. La decisión OD-22 es prospectiva y su implementación no contradice ninguna aceptación previa (distinción régimen anterior ↔ regla vigente documentada).
