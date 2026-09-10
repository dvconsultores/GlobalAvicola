# `MUTATION CHECKPOINT` — gobernanza ejecutable del driver de sensibilidad

**Establecido** 2026-09-10 · WAVE B tranche 14 · `GA-REM-002` enmienda E `T-002-E4`.
**Implementación** `backend/scripts/mutation_guard.py` · **prueba** `backend/tests/test_mutation_guard.py` (casos A…E).

## Por qué

El driver de sensibilidad instala una mutación en un archivo de producción, corre la prueba que debería enrojecer y restaura. La restauración se hacía
con `git checkout -- <archivo>`, que toma el contenido de **`HEAD`**. Si la implementación todavía no está confirmada, `HEAD` es el commit anterior y la
restauración **borra la implementación**, sin error y sin aviso.

Ocurrió en el **tranche 10** y volvió a ocurrir en el **tranche 13**, esta última vez al validar una prueba reformulada. En ambos casos se detectó y se
reimplementó, pero la lección es la misma:

> Una instrucción escrita no es una garantía. La garantía es una **precondición ejecutable** que se niega a continuar.

## Las siete señales — todas deben ser favorables

| # | Señal | Qué evita |
|---|---|---|
| 1 | `IMPLEMENTATION_COMMIT` declarado | mutar «contra lo que haya» |
| 2 | ese commit existe y se resuelve | un identificador mal copiado |
| 3 | `HEAD` **es** ese commit | restaurar a un estado anterior a la implementación (el incidente) |
| 4 | árbol de producción limpio (`backend/app/`, `frontend/src/`, `backend/alembic/`) | destruir cambios sin confirmar |
| 5 | cada archivo a mutar existe en ese commit | restaurar a la nada |
| 6 | la restauración usa el **commit declarado**, no `HEAD` | la causa raíz exacta del incidente |
| 7 | tras restaurar, el archivo es byte a byte el del commit | residuo silencioso |

## Contrato

- Ante cualquier señal desfavorable: **`ABORTAR`**. No hay aviso-y-continuar.
- No existe `--force` ni `--skip-check`. Si en algún momento hiciera falta un mecanismo de emergencia, requiere autorización explícita del propietario
  y queda fuera de este contrato.
- El informe (`GuardaDeMutacion.informe()`) se incluye en la evidencia de cada tranche, antes de la primera mutación.
- La negativa del guardián se prueba en cada regresión: `tests/test_mutation_guard.py` construye repositorios desechables y comprueba que el driver
  **se niega** en cada modo de fallo conocido y **permite** solo cuando todo está en orden. Producción no se toca para probarlo.

## Orden obligatorio de un tranche

```
commit de spec → rojo válido → implementación → verde dirigido → COMMIT DE IMPLEMENTACIÓN
                                                                        ↓
                                       informe del guardián (las 7 señales) → sensibilidad
                                                                        ↓
                       integridad posterior (HEAD == implementación · residuo 0) → regresión → evidencia → push
```
