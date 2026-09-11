# GA-FE-07 · EVIDENCIA FRONTEND

## Cambio (C2 `5a5bb3f`)

`frontend/src/pages/lots/LotFormPage.tsx` — en la carga de maestros del formulario:

```ts
if (areaRes.status === 'fulfilled') {
  setAreas((areaRes.value.data ?? []).filter((a: any) => a.is_active !== false))
}
```

- **Solo** el selector transaccional del alta filtra por estado; `MasterListPage` (administración) **no** se tocó y sigue mostrando activas e inactivas.
- Sin claves i18n nuevas (el mensaje de denegación viaja por el canal de errores existente; SIN textos nuevos ⇒ ES/EN N/A documentado).
- Sin cambio de endpoints ni de forma de datos (el listado ya incluía `is_active`).

## Tests

| Suite | Resultado |
|---|---|
| `gaFe07.inactiveAreaEligibility.test.tsx` (selector filtra; activa presente; control: el API sí devuelve inactivas) | RED → **2/2 verdes** |
| `src/pages/lots` completo (GA-FE-06 + GA-FE-07) | **9/9** |
| Vitest completo | **280/280** (37 archivos; +2 de esta tranche) |
| `npx tsc -b --noEmit` | **0 errores** |
| `npm run build` | **PASS** |

## Runtime (generación `index-BUthrUt9.js`)

- Selector desktop: opciones = `Seleccionar área…`, `Nave Activa GA-FE-07` (activa propia 6), `Nave Activa <sufijo>` (fixture activa 11), `Nave Carrera <sufijo>` (activa en el momento de la captura) — **CERO inactivas** (H=12, retirada=8, y todos los fixtures inactivos anteriores) y **sin IDs crudos**.
- Móvil 390×844: idéntico resultado.
- Carrera: con el formulario abierto y el área seleccionada, la baja oficial del área produce `400 «Área inactiva»`, error visible y **sin persistencia**; el resto del formulario queda utilizable.
- Capturas: `evidence/green/ds-selector-final.png` · `mb-selector-final.png` · `ds-race-error.png`.
