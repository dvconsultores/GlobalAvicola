# RELEASE COMPATIBILITY REPORT

**Fecha** 2026-09-04 · **Wave** 2.5
**Pregunta que responde:** ¿puede el código actualmente verde actualizar de forma segura
una instalación existente de Global Avícola sin romper la base, los permisos, las sesiones
ni las operaciones?

---

## Las diez preguntas

### 1. ¿Una instalación nueva funciona?

**Sí.** `PATH A`: PostgreSQL vacío → `alembic upgrade head` → semillas → aplicación →
**229 PASS · 0 FAIL**, y **229 PASS** también con el calendario en 2028.

### 2. ¿Una instalación existente puede actualizarse?

**Sí, con una condición previa que esta Wave resolvió.** `PATH B` parte del esquema
`i9j0k1l2m3n4` con la matriz de permisos histórica, usuarios reales y los enums con
deriva; aplica las migraciones nuevas y da **35 PASS · 0 FAIL**.

La condición era `GA-REM-024`: **no existía ningún paso de migración en el despliegue.**
Sin él, ninguna de las tres migraciones habría llegado a producción y el contenedor nuevo
habría arrancado con el código nuevo contra el esquema viejo.

### 3. ¿`R-40` migra correctamente?

**Sí.** Sobre una base cuyo `eventtype` tenía 24 valores y datos existentes:
`ALTER TYPE ... ADD VALUE IF NOT EXISTS` la deja en 25, y el 25.º tipo de evento se
registra y se relee. Verificado en `PATH B`, no solo en base nueva.

### 4. ¿`R-41` migra correctamente?

**Sí.** `birdtypeenum` pasa de 4 a 5 valores. Se comprobó antes de migrar que **ninguna
fila** usaba el valor histórico —no podía: la aplicación nunca pudo escribirlo—, y el valor
se conserva en lugar de eliminarse, porque quitarlo exigiría recrear el tipo y reescribir
las columnas que lo usan. Tras la migración se crea y se lee un lote de incubadora, y los
lotes históricos siguen siendo legibles.

### 5. ¿`R-44` reconcilia los permisos correctamente?

**Sí.** Migración de datos `l2m3n4o5p6q7`, no semillas: las semillas sirven a instalaciones
nuevas y no tocan una base existente. De 24 asociaciones históricas a 41, **cero
eliminadas**, cero roles creados o borrados, cero usuarios modificados.

### 6. ¿Los usuarios que no son Super Admin conservan sus accesos?

**Sí.** 13 comprobaciones de acceso real por rol tras la actualización —operador,
supervisor, aprobador, analista SAP y auditor sobre las rutas que su función exige—, todas
sin 403.

Sin la reconciliación, todas ellas habrían devuelto 403: `masters:read`, que 40 rutas
exigen, no lo concedía ningún rol.

### 7. ¿El RBAC rechaza lo que debe rechazar?

**Sí.** 8 comprobaciones negativas: un operador no aprueba, no exporta a SAP, no borra
maestros ni consulta auditoría; un auditor no registra ni aprueba; un analista SAP no
aprueba; un supervisor no crea maestros. Todas 403.

Reconciliar no se convirtió en abrir la mano: 13 operaciones de administración siguen
siendo exclusivas del Super Admin, y el Auditor no recibió **ni una** acción de escritura.

### 8. ¿La reconciliación es idempotente?

**Sí.** Verificado por dos vías: la migración solo inserta lo que falta, y un test
comprueba que no existe ninguna asociación duplicada (`GROUP BY … HAVING count(*) > 1`) ni
variación en el recuento.

### 9. ¿Hay pérdida de datos?

**No.** 6/6 usuarios conservados con su rol original, 33/33 permisos históricos intactos,
lotes históricos legibles, valor de enum histórico conservado.

### 10. ¿Existe alguna ventana incompatible durante el arranque?

**No, tras `GA-REM-024`. Antes de esta Wave, sí — y era permanente.**

El arranque era `uvicorn` directo. Un contenedor nuevo empezaba a atender peticiones con el
código nuevo contra el esquema viejo, y esa ventana no se cerraba nunca porque nada
aplicaba las migraciones. Ahora:

```
docker-entrypoint.sh
  -> alembic upgrade head      (si falla, `set -e` impide servir)
  -> exec uvicorn              (el servidor hereda el PID 1)
```

El orden queda garantizado **por construcción**, no por convención. Y si la migración
falla, el contenedor no sirve: servir con el esquema equivocado corrompe datos, y caerse
ruidosamente es preferible.

`EX-01` intacto: Watchtower sigue vigilando `:latest` con `pull_policy: always` y recreando
el contenedor igual que antes. Lo único que cambia es lo que el contenedor hace en su
primer segundo, que es responsabilidad de la imagen y no de la estrategia de despliegue.

---

## Condición de operación

Una acción manual, **una sola vez**, en el servidor:

```
docker compose up -d
```

Watchtower recrea el contenedor con la imagen nueva pero **no vuelve a leer el fichero
compose**: conserva la definición de volúmenes con la que el contenedor se creó. El volumen
`avicola-media` que la Wave 1 añadió (`GA-REM-009`) no se monta hasta que alguien lo
ejecute, y hasta entonces las evidencias siguen perdiéndose en cada recreación.

No impide publicar —el sistema funciona sin ello— pero `GA-REM-009` no surte efecto hasta
que se haga. Registrado como **`R-52`**.

---

## Veredicto

```
READY_FOR_RELEASE = YES
```

Una instalación existente puede actualizarse de forma segura. Ambos caminos están
certificados con evidencia, no por analogía con la base nueva.

Con una condición de operación (`R-52`) que debe ejecutarse en el mismo despliegue, y que
no bloquea la publicación.
