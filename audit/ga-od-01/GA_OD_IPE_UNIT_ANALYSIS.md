# GA-OD-01 · ANÁLISIS DE UNIDADES

## 1 · Unidad de salida del IPE bajo cada interpretación

| Variable | Unidad actual | ¿Qué espera la fórmula con `×100`? | ¿Qué espera la fórmula sin `×100` (EPEF)? |
|---|---|---|---|
| Viabilidad | **Porcentaje (0-100)**: `95.0` | Fracción (0-1): `0.95` (el `×100` la convierte) | Porcentaje (0-100) |
| ADG | g/día | g/día ✔ | g/día ✔ |
| FCR | cociente | adimensional ✔ | adimensional ✔ |
| `×10` del divisor | — | normalización de escala del índice (constante del sector) | igual |
| Salida | ×100 sobre EPEF | EPEF estándar | EPEF estándar |

## 2 · El punto central (probado, no supuesto)

- `viabilidad = 100.0 − mortalidad%` ⇒ **ya es porcentaje** (95.0) — verificado en código y en runtime (`viabilidad_pct: 100.0` / `95.0` en respuestas capturadas).
- El `×100` del numerador es la conversión fracción→porcentaje **de una entrada que ya está en porcentaje** ⇒ doble conteo ⇒ **factor 100 exacto** sobre el EPEF estándar.
- Comprobación algebraica: fijadas ADG y FCR, `IPE_implementado / EPEF_estándar = 100` para cualquier dato (los demás términos son idénticos).
- No hay ninguna normalización oculta en el divisor que compense el factor: `FCR × 10` es idéntico en ambas expresiones.

## 3 · Clasificación del conflicto

**`CONFIRMED_100X_SCALE_CONFLICT`** — exacto, reversible (dividir el resultado entre 100 equivale a eliminar el `×100`), sin dependencia de datos.

## 4 · Verificación numérica rápida (3 casos)

| Caso | ADG | Viabilidad | FCR | Implementado | EPEF (sin ×100) | Ratio |
|---|---|---|---|---|---|---|
| Ejemplo B (sintético) | 105.26 g/d | 95.0 % | 3.0 | 33333.3 | 333.3 | 100.0 |
| Ejemplo C (engorde real típico) | 60 g/d | 95.0 % | 1.6 | 35625.0 | 356.25 | 100.0 |
| Ejemplo C-bis (lote flojo) | 45 g/d | 90.0 % | 1.9 | 21315.8 | 213.16 | 100.0 |
