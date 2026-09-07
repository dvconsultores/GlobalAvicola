# `P-14` · NOTIFICACIONES Y ALERTAS — CADENA COMPLETA

`docs/02 §3.14` · `docs/10 §6.2` · `OD-07` · `GA-REM-038`

`docs/02 §3.14` enumera **seis** tipos de aviso. La cadena de `P-14` no es «que funcione la
campana»: es que cada uno de esos seis llegue a quien debe. Esta matriz los recorre uno a uno.

---

## 1. El canal

| # | Paso | Requisito | Precondición | Acción | Esperado | Prueba |
|:--:|---|---|---|---|---|---|
| 1 | El canal es interno | `OD-07` | — | — | existe bandeja en el producto | `T-038-11`, `UI_E2E` |
| 2 | Ningún canal externo | `OD-07` | — | — | ni correo, ni SMS, ni push, ni suscripciones | `T-038-11`, `AC02` `UI_E2E` |

## 2. Los seis tipos de `§3.14`

Tras `OD-08`, el destinatario de todos sale de la misma regla: los explícitos de fuentes
anteriores más quien cargó el dato, los administradores, la contraloría y los supervisores de
esa empresa, deduplicados.

| # | Tipo (nombre literal) | Disparador | Destinatarios | Estado |
|:--:|---|---|---|:--:|
| 3 | **Registro pendiente de revisión > 24h** | `notifications/sla.py` · 24 h desde la transición, tomada de la auditoría | `OD-08` | **PASS** |
| 4 | **Registro rechazado (notificar al operador)** | `review/service.py:409` | operador **∪** `OD-08` | **PASS** |
| 5 | **Mortalidad > umbral configurable** | alerta `high_mortality`, umbral en `settings` | `OD-08` | **PASS** |
| 6 | **Peso fuera de estándar** | alerta `weight_deviation` (`GA-REM-037`) | `OD-08` | **PASS** |
| 7 | **Error de envío SAP** | `sap/service.py:367,451` | `Analista SAP` **∪** `OD-08` | **PASS** |
| 8 | **Lote próximo a cierre** | **no existe**; «próximo» sin definir en ninguna fuente | — | **BLOCKED_BY_OWNER_DECISION** |

### Y una función de `OD-08` que no se puede resolver

| Función | Estado |
|---|:--:|
| persona que cargó el dato · administradores · contraloría · supervisor | **PASS** |
| **gerente del área** | **BLOCKED_BY_MODEL_GAP** — no hay áreas ni rol de gerencia |

## 3. El ciclo de vida del aviso

| # | Paso | Requisito | Precondición | Acción | Esperado | Prueba |
|:--:|---|---|---|---|---|---|
| 9 | Se crea con el hecho | `AC03`, `AC05` | evento del negocio confirmado | rechazar | aviso con empresa, destinatario y entidad | `T-038-01` |
| 10 | No se crea si el hecho no ocurre | `AC06` | evento no rechazable | rechazar | cero avisos | `T-038-02` |
| 11 | Consultar no crea | `AC07` | bandeja con avisos | listar tres veces | el número no cambia | `T-038-03` |
| 12 | Un reintento no duplica | `AC08` | envío fallido sin leer | reintentar | sigue habiendo uno | `T-038-10` |
| 13 | Se lista con su total | `AC11` | tres avisos | listar con `limit=2` | dos filas y `X-Total-Count ≥ 3` | `T-038-06` |
| 14 | El contador es exacto | `AC12` | 5 creados, 2 leídos | contar | exactamente 3 | `T-038-04` |
| 15 | Marcar es idempotente | `AC13` | aviso sin leer | marcar dos veces | mismo `read_at`, mismo contador | `T-038-05` |

## 4. La bandeja es de una persona

| # | Comprobación | Control | Tratamiento | Estado |
|:--:|---|---|---|:--:|
| 16 | Propiedad dentro de la empresa | el destinatario la lee → `200` | otro usuario de la misma empresa → `404` | **PASS** |
| 17 | Aislamiento entre empresas | — | usuario de otra empresa → `404` y no aparece en su lista | **PASS** |

El sujeto negativo del paso 16 es el aprobador, con empresa propia. No el Super Administrador:
su exención de tenencia haría pasar la prueba sin comprobar nada.

## 5. La experiencia

| # | Paso | Requisito | Esperado | Prueba |
|:--:|---|---|---|---|
| 18 | Campana con número de no leídas | `AC16` | visible en escritorio y móvil, con el número **en el nombre accesible** | `UI_E2E`, `vitest` |
| 19 | El panel dice qué pasó y cuándo | `AC17` | título, detalle, antigüedad | `UI_E2E`, `vitest` |
| 20 | Leída y no leída se distinguen **por texto** | `AC17` | «Sin leer» / «Leída» | `UI_E2E`, `vitest` |
| 21 | Abrir marca leída y baja el contador | `AC18` | sin recargar el navegador | `UI_E2E`, `vitest` |
| 22 | Lleva a la entidad relacionada | `AC17` | `/operations/{id}` | `UI_E2E` |
| 23 | Sin destino no se navega | `AC17` | `sap_payload` se lee y no enlaza | `vitest` |
| 24 | Vacío, cargando y error son distintos | `AC19` | un fallo de API **no** es bandeja vacía | `vitest` |
| 25 | Paridad `i18n` | `AC20` | `es` = `en` | conteo |

## 5 bis. Los destinatarios, comprobados uno a uno

| # | Comprobación | Estado |
|:--:|---|:--:|
| 26 | Quien cargó el dato recibe, en los cuatro eventos con originador | **PASS** |
| 27 | Los administradores de la empresa reciben | **PASS** |
| 28 | La contraloría recibe | **PASS** |
| 29 | Los supervisores reciben | **PASS** |
| 30 | El gerente del área | **BLOCKED_BY_MODEL_GAP** |
| 31 | El operador sigue recibiendo el rechazo (`docs/02 §3.14`) | **PASS** |
| 32 | El `Analista SAP` sigue recibiendo el error de envío (`docs/10 §6.2`) | **PASS** |
| 33 | Quien cumple dos condiciones recibe **un** aviso | **PASS** |
| 34 | Las mismas funciones en otra empresa reciben **cero** | **PASS** |

## 6. Recuento

```
34 pasos · PASS 32 · BLOQUEADOS 2
    2 de canal
    5 de 6 tipos normativos          ← queda «lote próximo a cierre»
   13 de ciclo de vida y aislamiento
    8 de experiencia
    9 de destinatarios               ← queda el gerente del área
```

**`P-14` = `PARTIAL`.** No por un defecto: cinco de los seis tipos que `docs/02 §3.14` exige
están cubiertos y funcionan de extremo a extremo. El sexto no tiene semántica, y
`GA-REM-016 AC05` no admite certificar por muestra — cinco de seis sigue siendo una muestra.

## 7. Qué falta exactamente

```
OD-08 · destinatarios ......... RESUELTO
OD-08 · semántica temporal .... ABIERTO

  · «lote próximo a cierre»: ¿qué es «próximo»?
    La única aparición de la frase en el repositorio es la línea que la enumera.
    `Lot.end_date` es la fecha REAL de cierre, no una prevista, y no hay `planned_end_date`.

  · Recurrencia del aviso de «> 24h»: ¿una vez o mientras siga pendiente?
    Mientras tanto se emite una sola vez, con idempotencia.

MODELO
  · gerente del área: no hay tabla de área ni rol de gerencia.
    El usuario solo se asocia a una empresa y a un rol.
```

## 8. Evidencia

| Nivel | Archivo | Resultado |
|---|---|:--:|
| Creación, destinatario, lectura, aislamiento | `backend/tests/test_notifications.py` | **11/11** |
| Experiencia | `e2e/proceso-p14-notificaciones.spec.ts` | **5/5** `UI_E2E` |
| Campana y estados | `frontend/src/components/notifications/__tests__` | **8/8** |
| Destinatarios de `OD-08` | `backend/tests/test_notification_recipients.py` | **9/9** |
| Regresión backend | suite completa | **469 passed · 49 skipped** |
| Regresión `E2E` | 17 suites | **129 passed** |
| Regresión `vitest` | suite completa | **82 passed** |
