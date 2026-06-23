# Estrategia de Auditoría — Global Avícola

> **Documento:** 13-audit-strategy.md
> **Versión:** 1.0.0
> **Fecha:** 2026-06-22

---

## 1. PRINCIPIO

> **Todo lo que ocurre en el sistema debe quedar registrado. Nada se borra. Todo se audita.**

La auditoría es un **requisito crítico y no negociable** de Global Avícola. Cada acción, por pequeña que sea, genera un registro inmutable con: quién, qué, cuándo, dónde, valor anterior, valor nuevo y motivo.

---

## 2. QUÉ SE AUDITA

### 2.1 Acciones auditadas

| Acción | Datos registrados |
|---|---|
| **Creación de registro** | Usuario, fecha/hora, entidad, valores iniciales |
| **Edición de registro** | Usuario, fecha/hora, campo modificado, valor anterior, valor nuevo |
| **Corrección en revisión** | Usuario corrector, fecha/hora, valor original, valor corregido, motivo, observación |
| **Revisión (visto bueno)** | Usuario revisor, fecha/hora, estado anterior → Revisado |
| **Aprobación** | Usuario aprobador, fecha/hora, estado anterior → Aprobado, resumen de datos |
| **Rechazo** | Usuario, fecha/hora, motivo (obligatorio), observaciones |
| **Devolución al operador** | Usuario, fecha/hora, observaciones para el operador |
| **Envío a SAP** | Usuario/proceso, fecha/hora, payload, identificador SAP |
| **Respuesta de SAP** | Fecha/hora, código de respuesta, mensaje, datos de respuesta |
| **Eliminación lógica** | Usuario, fecha/hora, motivo, registro completo antes de eliminar |
| **Anulación** | Usuario, fecha/hora, motivo, registro completo |
| **Login/Logout** | Usuario, fecha/hora, IP, dispositivo, éxito/fallo |
| **Cambio de permisos** | Usuario admin, fecha/hora, rol modificado, permisos anteriores/nuevos |
| **Activación manual de lote** | Usuario, fecha/hora, datos cargados, motivo |
| **Importación de datos SAP** | Usuario, fecha/hora, archivo/proceso, cantidad de registros |
| **Cambio de configuración** | Usuario, fecha/hora, parámetro, valor anterior, valor nuevo |

---

## 3. ESTRUCTURA DEL REGISTRO DE AUDITORÍA

```
AuditLog
├── id: UUID
├── company_id: FK → Company
├── user_id: FK → User (quién)
├── action: enum (qué acción)
├── entity_type: str (sobre qué entidad)
├── entity_id: UUID (identificador de la entidad)
├── lot_id: FK → Lot (contexto: lote)
├── farm_id: FK → Farm (contexto: granja)
├── house_id: FK → House (contexto: galpón)
├── module: str (en qué módulo)
├── previous_state: JSON (estado anterior)
├── new_state: JSON (estado nuevo)
├── previous_values: JSON (valores anteriores)
├── new_values: JSON (valores nuevos)
├── change_reason: str (motivo del cambio)
├── comments: str (observaciones)
├── sap_reference_id: FK → SapReference (doc SAP relacionado)
├── ip_address: str
├── user_agent: str
├── created_at: datetime (con microsegundos)
└── is_sensitive: bool (marca datos protegidos)
```

---

## 4. PRINCIPIOS DE AUDITORÍA

1. **Inmutabilidad:** Una vez creado, un AuditLog nunca se modifica ni se elimina.
2. **Automatismo:** La auditoría es automática. El desarrollador no decide qué auditar; el sistema audita todo.
3. **Contexto completo:** Cada registro incluye el contexto (lote, granja, galpón) para facilitar búsquedas.
4. **Corrección auditada:** Valor original + valor corregido siempre visibles.
5. **No repudio:** Las acciones no pueden negarse; el registro de auditoría es evidencia.
6. **Segregación:** Los registros de auditoría están en tabla separada (posiblemente particionada).

---

## 5. IMPLEMENTACIÓN TÉCNICA

### 5.1 Backend (FastAPI)

**Enfoque: SQLAlchemy Event Listeners**

```python
# Ejemplo conceptual
@event.listens_for(Session, "after_flush")
def audit_listener(session, flush_context):
    for change in session.new:
        if isinstance(change, AuditableMixin):
            create_audit_log(change, action="CREATED")
    for change in session.dirty:
        if isinstance(change, AuditableMixin):
            create_audit_log(change, action="UPDATED")
```

**Alternativa:** Middleware de FastAPI que intercepta requests y registra cambios.

### 5.2 Corrección Auditada

```python
class CorrectionService:
    def correct_event(self, event_id, field, new_value, corrected_by, reason):
        event = get_event(event_id)
        original_value = getattr(event, field)
        
        # 1. Guardar corrección
        correction = CorrectionLog(
            event_id=event_id,
            field_name=field,
            original_value=original_value,
            corrected_value=new_value,
            corrected_by=corrected_by,
            correction_reason=reason
        )
        
        # 2. Aplicar corrección
        setattr(event, field, new_value)
        
        # 3. Auditar
        audit_log = AuditLog(
            action="CORRECTED",
            previous_values={field: original_value},
            new_values={field: new_value},
            change_reason=reason
        )
        
        # 4. Todo en una transacción
        session.add_all([correction, audit_log])
        session.commit()
```

---

## 6. VISTA DE AUDITORÍA (UI)

### 6.1 Acceso
- **Roles autorizados:** Super Administrador, Administrador de Empresa, Auditor, Supervisor (solo sus granjas), Analista SAP (solo integración)
- **No autorizados:** Operadores, Consulta/Reportes (pueden ver su propio historial limitado)

### 6.2 Funcionalidades de la vista
- Búsqueda por: Usuario, Lote, Granja, Galpón, Fecha (rango), Tipo de acción, Módulo, Estado, Documento SAP
- Filtros combinables
- Ordenamiento cronológico (más reciente primero)
- Vista de detalle expandible con valores JSON formateados
- Comparación side-by-side de valor anterior vs nuevo
- Exportación a Excel/PDF
- Paginación

### 6.3 Vista de trazabilidad de un registro específico
- Línea de tiempo visual del registro:
  1. Creado por [Usuario] el [Fecha] [Hora]
  2. Enviado a revisión el [Fecha]
  3. Revisado por [Supervisor] el [Fecha]
  4. Corregido: campo [X] cambió de [A] a [B] por [Usuario] — Motivo: [...]
  5. Aprobado por [Aprobador] el [Fecha]
  6. Consolidado el [Fecha]
  7. Enviado a SAP el [Fecha] — ID SAP: [XXX]
  8. Confirmado por SAP el [Fecha]

---

## 7. RETENCIÓN DE DATOS DE AUDITORÍA

- **Período mínimo:** 7 años (cumplimiento fiscal/auditoría típico)
- **Estrategia:** Particionamiento por mes/año en PostgreSQL
- **Archive:** Posibilidad de mover particiones antiguas a almacenamiento frío
- **No se elimina:** Incluso después del período de retención, se prefiere anonimización a eliminación

---

## 8. SEGURIDAD DE LA AUDITORÍA

1. **Acceso restringido:** Solo roles autorizados pueden ver la auditoría completa
2. **Sin API de modificación:** No existe endpoint para modificar o eliminar AuditLog
3. **Sin API de eliminación:** No existe DELETE para AuditLog
4. **IP y User-Agent:** Registrados para trazabilidad forense
5. **Datos sensibles:** Campos marcados como `is_sensitive` pueden requerir permiso adicional
6. **Protección contra manipulación:** Hash encadenado opcional (similar a blockchain) para detectar alteraciones

---

## 9. PRUEBAS DE AUDITORÍA

| Prueba | Descripción |
|---|---|
| Creación de registro | Verificar que se genera AuditLog con action=CREATED |
| Edición de registro | Verificar previous_values y new_values |
| Corrección | Verificar que se conserva valor original y corregido |
| Aprobación | Verificar registro de quién aprobó y cuándo |
| Rechazo | Verificar que el motivo es obligatorio y queda registrado |
| Envío SAP | Verificar payload, respuesta y estado |
| Eliminación lógica | Verificar que no hay DELETE físico y se registra motivo |
| Inmutabilidad | Verificar que no se puede modificar un AuditLog existente |
| Permisos | Verificar que solo roles autorizados acceden a la auditoría |
