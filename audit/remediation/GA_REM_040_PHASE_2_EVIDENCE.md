# `GA-REM-040` FASE 2 · SEGURIDAD CENTRAL · EVIDENCIA

2026-09-07 · `T-040-06`, `T-040-07`, `T-040-08` · `T-040-32`…`T-040-34`
· `OD-11` · `OD-09.e`

```
ALCANCE   empresa efectiva · guarda central de unidad · clasificación de las 198 rutas
FUERA     filtro por fila · agregados · contratos · clasificación pendiente
          API de administración · sesión · frontend · P-14 · tareas de fondo
```

---

## 1. Lo que ya existía, y no se ha reescrito

La regla de empresa efectiva **estaba implementada y era correcta** desde `R-48`:

```
usuario normal    manda la base; un token no reclama compañías ajenas
Super Admin       se honra la empresa desplazada por `switch-company`
```

`OD-11` la ratifica. Lo que la fase 2 añade es lo que faltaba **alrededor**, y son tres cosas
concretas, no una reescritura:

| Faltaba | Por qué importaba |
|---|---|
| **Poder invocarla** | vivía dentro de `get_current_user`; un servicio o una tarea de fondo tenían que reimplementarla, y una regla reimplementada acaba divergiendo |
| **Revalidarla** | se comprobaba la autoridad del actor, no que la empresa de destino siguiera existiendo y activa. El token vive treinta minutos y la renovación lo reemite |
| **Dejar rastro** | situarse en otra empresa decide sobre qué datos se opera después, y no constaba en ninguna parte |

## 2. El hallazgo de diseño que `AC-B12` obligó

`OD-09.e` exige que volver a una empresa anterior no reactive la concesión. Al implementarlo
apareció algo que no estaba previsto:

> **«Volvió a la empresa A» es indistinguible de «nunca salió de A»** si no se registra la
> salida.

Con la concesión apuntando a la habilitación de A y el usuario de vuelta en A, el resolutor
vuelve a casar. No hay consulta que lo evite: falta el dato.

De ahí `revoked_at`, y con él una decisión más:

```
UNICIDAD PARCIAL   única entre las concesiones VIVAS
```

Con una restricción total, revocar habría sido **irreversible**: el usuario no podría recuperar
nunca ese acceso, que no es lo que revocar significa.

### 2.1 Una limitación declarada, no escondida

`revocar_concesiones` **existe antes que su llamador**. Hoy ningún camino cambia la empresa de un
usuario:

```
UserUpdate              no acepta `company_id`
switch-company          desplaza el CONTEXTO; no toca `users.company_id`
```

La fase 7, que traerá esa administración, encontrará la regla escrita en vez de tener que
deducirla. **Mientras tanto la garantía vale lo que valga ese futuro llamador**, y las pruebas
mueven al usuario por la operación sancionada —revocar y después cambiar— en lugar de empujar el
campo a mano: hacerlo a mano deja el modelo en un estado que ninguna operación produce, igual que
escribir `role_id` a mano se salta el `RBAC`.

## 3. Trazabilidad

| `AC` | Prueba | Estado |
|---|---|:--:|
| `AC-C09` empresa persistida | `test_ac_c09_para_un_usuario_normal_manda_la_base` | **PASS** |
| `AC-C10` la reclamación ajena se ignora | `test_ac_c10_una_reclamacion_ajena_no_desplaza_el_inquilino` | **PASS** |
| `AC-C11` contexto autorizado y válido | `test_ac_c11_un_actor_autorizado_si_desplaza_el_contexto` · `..._una_empresa_inexistente_no_da_contexto` | **PASS** |
| `AC-C12` revalidado en cada petición | `test_ac_c12_una_empresa_desactivada_deja_de_dar_contexto` | **PASS** |
| `AC-C13` sin contexto no hay acceso | `test_ac_c13_sin_empresa_y_sin_contexto_no_hay_empresa_efectiva` | **PASS** |
| `AC-C14` cambiar no concede unidades | `test_ac_c14_cambiar_de_empresa_no_concede_ninguna_unidad` | **PASS** |
| `AC-C15` toda ruta clasificada | `test_ac_c15_toda_ruta_esta_clasificada` · `..._una_ruta_nueva_sin_clasificar_rompe_el_arranque` | **PASS** |
| `AC-C16` invocable sin `Request` | `test_la_guarda_no_necesita_una_peticion_http` | **PASS** |
| `AC-C08` lo no resuelto deniega | `test_la_guarda_deniega_sin_concesion` · `..._si_la_empresa_apago_la_unidad` · `..._al_usuario_sin_unidades` | **PASS** |
| `AC-B12` volver no reactiva | `test_ac_b12_volver_no_reactiva_la_concesion` · `..._al_volver_hace_falta_una_concesion_nueva` · `..._la_concesion_anterior_sigue_registrada_tras_volver` | **PASS** |
| `AC-F05` sin atajo por rol | `test_el_nombre_del_rol_no_atraviesa_la_guarda` | **PASS** |
| `AC-I06` el cambio se audita | `switch_company` emite `CONTEXT_SWITCHED` en `P-09` | **PASS** |

```
PRUEBAS DE LA FASE 2      25 / 25 PASS
FASE 1 + 1.1              31 / 31 PASS  (sin cambios)
```

## 4. La clasificación de las 198 rutas

| Clase | Rutas | Qué significa |
|---|:--:|---|
| `PUBLICA` | 2 | sin sesión — `login`, `refresh` |
| `CORE` | 15 | autenticada y ajena a toda unidad |
| `CONTROL` | 28 | plano de control de la empresa (`OD-09.b`) |
| `UNIDAD_UNICA` | 22 | pertenece a una cadena concreta |
| `MULTI_UNIDAD` | 119 | puede tocar varias — **sus filas, la fase 3** |
| `CONTRATO` | 12 | traspaso entre unidades — sus campos, la fase 5 |
| **Sin clasificar** | **0** | la guarda de arranque falla si aparece una |

La clasificación de los maestros **no se inventó aquí**: viene de
`MASTER_DATA_BUSINESS_UNIT_SCOPE_MATRIX.md`, donde los veintidós se clasificaron por alcance
semántico del dato y no por dónde está el menú.

### 4.1 Clasificar no es proteger

```
CLASIFICACIÓN DE RUTA   ≠   AISLAMIENTO POR FILA
```

`/api/v1/lots` figura como `MULTI_UNIDAD` y **sigue devolviendo lotes de todas las unidades de la
empresa**. Lo mismo los `KPI`, los paneles, los reportes y las exportaciones. Saber qué hay que
proteger no es haberlo protegido; es la fase 3 y no ha empezado.

Hay una prueba dedicada a que nadie lea la clasificación como una certificación:
`test_lots_es_multi_unidad_y_eso_no_la_hace_segura`.

## 5. Sensibilidad · `GA-REM-016 AC13`

Diez mutaciones, sobre un árbol verde ya comiteado, con instantánea y restauración.

| # | Mutación | Resultado | Cayeron |
|:--:|---|:--:|:--:|
| 1 | confiar en la reclamación del token sin más | **RED** | 2 |
| 2 | cualquiera puede cambiar de empresa | **RED** | 1 |
| 3 | ignorar la empresa persistida | **RED** | 5 |
| 4 | no revalidar que la empresa siga activa | **RED** | 2 |
| 5 | ignorar la habilitación de la empresa | **RED** | 4 |
| 6 | ignorar la concesión del usuario | **RED** | 16 |
| 7 | casar la unidad por el catálogo, sin empresa | **RED** | 3 |
| 8 | la concesión revocada revive | **RED** | 4 |
| 9 | atajo por nombre de rol en la guarda | **RED** | 1 |
| 10 | admitir rutas sin clasificar | **RED** | 1 |

La 6 rompe dieciséis porque su implementación alternativa —devolver todo lo habilitado— es
coherente pero cambia la respuesta de casi todo el conjunto. Se registra el número tal cual: una
mutación ancha demuestra menos que una estrecha, y conviene que se vea.

```
MUTACIONES        10 / 10 detectadas
RESTAURACIÓN      los tres ficheros idénticos a su instantánea · árbol limpio
PATRONES          doce comprobaciones positivas tras restaurar, no solo `git diff`
```

## 6. Dos cosas que la suite existente cazó

**`AuditLog.action` es un enum nativo de PostgreSQL.** Al inspeccionarlo, `Column.type` se
presentaba como `VARCHAR(17)` y parecía texto libre; añadir `CONTEXT_SWITCHED` solo en Python
dejaba **cada `switch-company` en 500**. Lo detectó
`test_los_enums_de_python_existen_en_postgresql`, que existe justo para este hueco desde que
`EGG_RECEPTION_CLASSIFICATION` faltó en `eventtype`. La migración añade el `ALTER TYPE`.

**Una prueba de estructura tuvo que portarse.**
`test_la_fuente_del_contexto_es_una_sola_y_esta_documentada` comprobaba el **texto fuente** de
`get_current_user`. La propiedad que defiende —una sola fuente de contexto— no cambia, pero la
regla se movió a `app/tenancy.py`. Se porta a los dos extremos, y queda **más fuerte**: que la
capa de petición **delega**, y que **no conserva una segunda copia** de la regla. Las pruebas de
comportamiento del mismo archivo pasaron sin tocarlas, que es la prueba real de que nada se
rompió.

## 7. Las doce preguntas de aceptación

| # | Pregunta | Respuesta | Evidencia |
|:--:|---|:--:|---|
| 1 | ¿Un usuario normal puede fingir otra empresa en el token? | **NO** | `AC-C10` |
| 2 | ¿Un actor no autorizado puede usar `switch-company`? | **NO** | `test_un_usuario_normal_no_puede_cambiar_de_empresa` |
| 3 | ¿Un actor autorizado establece contexto de empresa? | **SÍ** | `AC-C11` |
| 4 | ¿Cambiar de empresa concede unidades? | **NO** | `AC-C14` |
| 5 | ¿La concesión de A satisface a B? | **NO** | `test_la_guarda_no_cruza_empresas_con_el_mismo_codigo` |
| 6 | ¿Una unidad apagada por la empresa pasa la guarda? | **NO** | `test_la_guarda_deniega_si_la_empresa_apago_la_unidad` |
| 7 | ¿Pasa un usuario sin concesión? | **NO** | `test_la_guarda_deniega_sin_concesion` |
| 8 | ¿Un usuario sin unidades sigue usando `CORE`? | **SÍ** | 15 rutas `CORE` no exigen unidad · `BU-D09` |
| 9 | ¿El nombre del rol atraviesa la guarda? | **NO** | `test_el_nombre_del_rol_no_atraviesa_la_guarda` |
| 10 | ¿Revive la concesión al volver a la empresa A? | **NO** | `AC-B12` |
| 11 | ¿Están las rutas clasificadas centralmente? | **SÍ** | 198 / 198 · 0 sin clasificar |
| 12 | ¿Se ha logrado aislamiento por fila? | **NO** | fase 3, no iniciada |

## 8. Regresión

```
BACKEND                            549 passed · 49 skipped     (eran 524)
AUTENTICACIÓN                      verde · login, renovación y cambio de empresa
RBAC                               verde · el resolutor no toca permisos
AISLAMIENTO DE EMPRESA             verde · incluida la suite multiempresa completa
FASE 1 + 1.1                       verde · 31 / 31
MIGRACIÓN                          cabeza única `r8s9t0u1v2w3` · base limpia PASS
T-025                              PASS · ninguna tabla nueva · 55 sin cambios
FRONTEND                           0 archivos
FILAS FILTRADAS                    0
```

## 9. Estado

```
CERTIFICACIÓN FUNCIONAL             14 / 15   sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD   0 / 15   sin cambios
```

**Ningún proceso recibe un `PASS` por esto.** Existe una guarda central y una clasificación
completa; ningún proceso está todavía acotado por unidad, porque nada filtra filas. Otorgarlo
sería la evidencia que `AC13` prohíbe.

## 10. Para la fase 3

```
GA-REM-040 · FASE 3 — AISLAMIENTO POR FILA     T-040-09 · T-040-10
NO INICIADA
```

Lo que la fase 2 deja preparado y la fase 3 tendrá que usar:

```
resolver_empresa_efectiva(db, user, reclamada, puede_cambiar)   →  la empresa
unidades_efectivas(db, user, company_id)                        →  el alcance
exigir_acceso_a_unidad(db, user, code, company_id)              →  la comprobación
route_scope.clasificar(camino) · unidad_requerida(camino)       →  qué exige cada ruta
```

Las 119 rutas `MULTI_UNIDAD` son el trabajo de la fase 3, y `/api/v1/lots` es la primera.
