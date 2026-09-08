# `R-128` · QUIEN REPARTE ACCESOS NO SE SIRVE A SÍ MISMO

`OD-15` · `AC-S01`…`AC-S05` · 2026-09-09

```
R-128  =  CERRADO
ROJO PREVIO        4 de 16 · los 12 controles pasando
VERDE              16 / 16  ·  backend 754 passed · 49 skipped
SENSIBILIDAD       10 mutaciones · 10 detectadas · 2 rehechas por inválidas
MIGRACIÓN          ninguna       FRONTEND  0 ficheros
```

---

## 1. La regla y dónde vive

```python
# `app/business_units/admin.py::conceder`
if actor is not None and user_id == actor.get("id"):
    raise SegregacionDeFunciones(...)
```

**Va primero, antes que las otras tres puertas.** No es estética: así la negativa no depende de
que el usuario objetivo exista, ni de que la unidad esté habilitada, ni del orden en que alguien
reordene mañana las comprobaciones de abajo. Una regla que dependa del orden de sus vecinas se
rompe cuando alguien las mueve.

Vive en el **servicio**, no en la ruta, de modo que sobrevive a que la superficie se reutilice.

`403` y no `409`: es la misma clase de negativa que `AC15` —«tienes la autoridad y aun así
esto no»— y comparte contrato para que el cliente no aprenda dos.

## 2. Trazabilidad

| `AC` | Qué | Prueba |
|---|---|---|
| `AC-S01` | la auto-concesión se deniega con todo lo demás correcto | `test_s01_el_administrador_no_se_concede_a_si_mismo` |
| `AC-S02` | conceder a otro de la misma empresa sigue funcionando | `test_s02_el_administrador_concede_a_otro_usuario…` |
| `AC-S03` | cero filas · alcance sin cambios · cero auditoría de éxito | `test_s03_la_auto_concesion_denegada_no_deja_rastro` |
| `AC-S04` | no hay excepción por ser el único administrador | `test_s04_no_hay_excepcion_por_ser_el_unico…` |
| `AC-S05` | otro administrador, y el Super Administrador situado, sí pueden | `test_s04_otro_administrador…` · `test_s05_el_super_administrador_situado…` |

**Las dos vías de arranque tienen prueba positiva.** Una regla que dejara a la figura en un
callejón sin salida sería una regla mal puesta, y comprobarlo es tan importante como comprobar
la negativa.

`OD-15.b` deja fuera la **auto-revocación**, con prueba de que sigue permitida: revocarse reduce
privilegio, no lo eleva. Ampliar la regla «por coherencia» habría sido inventar segregación que
nadie pidió.

## 3. Sensibilidad · 10 mutaciones, 10 detectadas

| # | Mutación | Huella | Resultado |
|:--:|---|:--:|:--:|
| `S1` | retirar la guarda | 1 | **2 failed** |
| `S2` | comparar contra el campo equivocado (`company_id`) | 1 | **2 failed** |
| `S3` | permitir la auto-concesión y solo suprimir la auditoría | 1 | **1 failed** |
| `S4` | excepción «si es el único administrador» | 1 | **1 failed** |
| `S5` | dar `business_units:create` a `Supervisor Avícola` | 2 | **1 failed** |
| `S6` | asignar el rol concede todas las unidades habilitadas | 1 | **1 failed** |
| `S7` | añadir comodín al rol sembrado | 1 | **1 failed** ⚠ |
| `S8` | autorizar por nombre de rol | 1 | **1 failed** |
| `S9` | quitar la validación de inquilino en la concesión | 1 | **1 failed** |
| `S10` | la administración de unidades ignora la empresa seleccionada | 1 | **1 failed** |

### `S7` destapó una aserción vacua **mía**

La primera versión de `S7` mutó `dev_seeds.py` cuando la prueba lee `baseline_seeds.py`:
**mutación en el fichero equivocado**, inválida, no contada.

Rehecha contra el fichero correcto… y **siguió sobreviviendo**. El motivo era peor que la
mutación: mi prueba parseaba el texto con `\w+` para el nombre del módulo, y `\w+` **no puede
capturar `*`**. La línea que decía comprobar que el rol no tiene comodín solo podía ser cierta.

Reescrita para **importar la constante** en vez de leer su texto. Ahora `S7` produce rojo.

```
UNA ASERCIÓN QUE NO PUEDE FALLAR NO ES UNA ASERCIÓN
```

### `S6` destapó una prueba débil, también mía

`test_s08` comprobaba que el sujeto sembrado no tenía concesiones. Eso no prueba que **asignar
el rol** no las cree. Reescrita para asignar el rol por la `API` y comprobar después; entonces
`S6` produce rojo.

### `S9` no llegó a instalarse

Ancla duplicada —el mismo bloque aparece en `conceder` y en `revocar`—. El guion abortó, que es
para lo que está. Rehecha con un ancla que solo existe en `conceder`.

```
MUTACIONES VÁLIDAS FINALES     10
INTENTOS INICIALES INVÁLIDOS    2   (`S7` fichero equivocado · `S9` no instalada)
PRUEBAS REFORZADAS POR ELLAS    2   (`s06` vacua · `s08` débil)
CONTADAS COMO DETECCIÓN SIN SERLO   0
```
