# GA-FE-07 · OWNER UAT — READINESS (sesión corta)

```
OWNER_UAT_READY: YES
GA-FE-07: FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING
R-185: CLOSED (técnico) — aceptación del propietario pendiente
```

## Qué valida el propietario (5 comprobaciones visibles, ~5 minutos)

1. **Área inactiva no se ofrece**: al crear un lote nuevo, el selector de Área **no** muestra áreas retiradas (solo activas de la empresa).
2. **Área activa sí aparece**: las áreas vigentes siguen seleccionables y el alta funciona como siempre.
3. **La historia se conserva**: un lote que ya tenía un área que después se retiró **sigue mostrando/leyendo su referencia** — nada se borra.
4. **Editar sin tocar el área no falla**: una edición permitida de ese lote histórico (p. ej. cambiar la fecha prevista de cierre) **no** se bloquea por tener un área retirada.
5. **Móvil**: mismo comportamiento que en escritorio.

## Qué NO repite

- Ataques directos por API, matrices de seguridad/inquilinio, BU/RBAC: certificación de ingeniería (ya ejecutada).
- El aviso SLA horario (mecanismo interno; UAT-11 ya N/A).

## Frase de decisión (cuando se convoque)

```
A) ACEPTO GA-FE-07
B) ACEPTO GA-FE-07 CON OBSERVACIONES: <texto>
C) RECHAZO GA-FE-07 — CORREGIR: <texto>
```

Estado ahora: **esperando convocatoria** (no se inicia otra tranche).
