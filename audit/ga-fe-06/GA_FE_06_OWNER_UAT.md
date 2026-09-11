# GA-FE-06 · PAQUETE UAT DEL PROPIETARIO — R-182

Objetivo: que el propietario pueda **reproducir y aceptar** el arreglo sin conocimiento técnico previo. Duración estimada: 5–8 minutos.

## Guion reproducible

Cuenta de prueba (efímera): `ga6.operador` — credencial entregada por canal seguro (se destruye al cierre de la tranche).

1. **Alta con fecha prevista y área** (escritorio): entra en `https://avicola.globaldv.net/lots/new`.
   - Rellena Código (p.ej. `UAT-1`), Tipo = Engorde, Granja, **Área = Nave Norte (GA-FE-06)** y **Fecha prevista de cierre** (elige una fecha de, digamos, dentro de unos días).
   - Pulsa «Crear Lote» → debe aparecer «Lote creado exitosamente» y abrirse el detalle.
   - **Comprueba**: la tarjeta «Información» muestra **«Fecha prevista de cierre»** con el día que elegiste (sin desfase de un día).
2. **Opcionalidad**: repite el alta **sin** fecha ni área → se crea igualmente (no son obligatorias).
3. **Sin áreas ajenas**: en el desplegable «Área» solo aparecen áreas de tu empresa (las dos «Nave … (GA-FE-06)»). No aparece ninguna «Del Sur».
4. **Móvil** (opcional): repite el paso 1 en el teléfono (390×844): el selector y la fecha funcionan igual.
5. **Inglés** (opcional): cambia el idioma a EN en el encabezado → verás `PLANNED CLOSE DATE` y `Area`.

## Qué mirar para aceptar

- La fecha que tecleas es la que se guarda y la que se ve (mismo día).
- El área se elige por nombre, de una lista de tu empresa.
- Nada más cambia: los permisos siguen mandando (un usuario sin permiso de alta no puede crear; sin unidad operativa tampoco).

## Evidencia disponible (índice)

- `GA_FE_06_AUTHENTICATED_RUNTIME_EVIDENCE.md` — batería E2E-01…16 con valores reales.
- `GA_FE_06_SCREENSHOT_INDEX.md` — capturas (alta, detalle, RBAC, móvil, inglés).
- `GA_FE_06_NETWORK_EVIDENCE.md` — payload antes/después.
- `GA_FE_06_RED_EVIDENCE.md` — el defecto demostrado antes de corregir.
- `GA_FE_06_R182_CLOSURE_RECONCILIATION.md` — respuestas directas de cierre.

## Decisión solicitada

```
A) ACEPTO GA-FE-06 (R-182 cerrado)
B) ACEPTO CON RESERVAS (indicar cuáles)
C) NO ACEPTO (indicar qué falla)
```

Estado: **OWNER_ACCEPTANCE_PENDING** — a la espera de la decisión del propietario (no se inicia ninguna otra tranche).

---

# ADDENDUM GA-FE-06-A (2026-09-11) — READINESS

**OWNER_UAT_READY: NO** — suspendido hasta que la remediación de seguridad de área ajena (GA-FE-06-A) cierre y R-182 quede recertificado. La matriz de seguridad de área ajena es de ingeniería y no requiere repetición por el propietario; su UAT sigue enfocado en lo visible (cierre previsto, selección de área, alta, persistencia, móvil, ES/EN). Este documento se actualizará tras la recertificación técnica completa.

---

# CIERRE GA-UAT-04 (2026-09-11) — DECISIÓN DEL PROPIETARIO

**A) ACEPTO GA-FE-06** (explícita, 2026-09-11; sin observaciones adicionales del propietario).

| Campo | Estado final |
|---|---|
| GA-FE-06 | FUNCTIONALLY_CERTIFIED · **OWNER_ACCEPTED** |
| OWNER_ACCEPTANCE | **PASS** |
| R-182 | **CLOSED · OWNER_ACCEPTED** |
| OWNER_UAT_READY | YES (consumado) |

Registro: `audit/ga-uat-04/GA_OWNER_ACCEPTANCE_GA_FE_06_RECORD.md` · Observaciones aceptadas (UAT-01 descubrimiento de «Lotes» — candidato UX P2; UAT-06 área no visible en detalle; UAT-04 opción de área de baja lógica) en `audit/ga-uat-04/GA_OWNER_UAT_GA_FE_06_OBSERVATIONS.md`. Limpieza ejecutada y verificada (ver `GA_OWNER_UAT_GA_FE_06_EVIDENCE.md §F`). R-184 permanece SEPARATE_UNCHANGED.

**ACTUALIZACIÓN (2026-09-11, cierre GA-FE-06-A): `OWNER_UAT_READY = YES`.** La remediación pasó (backend `69d0c95`, runtime recertificado, R-182 CLOSED; ver `GA_FE_06_CERTIFICATION.md` §RE-VEREDICTO y `audit/ga-fe-06-a/`). El Owner UAT **no se ha ejecutado** en esta tranche y no se inicia aquí; queda listo para cuando el propietario lo ordene, con el foco visible ya descrito.
