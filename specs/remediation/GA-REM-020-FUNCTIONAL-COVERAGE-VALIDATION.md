# GA-REM-020 — VALIDACIÓN DE COBERTURA FUNCIONAL CONTRA LA DOCUMENTACIÓN DEL CLIENTE

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-020` · **Tipo** `VALIDATION SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P1** |
| **Estado** | `SPEC_READY` |
| **Dependencias** | `GA-REM-001` |
| **Informa a** | `GA-REM-016` (certificación) · `GA-REM-021` · `GA-REM-022` · backlog general |
| **Hallazgo** | **R-15** — descubierto en la revalidación, no estaba en la auditoría |
| **Origen** | explotación de `Imagen de Procesos Documentado/`, registrada por la auditoría como fuente disponible y no explotada formalmente |

---

## ⚠ Aclaración de propósito (decisión del propietario)

> **La taxonomía de procesos del proyecto NO debe adecuarse a la codificación de PROTINAL.**
>
> La documentación del cliente se utiliza **exclusivamente como fuente de validación**: sirve para comprobar que los procesos, procedimientos, pasos, reglas de negocio, datos y KPI implementados son **completos y correctos**.
>
> Global Avícola conserva su propia taxonomía (`processCatalog.ts`, 6 etapas) como unidad de trabajo y de certificación.

Queda **expresamente fuera de alcance**:
- adoptar los códigos `AVI-*` como identificadores del sistema;
- reestructurar `processCatalog.ts` para replicar la descomposición del cliente;
- convertir cada proceso codificado del cliente en una unidad certificable;
- renombrar etapas, operaciones o pantallas para alinearlas con la nomenclatura de PROTINAL.

---

## 1. Problema

El repositorio contiene 43 documentos funcionales del cliente que **nunca se han usado para validar la implementación**. La auditoría los registró como fuente disponible y no explotada; la revalidación posterior los abrió y, en una lectura parcial, encontró de inmediato **dos requisitos incumplidos** (R-13 consumo de agua, R-14 tasa de eclosión).

El problema no es que la taxonomía difiera. El problema es que **nadie ha comprobado sistemáticamente si lo implementado cubre lo que el negocio describió**, y la muestra sugiere que hay más huecos.

## 2. Evidencia

### 2.1 Material disponible y su utilidad como fuente de validación

| Documento | Contenido | Utilidad |
|---|---|---|
| `Bases Consideradas en el Desarrollo de la App Avicola.pdf` (13 pág.) | **documento de requerimientos original**, firmado por la gerencia de proyecto. Define, por etapa, los datos diarios a registrar y los KPI calculables | **alta** — es la fuente de requisitos funcionales |
| `Control de Codificación de Procesos Avicolas PROTINAL.xlsx` | inventario de 30 procesos del negocio con área, nombre y estado | **alta** — sirve de **lista de comprobación de cobertura**, no de estructura a copiar |
| `Sap y App Proceso Avícola Software primera version.pdf` (34 pág.) | descripción del proceso avícola y su relación con SAP | media — contexto de negocio; **no** contiene el contrato técnico de SAP |
| `Recomendación central.pdf` · `Incubadora.pdf` | procedimientos operativos | media |
| Manuales Ross y Cobb (5 PDF) | estándares técnicos de la línea genética | **alta** para validar curvas, rangos y umbrales |
| `Formato Especificaciones - AVI-*.xlsx` (30 archivos) | formularios de especificación de proceso | **baja** — ver limitación §2.3 |
| Capturas del sistema legacy (`.docx`, `.pdf`) | referencia de la aplicación anterior | media — permite detectar funcionalidad perdida |
| `Proceso de Avicola - Modificado-1.0.png/jpg` | diagrama del proceso global | media |

### 2.2 Verificación del estado actual
```
grep -r "AVI-" specs/ docs/            → 0 resultados
grep -r "AVI-" backend/app frontend/src → 1 resultado
```
La única aparición es un **placeholder de ejemplo** en el campo de código de lote:
`frontend/src/pages/lots/LotFormPage.tsx:129` → `placeholder="AVI-REP-PES-2024-001"`.

Es preexistente y **no constituye adopción de la taxonomía**: solo sugiere al usuario un formato de código de lote. Se deja como está.

Fuera de eso, **ninguna referencia cruzada** entre la documentación del cliente y el proyecto: la especificación se redactó sin trazar contra esta fuente.

### 2.3 Limitación de la fuente — `RA-04`
Los 30 formatos `Formato Especificaciones - AVI-*.xlsx` resultaron ser **plantillas vacías**. Contienen la estructura del formulario (Actividad · Rol asociado · Frecuencia · Paso a Paso · Reglas de Negocio · Entradas · Salidas · KPI) sin contenido rellenado. Solo 5 de 30 figuran como «LISTO» en el índice y ninguno de los revisados contiene el detalle del proceso.

**Consecuencia:** el detalle paso a paso por proceso **no está disponible**. La validación se apoyará en el documento de requerimientos, los manuales técnicos y el inventario de procesos, no en los formatos.

### 2.4 Muestra de lo que la validación encuentra
Una lectura parcial del documento de requerimientos ya produjo:

| Hallazgo | Naturaleza |
|---|---|
| **R-13** consumo de agua exigido en 3 etapas y **no capturado** | requisito incumplido |
| **R-14** tasa de eclosión que devuelve texto en vez de número | requisito incumplido |
| `egg_storage` exigido por el cliente y sin spec del proyecto | reclasificado de scope creep a `SPEC_GAP` |
| condiciones de transporte exigidas y **sí** implementadas | confirmación de cobertura |

Una validación sistemática cubrirá el resto.

## 3. Comportamiento actual
Ningún mecanismo comprueba si la implementación cubre lo que el negocio describió. Los huecos solo aparecen por casualidad.

## 4. Comportamiento esperado
Existe una **matriz de validación de cobertura funcional** que, para cada elemento documentado por el cliente, declara si está cubierto, parcialmente cubierto, ausente o fuera de alcance — con evidencia. Los huecos encontrados entran al backlog como hallazgos con su propia spec.

## 5. Alcance

1. **Extraer y catalogar** el contenido funcional utilizable de la documentación del cliente:
   - datos diarios exigidos por etapa;
   - KPI calculables exigidos por etapa;
   - procesos y procedimientos del inventario;
   - rangos y estándares técnicos de los manuales Ross y Cobb;
   - funcionalidad visible en las capturas del sistema legacy.
2. **Contrastar cada elemento** contra la implementación actual: modelo de datos, tipos de evento, formularios, reglas de negocio, KPI y pantallas.
3. Producir la **matriz de validación de cobertura**.
4. Registrar cada hueco como hallazgo, con su prioridad y su spec destino.
5. Registrar cada **confirmación** de cobertura: son evidencia positiva para la certificación de procesos.
6. Documentar las **discrepancias de criterio** entre la documentación del cliente y la implementación, sin resolverlas unilateralmente (Art. 18 de la constitución).

## 6. Fuera de alcance

- Adoptar la codificación `AVI-*` como identificador del sistema.
- Reestructurar `processCatalog.ts` ni la taxonomía de 6 etapas.
- Implementar los huecos que se encuentren: cada uno genera su propia spec.
- La cadena LIVIANAS / Ponedoras, declarada fuera de v1 en `spec.md §9` (`RA-03`).
- Rellenar los formatos vacíos del cliente.

## 7. Matriz de validación — formato obligatorio

| ID | Elemento documentado | Fuente (documento · página) | Tipo | Etapa | Estado de cobertura | Evidencia en el código | Hallazgo |
|---|---|---|---|---|---|---|---|

**Tipo:** `dato` · `KPI` · `proceso` · `procedimiento` · `regla` · `estándar técnico` · `funcionalidad legacy`
**Estado de cobertura:** `CUBIERTO` · `PARCIAL` · `AUSENTE` · `FUERA_DE_ALCANCE` · `NO_VERIFICABLE`

Se versiona en `audit/remediation/FUNCTIONAL_COVERAGE_MATRIX.md`.

## 8. Validación preliminar ya realizada

### 8.1 Datos diarios exigidos por el cliente
| Dato | Etapas | Cobertura | Evidencia |
|---|---|---|---|
| Consumo de agua | Cría · Producción · Engorde | **AUSENTE** | `grep water backend/app` → 0 → `GA-REM-021` |
| Condiciones ambientales (temp. y humedad) | todas | `CUBIERTO` | `inspection_details` |
| Alimento consumido | todas | `CUBIERTO` | `feed_movements` |
| Peso de muestra representativa | todas | `CUBIERTO` | `bird_movements.avg_weight`, `sample_size` |
| Mortalidad diaria | todas | `CUBIERTO` (**bloqueado por P0-1**) | `bird_movements` + `validate_mortality` |
| Incidencias de salud | todas | `CUBIERTO` | `vaccination`, `medication` |
| Huevos puestos / fértiles / infértiles / descartados | Producción | `CUBIERTO` | `egg_movements.egg_type` |
| Peso promedio de huevos | Producción | `CUBIERTO` | `egg_movements.avg_weight` |
| Almacenamiento de huevos: fecha, condiciones, duración | Producción · Incubadora | `CUBIERTO` sin spec → `SPEC_GAP` | `egg_storage` |
| Condiciones de transporte | traslados | `CUBIERTO` | `extra_data.transport_*` |
| Identificación de lote para trazabilidad | traslados | `PARCIAL` — el emparejamiento está roto | `GA-REM-008` |
| Pollitos nacidos: sanos / débiles | Incubadora | `CUBIERTO` | `birth_registration` |
| Rotación de huevos: frecuencia y ángulo | Incubadora | `PARCIAL` — hay `turning` booleano, no frecuencia ni ángulo | **hallazgo nuevo, a confirmar** |
| Duración del almacenamiento | Incubadora | `CUBIERTO` | `egg_storage.storage_start_date` / `storage_end_date` |

### 8.2 KPI exigidos por el cliente
| KPI | Cobertura | Destino |
|---|---|---|
| Tasa de Eclosión | **devuelve texto** | `GA-REM-022` |
| Eficiencia de Vacunación | implementado, **sin consumidor** | `GA-REM-022` |
| Eficiencia de Traslado | implementado, **sin consumidor** | `GA-REM-022` |
| Tasa de Fertilidad | `PARCIAL` | `GA-REM-022` |
| % Huevos Infértiles · % Descartados · Alimento por Huevo · % Pollitos Sanos · Mortalidad de Pollitos | **por confirmar** | esta spec |
| Tasa de Mortalidad · Peso Promedio de Huevos · Conversión Alimenticia | `CUBIERTO` | — |

### 8.3 Procesos del inventario del cliente — comprobación de cobertura
Se usa como **lista de comprobación**, no como estructura. Cadena PESADAS (17 procesos en alcance):

| Proceso del cliente | ¿Cubierto funcionalmente por la implementación? |
|---|---|
| Recepción de Pollitos Reproductores (Abuelas) | sí — `grandparent_import`, `bird_reception`, `bird_distribution` |
| Control de Producción Cría y Levante (Abuelas) | sí, **bloqueado por P0-1** |
| Desalojo Cría y Levante (Abuelas) | sí — `bird_exit` |
| Recepción de Reproductores (Abuelas) | sí — `bird_reception` |
| Control de Producción de Huevo Fértil (Abuelas) | sí — `egg_collection`, `egg_dispatch` |
| Desalojo HF (Abuelas) | sí — `bird_exit` |
| Incubación de Reproductoras | sí — 9 eventos de incubadora |
| Recepción / Control / Desalojo de Reproductoras (×3) | sí — equivalentes en `breeder_rearing` y `breeder_production` |
| Recepción / Control / Desalojo HF Reproductoras (×3) | sí |
| Incubación de Pollos de Engorde | sí |
| Recepción de Pollitos Bebé | sí — `bird_reception` |
| Control de Producción de Pollo de Engorde | sí, **bloqueado por P0-1** |
| Desalojo de Pollo de Engorde | sí — `bird_exit`, `lot_closure` |

**Conclusión preliminar: los 17 procesos del cliente en alcance tienen cobertura funcional en la implementación**, aunque con otra descomposición y con dos de ellos bloqueados por el defecto de mortalidad. **No se detecta ningún proceso de negocio ausente.**

Esto **elimina** la preocupación registrada inicialmente como `RC-06`: no hay conflicto de granularidad que resolver, porque no se va a adoptar la granularidad del cliente. El «Desalojo» está cubierto como operación; no necesita ser una unidad certificable propia.

## 9. Reglas de negocio afectadas
Ninguna directamente. La validación puede **descubrir** reglas documentadas por el cliente y no implementadas; cada una se registraría como hallazgo.

## 10. Arquitectura / Frontend / Backend / Base de datos afectados
**Ninguno.** Esta spec no modifica código. Produce un documento de validación y hallazgos.

## 11. Seguridad
Ninguna superficie. La documentación se lee, no se publica.

## 12. Migraciones
Ninguna.

## 13. Compatibilidad
Total.

## 14. Edge cases
| Caso | Comportamiento exigido |
|---|---|
| Elemento documentado por el cliente y fuera del alcance v1 | `FUERA_DE_ALCANCE`, citando `spec.md §9` |
| Elemento del cliente que contradice una spec vigente | `REQUIREMENT_CONFLICT` (Art. 18); no se resuelve unilateralmente |
| Elemento cuya cobertura no puede determinarse sin el cliente | `NO_VERIFICABLE`, con la pregunta concreta a escalar |
| Funcionalidad implementada que el cliente no documenta | se registra; **no** implica que sobre |
| Formato del cliente vacío | `RA-04`; no se infiere contenido |

## 15. Acceptance Criteria

**AC01 — Matriz de validación completa**
```
Given la documentación funcional del cliente
When  se consulta la matriz de validación de cobertura
Then  cada elemento funcional extraído tiene un estado de cobertura asignado
And   cada estado tiene evidencia: ruta y línea, o la ausencia verificada
```
**AC02 — Los huecos generan hallazgos**
```
Given un elemento con estado AUSENTE o PARCIAL
When  se consulta la matriz
Then  tiene un identificador de hallazgo y una spec destino asignada
```
**AC03 — Las confirmaciones quedan registradas**
```
Given un elemento con estado CUBIERTO
When  se consulta la matriz
Then  cita la evidencia en el código que lo respalda
```
**AC04 — Cobertura de los procesos del cliente comprobada**
```
Given el inventario de procesos del cliente dentro del alcance v1
When  se contrasta contra la implementación
Then  cada uno tiene cobertura declarada
And   los que no la tengan están listados como candidatos a spec propia
```
**AC05 — La taxonomía del proyecto NO se modifica**
```
Given el diff de cierre de GA-REM-020
When  se listan los archivos modificados
Then  processCatalog.ts no ha sido modificado
And   ningún archivo de backend/app/ ni frontend/src/ ha sido modificado
And   no se ha introducido ningún identificador AVI-* nuevo en el código
And   el único preexistente (placeholder de LotFormPage.tsx:129) permanece sin cambios
```
**AC06 — Los estándares técnicos se validan**
```
Given las curvas y rangos de los manuales Ross y Cobb
When  se contrastan con thermalCurves.ts y los rangos codificados
Then  cada discrepancia queda registrada como hallazgo
```
**AC07 — Las discrepancias se escalan, no se resuelven**
```
Given una contradicción entre la documentación del cliente y una spec vigente
When  se registra en la matriz
Then  figura como REQUIREMENT_CONFLICT con alternativas e impacto
And   no se ha modificado ninguna spec ni código para resolverla
```

## 16. Tests requeridos
La spec produce un documento, no código.
| ID | Verificación |
|---|---|
| `T-020-01` | AC01 — completitud de la matriz frente al catálogo de elementos extraídos |
| `T-020-02` | AC05 — verificación del diff: sin cambios en código ni en `processCatalog.ts` |
| `T-020-03` | AC05 — no se han **introducido** identificadores `AVI-*` nuevos: el recuento en `backend/app` y `frontend/src` sigue siendo 1 (el placeholder preexistente de `LotFormPage.tsx:129`) |
| `T-020-04` | AC02 — cada `AUSENTE`/`PARCIAL` tiene hallazgo y destino |

## 17. Riesgos
| Riesgo | Mitigación |
|---|---|
| La validación se convierte en un rediseño encubierto hacia la taxonomía del cliente | AC05 lo verifica sobre el diff; el propósito está declarado en el encabezado |
| Los formatos vacíos llevan a inferir contenido inexistente | `RA-04`; no se infiere |
| La matriz encuentra tantos huecos que paraliza el programa | los huecos se registran y priorizan; no se implementan dentro de esta spec |
| Se resuelve una discrepancia unilateralmente | AC07 lo prohíbe; Art. 18 de la constitución |

## 18. Rollback lógico
No aplica: no se modifica código ni datos.

## 19. Definition of Done
- [ ] `FUNCTIONAL_COVERAGE_MATRIX.md` publicada y versionada
- [ ] AC01–AC07 verificados
- [ ] Cada hueco con hallazgo y spec destino
- [ ] `T-020-02` y `T-020-03` confirman que la taxonomía del proyecto permanece intacta
- [ ] Discrepancias escaladas, no resueltas
- [ ] Certification report
