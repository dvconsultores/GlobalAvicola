# PROCESO 02 DEL ORDEN DE `GA-REM-016` — CONTROL PRODUCCION DIARIO

| | |
|---|---|
| **Estado final** | **`CERTIFIED`** |
| **Fecha** | 2026-09-04 · **Wave** 3 |
| **Evidencia** | `e2e/proceso-02-*.spec.ts` — **7/7 PASS** |

> Este es un proceso del **orden de certificación** que fija `GA-REM-016`, no uno de los
> 15 procesos `P-XX` de la taxonomía. Atraviesa varios de ellos sin agotar ninguno: por eso
> los procesos de etapa que lo contienen quedan `PARTIAL` en la matriz y no heredan su
> certificación. Ver `PROCESS_CERTIFICATION_MATRIX.md §4`.

## Spec y requisitos

`GA-REM-016` orden #2 —«concentra el bloqueador `P0-1` y es el de mayor frecuencia
operativa»— · depende de `GA-REM-005`, `CERTIFIED`, cuya implementación **no se reabre**.

Cliente: «Mortalidad — Cantidad, **causa**» (§16) · «Registrar consumo de alimento — Sí» ·
«Registrar peso promedio — Sí» · «Muestra tomada» (§11).

## Casos ejecutados

| Caso | Verifica | Resultado |
|---|---|---|
| `HAPPY PATH` | mortalidad con causa; el saldo baja | 201, causa conservada, saldo −10 ✅ |
| `REGLA` | `BR-01` mortalidad > saldo | 400 con el saldo en el mensaje; nada persiste ✅ |
| `REGLA` | mortalidad de cero | rechazada ✅ |
| `ALERTA` | umbral **configurado** dispara la alerta | 10 % → severidad `critical` ✅ |
| `ALIMENTO` | consumo con su tipo | 250,5 kg y `feed_type_id` ✅ |
| `PESAJE` | peso promedio y muestra | 1 850,5 g y `sample_size` 30 ✅ |
| `AISLAMIENTO` | mortalidad en lote ajeno | rechazada ✅ |

## Datos derivados

El saldo de aves se recalcula desde los eventos antes y después de cada caso. Es la
verificación que `P0-1` impedía: durante meses **ninguna mortalidad válida podía
registrarse**.

## `AC08` — umbral configurable

El caso de alerta ejercita el umbral que la configuración declara
(`MORTALITY_ALERT_WARNING_PCT` / `_CRITICAL_PCT`, expuestos en `docker-compose.yml`).
El alcance **por empresa** sigue en `GA-REM-019` y **no se implementa**.

## Huecos

`GA-REM-021` (consumo de agua) es un requisito real identificado y **no forma parte de los
AC de este proceso** según la spec vigente: `docs/02 §3.14` lo enumera entre los datos
diarios, pero `GA-REM-016` no lo incluye en el alcance del control de producción. Se
registra la cobertura como parcial en la matriz en lugar de ocultarla, y no se implementa:
`GA-REM-021` no está autorizada en esta Wave.
