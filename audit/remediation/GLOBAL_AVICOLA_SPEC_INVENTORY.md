# INVENTARIO NORMATIVO — GLOBAL AVÍCOLA

Auditoría maestra · 2026-09-08 · `HEAD = e245157` · **solo lectura, sin cambios de código**

---

## 1. Qué hay, y de qué tipo

| Familia | Ubicación | Nº | Papel normativo |
|---|---|--:|---|
| Spec de producto | `docs/00`…`docs/16` | 16 | **La autoridad de requisito de negocio.** Visión, spec funcional, modelo de dominio, plan técnico, contrato de API, estrategia SAP, flujo de aprobación, auditoría |
| Remediaciones | `specs/remediation/GA-REM-001…040` | 40 | Corrigen defectos concretos. **No** definen el producto |
| Decisiones de propietario | `specs/remediation/OD-09…OD-12` | 4 | `OD-01`…`OD-08` no son ficheros: viven **dentro** de sus `GA-REM` |
| Matrices y evidencia | `audit/remediation/` | 165 | Evidencia de ejecución, no norma |
| Auditorías previas | `audit/` | 22 | Histórico |

**El hallazgo estructural del inventario:** la norma de producto vive en `docs/`, y el trabajo
de los últimos meses vive en `specs/remediation/`. Son 40 remediaciones contra 16 documentos de
producto. La proporción explica por sí sola cómo se llegó hasta aquí: se ha estado corrigiendo
con mucho rigor sobre una superficie que nadie estaba comprobando contra `docs/02` y `docs/10`.

---

## 2. Los cuatro documentos que gobiernan las preguntas del propietario

| Documento | Qué decide | Estado frente al código |
|---|---|---|
| `docs/02-functional-spec.md` §3.1.4 | Aislamiento multicompañía, declarado **CRÍTICO** | **CONTRADICHO** en dos superficies · `F-A`, `F-B` |
| `docs/02-functional-spec.md` §3.2.1 | Empresas y Granjas son **catálogos base locales** | Coincide con el código; **contradice la expectativa del propietario** · `F-F` |
| `docs/10-sap-integration-strategy.md` §3.1 | Qué importa SAP: Centros, Almacenes, Materiales, Proveedores, Lotes | Ni Empresas ni Granjas figuran · `F-F` |
| `docs/03-domain-model.md` §686 | «La mayoría de entidades tienen `company_id`» | `Company` no lo tiene, y de ahí sale `F-B` |

---

## 3. `OD` reales, con su ubicación

| `OD` | Dónde vive | Tema |
|---|---|---|
| `OD-01`…`OD-08` | Dentro de `GA-REM-007`, `012`, `030`, `031`, `032`, `034`, `038`, `039` | Decisiones puntuales de cada remediación |
| `OD-09` | Fichero propio | Plano de control vs unidad de negocio |
| `OD-10` | Fichero propio | Contrato de traspaso y clasificación pendiente |
| `OD-11` | Fichero propio | Empresa efectiva de una petición |
| `OD-12` | Fichero propio | Contrato transversal SAP |

Las cuatro con fichero son de `GA-REM-040`. **Ninguna decisión formalizada cubre el origen de
los maestros ni la activación de módulos por empresa**, que son dos de las tres preguntas que
motivaron esta auditoría.

---

## 4. Lo que el inventario **no** encontró

```
activación de módulos por empresa       0 coincidencias en docs/ y specs/
compañías como maestro de SAP           0 coincidencias
granjas como maestro de SAP             0 coincidencias
entitlement · licencia · suscripción    0 coincidencias
```

Esto no significa que el propietario esté equivocado. Significa que **son requisitos que nunca
se escribieron**, y por tanto nunca se construyeron ni se certificaron. La distinción importa:
no es deuda de implementación, es ausencia de norma.
