# GA-BU-D10 · EVIDENCIA RUNTIME AUTENTICADA (R-188 · OD-23 B)

Entorno: `https://avicola.globaldv.net` (empresa 1) · Fecha: 2026-09-11.
Generación congelada: backend **C3 `bee33f5` + C3b `399751c`** desplegado (detectado por comportamiento: el apagado marca concesiones — primera marca `19:33:10Z`) · Bundle `index-BUthrUt9.js` (sin cambio).
Raw: `evidence/runtime-api.json` · `runtime-ui.json` · `cleanup.json`.

## 1 · Ciclo completo (API autenticada; actores sintéticos bu188*)

| Caso | Pasos | Resultado |
|---|---|---|
| E2E-01 (L1/S4) | BU ON + concesión viva + RBAC | lots 200 · **ipe 200** · `/me` efectivas `[broiler]` ⇒ **ALLOW** |
| E2E-02 (L2/S1) | Apagar ⇒ **termina** concesiones | ipe **404** · `/me` efectivas `[]` y **concedidas `[]`** · filas con `revoked_at` (historia escrita) ⇒ **DENY** |
| E2E-02b (AC24) | Apagado repetido (idempotente/normalizador) | 200 · sin duplicados ni eventos extra |
| E2E-04 (L5/L6) | Re-encender (**B**) | lots 200 con **0 lotes** · ipe **404** · `/me` `[]` ⇒ **ningún histórico vuelve** |
| E2E-05 (L7/S8) | Access Admin concede de nuevo | grant **201** (actor control-plane; `me []`, ipe propio **403**) ⇒ OP: lots 200 · **ipe 200** |
| E2E-06 (L15/L16/S-nueva) | Sesión activa: OFF ⇒ DENY inmediato · ON ⇒ **sigue 404** · regrant ⇒ 200 | **sin privilegio obsoleto** |
| E2E-07 (L13/S9) | Self-grant del Access Admin | **403** |
| E2E-08 (L14/S10) | Conceder con unidad OFF ⇒ **409** · cross-company ⇒ **404** | GOBIERNO PRESERVADO |
| E2E-09 (L8/S3) | Concesión viva + BU ON + **sin `reports:read`** | lots 200 · ipe **403** ⇒ RBAC exigido |
| E2E-10 (L10/S6) | Zero-BU | lots 200 con **0 lotes** · `/me` `[]` ⇒ CORE sin dato productivo |
| E2E-11 (L3/S5) | **Global + BU OFF ⇒ 404** · BU ON ⇒ 200 (exención de concesión, no de habilitación) | OD-16 ABSOLUTO |
| E2E-12 (AC15) | Relogin (token nuevo) | ipe 200 ⇒ estable |
| E2E-13 (AC16) | Auditoría | `GET /audit` 200 · **23 eventos** `user_business_unit` · **9 terminaciones con causa** `company_business_unit_disabled` (una por concesión y ciclo) |
| E2E-14 (AC23) | Persistencia | Concesiones de OP: **6 terminadas + 1 viva** ⇒ historia completa, sin borrado |

Sin `5xx` en toda la batería (0 × HTTP 500).

## 2 · UI (Playwright; screenshots en `evidence/`)

| Caso | Resultado |
|---|---|
| U1 (ON+concesión) | Tarjeta **IPE 333.3** visible · nav `/lots` presente · sin error crudo · `U1-ON-detalle-54.png` |
| U2 (OFF) | IPE **ausente** · **nav `/lots` ausente** · sin error crudo · `U2-OFF-denegado.png` |
| U3 (re-encender · B) | IPE **sigue ausente** · nav **sigue ausente** · `U3-reenable-sin-acceso.png` |
| U4 (concesión nueva) | IPE **restaurada** · nav presente · `U4-regrant-acceso.png` |
| U5 (móvil 390×844) | IPE 333.3 · `overflow 0` · sin error · `U5-movil-ON.png` |
| U6 (Access Admin · `/admin/unit-access`) | Página operativa: «Engorde **Activa**» + «Desactivar»; el actor administra **sin** acceso productivo propio · `U6-unit-access-adm.png` |

0 errores fatales de página; sin texto crudo de backend.

## 3 · Matriz de seguridad S1-S12

S1✔ (E2E-02) · S2✔ (E2E-04) · S3✔ (E2E-09) · S4✔ (E2E-01/05) · S5✔ (E2E-11) · S6✔ (E2E-10) · S7✔ (E2E-05: admin control-plane sin productivo) · S8✔ (E2E-05) · S9✔ (E2E-07) · S10✔ (E2E-08) · S11✔ (transferencia: suites AC-B08/B12 preservadas en CI; **sin API viva que transfiera de empresa** — declarado en el código; no afectada por R-188) · S12✔ (**B**: no revive; regrant 201 la restaura).

## 4 · Regresiones

- **R-187 / OD-22 intactos**: tarjeta IPE **333.3** observada en U1/U4/U5 (G-06 sin cambios; 200s).
- **R-186/G-05 · R-184 · R-185/OD-21**: sin superficies tocadas por el diff (backend solo `business_units/*`); sin regresión observable.
- **GA-FE-02/03/04 spot**: unit-access (U6) + navegación por acceso efectivo (U1-U4 nav) + RBAC (E2E-09). **GA-FE-05/06/07**: sin diff en sus superficies (Vitest 280/280).
- **OD-16**: absoluto verificado (E2E-11).

## 5 · Limpieza (ver `evidence/cleanup.json`)

Concesión viva revocada (200) · 4 usuarios baja lógica (204) · **20 roles `BU188*` desactivados** (4 útiles + 16 duplicados creados por re-ejecuciones del script — todos inactivos) · **BU broiler OFF restaurada (4×OFF)** · admin operativo. Fixtures de lotes 54-59 intactos (solo lectura). Humanos: no modificados.
