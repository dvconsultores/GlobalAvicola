# `R-167` · MATRIZ DE EFECTOS DE LA MORTALIDAD AL ARRIBO

**WAVE B · tranche 8 · pre-flight** · 2026-09-10 · hallazgo registrado en el tranche 7 (`GA_REM_021_B01_RECEPTION_RECONCILIATION_MATRIX.md §7`, P3)
· pregunta: ¿el mismo hecho «aves muertas al arribo» puede afectar dos veces al saldo productivo?

## 1. Traza real (leída en el código, confirmada por prueba)

```
received_total (declarado) ─┐
dead_on_arrival (declarado) ─┼─ BR-20: received_total == Σ bird_movements.quantity + dead + rejected   (validators.py:420-455)
rejected_on_arrival (decl.) ─┘
Σ bird_movements.quantity = ALOJADAS ──► única entrada de la recepción al saldo (validators.get_current_bird_balance: BIRD_RECEPTION suma BirdMovement.quantity)
dead_on_arrival ──► NO se lee en ningún saldo, KPI, alerta ni evento derivado (grep app/: solo validators/service/schemas/models/corrections)
mortality_recording (evento aparte, §9) ──► descuenta Σ bird_movements.quantity una sola vez (_suma_neta, excluye CANCELLED)
```

| Campo / evento | Significado | Recurso | Cuándo | Estado exigido | Cantidad | Signo | ¿Afecta saldo? | Función | ¿KPI? | ¿Auditoría? | ¿Mismo hecho que la mortalidad al arribo? | ¿Duplica otro efecto? | Fuente | Semántica esperada |
|---|---|---|---|---|---|:--:|:--:|---|:--:|:--:|:--:|:--:|---|---|
| `received_total` | aves que llegaron | recepción (`bird_reception`, lote `breeder`) | alta / `PUT` | ≠ `CANCELLED` (no participa) | declarada | — | **no** | — | no (ola C) | sí (evento) | — | no | Rec. §6 | dato del cuadre |
| `dead_on_arrival` | muertas al llegar; nunca alojadas | recepción | alta / `PUT` | — | declarada | — | **no** | ninguna | no (ola C decidirá si cuenta en la tasa) | sí | **es** el hecho | **no**: no produce efecto productivo | Rec. §6 «Mortalidad al arribo» | descriptivo del cuadre |
| `rejected_on_arrival` | rechazadas; nunca alojadas | recepción | alta / `PUT` | — | declarada | — | **no** | ninguna | no | sí | no | no | Rec. §6 | descriptivo |
| Σ `bird_movements.quantity` | **alojadas** | recepción | alta | ≠ `CANCELLED` | por fila ♀/♂/galpón | **+** | **sí** | `get_current_bird_balance` | sí | sí | no | no | `R-130` · `RR-12` | entrada única |
| `mortality_recording` | aves alojadas que murieron | evento de mortalidad (§9) | posterior | ≠ `CANCELLED` | por fila | **−** | **sí** | `get_current_bird_balance` · `validate_mortality` (`BR-01`) | sí | sí | **otro hecho** (población ya alojada) | no: descuenta una vez | Rec. §9 · `R-130` | salida |
| contrapartida de reverso | neutraliza un aprobado | `reversals` | aprobación | `REVERSED` | copia del original | ∓ | sí | `_suma_neta` | — | sí | no | no (`OD-19`, exactamente una) | `GA-REM-041` | — |

## 2. Reproducción controlada (`tests/test_reception_reconciliation.py::test_r167_…`, verde = no reproducido)

```
recibidas 100 · muertas 5 · rechazadas 5 · alojadas 90        →  saldo 90 · 0 eventos de mortalidad creados · 0 alertas
PUT (recibidas 101 · muertas 6)                                 →  saldo 90 (las alojadas no cambiaron)
mortality_recording 5 (otro hecho)                              →  saldo 85 (una sola vez)
```

## 3. Clasificación

```
R-167 ............ NOT_REPRODUCED como defecto de código: no existe ninguna ruta que descuente dead_on_arrival del saldo,
                   ni el alta fabrica un evento de mortalidad. UN HECHO = UN EFECTO se cumple: las muertas al arribo tienen
                   efecto productivo CERO (nunca entraron) y las alojadas entran una vez.
residuo .......... riesgo de DOBLE CAPTURA por el operador (declarar dead_on_arrival y además registrar un mortality_recording
                   por las mismas aves). El sistema no puede distinguirlo de una mortalidad real del día 0 y ninguna fuente
                   autoriza una regla que lo impida (§9 admite mortalidad diaria desde el día 0). Es instrucción de proceso:
                   la mortalidad al arribo se declara en la recepción (Rec. §6) y no se repite como evento (§9).
docs/16:177 ...... la equivalencia «Mortalidad al arribo ✅ mortality_recording» era la elección de nivel 5 anterior a B01;
                   queda superada por GA-REM-021-B (RR-12). Se anota como corrección documental.
KPI .............. si las muertas al arribo cuentan en la «tasa de mortalidad» (Bases p.2: muertos / total al inicio) no lo
                   fija ninguna fuente: dependencia de GA-REM-022 (ola C). No se decide aquí.
severidad ........ P3 → NO DEFECTO (cerrado como no reproducido; nota de proceso + dependencia KPI). Sin cambio de código.
```

## 4. Corrección / concurrencia

La tupla del cuadre se edita atómicamente por `PUT` (`BR-20` revalida) y no es corregible uno a uno (`NO_CORREGIBLES_POR_IDENTIDAD`);
editar `dead_on_arrival` no altera las alojadas ni el saldo (prueba). Sin agregado compartido: sin carrera propia.
