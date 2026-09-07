# LOS QUINCE PROCESOS FRENTE A LA UNIDAD DE NEGOCIO

Auditoría del 2026-09-07 · **solo lectura**

---

## 1. Una distinción que hay que hacer explícita

```
CERTIFICACIÓN FUNCIONAL       el proceso hace lo que la spec dice        14 / 15 hoy
CERTIFICACIÓN DE MÓDULO       solo lo ve quien debe                      0 / 15 hoy
```

Introducir un requisito nuevo **no invalida** lo ya certificado. Los catorce procesos
certificados siguen haciendo lo que sus specs exigen. Lo que ninguno tiene todavía es
aislamiento por unidad de negocio, porque hasta hoy nadie lo había pedido.

## 2. La matriz

| Process | Primary Module | Secondary Module | Multi-Module? | Cross-Module Data | Current Isolation |
|---|---|---|:--:|---|---|
| `P-01` Progenitoras — Cría | **Progenitoras** | — | no | — | solo empresa |
| `P-02` Progenitoras — Producción | **Progenitoras** | Reproductoras (destino del huevo) | **sí** | `egg_batches` | solo empresa |
| `P-03` Reproductoras — Cría | **Reproductoras** | — | no | — | solo empresa |
| `P-04` Reproductoras — Huevo fértil | **Reproductoras** | **Incubadora** (despacho) | **sí** | `egg_batches`, `egg_dispatch` | solo empresa |
| `P-05` Incubación | **Incubadora** | Reproductoras (recepción) · Engorde (despacho) | **sí** | `egg_batches`, `chick_batches` | solo empresa |
| `P-06` Pollo de engorde | **Engorde** | Incubadora (recepción) | **sí** | `chick_batches` | solo empresa |
| `P-07` Revisión → Aprobación | — | **las cuatro** | **sí** | `operational_events` | solo empresa |
| `P-08` Consolidación SAP | — | **las cuatro** | **sí** | `consolidated_movements` | solo empresa · `BLOCKED_EXTERNAL` |
| `P-09` Auditoría interna | — | **las cuatro** | **sí** | `audit_logs` | solo empresa |
| `P-10` Trazabilidad generacional | — | **las cuatro, por diseño** | **sí** | `egg_batches`, `chick_batches` | solo empresa |
| `P-11` Activación manual de lotes | derivable | las cuatro | **sí** | `lots` | solo empresa |
| `P-12` Datos maestros | — | mixta | **sí** | 22 maestros | solo empresa |
| `P-13` Usuarios y roles | — | — | no | — | solo empresa |
| `P-14` Notificaciones | — | **las cuatro** | **sí** | `notifications` | solo empresa |
| `P-15` Reportes y KPI | — | **las cuatro, agregadas** | **sí** | KPI y paneles | solo empresa |

```
de una sola unidad ....  3     P-01 · P-03 · P-13
multi-unidad .......... 12
aislamiento por unidad   0 / 15
```

## 3. Los tres que parecen simples y no lo son

`P-01` y `P-03` son de una sola unidad **en su cadena**, pero comparten tablas con las demás:
sus eventos viven en `operational_events` junto a los de Incubadora. Que el proceso sea de una
unidad no significa que sus datos estén separados.

`P-13` es el único genuinamente ajeno a la unidad de negocio — y aun así será donde se conceda
el acceso a módulos, de modo que **hereda la responsabilidad**.

## 4. Los que no se pueden aislar sin una decisión

`P-02`, `P-04`, `P-05`, `P-06` y `P-10` **cruzan la frontera por diseño**: la cadena avícola es
una secuencia, no cuatro silos. Filtrar sus datos por unidad sin un contrato explícito rompería
la trazabilidad que `GA-REM-008` y `GA-REM-031` certificaron.

Ver `CROSS_MODULE_FLOW_MATRIX.md`.

## 5. Lo que esta auditoría **no** hace

No cambia el estado de certificación de ningún proceso. `14 / 15` sigue siendo cierto en la
dimensión funcional. Lo que se propone es **añadir una segunda dimensión**, no reescribir la
primera.
