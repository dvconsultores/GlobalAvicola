# GA-OD-01 · EVIDENCIA DE ESCALA (referencias, unidades, ejemplos)

## 1 · Referencias y hechos resueltos

| Hecho | Estado | Fuente |
|---|---|---|
| Fórmula implementada exacta | RESUELTO | `service.py::get_kpi_ipe` (traza §2) |
| Viabilidad en porcentaje (95.0) | RESUELTO | código + runtime (`viabilidad_pct`) |
| ADG en g/día | RESUELTO | código (`peso_g / edad_d`) |
| Bandas 200/250/300 con textos Excelente/Bueno/Regular | RESUELTO | backend `reference` + FE 2 páginas + i18n |
| Factor de escala = 100 exacto | RESUELTO | álgebra + 3 casos (§4 de unidades) |
| IPE se persiste en BD | **NO** — cálculo en vivo por vista; nada almacenado | grep de modelos/migraciones; respuestas runtime |
| El FCR es un placeholder documentado («requiere pesaje real») | RESUELTO | nota del propio endpoint de conversión |
| Nombre «Europeo»/EPEF es la referencia de la escala de bandas | Referencia del contrato (docstring «European Production Index» + bandas estándar); **la interpretación exacta que el propietario quiera ratificar es el objeto de esta sesión** | — |

**Referencia externa (no canónica hasta ratificación)**: el EPEF convencional del sector para broilers se reporta comúnmente en el rango ~200-400, coherente con las bandas ya codificadas. Se documenta como contexto; la decisión es del propietario.

## 2 · Ejemplos deterministas

### EJEMPLO A — fixture certificado de R-184/GA-UAT-06 (lote 11, runtime)
Valores: viabilidad **100.0 %** · ADG **13.636 g/día** (1500 g / 110 d) · FCR **24.5** (simplificado heredado).

| | Resultado | Clasificación con bandas actuales |
|---|---|---|
| Actual | **556.6** (capturado en runtime) | 🟢 «Excelente» |
| Opción A (sin ×100) | **5.6** | 🔴 «Regular» (por el FCR placeholder; con FCR real el caso cambiaría) |
| Opción B (bandas ×100: >30000) | **556.6** sin cambio | 🔴 «Regular» (bajo la banda reescalada) |

> Nota honesta: el FCR simplificado (24.5) domina este caso; su clasificación baja **en ambas opciones coherentes** refleja el placeholder de FCR, no la escala. Es una limitación separada, ya documentada en el contrato del KPI.

### EJEMPLO B — sintético GA-GOV-02
Valores: viabilidad **95.0 %** · ADG **105.263 g/día** (2000/19) · FCR **3.0**.

| | Resultado | Clasificación |
|---|---|---|
| Actual | **33333.3** | 🟢 «Excelente» |
| Opción A | **333.3** | 🟢 «Excelente» |
| Opción B | 33333.3 vs >30000 | 🟢 «Excelente» |

### EJEMPLO C — engorde real, dos calidades
C1 (bueno): viabilidad 95 % · ADG 60 g/d · FCR 1.6 → Actual **35625.0** 🟢 · Opción A **356.25** 🟢 · Opción B 🟢.
C2 (flojo): viabilidad 90 % · ADG 45 g/d · FCR 1.9 → Actual **21315.8** — **🟢 «Excelente» (CLASIFICACIÓN ENGAÑOSA)** · Opción A **213.2** → 🔴 «Regular» · Opción B (bandas ×100) → 🔴 «Regular» (idéntica a A).

**Conclusión de ejemplos**: Actual no discrimina (todo ≥300). A y B **clasifican idénticamente entre sí** (porque el factor es exacto); difieren solo en el número mostrado (356.25 vs 35625) y en la comparabilidad con el estándar.

## 3 · Incertidumbres declaradas
- FCR placeholder afecta **valores absolutos** bajo todas las opciones (limitación separada).
- No hay más fuentes de especificación del IPE en `docs/`/`specs/` que las citadas.
