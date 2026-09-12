# GA-UAT-09 · LEDGER DEL FIXTURE — R-153 / OD-25

Fecha: 2026-09-12 · Empresa 1 · `LIMPIEZA POST-DECISIÓN PENDIENTE` (los elementos quedan **vivos** para la sesión del propietario).

## 1 · Actores sintéticos (por ID exacto — no usar búsquedas no verificadas)

| Elemento | ID | Detalle |
|---|---|---|
| Rol operador | **125** (`uat09-op-8e60c2`) | operations leer/crear/editar · lots leer/crear · masters leer · sap leer |
| Rol aprobador | **126** (`uat09-ap-8e60c2`) | review leer/revisar · approvals aprobar/rechazar · corrections leer/corregir · operations/lots/masters leer |
| Usuario operador | **181** (`uat09-op-8e60c2`) | concesión `grandparent` vigente |
| Usuario aprobador | **182** (`uat09-ap-8e60c2`) | concesión `grandparent` vigente |

Credenciales: **fuera del repo** en `~/ga_uat09_credentials.txt` (600). Se destruyen en la limpieza post-decisión.

## 2 · Contexto

- Unidad **Progenitoras (grandparent): ON** durante UAT-09 (se restaura a OFF en la limpieza post-decisión).
- OC candidata: `PO-C001-GPR-0001` (maestro SAP existente; no se creó nada).

## 3 · Datos de negocio del ejercicio

| Elemento | Resultado | Nota |
|---|---|---|
| Importación UAT | **NINGUNA** — el alta por interfaz fue rechazada (F-01); las repeticiones internas quedaron canceladas o no se crearon | el bloqueo impide el caso |
| Sondeo de recepción (verificación de alcance de F-01) | evento **97** → **cancelado** | creado solo en la sonda con `[]`; ya cancelado |
| Evento 87 (recepción retenida) | **registered** | del ledger GA-R153 (tranche anterior; retenido por R-130) — no forma parte de UAT-09 |
| Lotes de la certificación (L-GP-07/08/09, manual) | intactos | no reutilizados para UAT-09 |

## 4 · Limpieza post-decisión (checklist)

Revocar concesiones → baja de usuarios **181/182** → desactivar roles **125/126** (solo por ID exacto) → restaurar **Progenitoras OFF** → destruir `~/ga_uat09_credentials.txt` → verificar que humanos/roles legítimos quedan intactos → registrar resultado.

## 5 · Retry de certificación (F-01d/F-01e · 2026-09-13)

Fixture sintético del retry (empresa 1 · misma pareja `uat09-op`/`uat09-ap` · Progenitoras ON):

| Elemento | ID / código | Estado | Nota |
|---|---|---|---|
| Importación RED (C2d) | evento **120** | approved | creada por UI; lote 64 |
| Lote RED (sin galpón) | **64** · `L-GP-2026-10` | activo · `house_id` NULL · **sin recepción** | exhibe el bloqueo BR-08 de F-01e |
| Importación retry (C2f) | evento **121** | approved | UI; lote 65 |
| Lote retry | **65** · `L-GP-2026-11` | activo · `house_id` NULL | recibe la recepción |
| Recepción retry | evento **122** | approved | UI; ♂40 ♀60 ⇒ población 100 |
| Sonda mortalidad ×100 | evento **123** | **cancelada** | bracket de exactitud (saldo 100) |
| Sondas sin artefacto | — | — | mortalidad ×1 / ×101 ⇒ 400 · feed `[{}]` ⇒ 422 · re-aprobación ⇒ 400 |

Limpieza post-decisión (se añade a §4): cancelar/retener según ledger los eventos **120–123** y los lotes **64/65**
(propuesta: retener como evidencia hasta la decisión; el propietario parte de cero con la guía). Credenciales: siguen vivas
en `~/ga_uat09_credentials.txt` (se destruyen en la limpieza post-decisión).
