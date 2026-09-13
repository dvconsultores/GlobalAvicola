# GA · PRE-SAP — PLAN DE RECERTIFICACIÓN UAT DEL PROPIETARIO (TRANCHE 0 · §10/§32/§33)

Preservación: **ningún registro histórico de aceptación se borra ni se reescribe**. Se clasifica su calidad conforme a §10 y se define la revalidación mínima.

## 1 · Clasificación de los registros históricos (§10)

Leyenda: `PRIMARY_VERIFIED` = evidencia primaria del propietario verificable · `RECORDED_NIV` = registrado pero no verificable independientemente · `REVALIDATE` = requiere UAT del propietario para revalidar · `NOT_REQUIRED` = no requiere UAT nueva.

| Registro | Alcance | Evidencia | Clase | Por qué |
|---|---|---|---|---|
| GA-UAT-01…06 | operativos/dashboard/navegación | walkthrough del agente; capturas propias | `RECORDED_NIV` | Sin artefacto del propietario (mensaje/captura/grabación/`LOGIN` en `audit_logs`) |
| GA-UAT-07 (R-187 IPE) | IPE | capturas duplicadas byte a byte; ventana 34 s | `RECORDED_NIV` (degradada) | Casos distintos con misma imagen (md5 iguales); además IPE contaminado por R-131/Wave C |
| GA-UAT-08 (R-188 BU) | BU ON/OFF | 9 capturas en 64 s; limpieza +46 s antes de decisión C2 | `RECORDED_NIV` (degradada) | El propietario no pudo recorrer los casos con BU OFF/usuarios de baja en el momento de decidir |
| GA-FE-08 (R-118 grant/nav) | permisos FE | 6 pares de capturas duplicadas | `RECORDED_NIV` (degradada) | Ídem |
| Negativos históricos (FVA-* / VNC) | varios | observaciones | `RECORDED_NIV` | 19 filas VNC sin AC (RES-07) |
| GA-UAT-09 (R-153/R-189) | importación + recepción progenitoras | **pendiente** | `REVALIDATE` (pendiente por diseño) | Sesión del propietario aún no ejecutada; credenciales preservadas (`~/ga_uat09_credentials.txt`) |
| 19-VNC CERT-PATH C (entrega 2, fila 14) | 8 filas con UAT | pendiente | `REVALIDATE` | Plan de 19 sin ejecutar |
| OD-19 (reverso) | reverso interno | n/a | `REVALIDATE` (condicionado a OD-19 §18) | Capacidad sin UI; si se construye, UAT nueva |

**Ningún registro histórico alcanza `PRIMARY_VERIFIED`**; la regla §32 se aplica hacia adelante.

## 2 · Regla nueva del modelo UAT (§32)

1. **Decisión del propietario**: registrada con fecha, canal y **texto exacto** (más lote de casos y hash del artefacto de walkthrough del equipo). El walkthrough del equipo es **evidencia técnica**, nunca aceptación.
2. **Evidencia primaria admisible**: mensaje del propietario, captura/grabación propia, o su `LOGIN` en `audit_logs` durante la ventana declarada; las capturas del equipo deben ser **discriminantes** (sin duplicados md5 entre casos distintos).
3. **Limpieza**: solo **después** de la decisión registrada y verificada; con artefacto de limpieza.
4. Un PASS por caso no se deriva de una «A» global: cada caso lleva su resultado y, si aplica, su observación.

## 3 · Revalidación mínima (agrupada, §33)

| Lote UAT final | Casos (resumen) | Procesos | Histórico relacionado | Evidencia mínima exigida |
|---|---|---|---|---|
| **U1 · Plataforma y seguridad** | login; **logout con revocación (AC04)**; rol sin wildcard (R-199); refresh no usable como access; reset en contexto; permisos batch; switch de empresa/BU | P-13, X-BU | GA-UAT-08, GA-FE-08 (revalidación dirigida) | 1 designación + decisión con texto + capturas discriminantes (usuario admin real) + `LOGIN`/`LOGOUT` en `audit_logs` |
| **U2 · Progenitoras** | **GA-UAT-09 retry (R-153/R-189)**; import 121 → recepción 122 → población 100; ubicación BR-08; BR-18/BR-20 | P-01, OD-25 | GA-UAT-09 pendiente; GA-F01 | Decisión del propietario sobre los 3 casos C1/C2/C3 del ledger GA-R153 + artefactos de corrida |
| **U3 · Reproductoras** | curvas; distribución por galpón (BR-17); recepción BR-20 por navegación natural | P-03 | GA-UAT-04/06 | Decisión + capturas discriminantes |
| **U4 · Incubadora** | huevos fértiles; carga; nacimiento (BR-21); despacho (BR-04); KPIs incubadora por unidad | P-04, P-05 | — (histórico P-04/P-05 degradado) | Ídem |
| **U5 · Engorde y cierre** | pesajes g/kg; alimento; cierre de lote; cierre tras reverso; FCR/peso final (decisión AOD-08/10) | P-06, OD-19 | GA-UAT-07 (IPE) | Ídem |
| **U6 · Revisión y reverso** | bandejas (in_review); aprobación multinivel (si AOD-17); reverso interno UI (si OD-19 §18); cancelación con motivo (si AOD-18) | P-07 | — | Ídem |
| **U7 · Reportes y trazabilidad** | KPIs corregidos (R-204/Wave C), IPE (revalidación R-187), trazabilidad 3 generaciones, auditoría visible | P-15, P-10, P-09 | GA-UAT-07 | Ídem |
| **U8 · Maestros y usuarios** | alta maestros completa; edición usuario; activación manual (si UI); notificaciones | P-12, P-13, P-11, P-14 | — | Ídem |

**Minimización**: 8 lotes cubren 11 registros históricos relevantes + 2 pendientes + todos los procesos con cambio visible. Los lotes U1-U2 tienen prioridad (seguridad y el pendiente GA-UAT-09).

## 4 · Criterio de cierre UAT (§33/§34)

- Cada lote: decisión registrada (texto exacto) + evidencia primaria adjunta + resultado por caso.
- Limpieza posterior con artefacto (fixtures, usuarios/roles/lotes de prueba, credenciales) — incluida la limpieza post-decisión de GA-UAT-09 ya pendiente.
- Si un lote revela un defecto: vuelve a su tranche (o a una micro-tranche correctiva) y el lote se repite; no se acepta con reservas no escritas.
