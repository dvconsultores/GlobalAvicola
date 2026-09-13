# R-205 · DISEÑO DE PRUEBAS RED · E2E RUNTIME · UAT

HEAD `c0b4afc` · Sin implementación en este documento.

## 1 · Diseño RED

### 1.1 `frontend/src/pages/operations/__tests__/r205.stageDerivation.test.ts` (unit puro)

Importa `resolverStageDelAsistente` de `../operationPayload` (HEAD: **no existe** ⇒ rojo válido). Tabla `it.each`: (`search` con `?stage=`, lote {bird_type,fase activa}, tipo de evento) ⇒ `stage` esperado; cubre: `?stage=production` manda; lote breeder en cría ⇒ `breeder_rearing`; lote broiler ⇒ `broiler`; sin contexto ⇒ `null` (paso 1).

### 1.2 `__tests__/r205.breederReceptionParity.test.tsx` (jsdom, camino real)

Arnés de `f01e.receptionHouse.test.tsx`. Fixtures: `LOTE_BREEDER = {id:1, bird_type:'breeder', status:'active', …}`, `LOTE_BROILER`, catálogos mínimos.

| Nombre exacto del `it` | Pasos | Aserción que **falla en HEAD** |
|---|---|---|
| `AC-R205-01 · recepción por hub con lote breeder ⇒ cuadre visible y payload completo` | `initialEntries=['/operations/new?type=bird_reception&lot_id=1']`; elegir lote; guardar con cuadre | `screen.getByText(/recibidas/i)` visible y `payload.received_total` presente — HEAD: sin campo y POST sin cuadre |
| `AC-R205-02 · recepción desde detalle de lote ⇒ paridad` | misma entrada con acción del detalle | ídem |
| `AC-R205-05 · cuadre incompleto ⇒ sin POST + mensaje` | dejar `received_total` vacío | `post` no llamado y mensaje visible — HEAD: POST viaja (400) |
| `AC-R205-03 · URL directa ⇒ control` | sin `?type=` (paso 1→2) | cuadre y 201 (verde) |
| `AC-R205-04 · lote broiler ⇒ sin cuadre` | lote broiler | sin campos de cuadre (verde) |

### 1.3 Control backend

`backend/tests/test_r26_error_contract.py::…BR-20` (ya existe): API sin los campos ⇒ 400 (verde en HEAD; guarda de no-regresión del validador).

Ejecución: `npx vitest run src/pages/operations/__tests__/r205.*` ⇒ rojos exactos; salida a `evidence/red/`.

## 2 · Diseño E2E runtime (C3)

Entorno nube (`avicola.globaldv.net`) con generación C2. Actores UAT-09 (operador breeder si existe; si no, crear lote breeder con la UI y usar operador con unidad `breeder`). Runner: extensión de `scripts_e2e_f01_retry.mjs` (intercepta `POST /operations` y guarda payload/respuesta).

| Caso | Actor | Pasos | Esperado | Limpieza |
|---|---|---|---|---|
| E2E-R205-01 | operador | hub → Reproductoras cría → «Recepción de aves» → lote breeder → cuadre (recibidas 100/DOA 2/rechazadas 3/avícolas 95) → guardar | 201; payload con los 3 campos; toast | evento queda `registered`; anular al final |
| E2E-R205-01m | operador | ídem 390×844 | 201; sin overflow | ídem |
| E2E-R205-02 | operador | desde detalle de lote | 201 | ídem |
| E2E-R205-03 | operador | URL directa (paso 1) | 201 (control) | ídem |
| E2E-R205-04 | operador | lote broiler + `bird_reception` | 201 sin cuadre (control) | ídem |
| E2E-R205-05 | operador | cuadre incompleto | sin petición; mensaje | — |
| E2E-R205-06 | sonda API | `POST` sin campos | 400 BR-20 | — |

Invariantes: `pageerror` = 0; `5xx` = 0; población del lote intacta tras anulaciones (control GET). Artefactos: `evidence/runtime-c3/journal.json`, `R205-0x.png`, `payloads/*.json`, `sonda-br20.json`. Verificación cruzada: re-ejecutar (tras GA-GOV-03) un caso de `p03/reproductoras` que antes caía por BR-20.

## 3 · Plan UAT del propietario (C4)

Guion ES, 20 min, misma generación certificada. Rol: operador de reproductoras (escritorio + móvil).

| Caso | Acción | Esperado |
|---|---|---|
| UAT-R205-01 | Desde el hub, registrar la llegada de un lote de reproductoras completando el cuadre en pantalla | «Operación guardada»; el dato de cuadre aparece en el detalle |
| UAT-R205-02 | Repetir desde el detalle del lote | Igual |
| UAT-R205-03 | Intentar guardar sin completar el cuadre | Mensaje claro bajo el campo; nada se envía; al completar, guarda |
| UAT-R205-04 | Cambiar a EN y repetir en móvil | Etiquetas EN; formulario usable; sin desplazamiento horizontal |

Criterio: 4/4; sin errores rojos del servidor.
