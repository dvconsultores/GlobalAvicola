# GA-GOV-03 · CLARIFICACIONES

Fecha: 2026-09-13 · HEAD `c0b4afc` · Resolver antes de C2 (ejecución). Las marcadas `OWNER_DECISION_REQUIRED` exigen respuesta explícita del propietario; las demás tienen supuesto por defecto verificado en el repositorio.

| # | Pregunta | Supuesto por defecto | Fuente | Decisión |
|---|---|---|---|---|
| C-01 | ¿La actualización de los 25 casos backend puede tocar `backend/app`? | **No**: solo `backend/tests/**` (la suite debe reflejar la regla vigente; si un caso revelara un defecto real, se detiene y se abre hallazgo propio). | `GA-GOV-03_FINDING.md §3` (0 APP_DEFECT) | técnica |
| C-02 | ¿La suite completa (≈20 min) entra en CI o se paraleliza? | Entra completa con timeout ≥ 40 min; si el coste se considera alto, `pytest -n auto` (pytest-xdist) como decisión de la tranche, sin cambiar aserciones. | `evidence/backend_full_suite.log` (1210 s) | técnica |
| C-03 | ¿El job de suite en `push` puede bloquear el docker-push? | **No, nunca** (invariante del repositorio: los tests no gatean el deploy). Job independiente y paralelo; el resultado se publica como artefacto/check informativo. | `.github/workflows/backend-ci.yml:4-12` (comentario) · convención del repo | **`OWNER_DECISION_REQUIRED`** solo si el propietario quiere cambiar la política (p. ej. exigir PR con CI verde para `frontend/**`/`backend/**`); el supuesto por defecto no la cambia |
| C-04 | ¿Se mantiene el trigger `pull_request` de `backend-ci.yml`/`frontend-ci.yml`? | Sí, intacto; se **añade** un workflow/job de suite en `push` (puede ser el mismo workflow con doble trigger si no altera la semántica de PR). | workflows actuales | técnica |
| C-05 | ¿Los 5 casos del grupo B se dan por verdes con el fixture corregido aunque `/me` siga devolviendo 500 con correos reservados? | Sí: el caso prueba el ciclo BU-D10, no la robustez de `EmailStr`; la robustez es **R-213** (su test irá en ese paquete). | `GA-GOV-03_FINDING.md §2.1 B`; registro G-25 (R-213) | técnica |
| C-06 | ¿Se reescriben los informes históricos de certificación? | **No**: se anotan con una cabecera de vigencia (`NOT_REPRODUCIBLE_EN_HEAD` + motivo) al ejecutar la tranche, sin borrar contenido. | encargo §52 («do not rewrite history») | técnica |
| C-07 | ¿La recertificación de procesos (P-01…P-15) forma parte de esta spec? | **No**: es la tranche 9 de la cola (tras cerrar las brechas de producto); GA-GOV-03 solo entrega la línea base verde y la regla de evidencia. | registro §3 orden 9 | técnica |
| C-08 | ¿`p03-curvas-ui` se arregla por `data-testid` nuevo (toca `frontend/src`)? | No: se desambigua el locator sin tocar producto (p. ej. `getByRole('heading')`/fila por texto compuesto). Si no fuera posible sin tocar producto, se documenta y se eleva. | `evidence/playwright_e2e.log:204-226` | técnica |
| C-09 | ¿Qué pasa con las fechas literales detectadas por `test_t028_04`? | Se retiran/parametrizan **solo en tests** (docstrings); la regla temporal del producto no cambia. | `test_time_determinism.py:95-115` | técnica |
| C-10 | ¿`OD-21…OD-25` ganan fichero en `specs/remediation/`? | Sí: fichero índice breve que enlaza su hogar canónico en `audit/ga-*` (sin duplicar contenido), y se actualiza `INDEX.md`. | `GA-GOV-03_FINDING.md §2.6` | técnica |

Sin decisiones abiertas que bloqueen el núcleo. C-03 solo escala si el propietario quiere **endurecer** la política de CI (opcional; el supuesto por defecto preserva la invariante de despliegue).
