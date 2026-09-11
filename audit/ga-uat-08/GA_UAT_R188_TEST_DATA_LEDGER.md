# GA-UAT-08 · R-188 — LEDGER DE DATOS DE PRUEBA

Entorno: producción de prueba (empresa 1). Regla: ningún humano modificado; actores sintéticos; mecanismos por API/UI oficiales.

## 1 · Registros de la sesión UAT

| Alias | IDs | Estado durante UAT | Propósito | Creación | Limpieza (tras decisión) | ¿Retenido? |
|---|---|---|---|---|---|---|
| Rol «UAT188 OP» (lotes+reportes) | **92** | activo | operador del camino visible | API oficial | desactivar | No |
| Rol «UAT188 ADM» (4 permisos administración de acceso) | **93** | activo | Access Administrator del regrant | API oficial | desactivar | No |
| Usuario `uat188op` | **146** | activo | operador (C01-C03, C05-C08) | API oficial | baja lógica | No |
| Usuario `uat188adm` | **147** | activo | regrant por UI (C04/C04b) | API oficial | baja lógica | No |
| Concesión `146→Engorde` (inicial, fresca) | fila 1 (terminada al apagar) | terminada por el ciclo | estado inicial UAT-01 | API (201) | — (historia) | Sí (historia) |
| Concesión `146→Engorde` (regrant UAT-04) | fila 2 | **viva y efectiva** al cierre del walkthrough | caso central del UAT | **UI real** (Acceder → Engorde → Conceder) | revocar | No |
| Ventana BU «Engorde» (empresa 1) | — | **ON** durante UAT | visibilidad del ciclo | API oficial | **restaurar OFF (4×OFF)** | estado original |
| Credencial `~/ga_uat08_credentials.txt` (600) | — | vigente durante UAT | acceso de los actores | archivo local fuera del repo | **destruir** | No |

## 2 · Solo lectura / verificación

| Registro | Uso | Estado |
|---|---|---|
| Lote 54 (`L-R187-DET`, IPE 333.3) | superficie productiva testigo (detalle y reporte) | Intacto |
| Demás lotes/concesiones | no usados | Intactos |

## 3 · Higiene

- Sin usuarios humanos modificados (admin verificado operativo).
- Auditoría preservada (altas + ciclo OFF/ON + terminación + regrant quedan registrados).
- Sin residuo inseguro: credenciales/temporales destruidos al cierre; sesiones de sintéticos invalidadas por baja lógica.
