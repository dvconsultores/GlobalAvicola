# FLUJOS QUE CRUZAN LA FRONTERA ENTRE UNIDADES

Auditoría del 2026-09-07 · **solo lectura**

---

## 1. Por qué esto no es un detalle

La cadena avícola **es** una secuencia. Progenitoras produce huevo que va a Reproductoras;
Reproductoras produce huevo fértil que va a Incubadora; Incubadora produce pollito que va a
Engorde. Aislar las cuatro unidades sin contrato rompería `P-10`, que es precisamente el proceso
que certifica que esa cadena se puede seguir de punta a punta.

```
El requisito NO es cortar la cadena.
Es decidir qué ve cada lado de ella.
```

## 2. La matriz

| Flow | Source Module | Target Module | Source User Can See | Target User Can See | Shared Record | Decision Gap |
|---|---|---|---|---|---|:--:|
| Huevo de progenitoras → reproductoras | Progenitoras | Reproductoras | hoy **todo** | hoy **todo** | `egg_batches` | **SÍ** |
| Despacho de huevo fértil → incubadora | Reproductoras | Incubadora | hoy todo | hoy todo | `egg_batches` · `egg_dispatch` / `egg_reception_hatchery` | **SÍ** |
| Nacimiento → despacho de pollito | Incubadora | Engorde | hoy todo | hoy todo | `chick_batches` · `chick_dispatch` / `bird_reception` | **SÍ** |
| Transferencia de aves entre granjas | cualquiera | cualquiera | hoy todo | hoy todo | `bird_movements` | **SÍ** |
| Consolidación a SAP | las cuatro | — | hoy todo | — | `consolidated_movements` | **SÍ** |
| Revisión y aprobación | las cuatro | — | hoy todo | — | `operational_events` | **SÍ** |
| Trazabilidad generacional | las cuatro | las cuatro | hoy todo | hoy todo | `egg_batches` · `chick_batches` | **SÍ** |

```
flujos que cruzan ................ 7
plenamente especificados ......... 0
requieren decisión del propietario 7
```

## 3. Las preguntas que ninguna fuente responde

`§22` del encargo prohíbe inventarlas, y con razón: cada una tiene respuestas defendibles y
opuestas.

```
1. Tras despachar huevo a Incubadora, ¿qué ve Reproductoras?
   ¿solo que salió? ¿si llegó? ¿cuántos nacieron de su lote?

2. Antes de recibir, ¿qué ve Incubadora del lote de origen?
   ¿solo la cantidad? ¿la genética? ¿el historial sanitario?

3. Después de recibir, ¿el origen sigue viendo el destino?

4. ¿Un usuario de Engorde puede seguir la trazabilidad hacia atrás
   hasta Progenitoras, o solo hasta su recepción?

5. En revisión y aprobación, ¿un aprobador con una sola unidad
   aprueba solo lo de la suya?

6. En SAP, ¿la consolidación exige ver las cuatro?

7. ¿Una transferencia entre unidades la ve el origen, el destino, o los dos?
```

## 4. El patrón que probablemente haga falta

Sin proponerlo como decisión, el análisis sugiere que **no** basta con «ve» o «no ve»: hará
falta una noción de **vista reducida** — el origen ve que su despacho llegó, sin ver la
operación completa del destino.

```
CROSS_MODULE CONTRACT REQUIRED
```

Eso es un contrato de datos, no una casilla. Y es la parte de esta capacidad que más se parece a
diseño de producto y menos a seguridad.

## 5. Riesgo de no decidirlo

Implementar el filtro por unidad **antes** de responder estas siete preguntas rompería `P-02`,
`P-04`, `P-05`, `P-06` y `P-10`, que están certificados. El orden importa: primero el contrato,
después el filtro.
