# GA-REM-013 — QUALITY GATES DE CI (SIN MODIFICAR EL DESPLIEGUE)

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-013` · **Tipo** `PROCESS SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P1** · **Estado** `SPEC_READY` |
| **Dependencias** | `GA-REM-001` · `GA-REM-014` (para el gate de backend) |
| **Hallazgos** | P0-12 · `GA-TD-010` (**parcialmente `OUT_OF_SCOPE`**) · `GA-TD-032` · `GA-TD-044` |
| **Revalidado** | 2026-09-03 — `backend-ci.yml:8` y `frontend-ci.yml:11` solo `pull_request`; 0 merges en 171 commits |

> ## ⚠ RESTRICCIÓN VINCULANTE DE ESTA SPEC
> ```
> DEPLOYMENT AUTOMÁTICO = KNOWN_ACCEPTED_RISK = OUT_OF_SCOPE = NO MODIFICAR
> ```
> Esta spec **no puede** —ni directamente ni por vía indirecta— modificar `docker-push-backend.yml`, `docker-push-frontend.yml`, `docker-build-push.yml`, el servicio `watchtower`, `pull_policy`, la etiqueta `:latest` ni los *triggers* de despliegue. **AC07 lo verifica explícitamente.**

## Problema
Los workflows de calidad existen, están razonablemente escritos y **nunca se han ejecutado**: se disparan solo en `pull_request` y el repositorio tiene 0 pull requests en 171 commits. Además, si se ejecutaran hoy fallarían por causas propias.

## Evidencia
| Ítem | Detalle |
|---|---|
| `backend-ci.yml:8-12` | `on: pull_request` |
| `frontend-ci.yml:11-15` | `on: pull_request` |
| `git log --merges` | **0** |
| Job de lint fallaría | `npm run lint` = `eslint .` sin `--max-warnings`; hoy 5 errores → exit 1 |
| Job de backend fallaría | levanta Postgres vacío **sin migraciones ni seeds**; la fixture `auth_headers` exige login 200 |
| Test roto | `tests/test_operations.py:19` afirma 24 tipos de evento; hay **25** |
| Auditorías no bloqueantes | `pip-audit … \|\| true` y `npm audit … \|\| true` |
| Consecuencias observadas | `fcb57a7` corrigió **31 errores de TypeScript** que estaban en `main` |

## Comportamiento actual
No existe ninguna señal automática de calidad sobre el código que se integra.

## Comportamiento esperado
Existe una señal de calidad **visible y ejecutada** sobre cada integración, aunque —por la restricción anterior— esa señal **no pueda impedir el despliegue**.

## Alcance
1. Ejecutar los workflows de calidad también en `push` a `main` (esto **no** es el pipeline de despliegue: son workflows distintos).
2. Reparar los jobs para que puedan pasar: lint sin errores, backend con migraciones y seeds (`GA-REM-014`), test de tipos de evento corregido.
3. Añadir el job de contract testing que produce `GA-REM-011`.
4. Publicar un informe de estado de calidad visible.
5. Quality gates ejecutables **localmente** antes del push, para que la disciplina no dependa del CI.
6. Documentar de forma prominente la limitación aceptada.

## Fuera de alcance — reiterado
Cambiar el mecanismo de despliegue por cualquier vía · condicionar la publicación de imágenes al resultado de los tests · bloquear el push directo a `main` **por motivo de despliegue** · retirar Watchtower · eliminar `:latest`.

## KNOWN_ACCEPTED_LIMITATION
```
Un quality gate en verde o en rojo NO impide que la imagen se publique
ni que Watchtower la despliegue en producción.
La señal es informativa, no bloqueante.
Decisión del propietario. No se corrige en este programa.
```
Esta limitación debe quedar escrita en el propio workflow, en el informe de estado y en la constitución (`EX-01`, ya registrado).

## Compensación autorizada
Dado que la puerta de despliegue no existe, la disciplina previa al push adquiere carácter crítico:
- comando único local que reproduce el CI completo (`make verify` o equivalente);
- documentación de que ejecutarlo **antes** de cada push es obligación de proceso (Art. 8 y 12 de la constitución);
- informe de estado que haga visible de inmediato una integración en rojo.

## Backend / Frontend afectados
Ninguno funcionalmente. Solo configuración de CI y, opcionalmente, el `Makefile` (que además está roto: `db-seed` apunta a `app.seeds`, inexistente; `ruff` y `mypy` no están instalados).

## Base de datos afectada
Ninguna.

## Edge cases
| Caso | Comportamiento exigido |
|---|---|
| Un push rompe el lint | el workflow falla y es visible; **la imagen se publica igualmente** (limitación aceptada) |
| El job de backend no dispone de base de datos | falla con mensaje claro; no se marca en verde falsamente |
| Un aviso de ESLint nuevo | los avisos no bloquean; los errores sí |
| Vulnerabilidad de dependencia detectada | decisión: informar o bloquear — documentar; hoy `|| true` la oculta |

## Acceptance Criteria

**AC01 — Los quality gates se ejecutan en cada push**
```
Given un push a main que toca backend/ o frontend/
When  se consultan las ejecuciones de GitHub Actions
Then  los workflows de calidad se han ejecutado
```
**AC02 — El gate de lint pasa**
```
Given el código en su estado actual
When  se ejecuta el job de lint
Then  termina en verde
And   no se ha conseguido rebajando reglas ni añadiendo exclusiones injustificadas
```
**AC03 — El gate de typecheck pasa**
```
When  se ejecuta el job de typecheck
Then  termina en verde
```
**AC04 — El gate de tests de frontend pasa**
```
When  se ejecuta el job de tests de frontend
Then  los 61 tests pasan
```
**AC05 — El gate de tests de backend se ejecuta de verdad**
```
Given el entorno aislado de GA-REM-014
When  se ejecuta el job de backend
Then  aplica migraciones, siembra datos y ejecuta los 76 tests
And   el resultado refleja el estado real, sin skips injustificados
```
**AC06 — La limitación está documentada**
```
Given los workflows y el informe de estado
When  se consultan
Then  declaran explícitamente que el gate no impide el despliegue
And   citan la decisión del propietario
```
**AC07 — El deployment NO ha sido modificado**
```
Given el diff completo de cierre de GA-REM-013
When  se listan los archivos modificados
Then  docker-push-backend.yml, docker-push-frontend.yml y docker-build-push.yml están intactos
And   docker-compose.yml conserva watchtower, pull_policy y la etiqueta :latest sin cambios
And   ningún workflow nuevo condiciona la publicación de imágenes
```
**AC08 — Verificación local reproducible**
```
Given un desarrollador en su máquina
When  ejecuta el comando único de verificación
Then  obtiene el mismo resultado que el CI
```

## Tests requeridos
`T-013-01` los workflows se ejecutan en push (evidencia de ejecución) · `T-013-02..05` cada job en verde · `T-013-06` script que verifica AC07 sobre el diff · `T-013-07` comando local equivalente al CI.

## Riesgos
| Riesgo | Mitigación |
|---|---|
| Ejecutar CI en push se interpreta como intento de bloquear el despliegue | AC07 lo verifica; los workflows de calidad y los de despliegue son archivos distintos y permanecen desacoplados |
| Reparar el lint tentando a rebajar reglas | AC02 lo prohíbe expresamente |
| El gate en rojo se normaliza y se ignora | informe de estado visible; Art. 10 de la constitución |

## Rollback lógico
Reversible por commit. Solo configuración de CI.

## Definition of Done
- [ ] AC01–AC08 verificados · [ ] **AC07 confirma deployment intacto** · [ ] Limitación documentada en workflows, informe y constitución · [ ] Certification report
