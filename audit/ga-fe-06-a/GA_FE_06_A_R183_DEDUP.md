# GA-FE-06-A · DEDUP R-183

## Decisión

**R-183 = ABSORBED_IN_R182** (subhallazgo de seguridad) — clasificación **A** del encargo.

## Razonamiento (verdad del repositorio)

| Pregunta de dedup | Verdad comprobada |
|---|---|
| ¿Es otra cosa distinta del defecto raíz de R-182? | No. R-182 es el contrato de `area_id` en el lote: capturarse, enviarse, persistirse **y pertenecer al inquilino**. `GA-REM-039` añadió el campo; la validación de pertenencia quedó sin registrar en `lots` — es la mitad de escritura del mismo contrato |
| ¿Ya existe un hallazgo que lo gobierne? | **La clase** sí: `app/tenancy.py` (`verificar_pertenencia` ← `R-42`/`GA-REM-002`; `verificar_catalogo_de_empresa` ← `R-179`; fail-closed ← `R-139`). **El sitio** `lots.area_id` nunca se registró en esas extensiones: no hay R-ID previo que lo cubra |
| ¿Cobertura de pruebas previa? | Lectura: `tests/test_areas.py::test_t_039_05` (`AC-A12`) — áreas no cruzan **GET**. Escritura en lote: **ninguna** prueba la cubría (confirmado por grep de `area` en `tests/security/`) |
| ¿Tensión con R-139/R-179? | Ninguna: el validador que se cablea es exactamente el que ambas fijaron (nulo = compartido; ajeno = inexistente; sin empresa = fail-closed) |

## Consecuencias

- No se crea deuda nueva: **no hay entrada R-183 independiente** en el backlog; la disposición queda registrada en la entrada de R-182 (sección GA-FE-06-A) y en `GA_FE_06_FINDINGS.md`.
- El subhallazgo recibe AC propios (`R182-SEC-AC01…08`) dentro de la especificación R-182 enmendada.
- La numeración del encargo (`R182-AC20` «cross-company Area cannot be assigned» / `R182-AC36` «foreign tenant Area cannot be referenced») se reconcilia como los criterios canónicos de este defecto; en la tabla local de GA-FE-06 el criterio equivalente se registró como AC11 (alias). La enmienda de spec deja el mapeo explícito.
