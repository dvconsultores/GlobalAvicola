# GA-FE-06 · PLAN (P1–P37)

Ejecución autónoma de extremo a extremo. Estados: ✔ hecho · ◐ en curso · ○ pendiente.

| # | Paso | Estado |
|---|---|---|
| P1 | Preflight: rama/HEAD local==remoto, worktree limpio, salud del runtime, bundle de entrada congelado | ✔ |
| P2 | Baseline frontend: tsc 0, build OK, Vitest 273/273 | ✔ |
| P3 | Baseline backend local (corrida PG-libre: 7 passed · lotes/SLA skipped sin PG, declarado) | ✔ |
| P4 | Lectura canónica del backlog R-182 | ✔ |
| P5 | Lectura canónica del modelo `Lot`/`Area` | ✔ |
| P6 | Verificación de migración (sin migración nueva) | ✔ |
| P7 | Lectura de schemas lote (create/update/read) | ✔ |
| P8 | Lectura del servicio (create/update/close, fecha de negocio, guardas) | ✔ |
| P9 | Lectura del evaluador SLA + destinatarios | ✔ |
| P10 | Lectura del formulario (zod, payload, maestros) | ✔ |
| P11 | Verificación i18n de claves existentes/faltantes | ✔ |
| P12 | Dedup: sin duplicados de R-182 en el backlog | ✔ |
| P13 | Reconciliación canónica escrita | ✔ |
| P14 | Traza del modelo de datos escrita | ✔ |
| P15 | Trazabilidad SLA escrita | ✔ |
| P16 | Matriz de alta escrita | ✔ |
| P17 | Matriz de edición escrita (N/A justificado) | ✔ |
| P18 | Matriz de contrato SLA escrita (3 capas de certificación) | ✔ |
| P19 | Matriz de actores escrita | ✔ |
| P20 | Matriz de fixtures escrita | ✔ |
| P21 | Especificación R182-AC01…52 escrita | ✔ |
| P22 | Clarificaciones C01–C25 escritas | ✔ |
| P23 | Plan/checklist/tareas escritos | ○ |
| P24 | Prueba RED vitest del contrato de alta (fallo objetivo triple) | ○ |
| P25 | Evidencia RED runtime pre-implementación (fixtures + alta real) | ○ |
| P26 | C1: commit de gobernanza + RED (+ push) | ○ |
| P27 | Implementación mínima: selector de áreas + payload PLD/área + clave i18n + fila detalle | ○ |
| P28 | GREEN dirigido + regresión completa frontend (tsc/build/Vitest) + gate PG-libre backend | ○ |
| P29 | C2: commit de implementación + push ⇒ despliegue (Docker/Watchtower) | ○ |
| P30 | Congelar generación nueva (bundle + Last-Modified + ETag) | ○ |
| P31 | E2E-01…16 autenticados (desktop/móvil, ES/EN, red, consola, auditoría) | ○ |
| P32 | Regresiones GA-FE-02/03/04/05 (R-98/R-119/R-181 verdes) | ○ |
| P33 | Escaneo SLA oportuno (relectura al cierre) | ○ |
| P34 | Higiene §101 (revocaciones, OFF de BUs, baja de áreas/roles/usuarios, destrucción de credenciales) | ○ |
| P35 | Documentos de evidencia (runtime, red, capturas, ledger, reconciliación R-182) | ○ |
| P36 | Cierre: certificación + addendum de auditoría + catálogo + paquete UAT | ○ |
| P37 | C4 evidencia + verificación final local==remoto/worktree limpio + informe final + STOP | ○ |
