# GA-FE-04 · RECONCILIACIÓN CANÓNICA `R-98` (cierre P-13)

**Método**: leído de fuentes canónicas, sin resumen de memoria (§11 del encargo).

## 1 · Redacción original de `R-98`

`audit/remediation/REMEDIATION_BACKLOG.md`:

> `R-98` | Ninguna pantalla oculta acciones de escritura por permiso: no hay modelo de permisos
> en el frontend | **P2 — OPEN · transversal, pertenece a `P-13`**

Y su párrafo de contexto (§ posterior al bloque de fijos `R-96/R-97`):

> «`R-98` es su residuo: al verificar `AC-FE16` se comprobó que **ninguna** pantalla de la
> aplicación oculta acciones de escritura según el permiso del usuario, porque `/me` no expone
> la lista de permisos. No es un defecto de las curvas sino transversal, y pertenece a `P-13`.
> No impide el acceso: el backend niega y la interfaz presenta la negativa.»

## 2 · AC original de la verificación que lo originó (`AC-FE16`)

`specs/remediation/GA-REM-037-GENETIC-WEIGHT-CURVES.md` §AC-FE16:

> **`AC-FE16` · La interfaz respeta `RBAC`: quien solo lee no ve acciones de escritura, y el
> backend sigue siendo la autoridad —ocultar un botón no es autorizar—.**

`audit/remediation/R-96-WEIGHT-CURVE-CAPABILITY-CERTIFICATION.md` §5, «dicho con precisión»:

> «Lo que **no** se verificó, porque no existe: ocultar botones según el permiso del usuario.
> Ninguna pantalla de esta aplicación lo hace — `/me` no expone la lista de permisos y no hay
> modelo de permisos en el frontend. Construirlo para las curvas habría creado una excepción
> incoherente con las otras diecinueve pantallas de maestros, y es trabajo de `P-13`, no de
> aquí. Queda registrado como **`R-98`**.»

Verificación ejecutable vigente: `e2e/proceso-p03-curvas-ui.spec.ts` — «AC-FE16 · sin permiso
sobre maestros no se administra ninguna curva» (control con `admin` que SÍ ve; tratamiento con
`approver` que NO lee y recibe alerta).

## 3 · Significado canónico de `P-13` y del residual

- `P-13` = **proceso «Gestión de usuarios, roles y permisos»** (`docs/02 §3.1`;
  `audit/06_PROCESS_COVERAGE`; matrices `P13_*`). El residual que GA-FE-03 dejó declarado es
  su cara **transversal intra-pantalla**: el modelo general de permisos en el frontend aplicado
  a **acciones dentro de las pantallas** (no a la navegación, que GA-FE-03 ya cerró).
- El residuo **no reclama funcionalidad nueva**: exige que las acciones de escritura ya
  existentes se oculten a quien solo lee, con el backend intacto como autoridad.

## 4 · Qué cerró cada tranche

| Tranche | Cobertura |
|---|---|
| `GA-FE-02` | `UnitAccessPage` y `UserBusinessUnitsButton` con `hasPermission` (business_units:read/update/create/delete) — **primer uso** del helper espejo de `tiene_permiso`; `/me` extendido (`AC-H11…H14`) ya expone `permissions` |
| `GA-FE-03` | Modelo de capacidades de **navegación** (`auth/navigation.ts`) + `CapabilityRoute`; cerró `R-119`; declaró `R-98 = PARTIAL` con el residuo exacto: «ocultado de acciones de escritura dentro de pantallas … pertenece al alcance de `P-13`» (`GA_FE_03_R98_RECONCILIATION.md`) |
| `GA-FE-04` | **Este cierre**: modelo de autoridad de acción (mismo vocabulario) aplicado a las acciones intra-pantalla de todas las pantallas con escritura |

## 5 · Por qué `R-98` quedó `PARTIAL` (condiciones de cierre faltantes)

1. Las acciones de pantalla de **usuarios/roles** (`users:*`), **maestros** (20 entidades +
   curvas, `masters:*`), **lotes** (`lots:*`), **operaciones** (`operations:*`), **revisión/
   aprobación** (`review:*`, `approvals:*`), **SAP** (`sap:send_sap`) y sus CTAs de estado
   vacío **seguían visibles/accionables** para actores sin el permiso de escritura.
2. No existía un **modelo de acción** compartido (solo el helper de permiso y los usos
   puntuales de GA-FE-02).
3. Faltaba la evidencia runtime autenticada de «solo lectura ⇒ sin acciones de escritura»
   fuera de la frontera de GA-FE-02.

## 6 · Condiciones EXACTAS de cierre de `R-98` (derivadas de las fuentes)

```
C1  Todo actor con SOLO lectura en una superficie NO ve/acciona controles de escritura
    de esa superficie (AC-FE16 generalizado a todas las pantallas con escritura).
C2  El backend permanece autoridad: la negativa directa de API sigue existiendo y con la
    misma semántica (ocultar ≠ autorizar).
C3  El modelo es compartido (mismo vocabulario de permisos que navegación/rutas; sin
    segundo sistema).
C4  Sin gating por nombre de rol ni por username (la autoridad es por permiso canónico).
C5  Evidencia runtime autenticada por actor + no-regresión de GA-FE-02/GA-FE-03.
```

## 7 · Dedup (`§12`)

| Finding | Relación | Efecto |
|---|---|---|
| `R-119` | Navegación/descubribilidad de menú — **CLOSED** en GA-FE-03 | No se reabre; se ejecuta regresión |
| `R-181` | `submit/resubmit` sin control UI — la funcionalidad **no existe** | Cualquier control relacionado se marca `EXCLUDED_R181` (no se implementa; no se cuenta contra R-98) |
| `R-182` | `LotForm` `planned_close_date`/`area_id` — funcionalidad fuera de alcance | Controles de ese formulario no se alteran (`EXCLUDED_R182`) |
| D-1 / D1 / F1–F4 | Certificados; frontera de datos y sesión | Solo regresión |
| `R-120` (denegación ≠ vacío) | Cerrado como capacidad (`CAP-ERR-01`); la UX de negativa se preserva | Reutilizado, no reabierto |
| `D-2`/`D-3`/`D-4` | Observaciones GA-FE-02 | Intactas (D-2 ya cerrado por GA-FE-03) |

**Conclusión**: `R-98` es el finding gobernante de este residual; **no se crea ID nuevo** para
la misma causa raíz. Los hallazgos que la certificación descubra, si fueran de otra raíz, se
registrarán aparte sin absorberlos en R-98.
