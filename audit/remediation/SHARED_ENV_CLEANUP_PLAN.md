# PLAN DE LIMPIEZA DEL ENTORNO COMPARTIDO

**GA-REM-025 §29 y §32** · 2026-09-04

---

## 1. Estrategia elegida: purga controlada

El encargo ofrece dos caminos y pide elegir por evidencia, no por comodidad.

**`OPTION A — CLEAN REBUILD`** (`DROP DATABASE` → `alembic upgrade` → seeds) es más simple
y deja menos margen a residuos. Se **descarta** por dos razones concretas: exige detener la
aplicación —el contenedor mantiene conexiones abiertas y `DROP DATABASE` las rechaza— y
exige permiso de creación de bases, que el usuario de la aplicación no tiene por qué tener.
Ninguna de las dos cosas puede comprobarse desde aquí, y una limpieza que falla a mitad es
peor que ninguna.

**`OPTION B — CONTROLLED PURGE`** es la elegida:

```
TRUNCATE de 41 tablas, en una transacción, RESTART IDENTITY CASCADE
    ↓
configuración e identidades conservadas
    ↓
seed de baseline, idempotente
```

Conserva el esquema y `alembic_version`, de modo que la versión no se mueve; se ejecuta en
una sola transacción, así que o se hace entera o no se hace; y no necesita más permiso que
el que la aplicación ya usa.

Verificado de extremo a extremo: 182 filas → 0, dos veces seguidas con el mismo resultado.

## 2. Salvaguarda que hace correcto el `CASCADE`

`TRUNCATE ... CASCADE` arrastra las tablas que dependen de las vaciadas. Antes de tocar
nada, la herramienta comprueba que **ninguna tabla conservada tenga una clave foránea hacia
una tabla a borrar**; si la hubiera, aborta con código 3 sin ejecutar el borrado. Sin esa
comprobación, el `CASCADE` podría vaciar configuración en silencio.

Estado actual: 0 dependencias cruzadas. Cubierto por `T-025-04`.

## 3. Plan por recurso

| Recurso | Actual | Conservar | Borrar | Recrear | Motivo |
|---|---|:--:|:--:|:--:|---|
| `alembic_version` | 1 fila | ✔ | | | borrarla haría que Alembic reaplicase toda la cadena |
| `roles` | 6 | ✔ | | seed si faltan | no hay API que cree asociaciones de permiso |
| `permissions` | 55 | ✔ | | seed si faltan | 46 operativas + 9 comodines del Super Administrador |
| `users` | varios | ✔ por omisión | opt-in | admin del baseline | §26: nunca en bloque; `--purge-identities` para retirar las obsoletas |
| `companies` | varias | ✔ por omisión | opt-in | `TEST COMPANY A` y `B` | mínimo exigido por `R-42`/`R-48`/`R-54`/`R-59` |
| `approval_steps` | — | ✔ | | `POST /approval-steps/seed-defaults` | configuración de flujo, no historia |
| `productive_phases` | 4 | ✔ | | seed si faltan | catálogo invariante del dominio; `lot_phases` depende de él |
| 17 maestros de cliente | 170 filas | | **✔** | los crea el usuario | CRUD completo por API; los actuales son inventados |
| 20 tablas de historia operativa | ficticia | | **✔** | fixtures de escenario | objetivo declarado del encargo |
| 4 tablas SAP | simulada | | **✔** | — | nunca hubo SAP real; conservarlas como «confirmadas» representa como real lo que no lo es |

## 4. Retirada de identidades

Por omisión el reset **no toca usuarios ni empresas**: quien esté probando no puede quedarse
fuera por una limpieza de datos. `--purge-identities` es explícito y opt-in, y aun así
reserva siempre el administrador del baseline y las dos empresas de certificación; sin esa
reserva el sistema quedaría sin acceso posible.

Verificado: retiró 10 usuarios y 4 empresas dejando exactamente el administrador y los dos
tenants.

## 5. Orden de ejecución

El orden importa, y una de sus razones se descubrió al probarlo:

```
1. detener el backend
2. inventariar            (--inventory, no modifica nada)
3. resetear               (--reset --confirm-database <base>)
4. arrancar el backend
5. verificar              (first_flow_check)
```

**El paso 1 no es una precaución de estilo.** Resetear con la aplicación en marcha deja
conexiones apuntando a filas que ya no existen, y los errores resultantes parecen defectos
del sistema sin serlo. Ocurrió durante esta certificación y costó una investigación.

## 6. Cómo se ejecuta

```sh
# 1 · inventariar, sin tocar nada
DATABASE_URL=… python -m scripts.environment_reset --inventory

# 2 · resetear
ENVIRONMENT=development \
GA_ALLOW_DESTRUCTIVE_RESET=1 \
GA_RESET_ALLOWED_TARGETS=<host>/<base> \
GA_BASELINE_ADMIN_PASSWORD=<contraseña> \
DATABASE_URL=… \
python -m scripts.environment_reset --reset --confirm-database <base> [--purge-identities]
```

Las cinco señales de la guarda deben cumplirse **todas**: entorno permitido, marcador
explícito de intención, destino en lista blanca, base sin marca de instalación real, y el
nombre de la base reescrito a mano. Cualquiera que falte aborta sin borrar.

## 7. Copia previa

`ENV-01` reclasifica este entorno: sus datos son de prueba, y una copia **no debe bloquear
el desarrollo** (§33 y §34 del encargo). Si el mecanismo está a mano, conviene un
`DEVELOPMENT SNAPSHOT`; no es una `PRODUCTION RELEASE BACKUP` y no debe llamarse así.

## 8. Qué no puede hacerse desde aquí

```
EJECUCIÓN SOBRE EL ENTORNO COMPARTIDO = BLOCKED_BY_NETWORK
```

La base no es alcanzable y no hay acceso al servidor. El plan, la herramienta y su
certificación están completos; **la ejecución requiere a alguien con acceso**, siguiendo
§5 y §6 de este documento.
