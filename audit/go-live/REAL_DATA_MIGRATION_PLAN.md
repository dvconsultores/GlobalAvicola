# GLOBAL AVÍCOLA — REAL DATA MIGRATION PLAN (Cutover de datos reales)

Fecha: 2026-09-17 · Baseline: `fef7289` · Estado: **SPEC/PLAN (sin ejecución)**
Regla dura: **no se inventa información faltante** — lo que no exista se declara `UNKNOWN` y se decide.

---

## 1 · Distinción de capas (mandato §4)

| Capa | Definición | Custodia |
|---|---|---|
| **SOURCE DATA** | Dato real tal como lo entrega el negocio (planillas, registros del sistema anterior, libros de granja) | Negocio (Owner) |
| **TRANSFORMED DATA** | Dato mapeado a la plantilla de la BU (códigos maestros, fechas ISO, unidades, UNKNOWN explícito) | Equipo de datos (transformación en borrador sobre copia) |
| **STAGING DATA** | Archivo subido al batch + filas normalizadas en `CutoverStagingRow` (sin efecto operacional) | Sistema (evidencia con checksum) |
| **CERTIFIED OPENING DATA** | `OpeningBalance` aplicado tras apply atómico + reconciliado + firmado en acta | Sistema (fuente de verdad operacional) |

## 2 · Dominios y datos requeridos (determinación exacta — mandato §4)

| # | Dominio | Datos requeridos | ¿Existe hoy? | Acción |
|---|---|---|---|---|
| D1 | **Empresas reales** | Razón social, RIF/ID fiscal, estado, unidades encendidas (OD-16) | No (solo `Avícola Global C.A.` de modelo) | Owner confirma empresas reales y sus BUs |
| D2 | **Unidades productivas (BU)** | Cuáles operan hoy (grandparent/breeder/hatchery/broiler) y desde cuándo | No | Decisión + verificación |
| D3 | **Granjas** | Código, nombre, ubicación, tipo | No (7 demo/fixtures) | Plantilla maestros reales |
| D4 | **Galpones** | Código, capacidad, granja | No (34 fixtures) | idem |
| D5 | **Lotes vivos** | `legacy_lot_code`, granja/galpón, `real_start_date`, genética, sexo, estado actual | No | Plantilla por BU (ave) |
| D6 | **Genética** | Línea genética por lote (Ross/Cobb/nativas) | Parcial (2 líneas seed) | Confirmar catálogo real |
| D7 | **Edades** | Derivadas de `real_start_date` (no se "declaran": se calculan) | — | Automático |
| D8 | **Poblaciones actuales** | Aves vivas al corte por lote | No | Campo obligatorio del archivo |
| D9 | **Mortalidad acumulada** | Total histórico por lote hasta el corte (si conocido) | No | KNOWN/UNKNOWN explícito |
| D10 | **Alimento acumulado** | kg consumidos hasta el corte (por lote) | No | idem |
| D11 | **Pesos** | Último peso promedio por lote (fecha de pesaje) | No | idem (si no hay: UNKNOWN) |
| D12 | **Inventarios operacionales** | Huevos en almacén, incubación en curso, medicación/vacunas en uso | No | Definir universo (GL-OD-07) |
| D13 | **Maestros** | Alimentos, causas mortalidad/descarte, vacunas, medicamentos, proveedores, transportes, fases | Modelo seed (no real) | Catálogo real del negocio |
| D14 | **Usuarios** | Personas reales, email, rol, BU(s) concedidas | No | Alta gobernada con admin (GL-OD-11) |
| D15 | **Roles** | Roles reales vs catálogo del producto (permiso es de producto, rol tiene alcance — OD-13) | No | Mapeo rol real → permisos |
| D16 | **Business Units por usuario** | Grants BU por usuario/empresa (fail-closed, OD-09/OD-16) | No | Matriz usuarios×BU |
| D17 | **Saldos/aperturas necesarios** | Openings por lote + no-lote (según D5-D12) | No | Plantilla de cutover |
| D18 | **Datos que NO deben migrarse** | Histórico sin valor operacional, registros del sistema viejo no auditables | No | Declaración formal (GL-OD-07) |

## 3 · Mapeo a plantillas existentes

- Cada dominio D3–D13 se mapea a **maestros reales** cargados primero (vía administración de maestros, no vía cutover).
- D5–D11 se mapean a la **plantilla de la BU** (`grandparent|breeder|hatchery|broiler v1.xlsx`), donde:
  - **celda vacía = UNKNOWN** · `0` = cero conocido · `N/A` = no aplica;
  - referencias a maestros **por código** (farm_code, house_code…) validados contra la BD (`MASTER_NOT_FOUND`/`MASTER_INACTIVE`);
  - consistencia si todos los componentes KNOWN: `placed − mortality − culls − transfers_out + transfers_in = live_at_cutover` (si no cuadra y todo es KNOWN ⇒ `CONSISTENCY_MISMATCH` bloquea);
  - incubadora: proceso en curso (carga activa, etapa, fechas) según §4 de GA-REQ-061 (auditoría fina al implementar).
- D14–D16 se cargan por **administración de acceso** (no por cutover).
- D17 = salida del apply del batch.

## 4 · Transformación (reglas)

1. Códigos: se crean/confirman códigos reales en maestros ANTES de subir; el archivo referencia códigos, nunca IDs.
2. Fechas ISO; números sin formato local; unidades declaradas en la hoja `Instrucciones`.
3. `legacy_lot_code` = identidad externa real (se conserva; el `lot_code` canónico lo decide el sistema).
4. **Nada se completa "por parecido"** — cualquier inferencia debe estar aprobada por el responsable funcional y documentada fila a fila.
5. Transformación en borrador sobre **copia**, nunca directamente sobre producción.

## 5 · Preguntas abiertas al negocio (input para G1)

1. ¿Cuál es el sistema/registro de origen por dominio (papel, Excel, otro software)?
2. ¿Existen cortes contables/operativos que fijen una fecha natural de cutover?
3. ¿Hay lotes sin genética conocida o sin fecha de inicio confiable? (→ UNKNOWN declarado)
4. ¿Qué histórico NO vale la pena migrar y por qué? (D18)
5. ¿Quién es el responsable funcional que valida fila a fila y firma el acta?
6. ¿Hay datos de terceros (integrados, genética de clientes) con restricciones de uso?

## 6 · Seguridad y custodia de datos reales

- Rehearsal con **set sanitizado** (R2) o sintético representativo primero; datos reales completos solo en el apply final autorizado.
- Acceso mínimo: transformadores + aprobador funcional; archivos con checksum y control por empresa (mismo control que batches).
- Este plan **no imprime ni transporta secretos**; los archivos reales no se versionan en git (van al batch y a evidencia controlada, no al repositorio).

## 7 · Criterio de completitud de esta fase de datos

La migración se declara lista cuando: (a) D1–D18 tienen fuente y responsable; (b) rehearsal R2 pasa con el set sanitizado; (c) acta firmada del rehearsal; (d) `GL-OD-06/07` resueltas. **Hoy: pendiente de acceso a datos (DATA-01).**
