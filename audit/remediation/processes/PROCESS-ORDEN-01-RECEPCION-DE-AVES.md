# PROCESO 01 DEL ORDEN DE `GA-REM-016` — RECEPCION DE AVES

| | |
|---|---|
| **Estado final** | **`CERTIFIED`** |
| **Fecha** | 2026-09-04 · **Wave** 3 |
| **Evidencia** | `e2e/proceso-01-*.spec.ts` — **7/7 PASS** |

> Este es un proceso del **orden de certificación** que fija `GA-REM-016`, no uno de los
> 15 procesos `P-XX` de la taxonomía. Atraviesa varios de ellos sin agotar ninguno: por eso
> los procesos de etapa que lo contienen quedan `PARTIAL` en la matriz y no heredan su
> certificación. Ver `PROCESS_CERTIFICATION_MATRIX.md §4`.

## Spec y requisitos

`GA-REM-016` orden #1 —«alimenta el inventario de todos los demás»— ·
`spec.md §4.4/§4.5/§4.8` · `docs/02 §3.5` · `BR-06`, `BR-07`, `BR-08`, `BR-17`, `BR-19`.

Cliente: «Registrar recepción de aves — Sí» y «Distribuir aves por galpón, sexo y lote —
Sí» (`Recomendación central.pdf` §2).

## Casos ejecutados

| Caso | Verifica | Resultado |
|---|---|---|
| `AUTENTICACIÓN` | sin sesión la aplicación no expone el proceso | redirige a `/login` ✅ |
| `HAPPY PATH` | UI → API → BD: 1 000 aves en dos sexos | 201, submovimientos íntegros ✅ |
| `VALIDACIÓN` | `BR-08` exige granja y galpón | 400 con `rule=BR-08` ✅ |
| `VALIDACIÓN` | `BR-19` período cerrado, fecha **relativa** | 400 con `rule=BR-19` ✅ |
| `AUTORIZACIÓN` | el aprobador no tiene `operations:create` | 403 ✅ |
| `AUDITORÍA` | la recepción deja rastro | entrada presente ✅ |
| `AISLAMIENTO` | lote de otra empresa | rechazado ✅ |

## Cadena verificada

`AUTENTICACIÓN → AUTORIZACIÓN → CONTEXTO DE EMPRESA → PERTENENCIA → VALIDACIÓN → REGLAS →
PERSISTENCIA → AUDITORÍA → RESPUESTA → INTERFAZ`.

El saldo de aves derivado se verifica en el proceso 02, que lo consume.

## Huecos

`R-47`: `POST /lots` ignora el `start_date` recibido, de modo que un lote recién creado no
admite eventos retroactivos. No bloquea este proceso —la recepción se registra con fecha
del día— pero sí limita el alta de lotes con historia. P1, `GA-REM-019`.
