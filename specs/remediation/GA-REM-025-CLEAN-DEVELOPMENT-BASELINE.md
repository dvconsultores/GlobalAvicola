# GA-REM-025 — BASELINE LIMPIO DEL ENTORNO COMPARTIDO

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-025` · **Tipo** `ENVIRONMENT + TEST DATA STRATEGY SPEC` |
| **Prioridad** | **P1 · habilitador de `GA-REM-016`** |
| **Estado** | `SPEC_READY` |
| **Origen** | `ENV-01` — aclaración normativa del propietario |
| **Dependencias** | `ENV-01`, `GA-REM-014` (infraestructura de test aislada), `GA-REM-004` (cuentas) |
| **Detectado** | 2026-09-04 — checkpoint de normalización de entorno |

## Problema

El entorno compartido acumula datos de negocio ficticios de dos años de desarrollo: lotes
demo, eventos operativos sintéticos, documentos SAP simulados marcados como confirmados,
transacciones de certificaciones antiguas. Nadie sabe cuáles siguen siendo necesarios.

Eso produce dos daños distintos, y conviene no confundirlos.

**El primero es de credibilidad de las pruebas.** Cuando un test pasa, no se sabe si pasó
porque el código funciona o porque encontró un lote que alguien dejó ahí en marzo. Un test
que asume `lot 123` no prueba nada: prueba que `lot 123` sigue existiendo.

**El segundo es arquitectónico, y es el grave.** Global Avícola nunca ha demostrado que
puede arrancar desde una base vacía. Si el sistema depende —sin que nadie lo haya
advertido— de registros que solo existen porque un seed antiguo los insertó, entonces la
instalación para el primer cliente real fallará, y se descubrirá en el peor momento
posible. Limpiar el entorno compartido es, de paso, la primera prueba real de instalación.

### Lo que la investigación previa establece

Se inventarió qué puede crear un cliente nuevo por sí mismo, y qué no:

| Recurso | ¿Autoservicio? | Evidencia |
|---|---|---|
| 19 maestros (granjas, galpones, líneas genéticas, causas, vacunas, transportes…) | **sí**, CRUD completo | `app/masters/router.py:88-106` |
| Pasos de aprobación | **sí**, incluso `POST /approval-steps/seed-defaults` | `app/review/router.py:166-206` |
| Roles | **sí** | `app/auth/router.py:125-149` |
| Fases productivas | **sí** (CRUD; ningún código depende de sus `code`) | `app/masters/router.py:101` |
| **Asociaciones rol→permiso** | **no** — no hay API; se crean al crear el rol o por migración | `app/auth/service.py:315` |
| **Primer usuario autenticable** | **no** — se necesita uno para poder llamar a cualquier API | — |

De ahí sale la lista corta de requisitos de inicialización del sistema: **roles,
permisos y un usuario administrador**. Todo lo demás es dato de cliente, y el baseline no
debe inventarlo (`ENV-01 §3`, encargo §60).

Detalle importante: la migración `l2m3n4o5p6q7` **no crea roles** —los busca por nombre y
salta los que no existen (`alembic/versions/l2m3n4o5p6q7:121-126`)—. Sobre una base vacía
no hace nada. Luego el baseline necesita un seed que cree roles y permisos; la migración
solo reconcilia instalaciones ya existentes.

## Alcance

1. Herramienta de inventario de datos persistentes, ejecutable contra cualquier base.
2. Herramienta de reset reproducible con guarda dura contra entornos no autorizados.
3. Seed mínimo de baseline: roles, permisos, administrador, contexto multiempresa de
   certificación. **Sin historia operativa.**
4. Separación explícita entre seed permanente y fixtures de escenario.
5. Certificación de arranque limpio, estados vacíos y primer flujo de negocio.

## Fuera de alcance

SAP real (`GA-REM-017`, `BLOCKED_EXTERNAL`) · umbral de mortalidad por empresa (diferido a
`GA-REM-019`) · corrección de los 23 fallos Playwright (`GA-REM-016`, se retoma después) ·
**cualquier cambio en el despliegue automático** (`EX-01`).

## Acceptance Criteria

| AC | Criterio | Verificación |
|---|---|---|
| **AC01** | Tras el reset no queda historia operativa ficticia: `lots`, `operational_events` y sus 12 tablas dependientes están vacías | consulta de recuento por tabla |
| **AC02** | Alembic queda en `head`, con una sola cabeza | `alembic current` / `alembic heads` |
| **AC03** | Existen los 6 roles y sus asociaciones de permiso; **46** para los 5 roles operativos, más los comodines del Super Administrador | consulta y comparación contra `PERMISOS_POR_ROL` |
| **AC04** | Los Settings requeridos están presentes y con los valores de la spec vigente | arranque de la aplicación + comprobación de `Settings` |
| **AC05** | Los usuarios de test autorizados pueden autenticarse; sus contraseñas no viven en el repositorio | login real + ausencia de literales |
| **AC06** | Existen —o pueden crearse de forma determinista— dos contextos de tenant para pruebas multiempresa | fixture de dos empresas |
| **AC07** | No queda ningún registro SAP simulado representado como envío real | recuento de `sap_payloads`, `sap_references`, `sap_responses`, `sap_sync_jobs` |
| **AC08** | La regresión completa del backend pasa contra la base de test aislada | suite backend |
| **AC09** | La regresión del frontend pasa: TypeScript, Vitest, ESLint, paridad i18n | gates del frontend |
| **AC10** | El entorno E2E crea sus propias precondiciones deterministas, sin depender de datos residuales | fixtures de escenario |
| **AC11** | El reset es reproducible: ejecutarlo dos veces produce el mismo estado | doble ejecución + comparación |
| **AC12** | No se introducen secretos ni información de producción real | revisión de diff |

Criterios adicionales que la investigación hizo necesarios:

| AC | Criterio | Verificación |
|---|---|---|
| **AC13** | La aplicación arranca y opera con la base de negocio vacía: sin errores 500, sin pantallas rotas, estados vacíos correctos | pruebas de estado vacío |
| **AC14** | Desde el baseline vacío puede recorrerse el primer flujo completo: maestros → lote → operación → saldo correcto | prueba de primer flujo |
| **AC15** | La herramienta de reset rechaza, de forma fail-closed, cualquier entorno que no sea inequívocamente de desarrollo/test | pruebas de la guarda |

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Borrar configuración necesaria creyéndola dato de prueba | inventario y clasificación **antes** de borrar; el plan de limpieza es explícito por tabla |
| Que la herramienta de reset se ejecute algún día contra un cliente real | guarda dura multiseñal, `AC15`; nunca se invoca desde el arranque ni desde el despliegue |
| Que los tests fallen tras la limpieza | es el resultado esperado si estaban mal aislados: se clasifica como `TEST_DATA_DEPENDENCY_DEFECT` y se corrige el fixture, **nunca** reinsertando datos |
| Que el entorno compartido quede inservible para quien esté probando | el baseline conserva usuarios y tenants de certificación; lo que desaparece es la historia operativa |

## Definition of Done

- `AC01`…`AC15` verificados con evidencia.
- Inventario, plan de limpieza y checklist de instalación publicados en `audit/remediation/`.
- Herramientas de inventario y reset versionadas y con pruebas propias.
- Seed de baseline separado del seed de desarrollo y de los fixtures de escenario.
- `ENVIRONMENT_NORMALIZATION_REPORT.md` emitido.
