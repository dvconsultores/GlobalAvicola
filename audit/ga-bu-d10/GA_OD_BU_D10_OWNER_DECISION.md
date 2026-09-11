# GA-BU-D10 · DECISIÓN DEL PROPIETARIO — CICLO APAGAR/ENCENDER UNA UNIDAD DE EMPRESA

**ID canónico: `OD-23`** (línea GA/OD; siguiente libre tras OD-22; a distinguir de la familia `AOD-*` de Wave B) · Fecha: 2026-09-11 · Tranche: GA-BU-D10 · Estado: **RATIFIED_IMPLEMENTED_OWNER_ACCEPTED** (implementada, certificada y **aceptada por el propietario** — GA-UAT-08, decisión A, 2026-09-11; registro: `audit/ga-uat-08/GA_OWNER_ACCEPTANCE_R188_BU_D10_RECORD.md`)
Decisión explícita del propietario: **B — RE-AUTORIZACIÓN.**

## 1 · La pregunta resuelta

Cuando una empresa **apaga** una unidad de negocio y después la **vuelve a encender** (misma empresa, mismo usuario, misma unidad, sin transferencia), ¿las concesiones previas vuelven a ser efectivas solas?

## 2 · Regla de negocio canónica (ratificada)

1. **Apagar** una unidad de empresa **termina la efectividad futura** de las concesiones de usuario existentes para esa unidad, **en ese ciclo de habilitación**: las concesiones quedan **marcadas como historia** (fecha de fin), **no se borran** (auditoría e historia completas).
2. **Re-encender** NO devuelve efectividad a ninguna concesión histórica. **Ningún acceso productivo se «resucita» solo.**
3. Cada usuario que deba operar la unidad tras la reapertura requiere una **concesión nueva y explícita** de un administrador de accesos autorizado (actor ≠ usuario, misma empresa, unidad habilitada — flujo ya existente de candidatos).
4. Mientras la unidad está apagada: sin acceso productivo para nadie (OD-16 intacto, incluido el actor global) **y no se puede conceder** (regla vigente preservada: conceder no habilita).
5. La **transferencia de empresa** (OD-09.e) permanece **separada e intacta**: volver a la empresa anterior sigue exigiendo concesión nueva (regla ya ratificada; sin cambios).

## 3 · Semántica de seguridad

- Mínimo privilegio por defecto: sin resurrección silenciosa de accesos productivos.
- Separación de conceptos preservada: **habilitar una línea ≠ conceder acceso a personas**. La reapertura es un acto comercial; el acceso, operativo.
- Todo reingreso productivo renovado tiene un **acto explícito y auditable** (quién, a quién, cuándo).

## 4 · Semántica de auditoría

- Apagar/encender la unidad: se conserva la auditoría existente de configuración (`CONFIG_CHANGE`, estado anterior/nuevo).
- Las concesiones terminadas por el ciclo **quedan auditadas individualmente** (fin de concesión, usuario, unidad, causa = «unidad de empresa deshabilitada», actor, fecha) — **no** se fabrican eventos de concesión.
- Las concesiones nuevas se auditan como cualquier concesión (acto explícito).
- **Prospectiva**: la regla aplica a los apagados que ocurran bajo esta política; los estados apagados preexistentes no se reclasifican retroactivamente (sin migración), y cualquier apagado posterior —incluida una invocación idempotente del apagado— normaliza el invariante «unidad apagada bajo OD-23 ⇒ sin concesiones vivas».

## 5 · Semántica histórica

- Concesiones históricas: **PRESERVADAS** (fila + `revoked_at`); nunca borrado masivo; la historia sigue siendo consultable/auditable.
- Sin migración de datos ni de esquema (representable con el modelo vigente).

## 6 · Consecuencia de implementación

- **Brecha real**: el producto hoy implementa la conducta provisional A (auto-reactivación, `AC-A06`). Se formaliza como finding **R-188** (P2) — `GA_BU_D10_IMPLEMENTATION_GAP_R188.md`.
- Tranche técnica: SPEC → AC → RED → implementación mínima → GREEN → deploy → runtime autenticado → certificación → **UAT del propietario** (B cambia comportamiento visible de acceso).

## 7 · Fuera de alcance

OBS-UAT-01 · Wave B · Wave C/SAP · rediseño RBAC/BU · migraciones · retro-clasificación de datos históricos · cambios al ciclo de transferencia de empresa.
