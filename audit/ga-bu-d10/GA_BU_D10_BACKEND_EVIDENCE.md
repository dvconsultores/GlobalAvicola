# GA-BU-D10 · EVIDENCIA BACKEND (R-188 · OD-23 B)

Fecha: 2026-09-11 · Commits: C2 `0542310` (decisión/SPEC/RED) · C3 `bee33f5` (implementación).

## 1 · Diff de implementación (mínimo)

```
backend/app/business_units/admin.py           (fijar_habilitacion: marca+audita al apagar; docstrings)
backend/app/business_units/models.py          (docstring del modelo alineado a OD-23)
backend/tests/test_business_units.py          (AC-A04 docstring; AC-A06 → expectativa B)
backend/tests/test_business_unit_admin.py     (AC-A05 listado; ciclo OFF→ON→regrant → B)
4 files changed, 90 insertions(+), 43 deletions(-)
```

Notas: **cero migraciones**, cero cambios de esquema, cero endpoints/permisos nuevos; resolutor y proyecciones intactos (la marca satisface `revoked_at IS NULL` sin tocar `service.py`).

## 2 · Gates locales ejecutados

| Gate | Resultado |
|---|---|
| `compileall` (admin/models/3 suites) | **OK** |
| Gate canónico OD-16+catálogo (subset local) | **7 passed** |
| Suites BU completas (r188+business_units+admin+guard+grant_candidates+access_administration) | **48 failed / 10 passed / 10 skipped / 117 errors** — **idéntico ANTES y DESPUÉS de C3** (verificado por `git stash` comparativo): artefactos locales por ausencia de PostgreSQL; **delta R-188 = 0**; corren en CI (`backend/scripts/run_tests.sh`) |
| Suite R-188 en local | **10 skipped** (PG requerido, declarado) |

## 3 · Qué cambia exactamente

- `fijar_habilitacion(habilitada=False)`: tras fijar `is_enabled`, **marca** (`revoked_at=now`) todas las concesiones vivas de ESA habilitación; audita cada terminación (`PERMISSION_CHANGE`, `granted→revoked`, `cause=company_business_unit_disabled`, `target_user_id`). Config idempotente + normalizadora (un segundo apagado no duplica nada).
- `fijar_habilitacion(habilitada=True)`: sin tocar concesiones (no revive nada).
- `conceder/revocar/candidatos`: sin cambios (puertas OD-15 intactas).
- Resolver `unidades_efectivas`: sin cambios.

## 4 · Expectativas provisionales reexpresadas (provisional A → ratificada B)

- `test_ac_a04_apagar_una_unidad_no_borra_las_concesiones` — conserva «no borra»; docstring OD-23.
- `test_ac_a06_...devuelve_la_efectividad...` → **`test_r188_rehabilitar_no_devuelve_efectividad_sin_concesion_nueva`** (apagar marca; encender no devuelve; concesión nueva sí).
- `test_deshabilitar_no_borra...devuelve` → **`test_r188_deshabilitar_termina_y_rehabilitar_no_devuelve`** (vivas 0 tras OFF; historia escrita; regrant restaura).
- `test_el_listado_separa_otorgada_de_efectiva` → **`test_r188_el_listado_refleja_terminacion_y_efectividad`**.
- Documentos históricos de auditoría (`audit/ga-fe-02/**`, matrices) **no se reescriben**; quedan superados por OD-23 con nota prospectiva en el hogar R-188.
