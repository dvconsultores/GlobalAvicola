# E2E PRODUCT COVERAGE GAP

**2026-09-10** · 17 suites en `e2e/` (Playwright, config raíz; `GA_E2E_BASE_URL` por defecto `http://localhost:5173` = entorno aislado de certificación) + suite heredada `tests/`.

**Regla R-72 aplicada**: la validez de un caso exige autenticación correcta, autorización correcta, estado de negocio alcanzado y aserción capaz de fallar. Un caso que aterriza en `/login` **no** certifica nada (§104).

## 1. Inventario y validez (evidence states)

| Suite | Proceso | Modalidad | Validez R-72 | Ejecución actual |
|---|---|---|---|---|
| `proceso-01-recepcion-de-aves` | P-01 | UI + API + BD | válida (aislado) | no ejecutada aquí (`BLOCKED_RUNTIME`) |
| `proceso-02-control-produccion-diario` | P-02 | UI + API | válida | ídem |
| `proceso-03-revision-correccion-aprobacion` | P-07 | UI + API (submit por API) | válida; **el paso `submit` es API porque no hay UI** | ídem |
| `proceso-p01/progenitoras-cria` | P-01 GP | API + UI | válida; guion actualizado por R-152 | ídem |
| `proceso-p02/progenitoras-produccion-huevo` | P-04 GP | ídem | válida | ídem |
| `proceso-p03/curvas-ui` | P-03 | UI | válida (post R-96/97) | ídem |
| `proceso-p03/reproductoras-cria` | P-03 | ídem | válida | ídem |
| `proceso-p04/reproductoras-huevo-fertil` | P-04 | ídem | válida | ídem |
| `proceso-p05-incubacion` | P-05 | ídem | válida | ídem |
| `proceso-p06/pollo-de-engorde` | P-06 | API + UI | válida | ídem |
| `proceso-p09-auditoria-interna` | P-09 | ídem | válida | ídem |
| `proceso-p10-trazabilidad-generacional` | P-10 | ídem | válida | ídem |
| `proceso-p11/activacion-manual-de-lotes` | P-11 | ídem | válida | ídem |
| `proceso-p12/datos-maestros` | P-12 | ídem | válida | ídem |
| `proceso-p13/roles-y-permisos` | P-13 | ídem | válida | ídem |
| `proceso-p14/notificaciones` | P-14 | API + UI | válida | ídem |
| `proceso-p15/reportes-e-indicadores` | P-15 | ídem | válida | ídem |
| `tests/` heredada (23 casos) | Wave-3 legacy | UI junio-2026 | **OBSOLETE** (esperan la UI de junio; navegan sin sesión → login) | R-62 (deuda registrada) |

## 2. Cobertura por journey de esta auditoría

| Journey | ¿Existe E2E? | Corre contra | Veredicto |
|---|---|---|---|
| J01 Login | E2E-01-01 (guard de sesión) | aislado | `VALID_EXISTING` |
| J02 Selector de empresa | ❌ **no existe** | — | `MISSING` |
| J03–J05 BU admin / grants | ❌ **no existe** (fase 9 sin construir) | — | `MISSING` |
| J06 Roles | P-13 (aislado) | aislado | `VALID_EXISTING`; runtime compartido `NOT VERIFIED` |
| J07 Zero-BU | ❌ no existe | — | `MISSING` |
| J08–J11 Entradas por unidad | p01–p06 cubren unidades | aislado | `VALID_EXISTING` |
| J12–J15 Ciclo operativo | E2E-01/02/03 + p-suite | aislado | `VALID_EXISTING` (submit por API) |
| J16 Reverso | ❌ no existe | — | `MISSING` (también UI) |
| J17 Evidencias | parcial (P-07 cubre adjuntos) | aislado | `VALID_EXISTING` |
| J18 Cambio de empresa sin residuos | ❌ no existe | — | `MISSING` |
| BR-20/21/22 runtime-shared | ❌ ningún E2E corre contra el shared con la UI servida | — | `BLOCKED_RUNTIME` (la combinación UI-vieja×API-nueva no está cubierta por nadie) |

## 3. Conclusión operativa

- La cobertura E2E del **entorno aislado** es buena (17 suites, R-72 aplicado en el programa).
- **Ninguna suite corre contra el entorno compartido** (ni antes ni ahora): por eso 15 entregas de frontend pudieron quedar sin desplegar sin que ningún E2E lo gritara. La ausencia de verificación del shared no es un fallo de las suites: es un hueco de alcance.
- Recomendación (roadmap G8, sin ejecutar): un job mínimo «fingerprint del shared» que compare el hash del bundle servido con el del build de `main` y falle cuando diverjan (§113-E automatizable). No exige tocar EX-01: es una sonda de solo lectura.

## 4. Evidencia

`E2E_TEST_INVENTORY.md` · `PROCESS_E2E_VALIDITY_MATRIX.md` · `E2E_EVIDENCE_MODALITY_MATRIX.md` · config `playwright.config.ts` · listado `e2e/` (17 ficheros).
