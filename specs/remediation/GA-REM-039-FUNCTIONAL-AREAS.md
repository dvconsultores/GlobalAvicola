# `GA-REM-039` · ÁREAS FUNCIONALES

| Campo | Valor |
|---|---|
| **ID** | `GA-REM-039` · `DOMAIN MODEL SPEC` |
| **Prioridad** | **P1** · **Estado** `SPEC_READY` |
| **Requisito** | `OD-08` · consumido por `docs/02 §3.14` |
| **Decisión** | **`OD-08`** — el área es dato maestro configurable por empresa |
| **Procesos** | `P-12` (maestro nuevo) · `P-13` (campo del usuario) · `P-14` (destinatarios) |
| **Dependencias** | `GA-REM-033` `CERTIFIED` (patrón de maestros) · `GA-REM-034` `CERTIFIED` (roles configurables) |
| **Antecedente** | `audit/remediation/P14_AREA_MODEL_MATRIX.md` |

---

## 1. Por qué existe, y por qué aparte

`OD-08` decidió que las notificaciones de `P-14` lleguen también al **gerente del área** y al
**supervisor del área**. El concepto de área no existe en el producto: ni tabla, ni relación con
el usuario, ni forma de que un evento sepa a qué área pertenece.

Se separa de `GA-REM-038` porque **no es de `P-14`**. Un maestro nuevo toca `P-12`, un campo en
el usuario toca `P-13`, y un campo en el lote toca `P-03` y `P-06`. `P-14` es su primer
consumidor, no su dueño.

## 2. Rol y área no son lo mismo

```
Role   qué PUEDE hacer el usuario
Area   dónde funcionalmente PERTENECE
```

Confundirlos —usar `role.name` como si dijera el área— haría que dos supervisores de áreas
distintas recibieran todo lo del otro. Son dos ejes y se modelan como dos.

## 3. El modelo

```
Area
    id
    company_id      FK companies       el área pertenece a una empresa
    name            str
    code            str?               como los otros maestros
    description     str?
    is_active       bool               baja lógica, nunca borrado
    created_at
```

```
users.area_id       FK areas, NULABLE  el área funcional del usuario
lots.area_id        FK areas, NULABLE  el ámbito del lote y de sus eventos
```

**Nulable en los dos casos, y es deliberado.** Existen usuarios y lotes anteriores a esta spec;
inventarles un área sería fabricar dato. Se completan desde la interfaz cuando corresponda.

**Sin `Area.manager_user_id`.** Guardar el gerente en el área **y** poder deducirlo del rol crea
dos fuentes que acabarán discrepando, sin regla de autoridad que las arbitre. La pertenencia
vive en el usuario y la capacidad en su rol:

```
GERENTE DEL ÁREA    = usuario activo · misma empresa · misma área · rol de gerencia
SUPERVISOR DEL ÁREA = usuarios activos · misma empresa · misma área · rol de supervisión
```

La relación con el área es **explícita** (`user.area_id`). El nombre del rol aporta la
capacidad, no el área: sin `area_id`, un usuario con rol de gerencia no es gerente de nada.

## 4. El rol de gerencia no se crea aquí

`docs/02 §6.1` enumera once roles y ninguno es de gerencia. `GA-REM-034` dio administración de
roles, de modo que la empresa que necesite uno lo crea como dato. El resolutor lo reconoce por
el nombre, igual que ya hace con administración, contraloría y supervisión, y si no existe **no
avisa a nadie por ese concepto y nada falla**.

Hardcodearlo en una migración sería inventar catálogo.

## 5. Cómo llega un evento a su área

Los seis eventos normativos de `P-14` convergen en el **lote**:

```
OperationalEvent → lot_id → Lot.area_id
SapPayload → ConsolidatedMovement → lot_id → Lot.area_id
Lot → directo
```

`Farm` no tiene área y no hay ningún otro contexto organizacional que reutilizar, así que el
vínculo va donde los seis lo alcanzan: **una columna en `lots`**, no una por tabla.

Un evento **sin lote** —las inspecciones de granja lo permiten desde `i9j0k1l2m3n4`— no resuelve
área. No es un error: se avisa a quien cargó el dato, a los administradores y a la contraloría,
y no al gerente ni al supervisor, porque no hay área que los identifique.

## 6. Lo que NO se modela

```
Department · Division · BusinessUnit · CostCenter · Region · Team
```

Ninguno. Ni jerarquía de áreas, ni áreas anidadas, ni áreas globales compartidas entre empresas.
Solo `Area`, con el alcance que `OD-08` necesita.

## 7. Criterios de aceptación

**`AC-A01`** · El área es dato maestro **configurable** y con alcance de empresa. Se crea, se
lee, se edita y se da de baja por la API, con el patrón de los otros maestros.

**`AC-A02`** · Los nombres de área **no** están codificados: ni enum, ni lista fija. No se
siembra ninguna.

**`AC-A03`** · Un usuario puede asignarse a un área, y puede no tenerla.

**`AC-A04`** · El gerente del área se resuelve de forma determinista: misma empresa, misma área,
rol de gerencia. Si no hay ninguno, el conjunto es vacío y nada falla.

**`AC-A05`** · Los supervisores del área se resuelven igual, y pueden ser varios.

**`AC-A06`** · Un usuario de otra empresa **nunca** se resuelve, aunque su área tenga el mismo
nombre.

**`AC-A07`** · Un usuario inactivo o un área inactiva no producen destinatarios.

**`AC-A08`** · Un usuario que cumple varias condiciones se deduplica.

**`AC-A09`** · El `Super Administrador` global —sin empresa— no se resuelve como destinatario de
ninguna empresa.

**`AC-A10`** · Se usa el área **del evento que originó el aviso**, no otra: un evento del área X
no alcanza al gerente del área Y de la misma empresa.

**`AC-A11`** · El área se administra desde la interfaz de maestros existente, y se asigna al
usuario desde la administración de usuarios existente. Sin módulo nuevo.

**`AC-A12`** · Aislamiento entre empresas en el maestro, con control y tratamiento.

**`AC-A13`** · Las pruebas satisfacen `GA-REM-016 AC13`.

## 8. Trazabilidad

| `AC` | Prueba | Nivel |
|---|---|---|
| `AC-A01`…`AC-A03`, `AC-A12` | `backend/tests/test_areas.py` | integración HTTP |
| `AC-A04`…`AC-A10` | `backend/tests/test_notification_recipients.py` | integración HTTP |
| `AC-A11` | `e2e/proceso-p14-notificaciones.spec.ts` | `UI_E2E` |
| `AC-A13` | informe de certificación | mutación |

## 9. Fuera de alcance

- **Jerarquía organizativa.** Solo `Area`.
- **Sembrar áreas.** Ninguna: los nombres los pone el cliente.
- **Rellenar retroactivamente** el área de usuarios o lotes existentes. No hay fuente segura y
  asignar «Supervisor → Producción» por su rol sería inventar dato.
- **Crear el rol de gerencia.** Lo crea la empresa con `GA-REM-034`.
- **Reabrir `P-12` o `P-13`.** Se les añade una entrada y un campo; su certificación se
  reverifica por regresión, no se rehace.

## 10. Definición de terminado

- `AC-A01`…`AC-A13` pasan.
- Migración con cabeza única, sin deriva, y con las tablas nuevas clasificadas para el baseline
  limpio (`T-025`).
- Legado nulable: ningún usuario ni lote existente recibe área inventada.
- Regresión completa de `P-12`, `P-13`, `P-03` y `P-06` sin fallos nuevos.
