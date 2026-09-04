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
