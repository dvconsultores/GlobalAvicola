# FINAL FRONTEND AUDIT · INVENTARIO ORIGINAL DE CAPACIDADES

Fecha: 2026-09-11 · Snapshot histórico: 2026-09-10, base `3808ed5`, runtime previo (bundle servido `index-D5dwMXuP.js` de 09-05) · Fuente única: `audit/frontend-runtime/` + `audit/remediation/REMEDIATION_BACKLOG.md` §tranche auditoría.

## 1 · Conteos históricos (verificados)

`MASTER_PRODUCT_CAPABILITY_CATALOG.md:95-107` (invariante `23 = 0+1+7+13+2`):

```
Capacidades user-visible inventariadas ......... 38
  clasificadas ................................ 23
    IMPLEMENTED_AND_VISIBLE ..................... 0
    IMPLEMENTED_BUT_NOT_EXPOSED ................. 1   (CAP-SES-05)
    FRONTEND_MISSING ............................ 7   (CAP-ADM-03/04/05/06/07 · CAP-OPS-08/09)
    DEPLOYMENT_STALE ............................ 13  (CAP-ADM-09 · CAP-BU-02/03 · CAP-OPS-02/04/05/06 · CAP-MAS-01/02/03 · CAP-AUD-01 · CAP-NOT-01 · CAP-ERR-01)
    BROKEN_FLOW (primario) ...................... 0   (3 rupturas BR-20/21/22 secundarias de filas stale)
    OWNER_DECISION_REQUIRED ..................... 2   (CAP-ADM-02 → R-124 · CAP-BU-04 → R-153/AOD-25)
  bloqueadas por credenciales (sin estado) ...... 15  (CAP-SES-01…04 · CAP-ADM-01/08/10 · CAP-BU-01 · CAP-OPS-01/03/07/10/11/12/13)
Capacidades internas (anexo, no contadas) ....... 7
```

- **45 = 38 + 7** — «45» no es literal en la fuente (aritmética); sin discrepancia de conteo (HISTORICAL_COUNT_DISCREPANCY: NINGUNA; la cifra 45 del encargo se reconcilia como 38+7).
- Blocker de las 15: `AUTHENTICATED_RUNTIME_BLOCKER` (§38 del encargo original: sin cuentas autorizadas; `GA-REM-004` rotó las históricas; prohibido seeds).

## 2 · Filas user-visible (FVA-01…FVA-38)

IDs de auditoría asignados en orden del catálogo. «Estado histórico» = estado primario del snapshot.

| FVA | CAP | Capacidad | Dominio | Estado histórico | Blocker histórico |
|---|---|---|---|---|---|
| FVA-01 | CAP-SES-01 | Iniciar sesión / sesión con token | SES | BLOCKED_AUTH | sin cuentas |
| FVA-02 | CAP-SES-02 | Cambio de contraseña | SES | BLOCKED_AUTH | íd. |
| FVA-03 | CAP-SES-03 | Perfil de usuario (ver datos) | SES | BLOCKED_AUTH | íd. |
| FVA-04 | CAP-SES-04 | Contexto de empresa visible | SES | BLOCKED_AUTH | íd. |
| FVA-05 | CAP-SES-05 | Selector de empresa (actor global) | SES | **IMPLEMENTED_BUT_NOT_EXPOSED** | render condicionado; cuenta |
| FVA-06 | CAP-ADM-01 | Catálogo de empresas (listado) | ADM | BLOCKED_AUTH | sin cuentas |
| FVA-07 | CAP-ADM-02 | Administración de empresas (metadatos) | ADM | **OWNER_DECISION_REQUIRED** | R-124/AOD-06 (propiedad SAP vs local) |
| FVA-08 | CAP-ADM-03 | Unidades por empresa (habilitar/apagar) | ADM | **FRONTEND_MISSING** | fase 9 congelada |
| FVA-09 | CAP-ADM-04 | Unidades por usuario (conceder/revocar) | ADM | **FRONTEND_MISSING** | fase 9 congelada |
| FVA-10 | CAP-ADM-05 | Bandeja de clasificación pendiente | ADM | **FRONTEND_MISSING** | fase 9 congelada (T-040-24, condicional al diseño) |
| FVA-11 | CAP-ADM-06 | Navegación adaptada a permisos y unidades | ADM | **FRONTEND_MISSING** | menú estático; R-98/R-119 |
| FVA-12 | CAP-ADM-07 | Estado «sin unidades» (zero-BU) | ADM | **FRONTEND_MISSING** | no distinguía cero-BU de vacío |
| FVA-13 | CAP-ADM-08 | Gestión de usuarios | ADM | BLOCKED_AUTH | patrón «denegación = tabla vacía» R-122 |
| FVA-14 | CAP-ADM-09 | Roles y permisos (pantalla) | ADM | **DEPLOYMENT_STALE** | `/roles` ausente del bundle servido; sin enlace |
| FVA-15 | CAP-ADM-10 | Asignación de rol en formulario | ADM | BLOCKED_AUTH | sin cuentas |
| FVA-16 | CAP-BU-01 | Entradas productivas 4 unidades (hub+etapas) | BU | BLOCKED_AUTH | gating por unidad ausente |
| FVA-17 | CAP-BU-02 | Importación de abuelas — plan tipado | BU/grandparent | **DEPLOYMENT_STALE** | UI antigua 400 BR-22 |
| FVA-18 | CAP-BU-03 | Catálogo de incubadora (mortalidad/descarte) | BU/hatchery | **DEPLOYMENT_STALE** | bundle sin la sección |
| FVA-19 | CAP-BU-04 | Creación automática del lote de abuelas | BU/grandparent | **OWNER_DECISION_REQUIRED** | R-153/AOD-25 |
| FVA-20 | CAP-OPS-01 | Recepción de aves (P-01 general) | OPS | BLOCKED_AUTH | sin cuentas |
| FVA-21 | CAP-OPS-02 | Recepción reproductoras B01/B02 | OPS/breeder | **DEPLOYMENT_STALE** | UI antigua 400 BR-20 |
| FVA-22 | CAP-OPS-03 | Control diario de producción (P-02) | OPS | BLOCKED_AUTH | íd. |
| FVA-23 | CAP-OPS-04 | Nacimiento incubadora B13 (R-170) | OPS/hatchery | **DEPLOYMENT_STALE** | UI antigua 400 BR-21 |
| FVA-24 | CAP-OPS-05 | Consumo de agua (B05) | OPS | **DEPLOYMENT_STALE** | captura ausente en runtime |
| FVA-25 | CAP-OPS-06 | Despacho — fila fértil única (R-172/174) | OPS/hatchery | **DEPLOYMENT_STALE** | UI antigua divergente |
| FVA-26 | CAP-OPS-07 | Ciclo Revisión→Corrección→Aprobación (P-07) | OPS | BLOCKED_AUTH | R-181 secundario |
| FVA-27 | CAP-OPS-08 | Envío/reenvío explícito a revisión | OPS | **FRONTEND_MISSING** | `operationsService.submit` sin llamadores; R-181 |
| FVA-28 | CAP-OPS-09 | Pantalla de reverso (solicitar/consultar) | OPS | **FRONTEND_MISSING** | diferida a fase 9 (gobernado) |
| FVA-29 | CAP-OPS-10 | Lotes (P-06) | OPS/broiler+ | BLOCKED_AUTH | sin entrada de menú |
| FVA-30 | CAP-OPS-11 | Evidencias (subir/descargar) | OPS | BLOCKED_AUTH | volumen R-52 pendiente |
| FVA-31 | CAP-OPS-12 | Dashboard / KPI | OPS | BLOCKED_AUTH | sin cuentas |
| FVA-32 | CAP-OPS-13 | SAP — referencias/envíos | OPS/SAP | BLOCKED_AUTH | backend PARTIAL (R-112); P-08 BLOCKED_EXTERNAL |
| FVA-33 | CAP-MAS-01 | Gestión completa de maestros (19+áreas) | MAS | **DEPLOYMENT_STALE** | bundle sin los 7 nuevos ni áreas |
| FVA-34 | CAP-MAS-02 | Áreas (maestro administrable) | MAS | **DEPLOYMENT_STALE** | bundle sin áreas |
| FVA-35 | CAP-MAS-03 | Curvas de peso (carga+evaluación) | MAS | **DEPLOYMENT_STALE** | `/weight-curves` 0→6 |
| FVA-36 | CAP-AUD-01 | Auditoría — filtros reales | AUD | **DEPLOYMENT_STALE** | pestañas sin filtro en runtime |
| FVA-37 | CAP-NOT-01 | Notificaciones internas (campana) | NOT | **DEPLOYMENT_STALE** | `/notifications` 0→3 |
| FVA-38 | CAP-ERR-01 | Estados de error distinguibles | ERR | **DEPLOYMENT_STALE** | patrón antiguo en runtime |

## 3 · Filas internas (FIA-01…FIA-07)

Sin IDs CAP propios (anexo del catálogo, líneas 84-90):

| FIA | Capacidad | Estado histórico |
|---|---|---|
| FIA-01 | Enforcement RBAC en cada ruta | IMPLEMENTED |
| FIA-02 | Aislamiento por inquilino/unidad en escritura | IMPLEMENTED |
| FIA-03 | Balance de población/huevos bajo bloqueo | IMPLEMENTED |
| FIA-04 | Trazabilidad generacional / linaje | IMPLEMENTED (árbol UI bloqueado) |
| FIA-05 | Auditoría inmutable (aplicación) | PARTIAL (R-148 BD) |
| FIA-06 | Reverso interno (servicio) | IMPLEMENTED (UI → fase 9) |
| FIA-07 | Adaptador SAP (semántica) | PARTIAL / SAP_DEFERRED / BLOCKED_EXTERNAL |

## 4 · Fuentes

`MASTER_FRONTEND_RUNTIME_GAP_MATRIX.md:11-19` · `MASTER_PRODUCT_CAPABILITY_CATALOG.md:95-107,21-90` · `MASTER_FRONTEND_RUNTIME_AUDIT_EVIDENCE.md:32,48,177-199` · `AUTHENTICATED_USER_JOURNEY_MATRIX.md:109` · `REMEDIATION_BACKLOG.md:1618-1634` · addenda GA-FE-02-B/C y GA-FE-03 (reclasificaciones posteriores, preservadas sin reescribir la instantánea).
