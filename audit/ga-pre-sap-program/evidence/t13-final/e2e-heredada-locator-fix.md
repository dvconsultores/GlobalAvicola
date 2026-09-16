# E2E heredada — corrección de locator frágil (evidencia rojo→verde)

Árbol final de certificación · 2026-09-16.

- **Corrida 1** (árbol final): `132 passed · 1 failed (3.3m)` —
  `[heredada] tests/operations.spec.ts:40` «Operaciones · hub de procesos › el
  menú avícola presenta sus categorías con descripción»:
  `expect(locator).toBeVisible()` sobre `page.getByText(/opciones|abrir/i).first()`
  resolvió 23× al `<span class="text-xs text-slate-900">1 opciones</span>` del
  **MobileDrawer** (menú móvil, oculto en escritorio) ⇒ `unexpected value "hidden"`.
- **Causa raíz**: fragilidad del test — `.first()` sin filtrar visibilidad; el
  menú móvil duplica el texto en el DOM. **No es un defecto de producto**: el
  menú de escritorio presenta sus categorías y descripciones (los demás casos
  del mismo archivo quedaron verdes; 132/133 globales).
- **Corrección (solo test)**: `filter({ visible: true })` antes de `.first()`
  en `tests/operations.spec.ts` (sin cambio de producto; `tests/**` no dispara
  despliegue).
- **Corrida 2 (post-fix)**: **`133 passed (3.1m)` · exit 0** — log
  `evidence/t13-final/e2e-full.log` (111 `[procesos]` + 22 `[heredada]`).
- **Clase**: `TEST_DEFECT` (locator frágil). El E2E certificado de referencia
  (`procesos`, 111) no incluía el proyecto `heredada`; con el fix, la corrida
  completa queda verde.
