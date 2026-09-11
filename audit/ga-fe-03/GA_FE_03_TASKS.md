# GA-FE-03 · TAREAS

**Regla**: sin tarea sin AC; sin código antes de que exista la tarea. Estados: `DONE`/`RED`/
`GREEN`/`PENDIENTE`.

| ID | Finding origen | Sección SPEC | AC | Archivos esperados | Test esperado | Evidencia runtime | Depende de | Estado |
|---|---|---|---|---|---|---|---|---|
| T1 | R-98/R-119 | §9, §16, §23 | AC01–03 | `src/auth/navigation.ts` (nuevo) | `gaFe03.navigation.test.ts` | — | — | PENDIENTE |
| T2 | R-119, CAP-ADM-06 | §8–13 | AC04–06, 11–18, 25–30 | `src/data/navigationConfig.ts` (metadatos + filtro) | `gaFe03.navVisibility.test.ts` | matriz actores §75 | T1 | PENDIENTE |
| T3 | R-119, D1 | §10, §26 | AC19–24, 42–43 | `src/stores/*` (sin cambio de contrato), `src/auth/navigation.ts` | casos switch/refresh | refresh/switch runtime | T1 | PENDIENTE |
| T4 | D-2, §34 | §9, §34 | AC07, 25–28, 44 | `src/pages/operations/MenuHubPage.tsx` | `gaFe03.menuHub.test.tsx` | hub D/A/B | T2 | PENDIENTE |
| T5 | §33, §35 | §9, §14 | AC06, 08, 16, 34–35 | `src/pages/dashboard/DashboardPage.tsx`, `src/components/layout/MobileDrawer.tsx`, `MobileNav.tsx`, `Sidebar.tsx` | tests de fuente móvil/desktop + dashboard | desktop/móvil matrices | T2 | PENDIENTE |
| T6 | §24, §36, §59 | §10 | AC09–10, 18, 30, 37 | `src/App.tsx` (guardas `CapabilityRoute`), `src/components/auth/CapabilityRoute.tsx` (nuevo) | `gaFe03.routeGuards.test.tsx` | deep links §79 | T1, T2 | PENDIENTE |
| T7 | §31, §39 C19 | §15 | AC31–33 | `public/locales/{es,en}/translation.json`, `navigationConfig.ts` | `gaFe03.i18n.test.ts` | ES/EN runtime | T2 | PENDIENTE |
| T8 | §64 | §18 | AC40 | (sin código) | suite completa 205+/205+ | spots F1–F4/D1/D-1 | T2–T7 | PENDIENTE |
| T9 | §74, §93 | §17, §19 | AC41 | (sin código) | — | 3D + ruta directa | deploy | PENDIENTE |
| T10 | §66, §92 | §7 | — (soporte) | fixtures sintéticos | — | ledger de datos | deploy | PENDIENTE |

**Archivos prohibidos en esta tranche** (fuera de alcance): `backend/**`, migraciones,
`LotForm*` (`R-182`), botones submit (`R-181`), SAP, Wave B/C, `docs/12`.

**Checklist de cierre por tarea**: test exigido escrito ANTES/actualizado en el mismo commit;
grep de rol/usuario en componentes de navegación = 0; sin `any` nuevos injustificados; i18n sin
claves crudas; sin secretos.
