# MASTER FRONTEND + RUNTIME GAP MATRIX

**2026-09-10** · base `3808ed5` · versión machine-readable: `MASTER_FRONTEND_RUNTIME_GAP_MATRIX.csv` (generada por `generate_gap_matrix.py` — sin discrepancia con esta tabla).

Regla: **exactamente un estado primario por capacidad**. `BLOCKED_AUTH` no es estado: es fila pendiente de la fase autenticada, contada aparte. `SECONDARY_GAPS` no altera el primario.

## Conteo (invariante)

| Estado | N.º | Capacidades |
|---|:--:|---|
| IMPLEMENTED_AND_VISIBLE | 0 | — (ninguna capacidad cumple la puerta completa sin evidencia autenticada) |
| IMPLEMENTED_BUT_NOT_EXPOSED | 1 | CAP-SES-05 (selector de empresa) |
| FRONTEND_MISSING | 7 | CAP-ADM-03 · CAP-ADM-04 · CAP-ADM-05 · CAP-ADM-06 · CAP-ADM-07 · CAP-OPS-08 · CAP-OPS-09 |
| DEPLOYMENT_STALE | 13 | CAP-ADM-09 · CAP-BU-02 · CAP-BU-03 · CAP-OPS-02 · CAP-OPS-04 · CAP-OPS-05 · CAP-OPS-06 · CAP-MAS-01 · CAP-MAS-02 · CAP-MAS-03 · CAP-AUD-01 · CAP-NOT-01 · CAP-ERR-01 |
| BROKEN_FLOW (primario) | 0 | — (3 rupturas de contrato vigentes son secundarias de filas stale, ver abajo) |
| OWNER_DECISION_REQUIRED | 2 | CAP-ADM-02 (R-124) · CAP-BU-04 (R-153/AOD-25) |
| **TOTAL CLASIFICADO** | **23** | |
| BLOCKED_AUTH (pendiente, fuera de la suma) | 15 | CAP-SES-01…04 · CAP-ADM-01/08/10 · CAP-BU-01 · CAP-OPS-01/03/07/10/11/12/13 |
| **TOTAL user-visible** | **38** | 23 + 15 |

## Las 7 filas FRONTEND_MISSING (el "product shell" que falta)

| ID | Capacidad | Backend | Por qué falta |
|---|---|---|---|
| CAP-ADM-03 | BU por empresa (habilitar/deshabilitar) | ✅ desplegado | fase 9 congelada; 0 referencias en frontend |
| CAP-ADM-04 | BU por usuario (conceder/revocar) | ✅ desplegado | fase 9 congelada; 0 referencias |
| CAP-ADM-05 | Bandeja de clasificación pendiente | ✅ desplegado | fase 9 congelada |
| CAP-ADM-06 | Navegación adaptada a permisos/unidades | ✅ (sesión fase 8) | menú estático; 0 `hasPermission`; `ProtectedRoute.roles` muerto |
| CAP-ADM-07 | Estado «sin unidades» (zero-BU) | ✅ | no existe superficie |
| CAP-OPS-08 | Envío/reenvío explícito a revisión | ✅ desplegado | servicio sin llamadores; **R-181 (nuevo)** |
| CAP-OPS-09 | Pantalla de reverso | ✅ desplegado | aplazada a fase 9 (gobernado) |

## Las 13 filas DEPLOYMENT_STALE (todo entregado y congelado por R-99)

Artefacto servido: generación **2026-09-05 14:09:27 GMT** (`index-D5dwMXuP.js`). Local: `index-Cl0MIg8E.js`.

| ID | Capacidad | Commit local | Marcador bundle (deployed→local) |
|---|---|---|---|
| CAP-ADM-09 | Roles y permisos | `fd5a389` (09-06) | `/roles` 1→7; ruta ausente del router servido; **sin enlace de navegación ni en local (sólo URL)** |
| CAP-MAS-01 | Maestros (7 nuevos + ediciones) | `0a44706` (09-06) | `/masters` 30→39 |
| CAP-MAS-02 | Áreas | `950bb21` (09-07) | `areas` 2→3 |
| CAP-MAS-03 | Curvas de peso | `99e874f` (09-06) | `/weight-curves` 0→6 |
| CAP-AUD-01 | Auditoría — filtros reales | `4386f87` (09-06) | (el commit que rompió el build) |
| CAP-NOT-01 | Notificaciones internas | `a2e21da`/`846b1bf` (09-07) | `/notifications` 0→3 |
| CAP-ERR-01 | Denegación ≠ vacío | `e75f168` (09-08) | patrón antiguo persiste |
| CAP-OPS-05 | Agua (B05) | `72600f1` (09-09) | `water_liters` 1→2 |
| CAP-BU-02 | Importación de abuelas | `2323d0c` (09-10) | `import_plan` 0→1 |
| CAP-OPS-02 | Recepción reproductoras B01/B02 | `a759a17` (09-10) | `dead_on_arrival` 0→1 |
| CAP-OPS-04 | Nacimiento B13/R-170 | `c653ff8` (09-10) | `chicks_healthy` 0→1 |
| CAP-BU-03 | Catálogo incubadora | `64dff76` (09-10) | — |
| CAP-OPS-06 | Despacho fértil (R-172/174) | `64dff76` (09-10) | — |

### Rupturas de contrato VIGENTES en el runtime compartido (secundarias, P1)

El backend del runtime **ya está nuevo** y la interfaz servida es la generación 09-05. Resultado, verificado por código:

| Flujo | Regla | Efecto hoy en el runtime |
|---|---|---|
| Recepción de reproductoras | `BR-20`: exige `received_total` + `dead_on_arrival` + `rejected_on_arrival` | La UI antigua no los declara → **400** |
| Nacimiento en incubadora | `BR-21`: exige `chicks_healthy`/`chicks_weak`; prohíbe fila «total» | La UI antigua no los envía y duplica el total → **400** |
| Importación de abuelas | `BR-22`: exige `extra_data.import_plan` tipado | La UI antigua enviaba cuatro claves sueltas → **400** |

Estos tres son los flujos centrales de Reproductoras, Incubadora y Progenitoras: **hoy no se pueden registrar desde la interfaz servida**. No se remedia aquí (auditoría); se eleva como consecuencia crítica de R-99.

## Las 15 bloqueadas por credenciales

Sesión/perfil (4) · Catálogo de empresas · Usuarios · Rol en formulario · Entradas productivas 4 unidades · Recepción general P-01 · Control diario P-02 · Ciclo P-07 · Lotes P-06 · Evidencias · Dashboard/KPI · SAP.

Único hueco: verificación autenticada contra el runtime. Bloqueo: `AUTHENTICATED_RUNTIME_BLOCKER` (§38). Cuentas necesarias: Super Admin · Administrador de Accesos · Supervisor · Operador · Contraloría · usuario multiempresa · usuario zero-BU; empresas con unidades en estados mixtos (ON/OFF) y concesiones mixtas.

## Precedencia aplicada (ejemplos verificables)

- **Selector de empresa**: existe (`company.store.ts` + Header) y está desplegado; no es stale → `IMPLEMENTED_BUT_NOT_EXPOSED` (exposición condicionada).
- **Roles**: local completo + runtime antiguo → `DEPLOYMENT_STALE` (la regla 2 precede a la 5; el flujo no está "roto" en local).
- **BU por empresa**: sin frontend suficiente en ninguna capa → `FRONTEND_MISSING` (regla 3).
- **Empresas CRUD**: expectativa indefinida (SAP vs local) → `OWNER_DECISION_REQUIRED` (regla 1).
