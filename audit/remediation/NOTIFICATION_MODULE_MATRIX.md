# NOTIFICACIONES FRENTE A LA UNIDAD DE NEGOCIO

Auditoría del 2026-09-07 · los seis eventos de `P-14` · **solo lectura**

---

## 1. La pregunta de `§37`

```
¿Un destinatario que califica por ROL debe recibir avisos de una unidad
de negocio que no tiene concedida?
```

Hoy la pregunta ni siquiera se plantea: `resolver_destinatarios` filtra por **empresa** y por
**área**, y no sabe nada de unidades. Un contralor de una empresa con las cuatro unidades recibe
los seis tipos de aviso de las cuatro.

## 2. La matriz

| Event | Origin Module | Recipient Rule | Recipient Must Have Module? | Cross-Module? | Decision Gap |
|---|---|---|:--:|:--:|:--:|
| Registro pendiente de revisión > 24h | derivable vía `lot_id` (**nulable**) | originador ∪ admin ∪ contralor ∪ gerente/supervisor del área | **hoy NO** | no | **sí** |
| Registro rechazado | ídem | operador ∪ `OD-08` | hoy NO | no | **sí** |
| Mortalidad > umbral | ídem | `OD-08` | hoy NO | no | **sí** |
| Peso fuera de estándar | ídem | `OD-08` | hoy NO | no | **sí** |
| **Error de envío SAP** | **las cuatro** (el consolidado agrupa) | `Analista SAP` ∪ `OD-08` | hoy NO | **sí** | **sí** |
| **Lote próximo a cierre** | `Lot.bird_type` — el único con unidad directa | `OD-08` | hoy NO | no | **sí** |

```
origen de módulo resoluble ......... 5 / 6 (con `lot_id` no nulo)
                                     1 / 6 cruza por naturaleza (SAP)
acceso de módulo exigido hoy ....... NO en los seis
```

## 3. El aviso de SAP es el caso difícil

Un `SapPayload` fallido corresponde a un `ConsolidatedMovement` que agrupa eventos de **un**
lote — pero el trabajo de exportación consolida las cuatro unidades a la vez. El `Analista SAP`
que debe enterarse del fallo es, por definición, alguien que trabaja con las cuatro.

Exigirle acceso a la unidad del lote fallido le impediría hacer su trabajo. Es un caso donde la
regla de módulo debe ceder ante la normativa de `docs/10 §6.2`, y eso es una **excepción que
alguien tiene que autorizar**.

## 4. El aviso de las 24 horas, en eventos sin lote

`farm_inspection` y `hatchery_inspection` pueden quedar pendientes de revisión sin tener lote.
Su unidad no es derivable. ¿A quién se avisa? Hoy, a todos los que califican por rol.

## 5. Lo que no se toca

Esta auditoría **no modifica `P-14`**. Lo que registra es que su regla de destinatarios —recién
certificada— tendrá que ganar un filtro más cuando exista el modelo de unidades:

```
destinatario actual  =  empresa  ∩  (originador ∪ rol ∪ área)
destinatario futuro  =  lo anterior  ∩  tiene la unidad del evento
                        salvo excepción normativa (Analista SAP)
```

---

## Resolución · `OD-09.a` (2026-09-07)

La pregunta de `§1` —«¿un destinatario que califica por rol debe recibir avisos de una unidad de
negocio que no tiene concedida?»— está contestada por el propietario:

```
SÍ, si su función es de control.        BU-D11 = C  →  OD-09.a
```

### La distinción que hay que conservar al implementar

```
DESTINATARIO OPERATIVO             DESTINATARIO DE CONTROL
recibe por su vínculo con el       recibe por su función de control
dato: lo registró, lo opera,       sobre la EMPRESA
lo supervisa en su área

originador · operador              administración · contraloría
gerente y supervisor del área      `Analista SAP` para el error de SAP

→ acotado por unidad, cuando       → toda la empresa, sin filtrar por
  exista el eje                      concesión de unidad
```

**Recibir un aviso es visibilidad de control, no autoridad operativa.** Que a un contralor le
llegue la alerta de un lote de incubadora no le da permiso para modificarlo: el aviso lo entera,
no lo autoriza.

### Lo que queda prohibido

```
FILTRAR EN SILENCIO los avisos de administración y contraloría
por concesión de unidad de negocio
```

Sería incumplir `OD-08` sin que ninguna prueba actual lo detectara, y es exactamente el riesgo
que esta matriz señaló. Un aviso que no llega es indistinguible de un problema que no ocurrió.

### Alcance

```
SIEMPRE DENTRO DE LA MISMA EMPRESA
```

El `Super Administrador` global —sin empresa— sigue sin resolverse como destinatario de ninguna,
tal como `OD-08` y `AC-A09` ya exigían. `OD-09` no lo cambia.

### Estado

```
P-14                          CERTIFIED · sin cambios · no se reabre
Código modificado             ninguno
Impacto registrado            documental, para cuando exista GA-REM-040
```
