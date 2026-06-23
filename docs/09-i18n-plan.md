# Plan de Internacionalización (i18n) — Global Avícola

> **Documento:** 09-i18n-plan.md
> **Versión:** 1.0.0
> **Fecha:** 2026-06-22

---

## 1. PRINCIPIOS

1. **Bilingüe desde el inicio.** Español (default) + Inglés.
2. **Zero hardcoding.** Ningún texto visible en el código fuente.
3. **Selector de idioma visible.** En header/navbar.
4. **Entidades técnicas en inglés.** Nombres de tablas, campos API, logs.
5. **Formato regional.** Fechas y números según locale.

---

## 2. IDIOMAS

| Idioma | Código | Locale | Default |
|---|---|---|---|
| Español | `es` | `es-ES` | ✅ |
| Inglés | `en` | `en-US` | |

---

## 3. IMPLEMENTACIÓN TÉCNICA

### 3.1 Frontend (react-i18next)

```
public/locales/
├── es/
│   └── translation.json
└── en/
    └── translation.json
```

**Estructura de archivos de traducción:**

```json
{
  "common": {
    "save": "Guardar",
    "cancel": "Cancelar",
    "delete": "Eliminar",
    "edit": "Editar",
    "search": "Buscar",
    "filter": "Filtrar",
    "export": "Exportar",
    "yes": "Sí",
    "no": "No",
    "back": "Volver",
    "next": "Siguiente",
    "loading": "Cargando...",
    "noResults": "Sin resultados",
    "confirm": "Confirmar",
    "actions": "Acciones"
  },
  "auth": {
    "login": "Iniciar Sesión",
    "logout": "Cerrar Sesión",
    "username": "Usuario",
    "password": "Contraseña",
    "forgotPassword": "¿Olvidaste tu contraseña?",
    "loginError": "Usuario o contraseña incorrectos"
  },
  "status": {
    "draft": "Borrador",
    "registered": "Registrado",
    "pendingReview": "Enviado a Revisión",
    "inReview": "En Revisión",
    "returned": "Devuelto",
    "corrected": "Corregido",
    "approved": "Aprobado",
    "rejected": "Rechazado",
    "consolidated": "Consolidado",
    "sentToSap": "Enviado a SAP",
    "sapConfirmed": "Confirmado por SAP",
    "sapError": "Error SAP",
    "cancelled": "Anulado"
  },
  "lots": {
    "title": "Lotes",
    "lotCode": "Código de Lote",
    "geneticLine": "Línea Genética",
    "birdType": "Tipo de Ave",
    "currentPhase": "Fase Actual",
    "startDate": "Fecha de Inicio",
    "status": "Estado",
    "activateManually": "Activar Lote Manualmente",
    "openingBalance": "Saldo Inicial"
  }
}
```

### 3.2 Backend

- Mensajes de error de API en inglés (técnico)
- Mensajes de validación con códigos de error (i18n en frontend)
- Logs en inglés

---

## 4. FORMATO DE FECHAS Y NÚMEROS

| Elemento | Español (es-ES) | Inglés (en-US) |
|---|---|---|
| Fecha corta | 22/06/2026 | 06/22/2026 |
| Fecha larga | 22 de junio de 2026 | June 22, 2026 |
| Número decimal | 1.500,75 | 1,500.75 |
| Moneda | 1.500,75 € | €1,500.75 |

---

## 5. COBERTURA i18N

| Área | Cobertura |
|---|---|
| Etiquetas de formularios | 100% |
| Mensajes de validación | 100% |
| Estados y badges | 100% |
| Navegación y menús | 100% |
| Tablas (headers) | 100% |
| Notificaciones / Toasts | 100% |
| Reportes | 100% |
| Errores de API | 100% (mapeados a mensajes i18n) |

---

## 6. PRUEBAS i18N

1. Verificar que no hay strings hardcodeados en el código
2. Cambiar idioma en runtime → todas las etiquetas cambian
3. Snapshots de componentes en ambos idiomas
4. Formato de fechas y números correcto según locale
