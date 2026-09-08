# ORIGEN DE VERDAD DE LOS MAESTROS

Auditoría maestra · 2026-09-08 · **solo lectura**

```
LO QUE LA SPEC DICE HOY:
    SAP importa      Centros · Almacenes · Materiales · Proveedores · Lotes · OC · OT
    GA es dueño de   Empresas · Granjas · Galpones · Incubadoras · y el resto del catálogo
```

`docs/10-sap-integration-strategy.md §3.1` es la lista completa de lo que entra desde SAP.
`docs/02-functional-spec.md §3.2.1` es la lista de «Catálogos Base», con campos propios y
prioridad, donde **Empresas** y **Granjas** figuran como maestros del producto.

---

## 1. La matriz

| Maestro | Spec que lo define | Origen de verdad **según spec** | Objeto SAP | Tabla local | ¿Crear local? | ¿Editar local? | ¿Borrar local? | Sync | UI |
|---|---|---|---|---|:--:|:--:|:--:|:--:|:--:|
| **Empresas** | `02 §3.2.1` | **GLOBAL-AVICOLA-OWNED** | — | `companies` | sí | sí | sí | no | `/masters` |
| **Granjas** | `02 §3.2.1` | **GLOBAL-AVICOLA-OWNED** | — | `farms` | sí | sí | sí | no | `/masters` |
| Galpones | `02 §3.2.1` | GLOBAL-AVICOLA-OWNED | — | `houses` | sí | sí | sí | no | `/masters` |
| Incubadoras · Nacedoras | `02 §3.2.1` | GLOBAL-AVICOLA-OWNED | — | `hatcheries` · `hatchers` | sí | sí | sí | no | `/masters` |
| Líneas genéticas · Razas | `02 §3.2.1` | GLOBAL-AVICOLA-OWNED | — | `genetic_lines` · `breeds` | sí | sí | sí | no | `/masters` |
| Fases productivas | `02 §3.2.1` | GLOBAL-AVICOLA-OWNED | — | `productive_phases` | sí | sí | sí | no | `/masters` |
| **Proveedores** | `02 §3.2.1` · `10 §3.1` | **SHARED** — lleva `código SAP` y SAP los importa | Vendors | `suppliers` | sí | sí | sí | manual | `/masters` |
| Tipos de alimento · Vacunas · Medicamentos | `02 §3.2.1` | GLOBAL-AVICOLA-OWNED | (Materiales, adyacente) | varias | sí | sí | sí | no | `/masters` |
| Causas de mortalidad · descarte | `02 §3.2.1` | GLOBAL-AVICOLA-OWNED | — | varias | sí | sí | sí | no | `/masters` |
| Transportes · Plantas de beneficio | `02 §3.2.1` | GLOBAL-AVICOLA-OWNED | — | varias | sí | sí | sí | no | `/masters` |
| Órdenes de compra · transferencia | `10 §3.1` | **SAP-OWNED** | PO · TO | `sap_references` | importación | no | no | manual | `/sap` |
| Centros · Almacenes · Lotes SAP | `10 §3.1` | **SAP-OWNED** | Plants · StorLoc · Batches | `sap_references` | importación | no | no | manual | `/sap` |

---

## 2. El veredicto sobre la pregunta del propietario

> «Compañías y granjas son datos de SAP, no CRUD propietario de Global Avícola.»

```
¿Lo dice alguna spec?                     NO — cero coincidencias en docs/ y specs/
¿El código lo contradice?                 NO — el código hace exactamente lo que dice `02 §3.2.1`
¿Contradice la expectativa del dueño?     SÍ
CLASIFICACIÓN                             SPEC_GAP  ·  OWNER_DECISION_REQUIRED
```

**Esto no es un defecto de implementación.** Es un requisito que nunca se escribió. El `CRUD` de
granjas y empresas que el propietario ve en la interfaz es el comportamiento **especificado**, y
fue construido y certificado contra esa especificación.

Convertirlo en defecto exige antes una decisión de propietario que cambie `docs/02 §3.2.1` y
`docs/10 §3.1`. Mientras eso no exista, marcar el `CRUD` como «contradicción» sería inventar una
norma y luego acusar al código de incumplirla.

### Lo que sí hay que decidir, y en este orden

```
1. ¿Es SAP el dueño de Empresas?   ¿Y de Granjas?   ¿Con qué objeto SAP se corresponden?
2. Si sí: ¿réplica de solo lectura, o copia con extensión local declarada?
3. ¿Qué pasa con las que ya existen creadas localmente?
4. ¿Y con `sap_config`, que hoy es un campo editable de la empresa?
```

Sin la 1 no se puede escribir la spec; sin la 2 no se puede diseñar; y la 3 es exactamente la
clase de pregunta que `BU-D10` dejó abierta para las unidades de negocio.

---

## 3. Un riesgo que la auditoría sí encontró aquí, y que es independiente

`Company` **no tiene columna `company_id`**, de modo que el filtro de inquilino de
`MasterService` no le aplica: `hasattr(self.model, "company_id")` es falso y la consulta sale
sin acotar. Cualquier usuario con `masters:read` —lo tienen los cinco roles sembrados— lista
**todas** las empresas del sistema, con `tax_id`, `country`, `currency`, `approval_levels` y
`sap_config`.

Es `F-B`, `P0`, y no depende de quién sea el dueño del maestro: con SAP o sin SAP, un inquilino
no debe poder enumerar a los demás.
