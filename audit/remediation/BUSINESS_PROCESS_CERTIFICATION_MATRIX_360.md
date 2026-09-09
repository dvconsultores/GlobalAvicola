# MATRIZ DE CERTIFICACIÓN POR PROCESO DE NEGOCIO — 360°

**Auditoría 360°** · 2026-09-09 · base `7310adb` · **AUDIT ONLY**

Regla del encargo y `constitution.md` Principio IV: **la unidad de certificación es el proceso
de negocio**; no se certifica por endpoint, por fase ni por transitividad, y **no se
re-certifica por inferencia**. Esta matriz **no** cambia ningún estado: reproduce el estado
registrado, fecha su evidencia y anota qué ha cambiado desde entonces y qué hallazgos 360 lo
afectan. Un proceso sigue `CERTIFIED` hasta que una prueba lo contradiga; pero su evidencia
puede estar **envejecida**, y eso sí se declara.

Hechos que aplican a **todos** los procesos:

- Última ejecución E2E registrada en `audit/remediation/`: **2026-09-06** (`PROCESS-14-CERTIFICATION.md:305`, 129 passed / 17 suites; `PROCESS-03-CERTIFICATION.md:265`, 124 passed). Desde entonces: **85 commits** (`git log --since=2026-09-06`), que tocaron `auth/service.py`, `masters/service.py`, `review/*`, `business_units/*`, semillas, `UsersPage` y `App.tsx`.
- Suites ejecutadas **hoy**: backend `784 passed · 49 skipped` (`run_tests.sh -rs`, 487 s); frontend `87 passed / 8 archivos` (vitest). **E2E no ejecutada** en esta auditoría (requiere backend en `127.0.0.1:8099` y credenciales del entorno; el encargo prohíbe montar nada nuevo).
- Certificación de acceso por unidad (`PROCESS_BUSINESS_UNIT_ACCESS_MATRIX.md`): **`PENDIENTE` en los 15** — pertenece a la fase 10/11 de `GA-REM-040`.

---

## 1. Matriz

| Proceso | Estado registrado | Evidencia (doc · fecha · clase) | Cambios posteriores que lo tocan | Hallazgos 360 que lo afectan | Acceso BU | SAP | Vigencia 360 |
|---|:--:|---|---|---|:--:|:--:|---|
| `P-01` Progenitoras — cría | `CERTIFIED` | `PROCESS-01`, `GA-REM-035` · 2026-09-06 · `API_E2E` | tenencia (`OD-13/14`), maestros | `H360-P01` (descarte/salida sin saldo) · `K01/K02` · `B05` agua · `B01/B02` recepción · verificación `grandparent_import` fuera de `in_types` | PEND. | n/a | **envejecida** |
| `P-02` Progenitoras — producción | `CERTIFIED` | `PROCESS-02` · 2026-09-05 · `API_E2E` (9) | ídem | `K10` (huevo: infértiles/descartados/peso/alimento por huevo ausentes) · `AOD-10` fertilidad | PEND. | n/a | envejecida |
| `P-03` Reproductoras — cría | `CERTIFIED` (addendum B) | `PROCESS-03` · 2026-09-06 · `API_E2E` + `UI` curvas | ídem | `P01` · `K01/K02/K08` · `B05` · `B07` umbrales fijos | PEND. | n/a | envejecida |
| `P-04` Reproductoras — huevo fértil | `CERTIFIED` | `PROCESS-04` · 2026-09-05 · `API_E2E` (9) | ídem | `K10` eficiencia de traslado de huevos ausente · `AOD-10` | PEND. | n/a | envejecida |
| `P-05` Incubación | `CERTIFIED` | `PROCESS-05` · 2026-09-05 · `API_E2E` (8) | ídem | `K03` (vacunación cuenta eventos, P1) · `K11` · `B13` sanos/débiles · `B12` capacidad incubadora no validada | PEND. | n/a | envejecida |
| `P-06` Pollo de engorde | `CERTIFIED` (tras `R-76`) | `PROCESS-06`, `GA-REM-029/036` · 2026-09-06 · `API_E2E` (5) | ídem | **`P01`** (`bird_exit` sin saldo) · `K01` FCR · `K06` AFCR · `K02` · `K07` · `P08` cierre sin FCR · `AOD-08` | PEND. | ver `P-08` | envejecida · **KPI del proceso no conformes a `Bases`** |
| `P-07` Revisión → corrección → aprobación | `CERTIFIED` | `PROCESS_CERTIFICATION_MATRIX.md:45` · 2026-09-05 · `proceso-03` `API_E2E` (7) | **`review/service.py`** (segregación, ámbito de unidad), `OD-14` (3 tests certificados reescritos con `switch-company`) | `P03` (`RETURNED`/`REJECTED`) · `P06` (`CORRECTED` doble semántica) · `P10` (`docs/12 R2`) · `P04` cancel | PEND. | — | **envejecida, con cambios directos en su código sin E2E posterior** |
| `P-08` Consolidación SAP | `PARTIAL` · `BLOCKED_EXTERNAL` | — | **no tocado** (instrucción) | `SAP_INTEGRATION_READINESS_AUDIT.md` (informativo) | PEND. | `NOT READY` | sin cambio |
| `P-09` Auditoría interna | `CERTIFIED` (`R-83` abierto) | `PROCESS-09`, `GA-REM-032` · 2026-09-06 | listeners sin cambio | `D04` inmutabilidad solo de aplicación · `P11` `version` | PEND. | — | envejecida |
| `P-10` Trazabilidad generacional | `CERTIFIED` | `PROCESS-10`, `GA-REM-030/031` · 2026-09-05 | `OD-14` | ninguno nuevo | PEND. | — | envejecida |
| `P-11` Activación manual | `CERTIFIED` | `PROCESS-11` · 2026-09-05 · `API_E2E` (6) | — | `K02` (es el **único** camino que alimenta `OpeningBalance`) | PEND. | — | envejecida |
| `P-12` Datos maestros | `CERTIFIED` | `PROCESS-12`, `GA-REM-033` · 2026-09-06 | **`masters/service.py`** (`R-115/116`, `OD-14`, `CONTROL_GLOBAL`) | **`R-127`** (`/masters/companies` 500 con `sap_config`) · `S01/S03/S05` placeholders sin clave · `R-124` | PEND. | placeholders | **envejecida, con cambios directos y un defecto abierto en su superficie** |
| `P-13` Usuarios y roles | `CERTIFIED` | `PROCESS-13`, `GA-REM-034` · 2026-09-06 | **`auth/service.py`** entero (`R-114…R-118`, `OD-13`, `OD-15`), `UsersPage`, 7.º rol | `F01` (`R-98/R-119`) · `R-122` · `R-123` · `A01` atajos `is_super_admin` | n/a | — | **envejecida, con reescritura de su servicio; cubierta por 80+ tests de integración nuevos, no por E2E** |
| `P-14` Notificaciones | `CERTIFIED` (6/6) | `PROCESS-14` addendum B · 2026-09-06 | `_usuario` de sus tests corregido (`OD-14`) | ninguno nuevo | PEND. | — | envejecida |
| `P-15` Reportes e indicadores | `CERTIFIED` | `PROCESS-15`, `GA-REM-022` enm. A · 2026-09-06 | `reports/service.py` ámbito de unidad | **`K01`, `K02`, `K03`, `K06`** (P1) · `K04/K05/K07/K11/K13` · `K10` 12 ausentes | PEND. | — | **envejecida · certificó la cadena, no las fórmulas → no conforme a `Bases`** |

## 2. Lectura

```
CERTIFIED (registrado) .......... 14     PARTIAL/BLOCKED ...... 1 (P-08)
con evidencia E2E ≤ 2026-09-06 .. 15/15  E2E re-ejecutada hoy . 0/15
con código del proceso tocado
  después de la evidencia ....... P-07 · P-12 · P-13 (directo) · todos (transversal: tenencia)
con hallazgo 360 P1 dentro ...... P-01 · P-03 · P-05 · P-06 · P-07 · P-12 · P-13 · P-15
certificación de acceso BU ...... 0/15
```

Ningún proceso se **desclasifica** aquí: no hay prueba fallida. Pero la afirmación «15 procesos
certificados» ya no describe el sistema en `7310adb` sin dos calificativos: *con evidencia de
hace 85 commits* y *sin conformidad de fórmulas ni de invariante de población*.

## 3. Qué haría falta para una certificación 360 (WAVE F)

1. Re-ejecutar las 17 suites E2E contra `main` y registrar el resultado con commit y fecha (`GA-REM-016` debe salir de `SPEC_DRAFT` para ampararlo).
2. Añadir a cada `PROCESS-xx` una sección **«Conformidad con la fuente del cliente»** (fórmulas, datos diarios, reglas §17) distinta de la cadena técnica.
3. Cerrar `H360-P01` y `K01/K02/K03/K06` antes de re-certificar `P-06` y `P-15`.
4. Certificar acceso por unidad (fases 10-11 de `GA-REM-040`) por proceso, no por ruta.
5. `P-08` permanece `BLOCKED_EXTERNAL` hasta `GA-REM-017`; su certificación exige SAP real (WAVE G).
