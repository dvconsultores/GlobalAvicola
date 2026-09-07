# ADMINISTRACIÓN DE MÓDULOS: DÓNDE VIVIRÍA

Auditoría del 2026-09-07 · **propuesta de ubicación, no implementación**

---

## 1. Lo que ya existe y se reutilizaría

| Superficie | Dónde | Qué aporta |
|---|---|---|
| Maestro de empresas | `/masters/companies` · `MasterListPage` | el objeto que recibe los módulos |
| Administración de usuarios | `/users` · `UsersPage` | ya edita rol, empresa y área |
| Administración de roles | `/roles` · `RolesPage` (`GA-REM-034`) | patrón de matriz de casillas |
| Patrón de maestros | `MasterListPage` | lista, diálogo, vacío, carga, error |

`RolesPage` es el precedente más directo: ya resuelve «marcar capacidades de una entidad en una
matriz», que es exactamente la forma de este problema.

## 2. La matriz

| Superficie | Dónde iría | Actor | Estados que debe mostrar |
|---|---|---|---|
| **Módulos de la empresa** | ficha de empresa, pestaña o sección | administrador de plataforma | habilitado · deshabilitado |
| **Módulos del usuario** | `UsersPage`, junto a rol y área | administrador de empresa | concedido · no concedido · **concedido pero inactivo** |
| Módulos efectivos | solo lectura, en la ficha del usuario | cualquiera con `users:read` | la intersección |
| Menú de navegación | `App.tsx` · `navigationConfig.ts` | — | oculta lo no efectivo |

## 3. El estado que no se puede omitir

```
concedido al usuario  +  apagado en la empresa  =  «concedido, inactivo»
```

Si la interfaz solo muestra el efectivo, un administrador que vea la casilla vacía la marcará
otra vez sin entender por qué no sirve. Hay que mostrar los tres hechos.

## 4. Quién administra qué

Auditado sobre el catálogo real:

```
Super Administrador       sin empresa fija, control total    → candidato a administrar módulos DE EMPRESA
Administrador de Empresa  normativo en docs/02 §6.1          → candidato a conceder módulos A USUARIOS
                          PERO NO ESTÁ SEMBRADO
```

`docs/02 §6.1` enumera once roles y hay seis sembrados; `Administrador de Empresa` es uno de los
que faltan. Quién puede hacer cada cosa **no está definido** para esta capacidad:

```
OWNER DECISION REQUIRED
  · ¿quién asigna módulos a una empresa? ¿solo la plataforma?
  · ¿un administrador de empresa puede concederse módulos a sí mismo?
    (es la misma pregunta que OD-05, todavía abierta, en otra dimensión)
```

## 5. Lo que la interfaz nunca debe ser

```
frontend gating = experiencia
backend gating  = seguridad
```

Ocultar una entrada de menú no protege el endpoint. Esta matriz describe comodidad para el
administrador, no control de acceso.

## 6. Y una advertencia sobre rol como sustituto

Hoy no hay ninguna pantalla que use el rol como proxy de unidad de negocio — se comprobó. Cuando
se implemente, conviene que siga siendo así: el día que alguien cree un rol llamado
«Operador de Incubadora» y lo trate como si concediera la unidad, las dos dimensiones se habrán
fundido otra vez.
