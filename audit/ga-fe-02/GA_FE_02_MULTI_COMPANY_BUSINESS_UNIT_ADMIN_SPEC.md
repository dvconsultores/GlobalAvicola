# GA-FE-02 · SPEC — ADMINISTRACIÓN MULTI-EMPRESA Y DE UNIDADES DE NEGOCIO (FRONTEND)

**Baseline**: `cb14523` · **Tranche**: GA-FE-02 · **Autorización**: `OD-20` (fase 9, 2026-09-11)
**Metodología**: Spec Development (`GA-REM-001`) · **Tipo**: remediación de producto visible ·
**Entorno**: `ENV-01` (compartido de desarrollo/test/certificación).

---

## 1. Problema

El backend de acceso por unidad productiva está certificado (fases 1–8 de `GA-REM-040`) y sus
contratos viven en runtime, pero **el frontend no tiene ninguna superficie administrativa** para:
saber en qué empresa se administra, cambiar de empresa, configurar las unidades de la empresa o
conceder/revocar unidades a usuarios. La capacidad existe y es invisible: sin pantalla no hay
flujo; sin flujo no hay certificación funcional. Las API probadas por backend (`business_units/*`,
`switch-company`, `/me`) no tienen contraparte de interfaz.

## 2. Objetivo

Construir la **experiencia administrativa mínima multi-empresa** — contexto visible, cambio de
empresa, administración de las cuatro unidades por empresa, concesión/revocación de unidades a
usuarios y navegación mínima que las haga descubribles — sobre los **contratos backend
existentes** (cero cambios de backend), desplegada por la cadena normal, con E2E autenticado
como requisito de certificación.

## 3. Fuera de alcance (explícito)

`GA-FE-03` · navegación dinámica global · `R-98` · `R-119` (completos) · `R-181` · `R-182` ·
Wave B/C · SAP · `BU-D10` · CRUD de empresa (SAP es autoridad del maestro) · quinta unidad ·
rediseño · infraestructura de despliegue. *(Detalle exhaustivo: `OD-20 §5`.)*

## 4. Vocabulario (vinculante)

| Término | Significado | No es |
|---|---|---|
| **Módulo RBAC** | permiso de software (`business_units:update`) | unidad de negocio |
| **Business Unit** | cadena productiva (`grandparent`·`breeder`·`hatchery`·`broiler`) | módulo ni área |
| **Empresa efectiva** | la empresa sobre la que opera la petición (`OD-11`) | «todas» |
| **Habilitación** | `CompanyBusinessUnit.is_enabled` — la empresa ENCIENDE una unidad | concesión |
| **Concesión** | `user_business_units` — la empresa CONCEDE una unidad a un usuario | habilitación |
| **Efectiva** (unidad) | concedida ∧ habilitada ∧ activa — la única que autoriza | concedida |

## 5. Reglas de negocio que la UI debe representar (todas ya vigentes en backend)

```
R1  Cuatro unidades, siempre presentes en el configurador — habilitada u OFF (OD-16.b, AC-A02)
R2  ENCENDER ≠ CONCEDER — habilitar no crea ninguna concesión (OD-16.d)
R3  APAGAR prevalece sobre la concesión y NO la borra (OD-16.e, AC-A04/A05)
R4  RE-ENCENDER devuelve la efectividad de concesiones históricas — comportamiento provisional
    certificado; BU-D10 sigue PENDING_RATIFICATION y la UI NO lo resuelve (OD-20 §4)
R5  El plano de control administra una unidad APAGADA (para poder reactivarla) (OD-16, §7)
R6  Concesión: otros usuarios elegibles de la MISMA empresa efectiva; auto-concesión DENEGADA
    en servidor (OD-15.a, AC-S01…S04)
R7  Candidatos = usuarios activos de la empresa efectiva, sin el actor (contrato backend)
R8  Habilitación 403 sin empresa efectiva; candidatos 409 si la unidad está OFF (contrato backend)
R9  Autoridad por PERMISO, nunca por nombre de rol (OD-09 §3.1, GA-REM-002)
R10 Actor global sin empresa seleccionada: las superficies de inquilino fallan cerrado —
    negativa o cero filas; JAMÁS unión de empresas (OD-11.c, OD-14.d)
R11 switch-company elige inquilino; no concede unidades ni permisos RBAC (OD-14.b, OD-11 §5)
R12 Revocar es marcar (`revoked_at`), no borrar; una revocada puede volver a concederse (AC-B11)
R13 La lista `effective_business_units` es la única que autoriza algo (contrato `/me`)
```

## 6. Superficies a construir

```
S1  Indicador de empresa efectiva          Header (web y móvil) — REUSAR company.store + Header
S2  Selector de empresa                    Header dropdown para actores con switch válido (hoy
                                           solo super_admin) — REUSAR; y contextos visibles
S3  Página "Acceso por unidad"             /admin/unit-access — NUEVA
      S3a  Encabezado de contexto: empresa efectiva + aviso si no hay empresa (fail-closed)
      S3b  Cuatro tarjetas de unidad: nombre localizado (i18n `businessUnits.*`), estado
           Habilitada/Inactiva (texto + símbolo, no solo color), acción habilitar/deshabilitar
           visible solo con `business_units:update`
      S3c  Concesión por unidad: selector de unidad → lista de candidatos (username,
           display_name, ya-concedido) → acciones conceder/revocar según permisos
           `business_units:create|delete`; muestra por usuario el estado efectivo cuando aplica
S4  Panel por usuario (UsersPage)          Acción "Unidades de negocio" por fila — NUEVA
      S4a  Modal: concesiones del usuario (incluidas revocadas, `is_effective`), estado de
           habilitación de cada unidad de la empresa, concesión/revocación por unidad
S5  Navegación mínima administrativa       Entrada en sección Administración → /admin/unit-access,
           condicionada a `business_units:read` (o comodín); la ruta directa también guardada
```

**Separación visual obligatoria** (AC-UBU-04): estado de la EMPRESA (habilitada/apagada) y estado
del USUARIO (concedida/revocada/efectiva) son columnas/indicadores distintos, nunca fusionados.

## 7. Autorización de UI (principio)

- Helper mínimo de permisos de GA-FE-02: `hasPermission(p)` sobre la sesión (`/me →
  permissions[]`) + comodín. **Sin** reescritura global de navegación (eso es GA-FE-03;
  frontera `R-98/R-119` intacta).
- Ninguna autorización por nombre de rol en código nuevo.
- Ocultar acción no es seguridad: el backend sigue siendo autoridad (control negativo directo
  contra API en piso E2E/backend).

## 8. Contrato de datos (resumen; matriz completa en `GA_FE_02_BACKEND_CONTRACT_MATRIX.md`)

```
GET  /api/v1/masters/companies        masters:read           → selector de empresa (super_admin)
POST /api/v1/switch-company           titular (super_admin)  → {company_id} → TokenResponse
GET  /api/v1/me                       titular                → effective_company_id · permissions ·
                                                              company_business_units ·
                                                              granted_business_units ·
                                                              effective_business_units · company_name
GET  /api/v1/business-units           business_units:read    → [{code,name_key,is_enabled}] (las 4)
PATCH/api/v1/business-units/{c}/enable|disable  business_units:update → HabilitacionRead
GET  /api/v1/users/{id}/business-units          business_units:read   → [{code,company_id,
                                                     granted_at,revoked_at,is_effective}]
GET  /api/v1/business-units/{c}/grant-candidates business_units:create → [{user_id,username,
                                                     display_name,already_granted}]
POST /api/v1/users/{id}/business-units          business_units:create → {code} → 201 ConcesionRead
DELETE /api/v1/users/{id}/business-units/{code} business_units:delete → 200 ConcesionRead
```

Reglas de sesión: tras `switch-company` el frontend **reemplaza ambos tokens**, vuelve a pedir
`/me` y **refresca los datos de inquilino** de las superficies GA-FE-02 (AC-COMP-03/04/05).

## 9. Acceptance Criteria

### AC-COMP — contexto de empresa
`AC-COMP-01` actor autorizado ve la empresa efectiva · `AC-COMP-02` actor multi-empresa elegible
puede seleccionar una empresa válida · `AC-COMP-03` el cambio actualiza el contexto efectivo del
backend · `AC-COMP-04` todas las pantallas GA-FE-02 se refrescan a la empresa seleccionada ·
`AC-COMP-05` sin datos obsoletos de la empresa anterior · `AC-COMP-06` actor global sin empresa
seleccionada: fail closed (negativa de las superficies de inquilino) · `AC-COMP-07` empresa no
autorizada no seleccionable por petición manipulada (backend) · `AC-COMP-08` refresh/relogin
según contrato de persistencia existente.

### AC-CBU — unidades de la empresa
`AC-CBU-01` página descubrible para actor autorizado · `AC-CBU-02` muestra las cuatro unidades
canónicas · `AC-CBU-03` estado ON/OFF viene del backend · `AC-CBU-04` habilitar permitido ·
`AC-CBU-05` deshabilitar permitido · `AC-CBU-06` persiste tras refresh · `AC-CBU-07` correcto al
re-entrar · `AC-CBU-08` habilitar crea CERO concesiones · `AC-CBU-09` deshabilitar no inventa
ciclo de vida de concesiones · `AC-CBU-10` unidad OFF bloquea operación productiva incluido el
actor global (contrato backend; verificación de paridad) · `AC-CBU-11` plano de control sigue
disponible para re-habilitar · `AC-CBU-12` actor no autorizado no muta · `AC-CBU-13` mutación de
empresa ajena imposible · `AC-CBU-14` auditoría coherente (backend) · `AC-CBU-15` fallo no deja
estado visual falso.

### AC-UBU — concesiones de usuario
`AC-UBU-01` administración de concesiones descubrible · `AC-UBU-02` empresa del usuario
seleccionado clara · `AC-UBU-03` concesiones renderizan verdad del backend (incl.
`is_effective`) · `AC-UBU-04` estado empresa ≠ estado usuario (visualmente separado) ·
`AC-UBU-05` conceder a otro usuario elegible funciona · `AC-UBU-06` persiste refresh ·
`AC-UBU-07` efecto en usuario objetivo según estado de la unidad · `AC-UBU-08` revocar funciona ·
`AC-UBU-09` persiste refresh · `AC-UBU-10` usuario objetivo pierde acceso efectivo ·
`AC-UBU-11` auto-concesión denegada (UI + petición directa) · `AC-UBU-12` concesión
entre-empresas denegada · `AC-UBU-13` sin permiso denegado · `AC-UBU-14` conceder no añade
permiso RBAC · `AC-UBU-15` conceder no activa la unidad de la empresa · `AC-UBU-16` revocar no
desactiva la unidad · `AC-UBU-17` concesión + unidad OFF no implica acceso productivo ·
`AC-UBU-18` auditoría coherente · `AC-UBU-19` sin estado de falso éxito.

### AC-NAV — navegación
`AC-NAV-01` actor autorizado descubre Admin de unidades · `AC-NAV-02` actor de acceso descubre
Concesiones · `AC-NAV-03` actor no autorizado no recibe navegación accionable · `AC-NAV-04` ruta
directa protegida · `AC-NAV-05` NO se implementa menú productivo dinámico general ·
`AC-NAV-06` `R-98`/`R-119` permanecen separados.

### AC-UI — calidad
`AC-UI-01` escritorio usable (≈1440×900) · `AC-UI-02` móvil usable (≈390×844) · `AC-UI-03`
loading claro · `AC-UI-04` errores claros · `AC-UI-05` feedback de éxito · `AC-UI-06` sin
autorización por nombre de rol · `AC-UI-07` sin IDs de empresa hardcodeados · `AC-UI-08` sin
strings mágicos duplicados de unidades (un único mapeo central) · `AC-UI-09` contrato i18n
preservado (ES/EN paridad) · `AC-UI-10` lenguaje visual actual preservado.

### AC-DEP — build y despliegue
`AC-DEP-01` TypeScript 0 errores · `AC-DEP-02` Vitest verde · `AC-DEP-03` `npm run build` verde ·
`AC-DEP-04` sin relajación de tsconfig · `AC-DEP-05` push normal únicamente · `AC-DEP-06` sin
cambios de EX-01 · `AC-DEP-07` fingerprint del runtime cambia · `AC-DEP-08` marcadores GA-FE-02 en
el bundle servido · `AC-DEP-09` navegador fresco carga la nueva superficie · `AC-DEP-10` sin
errores fatales de runtime.

### AC-NR — no regresión
`AC-NR-03` `R-158`/`R-99` permanecen cerrados (tsc 0 → build → despliegue) · `AC-NR-04` cero
cambios de backend/migraciones/config de despliegue · `AC-NR-05` `R-98`/`R-119`/`R-181`/`R-182`
sin cambio · `AC-NR-06` sin auto-concesión, sin borrado de concesiones, sin resolución `BU-D10`.

## 10. Niveles de cierre (declaración explícita)

```
BACKEND CONTRACT      READY (fases 1–8 certificadas; sin cambios)
FRONTEND IMPLEMENTATION  COMPLETE / PARTIAL
DEPLOYMENT            CURRENT / STALE
AUTHENTICATED E2E     PASS / PARTIAL / BLOCKED_AUTH
OWNER UAT             PASS / PENDING / FAIL
GA-FE-02              FUNCTIONALLY_CERTIFIED  ⇔ E2E autenticado en PASS
                      FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING (si UAT pendiente)
                      DEPLOYED_IMPLEMENTATION_COMPLETE / FUNCTIONAL_CERTIFICATION_BLOCKED_AUTH
                      (sin credenciales autorizadas)
```

## 11. Trazabilidad

`OD-20` (autorización) · `OD-09/11/14/15/16` (semántica) · `GA-REM-040` (contratos y AC-A/B/S/H)
· `GA-REM-002` (RBAC) · `ENV-01` · matrices del paquete (`BACKEND_CONTRACT_MATRIX`,
`EXISTING_FRONTEND_MAP`, `ACTOR_CAPABILITY_MATRIX`, `TEST_MATRIX`) · evidencia y UAT al cierre.
