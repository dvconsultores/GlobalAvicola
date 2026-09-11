# GA-BU-D10 · EVIDENCIA RED (R-188 — OD-23 · B)

Fecha: 2026-09-11 · C1 pre-decisión: `067fba6` · Decisión: **B** (OD-23 RATIFIED).

## 1 · Qué es el RED

Con OD-23 (B) ratificada, la conducta vigente del producto (provisional A: al re-encender, la concesión previa **vuelve a ser efectiva** — `AC-A06`) **difiere** de la política ratificada. El RED es la suite nueva `backend/tests/test_r188_bu_lifecycle.py` (10 pruebas) que afirma **B**:

- apagar **termina** (marca `revoked_at`; no borra; auditoría individual con causa);
- re-encender **no devuelve** efectividad;
- concesión nueva **restaura** y conserva historia (2 filas);
- idempotencia normalizadora; puertas preservadas (conceder-con-OFF 409 · self-grant 403 · cross-company 404 · zero-BU); transferencia de empresa intacta.

## 2 · Por qué el RED es válido contra el código actual (pre-C3)

1. **Contradicción directa de suites**: la prueba vigente `test_ac_a06_rehabilitar_devuelve_la_efectividad_a_la_concesion_previa` (`test_business_units.py:509`) afirma lo **contrario** a `test_r188_reactivar_no_devuelve_la_concesion`. Pre-C3 no pueden pasar ambas ⇒ la suite R-188 es RED.
2. **Traza de código**: `admin.fijar_habilitacion` (`:137-172`) solo modifica `is_enabled` (+ auditoría CONFIG_CHANGE); **no marca ninguna concesión**. El resolutor (`service.py:97-124`) exige `is_enabled=True` ⇒ al re-encender, la concesión viva vuelve a ser efectiva **sin acto alguno** (conducta A probada por la suite provisional).
3. **Ejecución local declarada**: `compileall` OK; `pytest tests/test_r188_bu_lifecycle.py` ⇒ **10 skipped** (requiere PostgreSQL; patrón declarado del repo, corre en CI con `backend/scripts/run_tests.sh`). La validación ejecutable de esta tranche es el **runtime autenticado** (post-fix) contra la evidencia pre-fix committeada (suites A + runtime GA-FE-02-E, `is_effective=false` con viva).

## 3 · RED→GREEN planificado

| Fase | Evidencia |
|---|---|
| RED (pre) | Suites A (auto-reactivación) committeadas + traza de código + esta suite B (contradice) |
| GREEN (post-C3) | Suite R-188 en CI; en runtime: E2E-04 «re-encender ⇒ DENY histórico» vs pre-fix «re-encender ⇒ ALLOW»; concesión nueva ⇒ ALLOW + auditoría; apagado ⇒ termina + audita |
| Control positivo | E2E-01/05 (ON+concesión ⇒ ALLOW; regrant ⇒ ALLOW) |

## 4 · Cambio de expectativas provisionales (a ejecutar en C3)

`AC-A04` conserva «apagar no borra» (ahora: **marca**; la fila queda) · `AC-A06` y `test_deshabilitar_no_borra_las_concesiones_y_rehabilitar_las_devuelve` se reexpresan a B (termina / no devuelve / concesión nueva restaura). Documentos históricos de auditoría (`audit/ga-fe-02/**`, matrices) **no se reescriben**: se superan por OD-23+R-188 con nota prospectiva.
