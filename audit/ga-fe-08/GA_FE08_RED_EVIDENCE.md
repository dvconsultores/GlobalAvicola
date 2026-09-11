# GA-FE-08 · EVIDENCIA RED

Fecha: 2026-09-11 · Baseline: `30fe3dc` · Comando: `npx vitest run src/data/__tests__/gaFe08.lotsNav.test.ts --reporter=verbose`

## Resultado pre-fix

```
Test Files  1 failed (1)
     Tests  7 failed | 5 passed (12)
```

**Fallan (rojo esperado — la entrada «Lotes» no existe aún):**

1. × existe una entrada declarativa hacia la ruta existente `/lots`, con permiso y dependencia de unidad declarados (AC01-04)
2. × vive bajo Gestión Avícola como primera opción del hub, sin raíz nueva (AC19, AC26)
3. × el operador autorizado descubre «Lotes» (AC01/02)
4. × OD-23: la concesión histórica terminada NO revive; la concesión fresca sí (AC09/10)
5. × actor global: sin contexto fail-closed; con unidad habilitada descubre (AC06/14)
6. × la entrada viaja en ambas vistas: web completa y móvil bajo Gestión Avícola (AC19/20)
7. × la ruta activa cubre lista y detalle y resalta el contenedor (AC05)

**Pasan pre-fix (controles negativos + reuso i18n):**

- ✓ sin el permiso de lotes no hay entrada (AC11)
- ✓ sin unidades efectivas (BU negativa) no hay entrada ni raíz productiva (AC08)
- ✓ empresa con BU OFF: sin producto, global incluido (AC07, AC14)
- ✓ zero-BU y Access Administrator no obtienen «Lotes» (AC12/13)
- ✓ `nav.lots` existe en ES («Lotes») y EN («Lots») — clave reusada (AC21-23)

## Interpretación

- El RED usa la **capa real de composición de navegación** (`NAV_ITEMS` + `filterNavItemsBySession` / `getNavItemsForViewType` / `isAnyChildActive`), no marcado ajeno (§34).
- Los controles negativos ya verdes fijan las fronteras de autoridad que la implementación **no** debe romper (§35).
- Reproducción runtime pre-fix (usuario autorizado + móvil): `evidence/pre-fix-repro.json`, `P01-P03` — sidebar/hub/móvil sin «Lotes»; URL directa OK (41 lotes; consola 0).
