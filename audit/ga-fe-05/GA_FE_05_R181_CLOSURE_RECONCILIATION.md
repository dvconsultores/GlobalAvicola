# GA-FE-05 · CIERRE R-181 — RECONCILIACIÓN FINAL

Fecha: 2026-09-11 · Generación: `index-WUv1-F9o.js` (C2 `005a252`) · Backend: sin cambios.

## 1 · Hallazgo original (R-181, P2) y su resolución

> «`POST /operations/{id}/submit` … no tiene ningún control en la interfaz: `operationsService.submit` no tiene llamadores … 0 refs `/submit` en el bundle desplegado; sin claves i18n …»

| Componente del hallazgo | Estado |
|---|---|
| Sin control en la interfaz | **RESUELTO** — CTA state-aware en `/operations/:id` (desktop y móvil) |
| Servicio sin llamadores | **RESUELTO** — `OperationDetailPage` consume `operationsService.submit` |
| 0 refs `/submit` en bundle | **RESUELTO** — bundle nuevo con el flujo completo |
| Sin claves i18n | **RESUELTO** — 5 claves ES/EN + `status.*` completadas |
| Feedback de estado | **RESUELTO** — chip localizado + GET fresco + toast; sin estado obsoleto |
| Reenvío devuelto/rechazado (`OD-17.a/b`, `docs/12 §2`) | **RESUELTO** — «Reenviar a revisión» en `returned`/`rejected` |

## 2 · AC originales de R-181 (contrato §36–40) — resultado

### Contrato
| AC | Resultado | Evidencia |
|---|---|---|
| R181-AC01 contrato backend documentado | PASS | reconciliación §2 (ruta/permiso/estados/auditoría verificados en código) |
| R181-AC02 gap frontend documentado | PASS | reconciliación §3–4 + RED |
| R181-AC03 permiso canónico | PASS | UI usa `operations:create`; R2 ⇒ 403 |
| R181-AC04 contexto de empresa | PASS | E2E-01 + negativos (E2E-02/03) |
| R181-AC05 CBU OFF bloquea | PASS | E2E-02 (UI sin CTA; API denegada) |
| R181-AC06 User BU/global | PASS | E2E-03 (sin concesión ⇒ denegado); E2E-02 global sin bypass |
| R181-AC07 backend autoridad final | PASS | API directa en todos los negativos |

### Submit
| AC | Resultado | Evidencia |
|---|---|---|
| R181-AC08 descubrible por UI | PASS | E2E-01 vía lista de Operaciones |
| R181-AC09 una mutación | PASS | E2E-01/09 (1 POST) |
| R181-AC10 refresh backend | PASS | 1 GET fresco + chip actualizado |
| R181-AC11 estado correcto | PASS | `registered → pending_review` |
| R181-AC12 CTA desaparece | PASS | post-submit 0 CTA |
| R181-AC13 sin éxito falso | PASS | E2E-10 (intercepción 403) |
| R181-AC14 refresh preserva | PASS | F5 |
| R181-AC15 relogin preserva | PASS | re-login |

### Resubmit
| AC | Resultado | Evidencia |
|---|---|---|
| R181-AC16 devuelto/rechazado exponen reenvío | PASS | E2E-06/07 (`returned`); `rejected` cubierto por contrato idéntico + vitest |
| R181-AC17 sin reenvío antes de corrección si el contrato lo exige | PASS (N/A documentado) | el contrato NO exige corrección para reenviar `returned`/`rejected`; `corrected` no muestra CTA |
| R181-AC18 reenvío autorizado funciona | PASS | E2E-07 |
| R181-AC19 estado resultante | PASS | `pending_review` |
| R181-AC20 persistencia | PASS | F5 + re-login |
| R181-AC21 final inmutable | PASS | E2E-08 (`approved` sin CTA) |

### Negativos
| AC | Resultado | Evidencia |
|---|---|---|
| R181-AC22 CBU OFF | PASS | E2E-02 (C y E) |
| R181-AC23 sin User BU | PASS | E2E-03 |
| R181-AC24 sin RBAC | PASS | E2E-04 (403) |
| R181-AC25 no autorizado | PASS | P/D (ruta denegada) |
| R181-AC26 estado inválido | PASS | E2E-05 (sin CTA; API 400 por contrato) |
| R181-AC27 API directa no elude | PASS | 404/403 canónicos |
| R181-AC28 global no elude CBU OFF | PASS | E2E-02 (E ⇒ 404) |

### Calidad
| AC | Resultado | Evidencia |
|---|---|---|
| R181-AC29 desktop | PASS | capturas 1440×900 |
| R181-AC30 móvil 390×844 | PASS | capturas + 0 overflow |
| R181-AC31/32 ES/EN | PASS | «Enviar/Reenviar…», «Submit/Resubmit for review» |
| R181-AC33 sin claves crudas | PASS | runtime EN (`rawKeys=false`) |
| R181-AC34 sin mutación duplicada | PASS | E2E-09 |
| R181-AC35 sin flash de permiso | PASS | gates fail-closed (vitest 4 controles) |
| R181-AC36 sin error fatal de consola | PASS | solo 1 error de recurso esperado (intercepción E2E-10) |
| R181-AC37 auditoría correcta | PASS | 3 filas de transición; 0 por denegados |
| R181-AC38/39/40 regresión GA-FE-02/03/04 | PASS | suite 273/273 + superficie de evidencia intacta (GA-FE-04 gates sin cambio) |

## 3 · Criterios de cierre (reconciliación §5)

Los 10 criterios: ✅ CTA submit · ✅ resubmit OD-17 · ✅ estado localizado · ✅ refresh/relogin · ✅ fallo sin éxito falso · ✅ sin doble mutación · ✅ final/no-reenviables sin acción · ✅ seguridad producto (UI+API) · ✅ 0 backend/0 permisos/0 migraciones · ✅ no regresión.

## 4 · Veredicto

**R-181 = CLOSED.** El hallazgo completo (envío + reenvío + estado + feedback + descubribilidad + seguridad) queda implementado, probado (10/10 automatizado + 13 casos runtime), evidenciado y certificado sobre una generación congelada.
