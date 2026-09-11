# GA-FE-03 · UAT DEL PROPIETARIO

**Estado**: `OWNER_UAT_READY = YES` · `OWNER_ACCEPTANCE = PENDING`.
El agente **no** se auto-aprueba. El propietario valida en `https://avicola.globaldv.net`.

## Guion de validación (15–20 min)

1. **Entrar como usuario normal (una unidad concedida)** — p. ej. una cuenta operativa de
   Posadas: el menú debe mostrar solo las áreas de su operación (Gestión Avícola con **su**
   unidad), y no Auditoría/Maestros/Usuarios/SAP. ¿Se entiende «qué puedo hacer aquí»?
2. **Entrar con un usuario sin unidades** — debe usar Inicio/KPI/perfil con normalidad, **sin
   menús vacíos** ni mensajes de error al entrar.
3. **Administrador de Accesos** — debe encontrar «Acceso por unidad» por sí solo (Configuración
   → hub) y poder conceder/revocar; no debe ver pantallas de producción.
4. **Administrador de unidades de empresa** — debe encontrar la misma superficie y habilitar/
   deshabilitar unidades; los usuarios operativos no deben ver nada hasta que exista, además,
   una concesión.
5. **Apagar una unidad de la empresa** — la operación productiva de esa unidad desaparece del
   menú de todos (incluida la autoridad global); volver a encenderla no concede accesos por sí
   sola.
6. **Cambiar de empresa (Super Admin)** — el menú se recalcula al instante y sobrevive a un
   refresco; sin restos de la empresa anterior.
7. **Móvil (390 px)** — los mismos actores ven el mismo menú semántico; nada fuera de pantalla.
8. **ES/EN** — las etiquetas del menú/administración se traducen completas.

## Preguntas concretas al propietario

```
U1  ¿El criterio «ocultar cuando no se puede operar» (vs. mostrarlo deshabilitado) es el
    correcto para su operación?         [SÍ / NO / AJUSTAR — anotar]
U2  ¿La unidad «apagada» debe explicarse en alguna pantalla al usuario operativo, o la
    desaparición silenciosa es suficiente?
U3  ¿La pantalla de Concesiones debe mostrar también las unidades apagadas de la empresa
    al administrador de accesos (hoy solo actúa sobre habilitadas)?
U4  ¿El rol «Acceso por unidad» debe ser descubrible también desde móvil en el futuro?
    (hoy las superficies de control son web por diseño)
U5  ¿Aprueba GA-FE-02 (pendiente) antes de la próxima tanda, o mantiene ambas
    aceptaciones abiertas?
```

**Política ratificada por el propietario**: NINGUNA (`OWNER_RATIFIED_POLICY: NONE`).
`BU-D10` sigue `PENDING_RATIFICATION` y **no** se convirtió en política por esta tranche.
