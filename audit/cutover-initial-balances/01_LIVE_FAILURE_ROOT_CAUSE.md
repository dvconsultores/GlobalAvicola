# CUTOVER-INITIAL-BALANCES · 01_LIVE_FAILURE_ROOT_CAUSE

Fecha: 2026-10-15 · SPEC 006 · Reproducción del fallo observado por el Owner en «Cargas Iniciales» (P-16 / T14)

---

## 1 · Procedencia del runtime

| Dato | Valor |
|---|---|
| Runtime compartido | `https://avicola.globaldv.net` (UAT) |
| HEAD remoto conocido | `57a421aabdf52db8de8140368a6a73479485f33f` |
| Marcadores verificados en el runtime | `GET /api/v1/sap/inbound/readiness` → 401 (ruta SPEC 005 presente); bundle del frontend con los textos del panel inbound de SPEC 005 |
| Conclusión | el runtime corre el código de `57a421a`: lo observado en vivo es reproducible en HEAD |

Las credenciales UAT disponibles (operador/aprobador de reproductoras) **no tienen** permisos `cutover:*`, por lo que la reproducción paso a paso se hizo sobre la pila local en `57a421a` (backend 8099 / frontend 5199, base de pruebas aislada) por la **UI real** con Playwright. Journal y capturas: `evidence/head-repro/`.

## 2 · Reproducción (HEAD `57a421a`)

| Paso | Acción por UI | Resultado | Evidencia |
|---|---|---|---|
| 0 | Abrir «Cargas Iniciales» | selector de BU por defecto en `broiler` aunque el usuario trabaje en otra BU | `journal.json#selector_por_defecto`, `01_pantalla_inicial.png` |
| 1 | Crear batch `breeder` con corte | 201, `status=draft` | `#crear_batch` |
| A1 | Descargar plantilla y subirla **sin rellenar** | **200 `validated`**, 0 filas: un archivo vacío queda listo para enviar | `#A1_upload_plantilla_vacia`, `02_A1_plantilla_vacia.png` |
| A2 | Rellenar como lo haría el negocio (fecha `01/08/2026`, `1.200` con separador de miles, granja por nombre) | `validating` con 3 errores (`INVALID_DATE`, `INVALID_NUMBER`, `MASTER_NOT_FOUND`) y **sin ningún toast ni explicación visible**; el usuario no sabe qué corregir | `#A2_validation`, `03_A2_errores_usuario.png` |
| A3 | Volver a subir el mismo archivo | silencio: el `<input type=file>` no se reinicia y el `onChange` no vuelve a disparar | `#A3_reupload_mismo_archivo_toasts` |
| B | Cambiar el selector a `hatchery` y pulsar «Descargar plantilla» con un batch `breeder` abierto | la descarga sigue el **selector**, no el batch; al subirla: **422 `BUSINESS_UNIT_MISMATCH`** | `#B_descarga_tras_cambiar_selector`, `#B_upload_plantilla_otra_BU`, `04_B_bu_mismatch.png` |
| C | Subir un CSV | **422 `INVALID_FILE: File is not a zip file`**; el input solo acepta `.xlsx` | `#C_upload_csv` |
| D | Recargar la página | el batch desaparece de la pantalla (no hay listado ni detalle por id) | `#D_tras_recargar_texto_vacio`, `05_D_recarga.png` |
| E | Carga «correcta» con la plantilla v1 | 200 `validated` con 1 fila | `#E_upload_ok`, `#E_items` |

## 3 · Causas raíz

| # | Causa | Dónde | Efecto en vivo |
|---|---|---|---|
| RC-1 | **Una sola plantilla genérica v1** (8 columnas de aves vivas por sexo) para las cuatro BU | `backend/app/cutover/templates.py` (`COLUMNAS_DATOS`), `parser.py` (`COLUMNAS_V1`) | incubadora y engorde no pueden describir su apertura (huevos, pollitos, mixto); el negocio «adapta» el archivo y falla |
| RC-2 | La descarga usa la BU del **selector** y no la del batch | `CargasInicialesPage.tsx` (`handleDownloadTemplate(businessUnit)`) | plantilla de otra BU → `BUSINESS_UNIT_MISMATCH` sin pista de cómo evitarlo |
| RC-3 | `N/A` y vacío colapsan a `None`; `N/A` en una columna requerida se acepta | `parser.py` (`normalizado[campo] = None` en ambos casos; `live_males=N/A` pasa) y `service._construir_opening` (`or 0`) | pérdida de la distinción UNKNOWN/N/A y fabricación de `0` en el opening |
| RC-4 | Un archivo sin filas queda `validated` | `service.subir_y_validar` (`invalidas == 0`) | el usuario cree que cargó; `submit` devuelve 409 sin explicar |
| RC-5 | Sin persistencia visible del batch: no hay `GET /cutover-batches` ni `GET /cutover-batches/{id}` | `router.py` | recargar la página «pierde» el trabajo |
| RC-6 | Solo XLSX; CSV rechazado como «no es zip» | `parser.parse_cutover_workbook`, `accept=".xlsx"` | el error no dice «use .xlsx o descargue la plantilla» |
| RC-7 | Errores de validación sin mensaje visible ni descarga | página: tabla sin columna `message`, sin toast en 200 con errores | el usuario no sabe qué corregir |
| RC-8 | Apply ancla todo lote a la **primera fase activa** (global) y no crea `LotPhase`, galpón, línea genética ni raza | `service._resolver_fase`, `_crear_o_reusar_lote` | lotes migrados sin fase real ni ubicación; continuidad operativa incompleta |
| RC-9 | Sin guarda de fecha de corte en el motor (CUT-GL-02) | `operations/validators.validate_event_date` | eventos con fecha ≤ corte se aceptan y duplican lo histórico |
| RC-10 | Saldos de huevos/pollitos no leen el opening | `validators.get_egg_balance`, `get_hatchery_egg_balance`, `get_viable_chick_balance` | un lote de incubadora migrado nace con saldo 0: `BR-02/03/04` bloquean la primera operación |
| RC-11 | Continuidad post-corte certificada solo para `broiler` | `e2e/proceso-p16-cutover-cargas-iniciales.spec.ts` | el gate «primera operación después del corte» no existe para GP/Breeder/Hatchery |

## 4 · Clasificación

```text
LIVE_FAILURE_REPRODUCED      = YES (HEAD 57a421a, por UI)
ROOT_CAUSE                   = DESIGN (una plantilla genérica + UX sin guía) y DOMAIN (apertura incompleta por BU)
REGRESSION_OF_GA_REQ_061     = NO (el contrato v1 se comporta como fue certificado; el contrato era insuficiente)
REMEDIATION                  = SPEC 006 (specs/006-cutover-initial-balances-remediation)
```
