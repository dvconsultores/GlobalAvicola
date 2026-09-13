# R-195 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

HEAD `c0b4afc` · Artefactos bajo `specs/R-195/evidence/`.

| AC | Criterio (resumen) | Test | RED en HEAD | Caso E2E | UAT | Artefacto |
|---|---|---|---|---|---|---|
| AC-R195-01 | Editar (rol+nombre) ⇒ 200; sin extras | `r195.usersEdit › edit` | rojo (422) | RT-01 | UAT-01 | journal+PNG |
| AC-R195-02 | Error ⇒ mensaje humano | `› error` | rojo (`[object Object]`) | RT-02 | UAT-02 | captura |
| AC-R195-03 | Alta sin `last_name` ⇒ validación | `› create` | rojo | RT-03 | — | salida |
| AC-R195-04 | Empresa por contexto | `› company` | rojo/verde | RT-04 | — | salida |
| AC-R195-05 | Baja fallida ⇒ mensaje | `› delete` | rojo (modal mudo) | RT-05 | UAT-03 | captura |
| AC-R195-06 | Sin diálogos nativos (C-02) | `› dialogs` | rojo | — | — | grep/salida |
| AC-R195-07 | Sin migración/endpoint/permiso | revisión | — | — | — | `git diff --stat` |
| AC-R195-08 | Regresión usuarios/roles verde | suites | verde (línea base) | — | — | log |

Cobertura: 8 AC · 6 con RED nueva · 5 casos E2E · 3 UAT.

## Trazabilidad fuente → AC

| Fuente (B-06/B-28; C) | AC |
|---|---|
| `username`/`company_id` en PUT | AC-01/04 |
| `alert('[object Object]')` | AC-02/05/06 |
| `last_name` no exigido | AC-03 |
| Baja sin mensaje | AC-05 |
