# 13 · Revisión independiente y remediación R1

**Fecha:** 2026-10-18 · **Baseline revisado:** `2510653` (SPEC 007 certificada en local; IMPL `9a5d11a`, CERT `b7942c7`) · **Base de gobierno:** `01ea51a` (ejecutor MCP `deepseek-executor`) · **Rama:** `main`.

Documento de detalle de la remediación: `specs/007-qa-integral-demo-dataset/remediation-r1.md` (tabla completa de hallazgos, decisión y corrección). Aquí se registra **cómo se hizo**, qué evidencia lo respalda y qué se decidió **no** hacer.

## 1 · Método

1. **Revisión independiente de solo lectura.** La ejecutó un ejecutor distinto del que implementó (DeepSeek), orquestada por Claude. No se le autorizó escritura: solo leer el código del seed, los tests, el manual y la evidencia, y devolver hallazgos con severidad. Se hizo en **dos partes acotadas** (ver §6).
2. **Triaje por el orquestador.** Cada hallazgo se clasificó como ADOPTADO / NO ADOPTADO con motivo; los no adoptados quedan registrados con su razón (no se «olvidan»).
3. **Remediación delegada.** Los cambios se aplicaron por delegación autosuficiente, en el código del seed y de los builders, en los tests, en el manual y en la documentación de `audit/`.
4. **Verificación por el orquestador**, no por quien corrigió: tests del seed, ciclo aislado de certificación y (en curso) regresión completa del backend. La regla de la ronda fue explícita: **ningún test se relaja ni se elimina para obtener verde**.

No se revisó el runtime compartido (sigue `BLOCKED_EXTERNAL`, ver `09_RUNTIME_VERIFICATION.md`) ni se hizo ninguna llamada SAP.

## 2 · Hallazgos y correcciones (resumen)

| Severidad | Tema | Corrección aplicada | Ref. |
|---|---|---|---|
| MAYOR | guarda de entorno por lista negra | **lista blanca** `ENTORNOS_PERMITIDOS={development, dev, test, qa, uat, local}` + vetos por substring (`prod`/`pre`/`stag`/`live`) | R1-02 |
| MAYOR | archivo de credenciales | `os.open` con `O_NOFOLLOW` y `0600` atómico (sin ventana de permisos laxos), aborta si la ruta es de otro usuario, valida el JSON y devuelve el dict filtrado por usuarios | R1-03 |
| MAYOR | `--force-unmarked` booleano | exige el `tax_id` exacto de una empresa QA; si no coincide ⇒ `AMBIGUOUS_QA_DATA` | R1-04 |
| MENOR | fallback por variable de entorno | `GA_QA_SEED_CONFIRM_TARGET` eliminado: toda escritura exige `--confirm-target` por CLI | R1-05 |
| MENOR | `destino_configurado()` | usa `sqlalchemy make_url`; nunca imprime usuario ni clave | R1-06 |
| MENOR | flags incoherentes | validación de combinaciones en `main()` (`--force-unmarked` solo con `--cleanup`; `--reset-passwords`/`--fixtures-dir`/`--manifest`/`--run-id`/`--credentials-file` solo con `--apply`) | R1-07 |
| MENOR | plan de limpieza incompleto | `audit_logs` por `company_id` **OR** `user_id`; `user_business_units` por `user_id` **OR** `company_business_unit_id`; pasos `hatchery_openings(planta)` y `hatchery_openings(opening)`; fail-closed ampliado a granjas (`QA`) y a batches de cutover (`source_system=QA_DEMO_V1`) | R1-08 |
| BUG MENOR | colisión de `sync_request_id` | nueva función pura `sync_request_id(run_id, objeto) = f"qa-{sha1(run_id:objeto)[:8]}-{objeto}"[:36]` | R1-10 |
| MENOR | idempotencia parcial | `usuarios()` sincroniza `email`/`nombre`/`apellido`/`view_type`; `unidades()` revoca concesiones vivas que ya no corresponden; `reversar()` reanuda por estado de la contrapartida; `cutover_aplicado()` reanuda por estado del batch | R1-11…13 |
| CALIDAD | ruido en el código | imports muertos, `Contexto.notas`, f-strings sin placeholders, `mort` sombreando la lambda, `hat_chick` sin uso; `roles_by_id` como campo de `Contexto` | R1-14 |
| MAYOR (manual) | pasos imposibles y catálogos inexistentes | carga de huevos en «QA Incubadora A1» (A4 queda como prueba negativa por inactiva); «QA Iniciador», «QA Mortalidad súbita», «QA Bajo peso», «QA Vacuna Newcastle» | R1-04 / R1-15 |
| MENOR (manual) | incoherencias narrativas | 25 lotes = 23 principal (3 cerrados) + 2 aislamiento; BR-18 unificada; §6 con 11 OC sintéticas (5 usadas); «Trazabilidad Generacional»; nota del contenedor «Configuración»; DOCX regenerados con `tools/qa_docs/build_qa_docx.py` | R1-16 |

## 3 · Evidencia

### Tests del seed (`backend/tests/test_qa_integral_dataset.py` + `test_seed_email_domains.py`)

`27 passed, 1 warning`

16 → **25 pruebas** en el archivo del seed (+2 de `test_seed_email_domains.py` = **27 passed**). Las nuevas son
`test_entorno_fuera_de_allowlist_aborta[produccion/prd/live/stg/staging2/pre-eu/desconocido]` (×7),
`test_force_unmarked_exige_tax_id_exacto`, `test_sync_request_id_unico_por_objeto`, y la guarda de
cobertura FK del cleanup pasa a leer el plan con `ast` (`_modelos_del_plan`), que además exige que estén los pasos
`HatcheryOpening`, `UserBusinessUnit` y `AuditLog`.

### Ciclo aislado (`backend/scripts/qa_dataset_isolated_cycle.sh` → `evidence/06_isolated_cycle.log`)

| Paso | Resultado |
|---|---|
| apply #1 | `CREATED=720 · EXISTING=4` (fases globales) en 14 s |
| verify #1 | 22/22 `PASS` · `QA_DATA_VERIFY = PASS` |
| apply #2 | `CREATED=0 · EXISTING=693` ⇒ idempotente |
| cleanup sin `--confirm-target` | `ABORTADO: la escritura exige --confirm-target 'global_avicola_test' en la línea de comandos. No hay variable de entorno ni override silencioso.` |
| cleanup `--dry-run` | `total=2449`, `ambiguous=[]` |
| cleanup real | `CLEANED total=2438` |
| baseline tras el cleanup | intacto: `companies=2 · roles=7 · admin=1 · productive_phases=4 · business_units=4 · permissions=64` |
| apply #3 | `CREATED=720` · verify `PASS` |
| `ENVIRONMENT=production --inventory` | `ABORTADO` |

### Regresión completa del backend

**PENDIENTE — ver `10_REGRESSION.md`.** Frontend sin cambios: no se repite (`npx vitest run` 542/542 y `tsc`/`build` de la certificación siguen siendo válidos porque la app no se tocó).

## 4 · Hallazgos no adoptados (con motivo)

| Hallazgo | Decisión | Motivo |
|---|---|---|
| Dividir `escenarios()` en funciones por cadena (GP/BR/HAT/BRO/ISO) | NO ADOPTADO | refactor grande sin valor funcional en esta ronda |
| `--no-fixtures` en `--apply` | NO ADOPTADO | los fixtures XLSX son entregables auditables en `audit/qa-integral-dataset/fixtures/` |
| `SELECT … FOR UPDATE` en el cleanup | NO ADOPTADO | el cleanup se ejecuta con el sistema en reposo (documentado); el bloqueo introduce riesgo de deadlock sin ganancia |
| Usar `code` como clave en `cat()` | NO ADOPTADO | los nombres `QA *` son estables y legibles en la evidencia |
| Test de integración `apply → limpiar → limpiar` | NO ADOPTADO (cubierto) | lo cubre el ciclo aislado `scripts/qa_dataset_isolated_cycle.sh` |
| Añadir `roles`/`permissions` al plan de limpieza | NO ADOPTADO | catálogos globales; `permissions` referencia `roles`, el paso defensivo se probó y se retiró (`cleanup-contract.md` §1) |

## 5 · Impacto en la evidencia previa

- `05_TESTS.md`: 18 → **27 passed** con las filas de los tests nuevos.
- `06_SEED_EXECUTION_ISOLATED.md`: números de la corrida nueva (720/4, dry-run 2449, cleanup 2438) y ciclo ejecutado ya por el **script versionado**.
- `QA_DATA_MANIFEST.md`: contador de la corrida (`CREATED=720`); el inventario del dataset no cambia.
- `04_IMPLEMENTATION.md`, `cleanup-contract.md`, `tasks.md`, `09_RUNTIME_VERIFICATION.md`: CLI y guardas al día.
- `07_CLEANUP_PROOF.md` conserva los números de la primera corrida (719 / 2447): el ciclo nuevo no lo invalida, pero unificarlos es deuda de documentación menor (ver §6).

## 6 · Lecciones del ejecutor

- **Una delegación de 40 turnos no alcanza** para revisar todo el entregable de una vez: la revisión completa en una sola delegación terminó en `INCOMPLETE`. Dividirla en **dos revisiones acotadas** (guardas/seguridad por un lado; limpieza/manual/testing por otro) sí produjo hallazgos completos y verificables.
- **Presupuesto de turnos visible**: el servidor del ejecutor inyecta ahora un aviso al **75 %** de los turnos para que el ejecutor cierre y reporte en vez de morir sin salida.
- **Revisar ≠ corregir**: separar la revisión (solo lectura) de la remediación (escritura) mantuvo el sesgo bajo; el orquestador verificó cada corrección con tests reales.
- **Los números de la evidencia caducan**: cualquier cambio en el seed obliga a re-ejecutar el ciclo; por eso el ciclo se convirtió en **script versionado** y no en una secuencia de comandos tecleada.
