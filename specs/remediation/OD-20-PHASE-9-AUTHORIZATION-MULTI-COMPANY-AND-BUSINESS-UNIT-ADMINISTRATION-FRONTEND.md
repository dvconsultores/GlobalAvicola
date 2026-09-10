# `OD-20` · FASE 9 AUTORIZADA — ADMINISTRACIÓN MULTI-EMPRESA Y DE UNIDADES DE NEGOCIO EN EL FRONTEND

## Metadata
| Campo | Valor |
|---|---|
| ID | `OD-20` |
| Tipo | **Decisión de propietario** (autorización de alcance) |
| Fecha | 2026-09-11 |
| Origen | **Autorización explícita del propietario** (prompt «GA-FE-02», 2026-09-11). No es implícita, ni inferida, ni una recomendación: es una declaración. |
| Estado | **APROBADO (APPROVED)** · `VIGENTE` |
| Alcance | Tranche `GA-FE-02`: experiencia administrativa multi-empresa + administración de Business Units por empresa + asignación de Business Units a usuarios + contexto de empresa mínimo + E2E autenticado desplegado |
| Preserva | `OD-09` · `OD-11` · `OD-14` · `OD-15` · `OD-16` · `GA-REM-040` (fases 1–8 certificadas) · `ENV-01` |
| No resuelve | `BU-D10` · `BU-D05` · `BU-D07` · `R-124`/`AOD-06` · ningún `AOD` pendiente |

```
FASE 9: FROZEN → AUTORIZADA (solo GA-FE-02)
GA-FE-03: NO autorizada aquí
```

---

## 1. Declaración

El propietario autoriza formalmente el inicio de la **fase 9** de `GA-REM-040`, limitada a la
tranche **`GA-FE-02`**: construir en el frontend la experiencia administrativa mínima
multi-empresa y de unidades de negocio, usando los contratos de backend ya certificados
(fases 1–8 de `GA-REM-040`), y desplegarla por la cadena normal para su certificación funcional
autenticada.

```
ADMINISTRAR EMPRESA Y UNIDADES   ≠   OPERAR LA CADENA PRODUCTIVA
GA-FE-02 administra. GA-FE-03 navegará.
```

## 2. Alcance autorizado (exacto)

1. **Experiencia administrativa multi-empresa** — operar el plano de control en el contexto de
   una empresa (`OD-11`, `OD-14`).
2. **Visibilidad de la empresa efectiva** — el actor debe poder saber en qué empresa está
   administrando; sin ambigüedad de inquilino.
3. **Selección / cambio de empresa** — reutilizando `POST /api/v1/switch-company` (contrato
   existente; Super Administrador), con refresco de contexto de las superficies de inquilino.
4. **Administración de Business Units de la empresa** — las **cuatro** unidades
   (`grandparent` · `breeder` · `hatchery` · `broiler`), estado habilitada/deshabilitada por
   empresa, sobre `GET /api/v1/business-units` + `PATCH …/{code}/enable|disable`
   (`business_units:read` / `business_units:update`).
5. **Concesión / revocación de unidades a usuarios** — ver concesiones de un usuario, asignar,
   revocar, con segregación (`OD-15`), sobre `GET /users/{id}/business-units`,
   `GET /business-units/{code}/grant-candidates`, `POST /users/{id}/business-units`,
   `DELETE /users/{id}/business-units/{code}` (`business_units:read|create|delete`).
6. **Navegación administrativa mínima** — las nuevas superficies deben ser descubribles desde
   la interfaz normal por actores autorizados, guardadas por **permiso**, nunca por nombre de
   rol. No es la navegación dinámica global (esa es `GA-FE-03`).
7. **Responsive web** de los flujos administrativos incluidos.
8. **Frontend + contrato backend + runtime desplegado + E2E autenticado** — la certificación
   funcional exige flujo autenticado real; sin credenciales autorizadas el estado máximo es
   `DEPLOYED_IMPLEMENTATION_COMPLETE / FUNCTIONAL_CERTIFICATION_BLOCKED_AUTH`.
9. **Paquete de aceptación del propietario** (`GA_FE_02_OWNER_UAT.md`).

## 3. Modelo de backend preservado (no se toca)

```
CompanyBusinessUnit(company_id, business_unit_id, is_enabled)   activación comercial — OD-16.b/e
user_business_units (concesión viva/revocada)                    acto operativo — OD-09/OD-15
RBAC (módulos y acciones)                                        capacidad de software — GA-REM-002
```

- **La seguridad la resuelve el backend.** El frontend solo refleja capacidades por permiso.
- **Encender ≠ conceder** y **conceder ≠ permitir**: invariantes `OD-16.d/f` intactos.
- **Apagar prevalece sobre la concesión** (`OD-16.e`) y **no borra** concesiones.
- El frontend **no inventa** semántica nueva de ciclo de vida de concesiones.

## 4. `BU-D10` permanece `PENDING_RATIFICATION`

Lo que ocurre con una concesión histórica al **volver a encender** una unidad **no se ratifica
ni se cambia** aquí. El comportamiento provisional ya implementado (`GA-REM-040 §6.3`) se
respeta tal cual; ninguna pantalla introducirá texto o efecto que implique una resolución nueva
de `BU-D10`. Si el copy lo requiriera → `OWNER_DECISION_REQUIRED`, no invención.

## 5. Lo que esta autorización NO incluye

`GA-FE-03` · remediación completa de `R-98` / `R-119` · navegación dinámica global ·
reconstrucción del sidebar · menú productivo dinámico por BU · `R-181` (submit/reenvío) ·
`R-182` (lote: `planned_close_date` / `area_id`) · `R-147` · `R-148` · `R-164` · remediaciones
Wave B restantes · Wave C (KPI) · SAP (`P-08` sigue `BLOCKED_EXTERNAL`) · `R-153`/`AOD-25` ·
`R-177`/`AOD-24` · `AOD-23` · `B03`/`AOD-22` · `B04`/`AOD-14` · `R-156`/`AOD-20` ·
resolución `BU-D10` · rediseño completo · design system nuevo · ERP nuevo · quinta unidad
productiva · propiedad del maestro de empresas · CRUD SAP de empresas · cambios de
infraestructura de despliegue (Watchtower · Nginx · auto-deploy · CI/CD).

Si durante `GA-FE-02` aparece una de estas necesidades: **registrar, clasificar, no implementar.**

## 6. Requisito de certificación de la tranche

Para una capacidad administrativa **visible**, la tranche no cierra por `tsc` verde, ni por
Vitest verde, ni por build verde, ni por componentes existentes. Cierra por:

```
SPEC → CONTRATO BACKEND → IMPLEMENTACIÓN → DESCUBRIBILIDAD → AUTORIZACIÓN → DESPLIEGUE
→ E2E AUTENTICADO (mutación · persistencia · refresh · relogin · segundo actor ·
   control negativo) → EVIDENCIA → CERTIFICACIÓN FUNCIONAL
```

Sin evidencia de runtime autenticado puede existir `TECHNICALLY IMPLEMENTED`; **nunca**
`FUNCTIONALLY_CERTIFIED`.

## 7. Jerarquía y reglas de la tranche

```
SPEC > OWNER DECISIONS > AC > TASK > PROMPT > CURRENT CODE      ·      BACKEND > FRONTEND
```

Sin RED válido no hay claim de implementación · sin navegación no hay descubribilidad ·
sin despliegue no hay runtime · sin autenticación no hay flujo · sin persistencia no hay
mutación · sin control negativo no hay autorización · sin evidencia no hay certificación.

## 8. Efecto en el registro

- `GA-REM-040` fase 9: `TECHNICALLY READY · FROZEN` → **`AUTHORIZED`** (esta decisión); pasa a
  `IN_PROGRESS` con el primer cambio de producto de `GA-FE-02`.
- Este `OD` **no altera** ninguna decisión vigente (`OD-09`…`OD-19`) ni sustituye a `OD-16`.
- La decisión autorizó, además, los paquetes de evidencia `audit/ga-fe-02/` como registro del
  tranche (spec, matrices, evidencia, UAT).

## 9. Trazabilidad

| Cláusula | Fuente |
|---|---|
| Cuatro unidades, activación por empresa | `OD-16.a/b` · `GA-REM-040 AC-A01…A07` |
| Empresa efectiva y switch | `OD-11` · `OD-14` · `POST /switch-company` |
| Segregación de acceso (no auto-concesión) | `OD-15` · `AC-S01…S09` |
| Contratos backend | `GA-REM-040` fases 7–8 (`business_units/router.py`, `admin.py`, `service.py`) |
| Entorno desplegado compartido | `ENV-01` |
| Metodología | `GA-REM-001` (Spec Development) |
