# GA-R184 · OWNER UAT — EJECUTADA (GA-UAT-06, decisión A)

Sesión corta y visible. El propietario **no repite** pruebas de tipos, seguridad ni fórmulas: eso ya está certificado de ingeniería.

## Qué valida (4 comprobaciones, ~3 minutos)

| # | Caso | Pregunta de aceptación |
|---|---|---|
| 01 | Abrir un lote con datos (p. ej. **L-BO-2026-05**) y ver la tarjeta **IPE** | ¿El valor aparece y se entiende? |
| 02 | Comprobar Viabilidad / FCR / Peso prom. / Edad en esa tarjeta | ¿Los números son coherentes con lo que espera del lote? |
| 03 | Refrescar (F5) y volver a entrar | ¿El indicador sigue igual? |
| 04 | Móvil | ¿Se ve bien en el teléfono? |

**Contexto honesto**: hasta ahora, la tarjeta IPE **desaparecía** para todo lote real (el servidor devolvía error y la tarjeta se ocultaba). Con la corrección, vuelve a mostrarse con el cálculo que el producto ya definía (misma fórmula de siempre).

## Frase de decisión (cuando se convoque)

```
A) ACEPTO R-184
B) ACEPTO R-184 CON OBSERVACIONES: <texto>
C) RECHAZO R-184 — CORREGIR: <texto>
```

Estado: **ACEPTADO — A) ACEPTO R-184 (2026-09-11, GA-UAT-06)**. Registro: `audit/ga-uat-06/GA_OWNER_ACCEPTANCE_R184_RECORD.md`. No se inicia otra tranche.
