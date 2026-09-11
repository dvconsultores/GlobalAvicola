# GA-FE-07 · REGISTRO CANÓNICO DE DECISIÓN DEL PROPIETARIO — **OD-21**

```
ID            OD-21 (siguiente libre tras OD-20; numeración del programa verificada)
FECHA         2026-09-11
ORIGEN        GA-GOV-01 (triage post-UAT-04) → pregunta A/B/C sobre elegibilidad por
              estado → elección EXPLÍCITA del propietario: «OPTION C — DOMAIN RULE COMPLETE»
ALCANCE       Decisión GENERAL de maestría de datos; **implementación de esta tranche limitada
              al caso probado Área → Lote** (GA-FE-07). El resto de maestros queda documentado
              para aplicación futura, SIN autorización de expansión masiva.
```

## Decisión

**UN RECURSO MAESTRO DADO DE BAJA LÓGICA (inactivo / deshabilitado / borrado lógico) NO PUEDE USARSE PARA NUEVAS REFERENCIAS.**

Principio canónico:

> **LA DESACTIVACIÓN LÓGICA IMPIDE EL USO NUEVO. LA DESACTIVACIÓN LÓGICA NO BORRA NI INVALIDA LA HISTORIA.**

## Aplicación específica Área → Lote

1. Un área con `is_active = false` **no debe aparecer** como opción elegible para asignar a un lote nuevo.
2. El backend **debe rechazar** la creación de un lote que intente asignar un área inactiva.
3. El backend **debe rechazar** una edición de lote que intente **cambiar** la referencia de área a un área inactiva.
4. Los registros históricos que ya referencian un área inactiva **conservan la referencia**.
5. La **visualización histórica** del área sigue siendo válida.
6. Una edición no relacionada de un lote que ya referencia un área inactiva **no debe fallar** por el solo hecho de que el área esté inactiva, siempre que la referencia de área no se esté cambiando.
7. Si la referencia de área **cambia**, el área nueva debe ser: **activa**, **válida** y de la **misma empresa** (y cumplir cualquier otra regla de pertenencia ya canónica).

## Fronteras de la decisión

- No reescribe, borra ni migra referencias históricas (§17 del encargo).
- No elimina la visibilidad administrativa de maestros inactivos en las pantallas de control (§22).
- No establece reglas nuevas de unidad de negocio, ni semántica RBAC, ni jerarquías.
- No retroactiva: solo gobierna **nuevas** referencias a partir de su vigencia.

## Trazabilidad

- Pregunta y opciones originales: `audit/ga-gov-01/GA_GOV_01_CLASSIFICATION_DECISIONS.md §OBS-UAT-04`.
- Implementación: `GA_FE_07_INACTIVE_AREA_REFERENCE_SPEC.md` · Finding: `R-185`.
- Mapa completo de la decisión: `GA_FE_07_OWNER_DECISION_TRACEABILITY.md`.

## Ratificación en uso real (GA-UAT-05)

El propietario **ratificó** la decisión OD-21 tras la sesión corta de aceptación de su implementación (Área→Lote):

- Sesión: **GA-UAT-05** (2026-09-11) — 5 casos visibles (selector, alta con activa, histórico usable, administración conserva retiradas, móvil).
- Decisión: **A) ACEPTO GA-FE-07**.
- Estado final: **OD-21 = RATIFIED_IMPLEMENTED_OWNER_ACCEPTED** · R-185 = `CLOSED_OWNER_ACCEPTED`.
- Registro: `audit/ga-uat-05/GA_OWNER_ACCEPTANCE_GA_FE_07_RECORD.md`.
