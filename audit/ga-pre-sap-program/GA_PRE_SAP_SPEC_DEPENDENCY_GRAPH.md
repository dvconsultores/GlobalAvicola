# GA · PRE-SAP — GRAFO DE DEPENDENCIAS ENTRE SPECS (TRANCHE 0 · §21)

## 1 · Aristas (depende_de → desbloquea)

Leyenda: **[F]** = serialización por fichero compartido · **[S]** = dependencia semántica (contrato/estado) · **[G]** = dependencia de gate (suite/verde/certificación).

| Spec | Depende de | Desbloquea a | Tipo | Fichero/frontera compartida | Proceso (BU) | Riesgo de la arista | ¿Paralelizable? |
|---|---|---|---|---|---|---|---|
| GA-GOV-03 | — (raíz) | **todas** (T2-T13) | [G] | `backend/tests/**`, `e2e/**`, `.github/workflows/**` | Todos (gobernanza) | Si no se hace primero, ninguna certificación es válida | No (es el gate de arranque) |
| R-199 | GA-GOV-03 | R-200, R-202, AC04, R-208 (permisos) | [F] | `auth/service.py` | P-13 | Colisión directa si se ejecuta al revés | No (serial dentro de T2) |
| R-200 | R-199, GA-GOV-03 | AC04 | [F][S] | `auth/security.py` | P-13 | Medio (mismo módulo) | No (serial) |
| GA-REM-003 AC04 | R-200 | T13 (UAT sesión) | [S] | `auth/router.py` (nuevo) | P-13 | Diseño del denylist | No (serial T2) |
| R-202 | R-199 | — | [F] | `auth/service.py` | P-13 | Bajo | Sí (paralelo dentro de T2 con otro autor, mismo módulo con cuidado) |
| R-208 | GA-GOV-03 | R-197 (T10) | [F] | `review/router.py` | P-07 | Bajo (solo dependencias de permiso) | Sí (T2, no toca servicio) |
| R-201 | GA-GOV-03; fase SAP | Fase SAP (GO(A)) | [S] | `integrations/sap/service.py` | P-08 | Medio | Sí (T3) |
| R-203 | GA-GOV-03 | R-192 (T7, mismo servicio) | [F] | `lots/service.py`, `masters` | P-12 | Medio-alto (tenencia) | Sí (T3, antes de T7) |
| R-204 (+R-216) | GA-GOV-03 | T12 (P-04/P-15) | [F] | `reports/service.py`, `dashboard/service.py` | P-04/P-15 | Medio | Sí (T3) |
| R-221 | GA-GOV-03; AOD-13 | T12 | [F] | `operations/service.py` | P-12 | Medio (unidad) | Sí (T3, antes de T5) |
| R-190 | T1-T3; — | R-205 (misma tranche), R-194 (T6) | [F][S] | `OperationFormPage.tsx` | P-01/P-03 | Alto dentro de la familia FE | No (primero de la familia) |
| R-205 | R-190 | T12 (P-03) | [F] | `OperationFormPage.tsx` | P-03 | Medio | Con R-190 (misma tranche, orden interno) |
| R-191 | T1-T3 | — | [F] | `lots.service.ts`, `LotDetailPage.tsx` | P-11 | Bajo | Sí (T5, distinto de payload) |
| R-206 | — | R-209/R-210 (misma tranche) | [F] | `operationPayload.ts` | P-02/P-09 | Medio (serialización) | No (primero de payload) |
| R-209 | R-206 | — | [F] | `operationPayload.ts`, `operations/service.py` | P-01/P-09 | Medio | Serial en T5 |
| R-210 | R-206 | — | [F] | `OperationFormPage.tsx` | P-02/P-09 | Medio | Serial en T5 |
| R-146 (rider) | R-206/209; AOD-16 | — | [F] | `operationPayload.ts` | P-02 | Bajo-medio | Rider T5 si se aprueba |
| R-194 | R-190 (helper); familia FE cerrada | T12 (P-04) | [F][S] | `OperationFormPage.tsx` | P-04 | Alto | No (tranche propia, después de T4) |
| R-192 | R-203 (si T3 antes); OD-19 §1 | R-193, R-211, R-207 | [S][F] | `validators.py`, `lots/service.py` | P-06/P-07 | Alto (estado REVERSED) | No (primero de T7) |
| R-193 | R-192 | T12 (P-01) | [F] | `validators.py` | P-01 | Medio | Serial en T7 |
| R-211 | R-192/193 | T12 (P-02/P-03) | [F] | `validators.py` | P-02/P-03 | Medio | Serial en T7 |
| P1-12-REOPEN | T1-T7 | R-198, R-219 | [F][S] | `audit/*` | P-09 | Alto (dedup de auditoría) | No (primero de T8) |
| R-198 | P1-12 | R-219; AOD-14 | [F] | `operations` evidencias + `audit` | P-02 | Medio-alto | Serial en T8 |
| R-219 | P1-12 | — | [S] | `AuditPage.tsx` | P-09 | Bajo | Rider T8 |
| R-215 | — | R-196 | [S] | app shell (boundary) | transversal | Bajo | Sí (T9, primero) |
| R-196 | R-215 | T12 (P-12) | [F] | `MasterListPage.tsx` | P-12 | Medio | Serial en T9 |
| R-195 (+R-122) | — | T12 (P-13) | [F] | `UsersPage.tsx` | P-13 | Bajo | Sí (T9) |
| R-197 | R-208 | R-207; R-142 rider | [F][S] | `review/service.py`, `router.py` | P-07 | Medio-alto (estados) | No (primero de T10) |
| R-207 | R-192, R-197; OD-19 §18 | T12 (reverso) | [S] | FE nueva + `reversals` | P-07 | Alto (capacidad nueva) | Serial en T10 |
| R-213 | — | R-212 | [S] | `auth/schemas.py` (lectura) | P-13 | Bajo | Sí (T11, primero) |
| R-212 | R-213 | T12 | [F] | guardas FE | transversal | Bajo | Serial en T11 |
| R-218 | — | T12 (P-15) | [F] | FE reportes | P-15 | Bajo-medio | Rider T11 |
| R-220 | T11 (por lotes) | — | [F] | varios | varios | Bajo | Sí (por lotes A→D) |
| Wave C (R-131…134, R-141) | **Decisión AOD-10** | T12 (P-15) | [G] | `reports/service.py` | P-15 | Alto si se decide corregir (spec nueva) | Condicional |
| R-217 | Fase SAP | — | [S] | `SapManagerPage.tsx` | P-08 | Bajo | No pre-SAP |
| Pista OPS (R-52, AC03/AC07, P1-6) | — | T13 (gate final) | [G] | Infra | Todos | Alto (evidencias/respaldos) | Sí (en paralelo, sin tocar código) |

## 2 · DAG de tranches

```mermaid
flowchart TD
  T1[T1 · GA-GOV-03 gobernanza] --> T2[T2 · Fundación seguridad<br/>R-199 · R-200 · AC04 · R-202 · R-208]
  T1 --> T3[T3 · Alcance de datos<br/>R-201 · R-203 · R-204+216 · R-221]
  T2 --> T4[T4 · Eventos y recepción FE<br/>R-190 + R-205]
  T3 --> T4
  T4 --> T5[T5 · Contrato de captura<br/>R-191 · R-206 · R-209 · R-210<br/>(+R-146 rider)]
  T5 --> T6[T6 · Cadena de incubadora<br/>R-194]
  T6 --> T7[T7 · Cierre y reversos<br/>R-192 · R-193 · R-211]
  T7 --> T8[T8 · Auditoría/evidencias<br/>P1-12 · R-198 · R-219]
  T8 --> T9[T9 · Maestros y usuarios<br/>R-215 · R-196 · R-195 (+R-122)]
  T9 --> T10[T10 · Revisión y reverso UI<br/>R-197 · R-207 (+R-142)]
  T10 --> T11[T11 · Residuales FE<br/>R-213 · R-212 · R-218 · R-220]
  T11 --> T12[T12 · Recertificación E2E 17 procesos<br/>+ decisión Wave C AOD-10]
  T12 --> T13[T13 · UAT del propietario + gate final<br/>+ Pista OPS cerrada]
  OPS[Pista OPS<br/>R-52 · AC03 · AC07 · P1-6] --> T13
  T2 -.->|obligatorio antes de| T12
  T3 -.->|obligatorio antes de| T12
```

## 3 · Validación del grafo

- **Sin ciclos**: verificado por inspección (todas las aristas van de menor a mayor tranche salvo riders intra-tranche y [F] de orden interno).
- **Camino crítico**: T1 → T2/T3 → T4 → T5 → T6 → T7 → T8 → T9 → T10 → T11 → T12 → T13 (14 eslabones). Cualquier adelanto de T12 exige mover antes todo el camino o justificar una excepción documentada (§41).
- **Excepciones documentadas a la serialidad**: (1) R-208 en T2 toca solo permisos de un router que R-197 (T10) modificará en servicio — riesgo aceptado con orden T2→T10 ya previsto; (2) R-203 (T3) y R-192 (T7) comparten `lots/service.py` — serializado T3→T7; (3) R-221 (T3) y R-209 (T5) comparten `operations/service.py` — serializado T3→T5.
- **Paralelización permitida dentro de tranche** (§42): solo con ficheros disjuntos y un único responsable por fichero; nunca dos specs con [F] sobre el mismo fichero a la vez.
- **BU/multicompañía**: toda spec toca el mismo tenant model; los tests de tenencia (OD-14/OD-16) corren en cada tranche como suite de regresión antes del cierre.
- **Migraciones**: ninguna spec de T4-T11 requiere migración de esquema (fixes de contrato/validación/FE y auditoría); R-83 (si se decide) y R-148 (si se decide) serían migraciones menores en T8/fase SAP — sin ALTER sobre datos de producción en este programa.
