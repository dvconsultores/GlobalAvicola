# GA-REM-016 — CERTIFICACIÓN E2E Y DE PROCESOS DE NEGOCIO

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-016` · **Tipo** `QA + PROCESS CERTIFICATION SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P1** · **Estado** `PARTIALLY CERTIFIED` (Wave 3, 2026-09-04) — 3 de 9 pasos del orden |
| **Dependencias** | `GA-REM-002, 005, 006, 007, 011, 014, 015` · **informada por** `GA-REM-020` (validación de cobertura) |
| **Hallazgos** | `audit/06_PROCESS_COVERAGE.md` (0 de 15 procesos certificados) · `GA-TD-035` · `GA-TD-059` |
| **Revalidado** | 2026-09-03 — `tests/` de la raíz (1 065 LOC) sigue sin `playwright.config` que lo ejecute |

## Problema
Cero procesos de negocio certificados. Existen ~80 casos E2E escritos que **nunca se han ejecutado**, y 1 065 LOC de ellos son directamente inejecutables por falta de configuración.

## Evidencia
| Ítem | Detalle |
|---|---|
| Suites E2E | `frontend/tests/` (4 archivos, ~50 casos, con config) · `tests/` raíz (4 archivos, 1 065 LOC, **sin config**) |
| Sin job de E2E en CI | ningún workflow los ejecuta |
| Artefacto obsoleto | `frontend/test-results/.last-run.json` del 2026-06-25, anterior al cambio de paleta y a la refactorización de navegación |
| Procesos identificados | **15 — taxonomía propia del proyecto**, que es la unidad de certificación |

## Comportamiento esperado
La unidad de cierre pasa a ser el **proceso de negocio**, no la pantalla ni el endpoint (Art. IV de la constitución).

## Alcance
1. Reparar la ejecutabilidad de las suites E2E (config, ubicación, datos).
2. Definir, para cada proceso, los casos exigidos: `HAPPY PATH` · `NEGATIVE PATH` · `AUTHORIZATION` · `VALIDATION` · `PERSISTENCE` · `STATE TRANSITION` · `AUDIT`, cuando apliquen.
3. Mantener la **matriz de certificación de procesos**.
4. Ejecutar y certificar por orden de dependencia del dominio.
5. Job de E2E en CI (sujeto a la limitación de `GA-REM-013`).

## Unidad de certificación

La unidad es el **proceso de negocio según la taxonomía propia del proyecto** (`processCatalog.ts`, 15 procesos identificados en `audit/06_PROCESS_COVERAGE.md`). **No se adopta la codificación del cliente.**

`GA-REM-020` aporta, como insumo, la validación de que esos procesos cubren lo que el negocio describió. Es una fuente de verificación de completitud, no una estructura a replicar.

## Matriz de certificación de procesos — formato obligatorio
| Proceso | Req | Specs | FE | BE | DB | Reglas | Seguridad | Tests | E2E | Cobertura validada | Estado |
|---|---|---|---|---|---|---|---|---|---|---|---|

Estados: `NOT_STARTED` · `PARTIAL` · `READY_FOR_E2E` · `E2E_FAILED` · `E2E_PASS` · `CERTIFIED`.

Un proceso solo alcanza `CERTIFIED` cuando **todos** sus componentes críticos están verificados.

## Orden de certificación — derivado del dominio, no arbitrario
La cadena productiva impone precedencia: un proceso que alimenta a otro se certifica antes.

```
1. Recepción de aves            (alimenta el inventario de todos los demás)
2. Control de producción diario (mortalidad · alimento · pesaje)   ← depende de GA-REM-005
3. Revisión → Corrección → Aprobación                              ← depende de GA-REM-006, 007
4. Producción y despacho de huevo fértil
5. Recepción en incubadora e incubación
6. Nacimiento y despacho de pollitos
7. Recepción en engorde y cierre de lote
8. Consolidación y preparación para SAP                            ← depende de GA-REM-010
9. Trazabilidad generacional (transversal)                         ← depende de GA-REM-008
```

La columna «Cobertura validada» se rellena con el resultado de `GA-REM-020`: indica si el proceso, además de funcionar, cubre lo que la documentación del cliente describe.

**Justificación**: el paso 2 concentra el bloqueador P0-1 y es el de mayor frecuencia operativa; el paso 3 es el diferenciador declarado del producto; los pasos 4–7 forman la cadena que la trazabilidad debe unir.

## Fuera de alcance
Certificar la cadena LIVIANAS (fuera de v1) · pruebas de carga · pruebas de accesibilidad automatizadas (backlog).

## Acceptance Criteria

**AC01 — Las suites E2E son ejecutables**
```
Given el repositorio
When  se ejecuta la suite E2E
Then  todos los archivos de test son descubiertos y ejecutados
And   ninguno queda huérfano por falta de configuración
```
**AC02 — Matriz de certificación mantenida**
```
Given la matriz de certificación de procesos
When  se consulta
Then  cada proceso tiene estado, y ninguno figura como CERTIFIED sin E2E en verde
```
**AC03 — Cada proceso certificado tiene sus casos**
```
Given un proceso en estado CERTIFIED
When  se consultan sus casos de prueba
Then  existen al menos happy path, negative path y autorización
```
**AC04 — El primer proceso queda certificado**
```
Given las dependencias resueltas
When  se ejecuta la certificación del primer proceso del orden
Then  alcanza el estado CERTIFIED con evidencia
```
**AC05 — No hay certificación por pantalla**
```
Given el registro de certificaciones
When  se inspecciona
Then  ninguna unidad certificada es una pantalla, un endpoint o un componente
```

## Riesgos
| Riesgo | Mitigación |
|---|---|
| Certificar un proceso que funciona pero no cubre lo que el negocio describió | `GA-REM-020` aporta la validación de cobertura como insumo de la matriz |
| E2E frágiles que se desactivan al primer fallo | Art. 8.3 de la constitución lo prohíbe |
| Certificar sobre datos sembrados que no representan la operación real | los datos de prueba se derivan de la documentación del cliente |

## Definition of Done
- [x] Suites ejecutables · [x] Matriz publicada · [x] Al menos un proceso `CERTIFIED` · [x] Certification report

## Estado tras la Wave 3 (2026-09-04)

| AC | Resultado |
|---|---|
| `AC01` Las suites E2E son ejecutables | ✅ 59 tests en 5 ficheros descubiertos por una configuración única. La suite de la raíz llevaba tres meses sin que ningún ejecutor la cargara: la tumbaba `tests/operations.spec.ts:137` |
| `AC02` Matriz mantenida | ✅ `PROCESS_CERTIFICATION_MATRIX.md`, 15 procesos con estado; ninguno `CERTIFIED` sin E2E en verde |
| `AC03` Cada proceso certificado tiene sus casos | ✅ los tres tienen happy path, negativo y autorización |
| `AC04` El primer proceso queda certificado | ✅ los **tres primeros** del orden |
| `AC05` No hay certificación por pantalla | ✅ la unidad es el proceso; los de etapa quedan `PARTIAL` en lugar de heredar por transitividad |

**Pasos 4–9 del orden pendientes.** El arnés (`scripts_e2e.sh`) y el patrón de casos están
establecidos; continuar es trabajo de ejecución, no de diseño.


---

# ENMIENDA · RECUPERACIÓN DE LA SUITE HEREDADA

**2026-09-05** · origen: clasificación de los 23 fallos de Playwright

## E.1 Por qué hace falta enmendar

El alcance §1 de esta spec dice «reparar la ejecutabilidad de las suites E2E (config,
ubicación, datos)». Eso cubrió lo que la Wave 3 necesitaba: que los ficheros se
descubrieran y se ejecutaran. Y `AC01` se cumple: los 59 casos se descubren y se ejecutan.

Lo que no cubre —y por tanto no autoriza— es lo que ahora toca:

```
reparar la autenticación obsoleta de los tests
reescribir tests contra el flujo vigente
retirar tests superados por un cambio normativo de requisito
```

Un test que se ejecuta y falla **sí** es ejecutable. `AC01` no dice nada sobre si su
contenido sigue siendo válido. Modificar veintitrés tests bajo esa cobertura sería estirar
la spec para que quepa lo que ya se ha decidido hacer, que es exactamente lo que
`NO SPEC = NO DEVELOPMENT` existe para impedir.

## E.2 Qué establece la clasificación

De los 23 fallos del baseline congelado (`15 PASS / 23 FAIL`):

```
DEFECTOS DE APLICACIÓN ....  0 / 23
DEFECTOS DE LOS TESTS ..... 23 / 23
```

| Causa | Casos |
|---|--:|
| `TEST_CREDENTIAL_OBSOLETE` | 8 |
| `TEST_MISSING_AUTHENTICATION` | 14 |
| `TEST_OBSOLETE_UI_CONTRACT` | 12 |
| `TEST_INVALID_EXPECTATION` | 1 |

Los grupos se solapan: doce casos tienen dos causas. El universo sigue siendo **23**.

Detalle en [`PLAYWRIGHT_FAILURE_CLASSIFICATION.md`](../../audit/remediation/PLAYWRIGHT_FAILURE_CLASSIFICATION.md).

## E.3 El objetivo, dicho con precisión

```
NO ES:  hacer que Playwright se ponga verde
ES:     restaurar cobertura válida de requisitos
```

Un test verde sin requisito detrás no certifica nada. Y un test que se retira sin sustituto
**pierde** cobertura aunque la consola mejore. Las dos cosas son formas de engañarse.

## E.4 Criterios de aceptación de la enmienda

| AC | Criterio | Verificación |
|---|---|---|
| **AC06** | La suite heredada se autentica por el mecanismo E2E vigente: usuarios `test_*` y contraseñas del entorno. Ninguna credencial literal entra al repositorio | revisión del diff + ejecución |
| **AC07** | Las afirmaciones funcionales de un test reparado **no se modifican** mientras representen un requisito vigente. Repararlo es quitarle el bloqueo, no reescribir lo que comprueba | comparación antes/después |
| **AC08** | Todo test que se reescriba conserva la **intención funcional** del original y se ejecuta contra el flujo actual, nunca contra la ruta heredada | matriz de disposición |
| **AC09** | Ningún test se retira sin evidencia normativa de que su requisito desapareció o fue sustituido, y sin comprobar que no se pierde cobertura obligatoria | matriz de disposición |
| **AC10** | Cada uno de los 23 casos queda con una disposición razonada, no con un resultado | matriz de disposición, 23/23 |
| **AC11** | Un test recuperado que descubra un desajuste entre spec y aplicación genera un **hallazgo**, no una corrección de código dentro del mismo cambio | registro de hallazgos |
| **AC12** | Las afirmaciones recuperadas no son vacías: se demuestra que pueden fallar | prueba de mortalidad |

## E.5 Disposiciones admitidas

```
REPAIR                 quitar el bloqueo; las afirmaciones no se tocan
REWRITE                el requisito sigue vigente; el flujo cambió
CORRECT_EXPECTATION    la afirmación nunca fue correcta
RETIRED_SUPERSEDED     el requisito desapareció o fue sustituido, con evidencia
BLOCKED_BY_SPEC_GAP    la spec no permite decidir; escala
```

## E.6 Restricciones

No se corrige `TEST_CREDENTIAL_OBSOLETE` sembrando un usuario `admin` con contraseña
`admin`: reintroduciría lo que `GA-REM-004` retiró. No se desactiva la autenticación de la
aplicación, ni se añaden rutas públicas, ni se introduce ningún rodeo para que un test pase.
La corrección vive en el test.

Durante esta tanda **no se modifica código de negocio**: la clasificación establece 0
defectos de aplicación. Si un test recuperado demuestra lo contrario, se detiene ese test y
se abre un hallazgo (`AC11`).

## E.7 Fuera del alcance de la enmienda

Refactorizar la suite más allá de lo necesario · añadir cobertura nueva no exigida por un
requisito · pruebas de accesibilidad automatizadas, que siguen en el backlog.
