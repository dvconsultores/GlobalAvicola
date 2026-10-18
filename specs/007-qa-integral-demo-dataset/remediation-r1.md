# Remediation R1 — SPEC 007 · dataset QA sintético `QA-DEMO-V1`

| Campo | Valor |
|---|---|
| SPEC | 007 — dataset QA sintético (`QA-DEMO-V1`) |
| Ronda | **R1** (revisión independiente + remediación) |
| Fecha | 2026-10-18 |
| Baseline certificado | `2510653` (CLOSE: IMPL `9a5d11a` · CERT `b7942c7` · REMOTE_SHA_MATCH PASS) |
| Base de gobierno | `01ea51a` (GOV: ejecutor MCP `deepseek-executor`, `CLAUDE.md` §1) |
| Rama | `main` (sin rama nueva, sin push en esta ronda) |
| Alcance de esta ronda | solo `backend/seeds/qa_integral_*.py`, `backend/tests/test_qa_integral_dataset.py`, `docs/` (manual + DOCX), `backend/scripts/qa_dataset_isolated_cycle.sh` y documentación. Sin cambios en código de la aplicación, sin migraciones, sin llamadas SAP |

## Origen

Revisión **independiente de solo lectura** del entregable certificado, ejecutada por un ejecutor distinto del
que implementó (DeepSeek, orquestado por Claude), en dos partes acotadas. Los hallazgos aceptados se corrigieron
en la ronda **R1**; los no aceptados se registran abajo con su motivo. Detalle del método y de la evidencia en
`audit/qa-integral-dataset/13_INDEPENDENT_REVIEW_AND_REMEDIATION.md`.

## Hallazgos y decisiones

| # | Severidad | Archivo | Hallazgo | Decisión | Corrección |
|---|---|---|---|---|---|
| H01 | MAYOR | `backend/seeds/qa_integral_dataset.py` | `exigir_entorno_seguro` razonaba con **lista negra**: cualquier alias de entorno nuevo pasaba la guarda por omisión | ADOPTADO | `ENTORNOS_PERMITIDOS = {development, dev, test, qa, uat, local}` (lista blanca) + `ENTORNOS_VETADOS = ("prod", "pre", "stag", "live")` como vetos por substring; lo no listado ⇒ `ABORTADO` |
| H02 | MAYOR | `qa_integral_dataset.py` (`credenciales`) | escribía el archivo de credenciales y **después** hacía `chmod 0600` (ventana con permisos laxos), seguía enlaces simbólicos y no validaba el contenido | ADOPTADO | `os.open(..., O_NOFOLLOW)` con `0600` atómico; aborta si la ruta pertenece a otro usuario; valida que sea un JSON `dict[str, str]` no vacío; devuelve siempre el dict filtrado por los usuarios pedidos |
| H03 | MAYOR | `qa_integral_dataset.py` (`limpiar` / CLI) | `--force-unmarked` era un booleano: autorizaba en bloque proceder con datos no marcados sin decir sobre qué empresa | ADOPTADO | ahora exige el `tax_id` exacto de una empresa QA (`--force-unmarked <tax_id>`); si no coincide ⇒ `AMBIGUOUS_QA_DATA` y 0 borrados |
| H04 | MAYOR | `docs/MANUAL_QA_PRUEBA_INTEGRAL_GLOBAL_AVICOLA.md` | el guion pedía cargar huevos en «QA Incubadora A4», que está **inactiva** ⇒ el paso principal fallaba | ADOPTADO | carga sobre «QA Incubadora A1» (115 200 de capacidad) y fila nueva de prueba negativa usando A4 (inactiva) |
| H05 | MENOR | `qa_integral_dataset.py` | fallback `GA_QA_SEED_CONFIRM_TARGET`: una variable de entorno podía autorizar una escritura | ADOPTADO | eliminado; toda escritura exige `--confirm-target` por CLI (el mensaje de abort lo dice explícitamente) |
| H06 | MENOR | `qa_integral_dataset.py` (`destino_configurado`) | parseaba el DSN a mano y podía acabar imprimiendo usuario/clave | ADOPTADO | `sqlalchemy.engine.make_url`: se devuelven solo `host` y `database` |
| H07 | MENOR | `qa_integral_dataset.py` (`main`) | combinaciones de flags incoherentes quedaban aceptadas | ADOPTADO | validación en `main()`: `--force-unmarked` solo con `--cleanup`; `--reset-passwords`/`--fixtures-dir`/`--manifest`/`--run-id`/`--credentials-file` solo con `--apply` |
| H08 | MENOR | `qa_integral_dataset.py` (`limpiar`) | condiciones del plan demasiado estrechas: `audit_logs` y `user_business_units` solo por una columna; `hatchery_openings` solo por lote; fail-closed limitado a usuarios/lotes/referencias SAP | ADOPTADO | `audit_logs` por `company_id` **OR** `user_id`; `user_business_units` por `user_id` **OR** `company_business_unit_id`; pasos complementarios `hatchery_openings(planta)` y `hatchery_openings(opening)`; fail-closed ampliado a granjas (código/nombre `QA`) y a batches de cutover (`source_system=QA_DEMO_V1`) |
| H09 | MENOR (decisión) | `qa_integral_dataset.py` (`limpiar`) | se propuso añadir `roles`/`permissions` al plan de limpieza | NO ADOPTADO (parcial) | `roles`, `permissions`, `productive_phases` y `business_units` son **catálogos globales** y no entran en el plan; un paso defensivo `roles` se probó y se retiró porque `permissions` referencia `roles` (documentado en `cleanup-contract.md` §1) |
| H10 | BUG MENOR | `backend/seeds/qa_integral_builders.py` | `sync_request_id` de los jobs SAP sintéticos se truncaba a 36 caracteres y colisionaba entre objetos que comparten prefijo (`purchase_order` vs `purchase_order_item`) | ADOPTADO | función pura `sync_request_id(run_id, objeto) = f"qa-{sha1(run_id:objeto)[:8]}-{objeto}"[:36]` ⇒ único por objeto |
| H11 | MENOR | `qa_integral_builders.py` | `usuarios()` no sincronizaba el perfil del usuario ya existente | ADOPTADO | la rama «existente» sincroniza `email`, `nombre`, `apellido` y `view_type` |
| H12 | MENOR | `qa_integral_builders.py` | `unidades()` no revocaba concesiones sobrantes | ADOPTADO | revoca las concesiones vivas que ya no corresponden al guion |
| H13 | MENOR | `qa_integral_builders.py` | `reversar()` y `cutover_aplicado()` re-ejecutaban a ciegas sobre estados intermedios | ADOPTADO | `reversar()` reanuda según el estado de la contrapartida (`_reanudar_reverso`); `cutover_aplicado()` reanuda por estado del batch: `draft`/`validating`/`validated` ⇒ subir+validar, `validated` ⇒ enviar, `pending_approval` ⇒ aprobar, `approved` ⇒ aplicar, `rejected` ⇒ `skipped` |
| H14 | CALIDAD | `qa_integral_dataset.py`, `qa_integral_builders.py` | imports muertos (`text`, `logging`/`log`, `EventType`), `Contexto.notas` sin uso, f-strings sin placeholders, parámetro `mort` que sombreaba la lambda, variable `hat_chick` sin uso | ADOPTADO | limpieza; además `roles_by_id` pasa a ser campo de `Contexto` |
| H15 | MAYOR (manual) | `docs/MANUAL_QA_PRUEBA_INTEGRAL_GLOBAL_AVICOLA.md` | nombres de catálogo inexistentes en el guion: «QA Inicio», «QA Asfixia», «QA Baja postura», «QA Newcastle» | ADOPTADO | corregidos a «QA Iniciador», «QA Mortalidad súbita», «QA Bajo peso», «QA Vacuna Newcastle» |
| H16 | MENOR (manual) | manual | frase de «25 lotes» ambigua; fila BR-18 contradictoria; §6 no aclaraba las OC sintéticas; faltaba «Trazabilidad Generacional» y una nota sobre el contenedor «Configuración» | ADOPTADO | 25 lotes = 23 principal (de ellos 3 cerrados) + 2 de aislamiento; BR-18 unificada en «Recepción con OC agotada ⇒ rechazado»; §6 aclara 11 OC sintéticas (5 usadas en recepciones); título «Trazabilidad Generacional»; nota del contenedor «Configuración»; DOCX regenerados con `tools/qa_docs/build_qa_docx.py` |
| H17 | REFACTOR | `qa_integral_dataset.py` (`escenarios`) | dividir `escenarios()` en funciones por cadena (GP/BR/HAT/BRO/ISO) | NO ADOPTADO | refactor grande sin valor funcional en esta ronda; se reevaluará si la función vuelve a crecer |
| H18 | — | CLI `--apply` | añadir `--no-fixtures` | NO ADOPTADO | los fixtures XLSX son entregables auditables en `audit/qa-integral-dataset/fixtures/`; quitarlos empobrece la evidencia |
| H19 | — | `limpiar` | bloquear con `SELECT … FOR UPDATE` durante el cleanup | NO ADOPTADO | el cleanup se ejecuta con el sistema en reposo (se documenta así en `cleanup-contract.md`); añadir bloqueos introduce riesgo de deadlock sin ganancia |
| H20 | — | `cat()` | usar `code` como clave de catálogo en vez del nombre | NO ADOPTADO | los nombres `QA *` son estables y legibles en la evidencia; migrar a `code` obliga a tocar todos los escenarios |
| H21 | COBERTURA | tests | test de integración `apply → limpiar → limpiar` | NO ADOPTADO (cubierto) | lo cubre el ciclo aislado `backend/scripts/qa_dataset_isolated_cycle.sh` (apply #1 → apply #2 → cleanup → apply #3) |

## Criterios de aceptación de la remediación

| AC | Criterio | Estado |
|---|---|---|
| R1-AC-01 | `test_qa_integral_dataset.py` crece de 16 a **25 pruebas** (27 con `test_seed_email_domains.py`) y **no se elimina ni se relaja ninguna** | PASS — `27 passed` |
| R1-AC-02 | guarda de entorno por **lista blanca** verificada con 7 entornos fuera de lista (`produccion`, `prd`, `live`, `stg`, `staging2`, `pre-eu`, `desconocido`) | PASS — `test_entorno_fuera_de_allowlist_aborta[×7]` |
| R1-AC-03 | ninguna escritura autorizada por variable de entorno: el test de `confirm-target` la fija a la base correcta y **aun así** aborta | PASS — `test_escritura_sin_confirm_target_aborta` |
| R1-AC-04 | la guarda de cobertura FK del cleanup lee el plan con `ast` (independiente del formato) y exige los pasos `HatcheryOpening`, `UserBusinessUnit` y `AuditLog` | PASS — `test_cleanup_cubre_toda_tabla_que_referencia_a_las_que_borra` |
| R1-AC-05 | ciclo aislado verde y reproducible con el script versionado: apply #1 `CREATED=720 · EXISTING=4`; verify **22/22 PASS**; apply #2 `CREATED=0 · EXISTING=693`; cleanup sin confirmar ⇒ `ABORTADO`; dry-run `total=2449`; cleanup real `CLEANED total=2438`; baseline intacto; apply #3 `CREATED=720` y `PASS`; `ENVIRONMENT=production` ⇒ `ABORTADO` | PASS — `audit/qa-integral-dataset/evidence/06_isolated_cycle.log` |
| R1-AC-06 | regresión completa del backend sin reducción de tests | **PENDIENTE** — ver `audit/qa-integral-dataset/10_REGRESSION.md` |
| R1-AC-07 | frontend sin cambios (el seed es aditivo): no se repite la corrida | N/A |
| R1-AC-08 | 0 llamadas SAP reales, sin secretos en la evidencia, sin rama nueva | PASS |

## Estado

**REMEDIACIÓN R1: IMPLEMENTADA Y VERIFICADA EN AISLADO.** Pendiente de cierre: regresión completa del backend
post-R1 (R1-AC-06) y el commit/push de la ronda (`tasks.md` T23, T24). El estado funcional del entregable no cambia
respecto de la certificación (`QA_DATA_LOCAL_ISOLATED = CERTIFIED`, `QA_DATA_RUNTIME = BLOCKED_EXTERNAL`).
