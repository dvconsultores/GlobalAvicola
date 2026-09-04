# Constitución de Global Avícola

**Versión**: 1.0.0 | **Ratificada**: 2026-09-03 | **Última enmienda**: 2026-09-03
**Origen**: `GA-REM-001` — Programa maestro de remediación post-auditoría
**Ámbito**: todo cambio sobre el repositorio `GlobalAvicola`

> Este documento sustituye a la plantilla de Spec Kit que permaneció sin ratificar desde el 2026-06-22. Es la norma vinculante del proyecto. Supersede cualquier práctica anterior no escrita.

---

## Principios rectores

### I. Spec-first (NO NEGOCIABLE)

```
NO SPEC = NO DEVELOPMENT
```

Ningún cambio con impacto funcional, de datos, de contrato, de seguridad o de regla de negocio se implementa antes de existir una spec aprobada que lo autorice. La spec precede al código; nunca lo acompaña ni lo sigue, salvo la excepción del Art. 4.

### II. Criterios de aceptación verificables (NO NEGOCIABLE)

```
NO ACCEPTANCE CRITERIA = NO IMPLEMENTATION
```

Una spec sin AC verificables no autoriza a implementar. Un AC es verificable si una persona distinta del autor puede ejecutarlo y obtener un resultado inequívoco.

### III. Validación como condición de cierre (NO NEGOCIABLE)

```
NO VALIDATION = NO COMPLETE
```

Nada se declara terminado sin evidencia ejecutable. Un informe que afirma que algo funciona no es evidencia; la salida de un test lo es.

### IV. El proceso de negocio es la unidad de certificación

```
NO E2E = NO PROCESS CERTIFIED
```

Una pantalla, un endpoint o un componente no se «certifican». Se certifica un proceso de negocio completo, con su cadena `usuario → UI → validación → API → autorización → regla → persistencia → respuesta → UI → error`.

### V. La evidencia gana a la declaración

Ante conflicto, el orden de autoridad es: **código ejecutable y su test** > **spec vigente** > **documentación del cliente** > **informes de estado**. Cuando la documentación del cliente y la spec discrepan, no se elige en silencio: se abre un `REQUIREMENT_CONFLICT` (Art. 18).

### VI. Conservar lo que ya está bien

Un componente verificado como correcto no se modifica salvo que un AC concreto lo exija. Ante la duda: *«¿es necesario para cumplir esta spec?»* Si no, no se toca.

---

## Artículos

### Art. 1 — Qué cambios exigen spec

Exigen spec **obligatoriamente**:

1. Nueva funcionalidad o pantalla.
2. Cambio de una regla de negocio, un umbral, un porcentaje o un cálculo.
3. Nueva columna, tabla, relación, enum o restricción.
4. Nuevo endpoint, o cambio del contrato de uno existente (ruta, parámetros, DTO, códigos de respuesta).
5. Cambio en autenticación, autorización, permisos o alcance multi-compañía.
6. Nueva integración externa, o cambio de su semántica.
7. Cambio de una máquina de estados o de una transición.
8. Cambio del design system, de la paleta o de la arquitectura de navegación.
9. Cambio de dependencia que altere comportamiento observable.
10. Cualquier cambio que altere lo que un operador ve o puede hacer.

### Art. 2 — Qué cambios NO exigen spec

Están exentos, para evitar burocracia sin valor:

1. Corrección de erratas en textos ya especificados.
2. Formateo, indentación y ordenación de imports.
3. Comentarios y documentación interna.
4. Renombrado de variables locales sin cambio de comportamiento.
5. Añadir un índice de base de datos que no cambia el esquema lógico.
6. Bump de dependencia sin cambio de comportamiento observable.
7. Añadir un test que no modifica código de producción.

**Criterio objetivo:** un cambio está exento si y solo si **no altera** ninguno de estos cuatro elementos: comportamiento funcional, forma de los datos, contrato de API o superficie de seguridad. Si altera cualquiera, exige spec.

### Art. 3 — Umbral de duda

Si no está claro si un cambio exige spec, **exige spec**. El coste de una spec innecesaria es minutos; el coste de un cambio no gobernado está documentado en la auditoría de 2026-09-02.

### Art. 4 — Excepción de hotfix

Un defecto que impide operar en producción puede corregirse sin spec previa, bajo estas cuatro condiciones acumulativas:

1. El defecto está impidiendo operar **ahora**.
2. La corrección es la mínima que restablece el servicio.
3. Se emite una spec retroactiva en **≤ 24 h**, marcada `RETROSPECTIVE SPEC` con la fecha real del cambio y el motivo de la excepción.
4. Se añade un test de regresión antes de cerrar la spec retroactiva.

Ninguna otra circunstancia justifica implementar sin spec.

### Art. 5 — Estructura mínima de una spec

Toda spec contiene, como mínimo:

```
Metadata (ID · título · tipo · prioridad · estado · dependencias · hallazgos relacionados · fecha)
Problema · Evidencia · Comportamiento actual · Comportamiento esperado
Alcance · Fuera de alcance
Reglas de negocio afectadas
Arquitectura / Frontend / Backend / Base de datos afectados
Seguridad · Migraciones · Compatibilidad · Edge cases
Acceptance Criteria · Tests requeridos
Riesgos · Rollback lógico · Definition of Done
```

Las secciones que no apliquen se declaran explícitamente como «ninguna». No se omiten.

### Art. 6 — Formato de los Acceptance Criteria

Obligatorio `Given / When / Then` o equivalente igualmente verificable.

**Prohibido** redactar AC como: *«el sistema debe funcionar correctamente»*, *«mejorar la experiencia»*, *«optimizar el rendimiento»* o cualquier formulación que no permita a un tercero determinar si se cumple.

Cada AC recibe un identificador (`AC01`, `AC02`, …) y se referencia desde su test.

### Art. 7 — Tasks

La implementación no arranca desde la spec: arranca desde tasks derivadas de ella. Cada task declara: archivo probable, capa, objetivo, dependencia, test asociado y AC relacionado.

Una task que no puede vincularse a un AC no pertenece a esta spec.

### Art. 8 — Testing

1. Todo AC con superficie ejecutable tiene al menos un test.
2. Los tests se ejecutan contra un entorno aislado; **nunca contra producción**. Debe existir una guarda técnica que rechace la ejecución si el entorno es productivo.
3. Prohibido borrar un test porque falla, marcarlo `skip` sin justificación escrita en la spec, rebajar aserciones, alterar el resultado esperado para acomodarlo al defecto, o mockear funcionalidad central para obtener verde.
4. Ante un test en rojo, el orden de decisión es `SPEC → REGLA DE NEGOCIO → TEST → IMPLEMENTACIÓN`. La spec vigente decide quién está equivocado.

### Art. 9 — Revisión

Toda spec se revisa antes de implementarse. La revisión verifica que los AC son verificables, que el alcance está acotado y que no contradice una spec vigente.

**Prohibida la auto-certificación**: el mismo agente, sesión o hilo que implementó un cambio no puede declararlo cerrado. El cierre requiere verificación independiente sobre evidencia ejecutable.

### Art. 10 — Cierre

Una unidad de trabajo se cierra únicamente con: spec + AC + tasks + implementación + tests en verde + evidencia registrada (comando, salida, ruta y línea) + control de regresiones superado + E2E cuando aplique.

Un informe declarativo no cierra nada.

### Art. 11 — Definition of Done

- [ ] Spec aprobada con AC verificables
- [ ] Tasks derivadas y vinculadas a AC
- [ ] Implementación con commits que referencian la spec
- [ ] Tests que cubren cada AC, ejecutados y en verde
- [ ] Evidencia registrada
- [ ] Control de regresiones superado (Art. 12)
- [ ] E2E cuando el AC tiene superficie de usuario
- [ ] Certification report emitido
- [ ] Métricas del proyecto actualizadas

**Estados admitidos:** `DISCOVERED` · `SPEC_DRAFT` · `SPEC_READY` · `IMPLEMENTING` · `IMPLEMENTED` · `TESTING` · `E2E_VALIDATION` · `CERTIFIED` · `BLOCKED_EXTERNAL` · `DEFERRED` · `ACCEPTED_RISK` · `ALREADY_RESOLVED`.

### Art. 12 — Control de regresiones

Antes de cerrar cualquier unidad de trabajo:

1. El problema declarado está resuelto.
2. Los AC se cumplen.
3. Los tests preexistentes siguen pasando.
4. Ningún otro proceso se rompe.
5. La base de datos mantiene **0 deriva** entre modelos y migraciones, y **1 solo head** de Alembic.
6. El frontend compila (`tsc -b --noEmit`).
7. El backend compila (`compileall`).
8. La paridad i18n se mantiene.

### Art. 13 — Trazabilidad

```
HALLAZGO → REQUERIMIENTO → SPEC → AC → TASK → CÓDIGO → TEST → E2E → CERTIFICACIÓN
```

Todo commit debe poder asociarse a una spec o a una de sus tasks. Formato de mensaje:

```
<tipo>(<SPEC-ID>): <resumen>

AC cubiertos: AC01, AC03
```

### Art. 14 — Retrospective specs

Se admiten para documentar código preexistente, **solo cuando aporten valor real**. Obligaciones:

1. Marcarlas `RETROSPECTIVE SPEC` en la cabecera.
2. Declarar la fecha real del código preexistente, obtenida de Git.
3. Declarar el motivo por el que no existió spec previa.
4. **Prohibido** presentarlas como si hubieran existido antes. No se reescribe la historia.

Para cada bloque de código sin spec se decide entre: `RETROSPECTIVE_SPEC` · `LEGACY_ACCEPTED` · `DEPRECATE` · `REPLACE` · `MERGE_INTO_CURRENT_SPEC`. No se retro-especifica todo por defecto.

### Art. 15 — Actualización de specs

Una spec vigente se modifica mediante enmienda fechada, no mediante edición silenciosa. Toda spec lleva número de versión y registro de cambios al pie.

Si durante la implementación se descubre que la spec está equivocada: se **detiene** la implementación, se enmienda la spec, se re-aprueban los AC afectados y se continúa. Nunca se implementa contra la spec.

### Art. 16 — Bugfix

Un bugfix exige spec cuando el defecto revela una regla de negocio mal entendida, cuando la corrección cambia comportamiento observable, o cuando toca autorización, datos o contratos. No la exige cuando restablece el comportamiento que la spec vigente ya describe.

Todo bugfix, con o sin spec, exige **test de regresión**: el test debe fallar antes de la corrección y pasar después.

### Art. 17 — Refactor

Un refactor que no altera comportamiento observable no exige spec propia, pero sí una nota de refactor en la spec vigente del módulo y el control de regresiones completo.

Un refactor que altera arquitectura, ORM, autenticación, estructura de módulos, design system o navegación **exige spec**.

**Prohibido** el refactor estético masivo: renombrados globales, reorganización de carpetas, cambio de framework o librería estable, y rediseño de UI sin spec que lo justifique.

### Art. 18 — Conflictos de requerimiento

Cuando `DOCUMENTACIÓN DEL CLIENTE ≠ SPEC ≠ CÓDIGO ≠ AUDITORÍA`, no se elige arbitrariamente ni se resuelve en silencio. Se abre un `REQUIREMENT_CONFLICT` que registra: alternativas, impacto, evidencia de cada fuente y comportamiento actual.

**No se desarrolla** hasta determinar la regla vigente.

### Art. 19 — Migraciones y cambios de esquema

1. Toda modificación de esquema se hace **exclusivamente** por migración Alembic formal.
2. Nunca se altera la estructura manualmente ni desde el ORM sin migración.
3. El docstring de cada migración cita la spec y el AC que la autorizan.
4. La cadena de migraciones mantiene **un solo head**.
5. La deriva entre `Base.metadata` y las migraciones debe permanecer en **cero**; se verifica en cada cierre.
6. Una migración que relaja una restricción de integridad exige justificación explícita en la spec.

### Art. 20 — Seguridad

1. Todo cambio con superficie de autenticación, autorización, sesión, permisos o datos personales exige spec y revisión.
2. La autorización se aplica **en el servidor**. Ocultar un control en la interfaz nunca constituye control de acceso.
3. Prohibido versionar credenciales reales, en código o en documentación.
4. Todo endpoint nuevo declara explícitamente su permiso exigido; no existe endpoint sin decisión de autorización documentada.

### Art. 21 — Integraciones externas

1. Una integración no puede **aparentar** haberse completado. Un adaptador manual o simulado no puede dejar un registro en un estado que signifique «confirmado por el sistema externo».
2. Los estados de integración distinguen entre preparado, enviado, confirmado y fallido.
3. Lo que dependa de credenciales, endpoints o especificaciones que no están en el proyecto se marca `BLOCKED_EXTERNAL`. **Prohibido simular éxito.**
4. La idempotencia de un envío externo es responsabilidad del servidor.

### Art. 22 — Cambios de reglas de negocio

Toda regla de negocio tiene un identificador único, usado de forma idéntica en la spec, en el código y en los mensajes al usuario. Cambiar una regla, su umbral o su cálculo exige spec, y la spec debe enumerar **todos** los puntos de entrada donde la regla se aplica.

Una regla validada en un solo punto de entrada cuando existen varios se considera **no implementada**.

### Art. 23 — Política de desviaciones

Las desviaciones se registran, no se ocultan. Cuando se detecta código fuera de spec se clasifica: `SPEC_COMPLIANT` · `SPEC_PARTIAL` · `IMPLEMENTED_WITHOUT_SPEC` · `CODE_BEFORE_SPEC` · `OUT_OF_SPEC` · `SPEC_DRIFT` · `LEGACY`.

Ninguna desviación se resuelve borrando la evidencia.

---

## Excepciones y riesgos aceptados

### EX-01 — Deployment automático

```
KNOWN_ACCEPTED_RISK
OUT_OF_SCOPE
NO MODIFICAR
```

Por decisión del propietario del proyecto, el mecanismo actual de despliegue automático se mantiene sin cambios: publicación automática de imágenes al hacer `push` a `main`, etiqueta `:latest` y actualización automática de contenedores por Watchtower.

**Limitaciones derivadas, reconocidas y aceptadas** (`KNOWN_ACCEPTED_LIMITATION`):

1. Un quality gate de CI **no puede impedir** que una imagen defectuosa llegue a producción.
2. El intervalo entre un commit defectuoso y su llegada a producción es de segundos.
3. No existe promoción por etiqueta ni rollback automatizado.

Esta constitución **no** exige corregir EX-01. Ninguna spec del programa puede introducir ese cambio por vía indirecta.

**Obligación compensatoria:** dado que la puerta de despliegue no existe, la disciplina de spec y test adquiere carácter crítico. Los Art. 1, 8, 10 y 12 se aplican con rigor máximo.

---

## Gobierno

1. Esta constitución supersede cualquier práctica anterior no escrita.
2. Toda spec, revisión y cierre debe verificar su cumplimiento.
3. Las enmiendas requieren: motivo documentado, incremento de versión y fecha.
4. La complejidad debe justificarse: ante dos soluciones que cumplen los AC, se elige la más simple.
5. El incumplimiento de un artículo no se resuelve borrando el artículo, sino registrando la desviación conforme al Art. 23.

### Versionado

`MAJOR.MINOR.PATCH` — MAJOR: cambio de un principio rector. MINOR: nuevo artículo o cambio sustantivo. PATCH: aclaración sin cambio normativo.

### Registro de cambios

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0.0 | 2026-09-03 | Ratificación inicial. Sustituye la plantilla sin rellenar vigente desde 2026-06-22. Origen: `GA-REM-001`. |
