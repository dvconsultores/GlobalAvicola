# `P-15` · SEMÁNTICA DE APROBACIÓN EN LOS INDICADORES

Fase de análisis · 2026-09-06

---

## 1. Lo observado

Todos los KPI de `reports/service.py` filtran a cuatro estados:

```python
OperationalEvent.status.in_([
    EventStatus.APPROVED, EventStatus.CONSOLIDATED,
    EventStatus.SENT_TO_SAP, EventStatus.SAP_CONFIRMED,
])
```

De ahí que un lote con actividad registrada pero sin aprobar muestre **cero en todo**.

## 2. Qué dice la norma

| Estado del dato | ¿Cuenta? | Fuente |
|---|:--:|---|
| Borrador (`registered`) | **no** | `GA-REM-022 AC05` — «los KPI **solo consideran eventos aprobados**» |
| Pendiente de revisión / en revisión | **no** | ídem |
| **Aprobado** y posteriores | **sí** | ídem |
| Rechazado | **no** | no está entre los cuatro estados admitidos |
| Cancelado | **no** | ídem |

```
Sin datos aprobados  →  null, con indicador explícito de dato insuficiente
                        (GA-REM-022 AC02), NO cero y NO texto
```

## 3. Las dos preguntas que el encargo dejaba abiertas, cerradas por la norma

**¿Deben incluirse los pendientes?** **No.** `AC05` es explícito y `§21` del encargo lo
refuerza: cambiar la consulta para que el indicador «deje de estar en cero» sería alterar la
semántica del negocio sin requisito que lo respalde.

**¿Es correcto mostrar cero?** **No, cuando no hay datos aprobados.** `AC02` distingue las
dos cosas:

```
0     ·  se midió y el resultado es cero
null  ·  no hay base aprobada sobre la que medir
```

Confundirlas hace que un lote sin aprobar y un lote con mortalidad nula se vean igual.

## 4. ¿Hace falta avisar al usuario?

**Sí, y no por intuición.** `GA-REM-022 AC05` lo exige literalmente:

> Then **la interfaz lo indica**, en lugar de mostrar cero sin explicación.

`§25` del encargo prohíbe inventar un aviso sin requisito; `§26` pide determinar mensaje,
lugar, condición e i18n cuando sí lo hay. Aquí lo hay.

| | |
|---|---|
| Condición | el lote tiene eventos registrados y ninguno aprobado |
| Lugar | la pantalla de indicadores del lote |
| Mensaje | que los indicadores se calculan solo con datos aprobados |
| i18n | clave declarada en ambos idiomas, sin texto embebido |

## 5. Por KPI

Todos comparten el mismo criterio, así que la tabla es corta:

| KPI | Borrador | Pendiente | Aprobado | Sin ninguno aprobado |
|---|:--:|:--:|:--:|---|
| los 15 obligatorios | no | no | **sí** | `null` + aviso |

La uniformidad no es casualidad: el filtro es el mismo en todas las consultas y así debe
seguir. Un indicador que contara pendientes mientras el resto no lo hiciera sería peor que el
defecto actual.
