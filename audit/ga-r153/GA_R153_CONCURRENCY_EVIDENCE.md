# GA-R153 · EVIDENCIA DE CONCURRENCIA Y SECUENCIA

Fecha: 2026-09-12.

## 1 · Diseño (implementado)

```
aprobación (P-07)                    ── dos aprobadores a la vez ⇒ serializa `_get_event_for_approval`
                                        (SELECT … FOR UPDATE); el segundo recibe 400 «no aprobable» y
                                        NO crea lote (AC23/26 de la suite).
creación del lote                    ── pg_advisory_xact_lock(hashtext('lote-gp:{empresa}:{año}'))
                                        «un solo lote por empresa/año se numera a la vez».
colisión real (unicidad GLOBAL)      ── savepoint (begin_nested) + hasta 3 reintentos contra el
                                        máximo global bajo lock 'lote-gp:{año}:global'.
fallo del lote (p.ej. plan ilegible) ── BR-22 → revierte la transacción entera: ni aprobación sin
                                        lote ni lote sin aprobación (AC31/32).
```

## 2 · Cobertura

- CI (declarada local, PG no disponible): `test_r153_import_lot_auto.py` — AC23/26 (doble aprobación), AC27 (legado), AC09/10 (secuencia 01→02 por empresa/año), AC31/32 (atomicidad).
- Runtime: no se ejerció concurrencia multi-proceso en producción (fuera del alcance del ejercicio; una única aprobación por evento en el E2E). La primitiva es la misma que ya usa el sistema (`R-130`, `GA-REM-040-H`), sin migración.

## 3 · Trazabilidad del código

`lots/service.py`: `_bloquear_secuencia` (solo PostgreSQL), `_siguiente_codigo_de_lote_gp`, bucle `for intento in range(4)` con `begin_nested()`; clave de lock estable por empresa/año y clave global para el reintento.
