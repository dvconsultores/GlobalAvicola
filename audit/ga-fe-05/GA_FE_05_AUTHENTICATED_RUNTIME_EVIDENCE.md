# GA-FE-05 · EVIDENCIA RUNTIME AUTENTICADA (R-181)

Generación certificada: **`index-WUv1-F9o.js`** (C2 `005a252`) · Last-Modified 2026-09-11 13:07:24 GMT
Backend: sin cambios (contrato verificado). Capturas: `audit/ga-fe-05/evidence/runtime/`.

## 1 · Actores y fixtures (sintéticos, flujo oficial)

| Alias | Usuario (id) | Rol (id) | Autoridad | Concesión |
|---|---|---|---|---|
| C | ga05-c (109) | GA-FE05 TEST OPERATOR (46) | dashboard:read · lots:read · operations:read+create | broiler (ventana) |
| Z | ga05-z (110) | 46 | íd. sin concesión | — |
| R2 | ga05-r (114) | GA-FE05 TEST READ ONLY OPS (49) | dashboard:read · lots:read · operations:read | broiler (ventana) |
| P | ga05-p (111) | GA-FE05 TEST CORE ONLY (47) | dashboard:read | broiler (ventana) |
| D | ga05-d (112) | 47 | dashboard:read | — |
| V | ga05-v (113) | GA-FE05 TEST REVIEWER (48) | dashboard:read · operations:read · review:read+review · approvals:approve | broiler (ventana) |

Estados de fixtures **solo por flujo oficial**: 44 submit UI (E2E-01) · 45 submit API (E2E-05) · 46 submit API → start → return (E2E-06/07) · 47 submit → start → approve (E2E-08) · 48 submit doble clic · 49 negativos (permanece `registered`) · 50 E (CBU OFF) · 51 EN · 52 móvil.

## 2 · Matriz E2E (mediciones duras)

| Caso | Medición | Resultado |
|---|---|---|
| **E2E-01** submit válido (44, por la lista de Operaciones) | CTA «Enviar a revisión» visible ⇒ **1 POST 200** ⇒ **1 GET fresco** ⇒ CTA desaparece ⇒ chip «Enviado a Revisión» ⇒ F5 conserva ⇒ re-login conserva | **PASS** |
| **E2E-09** doble clic (48) | 2 clics rápidos ⇒ **1 POST** ⇒ `pending_review` | **PASS** |
| **E2E-10** fallo controlado (49, 403 interceptado) | 1 intento ⇒ error visible («No se pudo enviar a revisión») · **sin toast de éxito** · estado sigue `Registrado` · CTA vuelve · GET de reconciliación | **PASS** |
| **E2E-05** estado inválido (45 `pending_review`) | 0 CTA · chip «Enviado a Revisión» | **PASS** |
| **E2E-08** final inmutable (47 `approved`) | 0 CTA · chip «Aprobado» | **PASS** |
| **E2E-06** devuelto (46) | chip «Devuelto» · CTA «Reenviar a revisión» visible · **observación de la devolución visible** («Peso fuera de rango…») | **PASS** |
| **E2E-07** reenvío (46) | **1 POST 200** ⇒ CTA desaparece ⇒ `pending_review` ⇒ F5 conserva ⇒ re-login conserva | **PASS** |
| **E2E-03** sin User BU (Z sobre 49) | 0 CTA · lectura permitida · API directa ⇒ **404 «Evento no encontrado»** (anti-enumeración por unidad no efectiva) · sin cambio de estado | **PASS** |
| **E2E-04** sin RBAC (R2 sobre 49) | 0 CTA (lectura sí) · API directa ⇒ **403 «Permiso requerido: operations:create»** | **PASS** |
| Sin autoridad (P, D) | ruta denegada («No tiene permiso») | **PASS** |
| **E2E-02** CBU OFF (C y E global) | UI 0 CTA y lectura bloqueada; API C ⇒ **404**, API E (global) ⇒ **404** — la unidad apagada saca el lote del alcance **también para el actor global (sin bypass)** | **PASS** |
| **EN** (51) | «Submit for review» ⇒ tras enviar, chip «Pending Review» · sin claves crudas | **PASS** |
| **Móvil 390×844** (52) | CTA visible ⇒ **1 POST** ⇒ chip «Enviado a Revisión» ⇒ CTA 0 · **sin desborde horizontal** | **PASS** |

## 3 · Autoría de la autoridad (backend)

- Permiso: `operations:create` (403 sin él).
- Unidad: guarda operativa `exigir_unidad_operativa` — sin concesión ⇒ 404 anti-enumeración; CBU OFF ⇒ 404 (incluido global).
- Estado: fuera de `REENVIABLES` ⇒ 400 (contrato).

## 4 · Auditoría

| Verificación | Resultado |
|---|---|
| Transiciones `«Enviado a revisión»` para 44/46 | **3 filas** (44 E2E-01 · 46 fixture API · 46 E2E-07) |
| Filas de éxito por Z / R2 (denegados) | **0** (solo filas `login`, no mutación) |
| E2E-10 (interceptado) | **0** filas (nunca llegó al backend) |

## 5 · Consola

- Sin errores fatales. 1 error de recurso **esperado** en E2E-10 (`403` forzado por intercepción de red del propio test).

## 6 · Estados finales de fixtures (evidencia retenida)

`44 pending_review · 45 pending_review · 46 pending_review · 47 approved · 48 pending_review · 49 registered · 50 registered · 51 pending_review · 52 pending_review`
(Estados legítimos de producto; se retienen como evidencia. No se fuerza SQL en ningún caso.)

## 7 · Limpieza

4 revokes (C/P/R2/V) · 6 bajas (109–114) · roles 46/47/48/49 OFF · **rol 35 intacto** · BU **4×OFF** · residuos `ga05-*` = 0 · credenciales destruidas.
