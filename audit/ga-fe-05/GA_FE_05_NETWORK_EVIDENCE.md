# GA-FE-05 · EVIDENCIA DE RED (sanitizada)

Generación: `index-WUv1-F9o.js`. Solo método + ruta + status; sin tokens/cabeceras.

## Submit válido (E2E-01, evento 44)

```
200 POST /api/v1/operations/44/submit      ← una única mutación
200 GET  /api/v1/operations/44             ← GET fresco obligatorio tras el éxito
```

## Reenvío (E2E-07, evento 46)

```
200 POST /api/v1/operations/46/submit
200 GET  /api/v1/operations/46
```

## Doble clic (E2E-09, evento 48)

```
200 POST /api/v1/operations/48/submit      ← exactamente 1 (2 clics rápidos ⇒ una mutación lógica)
```

## Fallo controlado (E2E-10, evento 49 — intercepción de red del test)

```
[interceptado en el navegador: 403 Permiso requerido: operations:create]
POST /api/v1/operations/49/submit          ← 1 intento; 0 llegadas al backend; 0 mutaciones
GET  /api/v1/operations/49                 ← reconciliación (estado sigue registered)
```

## Denegaciones canónicas (API directa con sesión real)

```
POST /api/v1/operations/49/submit   (Z, sin User BU)      → 404 {"detail":"Evento no encontrado"}
POST /api/v1/operations/49/submit   (R2, sin RBAC)        → 403 {"detail":"Permiso requerido: operations:create"}
POST /api/v1/operations/49/submit   (C, CBU OFF)          → 404 {"detail":"Evento no encontrado"}
POST /api/v1/operations/50/submit   (E global, CBU OFF)   → 404 {"detail":"Evento no encontrado"}
```

Notas:
- Sin duplicación de mutaciones en ningún caso; sin éxito falso; sin persistencia en denegados/falso.
- El `404` en casos de unidad apagada/sin alcance es la semántica anti-enumeración del backend (el lote deja de existir para el actor); el `403` es la negativa de permiso. Ambos deniegan.
- La generación no cambió durante la certificación (bundle congelado `index-WUv1-F9o.js`).
