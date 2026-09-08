# `GA-REM-040` FASE 1 · FUNDAMENTO · EVIDENCIA

2026-09-07 · `T-040-01` … `T-040-05`

```
ALCANCE          catálogo · habilitación por empresa · concesión por usuario · resolutor
FUERA            guardas de ruta · filtro por fila · agregados · contratos · clasificación
                 pendiente · API de administración · sesión · frontend · P-14 · P-09 · jobs
```

---

## 1. Las cinco tareas

| Tarea | Qué exigía | Resultado |
|---|---|---|
| `T-040-01` | ¿existe modelo reutilizable de habilitación o alcance? | **no existe** → `CREATE` · §2 |
| `T-040-02` | catálogo, y su relación con `BirdTypeEnum` decidida | `business_units` · correspondencia registrada, no autoridad |
| `T-040-03` | persistencia de habilitación por empresa | `company_business_units` |
| `T-040-04` | persistencia de concesión por usuario | `user_business_units` |
| `T-040-05` | resolutor central | `app/business_units/service.py` |

## 2. `T-040-01` · la auditoría de reutilización

Buscado en `backend/app/`: `feature`, `capability`, `business_unit`, `entitlement`,
`company feature`, `tenant capability`, `scope`, catálogo de tipo de ave.

```
clases candidatas encontradas   0
tablas candidatas encontradas   0
configuración de empresa        `companies` tiene `sap_config`, `approval_levels`,
                                `is_active` — ninguna sirve de habilitación por capacidad
```

**Decisión: `CREATE`.** No hay autoridad existente que extender.

## 3. Trazabilidad de criterios

| `AC` | Prueba | Estado |
|---|---|:--:|
| `AC-A01` catálogo, código estable, `i18n`, correspondencia | `test_ac_a01_el_catalogo_tiene_las_cuatro_unidades` · `..._los_codigos_son_unicos` · `..._el_nombre_visible_es_una_clave_de_i18n` · `..._la_correspondencia_con_bird_type_esta_registrada` | **PASS** |
| `AC-A02` habilitación persistida y consultable | `test_ac_a02_la_habilitacion_distingue_encendida_de_apagada` · `..._una_empresa_no_puede_habilitar_dos_veces_la_misma_unidad` | **PASS** |
| `AC-A03` la empresa puede habilitar y deshabilitar | modelo listo; **la superficie es la fase 7** | **PARCIAL** |
| `AC-A04` deshabilitar no borra dato ni concesiones | `test_ac_a04_apagar_una_unidad_no_borra_las_concesiones` | **PASS** |
| `AC-A05` unidad deshabilitada inaccesible | `test_ac_b02_la_empresa_apagada_manda_sobre_la_concesion` | **PASS** |
| `AC-A06` rehabilitar devuelve efectividad | `test_ac_a06_rehabilitar_devuelve_la_efectividad_a_la_concesion_previa` | **PASS** |
| `AC-A07` aislamiento entre empresas | `test_ac_a07_la_habilitacion_no_cruza_empresas` · `..._la_concesion_no_alcanza_lo_habilitado_en_otra_empresa` · `..._un_usuario_sin_empresa_no_resuelve_nada` | **PASS** |
| `AC-B01` subconjunto por usuario | `test_ac_b01_el_usuario_recibe_un_subconjunto` · `..._no_se_puede_conceder_dos_veces_la_misma_unidad` | **PASS** |
| `AC-B02` la empresa apagada manda | `test_ac_b02_la_empresa_apagada_manda_sobre_la_concesion` · `..._una_unidad_que_la_empresa_no_declaro_no_es_efectiva` | **PASS** |
| `AC-B03` el usuario sin unidades se autentica | `test_ac_b03_el_usuario_sin_unidades_sigue_siendo_valido` | **PASS** |
| `AC-B04` y no ve dato productivo | `test_ac_b04_sin_concesiones_el_conjunto_efectivo_esta_vacio` | **PASS** en el resolutor · el filtro es la fase 3 |
| `AC-B05` efecto inmediato | `test_la_revocacion_surte_efecto_de_inmediato` | **PASS** |
| `AC-B06` no sustituye al `RBAC` | el resolutor no consulta permisos; `test_role_administration` y `test_security_regression` siguen verdes | **PASS** |
| `AC-C01` resolutor central | `test_la_pregunta_puntual_coincide_con_el_conjunto` | **PASS** en su parte de fundamento |
| `AC-C07` invocable fuera de `HTTP` | `test_el_resolutor_no_necesita_una_peticion_http` | **PASS** |
| `AC-C08` lo no resuelto deniega | `test_ac_b02_una_unidad_que_la_empresa_no_declaro_no_es_efectiva` · `test_una_unidad_inactiva_en_el_producto_no_es_efectiva` | **PASS** |
| `AC-F05` sin atajo por nombre de rol | `test_el_nombre_del_rol_no_concede_nada` · `test_el_nombre_del_rol_de_control_tampoco` | **PASS** en su parte de fundamento |

```
PRUEBAS DE LA FASE     23 / 23 PASS
AC COMPLETOS           16
AC PARCIALES            1        AC-A03 — su superficie es la fase 7
```

## 4. Sensibilidad · `GA-REM-016 AC13`

Cinco mutaciones sobre `unidades_efectivas`, aplicadas una a una sobre un árbol verde ya
comiteado, con instantánea del fichero y restauración desde ella.

| # | Mutación | Resultado | Pruebas que cayeron |
|:--:|---|:--:|:--:|
| 1 | ignorar la concesión del usuario | **RED** | 5 |
| 2 | ignorar la habilitación de la empresa | **RED** | 1 |
| 3 | quitar el filtro de inquilino | **RED** | 1 |
| 4 | sin concesiones → devolver toda la empresa | **RED** | 4 |
| 5 | atajo si el nombre del rol contiene «admin» o «contralor» | **RED** | 2 |

```
MUTACIONES              5 / 5 detectadas
RESTAURACIÓN            fichero idéntico a la instantánea · árbol limpio
```

**Verificación por patrón después de restaurar**, no solo `git diff` — el incidente en que un
`git checkout` borró una implementación recién escrita y el diff dijo «limpio» está registrado
en `WAVE_3_COMMIT_LOG.md`:

```
✓ class BusinessUnit · class CompanyBusinessUnit · class UserBusinessUnit
✓ uq_company_business_unit · uq_user_business_unit
✓ unidades_habilitadas · unidades_efectivas · tiene_acceso
✓ las cuatro condiciones del resolutor, una por una
✓ ninguna mención a `role.name` en código — la única aparición es prosa del docstring
```

## 5. Regresión

```
BACKEND         514 passed · 49 skipped        eran 493 · 49
                los 21 nuevos son de esta fase; ninguna prueba existente cambió de estado
                (+2 después, al añadir AC-A04 y AC-A06 → 516)
RBAC            verde · el resolutor no toca permisos
INQUILINO       verde · ninguna consulta nueva cruza empresa
MIGRACIÓN       cabeza única `p6q7r8s9t0u1` · `upgrade` limpio · `downgrade` escrito
T-025           tres tablas nuevas clasificadas; ninguna queda `UNKNOWN`
FRONTEND        0 archivos
```

### Una corrección de infraestructura que salió al paso

El guard de recuento de tablas de `scripts/run_tests.sh` seguía en **48** desde `7b22c4c`,
mientras las tres últimas migraciones —curvas, notificaciones, áreas— añadían cuatro tablas.
El paso 4/5 del arnés llevaba **fallando desde `m3n4o5p6q7r8`**, y por eso las regresiones
recientes debieron correrse invocando `pytest` por otra vía.

```
48  →  52   valor real antes de tocar nada
52  →  55   con las tres tablas de esta fase
```

## 6. Decisiones de modelo, y por qué

**La concesión apunta al catálogo, no a la habilitación de una empresa.** Si apuntara a
`company_business_units` se podría escribir la fila «usuario de la empresa A sobre la
habilitación de la empresa B» y habría que prohibirla con un validador. Apuntando al catálogo,
esa combinación **no se puede ni expresar**. Es más fuerte que validarla.

**Sin `company_id` propio en la concesión.** Duplicarlo crearía una segunda fuente que quedaría
obsoleta el día que alguien mueva un usuario de empresa — el mismo error que `GA-REM-039` evitó
al no guardar el gerente dentro del área.

**Sin cascada desde la habilitación.** `BU-D10` sigue pendiente de ratificación. Si apagar
borrase las concesiones, la opción «conservar el histórico» habría desaparecido de hecho antes
de que el propietario la decidiera. La concesión sobrevive y pierde efectividad, que es
reversible.

**El catálogo se siembra, no se migra.** Criterio que `l2m3n4o5p6q7` ya fijó para los roles: una
migración que inserta catálogo obliga a mantener el dato en dos sitios. La misma función sirve
al baseline y a las semillas de prueba, para que no discrepen.

**Solo el catálogo se siembra.** Ni habilitaciones de empresa ni concesiones de usuario.
Encender las cuatro para toda empresa dejaría la capacidad apagada de hecho el día que se
estrene; conceder todo a los usuarios existentes haría lo mismo desde el otro lado.

## 7. Estado

```
GA-REM-040                          FASE 1 DE 11 COMPLETA · spec incompleta
CERTIFICACIÓN FUNCIONAL             14 / 15    sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD   0 / 15    sin cambios — no hay enforcement todavía
```

**Ningún `PASS` de certificación de acceso se otorga por tener tablas y un resolutor.** Nada de
lo construido en esta fase impide todavía que un usuario vea un lote de otra unidad: eso
empieza en la fase 3, y hasta que exista, un `PASS` sería la evidencia que `AC13` prohíbe.

## 8. Siguiente

```
GA-REM-040 · FASE 2 — SEGURIDAD CENTRAL     T-040-06 … T-040-08
NO INICIADA
```

---

# FASE 1.1 · LA CONCESIÓN SE ACOTA A LA EMPRESA (2026-09-07)

`T-040-31` · `GA-REM-040` enmienda A · `OD-09.d`

## 9. El defecto, comprobado ejecutando

La fase 1 dejó una pregunta abierta y anotada al cerrarla: *«la concesión no guarda a qué
empresa pertenecía cuando se otorgó»*. El propietario pidió comprobarlo antes de la fase 2.

Se comprobó **ejecutando**, no razonando:

```
empresa A con `breeder` habilitada · usuario U en A con concesión de `breeder`  → ['breeder']
se mueve U a la empresa B, que también tiene `breeder` habilitada
sin que nadie le conceda nada en B                                              → ['breeder']
                                                                                   ^^^^^^^^^^
                                                                                   debía ser []
```

**La concesión viajó con el usuario.** El resolutor no falló: comprobaba la empresa actual, y
hacía todas las comprobaciones que sabía hacer. Falló el dato, que no contenía la respuesta.

## 10. Por qué el modelo de la fase 1 parecía correcto

La concesión apuntaba al catálogo por una razón que sigue siendo buena: apuntando a la
habilitación de una empresa se podía escribir la fila «usuario de A sobre habilitación de B».

El error fue tratar **una** combinación inválida como si fueran todas. Al quitar la empresa de la
fila desapareció esa fila imposible **y también** lo que distingue un contexto de otro: `breeder`
de A y `breeder` de B pasaron a ser indistinguibles.

La respuesta correcta no era quitar la empresa. Era ponerla y validarla.

## 11. La corrección

```
ANTES    user_business_units  →  business_units
AHORA    user_business_units  →  company_business_units  →  companies
                                                         └→ business_units
```

Cerrada por los dos lados, y **las dos hacen falta**:

```
AL ESCRIBIR   `conceder_unidad` rechaza dar a un usuario la habilitación de otra
              empresa, y no queda escrita.                            `AC-B10`

AL LEER       el resolutor exige que la empresa de la habilitación sea la ACTUAL
              del usuario.                                            `AC-B08`
```

La primera sola dejaría efectiva una concesión legítima de ayer cuando el usuario se mueve hoy.
La segunda sola permitiría escribir filas que nunca sirven, y una fila inválida que existe acaba
encontrando el camino a una consulta que la lea mal.

`conceder_unidad` vive en la fase 1 y no en la 7 —donde estará la API de administración— porque
la regla que protege es del modelo, no de la pantalla.

## 12. Trazabilidad

| `AC` | Prueba | Estado |
|---|---|:--:|
| `AC-B07` la concesión dice bajo qué empresa se otorgó | `test_ac_b07_la_concesion_dice_bajo_que_empresa_se_otorgo` · `..._conceder_por_el_servicio_produce_la_misma_efectividad` | **PASS** |
| `AC-B08` no viaja con el usuario | `test_ac_b08_la_concesion_no_viaja_con_el_usuario` · `..._en_la_empresa_nueva_hace_falta_conceder_de_nuevo` | **PASS** |
| `AC-B09` mismo código, dos contextos | `test_ac_b09_el_mismo_codigo_en_dos_empresas_son_dos_contextos` | **PASS** |
| `AC-B10` la concesión cruzada se rechaza | `test_ac_b10_conceder_cruzando_empresas_se_rechaza` · `..._a_un_usuario_sin_empresa_se_rechaza` · `test_ac_a07_no_se_aprovecha_lo_habilitado_en_otra_empresa` | **PASS** |
| `AC-B11` no se borra la historia | `test_ac_b11_mover_de_empresa_no_borra_la_concesion_anterior` | **PASS** |

```
PRUEBAS DE LA FASE     31 / 31 PASS        (eran 23; +8)
```

Dos pruebas de la fase 1 cambiaron de forma porque **su premisa ya no es construible**: conceder
una unidad que la empresa no declaró, o la habilitación de otra empresa, ya no llega a existir.
Comprueban esa propiedad —que es más fuerte— y no una más débil.

## 13. Sensibilidad

| # | Mutación | Resultado | Cayeron |
|:--:|---|:--:|:--:|
| 1 | ignorar la empresa actual del usuario | **RED** | 2 |
| 2 | casar solo por el código del catálogo | **RED** | 2 |
| 3 | la concesión viaja: casar por la unidad subyacente *(el defecto de la fase 1, reproducido)* | **RED** | 2 |
| 4 | «limpiar» las concesiones de la empresa anterior al conceder | **RED** | 1 |

La mutación 3 se rehízo. El primer intento rompió 17 de 31 pruebas, y eso **no es evidencia**:
una mutación que rompe la consulta entera demuestra que la consulta era necesaria, no que la
regla concreta lo sea. Reescrita como implementación coherente —casar por la unidad subyacente,
que es exactamente el defecto de la fase 1— cae en las dos pruebas del alcance y en ninguna más.

La mutación 4 solo es observable porque `AC-B11` se reforzó para conceder también en la empresa
nueva: es el momento en que alguien sentiría la tentación de limpiar lo anterior. Sin ese paso,
la preservación era estructural —nada la borra— y ninguna mutación razonable podía romperla.

```
MUTACIONES        4 / 4 detectadas
RESTAURACIÓN      fichero idéntico a la instantánea · árbol limpio
PATRONES          modelo, resolutor, límite de escritura y ausencia de borrado, verificados
```

## 14. La migración

```
q7r8s9t0u1v2      cabeza única · upgrade y downgrade escritos
```

**No adivina.** Resuelve la habilitación por la empresa **actual** del usuario y la unidad que la
concesión nombraba —derivación de dato persistido—, y si alguna fila queda sin resolver **se
detiene con un error** en lugar de borrarla o inventarle empresa:

```
RuntimeError: N concesiones sin habilitación de empresa resoluble.
              No se borran ni se les inventa empresa.
```

Perder en silencio una concesión sería peor que fallar la migración. En la práctica hay **cero
filas**: ninguna semilla crea concesiones, por decisión de la fase 1.

## 15. Cómo se mueve hoy un usuario de empresa

Auditado, porque la corrección depende de qué es posible:

```
UserUpdate            NO acepta `company_id`  →  ninguna API mueve a un usuario hoy
POST /auth/switch-company   super administrador únicamente; desplaza la empresa en la
                            RECLAMACIÓN del token y no toca `users.company_id`
```

**La ausencia de la pantalla no se usó como excusa.** El modelo tiene que ser correcto frente a
un cambio directo futuro: una migración, un script de soporte o la API que la fase 7 traiga.

### Una observación para la fase 2

`switch-company` es del super administrador, que se siembra **sin empresa** y por tanto no
resuelve ninguna unidad. Hoy no hay riesgo. Pero la fase 2 tendrá que decidir **de dónde toma la
guarda la empresa efectiva de una petición**: de `users.company_id` o de la reclamación del
token. Si son dos fuentes, hay que decir cuál manda. Queda anotado, no resuelto.

## 16. Lo que sigue sin decidir

**Si el usuario vuelve a la empresa anterior, ¿revive su concesión?**

```
SPEC DECISION REQUIRED
```

Ninguna fuente lo dice y no se inventa. Rige lo conservador: volver no reactiva nada. Es
**distinto de `BU-D10`** —que trata de qué pasa cuando la empresa apaga una unidad— y no se
resuelve arrastrando aquella.

```
BU-D10     PENDIENTE DE RATIFICACIÓN     sin tocar
```

## 17. Regresión y estado

```
BACKEND                            524 passed · 49 skipped     (eran 516)
MIGRACIÓN                          cabeza única `q7r8s9t0u1v2` · base limpia PASS
T-025                              PASS · ninguna tabla nueva
TABLAS                             55 · sin cambios
FRONTEND                           0 archivos
RUTAS                              0 de 198
LOS 22 MAESTROS                    sin cambios: la corrección no afecta a su clasificación
CERTIFICACIÓN FUNCIONAL            14 / 15   sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD  0 / 15   sin cambios
```

## 18. Siguiente

```
GA-REM-040 · FASE 2 — SEGURIDAD CENTRAL     T-040-06 … T-040-08
NO INICIADA
```

El fundamento queda **seguro para concesiones acotadas a la empresa**: una concesión pertenece a
usuario + empresa + unidad, no se transfiere, no se borra y no se puede escribir cruzada.
