# 07 — MAPA FUNCIONAL DEL SOFTWARE

Perspectiva de usuario. Estado: `COMPLETA` · `PARCIAL` · `ROTA` · `MOCK` · `NO IMPLEMENTADA` · `NO VERIFICABLE`.

```
GLOBAL AVÍCOLA
│
├── Seguridad y acceso
│   ├── Login usuario/contraseña ................................. COMPLETA
│   ├── Refresh automático de sesión ............................. PARCIAL  (pierde view_type/company_id/role_id)
│   ├── Cierre de sesión (cliente) ............................... PARCIAL  (sin revocación en servidor)
│   ├── Cambio de contraseña propia .............................. PARCIAL  (ProfilePage, sin verificar la actual)
│   ├── Selector de compañía (Super Admin) ....................... ROTA     (limit=200 → 422)
│   ├── Vista dual móvil / web (view_type) ....................... COMPLETA
│   ├── Control de acceso por rol ................................ NO IMPLEMENTADA
│   ├── Recuperación de contraseña ............................... NO IMPLEMENTADA
│   └── MFA ...................................................... NO IMPLEMENTADA
│
├── Gestión Avícola (operación de campo)
│   ├── Hub de procesos (6 etapas) ............................... COMPLETA
│   ├── Flujo por etapa con pasos numerados ...................... COMPLETA
│   ├── Formulario guiado de operación (25 tipos) ................ PARCIAL
│   │     ├── Selección Granja/Incubadora → Lote (SearchSelect) .. COMPLETA
│   │     ├── Secciones específicas por tipo de evento (25) ...... COMPLETA
│   │     ├── Indicadores de rango Ross/Cobb ..................... COMPLETA
│   │     ├── Inspección por galpón con equipos ................. COMPLETA
│   │     ├── Validación ±10 % contra orden SAP .................. PARCIAL  (solo texto en observaciones)
│   │     ├── Envío de sap_document_ref ......................... NO IMPLEMENTADA
│   │     └── Envío de idempotency_key .......................... NO IMPLEMENTADA
│   ├── Registrar mortalidad ..................................... ROTA     (HTTP 500)
│   ├── Listado de operaciones ................................... COMPLETA
│   ├── Detalle de operación + evidencias ........................ PARCIAL  (evidencias sin persistencia)
│   ├── Enviar a revisión / cancelar ............................. COMPLETA
│   └── Mis Pendientes (móvil) ................................... ROTA     (filtro de estado inválido)
│
├── Lotes
│   ├── Listado de lotes ......................................... COMPLETA
│   ├── Crear lote (solo web) .................................... COMPLETA
│   ├── Detalle de lote .......................................... ROTA
│   │     ├── KPIs del lote (IPE, uniformidad) .................. ROTA (arrastrada)
│   │     ├── Fases y transición Cría→Producción ................ ROTA (arrastrada)
│   │     ├── Cierre de lote ..................................... ROTA (arrastrada)
│   │     ├── Alertas del lote ................................... ROTA (arrastrada)
│   │     └── Árbol de trazabilidad generacional ................ ROTA (arrastrada)
│   ├── Trazabilidad automática entre generaciones ............... ROTA
│   ├── Enlace manual de generaciones ............................ PARCIAL  (funciona, pantalla inaccesible)
│   └── Activación manual / saldos iniciales ..................... NO IMPLEMENTADA (sin UI)
│
├── Revisión y aprobación
│   ├── Bandeja de revisión ...................................... PARCIAL  (pestañas de estado y filtro de operador inertes)
│   ├── Iniciar revisión ......................................... COMPLETA
│   ├── Devolver al operador ..................................... COMPLETA
│   ├── Completar revisión ....................................... PARCIAL  (aprueba sin validar segregación)
│   ├── Detalle de revisión ...................................... ROTA
│   ├── Formulario de corrección ................................. ROTA
│   ├── Corrección auditada (aplicar el valor) ................... NO IMPLEMENTADA
│   ├── Lotes de revisión (ReviewBatch) .......................... COMPLETA
│   ├── Panel de aprobación (individual y masiva) ................ COMPLETA
│   ├── Rechazo con motivo obligatorio ........................... COMPLETA
│   └── Configuración de niveles de aprobación ................... NO IMPLEMENTADA (sin UI, sin enforcement)
│
├── Integración SAP
│   ├── Listado de referencias SAP ............................... COMPLETA
│   ├── Importación de referencias (API) ......................... PARCIAL  (sin UI de carga)
│   ├── Consolidación de aprobados ............................... COMPLETA
│   ├── Exportación a SAP ........................................ PARCIAL  (adaptador manual, archivo efímero)
│   ├── Reintento de fallidos .................................... PARCIAL  (backoff defectuoso)
│   ├── Bitácora (jobs, payloads, errores) ....................... COMPLETA
│   ├── Chequeo de conexión ...................................... MOCK     (ManualSapAdapter devuelve siempre true)
│   ├── Adaptador SAP real ....................................... NO IMPLEMENTADA
│   └── Comparativo SAP vs App ................................... ROTA     (siempre vacío)
│
├── Auditoría
│   ├── Registro automático de eventos y transiciones ............ PARCIAL  (duplicado)
│   ├── Registro de correcciones y aprobaciones .................. PARCIAL  (duplicado)
│   ├── Registro de acciones de autenticación .................... NO IMPLEMENTADA
│   ├── Registro de cambios en maestros / permisos ............... NO IMPLEMENTADA
│   ├── Visor de auditoría ....................................... PARCIAL  (búsqueda y pestañas inertes)
│   └── Línea de tiempo por entidad .............................. COMPLETA (API); sin consumidor real
│
├── Reportes y KPIs
│   ├── 14 endpoints de KPI ...................................... PARCIAL  (4 huérfanos)
│   ├── Página de reportes con gráficas .......................... PARCIAL  (gráficas rotas, lote por ID numérico)
│   ├── Reporte por lote ......................................... PARCIAL
│   ├── Exportación Excel ........................................ COMPLETA
│   ├── Exportación PDF .......................................... COMPLETA
│   └── Comparativo SAP .......................................... ROTA
│
├── Dashboard
│   ├── Dashboard móvil del operador ............................. PARCIAL  (quick_actions con emojis y texto fijo en backend)
│   ├── Dashboard web ejecutivo .................................. PARCIAL
│   ├── Tendencia de mortalidad (8 semanas) ...................... COMPLETA
│   └── Alertas activas .......................................... PARCIAL  (dependen del generador roto)
│
├── Maestros
│   ├── 19 catálogos en API ...................................... PARCIAL  (15 sin PUT)
│   ├── 12 pantallas de catálogo ................................. PARCIAL
│   ├── Edición de catálogo ...................................... ROTA en 8 de 12 (405)
│   ├── Alta y baja lógica ....................................... COMPLETA
│   ├── Paginación / total ....................................... ROTA     (total = tamaño de página)
│   └── 7 catálogos sin pantalla ................................. NO IMPLEMENTADA
│
├── Administración
│   ├── Gestión de usuarios ...................................... ROTA
│   ├── Gestión de roles ......................................... NO IMPLEMENTADA (sin UI)
│   ├── Gestión de permisos ...................................... NO IMPLEMENTADA
│   └── Perfil propio ............................................ PARCIAL
│
├── Alertas y notificaciones
│   ├── Alerta de mortalidad alta ................................ ROTA
│   ├── Alerta de temperatura fuera de rango ..................... COMPLETA
│   ├── Alerta de humedad fuera de rango ......................... COMPLETA
│   ├── Resolución de alertas .................................... COMPLETA
│   ├── Alerta de peso fuera de curva ............................ NO IMPLEMENTADA
│   └── Notificaciones (email / push / Telegram) ................. NO IMPLEMENTADA
│
└── Canal Telegram
    ├── Bot con botón de Mini App ................................ COMPLETA
    ├── SDK en el frontend (back nativo, confirmación de cierre) . COMPLETA
    └── Autenticación por initData de Telegram ................... NO IMPLEMENTADA (login usuario/contraseña)
```

## Resumen del mapa funcional

| Estado | Nº de funcionalidades |
|---|---|
| COMPLETA | 33 |
| PARCIAL | 30 |
| ROTA | 16 |
| MOCK | 1 |
| NO IMPLEMENTADA | 18 |
| **Total** | **98** |

## Módulos completos / parciales / rotos

| Módulo | Estado funcional | Comentario |
|---|---|---|
| Canal Telegram | **VERDE** | cumple su objetivo (lanzador); sin spec |
| Internacionalización | **VERDE** | 865/865 claves, paridad total |
| Operaciones (captura) | **AMARILLO** | 24 de 25 tipos operan; mortalidad rota |
| Revisión y aprobación | **AMARILLO** | núcleo correcto; corrección y detalle rotos |
| Maestros | **AMARILLO** | 12/19 con UI; edición rota en 8 |
| Reportes / KPIs | **AMARILLO** | cálculos correctos; UI degradada |
| Dashboard | **AMARILLO** | funciona; contenido con deuda |
| Auditoría | **AMARILLO** | registra, pero duplicado y con cobertura parcial |
| Lotes | **ROJO** | pantalla central rota; activación manual sin UI |
| Integración SAP | **ROJO** | sin adaptador real, activada en producción |
| Seguridad / RBAC | **ROJO** | modelo sin enforcement; escalada por refresh |
| Administración (usuarios/roles) | **ROJO** | pantalla rota; roles y permisos sin UI |
| Trazabilidad generacional | **ROJO** | auto-creación defectuosa |
| Notificaciones | **ROJO** | no implementado |
