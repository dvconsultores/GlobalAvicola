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

| # | Tipo | Disparador | Destinatario | Fuente del destinatario | Estado |
|:--:|---|---|---|---|:--:|
| 3 | **Registro rechazado** | `review/service.py:409` | `event.registered_by_id` | `docs/02 §3.14`, literal | **PASS** |
| 4 | **Error de envío SAP** | `sap/service.py:367,451` | rol `Analista SAP` | `docs/10 §6.2`, literal | **PASS** |
| 5 | Mortalidad > umbral | existe (`high_mortality`) | — | **ninguna fuente lo dice** | **FAIL** — `OD-08` |
| 6 | Peso fuera de estándar | existe (`weight_deviation`) | — | **ninguna fuente lo dice** | **FAIL** — `OD-08` |
| 7 | Pendiente de revisión > 24 h | **no existe** (temporal, sin planificador) | — | ninguna | **FAIL** — `OD-08` |
| 8 | Lote próximo a cierre | **no existe**; «próximo» sin definir | — | ninguna | **FAIL** — `OD-08` |

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

## 6. Recuento

```
25 pasos · PASS 21 · FAIL 4
    2 de canal
    2 de 6 tipos normativos    ← aquí está el hueco
   13 de ciclo de vida y aislamiento
    8 de experiencia
```

**`P-14` = `PARTIAL`.** No porque el canal falle —funciona de extremo a extremo— sino porque
cuatro de los seis tipos que `docs/02 §3.14` exige no tienen a quién avisar. `GA-REM-016 AC05`
no admite certificar por muestra, y dos de seis es una muestra.

## 7. Qué falta exactamente

```
OD-08 = OWNER_DECISION_REQUIRED

  · ¿quién recibe el aviso de mortalidad sobre umbral?
  · ¿quién recibe el de peso fuera de la curva estándar?
  · «pendiente de revisión > 24 h»: ¿a quién, y con qué mecanismo?
    (es temporal, y el proyecto no tiene planificador)
  · «lote próximo a cierre»: ¿qué es «próximo», y a quién se avisa?
```

Los dos primeros ya tienen disparador funcionando: solo falta la persona. Los dos últimos
necesitan además una decisión de arquitectura que `OD-07` no tomó, porque resolvió el canal y
solo el canal.

## 8. Evidencia

| Nivel | Archivo | Resultado |
|---|---|:--:|
| Creación, destinatario, lectura, aislamiento | `backend/tests/test_notifications.py` | **11/11** |
| Experiencia | `e2e/proceso-p14-notificaciones.spec.ts` | **5/5** `UI_E2E` |
| Campana y estados | `frontend/src/components/notifications/__tests__` | **8/8** |
| Regresión backend | suite completa | **460 passed · 49 skipped** |
| Regresión `E2E` | 17 suites | **129 passed** |
| Regresión `vitest` | suite completa | **82 passed** |
