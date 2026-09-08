# LOS 22 MAESTROS FRENTE A LA UNIDAD DE NEGOCIO

`GA-REM-040` fase 1 · pre-vuelo obligatorio · 2026-09-07 · **sin cambiar ningún maestro**

---

## 1. Por qué se clasifica ahora y no al filtrar

`OD-09.b` decidió que la frontera entre plano de control y plano operativo se **ratifica**, no
se deduce durante la implementación. `GA-REM-040 §12` añadió la condición concreta: los
veintidós maestros se clasifican **una vez, en el catálogo**, y no pantalla por pantalla.

Dejarlo para la fase 3 significaría que cada listado eligiera por su cuenta, que es exactamente
la opción `C` que el propietario descartó.

## 2. El criterio

```
SE CLASIFICA POR       de quién es el dato, semánticamente
NO SE CLASIFICA POR    dónde está el menú · qué página lo pinta
                       cómo se llama el router · qué le resulta cómodo a quien programa
```

Vocabulario de `GA-REM-040 §12`, sin taxonomía paralela.

## 3. La matriz

Las veintidós entidades verificadas contra `Base.metadata` el 2026-09-07: las veintidós existen.

| Maestro | Entidad real | Alcance semántico | Evidencia | ¿Campo de unidad? | Fase |
|---|---|---|---|:--:|:--:|
| Empresas | `companies` | **`CORE` de empresa** | es el inquilino mismo | **no** | — |
| Áreas funcionales | `areas` | **`CORE` de empresa** | `company_id` · organigrama (`GA-REM-039`) | **no** | — |
| Fases productivas | `productive_phases` | **global de producto** | sin `company_id`; invariante del dominio | **no** | — |
| Granjas | `farms` | **compartido** | `company_id`; **una granja aloja varias unidades** | **no** | 3 · §5 |
| Galpones | `houses` | **compartido** | `farm_id`; hereda de la granja | **no** | 3 · §5 |
| Incubadoras | `hatcheries` | **de una unidad** · Incubadora | `company_id`; su razón de ser es incubar | no — se deriva | 3 |
| Incubadoras (máquina) | `incubators` | **de una unidad** · Incubadora | `hatchery_id` | no — vía incubadora | 3 |
| Nacedoras | `hatchers` | **de una unidad** · Incubadora | `hatchery_id` | no — vía incubadora | 3 |
| Líneas genéticas | `genetic_lines` | **compartido** | `company_id`; una línea cruza la cadena entera | **no** | 3 |
| Curvas de peso | `genetic_weight_curves` | **compartido** | sin `company_id`: cuelga de la línea genética | **no** | 3 |
| Razas | `breeds` | **con unidad explícita** | **`bird_type`** — el único maestro que ya la lleva | ya existe | 3 |
| Tipos de alimento | `feed_types` | **compartido** | `company_id`; transversal | **no** | 3 |
| Vacunas | `vaccines` | **compartido** | `company_id`; transversal | **no** | 3 |
| Medicamentos | `medications` | **compartido** | `company_id`; transversal | **no** | 3 |
| Causas de mortalidad | `mortality_causes` | **compartido** | `company_id`; transversal | **no** | 3 |
| Causas de descarte | `cull_causes` | **compartido** | `company_id`; transversal | **no** | 3 |
| Transportes | `transports` | **compartido** | `company_id`; el mismo camión sirve a varias | **no** | 3 · 5 |
| Plantas de proceso | `processing_plants` | **de una unidad** · Engorde | `company_id`; es el destino del engorde | no — se deriva | 3 |
| Motivos de rechazo | `rejection_reasons` | **compartido** | `company_id`; del flujo de revisión | **no** | 3 |
| Tipos de corrección | `correction_types` | **compartido** | `company_id`; del flujo de corrección | **no** | 3 |
| Proveedores | `suppliers` | **compartido** | `company_id`; transversal | **no** | 3 |
| Referencias SAP | `sap_references` | **multi-unidad** | `company_id`; el consolidado agrupa las cuatro | **no** | 5 |

```
CLASIFICADOS            22 / 22
SIN RESOLVER             0
CAMPOS DE UNIDAD NUEVOS  0        ninguno hace falta
BLOQUEA LA FASE 1        NO
```

## 4. Ningún maestro necesita una columna de unidad

Es el resultado más útil de este pre-vuelo, y conviene decirlo explícito:

```
DE UNA UNIDAD      hatcheries · incubators · hatchers · processing_plants
                   su unidad se DERIVA de su naturaleza, no se guarda:
                   una incubadora es de Incubadora por serlo

CON UNIDAD         breeds — ya lleva `bird_type` desde antes de todo esto

COMPARTIDOS        el resto — asignarles una unidad sería falsear el dato
```

Añadir `business_unit_id` a un maestro compartido para «hacer funcionar el filtro» duplicaría
el maestro cuatro veces en la práctica, que es lo que `GA-REM-040 §12` prohíbe.

## 5. Lo que queda abierto, y de qué clase es

**Las granjas y los galpones.** Están clasificados —compartidos— y eso no está en duda. Lo que
falta decidir es de **fila**, no de clasificación:

> Una granja aloja galpones de reproductora y de engorde. Un usuario que solo tiene Engorde,
> ¿ve la granja?

No se puede responder desde la fila de la granja, porque la granja no tiene unidad; se responde
desde los lotes que aloja. **Es una decisión de la fase 3**, no un hueco de spec y no un
bloqueante de la fase 1: el fundamento no toca `farms` ni depende de esa respuesta.

Se registra aquí para que la fase 3 no la descubra a mitad de camino.

## 6. Alcance de este documento

```
MAESTROS MODIFICADOS       0
COLUMNAS AÑADIDAS          0
FILTROS APLICADOS          0
```

Clasificar no es filtrar. El filtro por fila es la fase 3.
