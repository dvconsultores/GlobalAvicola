# GA-GOV-02 · RECONSTRUCCIÓN DE FUENTE — OBSERVACIÓN DE NEGOCIO (R-184)

Objetivo: recuperar la **redacción exacta y el contexto** de la observación de negocio registrada durante R-184.

## 1 · Redacción original exacta

| Fuente | Redacción literal |
|---|---|
| Principal — `audit/ga-r184/GA_R184_IPE_BUSINESS_TRACE.md` §7 «Tensión detectada (registrada, NO resuelta aquí)» (commit `304174d`) | «Con constantes realistas (peso 2000 g, edad 19 d, viabilidad 95 %, FCR 3.0) la fórmula implementada devuelve **33333.3**, mientras las bandas del propio contrato sugieren escala EPEF (~300). El patrón conocido del EPEF europeo es `ADG × viabilidad% / (FCR × 10)` — el `× 100` extra del numerador produce un factor ~100 sobre esa escala cuando la viabilidad se maneja como porcentaje (95.0) en vez de fracción (0.95). … **STATUS: OBSERVACIÓN DE NEGOCIO registrada** (candidata a decisión del propietario; NO bloquea R-184).» |
| Complemento — `GA_R184_CLARIFICATIONS.md` (subcaso) | «la tensión escala-fórmula vs bandas `reference` **no impide** resolver R-184 (la fórmula está canonizada y se preserva); queda como **observación de negocio** registrada para el propietario (`OWNER_DECISION_REQUIRED`, no bloquea). No se inventó ninguna fórmula alternativa.» |
| Complemento — `GA_R184_CERTIFICATION.md` §Registros derivados (2) | «posible factor ~100 de la fórmula implementada frente a la escala de las bandas `reference` (viabilidad en % + ×100 en numerador). No se toca; clasificada `OWNER_DECISION_REQUIRED` futura, no bloquea.» |

## 2 · Cómo se descubrió

Durante la **traza de negocio del IPE** (paso obligatorio de R-184), al calcular a mano el valor esperado con las constantes del fixture determinista (2000 g · 19 d · 95 % · FCR 3.0 → 33333.3) y contrastarlo con las **bandas del propio contrato de respuesta** (`reference: {"excellent": ">300", "good": "250-300", "average": "200-250"}`) y con el patrón estándar del Índice de Producción Europeo. No proviene de un fallo de runtime: es una **incoherencia de semántica de negocio detectada por cálculo independiente**.

## 3 · Concepto afectado

- **Escala e interpretación del IPE** (Índice Productivo Europeo, G-06): fórmula `(Viabilidad% × Ganancia_Diaria_g × 100) / (FCR × 10)` (viabilidad como número de porcentaje) **vs** bandas `reference` alineadas con la escala estándar EPEF (~200-400).
- Interacciones registradas: (a) la unidad de viabilidad (% vs fracción) decide el factor ~100; (b) el FCR es **simplificado** por contrato propio («kg feed / kg weight (estimado)», nota explícita «requiere datos de pesaje para FCR real») — con datos heredados el FCR resultante no es comparable con FCR reales, lo que condiciona igualmente la interpretabilidad del índice.
- No es: fecha/tipo temporal (eso fue R-184), seguridad, ni datos persistidos.

## 4 · Por qué no se resolvió en R-184

- El encargo R-184 ordenaba **preservar la fórmula** (§2/§40/§81): «*DO NOT CHANGE THE FORMULA JUST TO REMOVE THE 500*»; cambiar escala/bandas era semántica de negocio, fuera de alcance. Se registró como observación y quedó igualmente fuera de la UAT del propietario (GA-UAT-06 §6: no convertir en decisión dentro de la UAT).

## 5 · Estado del arte

- Documentada en tres artefactos (arriba) + fila propia en `GA_R184_CANONICAL_RECONCILIATION.md` §7 y en la matriz de GA-UAT-06.
- **Sin implementación, sin OD asignada, sin finding** hasta esta tranche.
