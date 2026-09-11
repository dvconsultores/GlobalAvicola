# GA-BU-D10 · CERTIFICACIÓN (R-188 · OD-23 B)

Fecha: 2026-09-11 · Commits: C2 `0542310` · C3 `bee33f5` · C3b `399751c` · Evidencia: este hogar (`evidence/`).

```
R-188:
CLOSED

Technical:
FUNCTIONALLY_CERTIFIED

OD-23:
RATIFIED_IMPLEMENTED

OWNER_UAT_REQUIRED:
YES        (OD-23 = B cambia comportamiento visible de acceso productivo)

OWNER_UAT_READY:
YES        (guía GA_BU_D10_OWNER_UAT.md; ventana y actores por operaciones)

Owner acceptance:
PENDING    (no se auto-aprueba)
```

## Alcance certificado

- **Apagar termina**: concesiones vivas marcadas (`revoked_at`) + auditoría individual con causa; nada borrado; idempotente/normalizador.
- **Re-encender no devuelve** (B): histórico intacto, sin efectividad; concesión nueva explícita restaura (con auditoría).
- **Puertas preservadas**: conceder ≠ habilitar (409 con OFF), self-grant 403, cross-company 404, RBAC posterior (403), zero-BU sin dato, global sin evasión de OD-16 (404).
- **Sesión**: relectura por petición; sin privilegio obsoleto (OFF⇒DENY inmediato; ON⇒sigue DENY; regrant⇒ALLOW); refresh/relogin estables.
- **Historia/auditoría**: 6+1 filas para el operador; 23 eventos; 9 terminaciones con causa.
- **Datos**: sin migración, sin borrados masivos, sin retro-clasificación (prospectivo); transferencia de empresa intacta.

## Límites y declaraciones honestas

- Suites PG (incl. R-188) quedan `skipped` en local (declarado; corren en CI); la validación ejecutada de esta tranche es el **runtime autenticado** (API E2E + UI).
- Suites BU completas en local: resultados **idénticos** antes/después de C3 (artefactos sin PG; delta R-188 = 0).
- Transparencia: los reintentos del probe crearon **roles duplicados** (inactivos; documentados en el ledger); el hallazgo funcional de esos reintentos (probe mal condicionado) fue corregido en el guion, no en producto.
- Fixtures de lotes 54-59 intactos; actores y credenciales destruidos.

## No reapertura

OD-16 (absoluto) · OD-09.e (transferencia) · GA-FE-02..07 · R-181/182/184/185/186/187 · OD-21/22: **PRESERVED** (verificado sin superficies tocadas + spots runtime + IPE 333.3).
