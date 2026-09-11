# GA-FE-08 · CLARIFICACIONES (C01–C20)

Fecha: 2026-09-11 · Baseline: `30fe3dc`. Todas resueltas con evidencia de repositorio y runtime.

| # | Cuestión | Resolución | Evidencia |
|---|---|---|---|
| C01 | Ruta exacta de Lotes | `/lots` (lista) · `/lots/:id` (detalle) · `/lots/new` (alta) | App.tsx:263-265 |
| C02 | Componente de lista | `LotListPage` (`frontend/src/pages/lots/LotListPage.tsx`) | idem |
| C03 | Guarda de ruta | `CapabilityRoute permission="lots:read"`; `/lots/new` añade `WebOnlyRoute` + `lots:create` | App.tsx:88-97,263-265 |
| C04 | Permiso exacto | `lots:read` (ver/entrar) · `lots:create` (alta) · `lots:update` (acciones) | router.py; LotListPage:53 |
| C05 | Dominio BU del lote | `{grandparent, breeder, broiler}` (`bird_type`); entrada declarativa = `requiresUnits: true` (multi-unidad, marco GA-FE-03); datos acotados a unidades efectivas. **Frontera documentada:** sesión solo-incubadora vería la entrada con lista vacía (la incubadora no produce lotes); se acepta sin cambiar autoridad ni añadir dimensiones al evaluador | LotListPage:9; service.py:80-96 |
| C06 | Regla de empresa | `effective_company_id` requerido; global sin contexto ⇒ fail-closed | navigation.ts:79-84 |
| C07 | Grupo existente | Contenedor `poultry` («Gestión Avícola», sección `operational`) | navigationConfig.ts:92 |
| C08 | Ubicación deseada | **Primera hija** de `poultry` ⇒ tarjeta en hub `/menu/poultry` (desktop y móvil) | decisión §3 nav trace |
| C09 | Clave de traducción | `nav.lots` ya existe ES «Lotes» / EN «Lots» — **reuso** (grep 0 usos previos) | translation.json:114 |
| C10 | Representación desktop | Tarjeta «Lotes» en el hub de Gestión Avícola (patrón atenea certificado) | MenuHubPage |
| C11 | Representación móvil | Mismo hub (barra inferior → Gestión Avícola → tarjeta); sin tocar la barra inferior; sin lógica especial | MobileNav/navigationConfig:252-280 |
| C12 | Estado activo | `isPathActive` cubre `/lots` y `/lots/:id`; contenedor resaltado por `isAnyChildActive` | navigationConfig.ts:320-340 |
| C13 | Deep link | Autorizado: funciona (contrato intacto). Sin autoridad: mismo contrato certificado (visual denegado sin permiso; datos fail-closed por unidades) | App.tsx:88-97; service.py |
| C14 | Zero-BU | Oculto (`requiresUnits`) y sin datos | evaluador |
| C15 | Access Admin | Oculto sin `lots:read`+unidades (rol de control) | fixtures GA-FE-03 (B) |
| C16 | Actor global | Contexto + unidad habilitada; BU OFF absoluto | navigation.ts:63-76 |
| C17 | OD-23 | Concesión terminada ⇒ sin unidades efectivas ⇒ oculto; concesión nueva ⇒ visible | R-188/OD-23 certificado |
| C18 | ¿Cambio backend necesario? | **NO** — diff backend 0 | análisis §4-§5 spec |
| C19 | ¿R nuevo? | **NO** — OBS-UAT-01 posee el trabajo | GA-GOV-01 |
| C20 | Criterios UAT | 5 casos del prompt §67 (encontrar · abrir · desaparecer sin acceso · volver con concesión · móvil) | spec §19 |
