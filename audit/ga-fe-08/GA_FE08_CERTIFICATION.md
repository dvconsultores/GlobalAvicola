# GA-FE-08 · CERTIFICACIÓN (OBS-UAT-01 · DESCUBRIBILIDAD DE LOTES)

Fecha: 2026-09-11 · Commits: C1 `4ba33f6` · C2 `a946cec` · C3 (este cierre) · Evidencia: este hogar (`evidence/`).

```
OBS-UAT-01:
RESOLVED

GA-FE-08:
FUNCTIONALLY_CERTIFIED

Clasificación de la brecha:
MISSING_NAV_CONFIGURATION

OWNER_UAT_REQUIRED:
YES        (cambio visible de navegación)

OWNER_UAT_READY:
YES        (guía GA_OWNER_UAT_FE08_GUIDE.md; 5 casos)

Owner acceptance:
PENDING    (no se auto-aprueba)

Generación:
index-DtzHNDMG.js (health 200)

Backend:
sin cambios (diff 0) · sin migración · sin permisos/rutas/endpoints nuevos

No reabre:
GA-FE-03 · R-119 · GA-FE-04 · R-98 · ningún R nuevo
```

## Alcance certificado

- Entrada declarativa `lots` en `NAV_ITEMS` como **primera hija de «Gestión Avícola»** → tarjeta en el hub `/menu/poultry` (desktop y móvil), reusando ruta `/lots`, permiso `lots:read`, icono `Layers` y clave `nav.lots` existente.
- Autoridad por el **evaluador certificado GA-FE-03** (permission ∩ unidad ∩ empresa): BU OFF oculta (global incluido); sin concesión oculta; OD-23 histórico no revive; concesión nueva restaura; sin RBAC oculta; zero-BU/control no ganan Lotes.
- Deep link: contrato de ruta intacto; sin autoridad ⇒ denegación visual (sin permiso) o sin datos (sin unidades).
- Desktop + móvil + ES/EN + estado activo + orden del hub.

## Evidencia clave

- RED 7 failed/5 passed → GREEN 292/292 (38 archivos; +12) · build ✓ · backend diff 0.
- E2E-01…10 **PASS** (C01-C09) · consola 1 pre-existente ajena (N-1) · overflow 0 · 404 spot cross-tenant.
- Limpieza: 4×OFF · usuarios/roles fuera · credenciales destruidas · login post-baja 403.

## Límites y declaraciones honestas

- Suites PG locales: skipped declarado (sin servidor); corren en CI (`backend/scripts/run_tests.sh`); backend diff = 0 ⇒ pre/post idéntico por construcción.
- Frontera incubadora-solo documentada (C05): la entrada usa «conjunto productivo no vacío» del marco certificado; no se añadió ninguna dimensión nueva al evaluador.
- 1 error de consola en la sesión del Access Admin: `GET /dashboard/admin → 403` en el home (pre-existente; N-1 GA-UAT-08; ajeno a esta tranche).
