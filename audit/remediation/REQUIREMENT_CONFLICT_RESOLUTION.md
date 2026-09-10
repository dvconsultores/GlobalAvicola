# REQUIREMENT CONFLICT RESOLUTION — Global Avícola

**Wave** 1.5 · Track A  ·  **Fecha** 2026-09-03  ·  **Estado** cerrado para los 5 RC en alcance

Este documento resuelve por evidencia los conflictos de requerimiento `RC-01`, `RC-02`,
`RC-03`, `RC-05` y `RC-07`. No introduce código. Cada resolución cita ruta y línea.

---

## 1. Jerarquía de evidencia aplicada

El encargo fija un orden estricto. Se aplica sin excepción y se declara, en cada RC,
**en qué nivel se detuvo la decisión**:

| # | Nivel | Fuentes concretas en este proyecto |
|---|---|---|
| 1 | Decisión del propietario | `RA-05` (Wave 1); ninguna otra registrada |
| 2 | Requerimiento del cliente | `Imagen de Procesos Documentado/Recomendación central.pdf`, `Bases Consideradas.pdf` |
| 3 | Documento de proceso operativo | `docs/12-approval-workflow.md`, `docs/02-functional-spec.md` |
| 4 | Spec vigente | `specs/global-avicola/spec.md`, `.specify/memory/constitution.md` |
| 5 | Implementación | `backend/app/**`, `frontend/src/**`, `alembic/versions/**` |
| 6 | Legado | `docs/01-legacy-audit.md`, `docs/15-cross-reference-old-vs-new.md` |

**Regla de corte.** La decisión se toma en el nivel más alto que se pronuncia. Un nivel
inferior no puede contradecir a uno superior; sí puede **precisar** lo que el superior
deja abierto. El silencio de un nivel no es aprobación: hace descender la decisión al
siguiente nivel que sí se pronuncia.

**Regla de escalado.** Si ninguna fuente por encima de la implementación se pronuncia y
la elección cambia el comportamiento de negocio, el resultado es `OWNER_DECISION_REQUIRED`.
No se resuelve por preferencia técnica.

---

## 2. Matriz de resolución

| RC | Tema | Alternativa A | Alternativa B | Fuente A | Fuente B | Código actual | Impacto | Conclusión |
|---|---|---|---|---|---|---|---|---|
| **`RC-01`** | ¿La corrección se aplica de inmediato o requiere aprobación? | Se aplica de inmediato al dato; el registro sigue requiriendo aprobación | La corrección misma queda pendiente de aprobación y el dato no cambia hasta aprobarse | Cliente §18 `CORREGIDO → APROBADO` + §26 «corregir antes de aprobar» · `docs/12 §2` diagrama · `spec.md:29` | ninguna fuente la sostiene | `corrections/service.py:53` marca `CORRECTED` pero **nunca escribe el valor** | Alto — P0-2 | **A · `RESOLVED_BY_EVIDENCE`** |
| **`RC-02`** | Semántica de `bird_transfer` en el balance de aves | Neutro: no entra ni sale del lote (movimiento entre galpones) | Salida del lote origen y entrada en el lote destino | Modelo de datos: `BirdMovement.source_house_id` / `target_house_id` (`operations/models.py:155-156`); **no existe ningún campo de lote destino** en todo el esquema | ninguna fuente la sostiene | `validators.py:27-33` lo excluye de `in_types` y de `out_types` | Bajo — el cálculo vigente es correcto | **A · `RESOLVED_BY_EVIDENCE`** |
| **`RC-03`** | ¿BR-14 (segregación) es absoluta o configurable? | Configurable por paso de aprobación, con valor por defecto «exigir segregación» | Absoluta e inderogable | `docs/02:554` «si el flujo requiere segregación» · `docs/12:139` «si configuración lo exige» · `review/models.py:81` `require_segregation` con `default=True` | `spec.md:275` (línea de tabla resumen, sin matiz) | Absoluta: `review/service.py:318` valida siempre; **la bandera nunca se lee** | Medio — bandera muerta y una ruta que la elude | **A · `RESOLVED_BY_EVIDENCE`** |
| **`RC-05`** | Política de complejidad de contraseñas | Una única política de longitud mínima **8**, fijada en el alta y aplicada también al cambio | Mantener 8 en alta y 6 en cambio/perfil | `auth/schemas.py:39` `min_length=8` — única declaración de política del sistema | `ProfilePage.tsx:21` `< 6` y `auth/schemas.py:11` `min_length=6`, ambos en rutas que **no son** creación de política | El cambio de contraseña **no existe**: `UserUpdate` (`auth/schemas.py:42-49`) no declara `password` | Alto — P0 nuevo | **A · `RESOLVED_BY_EVIDENCE`** (longitud) · complejidad → `OWNER_DECISION_REQUIRED` no bloqueante |
| **`RC-07`** | Política de mortalidad frente a SAP | Movimiento de inventario (baja/merma valorizada) | Solo indicador productivo / costo | — | — | `sap/service.py` no mapea mortalidad a ningún documento SAP | Alto para `GA-REM-017`; **nulo** para la captura | **`OWNER_DECISION_REQUIRED`** — el propio cliente la declara pendiente |

---

## 3. RC-01 · Flujo de corrección

### 3.1 Qué decía cada nivel

| Nivel | Pronunciamiento | Evidencia |
|---|---|---|
| 2 · Cliente | `OBSERVADO ↓ CORREGIDO ↓ APROBADO`; «Solo el estado APROBADO puede viajar a SAP»; «corregir antes de aprobar»; debe bloquearse «corrección sobre registro aprobado sin versión/reverso» | `Recomendación central.pdf` §18, §26, §17 |
| 3 · Proceso | `EnRevision → Corregido → Aprobado`; `R4` «toda corrección conserva valor original + valor corregido»; `R5` «una vez enviado a SAP, el registro no puede editarse» | `docs/12-approval-workflow.md:19-42`, `:141-142` |
| 4 · Spec | «Revisión → Corrección → Aprobación → Consolidación → SAP»; `BR-09`, `BR-16` | `specs/global-avicola/spec.md:29`, `:270`, `:277` |
| 5 · Código | Estados corregibles = `REGISTERED`, `PENDING_REVIEW`, `IN_REVIEW`, `RETURNED` — excluye `APPROVED` | `backend/app/corrections/service.py:34` |

### 3.2 Por qué no era un conflicto

Los cuatro niveles dicen **lo mismo**. La disyuntiva «inmediata *o* con aprobación» era
falsa porque mezcla dos planos distintos:

- **plano del dato** — el valor corregido se escribe en el acto;
- **plano del registro** — el registro corregido pasa a `CORRECTED` y **sigue necesitando aprobación** antes de consolidarse y viajar a SAP.

`RC-01` no era un conflicto de requerimiento sino **una omisión de `spec.md §4.10`**, que
enumera «corrección auditada» sin describir el momento de aplicación. Clasificación
secundaria: **`SPEC_DEFECT`** — se corrige redactando, no decidiendo.

### 3.3 Regla vigente resuelta

> **RR-01.** La corrección de un registro operativo escribe el valor corregido en el dato
> en el mismo acto, conserva el valor original en `CorrectionLog` y deja el registro en
> estado `CORRECTED`. Un registro `CORRECTED` **no** es un registro aprobado: requiere
> aprobación posterior antes de consolidarse o enviarse a SAP. Sobre registros en
> `APPROVED`, `CONSOLIDATED`, `SENT_TO_SAP` o `SAP_CONFIRMED` la corrección directa está
> prohibida; procede reverso, nueva versión o movimiento autorizado (`BR-15`, `BR-16`).

### 3.4 Consecuencias verificadas

| Hallazgo | Evidencia | Destino |
|---|---|---|
| El valor corregido nunca se aplica al dato (P0-2) | `corrections/service.py:41-53` — se crea `CorrectionLog` y se cambia `status`; ninguna escritura sobre el evento ni sobre el sub-movimiento | `GA-REM-006` — desbloqueada |
| `complete_review` con `approval_levels <= 1` aprueba **sin** validar `BR-14` | `review/service.py:203-207` fija `APPROVED` y `approved_by_id` sin llamar a `validate_segregation`; la validación solo existe en `approve()` (`:318`) | `GA-REM-007` — hallazgo nuevo `R-23` |
| El bloqueo de corrección post-SAP es correcto | `corrections/service.py:34` excluye `APPROVED` y posteriores | conforme — sin acción |

---

## 4. RC-02 · Semántica de `bird_transfer`

### 4.1 La evidencia decisiva es estructural

`BirdMovement` declara **galpón** de origen y destino, nunca lote:

```
backend/app/operations/models.py:155   source_house_id  -> houses.id
backend/app/operations/models.py:156   target_house_id  -> houses.id
```

Y el evento portador tiene **un solo** `lot_id`, anulable, sin contraparte de destino:

```
backend/app/operations/models.py:80    lot_id -> lots.id   (Optional)
```

Búsqueda exhaustiva de un lote destino en todo el esquema: **cero coincidencias** para
`target_lot`, `destination_lot`, `dest_lot`. El esquema es, por construcción,
**incapaz** de expresar la alternativa B.

### 4.2 Regla vigente resuelta

> **RR-02.** `bird_transfer` y `bird_distribution` son movimientos **intra-lote** entre
> galpones. Son **neutros** en el balance de aves del lote: no se suman a las entradas ni
> a las salidas. El movimiento de aves entre lotes o hacia otra fase productiva se
> representa con `bird_exit` (salida del lote origen) y `bird_reception` (entrada al lote
> destino), que sí afectan el balance.

La exclusión vigente en `validators.py:27-33` **es correcta** y no debe modificarse.

### 4.3 Lo que sí queda pendiente

`RR-02` desbloquea `GA-REM-005` en su parte de balance, pero deja al descubierto un hueco
real que la spec debe recoger: **no existe validación de que un `bird_transfer` cuadre a
nivel de galpón** (que el galpón origen tenga esa población y que el destino admita la
capacidad). `validate_house_capacity` existe (`validators.py:297`) pero no se aplica a
las transferencias. Hallazgo nuevo `R-24` → `GA-REM-005`.

---

## 5. RC-03 · ¿BR-14 absoluta o configurable?

### 5.1 Aplicación de la jerarquía

| Nivel | Pronunciamiento | Evidencia |
|---|---|---|
| 2 · Cliente | **silencio**. Exige bloquear «registro sin usuario responsable» y «registro sin aprobación» (§17); nunca menciona segregación de funciones | `Recomendación central.pdf:954-956` |
| 3 · Proceso | **configurable**, dos veces y de forma independiente | `docs/02-functional-spec.md:554` «(si el flujo requiere segregación)» · `docs/12-approval-workflow.md:139` `R2` «(si configuración lo exige)» |
| 4 · Spec | **absoluta** — pero es una celda de tabla resumen de una línea, sin matiz ni contexto | `specs/global-avicola/spec.md:275` |
| 5 · Código | **absoluta** en la ejecución, **configurable** en el esquema | `review/service.py:318` valida siempre · `review/models.py:81` `require_segregation` existe y nunca se lee |

El nivel 2 calla, así que decide el nivel 3, que se pronuncia dos veces y en el mismo
sentido. El nivel 4 no puede prevalecer sobre el 3. Se añade que el **esquema de datos**
—decisión de diseño ya migrada y en producción— materializa la lectura configurable.

### 5.2 Por qué esta resolución no debilita el control

La opción A es un **superconjunto** de la B: con `require_segregation = True` —el valor
por defecto de la columna— el comportamiento es idéntico al actual. Resolver a favor de
«configurable» **no relaja nada por sí mismo**; convierte una bandera muerta en una
bandera honesta.

### 5.3 Regla vigente resuelta

> **RR-03.** `BR-14` es **configurable por paso de aprobación** mediante
> `ApprovalStep.require_segregation`, cuyo valor por defecto es `True`. Toda ruta que
> apruebe, consolide o envíe a SAP debe consultar la bandera del paso aplicable, y no
> aplicar segregación únicamente cuando esté explícitamente en `False`. Ponerla en `False`
> es un cambio de configuración auditable y de alcance por empresa; no puede hacerse de
> forma implícita ni por omisión. Ninguna ruta de aprobación puede eludir la comprobación.

### 5.4 Consecuencias verificadas

| Hallazgo | Evidencia | Destino |
|---|---|---|
| `require_segregation` es una columna muerta | 0 lecturas condicionales en `backend/app/`; solo 3 escrituras de siembra (`review/service.py:476`, `:484`, `:492`) | `GA-REM-007` |
| `complete_review` elude `BR-14` por completo | `review/service.py:203-207` | `GA-REM-007` · `R-23` |
| La validación está duplicada y descentralizada | única invocación en `review/service.py:318`, con `import` local dentro del método | `GA-REM-007` (centralización — ya era su objeto) |

---

## 6. RC-05 · Política de contraseñas

### 6.1 Inventario completo de las reglas existentes

| # | Regla | Ubicación | ¿Es una política? |
|---|---|---|---|
| 1 | `min_length=8` en el alta de usuario | `backend/app/auth/schemas.py:39` | **sí** — única declaración de política del sistema |
| 2 | `min_length=6` en la petición de *login* | `backend/app/auth/schemas.py:11` | **no** — restricción de entrada sobre un intento de autenticación |
| 3 | `z.string().min(6)` en el formulario de *login* | `frontend/src/pages/auth/LoginPage.tsx:14` | **no** — espejo de la anterior |
| 4 | `newPassword.length < 6` en el perfil | `frontend/src/pages/users/ProfilePage.tsx:21` | **no** — validación de una ruta que no funciona (§6.3) |

Las reglas 2 y 3 no fijan política: se aplican a un intento de *login*, no a la creación
de un secreto. La regla 4 valida una operación inexistente. **Solo la regla 1 es una
política**, y no compite con ninguna otra: el conflicto registrado era aparente.

### 6.2 Silencio de los niveles superiores

Búsqueda en cliente, `docs/**` y `specs/**`: **ninguna fuente enuncia una política de
contraseñas** (longitud, complejidad, caducidad o histórico). El nivel más alto que se
pronuncia es el 5, la implementación, y lo hace una sola vez: `min_length=8`.

### 6.3 Hallazgo nuevo — el cambio de contraseña falla en silencio

`ProfilePage` envía `PUT /api/v1/users/{id}` con `{ password }`
(`ProfilePage.tsx:24`). `UserUpdate` **no declara `password`** (`auth/schemas.py:42-49`)
y no fija `model_config`, por lo que rige el `extra="ignore"` de Pydantic v2: el campo se
descarta antes de llegar al servicio. `update_user` hace
`data.model_dump(exclude_unset=True)` (`auth/service.py:136`), que nunca contendrá la
clave. La respuesta es **200 OK** y la interfaz muestra `profile.passwordUpdated`.

**Verificación en ejecución** (base de pruebas aislada, Wave 1.5):

```
[1] alta de usuario                        -> 201
[2] PUT /api/v1/users/4 {"password": ...}  -> 200   ← la API confirma
[3] login con la contraseña NUEVA          -> 401   ← la nueva no sirve
[4] login con la contraseña ORIGINAL       -> 200   ← la vieja sigue viva
VEREDICTO: CAMBIO DESCARTADO EN SILENCIO
```

Severidad **P0**. El usuario cree haber rotado su credencial y no lo ha hecho: cualquier
rotación tras una sospecha de compromiso es ficticia. Se registra como **`P0-13`**.
Alcanza también a `UsersPage.tsx:26`, que envía `password` al editar un usuario.

Como efecto colateral, `PUT /api/v1/users/{id}` no comprueba autorización más allá de
estar autenticado (`auth/router.py:88-95`): cualquier usuario válido puede modificar el
registro de cualquier otro. Se enlaza con `GA-REM-002` (RBAC), no se amplía aquí.

### 6.4 Regla vigente resuelta

> **RR-05.** La política de contraseñas del sistema es **una sola**: longitud mínima de
> **8** caracteres, aplicada de forma idéntica en el alta, en el cambio por el propio
> usuario y en el restablecimiento por un administrador. El *login* no impone longitud
> mínima: valida credenciales, no políticas. El cambio de contraseña debe ser una
> operación explícita, con verificación de la contraseña actual cuando el usuario cambia
> la propia, y **no puede aceptarse en silencio**: una petición que no cambia la
> contraseña debe fallar, no responder `200`.

### 6.5 Lo que queda para el propietario — no bloqueante

Ninguna fuente exige reglas de **complejidad** (mayúsculas, dígitos, símbolos), caducidad
ni histórico de reutilización. Su ausencia no es un conflicto: es una decisión de
endurecimiento nunca planteada. Se registra como `OD-01`, **no bloquea `GA-REM-012`**,
cuyo objeto es que el cambio funcione y que la longitud sea única.

---

## 7. RC-07 · Política de mortalidad frente a SAP

### 7.1 El cliente no resuelve: escala

El documento del cliente incluye una sección titulada **«25. Decisión crítica antes de
avanzar»** que enumera cinco definiciones que *la empresa* debe cerrar en SAP. La cuarta es
literalmente el objeto de `RC-07`:

```
Recomendación central.pdf §25
  4. La mortalidad generará movimiento de inventario o solo indicador/costo.
```

Y en §5, sobre el maestro de materiales:

```
Recomendación central.pdf:324-327
  ● Mortalidad, solo si SAP la manejará como material/merma.
  No recomiendo manejar "mortalidad" como material si solo será KPI.
  Sí debe manejarse si contablemente se necesita valorizar la baja.
```

El nivel 2 de la jerarquía **se pronuncia declarando que la decisión no está tomada**.
Ningún nivel inferior puede suplirla: la elección determina si la app emite un documento
de material contra SAP o solo un indicador, y eso es una decisión contable de la empresa.
No se resuelve por evidencia técnica. Se cierra como **`OWNER_DECISION_REQUIRED`**.

### 7.2 Las tres opciones, formuladas para que sean decidibles

| Opción | Qué hace la app | Qué recibe SAP | Requisitos previos |
|---|---|---|---|
| **O-1 · Baja valorizada** | Emite movimiento de inventario por la mortalidad | Documento de material (merma/baja) contra lote/centro de costo | Material «mortalidad» creado en SAP; almacén y motivo de movimiento definidos; §25.1 (ave viva como inventario valorizado) resuelto en el mismo sentido |
| **O-2 · Solo indicador** | Registra, valida contra el balance y publica KPI | Evento productivo sin impacto de stock — o nada | Ninguno adicional |
| **O-3 · Híbrida** | Indicador siempre; baja valorizada solo por causa (p. ej. descarte sanitario) | Documento de material únicamente para las causas marcadas | Catálogo de causas clasificado por impacto contable; regla de clasificación aprobada |

### 7.3 Qué desbloquea esta clasificación

`RC-07` afecta **solo al mapeo hacia SAP**, no a la captura. El cliente exige registrar
mortalidad («Registrar mortalidad — Sí», §2) y bloquear «mortalidad superior a población
actual» (§17) **con independencia de la opción elegida**.

> **RR-07.** La captura de mortalidad, su validación contra el balance de aves y su
> exposición como indicador son requisitos firmes y **no dependen de `RC-07`**. Solo el
> mapeo de mortalidad a un documento SAP queda supeditado a la decisión del propietario.

En consecuencia `RC-07` **deja de bloquear `GA-REM-005`** (mortalidad y balance de aves) y
bloquea exclusivamente la parte de mapeo de mortalidad dentro de `GA-REM-017`, que ya
estaba `BLOCKED_EXTERNAL` por el contrato técnico SAP.

---

## 8. Resultado por RC

| RC | Clasificación | Regla vigente | Desbloquea | Bloqueo residual |
|---|---|---|---|---|
| `RC-01` | `RESOLVED_BY_EVIDENCE` + `SPEC_DEFECT` | `RR-01` | `GA-REM-006` | ninguno |
| `RC-02` | `RESOLVED_BY_EVIDENCE` | `RR-02` | `GA-REM-005`, `GA-REM-018` | ninguno |
| `RC-03` | `RESOLVED_BY_EVIDENCE` | `RR-03` | `GA-REM-007` | ninguno |
| `RC-04` | **`RESOLVED_BY_EVIDENCE`** + `SPEC_DEFECT` (Wave 2) | `RR-04` | `GA-REM-008` | ninguno |
| `RC-05` | `RESOLVED_BY_EVIDENCE` (longitud) | `RR-05` | `GA-REM-012` | `OD-01` complejidad — **no bloqueante** |
| ~~`RC-06`~~ | cerrado en Wave 1 por `RA-05` | — | — | — |
| `RC-07` | `OWNER_DECISION_REQUIRED` | `RR-07` (alcance acotado) | `GA-REM-005` | mapeo SAP de mortalidad en `GA-REM-017` |

---

## 9. Decisiones que siguen correspondiendo al propietario

| ID | Decisión | Bloquea | Urgencia |
|---|---|---|---|
| `OD-01` | ¿Se exigen reglas de complejidad, caducidad o histórico de contraseñas? | nada | baja |
| `OD-02` | `RC-07` — ¿mortalidad como baja valorizada (`O-1`), indicador (`O-2`) o híbrida (`O-3`)? | mapeo SAP de mortalidad | media — antes de `GA-REM-017` |
| `OD-03` | ¿Alguna empresa operará con `require_segregation = False`? | nada — el valor por defecto es `True` | baja |

Ninguna de las tres bloquea la Wave 2.

---

## 10. Hallazgos nuevos generados por Track A

| ID | Hallazgo | Severidad | Evidencia | Destino |
|---|---|---|---|---|
| `P0-13` | El cambio de contraseña se descarta en silencio y responde `200` | **P0** | `auth/schemas.py:42-49` · `auth/service.py:136` · verificado en ejecución (§6.3) | `GA-REM-012` |
| `R-23` | `complete_review` aprueba sin validar `BR-14` cuando `approval_levels <= 1` | P1 | `review/service.py:203-207` | `GA-REM-007` |
| `R-24` | `bird_transfer` no valida población de origen ni capacidad de destino a nivel de galpón | P2 | `validators.py:27-33` · `validate_house_capacity` sin aplicar | `GA-REM-005` |
| `R-25` | `PUT /users/{id}` no comprueba autorización más allá de la autenticación | P1 | `auth/router.py:88-95` | `GA-REM-002` |

Ninguno se corrige en esta Wave. Todos quedan trazados.


---

## 11. `RC-04` — resuelto en la Wave 2 · Stage 8

### El conflicto

`spec.md §4.9`: «Un EggBatch se crea automáticamente al registrar `egg_dispatch` +
`egg_reception_hatchery` **para el mismo lote de huevos**». La implementación lo leyó como
«el mismo `lot_id`» y filtró ambos lados por él.

### La evidencia decisiva vuelve a ser estructural

`EggBatch` declara **dos** columnas de lote:

```
backend/app/lots/models.py:109   source_lot_id    -> lots.id   (lote reproductor origen)
backend/app/lots/models.py:111   hatchery_lot_id  -> lots.id   (lote de incubadora destino)
```

Existen dos porque son dos lotes distintos. Si «el mismo lote» significara un identificador
compartido, la segunda columna no tendría razón de ser y el vínculo uniría un lote consigo
mismo. La lectura correcta es la única que el modelo admite: **el mismo lote físico de
huevos viajando de un lote productivo a otro**.

Es el mismo argumento que resolvió `RC-02`: el esquema es incapaz de expresar la
alternativa, luego la alternativa no era una opción de negocio.

> **RR-04.** «El mismo lote de huevos» designa el mismo lote físico, no un `lot_id`
> compartido. El vínculo une **siempre dos lotes distintos**; uno que se enlaza consigo
> mismo es, por definición, incorrecto. El emparejamiento automático usa el **destino
> declarado por el operador** (`destination_farm_id` / `destination_plant_id`) — utilizable
> solo desde que `P0-14` lo persiste. Sin destino declarado no se crea vínculo automático:
> `spec.md §4.9` ya contempla el enlace manual para ese caso, y adivinar la
> correspondencia sería peor que no establecerla.

Clasificación secundaria: **`SPEC_DEFECT`**. La redacción de `spec.md §4.9` es ambigua y
fue la que produjo el defecto; conviene precisarla.

## 10. RC-10 · Unidad y reglas de valor del consumo diario de agua (`GA-REM-021 B05`) — 2026-09-09

| # | Nivel | Dice |
|---|---|---|
| 2 · Cliente | «Cantidad de agua consumida por los pollitos / las gallinas / los pollos durante el día» (`Bases` p.2, 4, 12) — **calla** sobre unidad, cero y decimales; igual que con el alimento |
| 3 · Proceso | `docs/02`, `docs/12`: **silencio** (el agua no aparece) |
| 4 · Spec | `spec.md`: silencio; `GA-REM-021`: el campo es opcional en la primera iteración; dónde vive lo deja a la spec |
| 5 · Implementación | el reporte lee `e.water_liters` y suma `water_l` (`ReportsPage.tsx:24-30`); el consumo diario existente (`FeedMovementSchema.quantity_kg`) es `Float` y `gt=0` |
| 6 · Legado | «Agua: Registro por semana (Lt Agua x Ave x Sem)»; `docs/15` prevé `OperationalEvent.water_liters` |

El nivel 2 fija **qué** (consumo), **cuándo** (día) y **quién** (parvada); calla sobre la unidad y el valor. Los niveles 3 y 4
callan. El nivel 5 se pronuncia (litros; consumo estrictamente positivo con decimales) y el 6 lo confirma (litros). La elección
no cambia el comportamiento de negocio respecto al alimento, ya certificado con la misma regla: **no hay escalado**.

> **RR-10.** El consumo diario de agua se registra en **litros** (`water_liters`), sin campo de unidad libre.
> **RR-11.** El consumo diario de agua, como el de alimento, es **estrictamente positivo** con decimales; la ausencia de dato se
> representa como **ausencia** (sin fila / `NULL`), nunca como `0`.

## 11. `RC-11` · cuadre y rango de pesos en la recepción de reproductoras (`GA-REM-021` `B01`/`B02`, 2026-09-10)

**Conflicto aparente 1 (`B01`).** `Recomendación central §6` exige que «hembras + machos + mortalidad + rechazo cuadren contra
recibido», pero el modelo (nivel 5) solo persiste `BirdMovement(sex, quantity)` y mapea la mortalidad al arribo a un evento
`mortality_recording` aparte (`docs/16:177`); la planificación de la ola B (nivel 5, `WAVE_B §2`) suponía que «el cuadre usa el saldo».
**Corte:** el nivel 2 nombra los sumandos y el lado derecho («Cantidad recibida», dato de la misma captura); la elección de nivel 5
cede. El saldo (`R-130`) no es el lado derecho: es la **consecuencia** (entran las alojadas). No hay escalado: nada cambia de
comportamiento de negocio respecto a lo que el cliente escribió; solo se capturan los datos que la regla necesita.

> **RR-12.** En la recepción de reproductoras, `recibido = Σ aves alojadas (♀ + ♂ por galpón) + mortalidad al arribo + rechazo`,
> con igualdad exacta y sin tolerancia; los tres datos se declaran explícitamente (la ausencia no es `0`); las **alojadas** son las
> entradas del saldo de aves (`R-130`, sin cambio) y la mortalidad al arribo y el rechazo **nunca** entran al saldo. Cada entrega
> parcial cuadra por sí misma; la acumulación contra la OC sigue siendo `BR-18` (`OD-04`).

**Conflicto aparente 2 (`B02`).** `§6` exige «pesos dentro de rango esperado» sin nombrar el referente. Candidatos: la curva estándar
del lote (`OD-06`, nivel 1; `docs/02 §3.12.1/§3.14`, nivel 3; `spec.md §4.5`, nivel 4), el peso declarado por el proveedor (nivel 6,
`R-156`/`AOD-20`) y un estándar fijo de pollito de un día (inexistente). El pre-flight del tranche 6 anotó «si ninguna fuente por encima
de la implementación lo fija, `OWNER_DECISION_REQUIRED`». **Corte:** el silencio del nivel 2 desciende a los niveles 3 y 4, que conocen
un único estándar de peso, y a `OD-06`, que fija su origen para la fase §4.5 de la que la recepción es el primer evento. La cautela
queda desestimada; no hay escalado. La consecuencia de estar fuera de rango la fija `GA-REM-037 §5` (nivel 4): alerta, no bloqueo —
coherente con «la app debe capturar la realidad de granja» (nivel 2, p.1).

> **RR-13.** El «rango esperado» de los pesos de la recepción de reproductoras es el de la **curva estándar fijada al lote** a la edad
> del lote el día de la recepción (`OD-06`, `GA-REM-037`: gramos, días, interpolación lineal, bordes inclusivos, sin tolerancia, sin
> extrapolación → `NO_REFERENCE` declarado). Cada fila ♀/♂ se evalúa contra la misma curva (el estándar de `OD-06` no distingue sexo).
> Fuera de rango se **persiste, se clasifica y alerta**; no bloquea el alta ni la aprobación. El peso declarado por el proveedor es
> `R-156` (`AOD-20`) y no participa. No aplica a engorde (`§4.8` sin alertas), progenitoras ni incubadora.

## 12. `RC-12` · nacimientos: una contabilidad, dos atributos (`GA-REM-021 B13` · `R-170`, 2026-09-10)

**Conflicto.** La UI de nacimiento (nivel 5) modelaba «Total nacidos», «Machos viables», «Hembras viables» y «Débiles» como cuatro filas de
`bird_movements`, y el saldo (nivel 4, `GA-REM-005-B`) suma todas las filas: un total y su desglose se contaban dos veces (`R-170`,
observado: 100 pollitos → viables 200). `Bases` p.9 (nivel 2) define **un** total («cantidad total de pollitos nacidos») y dos
subconjuntos disjuntos de ese total («nacidos sanos y viables», «nacidos débiles o con problemas»); no define ni «machos viables» ni una
fila «total». **Corte:** nivel 2 sobre nivel 5.

> **RR-14.** Los nacidos son `Σ bird_movements.quantity` del `birth_registration`, con **una fila por sexo** (`male`, `female`, `mixed`) y
> `mixed` excluyente con las filas sexadas; no existe fila «total»: el total se deriva. Un nacimiento sin nacidos no es un nacimiento (Σ ≥ 1).

> **RR-15.** «Sanos» y «débiles» son **atributos** del nacimiento (`chicks_healthy`, `chicks_weak`), subconjuntos disjuntos de los nacidos
> (`sanos + débiles ≤ nacidos`) que **no entran en ningún saldo**; «débil» no es descarte ni mortalidad (el descarte sigue siendo
> `cull_recording`, `Rec. §12`; la mortalidad, `mortality_recording`). La igualdad `sanos + débiles = nacidos` no la afirma ninguna fuente
> (`AOD-23`). Sin sanos/débiles por sexo (`GA-REM-005:420`).

## 13. `RC-13` · descarte de pollitos: evento, no atributo del nacimiento (`R-171`, 2026-09-10)

**Conflicto.** `docs/02 §3.7.5` y `spec.md §4.7` (nivel 3/4) listan «Pollitos descartados» entre los datos del **nacimiento**; `GA-REM-005-B`
(nivel 4, certificado con `R-130`) modela el descarte como el **evento** `cull_recording` que resta de viables; `Bases` p.9 (nivel 2) no tiene
descartados al nacer y `Rec. §12` (nivel 2) pide capturar «Pollitos descartados» sin fijar la representación. **Corte:** el nivel 2 exige el
dato y calla la forma; entre las dos formas de nivel 3/4, la única que no duplica el efecto (`R-170`) es la ya certificada.

> **RR-16.** El descarte de pollitos es el evento `cull_recording` del lote de incubación (posterior al nacimiento), que resta de viables y
> del saldo una sola vez; no se añade un atributo «descartados» al nacimiento. La mortalidad de pollitos (`Bases` p.10) es el evento
> `mortality_recording` del mismo lote. Ambos deben ofrecerse en el flujo de incubadora (`R-171`).
