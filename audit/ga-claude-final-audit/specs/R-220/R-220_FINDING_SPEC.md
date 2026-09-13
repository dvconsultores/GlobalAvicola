# R-220 · FINDING + SPEC (COMPACTO, ITEMIZADO) — RESIDUALES P3 DE CONTRATO, UX, MÓVIL, I18N Y RUTAS

| Campo | Valor |
|---|---|
| **ID** | **R-220** · P3 · **no bloquea** · Estado `SPEC_READY` (itemizado; puede ejecutarse por lotes) |
| **Origen** | C#17/18/25–37; B-17…B-41 (no cubiertos por otros paquetes); F (G-03/G-04/G-05/G-06/G-07/G-08/G-09/G-10/G-13/G-14/G-15/G-18/G-19) · Registro G-32 · HEAD `c0b4afc` · 2026-09-13 |
| **GA-REM** | a asignar; sin migración/permiso · UAT: no |

## 1 · Contexto

Residuales reales pero no bloqueantes de la auditoría **no** asignados a otros paquetes. Los que ya tienen hogar se citan como referencia (no se duplican): B-11/B-26/B-37 → R-206; B-22/B-33 → R-194; B-28 → R-195; B-36 → R-196; B-09/B-10/B-27 → R-209/R-217; C#27 `reversed` → R-207; C#36 → R-198; B-23/R-146; C#8/INT-19 → R-192; C#16 saldo visible → familia R-153/E-20.

## 2 · Inventario itemizado (a corregir en lotes)

### Lote A · Contrato de lectura/UX menor
| # | Ítem | Evidencia | Corrección esperada |
|---|---|---|---|
| A1 | Fechas sin zona: `start_date` ISO crudo; `new Date('YYYY-MM-DD')` localizado ⇒ −1 día en UTC−4 | C#17 (`MyPendingPage.tsx:102`, `TraceabilityTree.tsx:180…`, `LotListPage.tsx:88`, `LotDetailPage.tsx:342`) | formateador único (locale del app) |
| A2 | Lote 2 codificado en reportes | C#18 (`ReportsPage.tsx:13,193`) | selector real de lote |
| A3 | KPIs «Aprobados/Rechazados» del panel siempre 0 | C#25 (`ApprovalPanel.tsx:146,168`) | contar sobre datos reales o retirar |
| A4 | «Lote #» cuando `lot_id` nulo (importación) | C#26 (5 listados) | texto «Se creará al aprobar» (patrón del detalle) |
| A5 | `rule`/`reason` no mostrados (4xx de negocio) | C#28; `WeightEvaluation.tsx:84-91` | mostrar regla/motivo cuando exista |
| A6 | Detalle de operación omite campos (agua, cuadre, sanos/débiles, vacuna, params, inspecciones) | C#29 (`OperationDetailPage.tsx:196-258`) | render de los campos presentes |
| A7 | Notificaciones: 4 de 6 tipos sin texto; `lot`/`sap_payload` sin destino | C#32/INT-30 | textos por tipo; navegación |
| A8 | Listados sin paginar (users 20, audit 50, lots/operations 100 con filtro cliente) | C#33/INT-31 | paginación con `X-Total-Count`/`total` |
| A9 | Doble clic en Aprobar sin guarda | C#35 | deshabilitar durante la petición |
| A10 | `sap_reference` de `LotFormPage` descartado en silencio | B-18 | retirar campo o llevarlo al contrato (decisión) |
| A11 | `farm_id` obligatorio en UI para lotes incubadora | B-19 | alinear con esquema (opcional con contexto) |
| A12 | Ovoscopía pierde el «día» (`week_number` descartado) | B-20 | campo con camino a BE o retirar |
| A13 | `transport_inspection` filas vacías persistidas; `value_numeric` nunca | B-21 | serializador (clase F-01d) |
| A14 | `water_consumption` ausente de `ALL_EVENT_TYPES` | B-24 | añadir al enum informativo |
| A15 | `egg_classification` inalcanzable | B-25 | retirar del switch/catálogo o cablear |
| A16 | `birth_registration`: dosis/`mixed`+sexadas (UX) | B-35 | mensajes/validación cliente |
| A17 | `week_number`/`avg_weight` solo en fila 0 | B-38/B-39 | mover a fila única canónica |
| A18 | `egg_storage` sin lote ⇒ 500 por API | B-40 | validación 4xx (hardening) |
| A19 | Errores de lote solo en consola | B-41 (ver R-192 AC-04) | cubierto por R-192; verificar |
| A20 | `CorrectionForm` solo `observations`; `PUT /operations` sin UI | B-30/B-31/INT-09 | paquete de edición pendiente (citar; no aquí) |

### Lote B · Móvil / responsive / navegación
| # | Ítem | Evidencia | Corrección esperada |
|---|---|---|---|
| B1 | Web `<1024px` sin sidebar/barra/hamburguesa/logout | F G-03 (R1) | breakpoint/patrón de navegación |
| B2 | Móvil sin logout ni perfil | F G-04 (R2) | acciones en cabecera móvil |
| B3 | `/my-pending` huérfana | F G-05 | entrada de menú (móvil/operador) |
| B4 | `/reports/lot/:id` casi huérfana (enlace fijo a 2) | F G-18 | enlaces desde lotes/reportes (con A2) |
| B5 | `/operations` sin entrada de menú; sin activo | F G-19 | ítem «Historial»/activo |
| B6 | Tiles/timeline sin gate `operations:create` ⇒ callejón | F G-20 | gate |
| B7 | `/poultry` legacy coherente | F §2.b | mantener (compatibilidad); contador fijo «6» → dinámico |
| B8 | Panel de notificaciones recortado a 390px | F G-17 (R5) | anclaje/ancho |
| B9 | Botón eliminar máquina mal posicionado (absoluto sin ancestro) | F G-22 (R4) | `relative` en contenedor |
| B10 | Cosméticos R7–R12/R14/R15 (wraps, inputMode, chevron) | F §3 | lote cosmético |

### Lote C · I18N
| # | Ítem | Evidencia | Corrección esperada |
|---|---|---|---|
| C1 | Enumerados crudos en pantallas críticas (status/event_type/sex/egg_type) | F G-07 | `t()` en los 8 puntos listados |
| C2 | `audit.*`/`roles.*` namespaces vacíos | F G-08 (ver R-219 para audit) | claves (roles en su lote) |
| C3 | Validación zod de lote solo ES | F G-09 (`LotFormPage.tsx:21-23`) | claves i18n |
| C4 | 15 claves ausentes con fallback ES | F G-10 | claves en ambos idiomas |
| C5 | Errores backend ES para EN | F G-11 | aceptable (documentado) o mapeo futuro |
| C6 | `weight_deviation` sin clave; fechas locale navegador; `EQUIPMENT_TYPES`/export ES fijo | F G-12/G-13/G-14 | claves/formateador |
| C7 | Semántica divergente (`common.edit`→detalle, `common.back`→Anterior…) | F G-15 | claves correctas |
| C8 | Texto EN en bundle ES (2 claves) y unidades sueltas | F G-24 | corrección de copy |
| C9 | Latentes (flowDesc.bird_transfer, evidence types, NotificationType) | F G-25 | baja prioridad |

### Lote D · Código muerto / contratos obsoletos
| # | Ítem | Evidencia | Corrección esperada |
|---|---|---|---|
| D1 | `hooks/*` sin uso con contratos `{error}` obsoletos; `api.types.ts` | C#34 | retirar o alinear |
| D2 | `auth.service.UserResponse`, `lots.service.LotResponse.sap_reference`, `review.service` tipos laxos | C#34 | alinear tipos |
| D3 | `MobileDrawer`/`SidebarSubmenu`/drawer store sin montar | F G-28 | retirar o montar (ver B1) |
| D4 | Clase activa inválida `bg-white[0.12]`; clases residuales | F G-27 | fix utilidades |
| D5 | `ProtectedRoute.roles` muerto; `puede_cambiar/company_filter` legado | F G-26; D A.24 | retirar (D legado puede ir con R-201 C-05) |

## 3 · Secciones §47 (resumen)

- **Alcance**: los lotes A–D (FE principalmente; A14/A18 tocan BE menor). Cada ítem con su test de unidad/lectura; los ítems con paquete propio se verifican, no se reimplementan.
- **Fuera**: KPI Wave C (R-131…); R-150 completo; telemetría.
- **Contrato/Seguridad/BU**: sin cambios (los ítems A18/B6 endurecen UI/validación menor).
- **AC/cierre**: ver `R-220_AC_RED_E2E_UAT.md`. Ejecutable por lotes independientes.

## 4 · Dedup

Los ítems listados provienen de los informes B/C/F con su registro; los ya cubiertos se citan con su paquete. **Nuevo** como paquete contenedor (G-32).
