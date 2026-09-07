# MATRIZ DE PRUEBAS DE SEGURIDAD POR UNIDAD

Auditoría del 2026-09-07 · **diseño de pruebas futuras, no ejecutadas**

---

## 1. Los fixtures

```
EMPRESA 1  →  Progenitoras
EMPRESA 2  →  Reproductoras · Incubadora · Engorde
EMPRESA 3  →  Incubadora
```

Dentro de la empresa 2:

```
USUARIO A  →  Reproductoras
USUARIO B  →  Incubadora
USUARIO C  →  Reproductoras + Incubadora
ADMIN      →  administración de módulos
```

Y datos en las tres unidades de la empresa 2, para que el aislamiento tenga contra qué fallar.

## 2. Los cinco casos de acceso

| # | Empresa | Módulo empresa | Módulo usuario | Permiso | Esperado |
|:--:|---|:--:|:--:|:--:|:--:|
| 1 | propia | ON | ON | ON | **PASS** |
| 2 | propia | **OFF** | ON (histórico) | ON | **DENY** |
| 3 | propia | ON | **OFF** | ON | **DENY** |
| 4 | **ajena** | ON | ON | ON | **DENY** |
| 5 | propia | ON | ON | **OFF** | **DENY** |

El caso 2 es el que exige que las dos capas sean **hechos separados**: la concesión histórica se
conserva y el acceso se deniega igual.

## 3. Lo que hay que comprobar en cada denegación

Denegar no basta: hay que comprobar que **no pasó nada más**.

```
sin mutación en la base
sin cambio de saldos
sin evento de flujo
sin notificación de P-14
sin envío a SAP
sin registro de auditoría de éxito
```

## 4. Lo que no se prueba con rutas de detalle

`§77` y `§78` del encargo tienen razón y aquí es literal: probar que
`GET /lots/{ajeno}` devuelve `404` **no demuestra aislamiento**. Hay que probar:

| Superficie | Qué comprobar |
|---|---|
| Listados | `GET /lots`, `GET /operations` devuelven **solo** las unidades efectivas |
| Contadores | `X-Total-Count` cuenta solo lo visible |
| Agregados | los 14 KPI y los 2 paneles suman solo lo visible |
| Buscadores | los 22 `search` devuelven solo lo visible |
| Exportación | hereda del listado, pero se comprueba |
| Notificaciones | el destinatario solo recibe de sus unidades |
| Tareas de fondo | no producen sobre módulos apagados |

## 5. Ciclo de vida del módulo

```
habilitar        → acceso concedido
usar             → datos creados
DESHABILITAR     → acceso denegado
                 → LOS DATOS SIGUEN AHÍ
                 → la concesión al usuario SIGUE AHÍ
rehabilitar      → acceso restaurado sin reconfigurar nada
```

Y el mismo ciclo para la concesión al usuario, por separado.

## 6. Sensibilidad que exigiría `GA-REM-016 AC13`

```
retirar el filtro de módulo en listados     → los tests de listado deben FALLAR
retirar el filtro en agregados              → los de KPI deben FALLAR
mutar la intersección a unión               → el caso 2 debe FALLAR
retirar el filtro de empresa                → el caso 4 debe FALLAR
conceder por rol en vez de por módulo       → el caso 3 debe FALLAR
```

## 7. Lo que esta matriz no es

Un plan de pruebas, no pruebas. Nada de esto se ha escrito ni ejecutado: **esta tanda es
auditoría**. Queda como insumo de la spec futura.
