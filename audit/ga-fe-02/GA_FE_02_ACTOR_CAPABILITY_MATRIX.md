# GA-FE-02 · ACTOR CAPABILITY MATRIX

Autoridad **por permiso**, nunca por nombre de rol (`OD-09 §3.1`, `GA-REM-002`).
Permisos relevantes: `business_units:read` (R) · `:update` (U) · `:create` (C) · `:delete` (D) ·
`masters:read` (MR, para el selector de empresas) · `users:read` (UR, solo afecta a la pantalla
de usuarios preexistente).

| Capacidad → | Ver empresa efectiva | Cambiar empresa | Ver unidades empresa | Habilitar/deshabilitar | Ver concesiones de usuario | Ver candidatos | Conceder | Revocar |
|---|---|---|---|---|---|---|---|---|
| **Super Administrador** (comodín `*`) | ✅ (efectiva o «sin seleccionar») | ✅ `POST /switch-company` (único con derecho) | ✅ | ✅ | ✅ | ✅ | ✅ a otros · ❌ a sí mismo (`OD-15.a`) | ✅ |
| **Administrador de Accesos** (rol sembrado: exactamente R·U·C·D) | ✅ (su empresa) | ❌ 403 backend | ✅ R | ✅ U | ✅ R | ✅ C (superficie de candidatos — no tiene `users:read`) | ✅ a otros · ❌ a sí mismo | ✅ D | 
| **Administrador de Empresa** (rol de inquilino con `users:read`; **no gobierna unidades** salvo concesión explícita de permisos) | ✅ | ❌ | Solo si tiene R | Solo si tiene U | Solo si tiene R | Solo si tiene C | Solo si tiene C | Solo si tiene D |
| **Contraloría** (rol transversal de control) | ✅ | ❌ | **No por rol** — su visibilidad de control no administra unidades (`OD-09 §3`, `OD-16 §7`); solo con permiso explícito `business_units:*` | ❌/solo permiso | ❌/solo permiso | ❌/solo permiso | ❌/solo permiso | ❌/solo permiso |
| **Usuario normal de empresa** | ✅ (su empresa) | ❌ | ❌ (403 sin permiso) | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Actor global (super admin) sin empresa seleccionada** | "sin seleccionar" (`effective_company_id:None`) | ✅ puede elegir | ❌ **fail-closed (403)** | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 |
| **Usuario zero-BU** (autenticado, sin unidades efectivas) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

## Reglas transversales

```
G1  La UI muestra solo acciones que el permiso REAL autoriza; el backend sigue denegando
    cualquier petición manipulada (la ocultación no es seguridad — AC-UBU-11c/13).
G2  Auto-concesión: la UI no la ofrece (el actor se excluye de los candidatos por contrato);
    la petición directa recibe 403 del servidor (control negativo obligatorio).
G3  Objetivo de concesión = usuario activo de la MISMA empresa efectiva; otro caso → 404.
G4  Unidad apagada: habilitación visible con su estado OFF; concesión nueva → 409 del backend
    (la UI refleja la regla, no la esconde ni la reinterpreta).
G5  Actor global sin contexto: las pantallas GA-FE-02 no cargan unión de empresas: muestran
    "sin empresa seleccionada" y no ofrecen mutaciones (OD-14.d).
G6  Habilitar/deshabilitar ≠ conceder/revocar: acciones visualmente separadas, permisos
    distintos, efectos disjuntos (OD-16.d).
```

## Superficies por actor (descubribilidad)

| Actor | Entrada de menú `Acceso por unidad` | Ruta directa `/admin/unit-access` | Acción "Unidades de negocio" en `/users` |
|---|---|---|---|
| Super Administrador (situado) | visible | permitida (guard admin + permiso) | visible (tiene `users:read`) |
| Administrador de Accesos | visible | permitida | no aplica (la página `/users` le exige `users:read`, que no tiene) |
| Actor con solo `business_units:read` | visible (solo lectura; sin acciones de mutación) | permitida (solo lectura) | no aplica sin `users:read` |
| Usuario sin permisos `business_units:*` | **no visible** | denegada por guard | sin acción |

Evidencia esperada por fila: pruebas de navegación (AC-NAV-01…04) + control negativo directo a
API en piso autenticado (AC-UBU-13) o piso backend ya certificado como respaldo (se declara la
frontera si las credenciales faltan).
