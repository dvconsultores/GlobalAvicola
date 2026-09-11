# GA-UAT-07 · R-187 — LEDGER DE DATOS DE PRUEBA

Entorno: producción de prueba (empresa 1). Regla: ningún usuario humano modificado; actor 100 % sintético; mecanismos por API oficial; sin mutación directa de BD.

## 1 · Registros de la sesión UAT

| Alias | ID | Estado durante UAT | Propósito | Creación | Limpieza (tras decisión) | ¿Retenido? |
|---|---|---|---|---|---|---|
| Rol «R187 UAT» (permisos normales: ver lotes + ver reportes) | **71** | activo durante el UAT | operador normal para la validación del propietario | API oficial (201) | **desactivar** | No |
| Usuario `ra187uat` | **141** | activo durante el UAT (login 200) | camino realista del propietario (detalle/reporte/IPE) | API oficial (201) | **baja lógica** | No |
| Concesión `141 → broiler` | — | concedida (201) | acceso a la unidad productiva de los lotes | API oficial | **revocar** | No |
| Ventana BU `broiler` empresa 1 | — | **ON** durante el UAT | visibilidad productiva de los fixtures | API oficial (PATCH 200) | **restaurar OFF (4×OFF)** | estado original |
| Credencial temporal `~/ga_uat07_credentials.txt` (600) | — | vigente durante el UAT | acceso del propietario | archivo local **fuera del repositorio** | **destruir** | No |

## 2 · Fixtures de negocio usados (retenidos desde R-187; sin cambios hoy)

| Lote | Código | IPE visible | Banda | Uso en UAT |
|---|---|---|---|---|
| 54 | `L-R187-DET` | **333.3** | 🟢 | Primario (UAT-01/02/03/04/05) |
| 56 | `L-R187-MID` | **282.7** | 🟡 | Apoyo de clasificación (UAT-02 · C07) |
| 55 | `L-R187-LOW` | **241.1** | 🔴 | Contexto de banda baja (no imprescindible) |
| 11 | `L-BO-2026-05` | 5.6 | 🔴 | Contexto de transición de escala (no es objetivo) |

## 3 · Solo lectura / verificación

| Registro | Uso | Estado |
|---|---|---|
| Eventos 63/64/65 (DET) y 75/76 (B250) | verificación de estados `approved` | Intactos |
| Lotes 33/35 · 14 · 53 · área 16 | no usados hoy | Intactos |

## 4 · Higiene

- Sin usuarios humanos modificados (admin verificado operativo).
- Auditoría preservada (altas del UAT incluidas en el AuditLog del sistema).
- Sin residuo inseguro en el paquete commiteado: **0 passwords · 0 tokens · 0 cookies** (verificado por grep); credenciales solo fuera del repositorio y destruidas al cierre.
