# GA-REM-018 — RECUPERACIÓN DE TRAZABILIDAD SPEC DEVELOPMENT

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-018` · **Tipo** `METHODOLOGY SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P1** · **Estado** `SPEC_READY` |
| **Dependencias** | `GA-REM-001` · debe ejecutarse **después** de estabilizar las funcionalidades críticas |
| **Hallazgos** | `GA-SPD-DEBT-006, 007, 008, 010, 011, 013, 014, 015` · `audit/05` · `audit/17` |

## Problema
12 funcionalidades sin ninguna spec, 3 desviaciones out-of-spec, 7 artefactos con deriva y 6 specs cerradas sin validación. La trazabilidad `HALLAZGO → SPEC → CÓDIGO` no existe para la mayor parte del sistema.

## Principio rector — Art. 14 de la constitución
```
NO se reescribe la historia.
NO se retro-especifica todo por defecto.
```
Toda retro-spec se marca `RETROSPECTIVE SPEC`, declara la fecha real del código obtenida de Git y el motivo por el que no existió spec previa.

## Alcance
1. Clasificar cada funcionalidad existente: `SPEC_COMPLIANT` · `SPEC_PARTIAL` · `IMPLEMENTED_WITHOUT_SPEC` · `CODE_BEFORE_SPEC` · `OUT_OF_SPEC` · `SPEC_DRIFT` · `LEGACY`.
2. Para cada bloque sin spec, decidir entre: `RETROSPECTIVE_SPEC` · `LEGACY_ACCEPTED` · `DEPRECATE` · `REPLACE` · `MERGE_INTO_CURRENT_SPEC`.
3. Producir solo las retro-specs que aporten valor real.
4. Regenerar los contratos derivados (`openapi.json`, ERD) para eliminar la deriva crítica.
5. Reconciliar la numeración de reglas de negocio (Art. 22).
6. Reescribir `README.md` y archivar los informes históricos.
7. Publicar `GLOBAL_AVICOLA_BASELINE_V1_1.md`.

## Decisión preliminar por elemento
| Elemento sin spec | Decisión propuesta | Motivo |
|---|---|---|
| Evidencias adjuntas | `RETROSPECTIVE_SPEC` | en uso; el cliente exige adjuntos de incidencias |
| Motor de alertas | `RETROSPECTIVE_SPEC` | en uso; `docs/02 §3.14` lo exige parcialmente |
| `SearchSelect` (34 campos) | `MERGE_INTO_CURRENT_SPEC` | patrón de UI; pertenece al design system |
| Inspección por galpón | `RETROSPECTIVE_SPEC` | cambia el modelo de datos de inspección |
| Selector de compañía | `MERGE_INTO_CURRENT_SPEC` | multi-compañía ya está en `spec.md §2` |
| Telegram Mini App y bot | `RETROSPECTIVE_SPEC` | **canal de producto nuevo**: requiere actores, alcance y autenticación |
| `egg_reception_classification` | `MERGE_INTO_CURRENT_SPEC` vía `GA-REM-020` | pertenece a la taxonomía de operaciones |
| `hatchery_purpose` | `MERGE_INTO_CURRENT_SPEC` vía `GA-REM-020` | ídem |
| `bird_transfer` | **desbloqueado** — `RC-02` resuelto (`RR-02`, 2026-09-03) | movimiento intra-lote entre galpones, neutro en el balance del lote |
| `egg_storage` | `RETROSPECTIVE_SPEC` | **el cliente sí lo exige** («Almacenamiento de Huevos») — es `SPEC_GAP`, no scope creep |
| Tabla `reversals` | `REPLACE` | BR-16 necesita spec propia antes de implementarse |
| `SignaturePad`, `DarkModeToggle`, `theme.store`, `SidebarSubmenu`, `mock_adapter.py`, `tests/` raíz | `DEPRECATE` | código muerto sin requisito |
| Paleta teal / identidad visual | `REPLACE` | ADR de cambio de identidad + actualizar `docs/11` y `spec.md §6.3` |
| Reglas BR-17, BR-18, BR-19 | `MERGE_INTO_CURRENT_SPEC` | incorporar a la tabla única de reglas |

## Acceptance Criteria
**AC01** — cada funcionalidad existente tiene una clasificación asignada con evidencia.
**AC02** — cada bloque sin spec tiene una decisión de las cinco admitidas, justificada.
**AC03** — toda retro-spec producida está marcada `RETROSPECTIVE SPEC` con fecha real de Git y motivo.
**AC04** — ninguna spec histórica ha sido modificada para aparentar cumplimiento previo.
**AC05** — `openapi.json` y el ERD versionados coinciden con el código.
**AC06** — la tabla de reglas de negocio usa identificadores idénticos en spec, código y mensajes.
**AC07** — `README.md` describe el estado real del proyecto.
**AC08** — `GLOBAL_AVICOLA_BASELINE_V1_1.md` publicado, incluyendo `AUTO DEPLOY: KNOWN_ACCEPTED_RISK / NO CHANGE REQUESTED`.

## Definition of Done
- [ ] AC01–AC08 verificados · [ ] Baseline v1.1 publicado · [ ] Certification report
