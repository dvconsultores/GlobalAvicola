# GA-FE-01 · DEPLOYMENT MARKERS

Marcadores **estables** que distinguen la generación servida (09-05) del frontend actual. Son
literales de cadena que sobreviven a la minificación (rutas de API, claves de campo) y pertenecen
a capacidades entregadas tras el congelamiento.

## Tabla (medida 2026-09-10, pre-fix)

| ID | CAPACITY | Marker (literal exacto) | ENTRY runtime | LOCAL (pre-fix) | ¿Cómo se detecta? | ¿Por qué es estable? |
|---|---|---|---|---|---|---|
| M1 | Roles y permisos | `permissions-catalog` | **0** | **1** | grep sobre bundle JS | endpoint literal `/roles/permissions-catalog` (no puede desaparecer sin borrar la llamada) |
| M2 | Áreas (maestro + usuarios) | `masters/areas` | **0** | **1** | grep | ruta de API literal |
| M3 | Notificaciones (bandeja/contador) | `notifications/unread-count` | **0** | **1** | grep | ruta de API literal |
| M4 | Curvas de peso (carga/evaluación) | `weight-curves` | **0** | **6** | grep | rutas de API (master + servicio) |
| M5 | Plan de importación Progenitoras | `import_plan` | **0** | **13** | grep | clave del contrato `extra_data.import_plan` + i18n |
| M6 | Cuadre de recepción (B01) | `dead_on_arrival` | **0** | **3** | grep | clave de campo del contrato BR-20 |
| M7 | Sanos/débiles al nacer (B13) | `chicks_healthy` | **0** | **2** | grep | clave de campo del contrato BR-21 |
| — | (cordón de control) | `switch-company` | 1 | 1 | grep | **no distinguen generación** — presente en ambas desde jun-2026; se usa como control negativo |

## Criterio de éxito post-despliegue (AC-R99-07)

```
Los marcadores M1–M7 deben estar PRESENTES en el bundle servido tras el despliegue
(presencia ≥ 1; los conteos pueden variar entre builds por la minificación y NO se comparan 1:1
contra el local).
```

## BR-20 / BR-21 / BR-22 — paridad estática (no E2E)

| Contrato | Marcadores del frontend actual | Lectura |
|---|---|---|
| BR-20 (recepción reproductoras) | M6 `dead_on_arrival` (+ `rejected_on_arrival`) | el contrato actual llega al runtime → desaparece el 400 por campos ausentes **a nivel de despliegue**; la ejecución funcional autenticada queda `BLOCKED_AUTH` |
| BR-21 (nacimiento B13) | M7 `chicks_healthy` (+ `chicks_weak`) | ídem |
| BR-22 (importación abuelas) | M5 `import_plan` | ídem |

Esto es **paridad estática de despliegue**: prueba que el runtime sirve el contrato del frontend
actual. **No** certifica recuperación funcional (eso exige ejecución autenticada — §58–60 del encargo).
