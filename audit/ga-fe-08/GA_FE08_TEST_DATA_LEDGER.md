# GA-FE-08 · LEDGER DE DATOS DE PRUEBA

Entorno: producción de prueba (empresa 1 «Avícola Global C.A.»). Regla: ningún humano modificado; actores sintéticos; mecanismos oficiales.

## 1 · Actores (creados 2026-09-11 por API oficial)

| Alias | IDs | Rol (id) | Permisos | Concesión | Vista | Propósito |
|---|---|---|---|---|---|---|
| A `fe08op` | user **148** | gaFe08-op (**94**) | dashboard:read · operations:read · lots:read | broiler (inicial, terminada por el ciclo OFF; **regrant fresco por UI** en E2E-05) | web | E2E-01/02/04/05/10 |
| F `fe08mob` | user **149** | gaFe08-op (94) | íd. | broiler (terminada por el ciclo OFF) | **mobile** | E2E-03 |
| B `fe08nob` | user **150** | gaFe08-op (94) | íd. | **ninguna** | web | E2E-06 (BU negativa) |
| C `fe08rbc` | user **151** | gaFe08-nolots (**95**) | dashboard:read · operations:read | broiler (terminada por el ciclo OFF) | web | E2E-07 (RBAC negativa) |
| D `fe08zbu` | user **152** | gaFe08-core (**96**) | dashboard:read | ninguna | web | E2E-08 (zero-BU) |
| E `fe08adm` | user **153** | gaFe08-adm (**97**) | business_units:read/update/create/delete | ninguna | web | E2E-09 (Access Admin) + regrant por UI |

Credencial efímera: `~/ga_fe08_credentials.txt` (600) — **destruida al cierre**.

## 2 · Estado del UAT

| Ítem | Antes | Durante | Al cierre (plan) |
|---|---|---|---|
| BU «Engorde» (empresa 1) | 4×OFF | **ON** (enable 200) | **OFF restaurada (verificar 4×OFF)** |
| Concesiones iniciales | — | op/mob/rbc → broiler (201) | revocadas/terminadas |
| Ciclo OD-23 en E2E | — | disable → grants terminadas → enable → sin regrant (histórico) → regrant UI | — |

## 3 · Datos de lectura

- Lotes existentes (L-R187-*, L-BO-*, etc.): solo lectura (lista/detalle). Sin mutación.
- Spot de inquilino: `/lots/999999` ⇒ 404 (sin fuga).

## 4 · Limpieza (al cierre)

Revocar/confirmar concesiones · baja lógica de usuarios 148-153 · desactivar roles 94-97 · **BU OFF** · verificar catálogo 4×OFF · destruir credenciales y `/tmp/ga08_*` · sesiones cerradas. Auditoría preservada; humanos intactos.
