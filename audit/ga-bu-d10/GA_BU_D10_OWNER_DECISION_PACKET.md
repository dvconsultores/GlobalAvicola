# GA-BU-D10 · PAQUETE DE DECISIÓN DEL PROPIETARIO

## LA PREGUNTA

**Cuando una empresa apaga una unidad de negocio (una línea) y más tarde la vuelve a encender, ¿las concesiones de usuario que ya existían vuelven a ser efectivas automáticamente, o cada usuario necesita una concesión nueva y explícita?**

Es el mismo negocio, el mismo usuario y la misma unidad — **no** es un cambio de empresa.

## QUÉ HACE HOY EL PRODUCTO (comportamiento provisional)

1. La empresa **apaga** la línea → nadie opera esa línea (ni el administrador global).
2. La concesión del usuario **no se borra**: queda guardada como historial («apagar no revoca»).
3. La empresa **vuelve a encender** la línea → las concesiones previas **vuelven a ser efectivas solas**: los usuarios que ya la tenían recuperan el acceso **sin que nadie vuelva a conceder nada**.

Este comportamiento está documentado como **provisional** desde el diseño original y **nunca fue ratificado**. La decisión es suya; el código no la tomó por usted (por eso apagar es reversible y no borra nada).

## POR QUÉ IMPORTA

- **Seguridad**: ¿una línea que estuvo cerrada (¿meses?) debe reabrir con los accesos de ayer, aunque las personas y los cargos hayan cambiado?
- **Auditoría**: ¿debe poder responderse «quién autorizó este acceso cuando se reabrió la línea»?
- **Operación**: ¿reabrir debe ser «encender y listo», o «encender y reasignar a quién le corresponde»?

## OPCIÓN A — LA CONCESIÓN HISTÓRICA VUELVE (persistente)

- Al re-encender, las concesiones previas **recuperan efecto automáticamente**. No hace falta ninguna acción por usuario.
- **Seguridad**: reingreso automático de los usuarios autorizados en el pasado.
- **Operación**: reapertura simple.
- **Auditoría**: el encendido de la línea queda registrado como la causa del cambio de acceso; no se fabrican concesiones nuevas (correcto: nadie concedió nada).
- **Datos**: cero cambios.
- **Es lo que el producto hace hoy** (y sería una reconciliación sin desarrollo).

## OPCIÓN B — CADA USUARIO REQUIERE UNA CONCESIÓN NUEVA (re-autorización)

- Al re-encender, **nadie recupera acceso solo**; un administrador de accesos debe volver a conceder la unidad a cada usuario que deba operarla.
- **Seguridad**: mínimo privilegio; sin «resurrección silenciosa» de accesos productivos.
- **Operación**: la reapertura exige reasignar; el flujo ya existe (candidatos → conceder) y no requiere permisos nuevos.
- **Auditoría**: cada reingreso tiene un acto explícito de concesión (quién, a quién, cuándo). El historial de las concesiones antiguas se conserva, marcado como terminado.
- **Datos**: no se borra nada; las concesiones antiguas quedan como historia.
- **Coherencia**: es la misma lógica que ya rige cuando alguien cambia de empresa (al volver, se le debe conceder de nuevo — regla vigente y aceptada).

## RECOMENDACIÓN (re-evaluada con la evidencia del repositorio)

**Opción B.** Motivos, en orden de peso:
1. **Coherencia con un precedente ya ratificado**: para el cambio de empresa (OD-09.e) el producto ya decidió que «volver no prueba el mismo cargo ni la misma necesidad operativa» — reabrir una línea es el mismo problema de fondo (el tiempo pasó, el equipo pudo cambiar).
2. **Los dos conceptos que ya separamos siguen separados**: habilitar una línea (decisión comercial) **no** es lo mismo que conceder acceso a personas (decisión operativa). B honra esa frontera también al reabrir.
3. **Auditoría**: cada acceso productivo renovado nace de un acto explícito y registrado.
4. **Mínimo privilegio** como postura por defecto del producto.
A es la conducta actual y **cuesta cero**; si su prioridad es continuidad operativa, A es una elección legítima — no hay un argumento de corrección técnica que la invalide. **La recomendación no es la decisión.**

## SU ELECCIÓN

**A)** AL REACTIVAR UNA BU DE EMPRESA, LOS GRANTS HISTÓRICOS DE LOS USUARIOS VUELVEN A SER EFECTIVOS AUTOMÁTICAMENTE.
**B)** AL REACTIVAR UNA BU DE EMPRESA, NINGÚN GRANT HISTÓRICO VUELVE A SER EFECTIVO; CADA USUARIO REQUIERE UNA NUEVA CONCESIÓN EXPLÍCITA.

**DECISIÓN DEL PROPIETARIO: — PENDIENTE —**

---
*Apéndices técnicos*: `GA_BU_D10_SOURCE_RECONSTRUCTION.md` · `GA_BU_D10_DATA_MODEL_TRACE.md` · `GA_BU_D10_EFFECTIVE_ACCESS_TRACE.md` · `GA_BU_D10_COMPANY_TOGGLE_TRACE.md` · `GA_BU_D10_USER_GRANT_TRACE.md` · `GA_BU_D10_DEDUP_REPORT.md` · `GA_BU_D10_DECISION_IMPACT_MATRIX.md` · `GA_BU_D10_TRACEABILITY.md`.
