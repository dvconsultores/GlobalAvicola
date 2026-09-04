# GA-REM-001 — GOBIERNO DE SPEC DEVELOPMENT

## Metadata

| Campo | Valor |
|---|---|
| **ID** | `GA-REM-001` |
| **Título** | Gobierno de Spec Development — ratificación de la constitución del proyecto |
| **Tipo** | `GOVERNANCE SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P0** — habilitante de todo el programa |
| **Estado** | `SPEC_READY` |
| **Dependencias** | ninguna |
| **Habilita** | GA-REM-002 … GA-REM-022 (todas) |
| **Hallazgos de auditoría relacionados** | `GA-SPD-DEBT-001` (constitución sin ratificar), `GA-SPD-DEBT-002` (prompts que ordenan desarrollo directo), `GA-SPD-DEBT-003` (sin AC verificables), `GA-SPD-DEBT-004` (auto-certificación), `GA-SPD-DEBT-009` (migraciones sin spec), `GA-SPD-DEBT-014` (numeración de reglas divergente), `GA-SPD-DEBT-015` (spec sin versionado) |
| **Fecha de creación** | 2026-09-03 |

---

## 1. Problema

El proyecto instaló GitHub Spec Kit v0.11.4, usó sus plantillas de spec, plan y tasks, y declaró en `spec.md §3` que «Spec-Driven Development» es uno de sus ocho principios rectores. Pero **nunca ratificó la constitución**, que en Spec Kit es el documento que convierte esos principios en reglas vinculantes.

Consecuencia directa y demostrada: **no existe ninguna regla escrita que se pueda invocar** para exigir spec previa, para rechazar un cambio fuera de alcance o para impedir que una spec se cierre sin evidencia. Por eso la auditoría **no pudo clasificar como incumplimiento formal** los 51 commits `fix` ni los refactores masivos: no había regla que incumplir.

## 2. Evidencia

| Evidencia | Detalle |
|---|---|
| `.specify/memory/constitution.md` | Plantilla sin rellenar. Contiene literalmente `[PRINCIPLE_1_NAME]`, `[PRINCIPLE_1_DESCRIPTION]`, `[SECTION_2_NAME]`, `[GOVERNANCE_RULES]`, `**Version**: [CONSTITUTION_VERSION] \| **Ratified**: [RATIFICATION_DATE]` |
| `.specify/init-options.json` | `{"ai":"copilot","speckit_version":"0.11.4","feature_numbering":"sequential"}` — el marco está instalado y configurado |
| `.github/copilot-instructions.md` | 3 líneas genéricas del propio Spec Kit; no añade reglas de proyecto |
| `CLAUDE.md` / `AGENTS.md` | **no existen** en el repositorio |
| `specs/global-avicola/spec.md §3` | principio 8: «Spec-Driven Development. Especificar → Planificar → Tareas → Implementar» — declarativo, sin fuerza normativa |
| `specs/global-avicola/spec.md §8` | 15 AC de MVP, todos marcados `✅` **en el propio documento**, ninguno con test asociado |
| `prompt-arquitectura-navegacion.md`, `prompt-rediseno-flujo-web-mobile.md`, `prompt-refinamiento-navegacion.md` | 3 de 4 prompts ordenan cambios de producto sin exigir spec previa |
| Historial Git | 171 commits, 0 PR, 0 merge; 9 de 21 migraciones sin spec; 24 commits contra una prohibición escrita (`spec.md §6.3`, dark mode) |

## 3. Comportamiento actual

```
NECESIDAD → PROMPT → CÓDIGO → (a veces) DOCUMENTO → AUTO-CERTIFICACIÓN
```

- La spec se escribe antes, después o en el mismo commit que el código, sin regla que lo determine.
- Una spec se «cierra» cuando el mismo agente que implementó emite un informe declarándola cerrada.
- Los cambios de esquema, los refactores y las reglas de negocio nuevas no requieren autorización documental.
- No hay definición de «terminado».

## 4. Comportamiento esperado

```
NECESIDAD → REQUERIMIENTO → SPEC → REVIEW → AC → TASKS
          → IMPLEMENTACIÓN → TEST → VALIDACIÓN → CIERRE
```

Con una constitución ratificada, versionada y fechada que:
- define qué cambios exigen spec y cuáles no (evitando burocracia en lo trivial);
- fija la estructura mínima de una spec y de sus AC;
- fija la Definition of Done;
- prohíbe la auto-certificación;
- regula retro-specs, bugfix, refactor, migraciones, seguridad, integraciones y cambios de reglas de negocio;
- establece cómo se registran las desviaciones en lugar de ocultarlas.

## 5. Alcance

1. Redactar y ratificar `.specify/memory/constitution.md`.
2. Definir los umbrales que separan cambio trivial de cambio que exige spec.
3. Definir la plantilla mínima de spec de remediación y de spec futura.
4. Definir el formato obligatorio de AC.
5. Definir la Definition of Done y los estados admitidos.
6. Definir la política de retro-specs (sin reescritura de historia).
7. Definir la política de desviaciones y conflictos de requerimiento.
8. Definir la trazabilidad exigida en commits.
9. Registrar el riesgo aceptado del deployment automático como excepción explícita y permanente.

## 6. Fuera de alcance

- Modificar workflows de deployment, Watchtower, `:latest` o triggers de despliegue (`OUT_OF_SCOPE` del programa).
- Bloquear el push directo a `main` **por motivo de deployment**.
- Crear retro-specs de funcionalidades existentes (eso es GA-REM-018).
- Reescribir specs históricas para aparentar cumplimiento.
- Cambiar la versión de Spec Kit o su estructura de directorios.

## 7. Reglas de negocio afectadas

Ninguna regla de negocio avícola. Esta spec regula el **proceso de ingeniería**, no el dominio.

## 8. Arquitectura afectada

Ninguna. No toca código de aplicación.

## 9. Frontend afectado

Ninguno.

## 10. Backend afectado

Ninguno.

## 11. Base de datos afectada

Ninguna. Sin migraciones.

## 12. Seguridad

Indirecta: la constitución establece que todo cambio con superficie de autenticación, autorización o datos personales exige spec y revisión, lo que habilita GA-REM-002, 003, 004 y 012.

## 13. Migraciones

Ninguna.

## 14. Compatibilidad

Total. Documento de gobierno; no altera artefactos ejecutables.

## 15. Edge cases considerados

| Caso | Regla resultante |
|---|---|
| Corrección de una errata en un texto de UI | no exige spec (cambio trivial, §Art. 3 de la constitución) |
| Hotfix de producción a las 3 de la madrugada | permitido sin spec previa, con spec retroactiva obligatoria en ≤ 24 h marcada `RETROSPECTIVE SPEC` |
| Bump de dependencia sin cambio funcional | no exige spec; exige control de regresiones |
| Bump de dependencia que cambia comportamiento | exige spec |
| Cambio de un umbral de negocio (p. ej. 3 % de mortalidad) | **exige spec** — es una regla de negocio |
| Refactor puramente interno sin cambio de comportamiento observable | exige nota de refactor en la spec vigente, no spec nueva |
| Añadir un índice de base de datos | exige migración con docstring que cite la GA-REM; no exige spec propia |
| Añadir una columna | **exige spec** |
| El equipo descubre que la spec está equivocada a mitad de implementación | se detiene, se actualiza la spec, se re-aprueban los AC, se continúa. Nunca se implementa contra la spec en silencio |

## 16. Acceptance Criteria

Todos verificables por inspección del artefacto resultante.

**AC01 — La constitución está ratificada**
```
Given  el repositorio en el commit de cierre de GA-REM-001
When   se inspecciona .specify/memory/constitution.md
Then   no contiene ningún marcador de plantilla con la forma [MAYÚSCULAS_CON_GUIONES]
And    contiene un número de versión semántico concreto
And    contiene una fecha de ratificación concreta
```

**AC02 — Los 20 puntos exigidos están cubiertos**
```
Given  la constitución ratificada
When   se contrasta contra la lista de 20 puntos del encargo (§11 del prompt maestro)
Then   cada uno de los 20 puntos tiene un artículo o sección que lo regula explícitamente
```

**AC03 — La regla principal es inequívoca**
```
Given  la constitución ratificada
When   se busca la regla de desarrollo
Then   declara literalmente "NO SPEC = NO DEVELOPMENT"
And    enumera de forma cerrada las excepciones válidas
```

**AC04 — Los cambios triviales están exentos**
```
Given  la constitución ratificada
When   un desarrollador consulta si un cambio requiere spec
Then   existe un criterio objetivo y comprobable que separa trivial de no trivial
And    ese criterio no exige spec para cambios sin impacto funcional, de datos, de seguridad ni de contrato
```

**AC05 — Los AC tienen formato obligatorio**
```
Given  la constitución ratificada
When   se consulta la sección de Acceptance Criteria
Then   exige formato Given/When/Then o equivalente verificable
And    prohíbe expresamente criterios no verificables del tipo "el sistema debe funcionar correctamente"
```

**AC06 — La auto-certificación está prohibida**
```
Given  la constitución ratificada
When   se consulta la sección de cierre
Then   prohíbe que el mismo agente o hilo que implementó declare cerrada una spec
And    exige evidencia ejecutable como condición de cierre
```

**AC07 — Las retro-specs no reescriben la historia**
```
Given  la constitución ratificada
When   se consulta la política de retrospective specs
Then   obliga a marcarlas como RETROSPECTIVE SPEC
And    obliga a declarar la fecha real del código preexistente y el motivo
And    prohíbe presentarlas como si hubieran existido antes
```

**AC08 — El riesgo aceptado queda registrado**
```
Given  la constitución ratificada
When   se consulta la sección de excepciones y riesgos aceptados
Then   registra el deployment automático como KNOWN_ACCEPTED_RISK / OUT_OF_SCOPE
And    registra la limitación derivada: un quality gate no puede impedir el despliegue
And    no propone corregirlo
```

**AC09 — Las migraciones quedan trazadas**
```
Given  la constitución ratificada
When   se consulta la política de cambios de esquema
Then   exige que el docstring de cada migración cite la GA-REM o spec que la autoriza
And    prohíbe modificar la estructura de la base de datos fuera de una migración Alembic
```

**AC10 — La Definition of Done es única y verificable**
```
Given  la constitución ratificada
When   se consulta la Definition of Done
Then   enumera condiciones comprobables (spec, AC, tasks, implementación, test, evidencia, regresiones)
And    define los estados admitidos de una unidad de trabajo
```

**AC11 — El documento es localizable y referenciado**
```
Given  el repositorio tras el cierre de GA-REM-001
When   se abre specs/remediation/GLOBAL_AVICOLA_REMEDIATION_PROGRAM.md
Then   referencia la constitución como norma aplicable al programa
```

**AC12 — No se ha tocado código de aplicación**
```
Given  el diff del commit de cierre de GA-REM-001
When   se listan los archivos modificados
Then   ninguno pertenece a backend/app/, frontend/src/, alembic/versions/ ni .github/workflows/
```

## 17. Tests requeridos

Esta spec no produce código ejecutable; su verificación es documental y automatizable por inspección.

| ID | Verificación | Método |
|---|---|---|
| `T-001` | AC01 — sin marcadores de plantilla | `grep -cE '\[[A-Z_]+\]' .specify/memory/constitution.md` → `0` |
| `T-002` | AC01 — versión y fecha presentes | `grep -E '\*\*Versión\*\*: [0-9]+\.[0-9]+\.[0-9]+' y `Ratificada: 2026-` |
| `T-003` | AC03 — regla principal literal | `grep -c "NO SPEC = NO DEVELOPMENT"` → `≥1` |
| `T-004` | AC08 — riesgo aceptado registrado | `grep -c "KNOWN_ACCEPTED_RISK"` → `≥1` |
| `T-005` | AC02 — cobertura de los 20 puntos | checklist de contraste, adjunta al certification report |
| `T-006` | AC12 — sin código tocado | `git show --name-only <commit>` sin rutas de aplicación |

## 18. Riesgos

| Riesgo | Mitigación |
|---|---|
| La constitución se vuelve burocrática y el equipo la ignora | AC04 exige exención explícita para cambios triviales; los artículos son cortos y accionables |
| La constitución contradice la decisión del propietario sobre deployment | AC08 obliga a registrarla como excepción permanente, no como incumplimiento |
| La constitución se convierte en otro documento muerto | GA-REM-013 publica un informe de cumplimiento; el `MASTER_REMEDIATION_MATRIX` la referencia en cada cierre |

## 19. Rollback lógico

Trivial: revertir el commit del documento. No hay estado persistente ni migraciones. La constitución previa era una plantilla vacía, por lo que ningún artefacto depende de ella.

## 20. Definition of Done

- [ ] `.specify/memory/constitution.md` ratificado, versionado y fechado
- [ ] AC01–AC12 verificados con evidencia
- [ ] `T-001` … `T-006` ejecutados
- [ ] Referenciada desde el programa maestro
- [ ] `GA-REM-001 — CERTIFICATION REPORT` emitido
- [ ] Ningún archivo de aplicación modificado
