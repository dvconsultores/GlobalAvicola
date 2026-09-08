# `GA-REM-040` FASE 5 · CONTRATOS DE TRASPASO · EVIDENCIA

2026-09-07 · `T-040-13` · `T-040-14` · `T-040-15`

```
VISIBILIDAD DE TRASPASO   ≠   ACCESO A LA UNIDAD AJENA
```

---

## 1. Lo primero, porque cambia la lectura del resto

De trece comprobaciones del contrato, **diez ya pasaban antes de escribir una línea**.

Las proyecciones de lectura ya eran acotadas —`EggBatchRead` no expone `notes`, y el lote de
enfrente llega como `LotRef` con cuatro campos—, y las fases 1 a 4 ya impedían pivotar del
identificador ajeno a su detalle. La mayor parte del contrato **estaba**, y conviene decirlo en
vez de presentar la fase como si lo hubiera construido entero.

Faltaban tres cosas, y las tres eran de escritura:

| Hueco | Qué permitía |
|---|---|
| el destino era **opcional** | un despacho sin destinatario: la incubadora no puede saber que es para ella antes de recibirlo |
| el **origen** no se acotaba | crear un traspaso saliendo del lote de otra cadena — operar sobre lo ajeno por la puerta del contrato |
| el flujo no se validaba | dirigir huevo fértil a un lote de engorde, escribiendo una cadena que `P-10` no puede reconstruir |

## 2. `T-040-14` · la auditoría del destino

`GA-REM-040 §10.3` prohibía proponer columna sin auditar primero. Resultado:

```
egg_batches.hatchery_lot_id        YA EXISTE
chick_batches.destination_lot_id   YA EXISTE
```

```
DECISIÓN   REUSE          ·   MIGRACIÓN   ninguna
```

El dato estaba; lo que faltaba era **hacerlo obligatorio**. Es literalmente lo que `OD-10.b §3.2`
anticipó: *«puede que el dato necesario ya exista y solo falte hacerlo obligatorio para este
flujo»*. No se creó `destination_business_unit_id` ni ninguna otra columna.

## 3. El contrato campo por campo

En `BUSINESS_UNIT_HANDOFF_CONTRACT_MATRIX.md`, con las cuatro categorías y el porqué de cada
campo. Resumen:

```
FLUJOS IMPLEMENTADOS      4 / 7    1 · 2 · 3 · 7
APLAZADOS A LA FASE 6     2 / 7    4 · 6 — se apoyan en `operational_events`, `lot_id` nulable
EXCEPCIÓN DECLARADA       1 / 7    5 — la consolidación agrupa las cuatro por definición
CAMPOS SIN CLASIFICAR     0
```

**Los dos aplazados no son comodidad.** Acotar hoy los eventos sin lote los haría desaparecer
para todos, incluida la persona que acaba de registrarlos; `OD-10.c` los manda a «pendiente de
clasificar», que es la fase 6.

## 4. Trazabilidad

| Comprobación | Prueba | Antes | Estado |
|---|---|:--:|:--:|
| El destino es obligatorio | `test_od10b_un_despacho_sin_destino_se_rechaza` | **fallaba** | **PASS** |
| Con destino se crea (control) | `test_od10b_con_destino_declarado_se_crea` | pasaba | **PASS** |
| El origen debe estar al alcance | `test_no_se_despacha_desde_un_lote_de_otra_cadena` | **fallaba** | **PASS** |
| El destino **no** exige su cadena | `test_el_destino_no_exige_tener_su_cadena` | pasaba | **PASS** |
| Destino válido para el flujo | `test_el_huevo_fertil_no_se_despacha_a_un_lote_de_engorde` | **fallaba** | **PASS** |
| Nunca a otra empresa | `test_no_se_despacha_a_otra_empresa` | pasaba | **PASS** |
| `C` fuera de la proyección | `test_la_proyeccion_no_lleva_datos_internos_del_otro_lado` | pasaba | **PASS** |
| El destino ve lo dirigido a él | `test_el_destino_ve_el_traspaso_dirigido_a_el` | pasaba | **PASS** |
| La otra incubadora no lo ve | `test_la_otra_incubadora_no_ve_el_traspaso` | pasaba | **PASS** |
| El id ajeno no abre su detalle | `test_conocer_el_lote_del_otro_lado_no_abre_su_detalle` | pasaba | **PASS** |
| El origen no gana la cadena ajena | `test_participar_en_un_traspaso_no_concede_la_cadena_ajena` | pasaba | **PASS** |
| El destino tampoco | `test_el_destino_tampoco_gana_la_cadena_del_origen` | pasaba | **PASS** |
| El nombre del rol no abre nada | `test_el_nombre_del_rol_no_abre_el_traspaso_ajeno` | pasaba | **PASS** |

```
PRUEBAS DE LA FASE 5     13 / 13
```

## 5. Sensibilidad

| # | Mutación | Resultado | Cayeron |
|:--:|---|:--:|:--:|
| 1 | serializar el objeto entero — exponer `notes` | **RED** | 1 |
| 2 | el destino vuelve a ser opcional | **RED** | 1 |
| 3 | no validar el flujo | **RED** | 1 |
| 4 | el origen deja de acotarse por cadena | **RED** | 1 |
| 5 | la traza deja de acotar su lote — bypass por id | **RED** | 1 |
| 6 | quitar el filtro de inquilino del vínculo | **RED** | 1 |

Cada una rompe **exactamente una** prueba: son mutaciones estrechas, que es lo que las hace
informativas.

### 5.1 Tres mutaciones del encargo no aplican, y por qué

```
«el traspaso concede la cadena ajena»       N/A — ningún código concede: la concesión solo
                                            nace de `conceder_unidad`, y el traspaso no la
                                            llama. La propiedad se prueba midiendo el
                                            conjunto efectivo antes y después.

«fuga de categoría D»                       N/A — no existe ningún campo agregado en la
                                            proyección. Añadir uno para poder mutarlo sería
                                            fabricar el defecto que se dice encontrar.

«cambiar el destino tras el bloqueo»        N/A — no hay superficie de edición: las
                                            entidades puente solo tienen `POST`.
```

```
MUTACIONES        6 / 6 aplicables detectadas · 3 N/A con razón
RESTAURACIÓN      los tres ficheros idénticos a su instantánea
```

## 6. Dos suites certificadas necesitaron fixtures válidas

**No se debilitó ninguna aserción.**

`test_el_enlace_manual_sigue_disponible` enlazaba un lote **de engorde** como origen de un lote
de huevo. Un huevo fértil no sale de un engorde: la fixture escribía una cadena que `P-10` no
puede reconstruir, y la validación nueva la rechaza con razón. Se le dieron los tipos correctos.

`test_traceability_ownership` falló en su **control** —el sujeto no podía enlazar ni sus propios
lotes— porque no tenía cadenas concedidas. Es `OD-09.c` funcionando. Se configuró la empresa con
el ayudante que la fase 3 dejó, y la parametrización pasa a llevar origen y destino propios de
cada flujo, porque el huevo y el pollito no salen de la misma cadena.

## 7. Regresión

```
BACKEND                  598 passed · 49 skipped     (eran 585)
P-10 TRAZABILIDAD        verde · la cadena generacional se reconstruye igual
P-02 · P-04 · P-05 · P-06 · P-11 · P-15   verdes
FASE 4 · FASE 3 · `R-111` · FASE 2 · FASE 1   verdes
INQUILINO · RBAC         verdes
MIGRACIÓN                ninguna · FRONTEND 0 archivos
```

## 8. Lo que sigue sin resolverse

```
CAMBIAR EL DESTINO TRAS CREARLO    SPEC DECISION REQUIRED — sigue abierta
                                   hoy no hay superficie de edición, así que no urge;
                                   habrá que contestarla antes de que la fase 7 la abra

FLUJOS 4 y 6                       dependen de `operational_events` · fase 6
FLUJO 5                            excepción declarada · `BU-D04` sigue PENDIENTE
ANULACIÓN DEL TRASPASO             no existe superficie propia · hueco registrado
```

## 9. Certificación

```
CERTIFICACIÓN FUNCIONAL              14 / 15   sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD    0 / 15   sin cambios
```

**Ningún `PASS`, tampoco para `P-10`.** Su cadena está protegida por contrato, y el proceso
consume además eventos operativos —fase 6— y su superficie de anulación no existe. Certificar por
entidad puente es tan inválido como certificar por endpoint.

## 10. Siguiente

```
GA-REM-040 · FASE 6 — CLASIFICACIÓN PENDIENTE     T-040-16 · T-040-17
NO INICIADA
```

Es la que desbloquea los flujos 4 y 6, los eventos operativos, las inspecciones y los lotes sin
cadena declarada — todo lo que hoy queda fuera por no poder atribuirse.

---

# ADDENDUM · `BU-D04` Y EL CIERRE DE LA FASE 5 (2026-09-07)

La evidencia original de la fase 5 se conserva íntegra. Esto es el estado actual.

## A.1 La historia del recuento

```
fase 5 original      4 / 7 implementados · 2 aplazados · 1 excepción pendiente
tras la fase 6       6 / 7 implementados · 0 aplazados · 1 excepción pendiente
tras `OD-12`         7 / 7 implementados · 0 aplazados · 0 excepciones sin resolver
```

## A.2 `BU-D04` · el flujo 5

```
DECISIÓN   OD-12 · capacidad operativa transversal EXPLÍCITA, acotada al contrato SAP
PERMISO    `sap:read` · `sap:send_sap`   —  REUSE, no se creó ninguno
```

### A.2.1 Lo primero: no hizo falta cambiar comportamiento

Las quince pruebas del contrato **pasaron sin tocar una línea**. No hubo rojo que provocar
porque no había defecto de comportamiento:

```
el permiso ya era explícito      en las diez rutas del módulo
la empresa ya se filtraba        incluidos los accesos por identificador
las superficies normales         ya seguían acotadas por cadena para el mismo actor
```

El hueco era otro y era de gobernanza: **la transversalidad existía por ausencia de filtro**. Y
una excepción que solo existe porque nadie puso el filtro es indistinguible de un fallo.

### A.2.2 Lo que se añadió, y lo que se decidió no añadir

**Se añadió** una declaración con dientes: `sap_contract.py` no filtra nada —ésa es su función—
y dice cuáles son las superficies transversales y qué las autoriza. Una prueba comprueba que la
lista declarada **coincide con las rutas reales**, de modo que una ruta SAP nueva no hereda la
excepción en silencio.

Y una prueba de que **no existe** ninguna función genérica de salto de alcance, porque una
excepción reutilizable acaba usándose donde nadie la previó.

**No se añadió** una comprobación redundante de las cinco condiciones de `OD-12.b`. Cada una vive
donde le corresponde —permiso en la ruta, empresa en el servicio, elegibilidad en las reglas de
negocio— y duplicarlas habría creado una copia que se desincronizaría con la real.

### A.2.3 El sujeto tiene **una sola** cadena concedida

A propósito. Probar `BU-D04` con un analista al que se le conceden las cuatro habría demostrado
que quien tiene todo ve todo, no que exista una excepción de contrato.

```
ANALISTA   `breeder` concedida · `sap:read` · `sap:send_sap`
           → alcanza el consolidado de las CUATRO cadenas por el contrato
           → y el detalle normal de un lote de incubadora le da 404
```

## A.3 Trazabilidad

| `AC` | Prueba | Estado |
|---|---|:--:|
| `AC-SAP01` capacidad explícita | `test_ac_sap01_sin_capacidad_sap_no_se_opera_el_contrato` | **PASS** |
| `AC-SAP02` misma empresa | `test_ac_sap02_el_contrato_no_cruza_la_empresa` · `..._el_analista_ajeno_no_ve_lo_nuestro` | **PASS** |
| `AC-SAP03` las cuatro cadenas | `test_ac_sap03_el_analista_alcanza_las_cuatro_cadenas` | **PASS** |
| `AC-SAP04` sin las cuatro concesiones | `test_ac_sap04_no_hacen_falta_las_cuatro_concesiones` | **PASS** |
| `AC-SAP05` `AC-SAP06` no concede ni habilita | `test_ac_sap05_operar_el_contrato_no_concede_ni_habilita` | **PASS** |
| `AC-SAP07` fuera del contrato, alcance normal | `test_ac_sap07_la_capacidad_sap_no_abre_las_superficies_normales` · `..._no_amplia_los_indicadores` · `test_el_identificador_obtenido_por_sap_no_es_una_llave` | **PASS** |
| `AC-SAP08` `AC-SAP09` proyección | `test_ac_sap09_la_proyeccion_no_lleva_el_objeto_ajeno` | **PASS** |
| `AC-SAP11` sin efectos al denegar | `test_ac_sap11_una_operacion_denegada_no_produce_efectos` | **PASS** |
| `AC-SAP12` sin atajo por nombre | `test_ac_sap12_el_nombre_del_rol_no_abre_el_contrato` | **PASS** |
| declaración con dientes | `test_la_excepcion_sap_esta_declarada_y_no_puede_crecer_en_silencio` · `..._configuracion_sap_quedan_fuera` · `test_no_existe_una_funcion_generica_de_salto_de_alcance` | **PASS** |

```
PRUEBAS DEL FLUJO 5     15 / 15
```

**`AC-SAP10` (elegibilidad de negocio) no tiene prueba propia** en esta tanda: no se tocó ninguna
regla de elegibilidad y las suites de `P-08` la cubren funcionalmente. Se declara como cobertura
heredada, no como comprobada aquí.

## A.4 Sensibilidad

| # | Mutación | Resultado | Detectado por |
|:--:|---|:--:|---|
| 1 | quitar la capacidad SAP explícita | **RED** | **la guarda de arranque** (`GA-REM-002 AC08`) |
| 2 | conceder las cuatro cadenas a quien tiene SAP | **RED** | 2 pruebas |
| 3 | autorizar por el nombre del rol | **RED** | **la guarda de arranque** |
| 4 | quitar el filtro de empresa | **RED** | 2 pruebas |
| 5 | la capacidad SAP abre las superficies normales | **RED** | 2 pruebas |
| 6 | serializar el objeto ajeno entero | **RED** *(tras corregir `R-112`)* | 1 prueba |

**Las mutaciones 1 y 3 no dieron un rojo de prueba sino un fallo de arranque.** La guarda de
`GA-REM-002 AC08` aborta la aplicación si una ruta no declara permiso, así que sustituirlo por
`get_current_user` o por una comprobación de nombre de rol **impide arrancar**. Es una detección
más fuerte que un test —el sistema no llega a servir—, y se registra nombrando el mecanismo en
lugar de presentarlo como si lo hubieran cazado las pruebas nuevas.

### A.4.1 La mutación 6 encontró un defecto real · `R-112`

Añadir un campo al esquema **no rompió nada**, porque `/sap/consolidated` **no declaraba
`response_model`**: devolvía objetos `ORM` crudos. La proyección que la fase 5 había dado por
buena existía en el fichero y no se estaba aplicando.

Hoy no filtraba nada —`ConsolidatedMovement` no tiene relaciones y sus columnas coinciden con el
esquema—, pero eso era **coincidencia, no contrato**: una relación o una columna nueva habrían
empezado a viajar sin que nadie lo decidiera, en la superficie donde el actor alcanza las cuatro
cadenas.

Corregido en `/consolidated`. Las otras ocho rutas SAP quedan registradas en `R-112`: cambiar
ocho formas de respuesta sin pruebas que las sujeten no corresponde a esta tanda.

## A.5 Estado de los siete flujos

| # | Flujo | Estado | Cómo |
|:--:|---|:--:|---|
| 1 | Progenitoras → Reproductora | **IMPLEMENTADO** | fase 5 |
| 2 | Reproductora → Incubadora | **IMPLEMENTADO** | fase 5 · destino obligatorio |
| 3 | Incubadora → Engorde | **IMPLEMENTADO** | fase 5 |
| 4 | Transferencia entre granjas | **IMPLEMENTADO** | fase 6 · por construcción |
| 5 | Consolidación a SAP | **IMPLEMENTADO** | `OD-12` · excepción declarada |
| 6 | Revisión y aprobación | **IMPLEMENTADO** | fase 6 |
| 7 | Trazabilidad generacional | **IMPLEMENTADO** | fase 5 |

```
CLASIFICADOS   7 / 7
IMPLEMENTADOS  7 / 7
APLAZADOS      0
EXCEPCIONES SIN RESOLVER  0
```

```
FASE 5   COMPLETE
```

## A.6 `P-08` no cambia

```
P-08   BLOCKED_EXTERNAL   sin cambios
```

`OD-12` gobierna **quién** puede operar el contrato y sobre qué filas. No prueba que SAP real
acepte nada, y nada de esto certifica la integración externa.

## A.7 Certificación

```
CERTIFICACIÓN FUNCIONAL              14 / 15   sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD    0 / 15   sin cambios
```

Que la fase 5 esté completa **no certifica ningún proceso**: faltan la administración —fase 7—,
la sesión —fase 8—, la interfaz —fase 9— y los avisos y tareas —fase 10—.
