# GA-FE-02-B · F4 — EVIDENCIA DEL SELECTOR DE EMPRESA (`CAP-SES-05`)

**2026-09-11 · ENV-01 · Requisito: `OD-14` (la autoridad global sin contexto debe poder ELEGIR
empresa desde la UI normal) · Root reutilizado: `CAP-SES-05` (auditoría frontend runtime,
`IMPLEMENTED_BUT_NOT_EXPOSED`; condición de render idéntica) — sin R-ID nuevo.**

## 1 · RED (antes del fix) — capturado en la suite

Comando: `npx vitest run src/components/layout/__tests__/gaFe02b.companySelector.test.tsx`

```
FAIL F4 · Header — alcanzabilidad del selector > autoridad global SIN contexto:
  el selector es visible (RED antes del fix)          → selector AUSENTE
FAIL F4 · fetchMe — nombre de la empresa efectiva con persistida nula:
  resuelve el nombre por el catálogo                  → AssertionError: expected null to be
                                                        'Avícola Global C.A.'
Tests  2 failed | 3 passed (5)   (los 3 controles: super con nombre presente ·
                                  usuario común sin selector ×2)
```

Nota de proceso: una primera corrida falló por el **specifier del mock de i18n** del propio test
(`../../i18n` → `../../../i18n`); corregido antes de capturar el RED real (sin tocar producto).

## 2 · Fix mínimo (commit `716d175`)

| Archivo | Cambio |
|---|---|
| `frontend/src/components/layout/Header.tsx` | condición del bloque selector/badge: `(isSuperAdmin || activeCompanyName || user?.company_name)`; etiqueta con placeholder `t('company.select')` cuando aún no hay nombre |
| `frontend/src/stores/auth.store.ts` | `fetchMe` resuelve el nombre de la empresa efectiva por catálogo también cuando la persistida es `null` (bootstrap admin): `if (effectiveId != null && effectiveId !== user.company_id)` |
| `frontend/public/locales/{es,en}/translation.json` | clave `company.select` («Seleccionar empresa» / «Select company») |

Sin tocar navegación global: `R-98`/`R-119` intactos. No es GA-FE-03.

## 3 · GREEN + gates

```
Test Files  2 passed (2)     Tests  10 passed (10)   (F4 5 + sesión GA-FE-02 5)
TSC_EXIT=0
Test Files  21 passed (21)   Tests  205 passed (205)
build ✓ (vite)
```

## 4 · Verificación en runtime autenticado (post-deploy)

Bundle verificado: **`index-B2-tZnkI.js`** (Watcher: `BUNDLE_CHANGED=index-B2-tZnkI.js`).
Sesión: bootstrap `admin` (super admin) vía login oficial en el navegador.

| # | Paso | Observado |
|---|---|---|
| 1 | Carga con bundle nuevo (hard reload; aviso: el SPA previo corría bundle pre-F4) | shell hidratado (`D1`: `/me` corrió; «Admin Sistema»), **sin** forbidden |
| 2 | Selector sin contexto | botón visible **«Seleccionar empresa»** (placeholder i18n) — ANTES del fix: ausente |
| 3 | Abrir dropdown | lista cargada vía `GET /masters/companies`: «Avícola Global C.A.» y «Avícola Del Sur C.A.» |
| 4 | Seleccionar «Avícola Global C.A.» | `POST /switch-company` OK; header pasa a mostrar **«Avícola Global C.A.»** (nombre resuelto por catálogo con persistida `null` — path corregido) |
| 5 | Deep-link `/admin/unit-access` | «Acceso por unidad» + **«Empresa: Avícola Global C.A.»**; sin forbidden; unidades `[]` (pendiente F1, catálogo server-side) |
| 6 | Hard-refresh (listener de red) | `hits: [{/api/v1/me, 200}]` · `alerts: 0` · selector y contexto intactos · `mainText: "Acceso por unidad\nEmpresa: Avícola Global C.A."` |
| 7 | Móvil 390×844 | cabecera móvil muestra badge «Avícola Global C.A.»; página usable sin scroll horizontal |
| 8 | Cierre | `Cerrar Sesión` → `/login` (entorno limpio) |

Control negativo en suite (usuario común → sin selector) cubierto en §1; el `OD-14.d` (fail-closed
sin empresa) sigue vigente sin cambios.

## 5 · Veredicto

**F4 · CLOSED** — la circularidad de recuperación quedó resuelta al mínimo: un actor global puede
ELEGIR empresa con la UI normal y el estado sobrevive al refresh sin falsos forbidden. Al
aprobarse F1 (catálogo BU) el paso 5 mostrará además las cuatro unidades.
