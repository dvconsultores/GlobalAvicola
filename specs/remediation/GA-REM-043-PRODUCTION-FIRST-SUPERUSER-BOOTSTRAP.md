# GA-REM-043 — BOOTSTRAP PRODUCTIVO DEL PRIMER SUPERUSUARIO

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-043` · **Tipo** `SECURITY + DEPLOYMENT REMEDIATION SPEC` |
| **Prioridad** | **P0** |
| **Estado** | `SPEC_READY` |
| **Dependencias** | `GA-REM-004`, `GA-REM-012`, `GA-REM-025`, `OD-13`, `OD-14` |

## Problema

Una instalación nueva no crea usuarios durante el arranque: el entrypoint aplica migraciones y
levanta el proceso. El seed de baseline puede crear `admin`, pero también inserta empresas y otros
catálogos de certificación. Ejecutarlo en la primera instalación comercial fabricaría datos ajenos
al cliente. Tampoco existe una ruta pública de registro: sin un primer usuario con autoridad global
no puede usarse la administración autenticada.

## Decisión

Se incorpora una herramienta manual, de una sola finalidad, ejecutable dentro del contenedor
backend después de las migraciones. Crea exclusivamente:

1. el rol de sistema `Super Administrador` (`company_id IS NULL`);
2. un permiso comodín `("*", acción, scope_type="all")` por cada `PermissionAction` vigente;
3. un usuario activo `admin`, sin empresa fija, asociado a ese rol.

No crea empresas, fases, unidades de negocio, líneas genéticas, maestros, datos operativos, SAP,
fixtures ni cuentas adicionales. No se invoca desde el entrypoint ni desde el despliegue automático.

## Seguridad

- La contraseña llega únicamente por `GA_FIRST_SUPERUSER_PASSWORD`; nunca por argumento.
- Un wrapper interactivo la solicita dos veces sin eco y la inyecta solo al proceso ejecutado.
- La herramienta nunca imprime la contraseña, su hash ni el DSN.
- Política de bootstrap: mínimo 12 caracteres, mayúscula, minúscula, dígito y símbolo. Es más
  estricta que el mínimo general de 8 (`GA-REM-012`) por tratarse de autoridad global temporal.
- Si ya existe el username o el email del bootstrap, la ejecución falla sin modificarlo.
- Si el rol existe, debe ser rol de sistema. Sus permisos faltantes pueden reconciliarse; permisos
  ajenos no se eliminan y ninguna cuenta existente se altera.
- La operación es idempotente después del éxito: una repetición informa que el bootstrap ya fue
  aplicado y no escribe nada.

## Configuración de base de datos

La herramienta usa `app.database`, por lo que respeta exactamente la configuración de la aplicación:
`DATABASE_URL` cuando existe o, en su ausencia, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`,
`POSTGRES_USER` y `POSTGRES_PASSWORD` mediante `Settings`. No compone un DSN alternativo ni imprime
credenciales.

## Acceptance Criteria

| AC | Criterio |
|---|---|
| **AC01** | Sobre una base migrada sin `admin`, crea solo el rol global, sus comodines y el usuario `admin`. |
| **AC02** | El usuario queda activo, sin empresa, con contraseña hasheada y autenticable. |
| **AC03** | No inserta empresas ni datos de negocio/certificación. |
| **AC04** | Repetir tras éxito no duplica ni modifica registros. |
| **AC05** | Si `admin` o su email ya existen en estado incompatible, falla y no sobrescribe credenciales ni asignaciones. |
| **AC06** | Contraseña ausente o débil falla antes de escribir y nunca se registra. |
| **AC07** | La contraseña no se acepta por argumento de línea de comandos y el wrapper usa entrada oculta. |
| **AC08** | Usa la configuración real de `Settings`, compatible con `DATABASE_URL` y `POSTGRES_*`. |
| **AC09** | No modifica workflows, entrypoint, seeds de desarrollo/certificación ni despliegue automático. |

## Tests requeridos

- `T-043-01`: creación mínima y autenticación del admin.
- `T-043-02`: segunda ejecución idempotente.
- `T-043-03`: rechazo de username/email existentes incompatibles sin overwrite.
- `T-043-04`: validación de contraseña ausente/débil.
- `T-043-05`: prueba estática de ausencia de datos de certificación y argumentos de contraseña.
- `T-043-06`: sintaxis del wrapper y uso de lectura oculta.

## Operación

Debe ejecutarse explícitamente por un operador autorizado desde el host de despliegue mediante el
wrapper versionado. Después del primer login, la contraseña temporal se cambia por la interfaz/API
y se retira de la sesión del operador.

## Rollback

Antes del primer uso comercial, una ejecución equivocada puede revertirse eliminando únicamente el
usuario `admin`, sus permisos comodín y el rol si no tiene otras referencias. Después de uso real,
no se hace rollback destructivo: se rota o desactiva la cuenta mediante procedimientos autenticados.

## Definition of Done

- AC01–AC09 cubiertos por pruebas dirigidas.
- Script ejecutable y compatible con `docker compose -f avicola.yml exec`.
- Ningún secreto ni dato comercial/certificación agregado al repositorio.
