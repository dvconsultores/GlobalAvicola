# `OD-18` · EL CATÁLOGO GENERAL DE EMPRESAS NO CONTIENE CONFIGURACIÓN DE INTEGRACIÓN SAP

Decisión de propietario · resuelve `AOD-12` · gobierna la forma de `R-127` · 2026-09-09 · **VIGENTE**
Alias: **`AOD-12 → OD-18`**.

```
CATÁLOGO DE EMPRESAS  =  IDENTIFICA EMPRESAS
CONFIGURACIÓN SAP     =  ASUNTO ADMINISTRATIVO APARTE
```

---

## 1. `OD-18.a` · la decisión

`GET /masters/companies` (y la lectura individual del catálogo) **no expone `sap_config`**. El
catálogo general devuelve **metadatos aprobados de identificación de la empresa**, con una
proyección explícita y acotada; nunca la fila entera del modelo.

El selector de empresa de la fase 9 **no necesita** configuración SAP: necesita identificar y
elegir (`id`, `name`, `is_active` como mínimo). La lista exacta de campos aprobados la fija la
spec que implemente `R-127`.

## 2. `OD-18.b` · la configuración SAP es un asunto separado

- Configurar la integración SAP de una empresa es una **superficie administrativa distinta**, con su propio contrato, permiso y evidencia, que **no existe todavía** y **no se diseña ahora** (`GA-REM-017 BLOCKED_EXTERNAL`; `SAP_INTEGRATION_READINESS_AUDIT §7`; `AOD-12` parte de persistencia).
- La **representación persistente** de esa configuración (`String` hoy; `JSON`/`JSONB` según `data-model.md:12`) queda **`DEFERRED`**: no se migra ahora. Corregir el catálogo no exige cambiar la columna.
- Los contratos de escritura (`CompanyCreate`, `CompanyUpdate`) que hoy aceptan `sap_config` **no forman parte del catálogo** y no se rediseñan en `R-127`; su tratamiento pertenece a la superficie administrativa futura.

## 3. Lo que sigue igual

- SAP es dueño del maestro oficial de empresa (Recomendación §1, §4). Esta decisión **no** avala un CRUD local de empresas como definitivo: las filas locales siguen siendo `SAP_DEFERRED_PLACEHOLDER` (`PL-05`) hasta la integración (`R-124` / `AOD-06`).
- `OD-14.c`: el catálogo de empresas es `CONTROL_GLOBAL` para la autoridad global —todas, con o sin contexto— y «solo la suya» para el actor de empresa. El contexto seleccionado **no** estrecha el catálogo global.
- `OD-16`: el catálogo identifica empresas; qué unidades opera cada una vive en `company_business_units`, otra superficie.

## 4. Trazabilidad

| Fuente | Relación |
|---|---|
| `R-127` (`REMEDIATION_BACKLOG.md:781`) | causa: `Company.sap_config` `String` tipado `dict`; `CompanyRead` lo valida como `dict` |
| `MASTER_PROGRAM_STATUS_RECONCILIATION.md §9` | clasificación `MODEL DEFECT · BLOCKER PHASE 9` |
| `PHASE_9_DEPENDENCY_PREFLIGHT.md §3` | única fuente del selector |
| `docs/02 §3.1.4` «Configuración SAP por compañía» | el campo es legítimo; **dónde se expone** es lo que aquí se decide |
