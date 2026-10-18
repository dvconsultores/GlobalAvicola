# 03 · Diseño del dataset `QA-DEMO-V1`

Contrato completo en `specs/007-qa-integral-demo-dataset/dataset-contract.md`. Resumen de diseño:

## Capas

```
empresas → roles(lookup) → usuarios → unidades (CBU/UBU) → fases(lookup) → maestros MAIN → maestros ISO → pasos de aprobación → SAP sintético
→ escenarios: lotes · aperturas manuales · fases de lote · historia (eventos aprobados por fastpath) · workflow real · correcciones · reverso
             · cancelación · consolidación · notificaciones · empresa ISO · cutover v2 aplicado por BU → fixtures XLSX → manifest
```

## Cobertura funcional por diseño

| Dimensión | Diseño |
|---|---|
| 4 BU | 5 lotes GP, 5 BR, 8 HAT, 5 BRO en MAIN (+2 en ISO) |
| Etapas | cría, producción, cercano a cierre (alerta), cerrado, cutover aplicado; incubadora en 6 etapas + ciclo generacional GP |
| Historia | 4–8 semanas: alimento, agua, pesaje semanal (con curva de peso), mortalidad, descarte, vacunación, medicación, inspecciones, huevos (recolección diaria en BR-PROD-001), despachos, recepciones, nacimientos, salidas, cierres |
| 28 tipos de evento | todos presentes (verificación «event types coverage») |
| Workflow | 11 estados internos poblados; 0 estados SAP |
| Segregación BR-14 | operador crea · supervisor revisa · aprobador aprueba/rechaza; caso «aprobador corrige» para demostrar la regla |
| Reverso OD-19 | recepción extra de 500 aves en QA-BRO-002 revertida con contrapartida aprobada |
| Cargas iniciales | 4 batches aplicados (UNKNOWN deliberado) + 4 XLSX libres |
| SAP | 14 objetos inbound staged, mappings, 47 referencias, OC coherentes con historia (BR-18), 1 pendiente de mapeo, 1 inválido |
| Multiempresa | ISO con 2 BU apagadas y usuarios/lotes propios |
| Móvil | `qa.mobile` (view_type mobile, BU broiler) |
| Notificaciones | leídas/no leídas + generadas por el motor (alertas de mortalidad/peso) |
| Reportes | 200+ eventos aprobados de alimento/peso/mortalidad/huevo |

## Trazabilidad

Prefijo `QA-` (códigos), `qa.` (usuarios), `QA_DEMO_V1` (marcador en `source_system`, `extra_data.qa_marker`, observaciones), `QA_SYNTHETIC` (SAP), `tax_id QA-DEMO-V1-*` (empresas), `run_id` en `source_reference`.
