# 17 — DEUDA DE SPEC DEVELOPMENT

Deuda **de proceso**, separada de la deuda técnica (`16_TECHNICAL_DEBT.md`). Una funcionalidad puede operar perfectamente y aun así constituir deuda metodológica.

| ID | Problema | Evidencia | Riesgo | Impacto | Prior. | Corrección |
|---|---|---|---|---|---|---|
| **GA-SPD-DEBT-001** | **La constitución del proyecto nunca fue ratificada.** `.specify/memory/constitution.md` sigue siendo la plantilla con marcadores `[PRINCIPLE_1_NAME]`, `[GOVERNANCE_RULES]`, `**Version**: [CONSTITUTION_VERSION]`. No existe ninguna regla de gobierno escrita y vinculante. | `.specify/memory/constitution.md` | no hay base formal para exigir spec previa; ninguna desviación es formalmente sancionable | metodológico estructural | **P0** | ejecutar `/speckit.constitution` y ratificar principios: NO SPEC = NO DEVELOPMENT, excepciones explícitas, criterios de cierre |
| **GA-SPD-DEBT-002** | **Prompts que ordenan desarrollo directo.** 3 de los 4 prompts versionados piden cambios de producto (navegación, jerarquía de menús, flujo del operador) sin exigir actualización previa de la spec. | `prompt-arquitectura-navegacion.md`, `prompt-rediseno-flujo-web-mobile.md`, `prompt-refinamiento-navegacion.md` | el patrón `SOLICITUD → CÓDIGO → DOC` queda institucionalizado | 20+ commits de navegación sin spec | **P1** | plantilla de prompt que obligue a citar la spec/AC que autoriza el cambio |
| **GA-SPD-DEBT-003** | **Ninguna spec tiene criterios de aceptación verificables por funcionalidad.** Los 15 AC de `spec.md §8` son globales, están marcados `✅` en el propio documento y ninguno referencia un test. | `spec.md §8` | imposible cerrar una spec con evidencia | `SPEC_PROCESS_DEBT` general | **P0** | AC por feature con `Given/When/Then` y test nombrado |
| **GA-SPD-DEBT-004** | **Auto-certificación sin verificación independiente.** 6 documentos declaran "APROBADO", "96/100", "CERTIFICADO", "listo para UAT"; fueron generados por el mismo agente y en el mismo hilo que produjo el código. | `e0eed25`, `a84eb2d`, `CERTIFICACION_FUNCIONAL.md`, `AUDITORIA_FUNCIONAL_E2E.md` | falsa confianza; decisiones de negocio sobre estado irreal | 8 bloqueadores P0 vivos bajo declaraciones de "completo" | **P0** | prohibir el cierre por auto-informe; exigir test verde en CI + revisión externa |
| **GA-SPD-DEBT-005** | **Ninguna puerta de calidad entre commit y producción.** CI configurado solo para `pull_request`; **0 PRs y 0 merges en 171 commits**; `push` a `main` publica imagen y Watchtower la despliega en 60 s. | `.github/workflows/*-ci.yml:8-12`; `git log --merges` → vacío; commit `9004f3a` | cualquier error llega a producción sin filtro | 9 commits de "fix build" son consecuencia directa | **P0** | CI en `push` + rama protegida + despliegue por tag aprobado |
| **GA-SPD-DEBT-006** | **12 funcionalidades sin ninguna spec**, cinco de ellas visibles para el usuario (alertas, evidencias, SearchSelect, Telegram, selector de compañía). | §3.3 de `05_SPEC_DEVELOPMENT_COMPLIANCE.md` | producto no gobernado; nadie sabe qué debe hacer el sistema | Out-of-Spec Rate 33 % | **P1** | retro-specs justificadas y fechadas (§108) |
| **GA-SPD-DEBT-007** | **Violación explícita de una regla escrita.** `spec.md §6.3` prohíbe el modo oscuro; se implementó en 24 commits y se revirtió sin actualizar la spec en ningún momento. | `git log -i --grep="dark mode\|modo oscuro"` → 24 | ~4 días de trabajo perdidos; restos de código | scope creep no justificado | **P1** | registrar la lección; exigir cambio de spec antes de contradecirla |
| **GA-SPD-DEBT-008** | **Design system sustituido sin decisión documentada.** La paleta obligatoria (`#2563EB`/`#1E3A5F`) se cambió por una paleta teal copiada de "atenea-front". La spec sigue diciendo lo contrario. | `tailwind.config.ts:12-24`; `index.css:1-3`; commit `a1d7843` | la identidad visual del producto no está gobernada | `CRITICAL_DRIFT` | **P1** | ADR de cambio de identidad + actualizar `docs/11` y `spec.md §6.3` |
| **GA-SPD-DEBT-009** | **9 de 21 migraciones (43 %) cambian el esquema sin requisito ni spec.** Una relaja una restricción de integridad (`operational_events.lot_id` → nullable). | `12_DATABASE_MODEL.md §7` | cambios de modelo no gobernados | `UNTRACED_SCHEMA_CHANGE` ×9 | **P1** | toda migración debe citar la spec/AC en su docstring |
| **GA-SPD-DEBT-010** | **Contratos de API y modelo de datos abandonados.** `specs/.../contracts/api-contract.md` y `docs/06` describen una fracción de 167 endpoints; `data-model.md` no refleja 47 tablas. | comparación con el esquema OpenAPI y `Base.metadata` | los contratos no sirven para nada | `CRITICAL_DRIFT` | **P1** | generar `openapi.json` en CI y versionarlo; regenerar el ERD |
| **GA-SPD-DEBT-011** | **Documentos que declaran estados falsos.** `README.md` afirma "el proyecto está en fase de especificación, no se ha iniciado codificación funcional" con el sistema desplegado; `CERTIFICACION_FUNCIONAL.md` lista rutas inexistentes; `IMPLEMENTATION_COMPLETE.md` presenta como entregable una funcionalidad ya eliminada. | `README.md:107`; `CERTIFICACION_FUNCIONAL.md §2`; `IMPLEMENTATION_COMPLETE.md` | desorientación de cualquier incorporación y de la dirección | docs vs realidad | **P2** | archivar los informes históricos en `docs/history/` y reescribir el README |
| **GA-SPD-DEBT-012** | **Tareas de la Fase 9 (producción) nunca cerradas ni actualizadas.** Las 7 casillas siguen sin marcar; T-085 (`RealSapAdapter`, "bloquea prod") sigue pendiente y sin embargo el flag SAP se activó en producción. | `tasks.md` "Production Activation Checklist"; `bfccdfb` | se saltó el propio checklist del proyecto | riesgo operativo | **P1** | reactivar la Fase 9 como puerta obligatoria |
| **GA-SPD-DEBT-013** | **Referencias documentales rotas.** `docs/17-production-checklist.md` (citado por la spec y por las tareas) y `docs/18-production-runbook.md` (entregable de T-090) no existen; falta también `docs/14`. | `ls docs/` | el checklist de producción que todo el proyecto cita no existe | proceso | **P2** | crear ambos o retirar las referencias |
| **GA-SPD-DEBT-014** | **Numeración de reglas divergente entre spec y código.** El código llama `BR-10` a la regla que la spec numera `BR-11`, y añade BR-17/18/19 inexistentes en la spec. Los mensajes al usuario citan identificadores equivocados. | `validators.py:227,243,296,313,332` vs `spec.md §5` | imposible auditar el cumplimiento por identificador | trazabilidad | **P2** | tabla única de reglas y uso del mismo identificador en código, spec y mensajes |
| **GA-SPD-DEBT-015** | **Especificación con edición en caliente sin control de versiones semántico.** `spec.md` pasó de 252 a 478 líneas en 5 ediciones, con dos secciones numeradas `4.9` y sin registro de cambios. | historial de `spec.md` | no se sabe qué versión gobernó qué implementación | baseline confuso | **P2** | encabezado con versión + changelog al pie de cada spec |
| **GA-SPD-DEBT-016** | **Tests sin trazabilidad a AC.** Solo `test_full_workflow_audit.py` nombra flujos F1–F10 alineados con los AC, y no se ejecuta. Los 4 archivos de test frontend no cubren ningún AC de negocio; 2 de ellos prueban componentes muertos. | `15_TESTING_STATUS.md` | los AC no son verificables | `PARTIAL_TRACEABILITY` | **P1** | nombrar cada test con el AC que verifica y publicar la matriz |

## Resumen

```
Deuda Spec Development total ....... 16 elementos
   P0 ....  4
   P1 ....  7
   P2 ....  5
```

## Cambios que produjeron regresiones (§95) — con evidencia

Solo se reportan cadenas demostrables.

| Cadena | Evidencia |
|---|---|
| **Alertas → mortalidad rota.** `bdb5cde` (2026-06-27 03:12, "Phase 3.2 auto alerts backend") introduce `_check_and_create_alerts`, que llama a una función no importada y con aridad incorrecta. Desde ese commit, **registrar mortalidad devuelve 500**. La funcionalidad de alertas no estaba especificada; el cambio no tenía spec ni test, y la regresión sobrevivió 3 meses. | `operations/service.py:242` |
| **Fusión de `egg_classification` → regresión de spec.** `f379b7e` (2026-06-29 05:27) elimina un tipo de operación que la spec exige en tres etapas. El enum del backend lo conserva; el catálogo del frontend no. Un lote histórico con eventos `egg_classification` ya no tiene pantalla que los muestre en el flujo. | `processCatalog.ts:190-215` vs `spec.md §4.4/§4.6/§4.7` |
| **Rediseño de paleta → contraste.** `a1d7843` (paleta teal) va seguido de `861280f` "fix(contrast): corregir texto blanco sobre fondos claros" y `e1209a1` "fix(ui): contraste estricto claro/oscuro". El cambio de identidad no especificado generó al menos dos commits de corrección de accesibilidad. | historial |
| **Campaña de dark mode → 15 commits de corrección y reversión total.** `fe4580a` … `8940d9e`. | historial |
| **`fcb57a7` "build local — 31 errores TypeScript corregidos"** (2026-06-29 21:25) demuestra que 31 errores de compilación estuvieron en `main` sin detectarse: consecuencia directa de GA-SPD-DEBT-005. | commit |

## Clasificación de recuperación (§100)

| Código sin spec | Acción recomendada |
|---|---|
| Evidencias adjuntas, motor de alertas, `SearchSelect`, inspección por galpón, selector de compañía | **RETRO-SPEC JUSTIFICADA** — funcionalidad válida y en uso; documentar con fecha real y marca `RETROSPECTIVE SPEC` |
| Telegram Mini App + bot | **RETRO-SPEC JUSTIFICADA** — es un canal de producto: requiere spec propia con actores, alcance y autenticación |
| `egg_reception_classification`, `hatchery_purpose`, `bird_transfer` | **RETRO-SPEC JUSTIFICADA** — incorporar al catálogo canónico de operaciones y reconciliar con `egg_classification` |
| `egg_storage` | **DOCUMENTAR COMO LEGACY** o eliminar: se escribe y no se lee |
| Tabla `reversals` | **REEMPLAZAR POR NUEVA SPEC** — BR-16 necesita una spec de flujo de reverso antes de implementarse |
| `SignaturePad`, `DarkModeToggle`, `theme.store`, `SidebarSubmenu`, `mock_adapter.py`, `tests/` de la raíz | **ELIMINAR DEL SCOPE** — código muerto sin requisito |
| Paleta teal / identidad visual | **REEMPLAZAR POR NUEVA SPEC** — ADR + actualización de `docs/11` y `spec.md §6.3` |
