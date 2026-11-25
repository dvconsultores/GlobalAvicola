# Campaña de sensibilidad — Tanda 2 (backend, 6 mutantes)

- Repo: rama `develop`, HEAD `3073ff6`; el código de producción de los cuatro ficheros mutados es
  idéntico al del commit `8366827` (`git diff --stat 8366827 HEAD -- <4 archivos>` vacío).
- Suite de cada corrida (una sola vez por mutante):
  `backend/scripts/run_tests.sh tests/test_uat_s2_write_contract.py tests/test_uat_s2_corrections_masters.py
  tests/test_uat_s2_corrections_messages.py tests/test_uat_s2_review_filters.py
  tests/test_uat_s2_operations_pins.py -q --tb=line -p no:cacheprovider`
- Línea base sin mutar: **61 passed** (29,6 s). Ninguna corrida falló por infraestructura.
- Restauración tras cada mutante: `git restore --source=8366827 -- <archivo>` + `git diff --stat`
  vacío verificado antes del siguiente (`DIFF_VACIO_OK` en las 6 restauraciones).
- Abreviaturas: `RF` = `tests/test_uat_s2_review_filters.py`, `CM` = `tests/test_uat_s2_corrections_messages.py`,
  `WC` = `tests/test_uat_s2_write_contract.py`.

| Mutante | Archivo | Mutación | Resultado | Tests que lo detectan |
|---|---|---|---|---|
| M7 | `app/review/router.py` · `list_pending_review` | `if date_from is not None and date_to is not None and date_from > date_to:` → `if False:` (sin 400 de rango invertido) | **DETECTADO** (1 fallo) | `RF::test_rev_s2_04_rango_invertido_es_400_y_valor_no_fecha_es_422` |
| M8 | `app/review/service.py` · `ApprovalService.get_pending_approvals` | 2.ª aparición del bloque `if lot_code and lot_code.strip():` → `if False:` | **DETECTADO** (1 fallo) | `RF::test_rev_s2_05_aprobaciones_filtran_por_codigo_de_lote` |
| M9 | `app/review/service.py` · `ReviewService.get_pending_review_events` | 1.ª aparición: `Lot.lot_code.ilike(` → `Lot.lot_code.like(` (sensible a mayúsculas) | **DETECTADO** (1 fallo) | `RF::test_rev_s2_01_bandeja_filtra_por_codigo_de_lote` |
| M10 | `app/corrections/service.py` · `etiqueta_de_campo` | `return ETIQUETAS_CAMPO.get(campo, campo)` → `return campo` (identificador técnico) | **DETECTADO** (5 fallos) | `CM::test_corr_s2_05_a_el_peso_promedio_se_nombra_en_castellano`, `CM::test_corr_s2_05_b_la_semana_se_nombra_en_castellano`, `CM::test_corr_s2_05_c_la_cantidad_de_alimento_se_nombra_en_castellano`, `CM::test_corr_s2_05_d_el_tamano_de_muestra_se_nombra_en_castellano`, `CM::test_corr_s2_05_e_la_fecha_del_evento_se_nombra_en_castellano` |
| M11 | `app/operations/service.py` · `update_event` | se comenta `self.validar_cantidades_del_candidato(event, cambios)` | **DETECTADO** (3 fallos) | `WC::test_ops_s2_04c_editar_la_muestra_por_encima_de_lo_recibido_es_400`, `WC::test_ops_s2_dosis_dosis_negativa_en_la_edicion_es_400`, `WC::test_ops_s2_dosis_dias_negativos_en_la_edicion_es_400` |
| M12 | `app/corrections/service.py` · `CorrectionService._nombre_de_maestro` (línea 342) | `if hasattr(modelo, "company_id") and self.company_id is not None:` → `if False:` (se quita el filtro por empresa del nombre de maestro) | **SUPERVIVIENTE** (61 passed, 0 fallos) | — |

## Conclusión

5/6 mutantes DETECTADOS, 1 superviviente (M12). Detección mínima de 1 test (M7, M8, M9) y máxima de 5 (M10).

**M12 · línea mutada:** `backend/app/corrections/service.py:342`, dentro de
`async def _nombre_de_maestro(self, campo, valor)`:

```python
consulta = select(modelo.name).where(modelo.id == identificador)
if hasattr(modelo, "company_id") and self.company_id is not None:   # ← mutado a `if False:`
    consulta = consulta.where(or_(modelo.company_id == self.company_id, modelo.company_id.is_(None)))
return (await self.db.execute(consulta)).scalar_one_or_none()
```

Con el guard desactivado, `_nombre_de_maestro` nombra un registro de catálogo de **otra empresa**
(se consulta solo por `id`), es decir, se pierde el aislamiento multiempresa en los nombres que
muestra `_anotar_nombres` (`original_display` / `corrected_display`, `AC-S2-C04`/`AC-S2-C05`).
La suite actual lo único que comprueba son los nombres propios de la empresa (`CM::test_corr_s2_05_*`
y `test_uat_s2_corrections_masters.py`), nunca el caso "id de un maestro de otra empresa no se
nombra", así que el mutante pasa. No se añaden tests (fuera de alcance de esta campaña): queda
propuesto como hueco de cobertura de `RR-`/`AC-S2-C04` para la Sesión 2.

Las 6 restauraciones dejaron `git diff --stat` vacío; `git status --short -- backend` y
`git diff --stat` finales quedan vacíos y el único artefacto nuevo es este informe.

## Cierre del superviviente M12

- El mutante M12 **sobrevivió**: `tests/test_uat_s2_corrections_masters.py` quedaba en **61 passed** sin cubrir el caso.
- Se añadió `test_corr_s2_11_un_maestro_de_otra_empresa_no_se_nombra` (un maestro de otra empresa no se nombra: `current_display` y `original_display` son `None`).
- Con el test nuevo, M12 queda **DETECTADO** por `test_corr_s2_11_un_maestro_de_otra_empresa_no_se_nombra`.
