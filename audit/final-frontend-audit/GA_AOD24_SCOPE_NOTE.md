# AOD-24 · NOTA DE ALCANCE (FUERA DE LAS 38)

Finding: **R-177** · Decisión: **AOD-24** · Prioridad: **P3** · Fecha: 2026-09-11 · RFC: `AUDIT_OWNER_DECISIONS_REQUIRED.md:85`, `R177_EGG_TYPE_OVOSCOPY_DOMAIN_MATRIX.md`, `FORM_API_CONTRACT_GAP_MATRIX.md:24`.

## Qué gobierna

**Tipo de huevo vs resultado de ovoscopía**: hoy un único campo libre (`egg_movements.egg_type`) guarda tanto los tipos de huevo de la recolección/clasificación (fértil, sucio, roto, infértil, descartado, comercial — `docs/02 §3.6.2`, `docs/03:277`) como los resultados de la ovoscopía (infértiles, embriones muertos tempranos/tardíos, contaminados — `docs/02 §3.7.3`, `spec.md:192`).

Opciones canónicas: **A)** un único conjunto cerrado que incluya ambos · **C)** dos datos distintos (`egg_type` en recolección/clasificación + resultado propio en ovoscopía) — B (maestro configurable) y D (maestro existente) **no tienen respaldo documental**. La elección cambia modelo de datos, captura y validación.

## Por qué queda FUERA de las 38

- No es una capacidad del inventario original: es un **contrato de forma/dato** dentro de eventos ya clasificados (OVOSCOPÍA pertenece a los flujos incubadora ya contados en CAP-OPS-04/06).
- No contradice ningún AC aceptado: `RR-17` (saldos) es independiente; la validación de valores/etiquetas/UI se hará con R-177 cuando se decida.

## Efectos sobre los gates

- **Bloquea cierre frontend: NO** (ninguna fila FVA queda pendiente por AOD-24; las superficies de ovoscopía funcionan con el contrato actual).
- **Bloquea Wave B readiness: NO** — es **contenido de la propia Wave B** (decisiones 9 · AOD-24 nueva; «BLOQUEADOS POR DECISIÓN» lista Wave B). La reconciliación de preparación de Wave B (separada, no iniciada) debe incluirlo en su orden del día.
- Puede permanecer como **gobernanza P3 separada**.

## Recomendación (no vinculante)

Presentar A vs C al propietario **en la futura reconciliación de Wave B** (o en un paquete conjunto con AOD-25 si el propietario prefiere agrupar decisiones Wave B). No se decide aquí (`NO DECIDIR POR EL PROPIETARIO`).
