# GA-FE-06 · CLARIFICACIONES (C01–C25)

Decisiones tomadas con evidencia canónica durante la reconciliación. Ninguna requirió interacción con el propietario (el encargo es autónomo).

| # | Pregunta de reconciliación | Decisión | Base |
|---|---|---|---|
| C01 | ¿El defecto R-182 es backend o frontend? | **Frontend**: pérdida silenciosa en el payload del alta | Lectura de `LotFormPage` + matrices |
| C02 | ¿Falta migración? | No: `o5p6q7r8s9t0` ya añade ambas columnas | Alembic + modelo |
| C03 | ¿Falta soporte backend en alta? | No: `LotBase` acepta ambos; servicio los aplica | `schemas.py`/`service.py` |
| C04 | ¿El control de fecha ya existía? | Sí (Input date), pero nunca se enviaba | Form |
| C05 | ¿Había control de área? | No; zod declaraba `area_id` sin UI (campo muerto) | Form |
| C06 | ¿El área es por finca o por empresa? | **Por empresa** (no existe `farm_id` en `Area`) ⇒ selector empresa, no cascada de finca | Modelo `Area` |
| C07 | ¿Área ajena debe filtrarse en selector? | Sí: fuente `/masters/areas` ya acotada al inquilino por el backend; se verifica en runtime | Permiso `masters:read` + experiencia E2E-06 |
| C08 | ¿Validación «área de la finca elegida»? | **N/A** — no existe vínculo área-finca; no se inventa | Modelo |
| C09 | ¿Área vs ventana operativa (BU)? | **N/A** — `Area` no tiene BU; sin acoplamiento | Modelo |
| C10 | ¿PLD obligatoria? | **No** — opcional; NULL válido y excluido del SLA por contrato | Schema + SLA |
| C11 | ¿Validar PLD > start_date? | **No** existe regla canónica; no se añade (prohibido inventar) | Búsqueda |
| C12 | ¿Zona horaria? | Día natural de negocio; backend normaliza a medianoche UTC (R-75); display por corte `slice(0,10)` | `_fecha_de_negocio` |
| C13 | ¿`area_id` visible en UI? | No mostrar IDs crudos; se muestra nombre en el selector; detalle conserva su tarjeta actual | UX existente |
| C14 | ¿Mostrar PLD en detalle? | **Sí, mínimo**: una fila «Cierre previsto» — cierra el contrato de lectura y es directamente verificable | Decisión de alcance mínimo |
| C15 | ¿Mostrar área en detalle? | No en esta tranche (evita rediseño); el contrato de lectura se prueba por fresh GET. Registrado | Alcance mínimo |
| C16 | ¿UI de edición de lote? | **No existe**; no se crea (expansión de alcance) — matriz UPDATE documenta | Matriz UPDATE |
| C17 | ¿`sap_reference`? | Observación separada; fuera de R-182; no tocado | Reconciliación |
| C18 | ¿Umbral SLA (3 días)? | Heredado del código vigente; no se modifica ni reinterpreta | `sla.py` |
| C19 | ¿Disparo SLA en runtime? | Ciclo interno horario (`3600 s`); sin endpoint manual. Certificación en 3 capas (datos/regla/oportunista) | `main.py`/`config.py` |
| C20 | ¿Lote cerrado en runtime? | No se fabrica cierre completo solo para el CASO; condición explícita y cubierta por suite canónica | Matriz SLA S6 |
| C21 | ¿Permisos nuevos? | Ninguno: el alta reutiliza `lots:create`/`masters:read` | GA-FE-04 |
| C22 | ¿BU para crear lote en fixtures? | Sí: ventana `broiler` ON durante prueba y restauración a OFF | CBU vigente |
| C23 | ¿Qué empresa para área ajena? | Empresa B (3) existente; jamás se crean áreas en A con sabor ajeno | Entorno |
| C24 | ¿Evidencia previa a la corrección? | Sí: RED en dos frentes (vitest + runtime pre-fix) — la tranche exige demostrar el defecto antes | Encargo §RED |
| C25 | ¿Qué NO se puede afirmar? | Nada de SLA runtime más allá de lo capturado; se declara `PENDING_SCAN_WINDOW` si el ciclo horario no corría | Honestidad de evidencia |
