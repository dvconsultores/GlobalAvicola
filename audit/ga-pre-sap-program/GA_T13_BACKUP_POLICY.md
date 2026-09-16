# GA · PRE-SAP — T13 · POLÍTICA DE RESPALDO Y RECUPERACIÓN (G-05)

Fecha: 2026-09-16 · Ámbito: entorno compartido `SHARED DEVELOPMENT / TEST /
CERTIFICATION / UAT` (`avicola.globaldv.net`) · Base: rehearsal real del
mecanismo (`evidence/t13-ops/g05-local-rehearsal.log`).

## Mecanismo canónico

```bash
pg_dump -Fc -d "$DATABASE_URL_SAFE" -f /backups/avicola_$(date -u +%Y%m%d_%H%M).dump   # formato custom comprimido
pg_restore --list <archivo>                                                             # legibilidad
createdb avicola_restore_check && pg_restore -d avicola_restore_check <archivo>         # restauración comprobada
# conteos de reconciliación: lots / operational_events / audit_logs (idénticos al original)
```

## Política

| Materia | Valor |
|---|---|
| **Obligatorio antes de cada `alembic upgrade`** | Sí — sin respaldo verificado no se ejecuta migración (criterio ya aplicado en el runbook de despliegue §5). |
| **Frecuencia operativa** | Diaria (ventana de baja actividad) + antes de cada release/migración. |
| **Retención** | 30 días rodantes + 1 copia mensual (12 meses). |
| **RPO (objetivo)** | ≤ 24 h para el entorno compartido. |
| **RTO (objetivo)** | ≤ 4 h (restauración completa verificada). |
| **Verificación de restauración** | Trimestral a base scratch con reconciliación de conteos clave; el rehearsal del 16-sep-2026 queda como primera verificación registrada del ciclo. |
| **Evidencia** | Referencia+timestamp+tamaño del dump y log de la restauración (sanitizado, sin DSN). |

## Nota de topología

La programación/ejecución periódica en el servidor es operación administrativa:
bajo la topología declarada (`SINGLE_DOCKER_COMPOSE_APPLICATION_RUNTIME`,
`HOST_INSPECTION_GATE = NOT_APPLICABLE_BY_OWNER_DECISION`) queda fuera del
modelo certificado; el **mecanismo** y su **restauración comprobada** sí están
certificados (G-05 = PASS en `GA_T13_HOST_GATES_RECONCILIATION.md`).
