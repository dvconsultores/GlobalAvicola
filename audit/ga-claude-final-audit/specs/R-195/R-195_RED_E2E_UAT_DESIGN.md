# R-195 · DISEÑO DE PRUEBAS RED · E2E · UAT

HEAD `c0b4afc` · Sin implementación en este documento.

## 1 · Diseño RED

### 1.1 `frontend/src/pages/users/__tests__/r195.usersEdit.test.tsx` (jsdom)

Mock api; usuario A (id 5) con rol 2.

| Nombre | Pasos | Aserción que **falla en HEAD** |
|---|---|---|
| `AC-R195-01 · editar envía el subconjunto permitido` | abrir edición; cambiar nombre y rol; guardar | `put` con claves ⊆ `{first_name,last_name,email,phone,role_id,is_active,view_type,area_id}` — HEAD: incluye `username`, `company_id` |
| `AC-R195-02 · 422 ⇒ mensaje humano` | simular 422 lista | texto visible sin `[object Object]` — HEAD: `alert` |
| `AC-R195-05 · baja fallida ⇒ mensaje` | simular 409 | mensaje visible — HEAD: modal mudo |
| `AC-R195-06 · sin diálogos nativos` | grep/espía de `window.alert` | no llamado — HEAD: llamado |

### 1.2 Control backend (sin cambio)

`PUT /users/{id}` con subconjunto ⇒ 200 (verde en HEAD; guarda).

Ejecución: `npx vitest run …/r195.*` ⇒ rojos exactos; salida a `evidence/red/`.

## 2 · Diseño E2E (C3)

| Caso | Pasos | Esperado |
|---|---|---|
| RT-01 | editar usuario (nombre+rol) por UI | 200; lista refrescada; detalle con nuevo rol |
| RT-02 | forzar error (correo inválido/duplicado) | mensaje legible |
| RT-03 | alta sin apellido | validación cliente |
| RT-04 | sonda: payload sin extras | 200 |

Artefactos: `evidence/r195/runtime-{red,c3}.json` + PNG; 0 `pageerror`.

## 3 · Plan UAT

| Caso | Acción | Esperado |
|---|---|---|
| UAT-R195-01 | Cambiar el rol de un usuario y su nombre | Guardado; visible al recargar |
| UAT-R195-02 | Provocar un error (dato duplicado) | Mensaje claro; sin pantalla rota |
| UAT-R195-03 | Dar de baja a un usuario | Confirmación clara; baja aplicada |

Criterio: 3/3 (agrupable con R-196/R-215).
