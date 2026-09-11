# GA-OD-01 · ANÁLISIS DE IMPACTO (A/B/C)

| Eje | OPCIÓN A (alinear valor) | OPCIÓN B (reescalar bandas) | OPCIÓN C (status quo) |
|---|---|---|---|
| Efecto de negocio | Valores en escala EPEF (comparables al estándar; «356» significa lo que parece) | Valores 100× el estándar; el número pierde referencia externa | Clasificación sigue sin discriminar (casi todo «Excelente») |
| Fórmula | Se elimina el ×100 sobrante (1 término) | Intacta | Intacta |
| Bandas | **Intactas** (200/250/300 + i18n) | Reescritas ×100 en 3 capas (backend reference, umbrales FE, posibles textos) | Intactas (incoherentes) |
| Frontend | **0 cambios** (umbrales y textos siguen válidos) | Cambiar umbrales `>=30000/>=25000` en 2 páginas | 0 |
| Backend | 1 expresión | 1 dict `reference` | 0 |
| Datos / migración | **Ninguna** (IPE es cálculo en vivo; nada persistido) | Ninguna | Ninguna |
| Histórico | Vistas antiguas recalcularán con la nueva escala (los informes no almacenan valores); la captura 556.6 queda como hecho de la regla entonces vigente | Igual (números viejos quedarían «bajos» frente a bandas ×100 en recálculos si se mezclan criterios) | Sin cambio |
| Móvil | Igual (mismos componentes) | Cambian umbrales mostrados | Igual |
| Traducciones | Sin cambio | Posible ajuste de textos | Sin cambio |
| Pruebas | Nuevo valor esperado determinista (×100 menor) + suite ajustada | Igual al actual (el número no cambia) + nuevos umbrales de UI probados | Sin cambio; se documenta la limitación |
| UAT | Requerida (lo visible cambia: el número) | Requerida menor (el número no cambia; cambia la lógica de clasificación visible para valores bajos) | No requerida |
| Proceso P-15 | El indicador gana interpretabilidad; sin impacto estructural | Mantiene magnitud no estándar bajo nombre europeo | Deuda de interpretabilidad abierta y documentada |

## Impacto en certificaciones (§17)
- **R-184 / GA-UAT-06**: PRESERVADOS. R-184 certificó el fix de fechas y preservó la fórmula entonces vigente; una decisión nueva de negocio es **prospectiva** y no convierte la aceptación pasada en error (el hecho histórico 556.6 sigue siendo cierto bajo la regla entonces canónica).
- **R-186 / G-05**: PRESERVADO (sin relación; G-05 no se toca).
- **GA-FE-02..07**: PRESERVADOS (sin superficies compartidas alteradas por una decisión de escala).
- La implementación (si A o B) sería **tranche nueva con su propia spec/AC/UAT**; nunca un «regression fix» de R-184.

## Riesgos
- A: cambio visible del número ⇒ requiere comunicación/UAT; con FCR placeholder algunos valores seguirán raros (limitación ya documentada e independiente de la escala).
- B: deuda de comparabilidad permanente + 3 capas a tocar para conservar el número.
- C: clasificación engañosa persistente (riesgo de decisión de negocio con dato inflado).
