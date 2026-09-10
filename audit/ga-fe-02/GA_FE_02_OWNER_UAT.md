# GA-FE-02 · UAT DEL PROPIETARIO (GUION DE ACEPTACIÓN)

**Estado**: `OWNER_ACCEPTANCE: PENDING` — el propietario valida este guion sobre el entorno
desplegado cuando lo estime. Este documento **no** se auto-declara aprobado (§165).
**Entorno**: `https://avicola.globaldv.net` (ENV-01). **Credenciales**: las del propietario /
cuentas de prueba autorizadas — no se incluyen aquí.

---

## Antes de empezar

- Cuenta sugerida: un actor con permiso de administración de unidades (el propietario o el
  Administrador de Accesos) **y**, si se quiere probar el efecto en un segundo usuario, una
  cuenta operativa de prueba.
- Estos pasos no modifican datos productivos reales: use la **empresa y unidades de prueba**
  acordadas; al terminar, deje la unidad de prueba como estaba.

## Guion

**1 · ¿Dónde veo en qué empresa estoy?**
Mire la esquina superior (escritorio) o la cabecera (móvil). Debe verse el nombre de la empresa
efectiva. Si su cuenta administra más de una empresa, ahí está el selector.

**2 · Cambiar de empresa (si le aplica).**
Abra el selector, elija otra empresa. La página se recarga con el contexto de la nueva empresa.
Vuelva a la original y compruebe que no se mezclan datos de la otra.

**3 · ¿Dónde se administran las unidades productivas?**
Menú **Administración → «Acceso por unidad»**. Deben aparecer las CUATRO unidades:
**Progenitoras, Reproductoras, Incubadora, Engorde** — cada una con su estado (Activa /
Inactiva) aunque alguna esté apagada.

**4 · Encender una unidad de prueba.**
Localice una unidad Inactiva de la empresa de prueba y actívela. Debe ver confirmación y, tras
refrescar la página (F5), la unidad sigue Activa. **Nota esperada**: al activar una unidad NADIE
recibe acceso — los usuarios siguen sin ella hasta que se les conceda (paso 6).

**5 · Apagar la misma unidad.**
Desactívela (le pedirá confirmación, con aviso si la acción es sensible). Tras refrescar, sigue
Inactiva. Vuelva a encenderla si su caso de prueba la necesita activa.

**6 · Conceder una unidad a un usuario de prueba.**
En la misma página, en la sección de concesiones de la unidad elegida, busque al usuario de
prueba y concédale la unidad. (También puede hacerse desde **Usuarios → fila del usuario →
«Unidades de negocio»**.) Debe ver la concesión reflejada al refrescar.

**7 · Comprobar el efecto en el segundo usuario.**
Con la cuenta del usuario de prueba: cierre sesión y entre de nuevo. Su sesión debe reflejar la
unidad concedida. Después revoque la unidad desde la cuenta administradora y repita la entrada:
la unidad deja de estar.

**8 · Ver los límites del Administrador de Accesos.**
Con la cuenta del Administrador de Accesos: puede administrar concesiones de OTROS usuarios de
su misma empresa, **no puede concederse a sí mismo** (no aparece su propia cuenta como
candidata) y **no ve** pantallas de operación productiva.

**9 · Confirmar en el móvil.**
Repita los pasos 3, 4 y 6 desde el teléfono (o ventana estrecha): todo debe ser utilizable sin
scroll horizontal y con botones alcanzables.

**10 · Deje la prueba limpia.**
Restaure la unidad de prueba al estado en que estaba y revoque la concesión concedida al usuario
de prueba.

---

## Qué observar y reportar

- Empresa efectiva visible y sin ambigüedad (pasos 1–2).
- Cuatro unidades SIEMPRE visibles, con estado real (paso 3).
- Encender/apagar persiste tras refrescar (pasos 4–5).
- **Encender no concede** y **conceder es un acto aparte** (pasos 4 y 6).
- Conceder/revocar se refleja en la sesión del usuario afectado (paso 7).
- El Administrador de Accesos reparte, no se sirve a sí mismo (paso 8).
- Móvil utilizable (paso 9).

Si algo no coincide con lo esperado: anote pantalla + paso + lo observado. No modifique datos
para "probar" otros caminos.
