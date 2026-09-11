# GA-GOV-02 · PAQUETE DE DECISIÓN DEL PROPIETARIO — ESCALA E INTERPRETACIÓN DEL IPE

> Una única decisión pendiente. No se decide por el propietario. Etiqueta de trabajo: **OD candidata (siguiente libre tras OD-21; numeración a ratificar al formalizar)**.

## QUESTION

**¿Qué escala e interpretación debe tener el IPE (Índice Productivo Europeo) y sus bandas visible (Excelente / Bueno / Regular)?**

## CURRENT BEHAVIOR

- Fórmula implementada: `(Viabilidad%_numérico × Ganancia_Diaria_g × 100) / (FCR × 10)` → para rangos típicos produce valores **~100×** por encima de las bandas.
- Bandas del contrato: `Excelente >300 · Bueno 250-300 · Regular 200-250` (escala estándar EPEF).
- Efecto práctico: la clasificación visible resulta **sistemáticamente favorable**; el número no es comparable con el estándar homónimo («Europeo»).
- Contexto adicional documentado: el FCR es **simplificado** por el propio contrato («requiere datos de pesaje para FCR real»), lo que condiciona el valor con datos heredados.

## WHY IT MATTERS

El IPE es un KPI de decisión productiva: si la escala y las bandas no comparten unidad, la clasificación que ve el usuario no informa (siempre «Excelente» en rangos normales). Es una **regla de negocio**, no un defecto de código: el código hace exactamente lo que su definición escrita dice — la falta es cuál definición debe mandar.

## OPTION A (recomendada) — Alinear el valor a la escala estándar de las bandas

- Eliminar el factor ×100 sobrante (viabilidad manejada como porcentaje) ⇒ valores típicos en escala EPEF (p. ej. 200-400).
- Las bandas actuales permanecen como están; la clasificación recupera sentido.
- **Consecuencia de negocio**: los números mostrados cambian (~100× menores). La interpretación pasa a ser la estándar del indicador.
- **Consecuencia técnica**: cambio pequeño en una expresión + tests + nueva aceptación visible (cambia lo mostrado ⇒ UAT propia). El FCR simplificado sigue siendo un límite documentado (los valores ganan coherencia de escala, no precisión de insumo).
- **Consecuencia sobre datos históricos**: ninguna (KPI calculado en vivo; nada persistido).

## OPTION B — Mantener el valor actual y reescalar las bandas ×100

- Bandas pasarían a `>30000 / 25000-30000 / 20000-25000`; el número aceptado (p. ej. 556.6) no cambia.
- **Consecuencia de negocio**: se abandona la comparabilidad con el EPEF estándar; el índice queda como «índice interno propio» con nombre europeo (ambigüedad de nombre a documentar).
- **Consecuencia técnica**: banda + umbrales de UI (>=300/250) a actualizar; requiere su propia aceptación.
- **Histórico**: ninguna.

## OPTION C — Mantener todo y documentar la limitación

- Sin cambios de producto; se documenta explícitamente que la escala actual no es la del estándar y que la clasificación es poco informativa hasta revisión.
- **Consecuencia**: mantiene la ambigüedad y la clasificación engañosa; coste cero ahora.

## RECOMMENDED OPTION

**A.** Razón: (1) las bandas y la lógica visual ya codifican la escala estándar — la interpretación «estándar» es la única que hace coherente todo el contrato existente; (2) B legitima un número no comparable y obliga a reescribir bandas y umbrales de UI para ganar menos coherencia; (3) C deja un KPI clasificando «Excelente» de forma sistemática; (4) el cambio es pequeño, sin migración y con UAT propia.

## NOTA DE SECUENCIA

Si se elige A o B: **OBSERVACIÓN → DECISIÓN → SPEC → (finding solo si hay brecha) → AC → IMPLEMENTACIÓN con aceptación**. No se implementa nada desde este paquete.

## RESOLUCIÓN (actualización de estado, 2026-09-11)

**DECIDIDA: Opción A** (respuesta explícita del propietario en la sesión GA-OD-01) → **OD-22 RATIFICADA** (`audit/ga-od-01/GA_OD_IPE_SCALE_OWNER_DECISION.md`). Brecha real ⇒ finding **R-187 · P2 · OPEN** (`audit/ga-od-01/GA_OD_IPE_SCALE_IMPLEMENTATION_GAP_R187.md`). Observación de negocio: **RESUELTA**. Implementación: **NO** (tranche propia futura con UAT).
