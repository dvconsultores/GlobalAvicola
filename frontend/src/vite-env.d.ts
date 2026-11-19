/// <reference types="vite/client" />

// SPEC 016 §B (D-B3): procedencia del build inyectada por `define` en vite.config.ts.
// Nunca se muestran en pantalla; `main.tsx` publica el SHA como atributo del documento.
declare const __GA_BUILD_SHA__: string
declare const __GA_BUILD_TIME__: string
