# LOS VEINTIDÓS MAESTROS FRENTE A LA UNIDAD DE NEGOCIO

Auditoría del 2026-09-07 · **solo lectura**

---

## 1. Por qué los maestros importan aquí

Son **106 de las 198 rutas** de la API. Y son vector de fuga por partida doble: por sus
listados, y por los buscadores y desplegables que los consumen (`§35` del encargo).

## 2. La matriz

| Maestro | Clasificación | Alcance de unidad | Riesgo |
|---|---|---|:--:|
| `companies` | **COMPANY CORE** | — | — |
| `areas` | **COMPANY CORE** | organigrama, no unidad | — |
| `productive_phases` | **GLOBAL PRODUCT** | invariante del dominio | P3 |
| `farms` | **SHARED BUSINESS** | una granja puede alojar varias unidades | **P2** |
| `houses` | SHARED BUSINESS | vía granja | P2 |
| `hatcheries` | **MODULE SPECIFIC — Incubadora** | sí | **P2** |
| `incubators` | **MODULE SPECIFIC — Incubadora** | vía incubadora | **P2** |
| `hatchers` | **MODULE SPECIFIC — Incubadora** | vía incubadora | **P2** |
| `genetic_lines` | SHARED BUSINESS | transversal | P3 |
| `genetic_weight_curves(_points)` | SHARED BUSINESS | por línea genética | P3 |
| `breeds` | **tiene `bird_type`** | **el único maestro con unidad explícita** | P2 |
| `feed_types` | SHARED BUSINESS | transversal | P3 |
| `vaccines`, `medications` | SHARED BUSINESS | transversal | P3 |
| `mortality_causes`, `cull_causes` | SHARED BUSINESS | transversal | P3 |
| `transports` | SHARED BUSINESS | transversal | P3 |
| `processing_plants` | **MODULE SPECIFIC — Engorde** | sí | **P2** |
| `rejection_reasons` | SHARED BUSINESS | transversal | P3 |
| `correction_types` | SHARED BUSINESS | transversal | P3 |
| `suppliers` | SHARED BUSINESS | transversal | P3 |
| `sap_references` | MULTI-MODULE | las cuatro | P2 |

```
CORE de empresa ......  2
GLOBAL de producto ...  1
específicos de unidad   4     hatcheries · incubators · hatchers · processing_plants
compartidos .......... 15
```

## 3. Los cuatro específicos

`hatcheries`, `incubators` y `hatchers` **solo tienen sentido con Incubadora habilitada**.
`processing_plants`, solo con Engorde. Una empresa que solo tenga Progenitoras vería hoy cuatro
maestros que no le sirven de nada — molesto, no peligroso.

Lo peligroso es al revés: un usuario de Reproductoras en una empresa que **sí** tiene Incubadora
ve el listado completo de incubadoras, con sus nombres y capacidades.

## 4. `breeds` es la excepción instructiva

Es el único maestro con `bird_type`. Que exista demuestra que el modelo **ya sabía** distinguir
unidades cuando le convino — y que no lo hizo en `lots` de forma obligatoria ni en
`operational_events` en absoluto.

## 5. Buscadores y desplegables

22 endpoints aceptan parámetro `search`. Cada uno es un autocompletado que hoy devuelve todo lo
de la empresa. Un usuario de Reproductoras escribiendo tres letras en un selector de incubadora
obtiene los nombres reales de las incubadoras ajenas a su unidad.

Es fuga de **baja gravedad y alta visibilidad**: no expone datos productivos, pero revela la
estructura de las unidades que el usuario no debería ver.
