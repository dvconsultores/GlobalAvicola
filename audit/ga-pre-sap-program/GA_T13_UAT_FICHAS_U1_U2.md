# GA · PRE-SAP — T13 · FICHAS UAT U1 y U2 (OWNER ACTION REQUIRED)

Fecha: 2026-09-16 · Para: **el propietario** · Ejecución manual, sin
conocimientos técnicos. Las instrucciones están en lenguaje llano; lo que no se
vea en pantalla se marca como observación (la parte técnica la cubre la
ingeniería y no se le pide).

> **Paso 0 (prerrequisito de entorno)**: dirección de UAT —
> `https://avicola.globaldv.net`. Para que esta sesión valide el producto
> certificado (`be5453f`), el entorno debe estar actualizado a ese build **o**
> usted debe declararlo como entorno objetivo (ver `OWNER ACTION REQUIRED —
> despliegue`). Si no está actualizado, Wave C (U7) no podría validarse.

---

## FICHA U1 · Plataforma y seguridad

| Campo | Valor |
|---|---|
| **UAT ID** | U1 |
| **Proceso** | P-13 (plataforma/usuarios) + X-BU (alcance empresa/unidad) |
| **Objetivo** | Comprobar que el acceso se comporta: la sesión se cierra de verdad, cada rol ve lo suyo, y los datos de empresas distintas no se mezclan |
| **Usuario/Rol** | Su cuenta de administrador (si tiene más de una empresa disponible, mejor) |
| **Empresa** | La suya |
| **Business Unit** | Las de su cuenta |
| **Datos/fixture** | No hay que crear nada; se usan los usuarios y roles existentes |
| **URL inicial** | `https://avicola.globaldv.net` |

### PRECONDICIONES
1. Entorno de UAT en el build certificado (Paso 0) o entorno objetivo declarado.
2. Credenciales de su cuenta admin a mano (canal seguro).
3. Navegador habitual (Chrome/Edge). No se necesita ninguna herramienta.

### PASOS EXACTOS
1. Abra la dirección e **inicie sesión** con su cuenta de administrador.
2. En el menú superior (arriba a la derecha), elija **«Cerrar sesión»**.
3. Pulse **«Atrás»** en el navegador y haga clic en cualquier enlace interno
   (p. ej. «Lotes» o «Reportes»).
4. **Vuelva a iniciar sesión**.
5. Si su cuenta tiene más de una **empresa** disponible: use el **selector de
   empresa** (menú superior) para cambiar a la otra, abra «Lotes» o «Reportes»,
   y después regrese a su empresa original.
6. Abra **«Administración → Usuarios»** y revise los roles que se muestran.
7. Con la aplicación abierta, espere unos minutos y siga usando una pantalla
   (p. ej. Reportes).
8. (Si su pantalla lo permite) abra **«Administración → Roles»**.

### RESULTADO ESPERADO
1. Entra sin errores.
2. La sesión termina y la aplicación vuelve a la pantalla de acceso.
3. **Ninguna pantalla interna sigue operativa**: la aplicación le pide volver a entrar.
4. Entra de nuevo con normalidad.
5. Los datos mostrados son **los de la empresa seleccionada**, sin mezclarse; al
   volver, otra vez los de la original.
6. Cada usuario de empresa muestra un **rol concreto** (Operador, Contralor…);
   **ningún rol de empresa** muestra permiso «global»/comodín (ese alcance solo
   corresponde al super administrador).
7. Si la sesión «caduca», la aplicación se renueva sola o le pide entrar de
   nuevo — **nunca** muestra datos de otra empresa.
8. Los roles de su empresa listan permisos concretos, sin «todas las empresas».

### QUÉ DEBE MIRAR EL OWNER
- Que tras cerrar sesión **no quede nada utilizable** pulsando «Atrás».
- Que al cambiar de empresa **cambian los datos** y no se mezclan.
- Que los roles son «normales» (permisos concretos, sin comodines).

### EVIDENCIA A CAPTURAR
- Captura de la pantalla de acceso **después** de logout + «Atrás» + clic interno.
- Capturas de «Lotes»/«Reportes» en **cada empresa** (para comparar).
- Captura de «Usuarios» (roles visibles).
- Un nombre de archivo distinto por caso (con fecha/hora). Opcional: su
  veredicto por escrito/foto.

### VEREDICTO OWNER
```
[ ] PASS
[ ] PASS WITH OBSERVATIONS
[ ] FAIL
OBSERVACIONES: ___________________________________________
```

---

## FICHA U2 · Progenitoras — el lote de abuelas nace al aprobar (GA-UAT-09 retry)

| Campo | Valor |
|---|---|
| **UAT ID** | U2 |
| **Proceso** | P-01 (Progenitoras) · regla OD-25 · hallazgos R-153/R-189 |
| **Objetivo** | Comprobar en vivo la regla que usted aprobó: la importación **no** carga aves; el lote nace **al aprobar**; las aves entran con la **recepción** (♂40 + ♀60 ⇒ población 100) |
| **Usuario/Rol** | Operador de abuelas y aprobador habituales (los dos del archivo `~/ga_uat09_credentials.txt`) |
| **Empresa** | La del contexto preparado (empresa 1) |
| **Business Unit** | Progenitoras (habilitada) |
| **Datos/fixture** | Contexto ya preparado (unidad Progenitoras ON; OC `PO-C001-GPR-0001` disponible). Referencia de ingeniería del mismo recorrido (13-sep): **7/7 en verde** (`GA_OWNER_UAT_R153_RETRY_REFERENCE.md`) |
| **URL inicial** | `https://avicola.globaldv.net` |

### PRECONDICIONES
1. Entorno de UAT en el build certificado (Paso 0) o entorno objetivo declarado.
2. Archivo `~/ga_uat09_credentials.txt` a mano (operador y aprobador).
3. La unidad **Progenitoras** aparece habilitada; si no la ve, avise **antes**
   de empezar.

### PASOS EXACTOS
1. **(Operador)** Operaciones → Progenitoras – Cría → **Importación**: complete
   el plan (país, cantidades ♂/♀, fechas, proveedor, transporte, OC
   `PO-C001-GPR-0001`) y **deje el lote vacío**. **Guardar**.
2. Abra la importación guardada.
3. **(Aprobador)** Envíe a revisión y complete la aprobación.
4. Abra el **lote** creado (enlace en el detalle).
5. **Antes de recepcionar**: intente registrar una mortalidad mayor al saldo
   (p. ej. 100).
6. **(Operador)** Registre la **recepción** del lote (♂40 ♀60) y apruébela.
7. Vaya a **«Lotes»**.

### RESULTADO ESPERADO
1. Se guarda **sin error**; junto al selector aparece: «Si no selecciona un
   lote, se creará automáticamente al aprobar la importación.»
2. Muestra «Lote: **Se creará al aprobar**» — **no existe** ningún lote todavía.
3. Al aprobar aparece «Lote: **#N**» con **enlace** al lote.
4. El lote tiene: código de abuelas (`L-GP-{año}-{nn}`), tipo **abuela
   (grandparent)**, sexo mixto, fecha de inicio = **fecha de llegada**, y la
   granja/galpón de la importación — **sin aves cargadas**.
5. La mortalidad **se rechaza** (aún no hay aves).
6. Tras aprobar la recepción, el lote refleja la recepción **una sola vez** y su
   población es **100**.
7. «Nuevo lote» sigue disponible (la vía manual no se rompió).

### QUÉ DEBE MIRAR EL OWNER
- La **nota** junto al selector de lote en el paso 1.
- Que **no** exista lote antes de aprobar (paso 2) y que **nazca** al aprobar (paso 3).
- Que las aves **entren solo con la recepción** (paso 5 se rechaza; paso 6 ⇒ 100 exactos).
- Si algo difiere, anótelo **sobre el evento/lote afectado** para diagnóstico.

### DECISIÓN ADICIONAL EXIGIDA (en el veredicto)
La decisión debe cubrir **expresamente** los 3 momentos clave:
**C1** alta sin lote · **C2** «se creará al aprobar» · **C3** la aprobación crea
el lote. Además del veredicto por caso.

### EVIDENCIA A CAPTURAR
- Captura tras guardar (nota visible junto al selector de lote).
- Captura del detalle **antes** de aprobar («Se creará al aprobar»).
- Captura **después** de aprobar («Lote: #N» con enlace).
- Captura del lote (datos + sin aves) y de la recepción aprobada con **100**.
- Un nombre de archivo distinto por caso (con fecha/hora).

### VEREDICTO OWNER
```
[ ] PASS
[ ] PASS WITH OBSERVATIONS
[ ] FAIL
C1: ____  C2: ____  C3: ____
OBSERVACIONES: ___________________________________________
```

---

## Registro de cierre (ingeniería — lo rellena el equipo)

| Lote | Fecha/hora decisión | Canal | Texto exacto | Artefactos (nombre+sha256) | LOGIN/LOGOUT audit | Resultado por caso |
|---|---|---|---|---|---|---|
| U1 | | | | | | |
| U2 | | | | | | |

**No se marca ninguna aceptación sin su declaración explícita.** Al recibir sus
resultados: si U1 y U2 son PASS (o PASS con observaciones sin bloqueo), se
preparan automáticamente U3–U8 con este mismo formato.
