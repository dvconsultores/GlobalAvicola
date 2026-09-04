# GA-REM-024 — EJECUCIÓN DE MIGRACIONES ANTES DE SERVIR

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-024` · **Tipo** `INFRASTRUCTURE + RELEASE SAFETY SPEC` |
| **Prioridad** | **P0 · RELEASE BLOCKER** |
| **Estado** | `SPEC_READY` |
| **Origen** | `GA-TD-013` (auditoría, `audit/16_TECHNICAL_DEBT.md:22`), reactivado por la Wave 2.5 |
| **Dependencias** | ninguna. **Bloquea** a `R-40`, `R-41` y `R-44` |
| **Detectado** | 2026-09-04 — Wave 2.5, Paso 1 |

## Problema

El despliegue de Global Avícola es:

```
push a main → build de la imagen → publicación en :latest → Watchtower → uvicorn
```

**No existe ningún paso de migración.** Se comprobó en las cinco ubicaciones donde podría
estar:

| Ubicación | Contenido | ¿Migra? |
|---|---|---|
| `backend/Dockerfile:56` | `CMD ["uvicorn", "app.main:app", …]` | **no** |
| `docker-compose.yml` (servicio `backend`) | sin `command` ni `entrypoint` | **no** |
| `app/main.py` `lifespan` | solo registra los *listeners* de auditoría | **no** |
| `.github/workflows/docker-push-backend.yml` | construye y publica; no ejecuta nada contra la base | **no** |
| Cualquier `entrypoint.sh` / script de despliegue | **no existe** (`find` sin resultados) | — |

La auditoría ya lo había registrado: *«No hay `alembic upgrade head` en el despliegue —
cada release con cambio de esquema rompe producción»* (`GA-TD-013`). Nunca recibió spec de
remediación.

### Por qué importa ahora y no antes

La Wave 2 produjo **dos migraciones de esquema** (`R-40`, `R-41`) y la Wave 2.5 necesita
**una migración de datos** (`R-44`). Ninguna de las tres llegaría a producción: el
contenedor nuevo arrancaría con el código nuevo contra el esquema viejo.

El resultado sería exactamente lo que `R-44` describe, pero peor: código que exige permisos
que la base no concede **y** un esquema al que le faltan valores de enum que el código usa.

Explica además, de forma retrospectiva, `R-40` y `R-41`: si las migraciones se aplican a
mano y de forma desigual, la deriva entre el enum de Python y el de PostgreSQL es el
resultado esperable, no una casualidad.

## Restricción de alcance — `EX-01`

El despliegue automático es `KNOWN_ACCEPTED_RISK` y **no se modifica**. La solución no puede
apoyarse en desactivar Watchtower, cambiar `:latest`, los *triggers*, `pull_policy` ni la
estrategia de publicación.

Por eso la migración se resuelve **dentro de la imagen**: un *entrypoint* que aplica
`alembic upgrade head` y solo entonces cede el control a `uvicorn`. Watchtower sigue
haciendo exactamente lo mismo; lo que cambia es lo que el contenedor hace al arrancar, que
es responsabilidad de la imagen y no de la estrategia de despliegue.

## Acceptance Criteria

| ID | Criterio |
|---|---|
| `AC01` | El contenedor aplica `alembic upgrade head` **antes** de aceptar la primera petición |
| `AC02` | Si la migración falla, el contenedor **no sirve tráfico**: termina con código distinto de cero y `restart: unless-stopped` reintenta |
| `AC03` | Arrancar dos veces seguidas no produce efectos distintos: la migración es idempotente por naturaleza de Alembic |
| `AC04` | El proceso servidor conserva el PID 1 o recibe correctamente las señales, de modo que `docker stop` sigue siendo limpio |
| `AC05` | Un despliegue sin migraciones pendientes no añade retraso perceptible |
| `AC06` | `EX-01` intacto: Watchtower, `:latest`, `pull_policy`, *triggers* y workflows sin cambios |
| `AC07` | El mecanismo queda documentado, con la ventana de indisponibilidad que introduce |

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Varias réplicas migrando a la vez | hoy hay **un** contenedor (`container_name: globalavicola-backend`), sin réplicas. Alembic además toma un bloqueo sobre `alembic_version`. Se documenta como condición vigente, no como garantía permanente |
| Una migración larga alarga el arranque | `start_period: 15s` del *healthcheck* absorbe lo razonable; una migración pesada exige ventana planificada y se documenta |
| Migración fallida deja el servicio caído | es el comportamiento **deseado**: servir con el esquema equivocado corrompe datos. Fallar ruidosamente es preferible |
| El contenedor del bot de Telegram comparte imagen | usa `command:` propio y no pasa por el *entrypoint* de la API; se verifica |

## Definition of Done

- [ ] `AC01`–`AC07` verificados · [ ] Camino de instalación nueva **y** de actualización probados · [ ] `EX-01` verificado · [ ] Certification report
