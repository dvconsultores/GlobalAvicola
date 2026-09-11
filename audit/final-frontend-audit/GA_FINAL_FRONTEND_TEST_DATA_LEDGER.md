# FINAL FRONTEND AUDIT · LEDGER DE DATOS DE PRUEBA

Entorno: producción de prueba (empresa 1 «Avícola Global C.A.»). Ningún humano modificado; actores sintéticos por mecanismos oficiales; credenciales efímeras destruidas.

## 1 · Actores (creados y destruidos 2026-09-11)

| Alias | IDs | Rol (id) | Permisos | Concesiones | Vista | Propósito |
|---|---|---|---|---|---|---|
| fdaop | user **154** | fda-op (**98**) | dashboard/operations(r,c,u)/lots(r,c)/reports read + masters:read (añadido en probe3) | grandparent, breeder, hatchery, broiler | web | FVA-01..05,16..18,20..25,27,29..31 |
| fdarev | user **155** | fda-rev (**99**) | dashboard, operations:read, review:read, approvals:approve/reject, corrections:correct | broiler | web | FVA-26 |
| fdaadm | user **156** | fda-adm (**100**) | dashboard, users(r,c,u), masters:read, audit:read, sap:read | — | web | FVA-06,13..15,33..36,32 |
| fdaacc | user **157** | fda-acc (**101**) | business_units:read/update/create/delete | — | web | FVA-08/09 (UI revoke→regrant) |
| fdazbu | user **158** | fda-core (**102**) | dashboard:read | — | web | FVA-12/38 (zero-BU) |
| fdamob | user **159** | fda-op (98) | íd. fdaop | 4 unidades | **mobile** | FVA-16/29 móvil |
| — | BU «4 unidades» | — | — | habilitadas durante el E2E | — | cubrir 4 etapas (restauradas OFF) |
| (global) | GA_FLOW_USER | super admin | wildcard | — | — | administración y limpieza |

## 2 · Fixtures de lectura

- Lotes existentes (41 en alcance broiler; 82-95 enlaces en lista con filtros), detalle con IPE (fixtures R-187/OD-22) — **solo lectura**.
- Sin creación de operaciones/lotes nuevos (la verificación de formularios es de presencia de campos, sin submit) — sin residuo de datos.

## 3 · Limpieza ejecutada

Revocación total de concesiones (200) · bajas lógicas de 154-159 (204; login posterior 403) · roles 98-102 desactivados (200) · **4 unidades OFF restauradas — catálogo 4×OFF** · admin operativo (200) · credenciales `~/fda_credentials.txt` destruidas · `/tmp/fda_*` eliminado · sesiones cerradas.

## 4 · Retenido

Evidencia: 21 capturas + 5 JSON en `evidence/` (sin secretos). Auditoría del sistema preservada (append-only). Humanos intactos.
