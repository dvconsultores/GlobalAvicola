# Plan de Compatibilidad de Navegadores — Global Avícola

> **Documento:** 08-browser-compatibility-plan.md
> **Versión:** 1.0.0
> **Fecha:** 2026-06-22

---

## 1. NAVEGADORES SOPORTADOS

| Navegador | Versión | Plataforma | Prioridad |
|---|---|---|---|
| **Chrome** | Últimas 2 versiones | Desktop + Android | Crítica |
| **Edge** | Últimas 2 versiones | Desktop | Alta |
| **Firefox** | Últimas 2 versiones | Desktop | Alta |
| **Safari** | Últimas 2 versiones | macOS + iOS | Alta |
| **Opera** | Última versión | Desktop | Media |
| **iOS Safari** | Últimas 2 versiones | iPhone/iPad | Crítica |
| **Android Chrome** | Últimas 2 versiones | Android | Crítica |
| **Samsung Internet** | Última versión | Android | Baja (si PWA) |

---

## 2. VIEWPORTS DE PRUEBA

| Viewport | Dispositivo representativo | Prioridad |
|---|---|---|
| **360×640** | Móvil pequeño (Android básico) | Crítica |
| **375×667** | iPhone SE | Crítica |
| **390×844** | iPhone 14 | Crítica |
| **412×915** | Android estándar (Pixel, Samsung) | Crítica |
| **430×932** | iPhone 15 Pro Max | Alta |
| **768×1024** | Tablet vertical (iPad) | Alta |
| **1440×900** | Desktop administrativo | Crítica |

---

## 3. MATRIZ DE PRUEBAS

| Feature | Chrome | Edge | Firefox | Safari | iOS Safari | Android Chrome |
|---|---|---|---|---|---|---|
| Login / Auth | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Formularios (todos) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tablas con filtros | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Date/Time Pickers | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Upload de archivos | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Gráficos (Recharts) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| i18n (ES/EN) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Responsive (todos los VP) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Modales / Dialogs | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Scroll horizontal (tablas) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Touch events (móvil) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 4. ESTRATEGIA DE PRUEBAS

### 4.1 Automatizadas (Playwright)

```typescript
// playwright.config.ts
export default defineConfig({
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
    { name: 'Mobile Safari', use: { ...devices['iPhone 14'] } },
    { name: 'iPhone SE', use: { ...devices['iPhone SE'] } },
    { name: 'iPad', use: { ...devices['iPad Pro'] } },
  ],
});
```

### 4.2 Manuales
- Opera (última versión)
- Samsung Internet
- Pruebas en dispositivo físico (iPhone, Android)

---

## 5. DEGRADACIÓN GRACIOSA

Para navegadores no soportados o muy antiguos:
- Mensaje de "Navegador no soportado" con enlaces para descargar Chrome/Firefox
- No se bloquea el acceso, pero se advierte de funcionalidad limitada

---

## 6. NOTAS TÉCNICAS

- **CSS Grid + Flexbox:** Soportado en todos los navegadores objetivo
- **TailwindCSS:** Genera CSS compatible con browserslist configurado
- **JavaScript ES2020+:** Vite transpila a target configurado
- **SVG:** Soportado en todos los navegadores
- **WebP:** Soportado en todos los navegadores modernos (fallback JPEG/PNG)
