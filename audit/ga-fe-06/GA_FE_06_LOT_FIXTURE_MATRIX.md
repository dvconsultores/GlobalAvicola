# GA-FE-06 · MATRIZ DE FIXTURES (datos runtime)

Convención de fechas: **día local del servidor** (`reference_today()`), consistente con `tests/test_lot_planned_close.py`. Códigos `GA6-*` para localización inequívoca y limpieza.

| Fixture | Tipo | Empresa | Valor | Propósito | E2E | Retirada |
|---|---|---|---|---|---|---|
| Área `GA6-AREA-A1` | Area | A (1) | nombre «Nave Norte (GA-FE-06)» | Área válida propia | 03,05,06 | baja lógica (`is_active=false`) |
| Área `GA6-AREA-A2` | Area | A (1) | «Nave Sur (GA-FE-06)» | Segunda opción de selector / no opción oculta | 03 | baja lógica |
| Área `GA6-AREA-XB` | Area | **B (3)** | «Área Del Sur (GA-FE-06)» | Inquilino ajeno: selector filtrado + API deny + sin persistencia | 06 | baja lógica |
| Lote `GA6-P10` | Lot | A | PLD hoy+10 · área A1 | Fuera de ventana SLA | 10 | documentar retención (histórico) |
| Lote `GA6-B3` | Lot | A | PLD hoy+3 · área A1 | **Frontera** ventana (entra) | 11 | íd. |
| Lote `GA6-I1` | Lot | A | PLD hoy+1 · área A2 | Dentro de ventana (entra) | 12 | íd. |
| Lote `GA6-NN` | Lot | A | PLD vacío (NULL) · área A1 | Opcionalidad real (no se inventa fecha) | 13 | íd. |
| Lote `GA6-PAST` | Lot | A | PLD hoy−1 | Exclusión de fecha pasada | extra | íd. |
| Rol R35/R36/R37 | Role | — | ver actor matrix | RBAC/CBU | 08,09 | eliminar o desactivar según contrato rol |
| Grants BU `broiler` | BusinessUnitGrant | C | broiler (ventana prueba) | Ventana operativa de C | 01…16 | revocar (usuario vuelve a 0) |
| BU estado | BusinessUnit | global | broiler ON durante pruebas | Habilitar la unidad | — | **restaurar las 4 en OFF** |

## Reglas

- Aislamiento: ningún fixture toca datos preexistentes; BUs de Empresa B intocadas (solo área XB para el cruce).
- Los lotes nacen por **flujo oficial**: E2E-01…07 los crean vía UI autenticada (ese es el objeto de la certificación: el alta real escribe PLD/área). Los lotes adicionales de borde (p.ej. PAST) pueden crearse por UI también — misma ruta, sin atajos SQL.
- Idempotencia: códigos `GA6-*` permiten detectar reejecuciones; si existieran de una corrida previa, se documenta y no se duplica.
- Escaneo SLA: el ciclo es **horario** (código); los fixtures con ventana se crean temprano y el aviso `lot_near_close` se relee al cierre de la tranche (ver `GA_FE_06_SLA_CONTRACT_MATRIX.md`, capa 3).
