# GA-BU-D10 · SPEC — CICLO DE VIDA DE LA CONCESIÓN AL APAGAR/ENCENDER UNA UNIDAD (OD-23 · B)

Estado: SPEC CONGELADA para implementación · Autoridad: **OD-23** (RATIFIED, 2026-09-11) · Finding: **R-188**

## 1 · Alcance

Comportamiento de las concesiones de usuario (`user_business_units`) cuando una **unidad de empresa** (`company_business_units`) pasa de habilitada a apagada y viceversa — **misma empresa, mismo usuario, misma unidad**. Transferencia de empresa: FUERA (OD-09.e intacta).

## 2 · Fuera de alcance

OBS-UAT-01 · Wave B/C/SAP · rediseño RBAC/BU/tenant · migraciones/retro-clasificación · nueva UI · nuevos permisos/endpoints.

## 3 · Modelo de datos (sin cambios)

`business_units` · `company_business_units(is_enabled, updated_at)` · `user_business_units(user_id, company_business_unit_id, created_at, revoked_at; única-entre-vivas)`. **Sin columnas nuevas. Sin migración.**

## 4 · Estados de ciclo (fuente de verdad)

```
viva      revoked_at IS NULL          ⇒ candidata a efectiva si habilitación ON ∧ unidad activa
histórica revoked_at con fecha        ⇒ existe, audita, NO es efectiva nunca más en ese ciclo
efectiva  viva ∧ CBU.is_enabled ∧ BU.is_active ∧ empresa actual  (resolutor, releído por petición)
```

## 5 · Semántica de APAGADO (OD-23 §2.1)

`PATCH /business-units/{code}/disable` (`fijar_habilitacion(habilitada=False)`):
1. `is_enabled=False` (como hoy; idempotente; auditoría `CONFIG_CHANGE` como hoy).
2. **Además**: TODA concesión **viva** de ESA habilitación se **marca** (`revoked_at=now`) — «terminada por el ciclo». Nunca se borra.
3. **Auditoría individual** por concesión terminada: `PERMISSION_CHANGE`/`users`, `previous=granted → new=revoked`, `new_values={target_user_id, business_unit, cause:"company_business_unit_disabled"}`. **No** se fabrican eventos de concesión.
4. Si no hay concesiones vivas: nada extra (sin eventos falsos).
5. Repetir «apagar» sobre una unidad ya apagada: sigue siendo idempotente en configuración y **normaliza** el invariante («apagada bajo OD-23 ⇒ 0 concesiones vivas»); solo se marcan las que aún estuvieran vivas.

## 6 · Semántica de ENCENDIDO (OD-23 §2.2)

`enable`: solo `is_enabled=True` (+ auditoría como hoy). **Ninguna concesión se crea ni se revive.** Las históricas siguen históricas. Los usuarios quedan sin acceso productivo hasta concesión nueva.

## 7 · Concesión nueva (re-autorización)

Flujo existente sin cambios: `POST /users/{id}/business-units` (actor ≠ usuario — OD-15.a; misma empresa; unidad **habilitada** — con OFF no se puede conceder; idempotente entre vivas; auditoría `PERMISSION_CHANGE`). Superficie: candidatos (`GET /business-units/{code}/grant-candidates`; excluye al actor; no requiere `users:read` — OD-15 §6).

## 8 · Resolutor y sesión (sin cambios, §37)

- `unidades_efectivas_por_id` (cuatro puertas) intacto: la marca de §5 lo satisface sin tocar el resolutor.
- **Relectura por petición** (sin token/caché): OFF y re-encendido surten efecto en la evaluación siguiente; sin privilegio obsoleto en sesiones vivas; refresh/relogin no alteran semántica (decisión releída). R-43/R-54 intactos.
- `/me` informa habilitadas/concedidas/efectivas + `is_effective` por concesión (proyección admin ya usa las mismas condiciones).

## 9 · Navegación

Deriva de acceso efectivo (`effective_business_units`; guards `requiresUnits`): OFF ⇒ navegación/deep-links productivos ocultos/denegados; tras re-encendido bajo B ⇒ **permanecen ocultos** hasta concesión nueva (diferencia visible vs A). Sin cambios de código frontend (0 archivos esperados).

## 10 · Access Administrator / SuperAdmin / actor global

- Access Admin: control-plane; no gana acceso productivo; puede re-conceder (candidatos); self-grant DENEGADO (se evalúa primero).
- SuperAdmin/actor global: **no evade OD-16** (OFF ⇒ DENY productivo); tras re-encendido: sin concesión no opera; las concesiones terminadas tampoco le pertenecen.
- Zero-BU: CORE por RBAC; 0 dato productivo.

## 11 · Empresa ajena / integridad

Conceder a usuario de otra empresa ⇒ 404 anti-enumeración. Terminar/marcar afecta SOLO a la habilitación de la empresa efectiva (la fila CBU lleva la empresa dentro). Sin cascadas. Sin reaparición cross-company.

## 12 · Auditoría (completa del ciclo)

| Acto | Evento |
|---|---|
| Apagar unidad | `CONFIG_CHANGE` config×1 (`previous/new`) + `PERMISSION_CHANGE` users×N (concesiones terminadas, causa declarada) |
| Encender unidad | `CONFIG_CHANGE` config×1 |
| Conceder (re-auth) | `PERMISSION_CHANGE` users×1 (`none→granted`) |
| Revocar manual | `PERMISSION_CHANGE` users×1 (`granted→revoked`) |
| Conceder duplicado | **sin evento** (no cambió nada) |

## 13 · Concurrencia (§39, patrones existentes)

RACE-01 (enable vs grant): transaccional; el grant exige habilitada ⇒ o antes del apagado (queda terminado por §5) o después del encendido (vive). RACE-02 (apagado vs petición productiva): el resolutor relee; próxima petición DENY. RACE-03 (re-enable con sesión vieja): denegado hasta concesión nueva. RACE-04 (grant×2): idempotente/única-entre-vivas. RACE-05 (grant+revoke): última transacción válida decide; nunca hay doble viva.

## 14 · Migración / datos

**Ninguna migración.** Prospectivo. Estados OFF preexistentes con vivas (2 en entorno de prueba): se normalizan en el siguiente apagado; nota residual operativa (revisión administrativa opcional) — sin cambio de datos en esta tranche.

## 15 · Criterios de aceptación (fuente única)

**BU-D10-AC01** OD-23 canonizada. **AC02** BU OFF ⇒ sin acceso productivo (nadie). **AC03** global no evade OFF. **AC04** concesión ≠ habilitación (conceptos separados; conceder no enciende; apagar no configura usuarios). **AC05** re-encendido bajo B: sin efectividad automática. **AC06** zero-BU ⊂ CORE sin dato productivo. **AC07** RBAC sigue exigido. **AC08** cross-company grant DENY. **AC09** self-grant DENY. **AC10** transferencia de empresa PRESERVADA. **AC11** `/me` efectivas coherente. **AC12** navegación = acceso efectivo. **AC13** API directa = UI. **AC14** refresh token sin acceso obsoleto. **AC15** relogin estable. **AC16** auditoría correcta (§12). **AC17** sin fuga cross-tenant. **AC18** GA-FE-02 preservado. **AC19** GA-FE-03. **AC20** GA-FE-04. **AC21** GA-FE-05..07. **AC22** R-181/182/184/185/186/187 · OD-21/22 preservados. **AC23** (añadido por SPEC) concesiones históricas consultables tras terminación (sin borrado). **AC24** idempotencia de apagado («normaliza» sin duplicar). **AC25** sin migración/borrado masivo.

## 16 · Pruebas

- Suite nueva `backend/tests/test_r188_bu_lifecycle.py` (PG/CI; skip local declarado): terminación al apagar (marca, no borra), no-reactivación al encender, concesión nueva restaura, auditoría ×N con causa, idempotencia, resolver/`/me` por estado, seguridad (self/cross), transferencia intacta.
- Actualización de pruebas de la conducta provisional (C3): `AC-A06` y `test_deshabilitar_no_borra...` reexpresadas a B; `AC-A04` conserva «no borra» (marca).
- Runtime E2E autenticado (§54-64 del encargo).

## 17 · UAT del propietario

**REQUIRED** (cambia comportamiento visible): 5 casos (§70): acceso con ON; OFF quita acceso; re-encendido NO lo devuelve; concesión nueva lo restaura; móvil/navegación reflejan efectivo. No auto-aprobada.
