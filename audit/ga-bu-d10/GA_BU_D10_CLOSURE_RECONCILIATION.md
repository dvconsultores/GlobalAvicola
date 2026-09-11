# GA-BU-D10 · RECONCILIACIÓN DE CIERRE (AC01-AC25 → evidencia)

Fecha: 2026-09-11 · Commits: C2 `0542310` · C3 `bee33f5` · C3b `399751c` · Evidencia `evidence/`.

## 1 · Respuestas explícitas (§68)

| Pregunta | Respuesta |
|---|---|
| Owner choice | **B** |
| Current policy implemented | **YES** |
| Company BU OFF absolute | **PASS** (E2E-02/11 incl. global) |
| Re-enable behavior | **PASS (B: sin efectividad automática; regrant la restaura)** |
| User grant distinction | **PASS** (apagar termina; conceder no habilita; habilitar no concede) |
| RBAC | **PASS** (E2E-09) |
| Access Administrator | **PASS** (control-plane; sin productivo propio; grant a otro OK; self 403) |
| global + BU OFF | **PASS** (404) |
| Company transfer | **PRESERVED** (suites AC-B08/B12; sin API viva de transferencia — declarado) |
| Session stale access | **NONE** (E2E-06: OFF⇒DENY inmediato; ON⇒sigue DENY; regrant⇒ALLOW) |
| Audit | **PASS** (23 eventos; 9 terminaciones con causa) |
| Historical grants | **PASS** (6+1 filas; nada borrado) |
| Tenant isolation | **PASS** (cross 404; sin fuga) |
| Residual | Externo: roles duplicados inactivos documentados en ledger · datos: estados OFF previos normalizados por el próximo apagado (sin reclasificación retroactiva, por diseño) |

## 2 · AC01-AC25

| AC | Estado | Evidencia |
|---|---|---|
| AC01 OD-23 canonizada | **PASS** | `GA_OD_BU_D10_OWNER_DECISION.md` |
| AC02 BU OFF sin acceso | **PASS** | E2E-02/11 |
| AC03 global no evade | **PASS** | E2E-11 (404) |
| AC04 concesión ≠ habilitación | **PASS** | E2E-08 (409 con OFF) + E2E-05 (habilitar no concede) |
| AC05 re-encendido sin automática | **PASS** | E2E-04 (404) · U3 (IPO ausente) |
| AC06 zero-BU CORE | **PASS** | E2E-10 |
| AC07 RBAC | **PASS** | E2E-09 (403) |
| AC08 cross-company | **PASS** | E2E-08 (404) |
| AC09 self-grant | **PASS** | E2E-07 (403) |
| AC10 transferencia | **PASS** | suites CI (preservadas; sin cambio) |
| AC11 /me | **PASS** | E2E-02/04 (`effective/granted` coherentes) |
| AC12 navegación | **PASS** | U1-U4 (nav `/lots` 1/0/0/1) |
| AC13 API directa = UI | **PASS** | E2E (API) + U (UI) mismo estado |
| AC14 refresh token | **PASS** | E2E-06 (sin acceso obsoleto) |
| AC15 relogin | **PASS** | E2E-12 |
| AC16 auditoría | **PASS** | E2E-13 |
| AC17 sin fuga | **PASS** | negativos sin cuerpo |
| AC18-21 GA-FE-02..07 | **PASS (spot)** | U6 · nav · Vitest 280/280 |
| AC22 R-181..187/OD-21/22 | **PASS** | sin superficies tocadas; IPE 333.3 observado |
| AC23 históricas consultables | **PASS** | E2E-14 (6 terminadas visibles con fecha) |
| AC24 idempotencia normalizadora | **PASS** | E2E-02b + suite |
| AC25 sin migración/borrado masivo | **PASS** | diff (0 migraciones; 0 deletes) |

## 3 · Veredicto

**Todos los críticos PASS ⇒ R-188: CLOSED (técnico), FUNCTIONALLY_CERTIFIED · OD-23: RATIFIED_IMPLEMENTED.**
**Owner UAT: REQUIRED** (comportamiento visible de acceso cambia) · **READY**: guía `GA_BU_D10_OWNER_UAT.md` · acceptance **PENDING** (no auto-aprobada).
