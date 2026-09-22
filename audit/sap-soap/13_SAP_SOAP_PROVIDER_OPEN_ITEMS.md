# SAP-SOAP · 13_SAP_SOAP_PROVIDER_OPEN_ITEMS

Fecha: 2026-09-22 · Lista corta para la próxima reunión (§40) · Separada por responsable: **SAP_PROVIDER_CLARIFICATION** (lo técnico que resuelve el proveedor), **OWNER_DECISION** (mínimo), **GA_DECISION** (ya resuelto por GA, no se pregunta)

---

## 1 · SAP_PROVIDER_CLARIFICATION (a llevar a la reunión)

| # | Tema | Pregunta concreta | Impacto si se demora |
|---|---|---|---|
| OI-01 | WSDL/entorno | ¿Dónde publicarán WSDL/sandbox (URL, auth de red)? | bloquea SOAP-5 |
| OI-02 | Estilo/binding | ¿document/literal wrapped + namespace propuesto OK? | cosmético, ajuste de ejemplos |
| OI-03 | Paginación | ¿`ContinuationToken` factible? ¿PageSize máx real por operación? | diseño de jobs |
| OI-04 | Delta por objeto | ¿Qué campo de cambio existe por objeto (timestamp/seq)? | estrategia delta |
| OI-05 | `GetIntegrationChanges` | ¿Ofrecen endpoint incremental común? ¿Forma? | alternativa de sincronización |
| OI-06 | Autenticación | ¿WS-Security UsernameToken, mTLS o Basic-over-TLS? ¿Allowlist? | bloquea SOAP-5/6 |
| OI-07 | Versionado | Confirmar `SchemaVersion=1.0` y política de cambios breaking | gobernanza |
| OI-08 | Outbound orders | ¿De dónde salen realmente (prod order/STO/doc material)? ¿Campos disponibles? | mapeo de dominio |
| OI-09 | Vendors | ¿Business Partner/CVI activo? ¿LIFNR = BP number? | maestro proveedor |
| OI-10 | Production orders | ¿Cuáles de los campos candidatos existen realmente? | contrato final |
| OI-11 | Cost centers | Confirmar exclusión de fase 1 (o argumentar entrada) | scope |
| OI-12 | Volumen/frecuencia | Estimaciones de volumen por objeto y ventanas de mantenimiento | sizing |
| OI-13 | Errores | Implementar la lista cerrada `07_…` (8 códigos) tal cual | interoperabilidad |
| OI-14 | Ejemplos | Devolver WSDL preliminar + ejemplos adaptados | arranque SOAP-2 |
| OI-15 | Datos de prueba | Dataset sandbox para reconciliación (pequeño, sintético o enmascarado) | SOAP-5/7 |
| OI-16 | BWART | ¿641/303 siguen siendo los tipos operativos relevantes? ¿Otros? | semántica movimientos |

## 2 · OWNER_DECISION (mínimo indispensable)

| # | Decisión | Contexto | Recomendación GA |
|---|---|---|---|
| OD-1 | Confirmar alcance fase 1 (13 objetos) y **deferral de COST_CENTER** | §5 del mandato lo pide validar; GA no tiene consumidor hoy | Aprobar deferral |
| OD-2 | Formalizar/llevar acta de decisión SOAP a go-live docs cuando corresponda | coherencia DAG (GL-OD-06 sigue `BLOCKED_EXTERNAL_SAP_INFORMATION` hasta evidencia real) | Sin cambio de estado ahora |

## 3 · GA_DECISION (resueltas internamente — NO se preguntan)

| Decisión | Valor | Fundamento |
|---|---|---|
| Modelo de dirección | **PULL** (GA consulta) | §3 del mandato; si SAP requiere PUSH → vuelve como decisión |
| Estructura PO | header + **items anidados** | §15; evita operación extra |
| Categorías de material | resueltas en **GA** (mapping), no en SAP | §14; anti-hardcode |
| RAW/STAGING | retenido con campos SOAP añadidos | §26 |
| Interfaz adaptador | nuevo ABC inbound separado del export | `12_…`; no romper GA-REM-010 |
| Transporte de secretos | pendiente custodia `AOD-12` | no bloquea contrato |

## 4 · Regla de gobierno

Ningún ítem de §1 se “resuelve” por suposición: se registra la respuesta del proveedor y se versiona el contrato si aplica. Los ítems §2 vuelven al Owner en el paquete de la próxima reunión. Los §3 no se re-abren sin causa técnica nueva.
