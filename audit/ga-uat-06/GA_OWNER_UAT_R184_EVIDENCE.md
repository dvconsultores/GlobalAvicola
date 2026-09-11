# GA-UAT-06 · EVIDENCIA — R-184 (secciones A–G)

## A · PRECONDICIONES TÉCNICAS

| Elemento | Valor |
|---|---|
| Baseline | `main` · HEAD `dc3bbb8` == remoto · worktree limpio (preflight) |
| Producto backend | último commit de producto `3f88f94` (fix R-184) — **sin cambios desde la certificación** (0 commits a `backend/` o `frontend/` después) |
| Producto frontend | sin cambio desde GA-FE-07 (`index-BUthrUt9.js`) |
| Frontend bundle | `index-BUthrUt9.js` |
| Runtime | https://avicola.globaldv.net — frontend 200 · salud 200 · API 401 sin sesión (normal) |
| R-184 técnico | **CLOSED · FUNCTIONALLY_CERTIFIED** (evidencia en `audit/ga-r184/`) |
| Smoke de preparación | tsc **PASS** · build **PASS** · Vitest **280/280** · gate backend canónico **7 passed** |
| Producto modificado en este paquete | **NO** (solo documentos/capturas) |

## B · FIXTURES UAT

- Actor sintético **`uat6.ipe`** (usuario 132, rol 64 «Operador IPE UAT R-184»: inicio, lotes lectura, operaciones lectura, reportes lectura; **concesión Engorde efectiva**). Credenciales efímeras fuera del repositorio.
- Ventana operativa: cadena **Engorde (broiler)** habilitada durante la sesión.
- Lote primario: **L-BO-2026-05** (id 11, empresa 1) — fixture determinista certificado; IPE esperado **556.6**; clasificación visible **«Excelente»**.
- Segundo lote: NO usado (la UAT por defecto requiere un único fixture primario).
- Verificación de actor por API: lote 11 → 200; `IPE = 556.6` (edad 110).

## C · RECORRIDO DE REFERENCIA (no sustituye la aceptación)

Datos: `evidence/reference-walkthrough.json` · capturas C01–C06.

| Medida | Resultado |
|---|---|
| Detalle del lote carga | **PASS** |
| Tarjeta IPE visible con **556.6** | **PASS** |
| Clasificación **«Excelente»** visible | **PASS** |
| Sin experiencia 500 / tarjeta rota / estado fatal | **PASS** (sin «Internal Server Error») |
| NaN / Infinity en pantalla | **0 / 0** |
| Recarga dura: mismo valor y clasificación | **PASS** |
| Cierre de sesión + nuevo inicio: mismo lote y mismo valor | **PASS** |
| Reporte del lote (`/reports/lot/11`): carga e IPE coherente (556.6) | **PASS** |
| Consola desktop: errores totales / fatales | **0 / 0** |
| Móvil 390×844: IPE visible, clasificación legible, sin desborde, consola 0 | **PASS** |

## D · CASOS DEL PROPIETARIO

Resultados del propietario: **PASS en los 6 casos** (UAT-01…06) según la **decisión explícita A) ACEPTO R-184** (2026-09-11) — sin observaciones adicionales reportadas. Detalle por caso: `GA_OWNER_UAT_R184_OBSERVATIONS.md`. El resultado de referencia de ingeniería (arriba) documenta que la experiencia visible estaba lista para la sesión.

## E · OBSERVACIONES DEL PROPIETARIO

Registro completo (CERRADO): `GA_OWNER_UAT_R184_OBSERVATIONS.md`. Sin observaciones del propietario (decisión A sin comentarios adicionales). Notas de preparación pre-sesión registradas allí: R-186 fuera de alcance · observación de negocio separada · OBS-UAT-01 existente · BU-D10 no decidido aquí.

## F · DECISIÓN DEL PROPIETARIO

**A) ACEPTO R-184** — decidida explícitamente por el propietario el 2026-09-11 en la sesión GA-UAT-06. Registro: `GA_OWNER_ACCEPTANCE_R184_RECORD.md`.

## G · LIMPIEZA

**Ejecutada tras la decisión y verificada (§40)**: concesión Engorde de `uat6.ipe` **revocada** (200) · usuario 132 **baja lógica** (204) · rol 64 **desactivado** (200) · BU `broiler` restaurada **OFF** — catálogo verificado **4×OFF** (`breeder·broiler·grandparent·hatchery`) · **lote 11 y todo el histórico intactos** (uso solo-lectura) · credenciales `~/ga_uat06_credentials.txt` y temporales `/tmp/ga06_*` **destruidos** (verificado inexistentes) · sesiones de navegador cerradas (almacenamiento local limpiado; sin storageState versionado) · **auditoría preservada** · admin humano operativo · **ningún usuario humano modificado** · registros de aceptación GA-FE-02..07 y GA-UAT-04/05 intactos.
