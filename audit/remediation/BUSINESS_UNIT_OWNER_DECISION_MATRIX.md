# LAS DOCE DECISIONES, EN UNA PÁGINA

2026-09-07 · resumen de `BUSINESS_UNIT_OWNER_DECISION_DOSSIER.md` · identificadores
**provisionales**, no son `OD-` definitivos

```
MÓDULO RBAC        un permiso       operations · lots · masters …     EXISTE
UNIDAD DE NEGOCIO  una línea        Progenitoras · Reproductora ·     NO EXISTE
                                    Incubadora · Engorde
```

---

## 1. La matriz

| # | Decisión | Origen | Recomendación | Bloquea | Estado |
|:--:|---|:--:|---|:--:|:--:|
| `BU-D01` | Qué ve cada línea al traspasar el producto | auditoría 1 | contrato de traspaso | **spec** | `PENDIENTE` |
| `BU-D02` | Registros sin línea derivable (inspecciones) | auditoría 2 | pendiente de clasificar | **spec** | `PENDIENTE` |
| `BU-D03` | Historial de auditoría entre líneas | auditoría 3 | completo solo con permiso de auditoría | — | `PENDIENTE` |
| `BU-D04` | El analista de SAP ve las cuatro | auditoría 4 | excepción declarada y probada | — | `PENDIENTE` |
| `BU-D05` | Empresas y usuarios que ya existen | auditoría 5 | habilitado hoy · declarado en el alta real | **alta real** | `PENDIENTE` |
| `BU-D06` | Lotes sin tipo de ave | auditoría 6 | segunda fuente: la raza, si se ratifica | — | `PENDIENTE` |
| `BU-D07` | Quién habilita a la empresa y quién concede | auditoría 7 | comercial vs operativo · toca `OD-05` | — | `PENDIENTE` |
| `BU-D08` | Contratado ≠ habilitado | auditoría 8 | separarlos ahora | — | `PENDIENTE` |
| `BU-D09` | Usuario sin ninguna línea | **nueva** | entra, ve lo transversal | **spec** | `PENDIENTE` |
| `BU-D10` | La empresa deja de tener una línea | **nueva** | revocar escritura · conservar histórico | — | `PENDIENTE` |
| `BU-D11` | Contraloría y administración transversales | **nueva** | sí, declarado · **protege `P-14`** | **spec** | `PENDIENTE` |
| `BU-D12` | Qué permisos quedan fuera del filtro | **nueva** | ratificar la frontera | **spec** | `PENDIENTE` |

```
DECISIONES              12       la auditoría había enumerado 8
NUEVAS                   4       D09 · D10 · D11 · D12
DESAPARECIDAS            0       ninguna de las ocho se cae
BLOQUEAN LA SPEC         5       D01 · D02 · D09 · D11 · D12
BLOQUEAN EL ALTA REAL    1       D05
DECIDIDAS                0
```

## 2. Por qué el número cambió de 8 a 12

La auditoría miró **el pasado**: qué hay guardado y cómo clasificarlo. Las cuatro nuevas son del
**régimen permanente**: cómo funcionará el producto cada día después de encenderlo.

| Nueva | Por qué no estaba |
|---|---|
| `BU-D09` | se leyó como problema de migración; ocurre con cada alta a medias, para siempre |
| `BU-D10` | nadie preguntó qué pasa al **quitar** una línea, solo al darla |
| `BU-D11` | exigía cruzar la capacidad nueva con `OD-08`, que se decidió después de la auditoría |
| `BU-D12` | se dio por hecho que la frontera se deduciría sola al implementar |

## 3. Lo que cambió de sitio

```
BU-D05   BLOQUEANTE DE LA SPEC  →  BLOQUEANTE DEL ALTA REAL
```

`ENV-01` —vigente, del propietario— establece que **no hay producción real desplegada** y que los
datos y usuarios actuales son de prueba y certificación. No hay operación que detener. La
decisión sigue haciendo falta; hace falta **más tarde**.

## 4. Lo que resultó no ser una decisión

```
«Registros de doble unidad»    NO EXISTEN
```

La auditoría marcó `egg_batches` y `chick_batches` como `BLOQUEANTE` por pertenecer a dos líneas
a la vez. Verificado contra el modelo: llevan **una columna por cada lado**. La fila no es de
nadie — **la fila es el traspaso**, y cada columna dice a quién alcanza. No hace falta decidir de
quién es, ni añadirles ninguna columna de línea.

## 5. Lo único que cuesta dato nuevo

De las doce, **una sola** obliga a capturar información que hoy no se guarda:

```
BU-D01, flujo 2    que la incubadora vea el huevo ANTES de recibirlo
                   exige que el despacho declare su destino
                   hoy hay destination_farm_id, que es una granja y es opcional
```

Conviene saberlo al decidir: decir «sí» ahí cuesta un campo obligatorio en el despacho, no solo
una regla de lectura.

## 6. El orden en que conviene decidirlas

```
PRIMERO   BU-D11   porque es la única que puede romper algo ya certificado
          BU-D12   porque de ella depende qué significa «no tener líneas»
          BU-D09
LUEGO     BU-D01   la más larga: siete flujos, con su propia matriz
          BU-D02
DESPUÉS   BU-D03 · BU-D04 · BU-D06 · BU-D07 · BU-D08 · BU-D10
AL FINAL  BU-D05   antes del primer cliente real, no antes de construir
```
