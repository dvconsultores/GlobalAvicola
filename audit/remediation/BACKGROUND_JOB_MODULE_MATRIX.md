# TAREAS DE FONDO FRENTE A LA UNIDAD DE NEGOCIO

Auditoría del 2026-09-07 · **solo lectura**

---

## 1. Qué corre solo hoy

Una sola tarea, introducida por `GA-REM-038`:

```
app/notifications/sla.py · vigilar_revisiones_pendientes()
  cada 3600 s, desde el `lifespan` de la aplicación
  → evaluar_revisiones_vencidas()
  → evaluar_lotes_proximos_a_cierre()
```

No hay `cron`, ni `Celery`, ni `Redis`, ni cola. Se comprobó explícitamente.

## 2. La matriz

| Job | Unidad | Company Scoped | Runs for Disabled Module? | Risk |
|---|---|:--:|:--:|:--:|
| `evaluar_revisiones_vencidas` | derivable vía `lot_id`, nulable | **no filtra por empresa: recorre todas** | **sí, correría** | **P1** |
| `evaluar_lotes_proximos_a_cierre` | `Lot.bird_type` | **no filtra: recorre todos los lotes activos** | **sí, correría** | **P1** |
| Reintento SAP (`retry_failed`) | multi | por petición, con sesión | n/a | P2 |
| Escuchadores de auditoría | transversal | por petición | n/a | — |

## 3. El matiz importante

Los dos evaluadores **no filtran por empresa en su consulta**: recorren todas las filas y usan
el `company_id` de cada una para dirigir el aviso. Eso es correcto hoy —una tarea de sistema no
tiene sesión de nadie— y **no es una fuga**: nadie recibe un aviso de otra empresa.

Pero significa que, el día que una empresa apague «Incubadora», el evaluador seguirá
recorriendo sus lotes de incubadora y creando avisos, salvo que se le enseñe el estado de los
módulos.

```
DISABLE MODULE  ≠  DELETE MODULE DATA
```

Los datos se conservan —eso es correcto—, pero la tarea de fondo tendría que dejar de
**producir** sobre ellos.

## 4. Lo que una tarea de fondo no puede hacer

No tiene sesión, así que no puede apoyarse en «los módulos del usuario». Solo puede consultar
«los módulos habilitados de la empresa». Eso hace que el nivel 2 —habilitación por empresa— sea
imprescindible para las tareas de fondo, mientras que el nivel 3 —concesión al usuario— solo
aplica a peticiones con sesión.

Es una razón arquitectónica concreta para **no fundir los dos niveles** en un solo modelo.
