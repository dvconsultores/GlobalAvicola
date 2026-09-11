# GA-R187 · GUÍA DE UAT DEL PROPIETARIO

Estado: **READY** — la UAT del propietario **no se inicia automáticamente**; se activará por su instrucción.

## Qué validar (solo el resultado visible de negocio)

1. **Tarjeta IPE** en el detalle de un lote: muestra ahora un valor en **escala estándar** (p. ej. **333.3** en `L-R187-DET`), no un número de miles.
2. **Clasificación con sentido**: contra las bandas que ya existían (>300 Excelente · 250-300 Bueno · ≤250 Regular) — un lote flojo ya **no** sale «Excelente». Ejemplos retenidos: `L-R187-LOW` (241.1 → 🔴) · `L-R187-MID` (282.7 → 🟡) · `L-R187-B300` (300.0 → 🟢) · `L-R187-B250` (250.0 → 🟡) · `L-R187-B249` (249.9 → 🔴).
3. **Detalle y reporte coherentes** (mismo valor en ambas pantallas).
4. **Refresh / relogin** estables (sin valor viejo de escala).
5. **Móvil** usable (valor legible, sin recortes).

## Redacción de la pregunta (importante — §71)

La decisión de fórmula ya está tomada (OD-22). La UAT **no** pregunta si prefiere la fórmula antigua o la nueva; pregunta:

> «¿El producto refleja ahora correctamente la regla de negocio que usted ya aprobó?»

## Qué NO debe probar el propietario

Recalcular la fórmula · ataques de API · tipos fecha/datetime · repetir la matriz de seguridad de tenant · regresiones técnicas (ya certificadas con evidencia).

## Nota operativa de acceso

Los lotes de ejemplo están en la empresa 1, unidad **broiler** (ventana habilitada temporalmente por operaciones durante la UAT, como en GA-UAT-06; al cierre se restaura el estado OFF). Códigos: `L-R187-DET/LOW/MID/B249/B250/B300`. Lote legado: `L-BO-2026-05` (11) — muestra **5.6** (su FCR simplificado es un caso límite documentado, independiente de esta decisión).
