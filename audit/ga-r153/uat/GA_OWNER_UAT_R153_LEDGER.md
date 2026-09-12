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
