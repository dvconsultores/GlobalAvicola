# GA-FE-02 · TEST MATRIX (RED + targeted green + validez)

## 1. Estrategia de RED

GA-FE-02 es funcionalidad **ausente** en el frontend: el RED demuestra la superficie de producto
faltante, no un backend roto (§78). Suites nuevas bajo `frontend/src/**/__tests__/` con los
patrones existentes (Vitest + RTL + `vi.mock` del cliente `api`, `react-i18next` mockeado a
claves). Fixtures construidas sobre las formas REALES del contrato
(`GA_FE_02_BACKEND_CONTRACT_MATRIX.md`), no inventadas (§79).

Fixtures/controles de RED requeridos:

```
FX1 actor autorizado Company-BU (permissions incluye business_units:read|update)
FX2 actor no autorizado (sin business_units:*)
FX3 Administrador de Accesos (read|update|create|delete; SIN users:read — el caso sin /users)
FX4 self (el actor dentro de candidatos — NO debe aparecer)
FX5 objetivo misma empresa (concedido / no concedido)
FX6 objetivo empresa ajena (404)
FX7 unidad ON / unidad OFF (409 en candidatos/concesión)
FX8 sesión sin effective_company_id (actor global sin seleccionar — fail closed)
FX9 concesión viva / concesión revocada (histórica) / no efectiva por OFF
FX10 sesión antigua SIN los campos nuevos (tolerancia — no romper navegación)
```

## 2. RED por AC (debe estar ROJO antes de implementar)

| RED | AC mapeado | Qué demuestra | Archivo previsto |
|---|---|---|---|
| R-ctx-1 | AC-COMP-01 | la sesión expone la empresa efectiva y la UI puede mostrarla | `stores/__tests__/gaFe02.session.test.ts` |
| R-ctx-2 | AC-COMP-06 | sin empresa efectiva la página NO ofrece mutaciones (fail closed) | `pages/admin/__tests__/UnitAccessPage.test.tsx` |
| R-nav-1 | AC-NAV-01/03 | entrada de menú visible SOLO con `business_units:read`/comodín; actor sin permiso no la ve | `data/__tests__/gaFe02.nav.test.ts` |
| R-nav-2 | AC-NAV-04 | ruta directa protegida por permiso | `App`/guard test |
| R-cbu-1 | AC-CBU-02/03 | las CUATRO unidades con estado del backend (estados mixtos FX7) | `UnitAccessPage.test.tsx` |
| R-cbu-2 | AC-CBU-04/05 | habilitar/deshabilitar llaman al endpoint EXACTO (método+ruta+code) y refetchean | ídem + assert de `api.patch` |
| R-cbu-3 | AC-CBU-08 | habilitar NO dispara ninguna llamada de concesión | ídem (assert llamadas) |
| R-cbu-4 | AC-CBU-12 | actor sin `business_units:update` no ve acciones de mutación | ídem |
| R-cbu-5 | AC-CBU-15 | fallo de API → estado reconciliado, sin falso éxito (toast error; refetch) | ídem |
| R-ubu-1 | AC-UBU-01/02 | sección/modal de concesiones accesible con `business_units:read`; identidad+empresa claras | `UsersPage` test nuevo |
| R-ubu-2 | AC-UBU-03/04 | concesiones renderizadas con `is_effective`; EMPRESA y USUARIO visualmente separados | ídem |
| R-ubu-3 | AC-UBU-05/08 | conceder/revocar llaman `POST/DELETE /users/{id}/business-units[/{code}]` y refetchean | ídem |
| R-ubu-4 | AC-UBU-11 | el actor (self) no aparece en candidatos / sin acción de auto-concesión | ídem (FX4) |
| R-ubu-5 | AC-UBU-14/15/16 | conceder/revocar no tocan RBAC ni habilitación (no existen esas llamadas) | assert de llamadas |
| R-sw-1 | AC-COMP-03/04/05 | tras `switchCompany`: tokens reemplazados, `/me` refetcheado, datos de inquilino recargados y selección de usuario limpiada si no pertenece | `stores/__tests__/gaFe02.switch.test.ts` |
| R-i18n-1 | AC-UI-08/09 | claves ES/EN presentes en ambos archivos (paridad) y mapeo central único de unidades | `data/__tests__/gaFe02.i18n.test.ts` |

**Definición de ROJO**: cada prueba falla por superficie ausente (módulo/página/clave inexistente
o comportamiento no implementado), con la razón registrada. Si algo ya pasara verde, NO es RED.

## 3. Validez de RED (§90) — por prueba se registra

```
TEST · AC · ACTOR(FX) · PERMISSIONS · EFFECTIVE COMPANY · COMPANY BU STATE · TARGET USER ·
USER BU STATE · ROUTE · EXPECTED · ACTUAL(por qué rojo) · CONTRATO DE FIXTURE · POR QUÉ ES GA-FE-02
```

**Inválido (crédito 0)**: fixture con auth incorrecta · esquema de respuesta inventado · empresa
equivocada · permiso equivocado · fallback de login · ruta legacy · harness no montado ·
expectativa de `R-98`/`R-119`/`R-181` ajena a la tranche.

## 4. Targeted GREEN esperado (§107 forma de reporte)

```
Company context:            x/x
Company switch:             x/x
Company BU render:          x/x
Company BU enable:          x/x
Company BU disable:         x/x
No auto-grants:             x/x
User BU render:             x/x
Grant:                      x/x
Revoke:                     x/x
Self-grant:                 x/x
Cross-company:              x/x
Permission:                 x/x
Navigation:                 x/x
Error states:               x/x
Mobile:                     x/x (browser/visual en piso E2E; el resto unit)
```

## 5. Sensibilidad (decisión §117)

Hipótesis críticas del frontend a las que se apunta (si el harness permite mutación segura
tras COMMIT 2, con checkpoint guard):

```
MU-1 quitar el guard de permiso de la ruta → R-nav-2 debe Rojar
MU-2 quitar el gating de acciones por permiso → R-cbu-4 / R-ubu-* deben Rojar
MU-3 permitir self en candidatos/acción → R-ubu-4 debe Rojar
MU-4 no limpiar selección/estado al cambiar de empresa → R-sw-1 debe Rojar
```

Si la sensibilidad frontend no resulta practicable con el harness actual: se documenta **N/A con
causa** y se compensa con los controles negativos autenticados (E2E) + los guards de backend ya
certificados. **Nunca** se muta seguridad de backend para probar la UI (y no se hará aquí).

## 6. Integración con la suite existente

Baseline actual: 108/108 (12 archivos). Los archivos nuevos se suman; **0 failed**, **0 skips
nuevos**. No se debilita ninguna prueba existente.
