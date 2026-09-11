# GA-UAT-07 · R-187 — GUÍA DE UAT DEL PROPIETARIO (OD-22 · IPE G-06)

Esta guía valida **solo el resultado visible de negocio** de la regla que usted ya aprobó (OD-22).
No requiere cálculos, comandos ni conocimientos técnicos. Tiempo estimado: 5-10 minutos.

**Acceso preparado por operaciones** (usuario temporal de operación, fuera del repositorio):
- Usuario: `ra187uat` · Contraseña: entregada por operaciones (archivo temporal fuera del repositorio).
- Entorno: `https://avicola.globaldv.net` · Empresa: Avícola Global C.A.

## Punto de partida

1. Abra el sistema e inicie sesión con el usuario indicado.
2. Entre a **lotes** y abra el lote **`L-R187-DET`** (también accesible en Reportes → lote).

> Nota: en el reporte puede aparecer un aviso amarillo sobre «registros aprobados». Se refiere a
> indicadores de **incubadora** que no aplican a un lote de engorde — es un texto pre-existente,
> ajeno a esta validación.

---

## Caso 1 (UAT-01) — El IPE aparece en la nueva escala

- **Dónde**: detalle del lote `L-R187-DET` → tarjeta **IPE**.
- **Qué debe ver**: IPE **333.3** en verde, con viabilidad 95 %, FCR 3, peso 2000 g y edad 19 días. Sin errores ni avisos técnicos.
- **Pregunta**: ¿El IPE mostrado corresponde ahora a la nueva escala que aprobó en OD-22?
- **Resultado**: PASE / PASE CON OBSERVACIÓN / FALLO

## Caso 2 (UAT-02) — La clasificación se entiende

- **Dónde**: el mismo lote (clasificación «Excelente», semáforo verde) y, como apoyo, el lote **`L-R187-MID`** (que muestra **282.7 · Bueno · amarillo**).
- **Qué debe ver**: la clasificación es coherente con el número y con las bandas que decidimos mantener (>300 Excelente · 250-300 Bueno · ≤250 Regular).
- **Pregunta**: ¿Le resulta coherente la clasificación mostrada con el nuevo valor del IPE y las bandas que decidimos mantener?
- **Resultado**: PASE / PASE CON OBSERVACIÓN / FALLO

## Caso 3 (UAT-03) — Detalle y reporte coinciden

- **Dónde**: detalle del lote y luego **Reportes → lote `L-R187-DET`**.
- **Qué debe ver**: el **mismo valor 333.3** en ambas pantallas, sin diferencias.
- **Pregunta**: ¿El IPE es consistente entre el detalle del lote y el reporte?
- **Resultado**: PASE / OBSERVACIÓN / FALLO

## Caso 4 (UAT-04) — Recargar y volver a entrar no altera el valor

- **Dónde**: en el reporte, use recargar del navegador; después cierre sesión y vuelva a entrar; regrese al lote.
- **Qué debe ver**: el valor sigue siendo **333.3** y la clasificación la misma, sin volver a números antiguos.
- **Pregunta**: ¿El IPE se mantiene correctamente después de recargar y volver a entrar?
- **Resultado**: PASE / OBSERVACIÓN / FALLO

## Caso 5 (UAT-05) — Móvil

- **Dónde**: abra el mismo lote desde su teléfono (o ventana estrecha ~390 px).
- **Qué debe ver**: tarjeta IPE legible (**333.3** · verde), clasificación visible, sin recortes ni desplazamiento horizontal molesto.
- **Pregunta**: ¿La visualización del IPE se entiende correctamente en móvil?
- **Resultado**: PASE / OBSERVACIÓN / FALLO

## Caso 6 (UAT-06) — Aceptación global

- **Pregunta final**: ¿Considera que el sistema ya refleja correctamente la regla OD-22, mostrando el IPE en la escala estándar y manteniendo las bandas existentes?
- **Resultado**: PASE / PASE CON OBSERVACIÓN / FALLO

---

**Cómo responder la decisión** (una sola): **A) ACEPTO R-187** · **B) ACEPTO R-187 CON OBSERVACIONES: <texto>** · **C) RECHAZO R-187 — CORREGIR: <texto>**.

*Su respuesta se registra tal cual, sin cambios de producto durante la validación.*
