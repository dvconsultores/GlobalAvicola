# 18 — FORENSE DE GIT

No se modificó el repositorio: solo lectura (`log`, `show`, `rev-list`, `shortlog`, `branch`, `tag`).

## 1. Panorama

| Métrica | Valor |
|---|---|
| Commits totales | **171** |
| Rango temporal | 2026-06-23 21:33 → **2026-07-08 20:35** (15 días) |
| Ramas | 1 (`main`) + `origin/main` |
| Tags | **0** |
| Merges | **0** |
| Pull requests | **0** (deducido de la ausencia total de merges) |
| Autores | `Maria` (157), `dvconsultores` (14) |
| Último commit | `bfccdfb` — "fix: habilitar SAP en produccion y corregir filtro company_id para super admins" |
| Días sin actividad desde el último commit | ~56 (auditoría al 2026-09-02) |

### Distribución diaria

```
2026-06-23  ██████████                    9
2026-06-24  ████████████████████████████ 28
2026-06-25  ██████████████               14
2026-06-26  ██████████                   10
2026-06-27  ██████████████████████████   26
2026-06-28  █████████████████████████████ 29
2026-06-29  ████████████████████████████████████████ 40
2026-06-30  █████                         5
2026-07-01  ███████                       7
2026-07-03  ██                            2
2026-07-08  █                             1
```

Un pico de 40 commits en un solo día (2026-06-29) y **156 de los 171 commits concentrados en 7 días**. Es un patrón de desarrollo intensivo asistido por agente, no de un ciclo de ingeniería con revisión.

### Naturaleza de los commits

```
fix ......... 51  (30 %)
feat ........ 37  (22 %)
docs .........  9
chore ........  4
audit/certify   4
test .........  3
refactor .....  3
otros ....... 60  (mensajes sin prefijo convencional, mayoritariamente en inglés a partir del 2026-06-28)
```

**Los `fix` superan a los `feat`.** De los 51 `fix`, al menos **24 son de UI/dark mode/contraste** y **9 de errores de compilación o build de Docker** — trabajo de corrección que un CI habría evitado.

## 2. Hallazgo forense principal: el commit inicial

```
3c93440  2026-06-23 21:33  "first commit"
         227 archivos, 32 954 inserciones
         incluye simultáneamente:
           docs/            17 documentos de especificación
           specs/            7 artefactos de Spec Kit
           backend/app/     todos los módulos de dominio
           frontend/src/    todas las páginas y componentes iniciales
           tests/           4 suites E2E
           .github/, .specify/, docker-compose, Makefile
```

**Consecuencia:** para todo lo contenido en ese commit —arquitectura, 25 tipos de evento, workflow de revisión/aprobación, integración SAP, auditoría, 47 tablas— **Git no puede demostrar ni refutar la precedencia de la spec sobre el código**. Se clasifica `NO_TRACEABILITY`, no "sin spec": las specs existen y son coherentes, pero el orden temporal es indemostrable.

Todo el análisis de Spec Development se apoya, por tanto, en los **170 commits posteriores**, donde sí hay resolución temporal.

## 3. Línea de tiempo por fases

| Fase | Rango | Commits | Naturaleza |
|---|---|---|---|
| **F0 — Volcado inicial** | 06-23 21:33 | 1 | sistema completo + specs en un commit |
| **F1 — Estabilización de CI/Docker** | 06-23 16:35→19:05 *(`dvconsultores`)* | 8 | workflows, docker-compose, dependencias |
| **F2 — Especificación y Fase 8 (spec-first real)** | 06-24 01:56→03:51 | 8 | i18n, auditoría documental, **tasks Fase 8 (02:55) → Sprints A-D (03:25-03:51)** |
| **F3 — Auto-auditoría y remediación** | 06-24 04:18→05:58 | 5 | "16 hallazgos" → "RE-CERTIFICACIÓN APROBADO" |
| **F4 — Feature flags y producción** | 06-24 15:11→21:20 | 12 | flags, restricciones móvil/web, **`9004f3a`: CI solo en PR** |
| **F5 — Rediseño UI y dark mode** | 06-25 → 06-28 | 45 | 24 commits de dark mode + cambio de paleta + reversión |
| **F6 — Profundización funcional** | 06-26 22:30 → 06-27 05:51 | 20 | formularios por tipo de evento, multi-compañía, validadores, alertas, evidencias, trazabilidad |
| **F7 — Rediseño mobile "atenea"** | 06-27 14:52 → 06-28 06:58 | 22 | navegación multinivel, hubs en grilla |
| **F8 — SearchSelect y cobertura operativa** | 06-28 21:30 → 06-29 07:20 | 24 | 34 SearchSelect, órdenes SAP en formularios, 4 informes por etapa |
| **F9 — Auditoría, seeds y Telegram** | 06-29 19:35 → 07-03 | 22 | auditoría automática, seeds de integración, Telegram Mini App y bot, 9 fix de build |
| **F10 — Activación en producción** | 07-08 20:35 | 1 | `FEATURE_SAP_ENABLED=true` + fix de `company_id` solo en `SapService` |

## 4. Evidencia forense: spec antes del código

```
37c8f0e  2026-06-24 02:55  docs: consolidar specs en documentos canónicos
                            └─ tasks.md incorpora "Phase 8: Gap Resolution" (T-067…T-083)
                               con gaps G-01…G-13, prioridad, esfuerzo y archivos objetivo
                                              ↓  Δ = 30 minutos
d3f37f8  2026-06-24 03:25  Sprint A+B: STAGE_OPERATIONS, BirdTypeEnum.HATCHERY, design system
b3a0c56  2026-06-24 03:36  Sprint C: Lot form, transición de fase, Masters CRUD, Dashboard KPIs
2d06024  2026-06-24 03:51  Sprint D: Export Excel/PDF, Business Rules, Trazabilidad Generacional
```

Verificado inspeccionando el contenido de `tasks.md` en cada commit: `Phase 8` aparece por primera vez en `37c8f0e` y no existe en `3c93440`.

## 5. Evidencia forense: código antes de la spec

```
2d06024  2026-06-24 03:51  implementa EggBatch/ChickBatch + migración f1e2d3c4b5a6 + TraceabilityTree
                                              ↓  Δ = 14 h 47 min
ac125b2  2026-06-24 18:38  spec.md incorpora §4.9 "Generational Traceability"
                                              ↓  Δ = 3 días
8318d0f  2026-06-27 15:14  docs: documentar trazabilidad generacional (segunda documentación)
```

Verificado por conteo de la cadena "Generational Traceability" en `spec.md` a lo largo del historial: 0 en `3c93440`, `37c8f0e`, `56cbaf8` y `b2c3f3c`; 1 a partir de `ac125b2`.

## 6. Evidencia forense: spec en el mismo commit que el código

```
b2c3f3c  2026-06-24 15:11  feat: feature flags dev/prod + fix npm ci lock sync + SAP conditional routing
                            ├─ backend/app/config.py     → FEATURE_SAP_ENABLED, FEATURE_RATE_LIMIT_ENABLED
                            ├─ backend/app/main.py       → routing condicional de SAP
                            └─ specs/.../spec.md         → §14 completo (379 → 458 líneas)
```

## 7. Introducción de artefactos clave

| Artefacto | Commit | Fecha | ¿Spec previa? |
|---|---|---|---|
| `backend/app/lots/models.py` | `3c93440` | 06-23 21:33 | indemostrable |
| `backend/app/operations/validators.py` | `3c93440` | 06-23 21:33 | indemostrable |
| migración `f1e2d3c4b5a6` (trazabilidad) | `2d06024` | 06-24 03:51 | tarea sí, spec no |
| `frontend/src/components/ui/SignaturePad.tsx` | `0b8a6b7` | 06-27 05:51 | **no** — y nunca se usó |
| `backend/app/integrations/sap/mock_adapter.py` | `0b8a6b7` | 06-27 05:51 | **no** — y no compila |
| `backend/app/audit/listeners.py` + `helpers.py` | `e357dbe` | 06-29 19:35 | spec del *qué* sí; del *cómo*, posterior |
| `frontend/src/components/ui/SearchSelect.tsx` | `b162695` | 06-28 21:30 | **no** |
| `frontend/src/hooks/useTelegram.ts` | `4c88dac` | 06-29 20:15 | **no** |
| `backend/app/integrations/telegram/bot.py` | `365050c` | 06-30 11:38 | **no** |

## 8. Refactores sin spec (§62) — `UNSPECIFIED_REFACTOR`

| Refactor | Commits | Alcance | Spec |
|---|---|---|---|
| Cambio completo de identidad visual (paleta, gradientes, glassmorphism) | `ed8f2ab`, `a1d7843` | 100 % del frontend | **ninguna** — y contradice `spec.md §6.3` |
| Introducción y eliminación del modo oscuro | 24 commits | 100 % de los TSX | **ninguna** — prohibido por la spec |
| Reestructuración de la navegación móvil (hubs en grilla, patrón "atenea") | `a9d6941`, `cddffa4`, `3fd61a0`, +17 | arquitectura de navegación del producto | **ninguna** (prompts, no spec) |
| Sustitución de `<select>` por `SearchSelect` en 34 campos | `b162695`, `8a63bc0`, `a65384a`, `11ce71b`, `3ecdb5f` | formulario principal | **ninguna** |
| Reorganización de rutas `/processes` → `/poultry` → `/menu/poultry` con redirecciones legacy | `f6f3f6c`, `1590dbb`, `2b8627e` | routing | **ninguna** |

## 9. Bugfixes fuera de spec (§63)

51 commits `fix`. **No se clasifican como incumplimiento formal**: el proyecto no tiene una regla ratificada que exija spec para bugfix (la constitución está vacía — GA-SPD-DEBT-001).

Se reportan como observación estos grupos, porque revelan la ausencia de puerta de calidad:

| Grupo | Commits | Lectura |
|---|---|---|
| Errores de compilación / build en `main` | `51680d8`, `fcb57a7` (**31 errores TypeScript**), `ae6d981`, `62bffa0`, `52cf1f8`, `5f82c41`, `81a84db`, `8469875`, `3302cfe` | 9 commits para arreglar lo que un CI en `push` habría bloqueado |
| Contraste y dark mode | 24 commits | trabajo generado por un refactor no especificado |
| Navegación móvil | ~20 commits | iteración sobre prompts en lugar de spec |
| Columna inexistente en producción | `bc40413` "columna total_count no existe en operational_events" | migración desalineada con el servidor |

## 10. Módulos abandonados / código huérfano detectado por Git

| Elemento | Introducido | Estado hoy |
|---|---|---|
| `SignaturePad` | `0b8a6b7` (06-27) como "firma digital" | 0 usos en páginas; solo su test |
| `mock_adapter.py` | `0b8a6b7` (06-27) como "mock SAP" | no compila; 0 importadores |
| `DarkModeToggle` + `theme.store` | `fe4580a` (06-25) | funcionalidad eliminada en `8940d9e`; los archivos permanecen |
| `tests/` en la raíz | `3c93440` | sin configuración de Playwright que los ejecute |
| `services/` + `hooks/` del frontend | `3c93440` | 21 módulos sin consumidor |
| Tabla `reversals` | migración `bfcc893f581a` | 0 referencias |

## 11. Autoría y patrón de trabajo

| Autor | Commits | Perfil |
|---|---|---|
| `Maria <maria@montessori.local>` | 157 | desarrollo funcional, specs, auditorías, rediseños |
| `dvconsultores` | 14 | CI/CD, docker-compose, Telegram, ajustes de dependencias |

No se atribuye responsabilidad a personas (§86). El patrón dominante —commits directos a `main`, sin PR, sin revisión, con auto-certificación en el mismo hilo— es un problema **de proceso**, no de individuos.

## 12. Conclusión forense

1. **Existe evidencia real de Spec Development** en una ventana concreta (Fase 8, 2026-06-24), con delta spec→código de 30 minutos.
2. **La línea base es indemostrable** por el volcado inicial: ~90 % del sistema no es trazable temporalmente.
3. **A partir del 2026-06-25 el proceso se degrada**: el trabajo pasa a guiarse por prompts de UI, con refactores masivos no especificados, una violación explícita de la spec y 12 funcionalidades sin autorización documental.
4. **La decisión de mover el CI a `pull_request` (`9004f3a`, 2026-06-24) en un repositorio sin pull requests** es el punto de inflexión que eliminó toda puerta de calidad; explica los 9 commits de "fix build", los 31 errores de TypeScript en `main` y la supervivencia de 12 defectos P0.
