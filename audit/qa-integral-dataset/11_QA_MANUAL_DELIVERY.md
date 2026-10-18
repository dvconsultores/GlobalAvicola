# 11 · Entrega de la guía QA

| Entregable | Ruta | Formato | Contenido |
|---|---|---|---|
| Guía de prueba funcional integral | `docs/MANUAL_QA_PRUEBA_INTEGRAL_GLOBAL_AVICOLA.md` | Markdown | 14 secciones: acceso y usuarios (sin contraseñas), empresas, estados; login y menú por rol (matriz rol × opción); dashboard; lotes (tabla de 23 lotes con su situación), crear/transición, historial y pendientes; registro de operaciones por cadena con casos positivos y negativos (BR-18, CUT-GL-02, saldos); revisión, aprobación individual y en lote, BR-14, corrección, reverso, cancelación; Integración SAP sintética; reportes; cargas iniciales (4 aplicadas + 4 fixtures); auditoría; administración (maestros, usuarios, acceso por unidad, perfil); multiempresa; notificaciones; qué hacer ante un fallo; fuera de alcance |
| Guía (Word) | `docs/MANUAL_QA_PRUEBA_INTEGRAL_GLOBAL_AVICOLA.docx` | DOCX (python-docx, generado desde el MD) | mismo contenido con tablas y estilos |
| Plantilla de resultados | `docs/QA_EXECUTION_RESULTS_TEMPLATE.docx` | DOCX | cabecera (persona QA, fecha, navegador, SHA), resumen OK/FALLO/BLOQUEADO, tablas por sección (2–12) con columnas Caso/Usuario/Resultado/Observación/Captura, tabla de hallazgos, firma |
| Fixtures de cargas iniciales | `audit/qa-integral-dataset/fixtures/QA_cutover_{grandparent,breeder,hatchery,broiler}.xlsx` | XLSX v2 (SPEC 006) con instrucciones y catálogos | códigos `QA-CUT-*-NEW-*` libres para el ciclo manual de QA |
| Matriz de cobertura | `audit/qa-integral-dataset/QA_DATA_COVERAGE_MATRIX.md` | Markdown | 26/26 entradas de `navigationConfig.ts` × datos × usuario × sección de la guía |
| Manuales previos (contexto) | `docs/MANUAL_USUARIO.md`, `docs/MANUAL_CARGAS_INICIALES.md` | Markdown | manual de usuario de todas las opciones; manual de las plantillas de cargas iniciales campo a campo |

## Controles

- Sin contraseñas, sin SQL, sin código, sin rutas de servidor ni DSN en la guía ni en la plantilla (revisión por `grep` en `evidence/`: SIN_FUGAS).
- Lenguaje de usuario; cada caso con *qué hay cargado · qué hacer · resultado esperado*.
- Credenciales: el Owner recibe la contraseña temporal por canal separado y la comunica a QA; el manual solo lista usuario/rol/empresa/BU/propósito (OD-QA-05).
