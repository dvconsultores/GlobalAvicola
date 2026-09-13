# R-201 · CLARIFICACIONES

Fecha: 2026-09-13 · HEAD `c0b4afc` · Resolver antes de C2 (implementación). Ninguna decisión del propietario requerida; supuestos verificados en código.

| # | Pregunta | Supuesto por defecto | Fuente | Decisión |
|---|---|---|---|---|
| C-01 | ¿Qué debe ver la autoridad global **sin** contexto en `/sap/*`? | Nada (`false()`): fail-closed, mismo patrón que `_acotar_a_empresa`. | `OD-14.d`; `operations/service.py:93-102` | técnica |
| C-02 | ¿Y la autoridad global **situada**? | Opera normalmente sobre su empresa efectiva (sin cambio). | `tenancy.py:294-307` | técnica |
| C-03 | ¿El 4xx de «sin contexto» en consolidate/export/retry debe ocurrir antes de leer? | Sí: mover/reutilizar `_require_company_id` al inicio de cada camino (elimina la lectura previa de filas ajenas). | `sap/service.py:208,258` (guardas tardías) | técnica |
| C-04 | ¿Se cambia el mensaje/estatus de `_require_company_id`? | No: se reutiliza tal cual (contrato actual del servicio). | código | técnica |
| C-05 | ¿Se retira `get_company_filter` (`security.py:170-178`)? | Se marca obsoleto/retira en la misma tranche (código muerto sin consumidores) con nota en el commit; si el equipo prefiere, se difiere como limpieza P3 independiente. | `D_security_tx.md A.24 #3` | técnica |
| C-06 | ¿Toca la máquina de estados SAP (retry → SAP_CONFIRMED, auditoría)? | No: E-25/R-157 quedan en `GA-REM-017` (fase SAP). | `E_domain_ledger.md T18, E-25` | técnica |
| C-07 | ¿Los tests usan fixtures de dos empresas reales o mocks? | Dos empresas reales en PG de pruebas (patrón `test_sap_transversal.py`), sin mocks para la frontera. | tests existentes | técnica |
| C-08 | ¿El panel SAP (`SapManagerPage`) requiere cambio por este fix? | No: mostrará ∅ sin contexto (correcto). Su alineación de estados es R-217. | registro G-29 | técnica |

Sin decisiones abiertas que bloqueen. C-05 es opcional (limpieza) y puede diferirse sin afectar los AC.
