# ÁREA FRENTE A UNIDAD DE NEGOCIO

Auditoría del 2026-09-07 · **solo lectura**

---

## 1. No son lo mismo, y conviene no fundirlas

```
AREA     dónde trabaja una PERSONA        organigrama      GA-REM-039, recién certificado
MÓDULO   qué CADENA PRODUCTIVA existe     producto         no existe todavía
```

Un «Área de Producción» puede abarcar Reproductoras **e** Incubadora. Y una empresa pequeña
puede tener una sola área con las cuatro unidades. No hay correspondencia uno a uno.

## 2. La matriz

| Dimensión | Qué responde | Dónde vive hoy | Alcance |
|---|---|---|---|
| `Company` | de quién es el dato | `company_id` en 29 tablas | inquilino |
| **`Area`** | dónde pertenece la persona | `areas` · `users.area_id` · `lots.area_id` | organigrama |
| **Unidad de negocio** | qué cadena productiva | `BirdTypeEnum`, solo en `lots` y `breeds` | **no modelada** |
| `Role` | qué puede hacer | `roles` · `permissions` | acción |

## 3. La tentación que hay que evitar

`lots.area_id` ya existe. Sería cómodo reutilizarlo como si fuera la unidad de negocio: ya está
en el lote, ya se propaga a los eventos, ya lo usa `P-14`.

Sería un error, y del mismo tipo que confundir rol con área:

```
un área puede contener varias unidades
una unidad puede repartirse en varias áreas
```

Fundirlos haría imposible expresar «el gerente del Área de Producción, que abarca Reproductoras
e Incubadora» — que es justo el caso realista.

## 4. Dónde sí se relacionan

En el destinatario de una notificación:

```
destinatario = empresa ∩ (originador ∪ rol) ∩ área del evento ∩ unidad del evento
```

Las dos últimas son filtros **independientes** que se aplican a la vez. Un supervisor del área
correcta pero sin la unidad concedida no debería recibir; y al revés tampoco.

## 5. Conclusión

La relación existe pero es de composición, no de sustitución. `GA-REM-039` no resuelve nada de
esta capacidad, y esta capacidad no invalida nada de `GA-REM-039`.
