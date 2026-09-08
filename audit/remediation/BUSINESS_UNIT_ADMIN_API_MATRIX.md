# MATRIZ DE LAS `API` DE ADMINISTRACIÓN POR UNIDAD DE NEGOCIO

`GA-REM-040` fase 7 · `T-040-18` · `T-040-19` · `OD-09.b` · 2026-09-08

```
ADMINISTRAR EL ACCESO   ≠   ACCEDER AL DATO
HABILITAR A LA EMPRESA  ≠   CONCEDER AL USUARIO
```

---

## 1. Las seis superficies

| `API` | Acción | Permiso exigido | Regla de inquilino | ¿El actor necesita la unidad concedida? | Auditoría | Prueba |
|---|---|---|---|---|:--:|---|
| `GET /business-units` | listar el catálogo con el estado de la empresa | `business_units:read` | empresa efectiva de `OD-11`; nunca otra | **no** | — | `el_listado_muestra_el_catalogo…` |
| `PATCH /business-units/{code}/enable` | habilitar | `business_units:update` | ídem; la fila se localiza por empresa + código | **no** | `CONFIG_CHANGE` · `CONFIG` | `habilitar_una_unidad_apagada…` |
| `PATCH /business-units/{code}/disable` | deshabilitar | `business_units:update` | ídem | **no** | `CONFIG_CHANGE` · `CONFIG` | `deshabilitar_apaga_la_unidad` |
| `GET /users/{user_id}/business-units` | listar concesiones | `business_units:read` | el objetivo debe ser de la empresa efectiva → `404` | **no** | — | `el_listado_separa_otorgada_de_efectiva` |
| `POST /users/{user_id}/business-units` | conceder | `business_units:create` | objetivo **y** habilitación de la empresa efectiva | **no** | `PERMISSION_CHANGE` · `USERS` | `conceder_una_unidad_habilitada` |
| `DELETE /users/{user_id}/business-units/{code}` | revocar | `business_units:delete` | ídem | **no** | `PERMISSION_CHANGE` · `USERS` | `revocar_retira_el_acceso…` |

Las seis declaran `response_model`. Ninguna acepta `company_id`, y ninguna acepta el
identificador de una habilitación: la unidad se nombra por **código** y la empresa se resuelve.

---

## 2. Por qué cuatro acciones y no una

```
business_units:update   contratar líneas          — decisión comercial
business_units:create   repartir accesos          — decisión operativa
business_units:delete   retirarlos
business_units:read     ver ambas cosas
```

Separadas para que se pueda autorizar a alguien a repartir acceso entre las cadenas ya
contratadas **sin** autorizarle a contratar cadenas nuevas. Son autoridades distintas porque
son decisiones de personas distintas.

---

## 3. Lo que ninguna de ellas hace

```
NO conceden unidades al actor            administrar no amplía el alcance propio
NO habilitan al conceder                 conceder no configura la empresa
NO conceden al habilitar                 habilitar no reparte
NO borran concesiones al deshabilitar    `AC-A04`; y por eso `BU-D10` sigue abierta
NO tocan RBAC, roles, lotes ni datos     `AC-B06`: unidad y permiso son dos cosas
NO miran el nombre del rol               `AC-F05`
```

---

## 4. Quién puede ejercerlas hoy

**Ningún rol sembrado.** Es `R-113`, y es una decisión de propietario, no un defecto: ninguna
de las cinco figuras del catálogo —Supervisor, Operador, Aprobador, Analista `SAP`, Auditor—
administra accesos, y darle `business_units:create` a cualquiera de ellas la convertiría en
alguien capaz de concederse las cuatro cadenas.

El permiso **es concedible** desde `/roles`: el catálogo lo declara. El valor por defecto es
cerrado, que es el lado correcto en el que equivocarse.
