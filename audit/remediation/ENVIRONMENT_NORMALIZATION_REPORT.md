# INFORME DE NORMALIZACIÓN DE ENTORNO

**`ENV-01` + `GA-REM-025`** · 2026-09-04

---

## 1. Resumen

El propietario aclaró que el entorno desplegado **no es producción**. Es un entorno
compartido de desarrollo, pruebas y certificación, y sus datos son datos de prueba. No
existe todavía ninguna instalación empresarial real.

Esa aclaración cambia el significado de varias conclusiones anteriores, y habilita algo que
antes estaba vedado: retirar la historia ficticia acumulada. De ahí sale este checkpoint.

Lo entregado: la decisión normativa `ENV-01`; la spec `GA-REM-025` con quince criterios de
aceptación; una clasificación de las 48 tablas persistentes; herramientas de inventario y
reset con guarda fail-closed; un seed de baseline mínimo; un módulo de fixtures
deterministas; y la certificación completa del ciclo sobre infraestructura aislada.

Lo no entregado, y por qué: **la ejecución sobre el entorno compartido**. Su base de datos
no es alcanzable desde esta red y no hay acceso al servidor.

Y lo que apareció por el camino, que quizá sea lo más valioso: **dos defectos reales que
solo se ven en una instalación limpia**, uno de ellos intermitente.

## 2. Aclaración del propietario

> El entorno actual desplegado no es producción real. Es un entorno compartido de
> desarrollo, pruebas y certificación. Los datos existentes son datos de prueba y
> certificación. No existe todavía una instalación productiva real de Global Avícola.

Es normativa y gobierna todo lo que sigue.

## 3. `ENV-01`

```
CURRENT DEPLOYED ENVIRONMENT   =  SHARED DEVELOPMENT / TEST / CERTIFICATION
REAL PRODUCTION                =  NOT DEPLOYED YET
CURRENT DATABASE BUSINESS DATA =  TEST / CERTIFICATION DATA
CURRENT USERS                  =  DEVELOPMENT / TEST / CERTIFICATION USERS
CURRENT AUTO DEPLOY            =  DEPLOYS TO SHARED DEVELOPMENT / CERTIFICATION
REAL PRODUCTION RELEASE        =  FUTURE SEPARATE GATE
```

Documento completo: [`ENV-01-ENVIRONMENT-CLASSIFICATION.md`](../../specs/remediation/ENV-01-ENVIRONMENT-CLASSIFICATION.md).

## 4. Qué se suponía antes

Los informes desde la auditoría integral hasta la Wave 3 trataron `avicola.globaldv.net`
como producción. Esa lectura gobernó decisiones reales: exigir copia verificada antes de
migrar, prohibir tocar el servidor, clasificar `GA-TD-040` como bloqueante de publicación,
y leer el despliegue automático como una vía directa a producción empresarial.

Era razonable con lo que se sabía. **No se reescribe la historia**: los informes conservan
su fecha, su hallazgo, su evidencia y su decisión, y llevan una anotación de
reclasificación donde la denominación afectaba a la conclusión.

## 5. Clasificación correcta

A partir de aquí, `SHARED_TEST` o `CERTIFICATION_ENVIRONMENT` para el servidor actual.
`PRODUCTION` y `REAL_PRODUCTION` quedan reservados para la instalación de cliente que
todavía no existe.

## 6. Efecto sobre los gates anteriores

Ningún hallazgo se cierra por la reclasificación. Cambian de urgencia:

| Antes | Ahora |
|---|---|
| `GA-TD-040` copia verificada · **bloqueante de publicación** | **`PRE-REAL-PRODUCTION`** — no bloquea el desarrollo |
| `GA-TD-039` observabilidad · pre-producción | **`PRE-REAL-PRODUCTION`**; la mínima del entorno compartido ya es útil |
| `R-52` volumen de evidencias · activación productiva | **mantenimiento normal del entorno de certificación** |
| `R-58` entrypoint en Docker real | **debe cerrarse en el entorno compartido**, que es Docker real |
| `R-44` efecto de la reconciliación | sigue abierto: afecta a quien está probando hoy |

## 7. Inventario de datos

48 tablas: las 47 del modelo más `alembic_version`. Cobertura verificada por prueba; nada
queda sin clasificar, y lo no clasificado no se borra.

| Categoría | Tablas | Destino |
|---|--:|---|
| `SYSTEM_REQUIRED` | 1 | conservar |
| `AUTH_REQUIRED` | 4 | conservar |
| `CONFIGURATION_REQUIRED` | 1 | conservar |
| `REFERENCE_MASTER_REQUIRED` | 1 | conservar |
| `CLIENT_MASTER_DATA` | 17 | **borrar** |
| `TEST_BUSINESS_DATA` | 20 | **borrar** |
| `SIMULATED_SAP_DATA` | 4 | **borrar** |

Detalle: [`SHARED_ENV_DATA_INVENTORY.md`](SHARED_ENV_DATA_INVENTORY.md).

**Los recuentos reales del entorno compartido no pudieron leerse**: su base rechaza la
conexión desde esta red. Las cifras medidas provienen de una réplica construida con los
mismos seeds.

## 8. Datos que deben persistir

La pregunta se respondió midiendo, no suponiendo. Se inventarió qué puede crear un cliente
nuevo por sí mismo: los 19 maestros tienen CRUD completo, los pasos de aprobación se
autoprovisionan, los roles se crean por API, las fases productivas también.

Lo único que **no** puede crearse desde cero: las **asociaciones rol→permiso** —no existe
API— y el **primer usuario**, sin el cual no puede llamarse a ninguna API.

Con un detalle que cambia el análisis: la migración `l2m3n4o5p6q7` no crea roles; los busca
por nombre y salta los que faltan. Sobre base vacía añade **0 asociaciones**, comprobado.
Reconciliar no basta para instalar.

## 9. Datos retirados

Del baseline desaparecen 41 tablas de contenido: 17 de maestros inventados, 20 de historia
operativa ficticia, 4 de SAP simulado. Medido sobre la réplica: **182 filas → 0**.

## 10. Datos conservados

`alembic_version`, `roles`, `permissions`, `users`, `companies`, `approval_steps` y
`productive_phases`. Los usuarios y las empresas se conservan **por omisión**; retirarlos
exige `--purge-identities`, explícito, y aun así se reserva siempre el administrador y los
dos tenants de certificación.

## 11. Datos SAP de prueba

```
SAP TEST/SIMULATION  =  ALLOWED IN DEVELOPMENT/CERTIFICATION
REAL SAP DELIVERY    =  NO EXISTE
```

Las cuatro tablas SAP se vacían. El adaptador de simulación **se conserva en código**: es
infraestructura de desarrollo, no dato de negocio falso. `GA-REM-017` sigue
`BLOCKED_EXTERNAL` y no se toca aquí.

La razón de vaciarlas no es de espacio: un documento simulado con estado «confirmado»
representa como real algo que nunca ocurrió, y eso es precisamente lo que `GA-REM-010`
vino a corregir en la semántica.

## 12. Usuarios, roles y permisos

6 roles · 55 asociaciones · 46 operativas + 9 comodines del Super Administrador.

La matriz **no se copia** en el seed: se importa de la migración que es su fuente única.
Mantener dos copias fue la causa de `R-44`, y repetir el error habría sido difícil de
justificar.

Verificado permiso a permiso, no por el total: dos roles con permisos intercambiados darían
el mismo 46 y una autorización equivocada. Se comprueba además que **no sobre** ninguno
fuera de `docs/12 §3`.

## 13. Settings

Los umbrales de mortalidad configurables (`GA-REM-005`) están presentes: 3 % y 8 %. Los
valores por omisión del compose coinciden con los del código, de modo que rigen igual se
relea el compose o no. No se introduce configuración por empresa: sigue diferida a
`GA-REM-019`.

## 14. Estrategia de limpieza

**Purga controlada**, no reconstrucción. La reconstrucción exigiría detener la aplicación y
permisos de creación de bases que no pueden verificarse desde aquí; una limpieza que falla
a mitad es peor que ninguna.

La purga corre en una transacción, conserva esquema y versión, y va precedida de una
comprobación que evita que el `CASCADE` arrastre configuración: **ninguna tabla conservada
puede depender de una borrada**. Hoy: 0 dependencias cruzadas.

Detalle: [`SHARED_ENV_CLEANUP_PLAN.md`](SHARED_ENV_CLEANUP_PLAN.md).

## 15. Baseline limpio

```
6 roles · 55 permisos · 4 fases productivas · 2 empresas de certificación · 1 administrador
0 filas de historia operativa · 0 filas SAP · 0 maestros de cliente
```

Reproducible: dos resets consecutivos dan exactamente el mismo estado.

## 16. Arranque desde cero

```
base vacía → alembic upgrade head → head único → seed de baseline → backend sirviendo
```

Sin deriva de esquema, tablas, columnas ni enums. `R-40` y `R-41` siguen coincidiendo entre
Python, SQLAlchemy y PostgreSQL sobre una base recién creada.

## 17. Estados vacíos

Nueve pantallas contra una base sin nada: lotes, operaciones, alertas, panel, granjas,
galpones, revisión, aprobaciones y auditoría. **Todas HTTP 200.** Ningún 500, ninguna
pantalla rota, ninguna suposición de que existan datos.

## 18. Primer flujo de negocio

```
login → situarse en la empresa → granja → galpón → línea → raza → causa
      → lote → recepción de 5.000 aves → mortalidad de 12 → saldo correcto
```

Todo por HTTP, como lo haría el frontend. El sistema arranca limpio y opera.

## 19. Regresión multiempresa

Sobre datos creados en la misma ejecución, con un usuario **no** Super Administrador —el
Super Admin está exento del filtro por diseño (`app/masters/service.py:35`), así que
probarlo con él mediría lo contrario de lo que se busca:

| Comprobación | Resultado |
|---|---|
| `R-48` situarse en una empresa | **PASS** |
| `R-54` el token queda alcanzado a esa empresa | **PASS** |
| `R-59` B no ve las granjas de A | **PASS** — 0 |
| `R-59` B no ve los lotes de A | **PASS** — 0 |
| `R-59` B no lee el lote de A por id directo | **PASS** — 404 |
| `R-59` B no ve las operaciones de A | **PASS** — 0 |
| `R-42` escritura de B sobre el lote de A | **PASS** — denegada |

## 20. Regresión backend

```
283 pasados · 49 omitidos · 0 fallos      (96 s)
```

Incluye las 18 pruebas nuevas de `GA-REM-025`. Contra la base de test aislada de
`GA-REM-014`, nunca contra el entorno compartido.

## 21. Regresión frontend

```
TypeScript ....... PASS
Vitest ........... 61/61
ESLint ........... PASS
Paridad i18n ..... 866 ES = 866 EN · 0 faltantes
```

## 22. `R-52` — volumen de evidencias

Reclasificado: de «acción de activación productiva» a **acción normal de mantenimiento del
entorno de certificación**. Sigue **PENDING**: Watchtower recrea el contenedor pero no
relee el compose, así que `avicola-media` no está montado y `GA-REM-009` no está activa.

Requiere `docker compose up -d backend` en el servidor. **`BLOCKED_BY_AUTH`.**

## 23. `R-58` — entrypoint en Docker real

Reclasificado: **debe cerrarse en el entorno compartido**, que es Docker real, sin esperar a
un productivo futuro. Sigue en `PASS_BY_INFERENCE`: el backend sirve tras un entrypoint con
`set -e`, luego migró; falta la lectura de `docker logs`.

**`BLOCKED_BY_AUTH`.**

## 24. Git, commits y push

Este checkpoint se versiona en commits atómicos por naturaleza del cambio. La política
vigente para el entorno compartido:

```
SPEC → AC → IMPLEMENTACIÓN → TEST → CHECKPOINT CERTIFICADO → COMMIT → PUSH → AUTO DEPLOY
```

No se exige preparación para producción real en cada push al entorno compartido. Sí se
mantiene `NO UNVERIFIED PUSH`: tests relacionados, regresión, revisión del diff, ausencia
de secretos, trazabilidad a spec y AC.

Autenticación: solo la explícitamente autorizada. Si no existe, `PUSH_BLOCKED_BY_AUTH`.

## 25. Preparación para el entorno compartido

```
READY_FOR_SHARED_TEST = YES
```

El código pasa toda la regresión, el baseline está certificado y las herramientas de
inventario y reset están probadas. Lo que falta es **ejecución con acceso**, no trabajo de
desarrollo.

## 26. Preparación para producción real

```
READY_FOR_REAL_PRODUCTION = NOT_YET_CERTIFIED
```

Pendiente: `GA-TD-040` (copia y restauración verificadas), `GA-TD-039` (observabilidad),
`R-67` y `R-68`, la certificación E2E completa de `GA-REM-016`, y la decisión sobre SAP
real (`GA-REM-017`).

## 27. Trabajo restante

| # | Acción | Bloqueo |
|--:|---|---|
| 1 | Ejecutar el inventario y el reset sobre el entorno compartido | acceso |
| 2 | `docker compose up -d backend` para `R-52` | acceso |
| 3 | `docker logs` para cerrar `R-58` | acceso |
| 4 | Verificar el efecto de `R-44` con una cuenta no Super Admin | credencial |
| 5 | Especificar y corregir `R-67` y `R-68` | spec pendiente |
| 6 | Retomar `GA-REM-016`: clasificar los 23 fallos Playwright | — |

## 28. Índice de evidencias

| Documento | Contenido |
|---|---|
| [`ENV-01`](../../specs/remediation/ENV-01-ENVIRONMENT-CLASSIFICATION.md) | decisión normativa de entorno |
| [`GA-REM-025`](../../specs/remediation/GA-REM-025-CLEAN-DEVELOPMENT-BASELINE.md) | spec y 15 criterios de aceptación |
| [`SHARED_ENV_DATA_INVENTORY.md`](SHARED_ENV_DATA_INVENTORY.md) | 48 tablas clasificadas |
| [`SHARED_ENV_CLEANUP_PLAN.md`](SHARED_ENV_CLEANUP_PLAN.md) | plan por recurso y procedimiento |
| [`FRESH_DEVELOPMENT_BASELINE_CHECKLIST.md`](FRESH_DEVELOPMENT_BASELINE_CHECKLIST.md) | 35 comprobaciones de instalación |
| `backend/scripts/data_classification.py` | fuente única de la clasificación |
| `backend/scripts/reset_guard.py` | guarda fail-closed de cinco señales |
| `backend/scripts/environment_reset.py` | inventario y purga controlada |
| `backend/scripts/certify_baseline.sh` | ciclo completo, un solo comando |
| `backend/scripts/first_flow_check.py` | estados vacíos y primer flujo |
| `backend/seeds/baseline_seeds.py` | seed mínimo |
| `backend/seeds/scenario_fixtures.py` | fixtures deterministas |
| `backend/tests/test_clean_baseline.py` | 18 pruebas de los AC |
