# GA-BU-D10 · LEDGER DE DATOS DE PRUEBA

Entorno: producción de prueba (empresa 1). Regla: ningún humano modificado; actores 100 % sintéticos; mecanismos por API oficial; sin mutación directa de BD.

## 1 · Actores y accesos

| Registro | IDs | Estado final | Propósito | Limpieza |
|---|---|---|---|---|
| Roles «BU188 OP/ADM/ZBU/NR» | **72-75** (útiles) + 76-91 (duplicados por re-ejecución del script) | **20× desactivado (200)** | operador · Access Admin · zero-BU · RBAC-neg | desactivados |
| Usuarios `bu188op` / `bu188adm` / `bu188zero` / `bu188nr` | **142 / 143 / 144 / 145** | **baja lógica (204)** | batería E2E + UI | baja + concesión viva revocada |
| Concesiones `142→broiler` | 7 filas (6 terminadas por ciclos + 1 viva) | **viva revocada (200)** en cleanup | ciclo OD-23 | historia conservada |
| Concesión `145→broiler` | 1 fila (terminada por ciclo) | ya terminada (revoke 404 = sin viva) | RBAC-neg | historia conservada |
| Ventana BU broiler (empresa 1) | — | **OFF restaurada (4×OFF)** | ventana de certificación | OFF |
| Credencial `~/ga_bu10_credentials.txt` (600) | — | vigente durante la sesión | actores sintéticos | **destruida al cierre** |

Nota de higiene (transparencia): el aprovisionamiento tolerante a re-ejecución creó **roles duplicados** en las re-ejecuciones del probe (los POST repetidos no fallaron por nombre); todos quedaron **inactivos** y se documentan aquí. Los usuarios no se duplicaron (unicidad por username/email). Sin residuo activo.

## 2 · Datos usados en solo lectura (sin modificación)

| Registro | Uso | Estado |
|---|---|---|
| Lote 54 (`L-R187-DET`, IPE 333.3) | endpoint productivo testigo + UI | Intacto |
| Lote 14 (empresa 3) | cross-company (grant 404) | Intacto |
| Lotes 33/35/53/55/56/59 | no usados hoy | Intactos |

## 3 · Mecanismo y evidencia

- Todo por **API oficial** (roles/usuarios/concesiones/toggles) como autoridad con `switch-company`; batería documentada en `evidence/runtime-api.json`.
- **Auditoría preservada**: 23 eventos `user_business_unit` (9 terminaciones con causa declarada) + eventos `CONFIG_CHANGE` de cada apagado/encendido + altas/bajas del fixture.
- **Sin residuo inseguro**: credenciales y temporales destruidos al cierre; sesiones de sintéticos invalidadas por baja lógica.
- **Humanos**: no modificados (admin verificado operativo post-limpieza con `GET /roles` 200).
