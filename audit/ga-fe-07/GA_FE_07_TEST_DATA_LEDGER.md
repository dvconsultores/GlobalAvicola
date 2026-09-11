# GA-FE-07 · LEDGER DE DATOS DE PRUEBA

## Identidades (todas efímeras; retiradas tras la certificación)

| Recurso | ID | Nombre | Estado final |
|---|---|---|---|
| Rol | 57 | «Operador Lotes GA-FE-07» | **desactivado** |
| Rol | 58 | «Solo-lectura GA-FE-07» | **desactivado** |
| Usuario C2 | 124 | `ga7.operador` (concesión broiler) | **baja lógica** (204) + concesión **revocada** |
| Usuario G2 | 125 | `ga7.sinventana` | **baja lógica** |
| Usuario H2 | 126 | `ga7.rbac` | **baja lógica** |
| Credenciales | — | `~/ga7_credentials.txt` · tokens `/tmp/ga7_*` | **destruidos** (verificado) |

## Áreas (todas `GA7-*`; baja lógica = estado retenido/restaurado)

| ID | Código | Rol en la tranche | Estado final |
|---|---|---|---|
| 6 | `GA7-AREA-ACTIVA` | Control activo (RED + E2E) | **baja lógica** (restaurado) |
| 7 | `GA7-AREA-HIST` | Fixture histórica del RED (lote 39/40/41/probes) | **baja lógica** (evidencia: referencias históricas retenidas) |
| 8 | `GA7-AREA-INACT2` | Destino inactivo (H3) | baja lógica (nunca referenciada) |
| 9/10 | `GA7-AREA-RACE-…` | Carrera de baja (2 corridas) | baja lógica |
| 11 | `GA7-ACTA-155019ujgc` | Área activa de la corrida final | **baja lógica** (restaurado) |
| 12 | `GA7-HSTA-155019ujgc` | Fixture histórica de la corrida final (lote 48) | **baja lógica** (referencia histórica retenida) |
| 5 | `GA6-AREA-XB` (empresa 3) | Regresión de área ajena (reactivada temporalmente) | **restaurada a baja lógica** (estado de entrada) |

## Lotes (retenidos como histórico del producto — sin borrado canónico)

39 `GA7-HIST-01` · 40 `GA7-ACT-02` · 41 `GA7-RED-INACT-01` · 42 `GA7-NULL-01` · 43/44 `GA7-PROBE-2/3` (sondas de despliegue con área 7, aceptadas por el backend pre-fix) · 45–47 `GA7-GREEN-*` (corrida interrumpida) · 48 `GA7-HIST2-155019ujgc` (fixture final; **ahora referencia el área activa 11** tras E2E-07) · 49 `GA7-ACT-155019ujgc` (control activo final) · denegados (`GA7-INACT-*`, `GA7-RACE-*`, `GA7-FOREIGN-*`, etc.): **sin persistencia** (verificado).

## Estado del entorno al cierre

- BU empresa 1: **4×OFF** (restaurado). · Usuarios/roles de prueba: inoperantes. · Credenciales/tokens: destruidos.
- Auditoría: **preservada** (sin borrados). · Humanos: **intactos** (solo DeepSeek creó/retiró fixtures). · Rol 35 y registros GA-FE-02..06: intactos.
