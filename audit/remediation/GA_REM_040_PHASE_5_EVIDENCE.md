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
