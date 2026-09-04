# GA-REM-019 — REEVALUACIÓN DE DEUDA P2/P3

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-019` · **Tipo** `TECHNICAL DEBT SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P2** · **Estado** `DEFERRED` — se abre tras estabilizar P0/P1 y certificar los primeros procesos |
| **Dependencias** | Fases A–G completadas |
| **Hallazgos** | `audit/16_TECHNICAL_DEBT.md` — 21 elementos P2 y 11 P3 |

## Problema
32 elementos de deuda P2/P3 catalogados antes de las correcciones. Parte de ellos quedarán resueltos indirectamente o dejarán de ser relevantes.

## Principio
**No se asume que todos los P2/P3 siguen siendo válidos.** Se reevalúan y reclasifican: `STILL_VALID` · `RESOLVED_INDIRECTLY` · `OBSOLETE` · `DEFERRED` · `ACCEPTED`.

## Elementos con reevaluación previsible
| ID | Elemento | Reevaluación esperada |
|---|---|---|
| `GA-TD-031` | listados sin total | `RESOLVED_INDIRECTLY` por `GA-REM-011` |
| `GA-TD-049` | `ReportsPage` con ID numérico de lote | `RESOLVED_INDIRECTLY` por `GA-REM-011` |
| `GA-TD-034` | `mock_adapter.py` no compila | `RESOLVED_INDIRECTLY` por `GA-REM-010` |
| `GA-TD-035` | tests E2E de la raíz sin runner | `RESOLVED_INDIRECTLY` por `GA-REM-016` |
| `GA-TD-027` | `client_max_body_size` | `RESOLVED_INDIRECTLY` por `GA-REM-009` |
| `GA-TD-044` | test de 24 tipos de evento | `RESOLVED_INDIRECTLY` por `GA-REM-015` |
| `GA-TD-020` | capa `services/hooks` muerta | depende de la decisión de `GA-REM-011`; probablemente `STILL_VALID` parcial |
| `GA-TD-028` | tabla `reversals` / BR-16 | `STILL_VALID` — requiere spec propia |
| `GA-TD-024` | aprobación multinivel sin enforcement | `STILL_VALID` — **candidata a spec propia**, es un diferenciador declarado del producto |
| `GA-TD-029` | activación manual de lotes sin UI | `STILL_VALID` — **crítica para la implantación** de lotes en curso |
| `GA-TD-030` | N+1 por 8 relaciones `selectin` | `STILL_VALID` |
| `GA-TD-033` | `OperationFormPage` de 1 973 LOC | `STILL_VALID` |
| `GA-TD-039` | observabilidad nula | **P1, no P2** — candidata a adelantarse |
| `GA-TD-040` | sin backups | **P1, no P2** — candidata a adelantarse |
| `GA-TD-036/037` | código muerto de dark mode y componentes sin uso | `STILL_VALID`, complejidad XS |
| `GA-TD-046` | sin `CHECK` constraints | `STILL_VALID` |
| `GA-TD-047/048` | textos fijos y emojis en el backend | `STILL_VALID` |
| `GA-TD-051/052/053` | Makefile roto, configuración duplicada, flag inerte | `STILL_VALID`, complejidad XS |
| `GA-TD-055/056` | `egg_storage` sin lectura, estados inalcanzables | `RESOLVED_INDIRECTLY` parcial por `GA-REM-010` y `GA-REM-018` |
| `GA-TD-058` | Watchtower con socket de Docker | **`ACCEPTED`** — deriva de `EX-01`, fuera de alcance |

## Nota sobre `GA-TD-039` y `GA-TD-040`
Observabilidad y copias de seguridad están clasificadas P1 en la auditoría. Dado que el despliegue automático se mantiene (`EX-01`) y **no existe ninguna puerta que impida llegar a producción**, la capacidad de detectar y revertir un fallo productivo adquiere más importancia, no menos. Se recomienda **adelantarlas** por delante del resto de P2.

## Acceptance Criteria
**AC01** — los 32 elementos reevaluados y reclasificados con justificación.
**AC02** — los `RESOLVED_INDIRECTLY` tienen evidencia de su resolución.
**AC03** — los `STILL_VALID` tienen prioridad recalculada y, si procede, spec propia.
**AC04** — `GA-TD-058` figura como `ACCEPTED` por derivar de `EX-01`.

## Definition of Done
- [ ] AC01–AC04 verificados · [ ] `audit/16_TECHNICAL_DEBT.md` actualizado · [ ] Certification report
