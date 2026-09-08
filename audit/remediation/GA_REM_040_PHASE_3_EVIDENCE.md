# `GA-REM-040` FASE 3 · AISLAMIENTO POR FILA · EVIDENCIA

2026-09-07 · `T-040-09` · `T-040-10`

```
LO QUE SE CIERRA   la fuga demostrada en la fase 2: `/lots` devolvía los lotes de todas
                   las cadenas de la empresa aunque la ruta estuviera clasificada
FUERA              agregados y KPI (4) · contratos de traspaso (5) · clasificación
                   pendiente (6) · API de administración (7) · sesión (8) · frontend (9)
```

---

## 1. La afirmación que esta fase deja demostrada

```
PERTENECER A LA EMPRESA   ES NECESARIO   PERO NO SUFICIENTE
```

Misma empresa, mismo endpoint, mismo permiso `RBAC`. Lo único distinto es la concesión de
unidad, y eso basta para que el lote de otra cadena desaparezca — del listado, del detalle, de
la mutación y del total.

## 2. Inventario de entidades

Reconstruido de `SHARED_ENTITY_ROW_SCOPE_MATRIX.md`, que documenta dieciséis entidades
compartidas.

| Entidad | Empresa | Unidad derivable | Mecanismo | ¿Traspaso? | Fase |
|---|:--:|:--:|---|:--:|:--:|
| `lots` | sí | **sí** | `bird_type` | no | **3 · HECHO** |
| `lot_phases` | vía lote | **sí** | `lot_id` → lote acotado | no | **3 · HECHO** |
| `opening_balances` | vía lote | **sí** | `lot_id` → lote acotado | no | **3 · HECHO** |
| `operational_events` | sí | parcial | `lot_id` **nulable** | no | 3 parcial / **6** |
| `bird_movements` · `egg_movements` · `feed_movements` | vía evento | parcial | cadena | no | 3 parcial / **6** |
| `inspection_details` | vía evento | **no** | el evento puede no tener lote | no | **6** |
| `hatchery_params` | vía evento | inferencia | — | no | **6** |
| `operational_alerts` | sí | parcial | `lot_id` | no | 4 / 6 |
| `notifications` | sí | **no** | entidad relacionada | no | **10** |
| `audit_logs` | sí | **no** | `lot_id` nulable | no | `BU-D03` |
| `egg_batches` · `chick_batches` | sí | **cruzan** | dos lados explícitos | **SÍ** | **5** |
| `consolidated_movements` | sí | parcial | `lot_id` | contrato | **5** |
| `approval_actions` · `correction_logs` | vía evento | parcial | cadena | no | 3 parcial / **6** |

```
A · propiedad única y derivable      3      lots · lot_phases · opening_balances
B · compartida y derivable por fila  0      (las candidatas dependen de eventos sin lote)
C · traspaso                         3      egg_batches · chick_batches · consolidated
D · CORE / de empresa                —      fuera de esta fase por definición
E · no clasificable                  7      dependen de la fase 6
```

**Solo `A` se implementa.** El resto queda declarado con su fase, no aplazado en silencio.

## 3. `lots` → unidad de negocio

```
Lot.bird_type   Enum(BirdTypeEnum)   grandparent · breeder · hatchery · broiler
                NULABLE
```

**Determinista donde el campo está.** Y `BirdTypeEnum` **no** es el control de acceso: quién
puede ver qué lo deciden `business_units`, `company_business_units` y `user_business_units`. El
enum solo casa la fila con el alcance ya resuelto. Si mandara el enum, cambiar un valor de
dominio cambiaría quién ve qué.

Un lote **sin** `bird_type` no se atribuye a nadie y **no se muestra**. Se deniega, no se abre:
`OD-10.c` decidió que lo no clasificable quede pendiente de clasificar, y esa bandeja es la fase
6. Es dependencia declarada, no olvido.

## 4. La arquitectura

```
unidades efectivas (fase 1.1/2)
        ↓
política por entidad          `app/business_units/scope.py`
        ↓
predicado SQL
        ↓
`MasterService`, junto al filtro de empresa, ANTES de contar y paginar
```

**Por política y no por un filtro universal.** Cada entidad determina su cadena de forma
distinta, y catorce de dieciséis no la tienen de forma fiable. Un predicado genérico las trataría
igual: cómodo de escribir y falso. `predicado()` devuelve `None` para lo que no sabe acotar, que
**no** es «déjala pasar»: es no afirmar nada, y el filtro de empresa y el `RBAC` siguen actuando.

El Super Administrador queda fuera del filtro **exactamente donde queda fuera del de empresa**.
Su semántica está certificada en `GA-REM-002` y esta fase no la reabre; se declara aquí como
excepción, no como descuido.

## 5. Tres hallazgos que no eran de unidades de negocio

Aparecieron al escribir las pruebas del detalle, y son anteriores a esta capacidad:

| Hallazgo | Qué pasaba | Clase |
|---|---|---|
| `/lots/{id}/phases` | consultaba por `lot_id` **sin comprobar pertenencia alguna** — ni de empresa | `IDOR` de inquilino |
| `/lots/{id}/opening-balance` | ídem | `IDOR` de inquilino |
| `add_phase` | creaba la fila sin comprobar de quién era el lote | escritura contra lo ajeno, clase `R-42` |

Proteger el detalle y dejar el sub-recurso libre no protege nada: el lote quedaba abierto por la
puerta de al lado. Los tres se cierran pasando por el mismo camino acotado que el detalle, con la
misma respuesta `404` — distinguir «no existe» de «no es tuyo» ya filtra información.

## 6. Trazabilidad

| Comprobación | Prueba | Estado |
|---|---|:--:|
| **`CONTROL`** · dos cadenas → ve las dos | `test_el_usuario_de_dos_cadenas_ve_las_dos` | **PASS** |
| **`TRATAMIENTO`** · una cadena → no ve la otra | `test_el_usuario_de_una_cadena_no_ve_la_otra` | **PASS** |
| Sin unidades → cero filas | `test_el_usuario_sin_unidades_no_ve_ningun_lote` | **PASS** |
| Otra empresa | `test_no_se_ven_los_lotes_de_otra_empresa` | **PASS** |
| Unidad apagada por la empresa | `test_apagar_la_unidad_a_la_empresa_retira_sus_lotes` | **PASS** |
| Lote sin cadena declarada | `test_un_lote_sin_cadena_declarada_no_se_muestra` | **PASS** |
| El parámetro del cliente no amplía | `test_pedir_la_otra_cadena_por_parametro_no_la_devuelve` | **PASS** |
| Detalle de otra cadena | `test_el_detalle_de_un_lote_de_otra_cadena_es_inalcanzable` | **PASS** |
| Detalle propio (control) | `test_el_detalle_del_lote_propio_sigue_funcionando` | **PASS** |
| Detalle de otra empresa | `test_el_detalle_de_otra_empresa_sigue_siendo_inalcanzable` | **PASS** |
| Mutación ajena, sin efecto | `test_no_se_modifica_un_lote_de_otra_cadena` | **PASS** |
| Mutación propia (control) | `test_si_se_modifica_un_lote_propio` | **PASS** |
| El total no cuenta lo oculto | `test_el_total_no_cuenta_lo_que_no_se_ve` | **PASS** |
| El alcance va antes de paginar | `test_el_alcance_se_aplica_antes_de_paginar` | **PASS** |
| Fases de otra cadena / otra empresa | `test_las_fases_de_*` (3) | **PASS** |
| Saldo de apertura ajeno | `test_el_saldo_de_apertura_de_otra_cadena_es_inalcanzable` | **PASS** |
| Activación manual ajena, sin efecto | `test_no_se_activa_manualmente_un_lote_de_otra_cadena` | **PASS** |
| Fase colgada de lote ajeno, sin efecto | `test_no_se_cuelga_una_fase_de_un_lote_de_otra_cadena` | **PASS** |
| El nombre del rol no amplía | `test_llamarse_administrador_no_amplia_el_alcance` | **PASS** |

```
PRUEBAS DE LA FASE 3     21 / 21
```

`CONTROL` y `TRATAMIENTO` en el mismo escenario, por `R-72`: sin el control, un filtro que
deniegue todo pasaría por seguro.

## 7. Sensibilidad · `GA-REM-016 AC13`

| # | Mutación | Resultado | Cayeron |
|:--:|---|:--:|:--:|
| 1 | quitar el predicado de unidad | **RED** | 12 |
| 2 | no pasar el alcance (solo empresa) | **RED** | 12 |
| 3 | usar todas las unidades **habilitadas** en vez de las concedidas | **RED** | 10 |
| 4 | sin unidades → no filtrar (`fail open`) | **RED** | 1 |
| 5 | filtrar en memoria después de contar y paginar | **RED** | 1 |
| 6 | el detalle solo por id y empresa | **RED** | 5 |
| 7 | la mutación no comprueba la unidad | **RED** | 1 |
| 8 | el sub-recurso vuelve a no comprobar nada | **RED** | 2 |
| 9 | el lote sin cadena se muestra | **RED** | 1 |
| 10 | atajo por nombre de rol | **RED** | 1 |

### 7.1 La mutación 10 encontró un hueco de cobertura, no de implementación

En su primer intento **no rompió nada**: el alcance estaba bien, pero ninguna prueba lo sujetaba
por ese lado —el rol de la fixture se llamaba `BUROW-Op`, y la mutación buscaba «admin» o
«contralor»—. Se añadió `test_llamarse_administrador_no_amplia_el_alcance`, con usuarios cuyo rol
se llama «Administrador de Empresa» y «Contralor Avícola» y concesión de una sola cadena. Con
ella, la mutación rompe.

Es para lo que sirve la sensibilidad: no solo para confirmar lo que ya se prueba, sino para
descubrir lo que no.

```
MUTACIONES        10 / 10 detectadas
RESTAURACIÓN      los tres ficheros idénticos a su instantánea
PATRONES          siete comprobaciones positivas · filtro en la línea 97, recuento en la 117
```

## 8. Una prueba certificada tuvo que configurarse

`test_t_073_06_no_se_cierra_el_lote_de_otra_empresa` empezó a fallar en su **control**: el sujeto
ya no podía cerrar ni su propio lote, porque no tenía unidades concedidas.

No es una regresión: es `OD-09.c` funcionando. La prueba mide el cierre, no el alcance, así que
se le **configura la empresa** —habilitar las cadenas y concedérselas—, que es lo que un cliente
real hará en su alta. La alternativa —que la ausencia de concesión signifique acceso total— es el
`fail open` que toda esta capacidad existe para impedir.

Queda como ayudante reutilizable en `tests/business_unit_fixtures.py`, con la distinción escrita:
donde la concesión **es** el objeto de estudio se concede a mano, unidad por unidad.

## 9. Regresión

```
BACKEND                            570 passed · 49 skipped     (eran 549)
FASE 2                             verde · empresa efectiva, guarda, clasificación
FASE 1 + 1.1                       verde
AISLAMIENTO DE EMPRESA             verde
RBAC                               verde
MIGRACIÓN                          ninguna — la cadena ya era derivable
FRONTEND                           0 archivos
```

## 10. Lo que **no** se ha logrado, dicho explícitamente

```
KPI Y AGREGADOS DE NEGOCIO         NO ACOTADOS      fase 4
PANELES                            NO ACOTADOS      fase 4
REPORTES Y EXPORTACIONES           NO ACOTADOS      fase 4
CONTRATOS DE TRASPASO              NO IMPLEMENTADOS fase 5
DESTINO DEL DESPACHO               NO IMPLEMENTADO  fase 5
CLASIFICACIÓN PENDIENTE            NO IMPLEMENTADA  fase 6
EVENTOS OPERATIVOS                 NO ACOTADOS      dependen de la fase 6
NOTIFICACIONES                     NO ACOTADAS      fase 10
```

El **total del listado** sí está acotado, y eso no es lo mismo que un `KPI`: es la corrección de
la respuesta que ese listado devuelve. Los indicadores de negocio siguen sumando toda la empresa.

## 11. Certificación

```
CERTIFICACIÓN FUNCIONAL              14 / 15   sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD    0 / 15   sin cambios
```

**Ningún proceso recibe `PASS`.** `/lots` es seguro; un proceso no lo es hasta que lo sean todas
sus superficies —listados, detalle, mutaciones, agregados, contratos y avisos según le apliquen—.
`P-03` y `P-06` dependen de eventos operativos y de `KPI`, que son las fases 4 y 6. Otorgarlo por
transitividad sería exactamente la evidencia que `AC13` prohíbe.

## 12. Siguiente

```
GA-REM-040 · FASE 4 — AGREGADOS Y KPI     T-040-11 · T-040-12
NO INICIADA
```

Y con una condición que la spec ya dejó escrita: la fase 4 **no puede ir al final**. Un total que
cuenta lo que la pantalla oculta lo revela por diferencia, y esa fuga no deja rastro.
