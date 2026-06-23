# Auditoría de Repositorios Legacy — Global Avícola

> **Fecha de auditoría:** 2026-06-22
> **Equipo auditor:** Product Manager Senior, Arquitecto de Software, Tech Lead Backend, Tech Lead Frontend, Analista Funcional Avícola
> **Versión:** 1.0.0

---

## 1. RESUMEN EJECUTIVO DEL SISTEMA ANTERIOR

El sistema legacy **"Lider Pollo"** es una aplicación de gestión avícola compuesta por tres repositorios:

| Repositorio | Tecnología | Rol |
|---|---|---|
| `app_liderpollo` | **Flutter 3.16 / Dart 3.2** | App móvil multiplataforma (Android, iOS, Web, Windows) |
| `app_liderpollo_fronend` | **Vue 3 / Vite / Vuetify 3 / TypeScript** | Frontend web administrativo |
| `app_liderpollo_backend` | **Node.js / Express / TypeScript / TypeORM** | Backend API REST |

El sistema cubre el ciclo productivo avícola (cría, producción, engorde, incubación) con registro operativo básico. **Carece de flujo de aprobación formal, integración SAP real y auditoría completa.**

---

## 2. REPOSITORIOS AUDITADOS

### 2.1 Repo 1: `app_liderpollo` (Flutter App)

| Característica | Valor |
|---|---|
| **Framework** | Flutter 3.16.0 (stable) |
| **Lenguaje** | Dart 3.2.0 |
| **State Management** | Provider + ChangeNotifier |
| **Router** | go_router |
| **HTTP Client** | Dio |
| **Almacenamiento local** | Hive, Flutter Secure Storage |
| **i18n** | flutter_gen/gen_l10n (es, en, pt) |
| **Multi-flavor** | dev, prod |
| **Plataformas** | Android, iOS, Web, Windows |
| **Autenticación** | JWT con almacenamiento seguro + biométrico |
| **Notificaciones** | flutter_local_notifications |
| **UI** | Diseño oscuro con degradados, pantallas con scroll, formularios modales |
| **Figma** | https://www.figma.com/proto/HvQ5hBkvaJvPCOOfDtGqqc |

#### Estructura de carpetas relevante:
```
lib/
├── main.dart                    # Entry point con Provider, BlocProvider, dotenv, Hive
├── main_provider.dart           # Provider global (tema, perfil, snackbars)
├── main_navigation.dart         # Navegación principal (bottom nav: Home, Registro, KPIs, Config)
├── routes/
│   ├── login_page.dart          # Login con biométrico opcional
│   ├── splash_page.dart         # Splash screen con logo y gradiente
│   └── shell_routes/
│       ├── home/home_page.dart       # Dashboard con KPIs, indicadores y carrusel
│       ├── register/register_page.dart  # Menú de registro por secciones
│       ├── kpis/kpis_page.dart       # Menú de KPIs por fase
│       └── configuration/            # Configuración y ajustes
├── pages/
│   ├── register_pages/
│   │   ├── food_registration_page.dart            # Registro de alimento
│   │   ├── farm_inspection_page.dart              # Inspección de granja
│   │   ├── birds_exit_page.dart                   # Salida de aves
│   │   ├── classify_breeding_eggs_page.dart        # Clasificación huevos
│   │   ├── incubator_page.dart                    # Incubación
│   │   ├── eggs_collection_page.dart              # Recolección de huevos
│   │   ├── production_birds_distribution_page.dart # Distribución aves producción
│   │   ├── fattening_birds_distribution_page.dart  # Distribución aves engorde
│   │   ├── transport_inspection_page.dart          # Inspección transporte
│   │   ├── transport_inspection_eggs_page.dart     # Inspección transporte huevos
│   │   └── operation_state_page.dart              # Estado post-operación
│   └── kpis_pages/
│       └── kpis_fattening_page.dart               # KPIs de engorde
├── models/                       # Modelos de datos (30+ archivos)
│   ├── lote_model.dart
│   ├── granja_model.dart
│   ├── galpon_model.dart
│   ├── incubadora_model.dart
│   ├── orden_alimento_model.dart
│   ├── profile_model.dart
│   └── ... (muchos más)
├── repositories/
│   └── api_lider_pollo.dart      # Cliente API principal
├── widgets/
│   ├── defaults/                 # AppBar, Button, Scaffold, Drawer, Snackbar
│   ├── form_fields/              # InputField, DatePicker, TimePicker, BottomSelect
│   ├── dialogs/                  # Modal widgets
│   ├── loaders/                  # AppLoader
│   └── sheets/                   # CardWidget
└── utils/
    ├── config/                   # router_config, theme, config (idiomas)
    ├── services/                 # Dio, Hive, SecureStorage, LocalAuth, Notifications
    ├── mixins/                   # ThemesMixin, ProviderMixin
    └── general/                  # Variables, funciones, validaciones
```

---

### 2.2 Repo 2: `app_liderpollo_fronend` (Vue.js Frontend Web)

| Característica | Valor |
|---|---|
| **Framework** | Vue 3 (Composition API, `<script setup>`) |
| **Build Tool** | Vite 5 |
| **Lenguaje** | TypeScript + JavaScript |
| **UI Framework** | Vuetify 3 (Material Design) |
| **State Management** | Vuex (store central) |
| **Router** | Vue Router 4 |
| **HTTP Client** | Axios |
| **Auth** | JWT con vue3-storage-secure |
| **i18n** | vue-i18n (mínimo: solo `en.js` con página de error) |
| **Charts** | vue3-apexcharts |
| **Estilos** | SCSS (global + por página/componente) |
| **Docker** | Multi-stage (Node build + Nginx serve) |
| **Figma Admin** | https://www.figma.com/design/KJgcc8Z4Oe9eOPPHGAHmlc |

#### Estructura de carpetas relevante:
```
src/
├── main.js                      # Entry point con plugins, moment UTC
├── app.vue                      # Root con Loader + router-view
├── router/index.js              # Vue Router con auth guard
├── store/index.js               # Vuex store (loader, drawer, filters)
├── i18n/
│   └── en.js                    # Solo traducciones de página de error
├── repository/api-lider-pollo/
│   ├── index.ts                 # Export de todos los módulos API
│   ├── users.ts
│   ├── crias.ts
│   ├── granjas.ts
│   ├── produccion.ts
│   ├── engorde.ts
│   ├── incubadora.ts
│   ├── cambio_clave.ts
│   └── enums.ts                 # Enums compartidos
├── layouts/
│   ├── default-layout.vue       # Layout con Drawer
│   ├── auth-layout.vue          # Layout para login
│   └── empty-layout.vue
├── pages/
│   ├── home.vue                 # Dashboard con indicadores por fase
│   ├── login.vue                # Login administrativo
│   ├── forgot-password.vue      # Recuperación de clave
│   ├── error.vue                # Página 404 con glitch effect
│   ├── users.vue                # CRUD usuarios (tabla con paginación)
│   ├── create-user.vue          # Formulario crear usuario
│   ├── editar-user.vue          # Formulario editar usuario
│   ├── create-roles.vue         # Crear roles con módulos/submódulos
│   ├── update-rol.vue           # Editar rol
│   ├── maestros.vue             # Gestión de maestros
│   ├── visualize.vue            # Visualización de datos
│   ├── breeding-birds-phase/    # CRÍA
│   │   ├── process-birds.vue          # Tabs: Alimento, Pesaje, Mortalidad, Vacunación
│   │   ├── birds-reception.vue        # Recepción y distribución de aves
│   │   ├── birds-exit.vue             # Salida de aves
│   │   ├── farm-inspection.vue        # Inspección de granja
│   │   └── inspection-transport.vue   # Inspección de transporte
│   ├── production-birds-phase/  # PRODUCCIÓN
│   │   ├── process-birds.vue          # Tabs: Alimento, Pesaje, Mortalidad, Vacunación
│   │   ├── birds-reception.vue        # Recepción aves producción
│   │   ├── birds-exit.vue             # Salida aves producción
│   │   ├── farm-inspection.vue        # Inspección granja producción
│   │   ├── inspection-transport.vue   # Inspección transporte producción
│   │   └── inspection-transport-eggs.vue # Inspección transporte huevos
│   ├── fattening-birds-phase/   # ENGORDE
│   │   ├── process-birds.vue          # Tabs: Alimento, Pesaje, Mortalidad, Vacunación
│   │   ├── birds-reception.vue        # Recepción aves engorde
│   │   ├── birds-exit.vue             # Salida aves engorde
│   │   ├── farm-inspection.vue        # Inspección granja engorde
│   │   └── inspection-transport.vue   # Inspección transporte engorde
│   ├── incubator/               # INCUBADORA
│   │   ├── incubator-inspection.vue   # Inspección de incubadora
│   │   ├── eggs-reception.vue         # Recepción de huevos
│   │   ├── eggs-classification.vue    # Clasificación de huevos
│   │   ├── eggs-incubation.vue        # Incubación de huevos
│   │   ├── birth-registration.vue     # Registro de nacimientos
│   │   └── chicks-exit.vue            # Salida de pollitos
│   └── kpis/                    # KPIs
│       ├── kpi-breeding-birds-phase.vue  # KPIs cría
│       ├── kpi-production-birds-phase.vue # KPIs producción
│       ├── kpi-fattening-birds-phase.vue  # KPIs engorde
│       └── kpi-incubator.vue              # KPIs incubadora
├── components/
│   ├── drawer.vue               # Menú lateral de navegación
│   ├── navbar.vue               # Barra superior con título
│   ├── process-birds/           # Componentes por proceso
│   │   ├── food-records.vue           # Tabla + formulario de alimento
│   │   ├── weight-records.vue         # Tabla + formulario de pesaje
│   │   ├── mortality-records.vue      # Tabla + formulario de mortalidad
│   │   └── vaccination-records.vue    # Tabla + formulario de vacunación
│   ├── birds-exit/              # Componentes de salida
│   │   ├── birds-exit.vue             # Salida de aves
│   │   └── inspection-transport.vue   # Inspección de transporte
│   ├── modals/                  # Loader, CustomModal
│   └── helpers/                 # FullScreen, VImgLoad, VImgInput, VAvatarUpload
└── plugins/
    ├── functions.js             # Utilidades (formateo, validación, compresión)
    ├── directives.js            # Directivas personalizadas
    ├── components-import.js     # Registro global de componentes
    ├── polyfills.js             # Polyfills para String, HTMLElement
    └── vue3-storage-secure.ts   # Configuración de almacenamiento seguro
```

---

### 2.3 Repo 3: `app_liderpollo_backend` (Node.js/Express Backend)

| Característica | Valor |
|---|---|
| **Runtime** | Node.js |
| **Framework** | Express.js |
| **Lenguaje** | TypeScript |
| **ORM** | TypeORM |
| **Base de datos** | PostgreSQL (inferido por TypeORM + entidades relacionales) |
| **Autenticación** | JWT (auth.middleware.ts) |
| **Documentación API** | Swagger/OpenAPI 3.0.3 (swagger-jsdoc) |
| **Validación** | Manual en controladores (sin librería de validación dedicada) |
| **Logging** | Morgan (comentado en producción) |
| **CORS** | Habilitado globalmente |
| **Body parser** | body-parser (50MB limit) |
| **Zona horaria** | UTC forzado |

#### Estructura de carpetas:
```
src/
├── app.ts                       # Entry point: Express config, TypeORM init, Swagger, subscribers
├── config/
│   ├── data.source.ts           # TypeORM DataSource (PostgreSQL)
│   └── swagger.ts               # Config Swagger/OpenAPI
├── controllers/
│   ├── user.controller.ts             # CRUD usuarios, login, loginAdministrative, roles
│   ├── user_cambio_clave.controller.ts # Cambio de clave (sendCode, verifyCode, changeClave)
│   ├── granjas.controller.ts          # Registros generales: inspección, alimento, pesaje, mortalidad, vacuna
│   ├── granja_cria.controller.ts      # Registros específicos cría: maestro lote, recepción, salida
│   ├── granja_engorde.controller.ts   # Registros específicos engorde: maestro lote, recepción, salida
│   ├── incubadoras.controller.ts      # Registros incubadora: inspección, recepción, clasificación, incubación, nacimiento, salida pollitos
│   ├── consult_granjas.controller.ts        # Consultas generales (granjas, galpones, proveedores, KPIs, etc.)
│   ├── consult_granja_cria.controller.ts    # Consultas específicas cría
│   ├── consult_granja_produccion.controller.ts # Consultas específicas producción
│   ├── consult_granja_engorde.controller.ts   # Consultas específicas engorde
│   ├── consult_incubadoras.controller.ts      # Consultas incubadora
│   └── consult_users.controller.ts            # Consultas usuarios, roles, módulos
├── services/                    # Lógica de negocio (paralelo a controllers)
│   ├── user.service.ts
│   ├── granjas.service.ts
│   ├── granja_crias.service.ts
│   ├── granja_produccion.service.ts
│   ├── granja_engorde.service.ts
│   ├── incubadoras.service.ts
│   ├── consult_granjas.service.ts
│   ├── consult_granja_cria.service.ts
│   ├── consult_granja_produccion.service.ts
│   ├── consult_granja_engorde.service.ts
│   ├── consult_incubadoras.service.ts
│   └── consult_users.service.ts
├── entities/                    # Entidades TypeORM (30+ tablas)
│   ├── users.entity.ts
│   ├── users_roles.entity.ts
│   ├── users_modulos.entity.ts
│   ├── users_sub_modulos.entity.ts
│   ├── users_roles_modulos.entity.ts
│   ├── users_roles_sub_modulos.entity.ts
│   ├── granjas.entity.ts
│   ├── galpones.entity.ts
│   ├── incubadoras.entity.ts
│   ├── proveedores.entity.ts
│   ├── transportes.entity.ts
│   ├── raza_aves.entity.ts
│   ├── tipo_alimento.entity.ts
│   ├── vacunas.entity.ts
│   ├── equipos.entity.ts
│   ├── equipos_inspecciones.entity.ts
│   ├── plantas_beneficio.entity.ts
│   ├── alimento_ordenes.entity.ts
│   ├── inspecciones_granjas.entity.ts
│   ├── granja_cria/                   # Entidades de cría
│   │   ├── crias_ordenes_recepcion.entity.ts
│   │   ├── crias_recepcion_granja.entity.ts
│   │   ├── crias_distribucion_granja.entity.ts
│   │   ├── crias_lotes.entity.ts
│   │   ├── crias_alimento_granja.entity.ts
│   │   ├── crias_pesaje.entity.ts
│   │   ├── crias_mortalidad.entity.ts
│   │   ├── crias_vacunas.entity.ts
│   │   ├── crias_ordenes_salida.entity.ts
│   │   ├── crias_salida_aves.entity.ts
│   │   └── crias_inspeccion_transporte.entity.ts
│   ├── granja_produccion/             # Entidades de producción
│   │   ├── produccion_lotes.entity.ts
│   │   ├── produccion_ordenes_recepcion.entity.ts
│   │   ├── produccion_recepcion_granja.entity.ts
│   │   ├── produccion_distribucion_lote_granja.entity.ts
│   │   ├── produccion_alimento_granja.entity.ts
│   │   ├── produccion_pesaje.entity.ts
│   │   ├── produccion_mortalidad.entity.ts
│   │   ├── produccion_vacunas.entity.ts
│   │   ├── produccion_recoleccion_huevos.entity.ts
│   │   ├── produccion_ordenes_salida.entity.ts
│   │   ├── produccion_ordenes_salida_huevos.entity.ts
│   │   ├── produccion_salida_aves.entity.ts
│   │   └── produccion_inspeccion_transporte.entity.ts
│   ├── granja_engorde/                # Entidades de engorde
│   │   ├── engorde_lotes.entity.ts
│   │   ├── engorde_ordenes_recepcion.entity.ts
│   │   ├── engorde_recepcion_granja.entity.ts
│   │   ├── engorde_distribucion_lote_granja.entity.ts
│   │   ├── engorde_alimento_granja.entity.ts
│   │   ├── engorde_pesaje.entity.ts
│   │   ├── engorde_mortalidad.entity.ts
│   │   ├── engorde_vacunas.entity.ts
│   │   ├── engorde_ordenes_salida.entity.ts
│   │   ├── engorde_salida_aves.entity.ts
│   │   └── engorde_inspeccion_transporte.entity.ts
│   └── incubadora/                    # Entidades de incubadora
│       ├── incubadora_recepcion.entity.ts
│       ├── incubadora_clasificacion.entity.ts
│       ├── incubadora_incubacion.entity.ts
│       ├── incubadora_nacimiento.entity.ts
│       ├── incubadora_salida_pollito.entity.ts
│       ├── incubadora_salida_pollito_lotes.entity.ts
│       ├── incubadora_ordenes_salida_pollitos.entity.ts
│       └── inspecciones_incubadoras.entity.ts
├── interfaces/                  # TypeScript interfaces
│   ├── granjas.interface.ts
│   ├── granja_cria.interface.ts
│   ├── granja_produccion.interface.ts
│   ├── granja_engorde.interface.ts
│   ├── incubadoras.interface.ts
│   └── users.interface.ts
├── enums/
│   ├── entities.enum.ts         # StatusEnum, StatusRecepcionEnum, EtapaEnum, GeneroEnum, VentilacionEnum, StatusSalidaEnum
│   └── granjas.enum.ts          # EtapaGranjaEnum (CRIA, PRODUCCION, ENGORDE)
├── middleware/
│   └── auth.middleware.ts        # JWT verification middleware
├── routes/
│   ├── index.ts                 # Dynamic route loader (lee carpeta routes/)
│   └── routes/                  # Archivos de rutas por módulo
│       ├── user.ts
│       ├── user_cambio_clave.ts
│       ├── granjas.ts
│       ├── granja_cria.ts
│       ├── granja_produccion.ts
│       ├── granja_engorde.ts
│       ├── incubadora.ts
│       ├── consult_granjas.ts
│       ├── consult_granja_cria.ts
│       ├── consult_granja_produccion.ts
│       ├── consult_granja_engorde.ts
│       ├── consult_incubadoras.ts
│       └── consult_users.ts
└── subscribers/                 # TypeORM subscribers (seed de datos)
    ├── users_modulos.subscriber.ts
    ├── users_sub_modulos.subscriber.ts
    ├── users_roles.subscriber.ts
    ├── user.subscriber.ts
    └── pre_carga.subscriber.ts
```

---

## 3. TECNOLOGÍAS DETECTADAS POR REPOSITORIO

| Tecnología | `app_liderpollo` | `app_liderpollo_fronend` | `app_liderpollo_backend` |
|---|---|---|---|
| **Framework principal** | Flutter 3.16 | Vue 3 (Composition API) | Express.js |
| **Lenguaje** | Dart 3.2 | TypeScript / JavaScript | TypeScript |
| **Build tool** | Flutter CLI | Vite 5 | tsc |
| **UI Framework** | Material (custom) | Vuetify 3 | N/A |
| **State management** | Provider + Bloc | Vuex | N/A |
| **Router** | go_router | Vue Router 4 | Express Router |
| **HTTP Client** | Dio | Axios | N/A |
| **ORM** | N/A | N/A | TypeORM |
| **Base de datos** | N/A (cliente API) | N/A (cliente API) | PostgreSQL |
| **Autenticación** | JWT + biométrico | JWT (secure storage) | JWT middleware |
| **i18n** | flutter_gen (es, en, pt) | vue-i18n (mínimo) | N/A |
| **Documentación** | N/A | N/A | Swagger/OpenAPI 3.0.3 |
| **Contenedores** | N/A | Docker + Nginx | N/A (sin Dockerfile detectado) |
| **Charts** | Custom pie graph | vue3-apexcharts | N/A |
| **Validación** | ValidatorField widget | Manual | Manual en controllers |
| **Testing** | Widget test básico | No detectado | No detectado |

---

## 4. MÓDULOS FUNCIONALES ENCONTRADOS

### 4.1 Flutter (app_liderpollo)

| Módulo | Pantallas/Componentes |
|---|---|
| **Autenticación** | Login (usuario/contraseña + biométrico), Splash |
| **Home / Dashboard** | Bienvenida, indicadores por etapa, gráficos de pastel, carrusel |
| **Registro** | Menú por secciones de registro operativo |
| **Registro - Alimento** | `food_registration_page.dart` |
| **Registro - Inspección Granja** | `farm_inspection_page.dart` |
| **Registro - Salida Aves** | `birds_exit_page.dart` |
| **Registro - Clasificación Huevos** | `classify_breeding_eggs_page.dart` |
| **Registro - Incubación** | `incubator_page.dart` |
| **Registro - Recolección Huevos** | `eggs_collection_page.dart` |
| **Registro - Distribución Producción** | `production_birds_distribution_page.dart` |
| **Registro - Distribución Engorde** | `fattening_birds_distribution_page.dart` |
| **Registro - Inspección Transporte** | `transport_inspection_page.dart` |
| **Registro - Inspección Transporte Huevos** | `transport_inspection_eggs_page.dart` |
| **KPIs** | Menú KPIs, `kpis_fattening_page.dart` |
| **Configuración** | Tema, idioma, perfil, logout |

### 4.2 Frontend Web (app_liderpollo_fronend)

| Módulo | Pantallas/Componentes |
|---|---|
| **Autenticación** | Login, Forgot Password, Logout |
| **Home / Dashboard** | Indicadores por fase (Cría, Producción, Engorde), KPIs, accesos rápidos |
| **Procesos - Cría** | Alimento, Pesaje, Mortalidad, Vacunación (tabs) |
| **Procesos - Producción** | Alimento, Pesaje, Mortalidad, Vacunación (tabs) |
| **Procesos - Engorde** | Alimento, Pesaje, Mortalidad, Vacunación (tabs) |
| **Recepción Aves** | Cría, Producción, Engorde |
| **Salida Aves** | Cría, Producción, Engorde |
| **Inspección Granja** | Cría, Producción, Engorde |
| **Inspección Transporte** | Cría, Producción, Engorde + Huevos |
| **Incubadora** | Inspección, Recepción Huevos, Clasificación, Incubación, Nacimiento, Salida Pollitos |
| **KPIs** | Cría, Producción, Engorde, Incubadora |
| **Usuarios** | CRUD, asignación de roles, módulos, submódulos |
| **Roles** | Crear, editar, activar/desactivar |
| **Maestros** | Gestión de datos maestros |
| **Visualización** | Visualización de registros |

### 4.3 Backend (app_liderpollo_backend)

| Módulo | Endpoints principales |
|---|---|
| **Auth / Users** | create-user, update-user, login, loginAdministrative, clear-mac, create-rol, update-rol, change-status-rol |
| **Cambio Clave** | send-code, verify-code, change-clave |
| **Granjas (general)** | set-inspeccion-granja, set-alimento, update-alimento, delete-alimento, set-pesaje, update-pesaje, delete-pesaje, set-mortalidad, update-mortalidad, delete-mortalidad, set-vacuna, delete-vacuna |
| **Granja Cría** | set-maestro-lote, set-recepcion, set-salida-aves, set-inspeccion-transporte |
| **Granja Producción** | set-maestro-lote, set-recepcion, set-salida-aves, set-salida-huevos, set-inspeccion-transporte, set-recoleccion-huevos |
| **Granja Engorde** | set-maestro-lote, set-recepcion, set-salida-aves, set-inspeccion-transporte |
| **Incubadora** | set-inspeccion-incubadora, set-recepcion, set-clasificacion, set-incubacion, set-nacimiento, set-salida-pollitos |
| **Consultas Granjas** | get-granjas, get-galpones, get-plantas-beneficio, get-equipos, get-proveedores, get-razas, get-tipo-alimento, get-transportes, get-vacunas, get-lotes-recepcion, get-ordenes-alimento, get-ordenes-salida, get-lotes-salida, get-semanas-lote, get-kpis-lote, get-kpis-home, get-inspecciones-granjas, get-registros-alimento/pesaje/mortalidad/vacunas, get-salidas-aves, get-inspecciones-transporte |
| **Consultas Cría** | get-ordenes-recepcion, get-lotes-disponibles, get-lotes-salida, get-maestro-lotes, get-recepciones, get-recepcion-byid |
| **Consultas Producción** | get-lotes-disponibles, get-lotes-salida, get-maestro-lotes, get-recepciones, get-recepcion-byid |
| **Consultas Engorde** | get-lotes-disponibles, get-lotes-salida-aprobada, get-lotes-salida, get-maestro-lotes, get-recepciones, get-recepcion-byid |
| **Consultas Incubadora** | get-incubadoras, get-lotes-salida-huevos, get-lotes-recepcion, get-ordenes-salida, get-semanas-incubadora, get-kpis-diario, get-inspecciones-incubadora, get-recepciones, get-incubaciones, get-nacimientos, get-salidas-pollitos |
| **Consultas Users** | get-users, get-user, get-modulos, get-sub-modulos, get-granjas-asignacion-user, get-roles, get-rol, get-rol-user |

---

## 5. PANTALLAS Y FORMULARIOS IDENTIFICADOS

### 5.1 Campos de formularios clave (extraídos de modelos e interfaces)

#### Recepción de Aves (Cría)
- `granja_id`, `orden_compra_id`, `proveedor_id`, `fecha_despacho`, `fecha_recepcion`
- `cantidad_machos`, `cantidad_hembras`, `peso_promedio_entrada`
- `raza_id`, `distribucion` (por galpón)

#### Registro de Alimento
- `lote_id`, `granja_id`, `galpon_id`, `tipo_alimento_id`, `fecha`
- `cantidad`, `orden_alimento_id`, `observaciones`

#### Registro de Pesaje
- `lote_id`, `granja_id`, `galpon_id`, `semana_id`, `fecha`
- `peso_promedio`, `cantidad_aves`, `tipo_ave` (macho/hembra)

#### Registro de Mortalidad
- `lote_id`, `granja_id`, `galpon_id`, `fecha`
- `cantidad_machos`, `cantidad_hembras`, `causa_id`, `observaciones`

#### Registro de Vacunación
- `lote_id`, `granja_id`, `galpon_id`, `vacuna_id`, `fecha`
- `dosis`, `via_aplicacion`, `observaciones`

#### Inspección de Granja
- `granja_id`, `lote_id`, `fecha_inspeccion`
- `condicion_cama`, `equipos` (selección múltiple), `temperatura`, `humedad`
- `observaciones`

#### Salida de Aves
- `lote_id`, `granja_origen_id`, `planta_destino_id` / `granja_destino_id`
- `transporte_id`, `fecha_envio`, `fecha_recepcion`, `cantidad_aves`
- `peso_promedio_salida`, `distribucion` (por galpón)

#### Inspección de Transporte
- `orden_salida_id`, `fecha_inspeccion`
- `condiciones_jaulas`, `temperatura_transporte`, `densidad`
- `observaciones`

#### Recolección de Huevos (Producción)
- `lote_id`, `granja_id`, `galpon_id`, `fecha`
- `cantidad_huevos_aptos`, `cantidad_huevos_sucios`, `cantidad_huevos_rotos`
- `cantidad_huevos_infertiles`, `cantidad_huevos_descartados`
- `peso_promedio_huevo`

#### Recepción de Huevos (Incubadora)
- `orden_salida_huevos_id`, `granja_origen_id`, `fecha_recepcion`
- `cantidad_recibida`, `lote_id`

#### Clasificación de Huevos
- `recepcion_id`, `fecha_clasificacion`
- `cantidad_fertiles`, `cantidad_sucios`, `cantidad_infertiles`
- `cantidad_descartados`, `peso_promedio_huevo`

#### Incubación
- `recepcion_id`, `incubadora_id`, `fecha_incubacion`, `hora`
- `cantidad_cargada`, `temperatura`, `humedad`, `co2`, `volteo`

#### Nacimiento
- `recepcion_id`, `incubacion_id`, `fecha_nacimiento`
- `cantidad_pollitos_nacidos`, `cantidad_pollitos_viables`
- `cantidad_pollitos_descartados`, `vacuna_id` (vacunación en planta)

#### Salida de Pollitos
- `orden_salida_id`, `granja_destino_id`, `fecha_salida`
- `cantidad_pollitos`, `lotes` (origen de los pollitos)

---

## 6. FLUJOS OPERATIVOS IDENTIFICADOS

### 6.1 Flujo general (sin aprobación formal en legacy)

```
1. Login → Home (Dashboard con indicadores)
2. Selección de módulo (Cría / Producción / Engorde / Incubadora)
3. Registro operativo (formulario → API POST)
4. Visualización en tabla (API GET con filtros)
5. Edición directa (API POST update)
6. Eliminación directa (API POST delete)
7. Consulta de KPIs
```

### 6.2 Flujo por fase productiva

```
Cría:
  Maestro Lote → Recepción y Distribución → 
  [Alimento | Pesaje | Mortalidad | Vacunación] recurrentes →
  Inspección Granja → Salida Aves → Inspección Transporte

Producción:
  Maestro Lote → Recepción (desde Cría) →
  [Alimento | Pesaje | Mortalidad | Vacunación] recurrentes →
  Recolección Huevos → Salida Huevos a Incubadora → 
  Salida Aves → Inspección Transporte

Engorde:
  Maestro Lote → Recepción (desde Incubadora) →
  [Alimento | Pesaje | Mortalidad | Vacunación] recurrentes →
  Salida Aves a Planta Beneficio → Inspección Transporte

Incubadora:
  Recepción Huevos → Clasificación → Incubación → 
  Nacimiento → Salida Pollitos → (van a Engorde)
```

---

## 7. REGLAS DE NEGOCIO DETECTADAS

### 7.1 En el código legacy (explícitas e implícitas)

| Regla | Ubicación | Tipo |
|---|---|---|
| Autenticación JWT obligatoria para todas las rutas | `auth.middleware.ts` | Explícita |
| Status de registros: ACTIVO / CERRADO | `entities.enum.ts` | Explícita |
| Estados de recepción: ACTIVO / CERRADO | `entities.enum.ts` | Explícita |
| Estados de salida: ACTIVO / CERRADO / APROBADO | `entities.enum.ts` (StatusSalidaEnum) | Explícita |
| Etapas: CRIA / PRODUCCION / ENGORDE | `granjas.enum.ts` | Explícita |
| Género de aves: MACHO / HEMBRA | `entities.enum.ts` | Explícita |
| Ventilación en incubadora: BUENA / REGULAR / MALA | `entities.enum.ts` | Explícita |
| Distribución de aves por galpón | Lógica en servicios | Implícita |
| Relación lotes → granjas → galpones | Modelo de datos | Explícita |
| Zona horaria UTC forzada | `app.ts` | Explícita |
| Timeout de sesión configurable | `session_timeout_config.dart` (Flutter) | Explícita |
| Eliminación lógica (no física) de registros | Endpoints `delete-*` | Parcial |
| Cálculo de KPIs desde datos operativos | Servicios de consulta | Implícita |

### 7.2 Reglas AUSENTES (que el nuevo sistema DEBE implementar)

| Regla | Prioridad |
|---|---|
| No permitir mortalidad > saldo disponible | **Crítica** |
| No permitir despacho de huevos > disponible | **Crítica** |
| No permitir cargar incubadora > huevos recibidos | **Crítica** |
| No permitir despachar pollitos > nacidos viables | **Crítica** |
| No permitir cierre de lote sin resumen final | **Crítica** |
| No permitir fechas operativas anteriores a activación de lote | **Alta** |
| No permitir movimientos sin lote activo | **Alta** |
| Toda corrección debe auditarse | **Crítica** |
| Toda eliminación debe ser lógica con trazabilidad | **Crítica** |
| Documentos SAP no deben duplicarse | **Alta** |
| Movimientos deben ser idempotentes | **Alta** |
| Ningún dato operativo a SAP sin aprobación | **Crítica** |
| Operador no puede aprobar su propia carga | **Alta** |
| Registros enviados a SAP no editables directamente | **Alta** |

---

## 8. VALIDACIONES EXISTENTES

| Validación | Dónde | Tipo |
|---|---|---|
| Campos requeridos en formularios | Flutter (`ValidatorField`) + Frontend (HTML5 required) | Frontend |
| Formato de números decimales | `maxDecimals = 3` en Flutter, `isOnlyDigits` en frontend | Frontend |
| Email formato | Formularios de usuario | Frontend |
| MAC address formato | `users.vue` | Frontend |
| JWT token válido y no expirado | `auth.middleware.ts` | Backend |
| Rate limiting o throttling | No detectado | **AUSENTE** |
| Validación de integridad referencial | TypeORM relaciones | Backend (parcial) |
| Sanitización de entrada | No detectado explícitamente | **AUSENTE** |
| Validación de tamaño de archivo | body-parser 50MB limit | Backend (básico) |

---

## 9. ENTIDADES Y DATOS UTILIZADOS

### 9.1 Entidades principales (TypeORM)

**Catálogos / Maestros:**
- `Granjas` — Datos de granjas
- `Galpones` — Galpones por granja
- `Incubadoras` — Incubadoras disponibles
- `Proveedores` — Proveedores
- `Transportes` — Transportes (con `id_sap`)
- `RazaAves` — Razas/líneas genéticas (con `id_sap`)
- `TipoAlimento` — Tipos de alimento
- `Vacunas` — Catálogo de vacunas
- `Equipos` — Equipos de granja
- `PlantasBeneficio` — Plantas de beneficio

**Usuarios y Roles:**
- `Users` — Usuarios del sistema
- `UsersRoles` — Roles (con CRUD granular: leer, insertar, editar, eliminar)
- `UsersModulos` — Módulos del sistema
- `UsersSubModulos` — Submódulos
- `UsersRolesModulos` — Asignación rol-módulo
- `UsersRolesSubModulos` — Asignación rol-submódulo

**Operativos (Cría):**
- `CriasOrdenesRecepcion` — Órdenes de recepción (con `id_sap`)
- `CriasRecepcionGranja` — Recepción en granja
- `CriasDistribucionGranja` — Distribución por galpón
- `CriasLotes` — Lotes de cría
- `CriasAlimentoGranja` — Registro de alimento
- `CriasPesaje` — Registro de pesaje
- `CriasMortalidad` — Registro de mortalidad
- `CriasVacunas` — Registro de vacunación
- `CriasOrdenesSalida` — Órdenes de salida (con `id_sap`)
- `CriasSalidaAves` — Salida de aves
- `CriasInspeccionTransporte` — Inspección de transporte

**Operativos (Producción):**
- `ProduccionLotes` — Lotes de producción
- `ProduccionOrdenesRecepcion` — Órdenes de recepción (con `id_sap`)
- `ProduccionRecepcionGranja` — Recepción en granja
- `ProduccionDistribucionLoteGranja` — Distribución por galpón
- `ProduccionAlimentoGranja` — Registro de alimento
- `ProduccionPesaje` — Registro de pesaje
- `ProduccionMortalidad` — Registro de mortalidad
- `ProduccionVacunas` — Registro de vacunación
- `ProduccionRecoleccionHuevos` — Recolección de huevos
- `ProduccionOrdenesSalida` — Órdenes de salida aves (con `id_sap`)
- `ProduccionOrdenesSalidaHuevos` — Órdenes de salida huevos (con `id_sap`)
- `ProduccionSalidaAves` — Salida de aves
- `ProduccionInspeccionTransporte` — Inspección de transporte

**Operativos (Engorde):**
- `EngordeLotes` — Lotes de engorde
- `EngordeOrdenesRecepcion` — Órdenes de recepción (con `id_sap`)
- `EngordeRecepcionGranja` — Recepción en granja
- `EngordeDistribucionLoteGranja` — Distribución por galpón
- `EngordeAlimentoGranja` — Registro de alimento
- `EngordePesaje` — Registro de pesaje
- `EngordeMortalidad` — Registro de mortalidad
- `EngordeVacunas` — Registro de vacunación
- `EngordeOrdenesSalida` — Órdenes de salida (con `id_sap`)
- `EngordeSalidaAves` — Salida de aves
- `EngordeInspeccionTransporte` — Inspección de transporte

**Operativos (Incubadora):**
- `IncubadoraRecepcion` — Recepción de huevos
- `IncubadoraClasificacion` — Clasificación de huevos
- `IncubadoraIncubacion` — Incubación
- `IncubadoraNacimiento` — Nacimiento de pollitos
- `IncubadoraSalidaPollito` — Salida de pollitos
- `IncubadoraSalidaPollitoLotes` — Relación salida-lotes
- `IncubadoraOrdenesSalidaPollitos` — Órdenes de salida (con `id_sap`)
- `InspeccionesIncubadoras` — Inspección de incubadoras

**Transversales:**
- `AlimentoOrdenes` — Órdenes de alimento (con `id_sap`)
- `InspeccionesGranjas` — Inspecciones de granja
- `EquiposInspecciones` — Relación equipo-inspección

---

## 10. ENDPOINTS ENCONTRADOS

### 10.1 Resumen por módulo

| Prefijo de ruta | Nº endpoints | Tipo de operaciones |
|---|---|---|
| `/user` | ~10 | CRUD usuarios, login, roles |
| `/user_cambio_clave` | 3 | Cambio de contraseña |
| `/granjas` | ~12 | Inspección, alimento, pesaje, mortalidad, vacunas |
| `/granja_cria` | ~5 | Maestro lote, recepción, salida aves, inspección transporte |
| `/granja_produccion` | ~7 | Maestro lote, recepción, salida aves, salida huevos, recolección |
| `/granja_engorde` | ~5 | Maestro lote, recepción, salida aves, inspección transporte |
| `/incubadora` | ~6 | Inspección, recepción, clasificación, incubación, nacimiento, salida |
| `/consult_granjas` | ~20 | Consultas generales de granjas, KPIs |
| `/consult_granja_cria` | ~6 | Consultas específicas cría |
| `/consult_granja_produccion` | ~6 | Consultas específicas producción |
| `/consult_granja_engorde` | ~6 | Consultas específicas engorde |
| `/consult_incubadoras` | ~10 | Consultas incubadora |
| `/consult_users` | ~8 | Consultas usuarios, roles, módulos |

**Total estimado: ~100+ endpoints**

Todos los endpoints usan `authMiddleware` (excepto login y cambio de clave).

---

## 11. INTEGRACIÓN SAP ENCONTRADA

### 11.1 Estado actual

**No existe integración SAP funcional en ningún repositorio.** Sin embargo, hay evidencia de preparación:

| Evidencia | Ubicación |
|---|---|
| Campo `id_sap` en múltiples entidades | `AlimentoOrdenes`, `CriasOrdenesRecepcion`, `CriasOrdenesSalida`, `EngordeOrdenesSalida`, `ProduccionOrdenesSalida`, `ProduccionOrdenesSalidaHuevos`, `IncubadoraOrdenesSalidaPollitos`, `RazaAves`, `Transportes` |
| Interface `MaestroLotesInterface` con `idSap` | `src/interfaces/granjas.interface.ts` |
| `StatusSalidaEnum.APROBADO` | `src/enums/entities.enum.ts` (único estado que sugiere flujo) |

**Conclusión:** El modelo de datos contempla referencias SAP pero no se implementó ninguna lógica de importación, sincronización o envío a SAP. Esto es deuda técnica significativa.

---

## 12. RIESGOS TÉCNICOS

| Riesgo | Severidad | Descripción |
|---|---|---|
| Sin integración SAP real | **Crítico** | Solo campos `id_sap` sin lógica |
| Sin flujo de aprobación | **Crítico** | Edición/eliminación directa sin revisión |
| Sin auditoría | **Crítico** | No hay trazabilidad de cambios |
| Sin control de correcciones | **Crítico** | No se conserva valor original vs corregido |
| Duplicación de entidades por fase | **Alto** | Misma estructura para Cría, Producción, Engorde (DRY violado) |
| Validación solo en frontend | **Alto** | Backend sin validación fuerte de entrada |
| Sin tests automatizados | **Alto** | Solo un widget test básico en Flutter |
| i18n incompleto en web | **Medio** | Solo inglés para página de error |
| CORS habilitado globalmente | **Medio** | `app.use(cors())` sin restricciones |
| Sin rate limiting | **Medio** | Vulnerable a abuso de API |
| Error handling inconsistente | **Medio** | Códigos de error parseados de strings |
| Sin Docker para backend | **Bajo** | Solo frontend tiene Dockerfile |

---

## 13. DEUDA TÉCNICA

| Deuda | Descripción | Impacto |
|---|---|---|
| **Entidades duplicadas** | Cría, Producción y Engorde tienen las mismas tablas con nombres diferentes | Mantenimiento costoso, inconsistencia |
| **Lógica en Flutter** | Validaciones y algunas reglas residen solo en la app móvil | Backend no es source of truth |
| **Sin capa de servicio pura** | Servicios mezclan lógica de negocio con queries TypeORM | Difícil de testear y mantener |
| **Manejo de errores frágil** | `error.message.split("-")[0]` para extraer HTTP status code | Propenso a fallos |
| **Sin migraciones** | No se detecta uso de migraciones TypeORM (solo `synchronize`) | Riesgo de pérdida de datos en producción |
| **Frontend sin TypeScript estricto** | Mezcla de `.js` y `.ts`, sin tipos en muchas funciones | Menos seguridad de tipos |
| **Sin tests** | Sin tests unitarios, de integración ni E2E en backend/frontend web | Regresiones no detectadas |
| **Polyfills intrusivos** | Modifica prototipos nativos (`String.prototype`, `HTMLElement.prototype`) | Riesgo de conflicto con librerías |
| **jQuery en index.html** | El frontend web carga jQuery desde CDN solo para un fadeOut | Innecesario, rompe con el estándar sin CDN |
| **Swagger incompleto** | Solo algunos endpoints tienen documentación Swagger | API no totalmente documentada |

---

## 14. TABLA DE DECISIÓN: CONSERVAR, REDISEÑAR, ELIMINAR

| Elemento | Decisión | Justificación |
|---|---|---|
| **Flujos operativos (ciclo avícola completo)** | ✅ **CONSERVAR** (como concepto) | El dominio funcional es sólido y completo |
| **Catálogo de entidades (granjas, galpones, etc.)** | 🔄 **REDISEÑAR** | Unificar en modelo normalizado sin duplicación por fase |
| **Campos de formularios** | ✅ **CONSERVAR** (con ajustes) | Los campos capturados son correctos; agregar los faltantes |
| **App Flutter** | ❌ **ELIMINAR** (como tecnología) | Solo usar como referencia funcional |
| **Frontend Vue.js** | ❌ **ELIMINAR** (como tecnología) | Reemplazar por React + Vite + TypeScript + TailwindCSS |
| **Backend Node.js/Express** | ❌ **ELIMINAR** (como tecnología) | Reemplazar por FastAPI + SQLAlchemy 2.x + PostgreSQL |
| **TypeORM → SQLAlchemy** | 🔄 **REDISEÑAR** | Migrar concepto de entidades, no código |
| **Autenticación JWT** | ✅ **CONSERVAR** (patrón) | Reimplementar con FastAPI + PyJWT |
| **RBAC por roles** | 🔄 **REDISEÑAR** | Modelo más granular con permisos por módulo y estado |
| **Campos `id_sap`** | 🔄 **REDISEÑAR** | Integrar correctamente con capa de abstracción SAP |
| **i18n (Flutter)** | ✅ **CONSERVAR** (concepto) | Implementar i18n completo desde inicio (ES/EN) |
| **Vuetify → TailwindCSS** | ❌ **ELIMINAR** | Sin CDN, solo TailwindCSS por paquete |
| **Dockerfile frontend (Nginx)** | 🔄 **REDISEÑAR** | Adaptar a React + Vite |
| **Estructura de endpoints** | 🔄 **REDISEÑAR** | Reorganizar por dominio en FastAPI |
| **Swagger/OpenAPI** | ✅ **CONSERVAR** | FastAPI lo genera automáticamente |
| **jQuery CDN** | ❌ **ELIMINAR** | Innecesario |
| **Polyfills intrusivos** | ❌ **ELIMINAR** | Usar polyfills estándar si son necesarios |
| **Diseño visual Flutter (oscuro)** | ❌ **ELIMINAR** | Nuevo diseño blanco/azul corporativo |
| **Diseño Vue.js (Vuetify Material)** | ❌ **ELIMINAR** | Nuevo diseño blanco/azul con TailwindCSS |
| **Proceso de abuelas/importación** | 🆕 **CREAR** | No existe en legacy |
| **Activación manual de lotes** | 🆕 **CREAR** | No existe en legacy |
| **Centro de Revisión Operativa** | 🆕 **CREAR** | No existe en legacy |
| **Flujo de aprobación multinivel** | 🆕 **CREAR** | No existe en legacy |
| **Auditoría completa** | 🆕 **CREAR** | No existe en legacy |
| **Integración SAP real** | 🆕 **CREAR** | No existe en legacy |

---

## 15. PLAN DE MIGRACIÓN FUNCIONAL HACIA REACT + FASTAPI

### 15.1 Principios de migración

1. **No migrar código.** Extraer conceptos, reglas de negocio y estructuras de datos.
2. **No replicar arquitectura.** Rediseñar con principios SOLID, DDD y arquitectura limpia.
3. **No copiar UI.** Rediseñar con estándar visual blanco/azul corporativo.
4. **No heredar deuda técnica.** Cada componente se construye desde cero con buenas prácticas.
5. **SAP-first design.** Diseñar asumiendo integración SAP desde el día 1.

### 15.2 Mapa de migración Node.js → FastAPI

| Node.js (TypeORM) | FastAPI (SQLAlchemy 2.x) |
|---|---|
| `entities/` | `models/` (SQLAlchemy ORM models) |
| `interfaces/` | `schemas/` (Pydantic v2) |
| `controllers/` | `routers/` (APIRouter) |
| `services/` | `services/` (lógica de negocio pura) |
| `middleware/auth.middleware.ts` | `auth/` (JWT + RBAC con dependencies) |
| `routes/` | `routers/` (organizado por dominio) |
| `config/data.source.ts` | `config.py` + Alembic |
| TypeORM `@Entity()` | SQLAlchemy `DeclarativeBase` |
| TypeORM `find()`, `save()` | SQLAlchemy `select()`, `session.add()` |
| Swagger manual | OpenAPI automático (FastAPI) |

### 15.3 Mapa de migración Vue.js → React

| Vue.js (Vuetify) | React (TailwindCSS) |
|---|---|
| `.vue` SFC | `.tsx` components |
| `v-data-table` | Custom table component con Tailwind |
| `v-tabs` | Custom tabs component |
| `v-navigation-drawer` | Custom sidebar/drawer |
| Vuex store | Zustand / React Context |
| Vue Router | React Router v6 |
| `vue-i18n` | `react-i18next` |
| `vue3-apexcharts` | `recharts` / `nivo` |
| SCSS por componente | TailwindCSS utility classes + CSS modules |
| `vue-toastification` | `react-hot-toast` |

### 15.4 Migración de modelo de datos

**Problema legacy:** Tablas duplicadas para Cría, Producción, Engorde (ej: `crias_pesaje`, `produccion_pesaje`, `engorde_pesaje`).

**Solución nueva:** Tabla unificada con campo `phase`:
```sql
-- En lugar de 3 tablas separadas:
weight_records (id, lot_id, farm_id, house_id, phase, ...)

-- En lugar de 3 tablas de mortalidad:
mortality_records (id, lot_id, farm_id, house_id, phase, ...)

-- etc.
```

---

## 16. ELEMENTOS QUE NO DEBEN MIGRARSE

1. ❌ **App Flutter completa** — solo referencia funcional
2. ❌ **Frontend Vue.js/Vuetify** — solo referencia de pantallas y flujos
3. ❌ **Backend Node.js/Express** — solo referencia de endpoints y entidades
4. ❌ **Diseño oscuro de Flutter** — incompatible con nuevo estándar blanco/azul
5. ❌ **Componentes Vuetify Material Design** — incompatible con TailwindCSS
6. ❌ **jQuery desde CDN** — prohibido en nuevo estándar
7. ❌ **Polyfills que modifican prototipos nativos**
8. ❌ **Manejo de errores con split de strings**
9. ❌ **Duplicación de tablas por fase** — rediseñar con modelo unificado
10. ❌ **Lógica de negocio en frontend** — debe residir en backend
11. ❌ **Eliminación física de registros** — debe ser lógica con trazabilidad
12. ❌ **CORS global abierto** — restringir a orígenes conocidos

---

## 17. ELEMENTOS PRIORITARIOS PARA LA NUEVA VERSIÓN

### Prioridad 1 — Críticos (MVP)
1. Modelo de datos unificado con eventos operativos auditables
2. Flujo de registro operativo (móvil) → revisión → corrección → aprobación
3. Centro de Revisión Operativa / Bandeja de Aprobación
4. Auditoría completa de cada acción
5. Autenticación JWT + RBAC
6. Maestros (granjas, galpones, incubadoras, líneas genéticas, etc.)
7. Dashboard ejecutivo con KPIs
8. Diseño mobile-first blanco/azul

### Prioridad 2 — Altos
9. Integración SAP (capa de abstracción)
10. Activación manual de lotes con saldos iniciales
11. Proceso de abuelas/importación
12. i18n completo español/inglés
13. Reportes e indicadores
14. Consolidación y preparación de datos para SAP

### Prioridad 3 — Medios
15. Notificaciones y alertas
16. Exportación Excel/PDF
17. Adjuntos/documentos soporte
18. Multi-empresa
19. PWA (opcional)

---

## 18. CONCLUSIONES DE LA AUDITORÍA

El sistema legacy **"Lider Pollo"** proporciona una base funcional sólida en cuanto a:
- Cobertura del ciclo productivo avícola completo
- Modelo de datos relacional (aunque duplicado por fase)
- API REST con ~100 endpoints documentados parcialmente
- Experiencia de usuario móvil funcional (Flutter)
- Panel administrativo web operativo (Vue.js)

Sin embargo, presenta **deficiencias críticas** que el nuevo sistema **Global Avícola** debe resolver:

1. **Ausencia total de flujo de aprobación** → Nuevo Centro de Revisión Operativa
2. **Ausencia de integración SAP real** → Capa de abstracción SAP desacoplada
3. **Ausencia de auditoría** → Auditoría completa en cada acción
4. **Ausencia de corrección auditada** → Valor original + valor corregido
5. **Arquitectura duplicada** → Modelo unificado por fase
6. **Validación débil** → Validación fuerte en backend con Pydantic v2
7. **Sin tests** → Cobertura completa (unit, integration, E2E)
8. **Diseño no corporativo** → Diseño blanco/azul profesional

**La migración debe ser conceptual, no técnica. Se extraen reglas de negocio, flujos y estructuras de datos, pero todo se reconstruye con estándares modernos de ingeniería de software.**
