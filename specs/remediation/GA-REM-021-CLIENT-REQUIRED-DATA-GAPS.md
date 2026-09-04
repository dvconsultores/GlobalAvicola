# GA-REM-021 — BRECHAS DE CAPTURA EXIGIDAS POR EL CLIENTE

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-021` · **Tipo** `REQUIREMENT GAP SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P1** · **Estado** `SPEC_READY` |
| **Dependencias** | `GA-REM-001` · **informada por** `GA-REM-020` (validación de cobertura) |
| **Hallazgo** | **R-13** — descubierto en la revalidación, **no estaba en la auditoría** |
| **Fuente** | `Imagen de Procesos Documentado/Bases Consideradas en el Desarrollo de la App Avicola.pdf` |

## Problema
El documento de requerimientos original del cliente exige el **consumo diario de agua** como dato obligatorio en tres de las cuatro etapas productivas. **No existe ningún campo de agua en el backend.** El frontend contiene una gráfica que lee `e.water_liters`, un campo inexistente, por lo que muestra una serie permanentemente en cero.

Este requisito **no aparece en `spec.md` ni en ninguno de los 16 documentos de `docs/`**: se perdió en la transcripción del requerimiento del cliente a la especificación del proyecto.

## Evidencia

### Exigencia del cliente
| Etapa | Cita textual | Página |
|---|---|---|
| Reproductora Fase Cría | «8. Consumo de Agua: Cantidad de agua consumida por los pollitos durante el día» | 2 |
| Reproductora Fase Producción | «11. Consumo de Agua: Cantidad de agua consumida por las gallinas durante el día» | 4 |
| Pollo de Engorde | «9. Consumo de Agua: Cantidad de agua consumida por los pollos durante el día» | 12 |
| Todas | «Optimización de Recursos: Ayuda a optimizar el uso de alimento, **agua** y otros recursos» | varias |

### Estado en la implementación
| Verificación | Resultado |
|---|---|
| `grep -rn "water\|agua" backend/app --include=*.py` | **0 resultados** |
| Campo en el modelo de eventos o submovimientos | **no existe** |
| `frontend/src/pages/reports/ReportsPage.tsx:30` | `if (e.water_liters) byDate[d].water_l += e.water_liters` — el campo nunca llega |
| `ReportsPage.tsx:127` | comentario: «matching old app: water, mortality, weight» — el sistema legacy **sí lo tenía** |
| Único «agua» en el frontend | `vaccination_route = "water"` («Agua de bebida») — una vía de vacunación, no consumo |

**El comentario del código confirma que el sistema legacy capturaba agua y que la nueva implementación lo perdió.**

## Comportamiento actual
La gráfica de consumo de agua existe en la interfaz de reportes y **siempre está vacía**. El operador no tiene dónde registrar el dato.

## Comportamiento esperado
El consumo de agua se registra a diario junto con el consumo de alimento y alimenta los KPI de optimización de recursos.

## Alcance
1. Confirmar, con la validación de `GA-REM-020`, en qué etapas de la taxonomía propia debe capturarse el dato.
2. Decidir dónde vive: campo en `feed_movements`, submovimiento propio, o campo en `operational_events`.
3. Captura en el formulario de las etapas donde el cliente lo exige.
4. Exposición en el reporte, sustituyendo la serie vacía.
5. Revisar si existen **otras** brechas del mismo tipo entre el documento del cliente y la implementación.

## Fuera de alcance
Sensores o telemetría automática · KPI de eficiencia hídrica avanzados · la cadena LIVIANAS.

## Revisión sistemática exigida
Esta spec debe verificar, punto por punto, la lista completa de datos diarios que el cliente exige por etapa, y no solo el agua. Hallazgos preliminares:

| Dato exigido por el cliente | Estado en la implementación |
|---|---|
| Consumo de agua | **AUSENTE** — objeto de esta spec |
| Condiciones ambientales (temperatura y humedad del galpón) | presente (`inspection_details`) |
| Alimento consumido | presente (`feed_movements`) |
| Peso de muestra representativa | presente (`bird_movements.avg_weight`, `sample_size`) |
| Mortalidad diaria | presente — **bloqueada por P0-1** |
| Incidencias de salud (enfermedad, tratamiento, vacunación) | presente |
| Huevos puestos / fértiles / infértiles / descartados | presente (`egg_movements.egg_type`) |
| Peso promedio de huevos | presente (`egg_movements.avg_weight`) |
| Almacenamiento de huevos: fecha, condiciones, duración | presente (`egg_storage`) — **sin spec del proyecto** → `SPEC_GAP`, ver `GA-REM-018` |
| Condiciones de transporte | presente (en `extra_data`) |
| Identificación de lote para trazabilidad | presente — **el emparejamiento está roto**, ver `GA-REM-008` |
| Pollitos nacidos: sanos / débiles | presente (`birth_registration` con filas viables y «Débiles») |
| Tasa de eclosión | **devuelve texto en lugar de número** → `GA-REM-022` |

## Base de datos afectada
**Sí.** Requiere columna nueva. Migración Alembic con docstring citando `GA-REM-021` y su AC (Art. 19 de la constitución).

## Acceptance Criteria
**AC01 — El dato se captura**
```
Given un operador en el formulario de registro diario de una etapa que lo exige
When  registra el consumo de agua del día
Then  el valor se persiste y es recuperable
```
**AC02 — La gráfica deja de estar vacía**
```
Given eventos con consumo de agua registrado
When  se consulta el reporte del lote
Then  la serie de consumo de agua muestra los valores registrados
```
**AC03 — Cobertura por etapa**
```
Given las etapas donde el cliente exige el dato
When  se abre el formulario correspondiente
Then  el campo de consumo de agua está disponible en todas ellas
```
**AC04 — Revisión sistemática completada**
```
Given la lista de datos diarios exigidos por el cliente
When  se contrasta contra la implementación
Then  cada elemento tiene estado documentado
And   las brechas encontradas están registradas como hallazgos
```
**AC05 — Trazabilidad al requerimiento del cliente**
```
Given el campo implementado
When  se consulta su spec
Then  cita la fuente del cliente que lo exige, con página
```

## Riesgos
| Riesgo | Mitigación |
|---|---|
| Añadir un campo obligatorio rompe la captura actual | el campo es opcional en la primera iteración |
| La revisión sistemática revela más brechas de las previstas | es el objetivo: mejor descubrirlas ahora que en producción |

## Definition of Done
- [ ] Revisión sistemática completa documentada · [ ] AC01–AC05 verificados · [ ] Migración con docstring trazado · [ ] Certification report
