# GA-UAT-05 · REGISTRO DE OBSERVACIONES DEL PROPIETARIO — GA-FE-07

Estado de la sesión: **CERRADA — DECISIÓN A) ACEPTO GA-FE-07** (2026-09-11, explícita; sin observaciones adicionales del propietario).
Regla: ninguna observación se convierte en defecto ni se corrige durante la sesión.

## Resultados por caso

| UAT ID | Resultado del propietario | Observación | Severidad | Captura | ¿Hallazgo existente? | ¿Candidato nuevo? | ¿Bloquea aceptación? | Comentario del propietario |
|---|---|---|---|---|---|---|---|---|
| UAT-01 | PASS | Selector: solo «Nave Disponible» (activa); retiradas ausentes; sin IDs | — | C01/C02 | No | No | No | (decisión A; sin comentario adicional) |
| UAT-02 | PASS | Alta con área activa correcta | — | C03 | No | No | No | |
| UAT-03 | PASS | Histórico `UAT7-HIST-01` usable tras retirar su área | — | C04 | No | No | No | |
| UAT-04 | PASS | Administración conserva «Nave Retirada» y «Nave Histórica» (presencia; sin marca visual de estado — nota abajo) | P3 (nota UX, no bloquea) | C05 | No | No | No | |
| UAT-05 | PASS | Móvil: misma lista (solo activa), sin desbordes | — | C06/C07 | No | No | No | |

> Las medidas objetivas del walkthrough de referencia están en `GA_OWNER_UAT_GA_FE_07_EVIDENCE.md` (§A/§C) y `evidence/reference-walkthrough.json`. No sustituyen la aceptación.

---

## Observaciones de ingeniería registradas ANTES de la sesión (para honestidad)

1. **Descubrimiento «Lotes»**: sigue sin existir entrada de menú (OBS-UAT-01, ya inventariada como UX P2 en GA-GOV-01; no es regresión de GA-FE-07). Recorrido facilitado con accesos directos.
2. **Estado del área en la lista administrativa**: la pantalla de Áreas **no marca visualmente** cuál está retirada (muestra nombre y código). La regla de retirada se verifica por su efecto (no elegible). Si el propietario comenta que debería distinguirse visualmente, se registrará como observación UX (P3) — la baja lógica ya es visible vía su efecto. No es un defecto de R-185.
3. **Consola**: único mensaje de error observado = respuestas **403 de widgets KPI** para roles sin permiso de reportes (clase ya registrada N-3; invisible en uso normal). Errores fatales: **0**.
4. **Lote histórico**: abrir y re-guardar **sin cambiar el Área** no crea referencia nueva (comportamiento H1 certificado); cambiar el Área sí exige un Área activa. UAT-03 solo pide abrir (y opcionalmente guardar sin tocar el Área).

---

# DECISIÓN DEL PROPIETARIO

**A) ACEPTO GA-FE-07** — decidida explícitamente por el propietario el 2026-09-11 en la sesión GA-UAT-05. Sin observaciones adicionales reportadas. Registro: `GA_OWNER_ACCEPTANCE_GA_FE_07_RECORD.md`.
