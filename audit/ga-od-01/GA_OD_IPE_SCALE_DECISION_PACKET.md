# GA-OD-01 · PAQUETE DE DECISIÓN DEL PROPIETARIO — ESCALA DEL IPE (G-06)

## THE QUESTION

**¿Qué escala e interpretación debe tener el IPE y su clasificación visible (Excelente / Bueno / Regular)?**

## WHY THIS DECISION EXISTS

El IPE es un indicador para decisiones productivas. Hoy el **número** y sus **bandas de clasificación** viven en escalas distintas (×100 de diferencia exacta), así que la clasificación que ve el usuario no informa: con datos reales casi todo sale «Excelente». Es una **regla de negocio**, no un defecto de código: el código hace lo que su definición escrita dice; falta decidir **cuál definición es la correcta**.

## WHAT THE PRODUCT DOES TODAY

- Calcula IPE con la fórmula histórica: `(Viabilidad% × Ganancia diaria × 100) / (FCR × 10)`.
- Clasifica con bandas estándar: **>300 Excelente · 250-300 Bueno · 200-250 Regular**.
- Resultado: números ~100× las bandas ⇒ la insignia dice «Excelente» aunque el lote sea mediocre (ejemplo real: un lote flojo da 21315 y sale 🟢).

## WHY FORMULA AND BANDS CONFLICT

El `×100` de la fórmula ya convertía la viabilidad de fracción (0.95) a porcentaje, pero la viabilidad **ya llega en porcentaje (95.0)**: se cuenta dos veces ⇒ factor 100 exacto (verificado con álgebra y con 3 casos). El resto de la fórmula es el estándar europeo (EPEF).

## REAL NUMERIC EXAMPLES

| Caso | Hoy muestra | Clasificación hoy | Con A mostraría | Con A/B clasificaría |
|---|---|---|---|---|
| Lote certificado (fixture R-184) | 556.6 | 🟢 Excelente | 5.6 (FCR placeholder) | 🔴 |
| Ejemplo sintético | 33333.3 | 🟢 Excelente | 333.3 | 🟢 |
| Engorde típico bueno | 35625 | 🟢 Excelente | 356.25 | 🟢 |
| Engorde flojo | **21315.8** | **🟢 Excelente (engañoso)** | 213.2 | **🔴 (correcto)** |

> A y B clasifican **igual entre sí**; difieren en el número mostrado y en su comparabilidad externa. El caso «5.6» refleja además el FCR simplificado (limitación ya documentada, independiente de esta decisión).

## OPTION A — ALINEAR EL VALOR A LA ESCALA DE LAS BANDAS (EPEF estándar)

- Se elimina el `×100` sobrante; el número queda en escala EPEF (típico 200-400).
- **Bandas, umbrales de pantalla y textos: SIN cambios.**
- Números comparables con el estándar del sector; clasificación intuitiva y discriminante.
- Contras: el número mostrado cambia (UAT propia); con FCR placeholder algunos lotes heredados seguirán viéndose bajos (limitación aparte).

## OPTION B — MANTENER EL NÚMERO Y REESCALAR LAS BANDAS ×100

- Bandas pasarían a >30000 / 25000-30000 / 20000-25000 (y umbrales de pantalla).
- El número actual no cambia.
- Contras: se abandona la comparabilidad con el estándar y con la cifra clásica «300»; hay que tocar **tres capas** (backend, umbrales de UI, textos) para conservar un número no estándar.

## OPTION C — STATUS QUO + DOCUMENTAR

- Nada cambia; se documenta que la escala no es la estándar y que la clasificación es poco informativa.
- Consecuencia (dicha claramente): **casi todo seguirá saliendo «Excelente»**, incluso lotes flojos. Riesgo de decisiones basadas en una señal engañosa. Coste técnico: cero. **No recomendada.**

## RECOMMENDATION

**Opción A** — re-evaluada tras la reconstrucción completa y **mantenida**: (1) alinea valor y bandas sin tocar bandas ni pantallas; (2) número comparable al estándar; (3) evita valores inflados; (4) clasificación recupera capacidad de discriminar; (5) coste mínimo y sin migración (nada persistido).

## OWNER DECISION

**PENDIENTE** — el propietario debe responder **A**, **B** o **C** (llamada de decisión). Tras su respuesta: se asigna el ID canónico (siguiente libre línea OD; ver trazabilidad), se ratifica la regla y se determinará, si procede, una tranche técnica nueva (spec → AC → implementación → UAT). **Nada se implementa en esta sesión.**

---
*Apéndices técnicos*: `GA_OD_IPE_CURRENT_FORMULA_TRACE.md` · `GA_OD_IPE_CLASSIFICATION_BANDS_TRACE.md` · `GA_OD_IPE_UNIT_ANALYSIS.md` · `GA_OD_IPE_SCALE_EVIDENCE.md` · `GA_OD_IPE_SCALE_IMPACT_ANALYSIS.md` · `GA_OD_IPE_SCALE_TRACEABILITY.md`.
