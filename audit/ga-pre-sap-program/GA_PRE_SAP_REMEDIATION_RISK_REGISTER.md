# GA · PRE-SAP — REGISTRO DE RIESGOS DEL PROGRAMA DE REMEDIACIÓN (§53)

Escala: Probabilidad (B/M/A) · Impacto (B/M/A/Crítico). Cada riesgo tiene mitigación integrada en el roadmap y gate de cierre.

| # | Riesgo | Prob. | Impacto | Specs/tranches afectadas | Mitigación | Gate de cierre |
|---|---|---|---|---|---|---|
| 1 | **Regresión de seguridad** (R-199/200 mal resueltos o wildcard reaparece) | M | Crítico | R-199, R-200, AC04 (T2) | Tests de ataque por spec; revisión de `security.py` completo; ninguna otra tranche toca `auth` después de T2 | T2: ataques bloqueados con artefacto; T12: regresión OD-14/OD-16 verde |
| 2 | **Fuga entre compañías** en superficies corregidas (KPIs, SAP, tenencia) | M | Crítico | R-201, R-203, R-204, R-221 (T3) | Escenarios de ataque multicompañía por spec; suite OD-14/OD-16 como regresión obligatoria de cada tranche | T3 y T12 |
| 3 | **Regresión multicompañía/BU** por tocar servicios compartidos | M | A | T3-T11 (servicios `lots`, `operations`, `review`, `reports`) | Matriz de touchpoints; un responsable por fichero; serialización por familias | Gate de cada tranche: suite completa verde |
| 4 | **Corrupción de datos** en cierre/reversos (T7) | B | Crítico | R-192, R-193, R-211 | Tests de saldos netos y cierre tras reverso; validar contra datos sintéticos espejo antes de tocar lógica | T7: casos RED→GREEN con artefacto; sin migraciones |
| 5 | **Regresión de saldos** (BR-17/BR-18) | M | A | T7 | Casos límite (n, 2n, contrapartidas, multi-galpón) en AC matrix; E2E P-01/P-02/P-03 | T7: AC completos verdes |
| 6 | **Conflicto de migraciones** (guardas caducadas, cabeza múltiple) | B | M | T1 (guards), Pista OPS (política de migraciones) | Guardas por import del head real (no literal); verificación `alembic heads` único en cada tranche | T1 y cada tranche |
| 7 | **Regresión de autenticación/sesión** (logout rompe refresh legítimo) | M | A | T2 (R-200, AC04) | Tests de ciclo completo login→refresh→logout→denylist; FE existente no cambia flujo visual | T2: ciclo verde; U1 en T13 |
| 8 | **Deriva FE↔BE** en contrato de captura | M | A | T4-T6 | Contrato fijado por spec (payload canónico); tests de contrato en ambas capas; E2E del proceso | Gates de T4-T6 |
| 9 | **Colisión de fichero compartido** (dos specs en un fichero) | M | M | Familias `captura FE`, `validators`, `audit`, `auth` | Matriz de touchpoints + serialización por familias + declaración de ficheros en cada commit | Verificación previa de cada tranche |
| 10 | **Deriva de tests** (corregir fixtures escondiendo defectos) | M | M | T1-T11 | Clasificación caso a caso ya hecha (37 TEST_DEFECT, 0 APP_DEFECT); fixtures se ajustan a la regla, no al revés | T1 y gates de tranche |
| 11 | **Runtime obsoleto** (certificar sobre build antiguo) | M | A | Todas (especialmente T12) | Paridad bundle==build y marcadores backend en cada cierre; chequeo de drift pre-tranche | Gates de tranche + T12 |
| 12 | **UAT del propietario inválida** (repetición del patrón sin evidencia primaria) | M | Crítico | T13 (U1-U8) | Modelo §32: decisión con texto exacto + evidencia primaria + capturas discriminantes + limpieza post-decisión | T13: checklist por lote |
| 13 | **Limpieza de datos de prueba** insuficiente o prematura | M | M | T13 (post-decisión) | Limpieza solo tras decisión registrada, con artefacto; fixtures aislados por lote | T13 |
| 14 | **Acoplamiento prematuro a SAP** | B | A | Fase SAP | P-08 fuera de alcance; programa termina en GO pre-SAP; eventos SAP solo se definen tras T12 | FUERA de T1-T13 |
| 15 | **Wave C no decidida** bloquea T12 (P-15/P-06) | A | A | AOD-10/AOD-08 (T12) | Pregunta elevada al propietario en el lote de decisiones; plan alternativo: si «aceptar documentado», se registra y T12 sigue | Antes de T12 |
| 16 | **Pista OPS incompleta** (evidencias efímeras/BD expuesta) bloquea gate | M | Crítico | R-52, AC03/AC07, P1-6 | Arrancar OPS ya; evidencia operativa por ítem; dueño operativo asignado | T13 |
| 17 | **Backlog vuelve a divergir** (nuevos hallazgos sin registro) | M | M | Gobernanza continua | Regla: ningún hallazgo sin ficha en backlog (T1 la restablece); revisión por tranche | Cada tranche |
| 18 | **Cabecera de histórico UAT borrada por error** | B | A | T13 | Este programa solo clasifica calidad; prohibido borrar registros históricos | T13 |

## Priorización de riesgos

- **Críticos** (seguridad/tenant/datos/UAT/OPS): #1, #2, #4, #12, #16 — sus mitigaciones ya están en T2/T3/T7/T13/OPS.
- **Altos**: #3, #5, #7, #8, #11, #14, #15.
- **Medios**: #6, #9, #10, #13, #17, #18.
- Todo riesgo con gate asignado queda **abierto hasta su tranche**; el cierre del programa exige que ninguno quede sin evidencia de mitigación.
