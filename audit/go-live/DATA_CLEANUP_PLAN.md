# GLOBAL AVÍCOLA — DATA CLEANUP PLAN (entorno actual → operación real)

Fecha: 2026-09-17 · Baseline: `fef7289` · Estado: **PLAN (nada se borra en esta fase)**
Evidencia de inventario: `evidence/runtime-data-inventory.log` (2026-09-16T23:56Z, solo lectura).

---

## 1 · Inventario del runtime ACTUAL — clasificación (reconciliación pre-SAP-0)

> **Alcance**: entorno **SHARED DEVELOPMENT / TEST / CERTIFICATION / UAT** — **NO es inventario productivo real**. Clases: `TEST_UAT_CURRENT_RUNTIME_DATA` (producido por UAT/certificación) · `SYNTHETIC` (modelo/fixture de seed). **No es fuente de verdad** para el cutover real: la fuente real queda `PENDING_SAP0_DISCOVERY` (cadena `SAP-0 → GL-OD-06 → REAL DATA MIGRATION → CUTOVER G1/G2`).

| Dominio | Contenido observado | Clasificación |
|---|---|---|
| Empresas | 1 (`id=1` · `Avícola Global C.A.`) | `SYNTHETIC` |
| Granjas | 7 — `GN-01/GS-01/GE-01` (demo) + `FARM-GP01/FARM-BR01/FARM-BO01/FARM-BO02` (fixtures) | `SYNTHETIC` |
| Galpones | 34 | `SYNTHETIC` |
| Lotes | 10 — `E2E-MAN-153-*`, `L-GP-2026-01/06` = `SYNTHETIC`; `L-GP-2026-07…13` (incl. **67 cerrado con BR-18**) = `TEST_UAT_CURRENT_RUNTIME_DATA` (evidencia de certificación) | Clasificado |
| Genética | 2 (`Ross 308`, `Cobb 500`) | `SYNTHETIC` |
| Proveedores | 5 (Cobb-Vantress, Aviagen, Hendrix, Lohmann, Proveedor Local 1) | `SYNTHETIC` |
| Transportes | 4 (`ABC-123`…) | `SYNTHETIC` |
| Alimentos | 9 | `SYNTHETIC` |
| Causas mortalidad / descarte | 12 / 8 | `SYNTHETIC` |
| Vacunas / Medicamentos | 10 / 10 | `SYNTHETIC` |
| Fases productivas | 4 (Cría, Producción, Engorde, Incubación) | `SYNTHETIC` |
| **Referencias SAP** | **39** — `PO-C001-GPR-0001`, `STO-48000-*`, `PO-450000-*`, etc. | `SYNTHETIC` (ficticias; **no** provienen del landscape real; el SAP real es futuro y su landscape se auditará en SAP-0) |
| Usuarios/roles | No enumerables con la cuenta del canal (403 por rol); incluye usuarios de UAT/seed (`uat09-*`, `test_admin`, etc.) | `TEST_UAT_CURRENT_RUNTIME_DATA` + `SYNTHETIC` (seed) |
| Eventos operativos | Creados por UAT/E2E (p. ej. import 129/131, recepción, reverso 132, alimento 133 sobre lote 67) | `TEST_UAT_CURRENT_RUNTIME_DATA` (evidencia de certificación) |

## 2 · Clasificación (mandato §5)

| Clase | Elementos | Destino propuesto |
|---|---|---|
A · **Datos ficticios de arranque** (demo/maestros) | Empresa 1, granjas demo GN/GS/GE, catálogos modelo, transportes, proveedores | **Excluir del runtime real** (no se borran aquí) |
| B · **Fixtures técnicos de certificación** | `FARM-*`, lotes `E2E-MAN-153-*`, `L-GP-2026-01/06`, usuarios `test_*` | **Excluir del runtime real**; conservar en el entorno UAT actual |
| C · **Datos de UAT con valor de evidencia** | Lotes `L-GP-2026-07…13` (incl. **67 cerrado**), eventos 120–133, notificaciones | **Preservar como evidencia** (archivo del entorno UAT; nunca en runtime real) |
| D · **Referencias SAP sintéticas** | 39 códigos `PO-*/STO-*/MAT-*` | **Excluir del runtime real** (las creará el SAP real futuro o carga declarada) |
| E · **Credenciales/usuarios de prueba** | par UAT-09, `uat-rate-check`, usuarios seed | **Rotar/eliminar en el entorno real**; nunca reutilizar credenciales entre entornos |

## 3 · Estrategia recomendada (sujeta a GL-OD-07)

**Opción recomendada — instancia nueva para operación real**:
- La operación real arranca en una **base de datos nueva** (INF-01), con maestros reales + cutover real; el entorno actual (`avicola.globaldv.net`) permanece como UAT/archivo de evidencia del Pre-SAP.
- Ventajas: cero riesgo de contaminación, la evidencia del Pre-SAP queda intacta, sin borrados masivos.
- La limpieza entonces = **provisión limpia** (no borrado): checklist de "base vacía" verificada antes del cutover.

**Opción alternativa — limpieza en sitio del mismo entorno** (si el Owner decide reutilizarlo):
1. Backup completo verificado (GA_T13_BACKUP_POLICY) ANTES de cualquier acción.
2. Script de limpieza por lotes con orden FK, ejecutado en copia primero (dry-run con conteos).
3. Candidatos a eliminar: clases A–B–D–E completas; eventos/notificaciones asociados a fixtures.
4. **Preservar**: logs de auditoría requeridos por evidencia (exportar antes, si se decide), y toda la documentación/evidence del repo.
5. Re-seed con **maestros reales** únicamente; usuarios reales por administración de acceso.
6. Reconciliación post-limpieza: conteos en cero para clases excluidas; verificación 1×1 contra el plan.
7. **Autorización escrita del Owner** + ventana + rollback (restore del backup).

## 4 · Reglas duras

- **Nada se borra en esta fase** (mandato §5). Cualquier eliminación futura requiere: plan → backup verificado → autorización → ventana → ejecución → verificación → evidencia.
- Los datos de clase C no se destruyen: son evidencia de certificación (lote 67 y su ciclo completo).
- Los datos reales **jamás** pasan por este entorno compartido sin la custodia de §6 del plan de migración.
