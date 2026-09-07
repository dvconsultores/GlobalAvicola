# REPORTES Y EXPORTACIONES FRENTE A LA UNIDAD DE NEGOCIO

Auditoría del 2026-09-07 · **solo lectura**

---

## 1. Dónde vive la exportación

`R-88` lo estableció en su día y sigue siendo cierto: **la exportación a Excel y PDF ocurre en
el cliente**, en `frontend/src/utils/export.ts`, con `SheetJS` y `jsPDF`. No hay endpoint de
exportación en el backend.

Eso tiene una consecuencia directa para esta auditoría:

```
El cliente exporta LO QUE LA API LE DIO.
Si la API filtra por unidad, la exportación queda filtrada sola.
Si no filtra, ninguna medida en el cliente lo arregla.
```

## 2. La matriz

| Report/Export | Origen | Unidad | Filtro actual | Riesgo | Nota |
|---|---|---|---|:--:|---|
| Reporte de lote | `/reports/lot/{id}` | derivable | empresa | **P1** | el detalle completo de un lote ajeno |
| Diferencias SAP | `/reports/sap-comparison` | las cuatro | empresa | **P2** | decisión: ¿se filtra? |
| Auditoría por usuario | `/audit?user_id=` | multi | empresa | **P1** | decisión — ver `P-09` |
| Auditoría por lote | `/audit?lot_id=` | derivable | empresa | **P1** | ídem |
| Reporte de estados | `reports/service.py` · `event_summary.by_status` | las cuatro | empresa | **P1** | agregado |
| Exportación Excel | cliente, sobre datos de la API | hereda | **ninguno propio** | **hereda** | `utils/export.ts` |
| Exportación PDF | ídem | hereda | ninguno propio | hereda | ídem |
| Exportación de artefacto SAP | `sap/adapter.py` · ficheros | las cuatro | empresa | **P2** | genera fichero en disco |

```
auditados ......... 8
seguros por unidad . 0
```

## 3. El artefacto SAP merece mención aparte

`ManualSapAdapter` escribe **ficheros** en `SAP_EXPORT_DIR` con el contenido consolidado de la
empresa. Es la única salida que persiste fuera de la base y fuera del control de sesión: quien
tenga acceso al directorio ve las cuatro unidades.

No se propone tocarlo —`P-08` está fuera de alcance—, pero queda registrado: cualquier filtro
por unidad que se implemente en las consultas **no alcanza** a un fichero ya escrito.

## 4. Conclusión

No hace falta una matriz de exportación separada del backend, porque **no hay exportación en el
backend**. Arreglar la API arregla la exportación. La única excepción es el artefacto SAP.
