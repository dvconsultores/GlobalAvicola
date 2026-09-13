# GA-CLAUDE · MATRIZ E2E DE PROCESOS — CERTIFICACIÓN PASO A PASO (§27 · §53)

Auditoría independiente Claude · 2026-09-13 · HEAD `c0b4afc` · Complementa `GA_CLAUDE_PROCESS_INVENTORY.md` (inventario y estados) con la **prueba por dimensiones** exigida por §27: setup · inicio por UI · ejecución backend · persistencia · reglas · transiciones · aprobación · handoff · estado final · auditoría · reporte/salida · autorización negativa · runtime actual.

**Leyenda de dimensiones**: `✔` probado por UI en runtime/local con evidencia · `~` probado parcialmente o por API · `✘` no probado / roto · `n/a` no aplica. Fuentes: `runtime-gp-e2e.json` (RT), `ui-e2e-local-pass1/2.json` (L1/L2), `playwright_e2e.log` (PW), informes A–F.

## 1 · Matriz por proceso

| Proceso | Setup | Inicio UI | Backend | Persist. | Reglas | Transic. | Aprobac. | Handoff | Estado final | Auditoría | Reporte | Neg. auth | Runtime | **Estado** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **P-01 Progenitoras cría** | ✔ (lote/import RT) | ✔ import/recepción | ✔ | ✔ | ✘ BR-08 en distribución/salida (R-190) | ✓ submit/return/approve (RT) | ✔ RT | n/a | ✘ cadena no completa | ~ (duplicada P1-12) | ~ (KPI) | ✔ 400/403 RT | ✘ | **BROKEN** |
| **P-02 Progenitoras producción** | ~ | ✘ transición 422 (R-191) | ✔ | ~ | ✘ egg_collection BR-08 (R-190) | ~ | ✔ | n/a | ✘ | ~ | ~ | ✔ | ✘ | **BROKEN** |
| **P-03 Reproductoras cría** | ✔ (L2 lote+galpón) | ✘ recepción hub 400 BR-20 (R-205) | ✔ | ✔ (por vía alterna) | ~ BR-17 (R-211), peso (R-210) | ✓ (L2) | ~ (rol semilla) | n/a | ✘ | ~ | ~ | ✔ | ✘ (PW rojo) | **BROKEN** |
| **P-04 Reproductoras huevo fértil** | ✔ | ✘ transición 422 (R-191) | ✔ | ✔ (L2 egg_dispatch) | ✔ BR-02 4xx seguro (L2) | ~ | ~ | ~ (egg_dispatch 201 L2) | ✘ | ~ | ~ | ✔ | ✘ | **BROKEN** |
| **P-05 Incubación** | ✔ (L2 lote) | ✘ recepción 422/400 (R-194) | ~ (sondas 201) | ✘ saldo 0 (R-194) | ✘ BR-03/BR-08/BR-21 | ✘ carga/nacimiento | ✘ | ✘ | ✘ | ~ | ✘ KPI | ✔ | ✘ (PW rojo) | **BROKEN** |
| **P-06 Pollo de engorde** | ✔ (L1/L2) | ✔ ×11 eventos (L1/L2) | ✔ | ✔ | ✔ R7/BR-05 (400 claro) | ✘ cierre tras reverso (R-192) | ~ aprobación por API (L2) | n/a | ~ cierre UI 200 (L2) | ~ (P1-12) | ✔ IPE/reporte (L2) | ✔ | ✘ no en RT | **PARTIAL** |
| **P-07 Revisión→corrección→aprobación** | ✔ | ✔ (RT 3 identidades) | ✔ | ✔ | ✔ BR-14 403 (RT) | ~ in_review huérfano (R-197) | ✔ | n/a | ~ | ✘ in_review invisible | n/a | ✔ | ~ | **PARTIAL** |
| **P-08 SAP** | — | — | ~ API interna | ~ | ~ | ~ | n/a | — | — | ✘ transiciones sin auditar | n/a | n/a | ✘ | **OUT_OF_SCOPE** (§56; ver matriz SAP) |
| **P-09 Auditoría** | ✔ | ✔ `/audit` carga (L2) | ✔ GET 200 (L2) | ✔ | ✘ duplicados (P1-12) | n/a | n/a | n/a | ~ | ✘ | n/a | ✔ | ~ | **PARTIAL** |
| **P-10 Trazabilidad** | ~ | ✘ (productores de vínculos roto: R-194) | ✔ tests contrato (13+4) | ~ | ✔ | n/a | n/a | ✘ | ✘ | ~ | ✘ | n/a | ✘ | **UNKNOWN** |
| **P-11 Activación manual** | ~ | ✘ sin UI (P1-15) | ✔ API | ✔ | ~ R-69/R-70 abiertos | n/a | n/a | n/a | ~ | ✘ sin auditar (E-10) | n/a | ~ | ✘ | **BACKEND_ONLY** |
| **P-12 Maestros** | ✔ | ✘ creación estructural (R-196) | ✔ API | ✔ | ~ OD-21 área (L2) | n/a | n/a | n/a | ✘ | ✔ CRUD auditado | n/a | ~ | ✘ | **BROKEN** |
| **P-13 Auth/usuarios** | ✔ | ✘ edición (R-195) | ✔ | ✔ | ✘ R-199/R-200 (seguridad) | n/a | n/a | n/a | ~ | ~ (E-13 usuarios sin auditar) | n/a | ✔ | ~ | **BROKEN** |
| **P-14 Notificaciones** | ✔ | ✔ campana (RT unread 1) | ✔ | ✔ | ~ E-06 SLA | n/a | n/a | n/a | ~ tipos sin re-ejercitar | ~ | n/a | ✔ | ~ | **PARTIAL** |
| **P-15 Reportes/KPI** | ✔ | ✔ `/reports` carga (L2) | ✔ | ✔ | ✘ R-204 (unidad), R-214 (doble conteo) | n/a | n/a | n/a | ~ IPE 200 (L2) | n/a | ✔ informe (L2) | ✔ 403 claro pendiente (R-212) | ~ | **PARTIAL** |
| **OD-19 Reverso** | ✔ (L1/L2 API) | ✘ sin UI (R-207) | ✔ | ✔ | ✘ R-192/R-193 | ~ | ✔ (contrapartida aprobada L2) | n/a | ✔ ambos `reversed` (L2) | ~ duplicada | n/a | ✔ | ✘ | **BACKEND_ONLY** |
| **OD-25 Lote al aprobar** | ✔ | ✔ import (RT) | ✔ | ✔ | ✔ BR-01 exacta (RT 50/51) | ✔ | ✔ pendiente propietario | ~ recepción 201 | ~ | ~ | ✘ cadena posterior (R-190) | ✔ | ✔ | **UAT_PENDING** |
| **X-BU Traspaso** | ✔ | ✘ recepción/destino (R-194) | ~ tests contrato | ~ | ✔ validar_flujo | ✘ | ~ | ✘ | ✘ | ~ | n/a | ✔ | ✘ | **BROKEN** |

## 2 · Respuesta §62/§63 por unidad (resumen; detalle en `GA_CLAUDE_PROCESS_INVENTORY.md §4`)

| BU | ¿Completable por UI sin rodeos? | Ruptura exacta | Spec |
|---|---|---|---|
| Progenitoras | **NO** | ubicación BR-08 (R-190); transición (R-191); fecha opcional (R-206) | R-190/R-191/R-206 |
| Reproductoras | **NO** | cuadre BR-20 (R-205); transición (R-191); peso (R-210); BR-17 (R-211) | R-205/R-191/R-210/R-211 |
| Incubadora | **NO** | recepción (R-194: BR-08/arrival_date/fértiles); nacimiento silencioso; despacho | R-194 |
| Engorde | **NO DEMOSTRADO** | aprobación por UI con rol semilla; cierre tras reverso (R-192); referencia OC (R-209) | R-192/R-209 |
| Cadena completa (traspaso) | **NO** | incubadora origen/destino (R-194) | R-194/X-BU |

## 3 · Puerta §53

```
Procesos pre-SAP (17: P-01…P-15 + OD-19 + OD-25 + X-BU)
FUNCTIONALLY_CERTIFIED_E2E ...... 0
PARTIAL ......................... 5   (P-06 · P-07 · P-09 · P-14 · P-15)
BROKEN .......................... 8   (P-01 · P-02 · P-03 · P-04 · P-05 · P-12 · P-13 · X-BU)
BACKEND_ONLY .................... 2   (P-11 · OD-19)
UAT_PENDING ..................... 1   (OD-25)
UNKNOWN ......................... 1   (P-10)
OUT_OF_SCOPE (legítimo, §56) .... 1   (P-08)
→ Ningún proceso supera la puerta §53 en HEAD.
```

Habilitadores de recertificación: **GA-GOV-03** (suite verde + CI) y el cierre de los paquetes de proceso (R-190/191/194/205 + integridad + UAT). La recertificación completa (tranche 9 de la cola) produce los artefactos de ejecución que hoy no existen.
