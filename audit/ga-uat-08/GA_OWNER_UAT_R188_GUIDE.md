# GA-UAT-08 · R-188 / BU-D10 / OD-23 — GUÍA DE UAT DEL PROPIETARIO

Valida **solo el comportamiento visible** de la política que usted ya aprobó (OD-23 = B). Tiempo estimado: 5 minutos. Sin conocimientos técnicos.

**Acceso preparado por operaciones** (actores temporales; contraseña entregada fuera del repositorio):
- Operador: `uat188op` · Administrador de accesos: `uat188adm` · Entorno: `https://avicola.globaldv.net`.

## Caso 1 (UAT-01) — Con acceso válido, el usuario trabaja normalmente

- **Qué mirar**: inicio de sesión como operador y abra sus lotes (p. ej. el lote de ejemplo `L-R187-DET`).
- **Qué debe ver**: el menú de trabajo (Lotes/Reportes) visible y el lote abierto con su tarjeta IPE normal (**333.3**). Sin errores.
- **Pregunta**: ¿El usuario con una concesión válida puede trabajar normalmente en la unidad habilitada?
- **Resultado**: PASE / PASE CON OBSERVACIÓN / FALLO

## Caso 2 (UAT-02) — Apagar la unidad quita el acceso

- **Qué ocurre**: operaciones **apaga la unidad «Engorde»** (mecanismo administrativo normal) **sin cerrar** la sesión del operador.
- **Qué debe ver el operador** (recargue): el menú de trabajo productivo **desaparece** y el lote deja de ser accesible. Sin errores crudos.
- **Pregunta**: ¿Al desactivar la unidad de negocio de la empresa, el usuario pierde el acceso productivo como corresponde?
- **Resultado**: PASE / OBSERVACIÓN / FALLO

## Caso 3 (UAT-03) — Volver a encender NO devuelve el acceso (caso central)

- **Qué ocurre**: operaciones **vuelve a encender «Engorde»** — **sin conceder nada a nadie**.
- **Qué debe ver el operador** (recargue): sigue **sin** menú productivo y **sin** acceso al lote. El acceso **no** reaparece solo.
- **Pregunta**: ¿Al volver a activar la unidad de negocio, el usuario permanece sin acceso hasta que se le conceda nuevamente de forma explícita?
- **Resultado**: PASE / OBSERVACIÓN / FALLO *(una reaparición automática = FALLO)*

## Caso 4 (UAT-04) — Una concesión nueva devuelve el acceso

- **Qué ocurre**: el **Administrador de accesos** entra en «Acceso por unidad», elige **Engorde** y pulsa **Conceder** para el operador (concesión nueva y explícita).
- **Qué debe ver el operador** (recargue o vuelva a entrar): el menú productivo **vuelve** y el lote se abre normalmente. No hace falta recrear usuarios ni roles.
- **Pregunta**: ¿Después de una nueva concesión explícita, el usuario recupera correctamente el acceso a la unidad?
- **Resultado**: PASE / OBSERVACIÓN / FALLO

## Caso 5 (UAT-05) — Móvil

- **Qué mirar**: el mismo operador desde el teléfono (o ventana estrecha): con acceso válido, el lote se ve legible; sin acceso, el menú productivo no aparece.
- **Pregunta**: ¿El comportamiento de acceso se refleja correctamente también en móvil?
- **Resultado**: PASE / OBSERVACIÓN / FALLO

---

**Su decisión (una sola)**:
**A)** ACEPTO R-188 / BU-D10 / OD-23 · **B)** ACEPTO … CON OBSERVACIONES: `<texto>` · **C)** RECHAZO … — CORREGIR: `<texto>`
