# 01 · Hallazgos de origen — Revisión QA (Yolinel Cortez, 2026-10-17)

> **NOTA DESTACADA — Fuente y trazabilidad**
>
> El PDF original **«REVISION GENERAL DE SISTEMA GLOBAL AVICOLA - 17-10-2026.pdf»** **NO está disponible**
> en la estación de trabajo. Por lo tanto, la fuente de este documento es el **mandato del Owner**, que
> transcribe los hallazgos tal como los formuló QA.
>
> Las **capturas de pantalla quedan pendientes de contraste** cuando el PDF esté disponible; en la tabla
> cada observación lleva la marca `pendiente PDF`. Este documento es **transcripción fiel del mandato**,
> no una certificación: es un insumo para la clasificación formal (ver «Siguiente paso»).

## Cabecera

| Campo | Valor |
|---|---|
| Fecha de la revisión | **2026-10-17** |
| Tipo de documento | `QA_GENERAL_EXPLORATORY_REVIEW` |
| Autor de la revisión | QA — Yolinel Cortez |
| Carácter | **PRELIMINAR / exploratoria** — no constituye certificación |
| Empresa usada en la revisión | «Avícola Global, C.A.» |
| Usuario usado en la revisión | `admin` |
| Fuente de este documento | Mandato del Owner (transcripción de hallazgos) |
| PDF original | **NO DISPONIBLE** en la estación de trabajo → capturas pendientes de contraste |
| Prioridad estratégica del Owner | **Reproductoras e Incubadora** para Líder Pollo |

### Alcance revisado

- **Administración**: Configuración, Usuarios, Roles, Perfil, Accesos por Unidad.
- **Maestros**: ~20 maestros.
- **Auditoría**.
- **Cargas Iniciales**: solo el paso **Unidad** y **Corte**.
- **Operativo**: Gestión Avícola (general).
- **Revisión**: Centro de Revisión, Aprobaciones.

### Alcance NO revisado

- **SAP** (módulo).
- **Reportes** (módulo).
- **Cargas Iniciales**: únicamente se recorrió el paso inicial (Unidad y Corte).

## Tabla de observaciones (18)

> Texto **fiel al mandato**. Tipo: `PREGUNTA` (indagación de comportamiento/regla de negocio),
> `OBSERVACIÓN` (hallazgo de comportamiento o presentación), `PROPUESTA` (mejora sugerida por QA).
> Columna «Captura»: todas `pendiente PDF` (ver nota destacada al inicio).

| ID | Módulo / Pantalla | Tipo | Texto (fiel al mandato) | Captura |
|---|---|---|---|---|
| QA-001 | Maestros | PREGUNTA | ¿Estos maestros (Granjas/Incubadoras) están relacionados a cada Granja o Incubadora con la Unidad de Negocio correspondiente? | pendiente PDF |
| QA-002 | Maestros | PREGUNTA / OBSERVACIÓN | ¿Un maestro puede eliminarse si ya existen registros que lo utilizan? Si proviene de SAP, no debería eliminarse en Global Avícola. | pendiente PDF |
| QA-003 | Maestros | PREGUNTA | ¿Existe un campo único que permita identificar Vacunas, Medicamentos, Causas de Mortalidad y Causas de Descarte? | pendiente PDF |
| QA-004 | Maestros / Incubadora | PREGUNTA | ¿Las plantas/incubadoras manejan ZONA igual que las Granjas? | pendiente PDF |
| QA-005 | SAP | PREGUNTA | Cómo se relacionan los maestros importados de SAP. | pendiente PDF |
| QA-006 | Lotes | PREGUNTA | ¿Los lotes vienen de SAP? ¿En qué casos se crean directamente en Global Avícola? | pendiente PDF |
| QA-007 | Operativo / Recepción de Aves | OBSERVACIÓN (crítica) | No debería poder seleccionarse una orden de Engorde dentro de Reproductoras. | pendiente PDF |
| QA-008 | Operativo / Recepción de Aves | OBSERVACIÓN | Al seleccionar una OC SAP en Recepción de Aves de Reproductoras todavía debe seleccionar granja, lote, etc. | pendiente PDF |
| QA-009 | Operativo | PREGUNTA (crítica) | ¿Se valida que los procesos se registren en orden? En Reproductoras/Cría no debería registrarse alimento si todavía no existe Recepción de Aves. | pendiente PDF |
| QA-010 | Revisión | PREGUNTA | ¿Desde qué estado pueden ocurrir rechazado, cancelado, reversado? | pendiente PDF |
| QA-011 | Revisión | PREGUNTA | ¿Cómo se configura y funciona la segregación de funciones? | pendiente PDF |
| QA-012 | Maestros | PROPUESTA | En los listados de Galpones, Incubadoras (equipo) y Nacedoras no se identifica claramente el padre (Granja / Planta). | pendiente PDF |
| QA-013 | Maestros | OBSERVACIÓN | Algunos maestros muestran una columna llamada EDITAR cuyo contenido corresponde a otro atributo. | pendiente PDF |
| QA-014 | Operativo / Revisión | PROPUESTA | Incluir Granja / Incubadora en Lotes, Historial, Mis Pendientes (y Centro de Revisión, Aprobaciones). | pendiente PDF |
| QA-015 | Operativo / Revisión | PROPUESTA | Agregar filtro por Granja / Incubadora. | pendiente PDF |
| QA-016 | Operativo | OBSERVACIÓN | En campos donde no se permiten fechas futuras, el calendario permite seleccionarlas y luego depende de la validación. | pendiente PDF |
| QA-017 | Revisión | OBSERVACIÓN | El Centro de Revisión busca constantemente (ejecución continua de búsqueda). | pendiente PDF |
| QA-018 | Operativo / Revisión | PROPUESTA | Mostrar Usuario y Fecha de creación en listados de registros operativos, revisión y aprobación. | pendiente PDF |

## Módulos no revisados

Estado declarado para los módulos fuera del alcance de esta revisión exploratoria:

| Módulo | Estado |
|---|---|
| SAP | `NOT_REVIEWED_YET` |
| Reportes | `NOT_REVIEWED_YET` |
| Cargas Iniciales | Solo paso inicial (**Unidad** y **Corte**) — resto `NOT_REVIEWED_YET` |

## Siguiente paso

La clasificación formal de estos 18 hallazgos (severidad, naturaleza, módulo, estado y tratamiento
propuesto) se realiza en **`02_FINDINGS_CLASSIFICATION.md`**.
