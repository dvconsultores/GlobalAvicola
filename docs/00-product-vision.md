# Global Avícola — Visión del Producto

> **Documento:** 00-product-vision.md
> **Versión:** 1.0.0
> **Fecha:** 2026-06-22

---

## 1. NOMBRE DEL PRODUCTO

**Global Avícola**

---

## 2. PROPUESTA DE VALOR

Global Avícola es la **plataforma empresarial de gestión operativa avícola** que funciona como capa auxiliar inteligente de SAP. Mientras SAP mantiene el control administrativo, contable y de inventario formal, Global Avícola gestiona la operación diaria en campo con un flujo obligatorio de **registro → revisión → corrección → aprobación → consolidación → envío a SAP**, garantizando trazabilidad completa, auditoría interna y control de calidad en cada paso del ciclo productivo avícola.

---

## 3. VISIÓN DEL PRODUCTO

Ser la plataforma estándar de gestión operativa avícola integrada con SAP para empresas del sector en Latinoamérica, reconocida por su:

- **Confiabilidad operativa** — Datos trazables desde el campo hasta SAP
- **Control de calidad** — Revisión y aprobación multinivel antes del registro contable
- **Diseño profesional** — Experiencia móvil de campo y web ejecutiva de alto nivel
- **Auditabilidad total** — Cada acción registrada, cada corrección documentada
- **Flexibilidad de integración** — Adaptable a cualquier entorno SAP (ECC, S/4HANA)

---

## 4. PROBLEMA QUE RESUELVE

### Problemas del sistema actual (legacy "Lider Pollo"):

1. **Sin control de calidad** — Los registros operativos van directo a SAP sin revisión ni aprobación
2. **Sin auditoría** — No se sabe quién modificó qué, cuándo ni por qué
3. **Sin trazabilidad** — No hay historial de cambios ni versiones de registros
4. **Sin integración SAP real** — Solo campos `id_sap` sin lógica de sincronización
5. **Sin segregación de funciones** — El operador registra y el mismo dato puede enviarse sin control
6. **Diseño no corporativo** — La app móvil (Flutter, tema oscuro) no proyecta imagen empresarial
7. **Arquitectura duplicada** — Tablas repetidas para cada fase productiva
8. **Deuda técnica acumulada** — Sin tests, sin migraciones, validación débil

### Lo que Global Avícola ofrece:

1. ✅ **Flujo de aprobación completo** — Registro → Revisión → Corrección → Aprobación → SAP
2. ✅ **Auditoría total** — Cada click registrado con usuario, timestamp, valor anterior/nuevo
3. ✅ **Trazabilidad por lote** — Desde abuelas hasta engorde, todo trazable
4. ✅ **Integración SAP real** — Capa de abstracción desacoplada lista para cualquier mecanismo
5. ✅ **Roles y permisos granulares** — Operador ≠ Supervisor ≠ Aprobador ≠ SAP
6. ✅ **Diseño corporativo blanco/azul** — Mobile-first para campo, web ejecutiva para oficina
7. ✅ **Arquitectura limpia unificada** — Un modelo de datos normalizado sin duplicación
8. ✅ **Ingeniería de software profesional** — Tests, CI/CD, migraciones, documentación OpenAPI

---

## 5. USUARIOS OBJETIVO

| Perfil | Dispositivo principal | Necesidades clave |
|---|---|---|
| **Operador de granja** | Móvil (teléfono) | Formularios rápidos, guardado simple, validaciones visibles |
| **Operador de incubadora** | Móvil / Tablet | Registro de parámetros, clasificación, nacimientos |
| **Operador de engorde** | Móvil | Pesajes, mortalidad, consumo de alimento |
| **Supervisor avícola** | Web escritorio | Bandeja de revisión, comparación de datos, KPIs |
| **Veterinario** | Web / Móvil | Registro de vacunas, medicamentos, alertas sanitarias |
| **Aprobador / Coordinador** | Web escritorio | Panel de aprobación, consolidación, envío a SAP |
| **Analista SAP** | Web escritorio | Gestión de integración, errores SAP, sincronización |
| **Auditor interno** | Web escritorio | Vista de auditoría, trazabilidad, reportes |
| **Administrador** | Web escritorio | Gestión de usuarios, roles, maestros, configuración |

---

## 6. DIFERENCIADORES CLAVE

### 6.1 Centro de Revisión Operativa
Un módulo único donde los supervisores pueden:
- Ver todos los registros pendientes de revisión
- Comparar datos cargados vs datos esperados (SAP)
- Corregir valores (conservando el original)
- Devolver al operador con observaciones
- Aprobar individualmente o por lote

### 6.2 Aprobación Multinivel Configurable
- Nivel 1: Operador registra
- Nivel 2: Supervisor revisa
- Nivel 3: Coordinador aprueba
- Nivel 4: Integración SAP consolida/envía
- Configurable por empresa: 1, 2 o 3 niveles

### 6.3 Auditoría Inmutable
Cada acción queda registrada:
- Quién, qué, cuándo, dónde, valor anterior, valor nuevo, motivo
- No se borra nada — eliminación lógica con trazabilidad
- Vista de auditoría para administradores y auditores

### 6.4 Integración SAP Desacoplada
- Capa de abstracción que permite cambiar el mecanismo (API, archivo, OData, BAPI, RFC)
- No depende de un tipo específico de SAP
- Idempotencia garantizada
- Bitácora de envíos y respuestas

### 6.5 Trazabilidad de Lote Completa
Desde la importación de abuelas hasta el despacho a planta de beneficio, cada movimiento está vinculado al lote origen y al lote destino.

---

## 7. PRINCIPIOS RECTORES

1. **SAP es el sistema principal administrativo.** Global Avícola es auxiliar operativo.
2. **Ningún dato va a SAP sin aprobación.**
3. **Todo movimiento es auditable.**
4. **Toda corrección conserva el valor original.**
5. **Mobile-first real.** El operador de campo es el usuario más importante.
6. **Diseño corporativo.** Blanco y azul, limpio, profesional.
7. **Bilingüe desde el inicio.** Español e inglés.
8. **Código limpio, testeado, documentado.**
9. **No copiar deuda técnica del legacy.**
10. **Spec-Driven Development.** Especificar antes de codificar.

---

## 8. MÉTRICAS DE ÉXITO

| Métrica | Objetivo |
|---|---|
| Tiempo de registro operativo en móvil | < 60 segundos por formulario |
| Tiempo de revisión por lote | < 5 minutos |
| Trazabilidad completa | 100% de registros trazables |
| Errores de envío a SAP | < 1% con reintento automático |
| Cobertura de tests | > 80% backend, > 70% frontend |
| Compatibilidad navegadores | 100% en Chrome, Edge, Firefox, Safari, Opera |
| i18n | 100% de textos visibles traducidos (ES/EN) |
| Tiempo de carga móvil | < 3 segundos en 4G |

---

## 9. NO-OBJETIVOS (fuera del alcance inicial)

- Reemplazar SAP como sistema contable
- Módulo de nómina o RRHH
- Facturación electrónica
- Integración con otros ERPs que no sean SAP
- App nativa (iOS/Android) — se usa PWA si aplica
- Machine Learning / IA predictiva (versión futura)
- IoT / Sensores en tiempo real (versión futura)

---

## 10. RESUMEN EJECUTIVO

**Global Avícola** transforma la gestión operativa avícola de un modelo de registro directo sin control a un **ecosistema empresarial de trazabilidad, calidad y auditoría**, integrado con SAP como sistema administrativo principal. No es una migración técnica del legacy — es una **reingeniería completa** que extrae el conocimiento funcional del sistema anterior y lo reconstruye con estándares modernos de ingeniería de software, diseño profesional y arquitectura preparada para el futuro.
