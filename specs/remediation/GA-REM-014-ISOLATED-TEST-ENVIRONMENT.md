# GA-REM-014 — ENTORNO DE TEST BACKEND AISLADO

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-014` · **Tipo** `INFRASTRUCTURE SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P0 habilitante** — sin esto no se puede cerrar ninguna spec con AC ejecutable |
| **Estado** | `SPEC_READY` |
| **Dependencias** | `GA-REM-001` |
| **Habilita** | `GA-REM-002, 003, 005, 006, 007, 008, 011, 012, 013, 015, 016` |
| **Hallazgos** | `GA-TD-023` · P1-7 · sección §2.2 de `audit/15_TESTING_STATUS.md` |
| **Revalidado** | 2026-09-03 — `backend/.env` apunta `DATABASE_URL` a un PostgreSQL en IP pública; Docker no instalado en la máquina auditada |

## Problema
La auditoría **no pudo ejecutar los 76 tests de backend**. La única base de datos configurada es un PostgreSQL en IP pública que, por los indicios (mismo host que el dominio productivo, seeds de «pruebas en vivo»), sirve al entorno real. Los tests **escriben**: crean eventos operativos, correcciones, aprobaciones y usuarios.

Sin entorno aislado, la regla `NO VALIDATION = NO COMPLETE` bloquea el programa entero.

## Evidencia
| Ítem | Detalle |
|---|---|
| Única BD configurada | `backend/.env` → `DATABASE_URL` a IP pública |
| Los tests escriben | `tests/test_full_workflow_audit.py` crea 6 tipos de evento, correcciones y aprobaciones |
| Dependencia de datos preexistentes | `tests/test_operations.py` usa `"lot_id": 2` codificado |
| Fixture que exige login real | `tests/conftest.py:26-34` — `assert resp.status_code == 200` con `admin/admin123` |
| CI sin migraciones ni seeds | `backend-ci.yml` levanta Postgres 15 vacío y ejecuta `pytest` directamente |
| Sin guarda técnica | ningún punto del código impide ejecutar tests contra producción |

## Comportamiento actual
```
pytest → lee backend/.env → conecta a la BD de la nube → ESCRIBE
```
No hay nada que lo impida.

## Comportamiento esperado
```
crear BD desechable → alembic upgrade head → seeds de test → pytest → destruir/resetear
```
Con **guarda técnica** que rechace la ejecución si el entorno objetivo es productivo.

## Alcance
1. Definir el mecanismo de base de datos desechable **compatible con la infraestructura real disponible**. Se evalúan, en este orden: PostgreSQL local, contenedor efímero, base de datos separada en el mismo servidor con nombre y credenciales distintas.
2. Ciclo completo: crear → migrar → sembrar → ejecutar → limpiar.
3. **Guarda técnica obligatoria**: los tests se niegan a ejecutarse si detectan un entorno productivo.
4. Seeds de test **independientes** de los seeds de demostración, deterministas y sin credenciales embebidas.
5. Independizar las fixtures de datos preexistentes (`lot_id=2`, usuario `admin`).
6. Aislamiento entre tests: cada test parte de un estado conocido.
7. Documentación del procedimiento para ejecutarlo localmente y en CI.

## Fuera de alcance
Reescribir los 76 tests (es `GA-REM-015`) · entorno de staging completo (backlog) · **cualquier cambio en el mecanismo de despliegue**.

## Decisión de infraestructura requerida
| Opción | Ventaja | Riesgo |
|---|---|---|
| **A · PostgreSQL local** | sin dependencias; rápido | requiere instalación en cada máquina; divergencia con CI |
| **B · Contenedor efímero** | idéntico a CI; desechable por construcción | Docker no está instalado en todas las máquinas de desarrollo |
| **C · BD separada en el servidor existente** | sin instalar nada | **riesgo alto**: misma instancia que producción; un error de configuración es catastrófico |

**Recomendación para la revisión: B en CI y A o B en local. Se desaconseja C**, precisamente porque el problema que se está resolviendo es la proximidad accidental a producción.

## Guarda técnica — requisito no negociable
Implementación conceptual, a concretar según la arquitectura:
```
al iniciar la sesión de pruebas:
    si el destino coincide con el host, la base o las credenciales productivas
    o si ENVIRONMENT == "production"
    → abortar con error explícito, sin ejecutar ningún test
```
La guarda debe estar en `conftest.py`, ejecutarse antes de cualquier fixture, y tener su propio test que verifique que aborta.

## Backend afectado
`tests/conftest.py` (guarda, fixtures independientes), nuevo módulo de seeds de test, posible `pyproject.toml` (configuración de pytest).

## Base de datos afectada
Ninguna en producción. Se crea y destruye una base desechable.

## Seguridad
Elimina el riesgo de escritura accidental en producción desde una sesión de pruebas. Los seeds de test **no** deben contener credenciales reutilizables (coordinado con `GA-REM-004`).

## Edge cases
| Caso | Comportamiento exigido |
|---|---|
| `DATABASE_URL` apunta a producción | los tests abortan antes de ejecutar nada |
| `ENVIRONMENT=production` | los tests abortan |
| Base desechable inexistente | se crea automáticamente o falla con instrucciones claras |
| Migraciones fallidas | los tests abortan con el error de Alembic, no con fallos en cascada |
| Ejecución concurrente de dos suites | bases con nombre distinto, o exclusión mutua |
| Test que deja datos residuales | aislamiento por transacción o limpieza entre tests |

## Acceptance Criteria

**AC01 — La guarda impide ejecutar contra producción**
```
Given DATABASE_URL apuntando al host productivo
When  se ejecuta pytest
Then  la sesión aborta antes de ejecutar cualquier test
And   el mensaje identifica el motivo
And   no se realiza ninguna escritura
```
**AC02 — La guarda salta con ENVIRONMENT=production**
```
Given ENVIRONMENT=production
When  se ejecuta pytest
Then  la sesión aborta
```
**AC03 — Ciclo completo reproducible**
```
Given una máquina limpia con los requisitos documentados
When  se ejecuta el comando único de pruebas
Then  se crea la base, se aplican las migraciones, se siembran los datos y se ejecutan los tests
And   al terminar la base queda destruida o reseteada
```
**AC04 — Fixtures independientes**
```
Given la suite de tests
When  se inspeccionan las fixtures
Then  ninguna depende de un identificador codificado como lot_id=2
And   ninguna depende de datos creados por otro test
```
**AC05 — Determinismo**
```
Given la suite ejecutada dos veces consecutivas
When  se comparan los resultados
Then  son idénticos
```
**AC06 — Seeds de test sin credenciales reutilizables**
```
Given los seeds de test
When  se inspeccionan
Then  no contienen contraseñas que funcionen en ningún entorno desplegado
```
**AC07 — El mismo ciclo funciona en CI**
```
Given el workflow de backend
When  se ejecuta
Then  aplica migraciones y seeds antes de pytest
And   la ejecución no depende de datos preexistentes
```
**AC08 — La producción permanece intacta**
```
Given la ejecución completa de la suite
When  se inspecciona la base de datos productiva
Then  no registra ninguna escritura originada por los tests
```

## Tests requeridos
`T-014-01` la guarda aborta con destino productivo · `T-014-02` la guarda aborta con `ENVIRONMENT=production` · `T-014-03` ciclo completo en máquina limpia · `T-014-04` idempotencia de dos ejecuciones · `T-014-05` análisis estático de fixtures sin identificadores codificados.

## Riesgos
| Riesgo | Mitigación |
|---|---|
| La guarda se implementa mal y no protege | tiene su propio test (`T-014-01/02`) que debe fallar si se desactiva |
| Docker no disponible en alguna máquina | opción A documentada como alternativa |
| Se elige la opción C por comodidad | la spec la desaconseja explícitamente y exige justificación si se adopta |

## Rollback lógico
Reversible por commit. No toca producción por definición.

## Definition of Done
- [ ] Decisión A/B/C documentada y justificada · [ ] Guarda técnica implementada y probada · [ ] AC01–AC08 verificados · [ ] Procedimiento documentado · [ ] Certification report
