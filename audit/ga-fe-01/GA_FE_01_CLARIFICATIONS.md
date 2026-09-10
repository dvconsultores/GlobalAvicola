# GA-FE-01 · CLARIFICATIONS

**2026-09-10** · investigaciones previas a escribir los AC (§13/§14 del encargo). Ninguna
requiere decisión del propietario.

---

## C-01 · `AuditPage.tsx:3` — `User`, `Database`

### Investigado
- **Uso histórico**: la línea 3 importaba `{ Shield, User, Database, RotateCcw }`; `User` y
  `Database` eran los iconos de las pestañas retiradas `by_user` y `by_lot`.
- **Commit que las retiró**: `4386f87` (2026-09-06, «fix(audit): cobertura de acciones y contrato
  de consulta»). El diff muestra la eliminación de las dos entradas de `AUDIT_TABS` **y conserva
  el import** → primer commit RED de la historia del frontend.
- **Gobernanza de la remoción**: el propio código lleva el comentario `GA-REM-032 AC11`: «Se
  retiran «por lote» y «por usuario»: no enviaban filtro alguno —una `group_by` que el backend
  nunca declaró— y mostraban todo el registro haciendo creer al auditor que estaba viendo un
  subconjunto». Documentado también en `R-82` (CERTIFIED, GA-REM-032).
- **¿Intención de restaurarlas?** No: la decisión es de gobernanza y producto (un control que
  aparenta filtrar sin filtrar). Nada del producto las reclama.
- **Tests**: no existe suite dedicada de `AuditPage`.

### Decisión
`User` y `Database` son **restos de una remoción intencional y gobernada**. Clase:
`STALE_IMPORT_AFTER_INTENTIONAL_REMOVAL`. Fix: eliminarlos del import.
**Prohibido**: restaurar las pestañas para «usar» los imports.

---

## C-02 · `LotFormPage.tsx:47` — `areas`, `setAreas`

### Investigado
- **Origen**: `950bb21` (2026-09-07, «feat(areas)», GA-REM-039/OD-08) añadió a la vez:
  `area_id` y `planned_close_date` al esquema zod, el estado `areas/setAreas`, el elemento
  `areaRes` en el destructuring, y el `Input` de `planned_close_date`.
- **Uso real**: el compilador es inequívoco — `areas` jamás se lee y `setAreas` jamás se llama
  (TS6133 sobre ambos). No hay ningún control JSX que consuma `areas`. No hay `api.get('/masters/areas')`
  en este archivo. No hay `area_id` en el payload (verificado línea a línea).
- **¿Hay AC que gobierne un selector de área en el alta de lote?** No:
  - `GA-REM-039 AC-A11` gobierna áreas **en la interfaz de maestros** y la asignación **de área al
    usuario** en la administración de usuarios — ambas implementadas (`UsersPage` + `MasterListPage`).
  - No existe ningún AC, ni en `GA-REM-039` ni en `docs/02` (cero menciones de «área»), que exija
    capturar el área en el alta de lote.
  - `lots.area_id` es un **contrato de dato del backend** (lo puebla la API; el E2E/notificaciones
    lo resuelven por él). Su captura por UI en el alta no está especificada.
- **¿Fue funcional alguna vez?** No. El commit lo dejó a medias: falta la petición 5.ª, falta el
  setter, falta el control. Nunca hubo comportamiento observable.
- **Tests**: no existe suite dedicada de `LotFormPage`.

### Decisión
`INCOMPLETE_EXISTING_FEATURE` en su parte **no gobernada para esta superficie**. Completarla
exigiría UX nueva (un selector) fuera de todo AC → **§33 del encargo: NO IMPLEMENTAR**. La
resolución que preserva el estado actual sin borrar la intención:
- eliminar **el estado muerto** `areas/setAreas` (cero comportamiento observable),
- **conservar** el campo `area_id` del esquema (traza de intención; inocuo),
- **registrar** la feature incompleta como finding distinto (candidato `R-182`; ver C-04).

---

## C-03 · `LotFormPage.tsx:85` — `areaRes`

### Investigado
- El array de `Promise.allSettled` tiene **4** peticiones (`farms`, `houses`, `genetic-lines`,
  `breeds`); el destructuring pide **5** nombres. `areaRes` (índice 4) no existe → `TS2493`; y
  además nunca se lee → `TS6133`.
- El commit `950bb21` cambió el destructuring de 4→5 **pero no añadió la 5.ª petición** (el diff
  solo toca la línea del destructuring y el array queda con 4 entradas).
- No hay ningún commit posterior que lo complete (historial del archivo tras `950bb21`: vacío).

### Decisión
`INVALID_DESTRUCTURING`. Fix: destructuring a 4 elementos. No se añade la petición de áreas: sería
parte de la feature no gobernada de C-02.

---

## C-04 · Feature incompleta detectada (no se corrige aquí)

Hallazgo distinto de los 6 errores, descubierto al clasificarlos:

```
El alta de lote CAPTURA pero NO ENVÍA:
  · planned_close_date — el formulario lo registra (Input, línea 190) y el payload lo omite
  · area_id            — el esquema lo declara; no hay control y el payload lo omite

IMPACTO (verificado contra el backend):
  · notifications/sla.py:153-159 selecciona lotes por `planned_close_date IS NOT NULL` y
    status active → un lote creado por UI NUNCA entra al aviso «lote próximo a cierre» (P-14).
  · El enrutado por área (`lots.area_id` → gerente/supervisor del área) no recibe dato de
    los lotes creados por UI.

CLASIFICACIÓN: INCOMPLETE_EXISTING_FEATURE (GA-REM-038 enm. B + GA-REM-039, wiring de frontend)
ACCIÓN GA-FE-01: NO corregir (fuera del alcance estricto) → registrar como finding nuevo
  propuesto `R-182` en el cierre, con esta evidencia.
```

---

## C-05 · Límites de la toolchain

- Node local y del Dockerfile: `node:24-alpine` + `npm` (misma familia). `package-lock.json`
  presente; **no se toca** (sin churn de lockfile, sin `npm audit fix`, sin actualizar deps).
- El typecheck de certificación se ejecuta **sin caché**: se elimina
  `node_modules/.tmp/tsconfig.app.tsbuildinfo` antes de cada corrida de evidencia.
- `tsc` local = el del lockfile (`typescript ~6.0.2`), el mismo que usa `npm run build` en Docker.

## C-06 · Verificación de que el RED es de R-158 (validez)

`npx tsc -b --noEmit` → exit 2 con **exactamente** los 6 diagnósticos, en el código actual, con
dependencias instaladas, sin fallos de instalación/red/entorno. `npm run build` falla **en la
etapa `tsc`** (el log no alcanza `vite build`). `npx vite build` aislado → exit 0. El RED es de
R-158 y solo de R-158.
