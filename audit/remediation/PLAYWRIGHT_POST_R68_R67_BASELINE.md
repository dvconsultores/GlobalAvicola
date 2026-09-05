# BASELINE DE PLAYWRIGHT TRAS `R-68` Y `R-67`

**2026-09-05** · suite ejecutada **sin modificar ningún test** · baseline congelado

---

## 1. Para qué se midió

`R-68` era un defecto sistémico capaz de producir falsos negativos en cualquier prueba E2E
de escritura: la respuesta salía antes de la confirmación, de modo que un test que creara
un recurso y lo consultara a continuación podía fallar sin que hubiera nada roto.

Por eso la clasificación de los 23 fallos heredados se pospuso. Primero había que eliminar
la causa sistémica; después medir de nuevo, sin tocar nada, para saber cuántos fallos eran
síntoma y cuántos defectos propios.

## 2. Resultado

```
36 pasados · 23 fallidos · 0 errores · 0 omitidos    (5,2 min · 59 casos)
```

| Proyecto | Casos | Pasados | Fallidos |
|---|--:|--:|--:|
| `procesos` (`./e2e`, `GA-REM-016`) | 21 | **21** | 0 |
| `heredada` (`./tests`) | 38 | 15 | **23** |

## 3. Comparación con el baseline anterior

| | Antes de `R-68`/`R-67` | Después |
|---|--:|--:|
| `heredada` pasados | 15 | **15** |
| `heredada` fallidos | 23 | **23** |
| Fallos eliminados por `R-68` | — | **0** |
| Fallos eliminados por `R-67` | — | **0** |
| Pendientes de clasificar | 23 | **23** |

**Los 23 fallos son exactamente los mismos casos.** No cambió ni el número ni la
composición.

## 4. Lo que eso significa, dicho sin adornos

La hipótesis de trabajo era que parte de los 23 fallos podían ser síntoma de la carrera
transaccional. **Medido, no lo eran: ninguno.** El informe de certificación de `R-68` y su
mensaje de commit anotaron esa posibilidad como algo a descartar; queda descartada.

No es un resultado decepcionante, es un resultado limpio. Ahora se sabe que los 23 fallos
son defectos con causa propia, y la clasificación que viene medirá cosas reales en lugar de
perseguir un fantasma. Ese era justamente el motivo de posponerla.

También confirma que `R-68` era invisible desde la suite E2E: su efecto aparecía en
secuencias escritura→lectura inmediata que estos tests no ejecutan. Se descubrió por el
recorrido de instalación limpia, no por Playwright.

## 5. Los 23 casos, congelados

Todos en el proyecto `heredada`. Ninguno se ha modificado.

### `tests/e2e.spec.ts` — 9 casos

| # | Línea | Caso |
|--:|--:|---|
| 1 | 18 | login redirects to dashboard on success |
| 2 | 34 | dashboard loads for authenticated user |
| 3 | 43 | mobile viewport shows bottom nav |
| 4 | 60 | farm_inspection: auto-initializes one house row on load |
| 5 | 68 | farm_inspection: shows numeric T° and H° fields (not dropdowns) |
| 6 | 82 | farm_inspection: litter condition is a select with 4 options |
| 7 | 96 | farm_inspection: can add additional house rows |
| 8 | 108 | farm_inspection: second house row can be deleted |
| 9 | 121 | farm_inspection: 375px mobile viewport renders correctly |

### `tests/operations.spec.ts` — 14 casos

| # | Línea | Caso |
|--:|--:|---|
| 10 | 12 | ProcessHubPage · should display 6 process cards |
| 11 | 20 | ProcessHubPage · should show process cards with icons and descriptions |
| 12 | 32 | ProcessHubPage · should navigate to process stage when clicked |
| 13 | 43 | ProcessHubPage · should show helpful hint at bottom |
| 14 | 66 | ProcessStagePage Timeline · should expand timeline item when clicked |
| 15 | 101 | ProcessStagePage Timeline · should allow lot selection |
| 16 | 116 | ProcessStagePage Timeline · should navigate to operation form when registering |
| 17 | 144 | Mobile Dashboard · should show welcome header on mobile |
| 18 | 152 | Mobile Dashboard · should display 3 KPI cards |
| 19 | 160 | Mobile Dashboard · should show 6 process cards on mobile |
| 20 | 168 | Mobile Dashboard · should show quick actions buttons |
| 21 | 183 | Mobile Dashboard · should navigate to operation form from quick action |
| 22 | 195 | Mobile Dashboard · should responsive grid on mobile |
| 23 | 210 | Accessibility · should have accessible process cards |

## 6. Cómo se reprodujo

```sh
bash scripts_e2e.sh
```

Base de pruebas aislada, esquema aplicado por el **entrypoint real**
(`backend/docker-entrypoint.sh`), semillas deterministas, backend en 8099 y frontend en
5199 —puertos propios para no apropiarse de servidores ajenos ya en marcha—. El entorno
compartido no interviene en ningún momento.

## 7. Qué sigue

La clasificación formal de los 23 casos, que es el trabajo pausado de `GA-REM-016`. Este
documento es su punto de partida: **23 fallos, causa propia, sin contaminación
transaccional.**

Nada de lo anterior autoriza a tocarlos todavía. `R-62` los agrupó preliminarmente como
«tests rotos por una interfaz de junio de 2026»; esa hipótesis sigue por verificar caso a
caso.

## 8. Nota de método

El arnés levanta la aplicación con el entrypoint de producción y ejecuta las 59 pruebas
contra ella. Que los 21 casos de `procesos` sigan en verde tras dos cambios en la capa
transaccional y en la regla de balance es, por sí solo, una regresión superada.
