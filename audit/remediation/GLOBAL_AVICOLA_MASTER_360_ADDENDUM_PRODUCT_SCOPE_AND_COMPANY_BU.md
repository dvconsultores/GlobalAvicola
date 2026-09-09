# ADDENDUM A LA AUDITORÍA MASTER 360 — ALCANCE PRODUCTIVO Y ACTIVACIÓN DE UNIDADES POR EMPRESA

**WAVE A0-P** · 2026-09-09 · base `7ee72a1` (Master 360 en `7ee72a1`, auditada sobre `7310adb`) ·
**sin código, sin migración, sin cambio de pruebas**

## 1. Por qué existe

La Master 360 (`MASTER_PROGRAM_STATUS_RECONCILIATION.md` y sus nueve matrices) **no se
reescribe**: es evidencia histórica de lo que se auditó y concluyó el 2026-09-09 sobre
`7310adb`. Este addendum existe porque el propietario declaró después dos requisitos que aquella
auditoría **no trató como tales**:

1. el producto vigente soporta **cuatro** unidades productivas completas, Progenitoras incluida;
2. **cada razón social** activa o desactiva cada unidad **dentro de Global Avícola**, con
   independencia del maestro de empresa de SAP.

Ambos quedan formalizados en `OD-16` y en `spec.md §4.0` (versión 1.1.0).

## 2. Qué omitió o subrayó poco la Master 360

| Tema | Cómo lo trató la Master 360 | Qué faltaba |
|---|---|---|
| Progenitoras como unidad productiva completa | la citó dentro de las «cuatro BU» y certificaciones `P-01`/`P-02`; no la auditó **superficie por superficie** ni distinguió sus huecos propios de los transversales | matriz propia → `PROGENITORAS_COVERAGE_MATRIX.md` |
| Activación de unidades por empresa | la consideró implementada (`GA-REM-040` fases 1-8) y anotó `BU 0/15` sin explicar qué mide | requisito de producto explícito (`OD-16`), matriz por unidad → `COMPANY_PRODUCTIVE_BUSINESS_UNIT_ACTIVATION_MATRIX.md`, lectura exacta de `0/15` |
| Empresa SAP ≠ configuración de unidades | trató `companies` como placeholder (`PL-05`) y conflicto `R-124` | la distinción de autoridad entre entidad oficial y configuración de producto (`OD-16.c`) |
| Frontend y unidades | `F01` (permisos en UI) | que la interfaz **no lee** la sesión de unidades: asume las cuatro (`H360A-01`) |
| `H360-A01` (atajos `is_super_admin`) | `P2 · PLAUSIBLE`, «verificar» | verificación exacta, hecha en la ola G: **confirmado** contra `OD-14.c` (`H360A-08`) |

## 3. Qué se auditó nuevamente

- Rastro completo de `grandparent` en specs, docs, modelo, rutas, servicios, esquemas, frontend, tests, KPI, semillas y evidencia de fases (`PROGENITORAS_COVERAGE_MATRIX.md`, 29 filas).
- Implementación real de `CompanyBusinessUnit` y `UserBusinessUnit`: tabla, FK, unicidad, `is_enabled`, auditoría (`audit_accion`), habilitar/deshabilitar, permisos, alcance de inquilino, transacción (`RutaTransaccional`), `API`, consumidor, resolutor, sesión y pruebas (`COMPANY_PRODUCTIVE_BUSINESS_UNIT_ACTIVATION_MATRIX.md`).
- Catálogo canónico: `business_units.code` ∈ {`grandparent`, `breeder`, `hatchery`, `broiler`}; `BirdTypeEnum` con los mismos cuatro valores; sin quinta unidad; sin variantes de nombre. Mapeo en `OD-16 §1`.
- Política por omisión: apagada sin fila (`GA-REM-040 §7.4`, `unidades_habilitadas`); ninguna semilla enciende nada; el alta real es `BU-D05`.
- Quién configura: `business_units:read/update` (Administrador de Accesos, Super Administrador); el reparto comercial/operativo es `BU-D07`, pendiente.
- Compatibilidad de la semántica certificada (empresa apagada prevalece · cero concesiones = nada · sin retroceso) con el requisito nuevo: **compatible sin cambios**.

## 4. Qué sigue vigente de la Master 360

Todo. Ninguna conclusión se revoca: los 10 entregables, el veredicto (`P0 = 0`), las 16 `AOD`, la
clasificación de `R-127`, `FASE 9 = BLOCKED` y la hoja de ruta por olas. Este addendum **añade**
y **precisa**; donde cambia un número lo dice en §7.

## 5. Hallazgos nuevos (`H360A-*`, provisionales; se reconcilian en la ola G)

| ID | Sev. | Requisito | Evidencia | Causa raíz | Consecuencia | ¿Solapa con backlog? |
|---|:--:|---|---|---|---|---|
| `H360A-01` | P2 | `GA-REM-040 §14.2-14.3`, `OD-16.b` | `navigationConfig.ts`, `processCatalog.ts`, `LotFormPage.tsx:18`, `DashboardPage.tsx` estáticos; `grep effective_business_units frontend/src` → 0 | la interfaz se escribió antes de la fase 8; la sesión ya entrega los cuatro conceptos | el menú muestra unidades apagadas o no concedidas; el backend deniega, la UX confunde | sí: fase 9 de `GA-REM-040` (no iniciada) |
| `H360A-02` | P2 | `docs/02 §3.4.1` (plan de importación) · `spec §4.4` | `grandparent_import` es un `OperationalEvent` genérico: `sap_document_ref`, `supplier_id`, `extra_data` libre; sin país, cantidades comprada/embarcada/recibida, mortalidad en traslado, cuarentena; adjuntos solo vía `evidences` sin tipología | el tipo se añadió al catálogo sin esquema propio | la importación no es validable ni conciliable con la OC internacional | no |
| `H360A-03` | P3 | `docs/02 §3.4.2` | ninguna rama crea un lote al completar la importación | no implementado | doble captura manual | no |
| `H360A-04` | P2 | `GA-REM-016` (evidencia por proceso) | `proceso-p01` no recorre transición de fase ni cierre; `P-01` certificó 12 pasos que terminan en `bird_exit` | alcance del E2E | `P-01` certificado sin evidencia de fase ni cierre | sí: `GA-REM-016 SPEC_DRAFT` |
| `H360A-05` | P2 | `OD-16`, `GA-REM-040` fases 10-11 | 0 E2E de configuración por empresa; `PROCESS_BUSINESS_UNIT_ACCESS_MATRIX` `0/15` | fases 10-11 no ejecutadas | requisito implementado y probado por integración, **no certificado como proceso** | sí: `GA-REM-040` |
| `H360A-06` | P1→ya registrado | `OD-16.c`, Recomendación §1/§4 | `companies` = entidad SAP + inquilino, sin código de sociedad | diseño inicial | conciliación futura imposible sin decisión | sí: `R-124` / `AOD-06` |
| `H360A-07` | P3 | `docs/03 §3.5` | `bird_type: enum (GRANDPARENT, BREEDER, BROILER)` — tres valores; el código tiene cuatro desde `d3f37f8` | deriva documental | lector engañado sobre el alcance | sí: grupo documental `H360-D*` |
| `H360A-08` | **P1** | `OD-14.c` («dato productivo: autoridad global sin contexto → cero filas; situada en `A` → solo `A`») | `operations/service.py:810` (`get_events`) y `:762` (`get_alerts`): `if not is_super_admin: filtrar por empresa` → el actor global **sin contexto ve los eventos y alertas de todas las empresas**; `lots/service.py:351` omite `verificar_pertenencia` para el actor global (escritura de saldo de apertura sobre lote ajeno); `:940/:949/:978/:997` (evidencias), `masters/curves.py:75`, `masters/router.py:137/:159` repiten el patrón. `GA_REM_040_PHASE_3_EVIDENCE.md:88` certificó la exención de unidad «exactamente donde queda fuera del de empresa», es decir, la semántica **anterior** a `OD-14` | `OD-14` se implementó en `users`, `roles` y `masters` (`771b402`) y no se propagó al dato productivo | incumplimiento de `OD-14.d` por el actor de mayor privilegio; sin escalada para actores de inquilino | sí: confirma `H360-A01` (era `P2 PLAUSIBLE`) |
| `H360A-09` | P2 | `BU-D07` | un solo permiso (`business_units:update`) en la empresa efectiva gobierna la habilitación; el reparto comercial/operativo no está decidido | decisión pendiente desde 2026-09-07 | sin consecuencia operativa hoy | sí: `BU-D07` (`PENDIENTE`) |
| `H360A-10` | P1→ya registrado | `Bases` p.2 | consumo de agua aplica a la cría de progenitoras | — | — | sí: `R-13` / `GA-REM-021` / `H360-B05` |

## 6. `BU-D10`

```
BU-D10   PENDING_RATIFICATION
PREGUNTA ¿Qué ocurre con las concesiones de usuario cuando una empresa deshabilita una unidad
         y más tarde la vuelve a habilitar?
   A     la concesión histórica vuelve a ser efectiva automáticamente   ← comportamiento
         provisional vigente (GA-REM-040 §6.3 · AC-A06 · test_deshabilitar_no_borra_las_concesiones_y_rehabilitar_las_devuelve)
   B     la concesión queda histórica/inactiva y hace falta una concesión explícita nueva
```

No existe `OD` ratificado. No se elige aquí; **ningún cambio de código depende de la elección**.
`OD-16.e` lo deja separado a propósito.

## 7. Impacto en la certificación y en la hoja de ruta (§88 del encargo)

| Pregunta | Respuesta |
|---|---|
| ¿La auditoría omitida de Progenitoras cambia alguna conclusión 360? | **No.** Añade dos huecos propios (`H360A-02` P2, `H360A-03` P3) y una carencia de evidencia (`H360A-04`). `P-01` y `P-02` siguen `CERTIFIED` con evidencia envejecida, como los demás. |
| ¿La activación por empresa cambia alguna conclusión 360? | **No.** Confirma que el requisito existe e está implementado; precisa que `0/15` es la dimensión de certificación de acceso, no una carencia funcional. Añade `H360A-01` (P2) y `H360A-05` (P2). |
| ¿Revelan un P0 nuevo? | **No.** |
| ¿Cambia el recuento de P1? | **Sí: 11 → 12.** `H360-A01` pasa de `P2 PLAUSIBLE` a **P1 confirmado** (`H360A-08`) por `OD-14.c`. Ningún P1 nuevo de Progenitoras ni de activación. |
| ¿Cambia la hoja de ruta? | Ajustes, no reordenación: `WAVE A` recibe `H360A-08` como tanda propia (exige spec + AC; fuera del alcance de esta ejecución); `WAVE B` recibe `H360A-02/03`; `WAVE E` absorbe `H360A-01` dentro de la fase 9; `WAVE F` recibe `H360A-04/05`. |
| ¿La certificación funcional 15/15 sigue siendo histórica? | **Sí.** Sin E2E re-ejecutada, nada se re-certifica ni se desclasifica. |
| ¿Cambia `BU 0/15`? | **No.** Sigue `0/15`; su cierre es la fase 10-11 de `GA-REM-040`. |

## 8. GO / NO-GO hacia la ola G (§37)

```
¿P0 nuevo que invalide el trabajo de WAVE A? ........ NO
¿Contradicción arquitectónica grave en la activación? NO   (modelo = OD-16, sin cambios)
¿P0 de seguridad/datos en Progenitoras? ............. NO
→ CONTINUAR con la reconciliación de gobierno (A0-G). Ningún hueco se arregla de paso.
```
