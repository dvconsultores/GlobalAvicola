# SAP-HANA-CLOUD · 03_HANA_QUERY_CATALOG

Fecha: 2026-10-06 · SPEC 005 · **Generado desde** `backend/app/integrations/sap/inbound/registry.py` (no se edita a mano)

> `LEGACY QUERY != CONTRACT` · `CURRENT HANA METADATA + APPROVED QUERY REGISTRY = CONTRACT`
>
> Ninguna definición está verificada contra el landscape real (SAP-0P = 0/12). `LEGACY_CONFIRMED` significa que sus tablas constan en el uso histórico; `CANDIDATE`, que al menos una se valida en el paso P5 del runbook. El schema aparece como `"<SCHEMA>"`: en ejecución es `SAP_HANA_SCHEMA`, validado como identificador.

---

## 1 · Resumen

| # | Objeto | `query_id` | Tablas | Fuente | Clave de origen | Estrategia | Candidato a watermark | Ámbito | Destino |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `company` | `company.v1` | T001 | `CANDIDATE` | `MANDT + BUKRS` | `SNAPSHOT` | — | company_code | staging (`STAGED_ONLY`) |
| 2 | `plant` | `plant.v1` | T001W, T001K | `CANDIDATE` | `MANDT + WERKS` | `SNAPSHOT` | — | company_code | `sap_references` · `plant` |
| 3 | `storage_location` | `storage_location.v1` | T001L, T001W, T001K | `CANDIDATE` | `MANDT + WERKS + LGORT` | `SNAPSHOT` | — | company_code | `sap_references` · `storage_location` |
| 4 | `vendor` | `vendor.v1` | LFA1, LFB1 | `CANDIDATE` | `MANDT + LIFNR` | `SNAPSHOT` | — | company_code | `sap_references` · `vendor` |
| 5 | `material` | `material.v1` | MARA, MAKT, MARC, T001K | `CANDIDATE` | `MANDT + MATNR` | `SNAPSHOT` | `LAEDA` | company_code | `sap_references` · `material` |
| 6 | `batch` | `batch.v1` | MCHA, T001K | `CANDIDATE` | `MANDT + MATNR + WERKS + CHARG` | `SNAPSHOT` | `LAEDA` | company_code | `sap_references` · `sap_batch` |
| 7 | `movement_type` | `movement_type.v1` | T156HT | `LEGACY_CONFIRMED` | `MANDT + BWART` | `SNAPSHOT` | — | client | staging (`STAGED_ONLY`) |
| 8 | `purchase_order` | `purchase_order.v1` | EKKO | `LEGACY_CONFIRMED` | `MANDT + EBELN` | `BOUNDED_RECONCILIATION_WINDOW` | `AEDAT` | company_code | `sap_references` · `purchase_order` (compuesta con posiciones e historial) |
| 9 | `purchase_order_item` | `purchase_order_item.v1` | EKPO, EKKO, EKET | `CANDIDATE` | `MANDT + EBELN + EBELP` | `BOUNDED_RECONCILIATION_WINDOW` | `AEDAT` | company_code | anidada en la referencia de su OC (`extra_data.items`) |
| 10 | `purchase_order_history` | `purchase_order_history.v1` | EKBE, EKKO | `LEGACY_CONFIRMED` | `MANDT + EBELN + EBELP + ZEKKN + VGABE + GJAHR + BELNR + BUZEI` | `BOUNDED_RECONCILIATION_WINDOW` | `BUDAT` | company_code | staging (`STAGED_ONLY`); alimenta `received_quantity` de la OC |
| 11 | `production_order` | `production_order.v1` | AUFK, AFKO, AFPO | `CANDIDATE` | `MANDT + AUFNR` | `BOUNDED_RECONCILIATION_WINDOW` | `AEDAT` | company_code | staging (`STAGED_ONLY`) |
| 12 | `transfer_order` | `transfer_order.v1` | EKPO, EKKO | `CANDIDATE` | `MANDT + EBELN + EBELP` | `BOUNDED_RECONCILIATION_WINDOW` | `AEDAT` | company_code | `sap_references` · `transfer_order` (agrupada por documento) |
| 13 | `outbound_order` | `outbound_order.v1` | LIKP, LIPS, T001K | `CANDIDATE` | `MANDT + VBELN + POSNR` | `BOUNDED_RECONCILIATION_WINDOW` | `ERDAT` | company_code | staging (`STAGED_ONLY`) |
| 14 | `material_movement` | `material_movement.v1` | MATDOC | `LEGACY_CONFIRMED` | `MANDT + MBLNR + MJAHR + ZEILE` | `BOUNDED_RECONCILIATION_WINDOW` | `BUDAT` | company_code | staging (`STAGED_ONLY`) |

Orden de sincronización: `company` → `plant` → `storage_location` → `vendor` → `material` → `batch` → `movement_type` → `purchase_order` → `purchase_order_item` → `purchase_order_history` → `production_order` → `transfer_order` → `outbound_order` → `material_movement`.

Grupos indivisibles (pedir uno sincroniza el grupo): `purchase_order` + `purchase_order_item` + `purchase_order_history`.

Diferidos (`DEFERRED_PHASE_1`): `SAP_COST_CENTER` (sin consumidor) · `SAP_INVENTORY_SNAPSHOT` (requiere aprobar MARD).

## 2 · Reglas comunes

- SQL estático: lo único interpolado es el schema. Todo valor es un parámetro bind (`:mandt`, `:bukrs`, `:langu`, `:date_from`, `:date_to`, `:page_limit`, `:page_offset`).
- Una consulta por sociedad mapeada: no hay listas `IN` construidas con datos.
- Paginación `LIMIT :page_limit OFFSET :page_offset` con `ORDER BY` estable; `page_limit ≤ max_page_size` y ≤ `SAP_HANA_PAGE_SIZE`; tope global `SAP_HANA_MAX_ROWS_PER_SYNC`.
- Objetos documentales: ventana obligatoria `:date_from … :date_to` (máx. 366 días por petición).
- Los parámetros fijos son valores de dominio estándar de SAP y también viajan como bind.
- Consulta de humo (única sin paginar): `SELECT 1 AS "ok" FROM DUMMY`.

## 3 · Definiciones

### `company.v1` — `company`

- Tablas: `T001` · fuente `CANDIDATE`
- Clave de origen: `MANDT + BUKRS` · orden: `MANDT, BUKRS` · página máx.: 1000
- Parámetros: `mandt`, `bukrs`
- Columnas obligatorias: `MANDT`, `BUKRS`, `BUTXT`
- Columnas opcionales (pueden venir nulas): `ORT01`, `LAND1`, `WAERS`
- Estrategia: `SNAPSHOT`
- Nota: Sociedad. Sin tipo de referencia: permanece en staging (OD-24, sin convergencia).

```sql
SELECT T.MANDT, T.BUKRS, T.BUTXT, T.ORT01, T.LAND1, T.WAERS
FROM "<SCHEMA>".T001 T
WHERE T.MANDT = :mandt AND T.BUKRS = :bukrs
ORDER BY T.MANDT, T.BUKRS
LIMIT :page_limit OFFSET :page_offset
```

### `plant.v1` — `plant`

- Tablas: `T001W`, `T001K` · fuente `CANDIDATE`
- Clave de origen: `MANDT + WERKS` · orden: `MANDT, WERKS` · página máx.: 1000
- Parámetros: `mandt`, `bukrs`
- Columnas obligatorias: `MANDT`, `WERKS`, `NAME1`, `BUKRS`
- Columnas opcionales (pueden venir nulas): `NAME2`, `ORT01`, `LAND1`
- Estrategia: `SNAPSHOT`
- Nota: T001W consta en el legacy; la relación centro→sociedad (T001K) es candidata.

```sql
SELECT W.MANDT, W.WERKS, W.NAME1, W.NAME2, W.ORT01, W.LAND1, K.BUKRS
FROM "<SCHEMA>".T001W W
JOIN "<SCHEMA>".T001K K ON K.MANDT = W.MANDT AND K.BWKEY = W.BWKEY
WHERE W.MANDT = :mandt AND K.BUKRS = :bukrs
ORDER BY W.MANDT, W.WERKS
LIMIT :page_limit OFFSET :page_offset
```

### `storage_location.v1` — `storage_location`

- Tablas: `T001L`, `T001W`, `T001K` · fuente `CANDIDATE`
- Clave de origen: `MANDT + WERKS + LGORT` · orden: `MANDT, WERKS, LGORT` · página máx.: 1000
- Parámetros: `mandt`, `bukrs`
- Columnas obligatorias: `MANDT`, `WERKS`, `LGORT`, `BUKRS`
- Columnas opcionales (pueden venir nulas): `LGOBE`
- Estrategia: `SNAPSHOT`
- Nota: LGORT es almacén, no galpón: la relación con house exige mapping explícito.

```sql
SELECT L.MANDT, L.WERKS, L.LGORT, L.LGOBE, K.BUKRS
FROM "<SCHEMA>".T001L L
JOIN "<SCHEMA>".T001W W ON W.MANDT = L.MANDT AND W.WERKS = L.WERKS
JOIN "<SCHEMA>".T001K K ON K.MANDT = W.MANDT AND K.BWKEY = W.BWKEY
WHERE L.MANDT = :mandt AND K.BUKRS = :bukrs
ORDER BY L.MANDT, L.WERKS, L.LGORT
LIMIT :page_limit OFFSET :page_offset
```

### `vendor.v1` — `vendor`

- Tablas: `LFA1`, `LFB1` · fuente `CANDIDATE`
- Clave de origen: `MANDT + LIFNR` · orden: `MANDT, LIFNR` · página máx.: 1000
- Parámetros: `mandt`, `bukrs`
- Columnas obligatorias: `MANDT`, `LIFNR`, `NAME1`, `BUKRS`
- Columnas opcionales (pueden venir nulas): `STCD1`, `LAND1`, `SPERR`, `LOEVM`
- Estrategia: `SNAPSHOT`
- Nota: LFA1 consta en el legacy; se acota por sociedad (LFB1). BP/CVI se valida en el probe.

```sql
SELECT A.MANDT, A.LIFNR, A.NAME1, A.STCD1, A.LAND1, A.SPERR, A.LOEVM, B.BUKRS
FROM "<SCHEMA>".LFA1 A
JOIN "<SCHEMA>".LFB1 B ON B.MANDT = A.MANDT AND B.LIFNR = A.LIFNR
WHERE A.MANDT = :mandt AND B.BUKRS = :bukrs
ORDER BY A.MANDT, A.LIFNR
LIMIT :page_limit OFFSET :page_offset
```

### `material.v1` — `material`

- Tablas: `MARA`, `MAKT`, `MARC`, `T001K` · fuente `CANDIDATE`
- Clave de origen: `MANDT + MATNR` · orden: `MANDT, MATNR` · página máx.: 1000
- Parámetros: `mandt`, `bukrs`, `langu`
- Columnas obligatorias: `MANDT`, `MATNR`, `MTART`, `MEINS`
- Columnas opcionales (pueden venir nulas): `MAKTX`, `MATKL`, `LVORM`, `LAEDA`
- Estrategia: `SNAPSHOT`
- Nota: Material de los centros de la sociedad. La categoría avícola se resuelve en GA.

```sql
SELECT M.MANDT, M.MATNR, T.MAKTX, M.MTART, M.MATKL, M.MEINS, M.LVORM, M.LAEDA
FROM "<SCHEMA>".MARA M LEFT
JOIN "<SCHEMA>".MAKT T ON T.MANDT = M.MANDT AND T.MATNR = M.MATNR AND T.SPRAS = :langu
WHERE M.MANDT = :mandt AND EXISTS ( SELECT C.MATNR
FROM "<SCHEMA>".MARC C
JOIN "<SCHEMA>".T001K K ON K.MANDT = C.MANDT AND K.BWKEY = C.WERKS
WHERE C.MANDT = M.MANDT AND C.MATNR = M.MATNR AND K.BUKRS = :bukrs)
ORDER BY M.MANDT, M.MATNR
LIMIT :page_limit OFFSET :page_offset
```

### `batch.v1` — `batch`

- Tablas: `MCHA`, `T001K` · fuente `CANDIDATE`
- Clave de origen: `MANDT + MATNR + WERKS + CHARG` · orden: `MANDT, MATNR, WERKS, CHARG` · página máx.: 1000
- Parámetros: `mandt`, `bukrs`
- Columnas obligatorias: `MANDT`, `MATNR`, `WERKS`, `CHARG`, `BUKRS`
- Columnas opcionales (pueden venir nulas): `HSDAT`, `VFDAT`, `ERSDA`, `LAEDA`, `LVORM`
- Estrategia: `SNAPSHOT`
- Nota: —

```sql
SELECT B.MANDT, B.MATNR, B.WERKS, B.CHARG, B.HSDAT, B.VFDAT, B.ERSDA, B.LAEDA, B.LVORM, K.BUKRS
FROM "<SCHEMA>".MCHA B
JOIN "<SCHEMA>".T001K K ON K.MANDT = B.MANDT AND K.BWKEY = B.WERKS
WHERE B.MANDT = :mandt AND K.BUKRS = :bukrs
ORDER BY B.MANDT, B.MATNR, B.WERKS, B.CHARG
LIMIT :page_limit OFFSET :page_offset
```

### `movement_type.v1` — `movement_type`

- Tablas: `T156HT` · fuente `LEGACY_CONFIRMED`
- Clave de origen: `MANDT + BWART` · orden: `MANDT, BWART` · página máx.: 1000
- Parámetros: `mandt`, `langu`
- Columnas obligatorias: `MANDT`, `BWART`
- Columnas opcionales (pueden venir nulas): `BTEXT`
- Estrategia: `SNAPSHOT`
- Nota: Catálogo informativo. Ningún tipo de movimiento es una regla de negocio en GA.

```sql
SELECT H.MANDT, H.BWART, MIN(H.BTEXT) AS BTEXT
FROM "<SCHEMA>".T156HT H
WHERE H.MANDT = :mandt AND H.SPRAS = :langu
GROUP BY H.MANDT, H.BWART
ORDER BY H.MANDT, H.BWART
LIMIT :page_limit OFFSET :page_offset
```

### `purchase_order.v1` — `purchase_order`

- Tablas: `EKKO` · fuente `LEGACY_CONFIRMED`
- Clave de origen: `MANDT + EBELN` · orden: `MANDT, EBELN` · página máx.: 1000
- Parámetros: `mandt`, `bukrs`, `doc_category`, `date_from`, `date_to` · fijos: `doc_category=F`
- Columnas obligatorias: `MANDT`, `EBELN`, `BUKRS`, `LIFNR`, `BEDAT`
- Columnas opcionales (pueden venir nulas): `BSTYP`, `BSART`, `EKORG`, `AEDAT`, `WAERS`, `LOEKZ`
- Estrategia: `BOUNDED_RECONCILIATION_WINDOW` sobre `AEDAT`
- Nota: Cabecera de OC. Los traslados (RESWK informado) van en transfer_order.

```sql
SELECT E.MANDT, E.EBELN, E.BUKRS, E.BSTYP, E.BSART, E.LIFNR, E.EKORG, E.BEDAT, E.AEDAT, E.WAERS, E.LOEKZ
FROM "<SCHEMA>".EKKO E
WHERE E.MANDT = :mandt AND E.BUKRS = :bukrs AND E.BSTYP = :doc_category AND (E.RESWK = '' OR E.RESWK IS NULL) AND E.AEDAT BETWEEN :date_from AND :date_to
ORDER BY E.MANDT, E.EBELN
LIMIT :page_limit OFFSET :page_offset
```

### `purchase_order_item.v1` — `purchase_order_item`

- Tablas: `EKPO`, `EKKO`, `EKET` · fuente `CANDIDATE`
- Clave de origen: `MANDT + EBELN + EBELP` · orden: `MANDT, EBELN, EBELP` · página máx.: 1000
- Parámetros: `mandt`, `bukrs`, `doc_category`, `date_from`, `date_to` · fijos: `doc_category=F`
- Columnas obligatorias: `MANDT`, `EBELN`, `EBELP`, `MATNR`, `WERKS`, `MENGE`, `MEINS`, `BUKRS`
- Columnas opcionales (pueden venir nulas): `TXZ01`, `LGORT`, `EINDT`, `LOEKZ`, `ELIKZ`, `AEDAT`
- Estrategia: `BOUNDED_RECONCILIATION_WINDOW` sobre `AEDAT`
- Nota: Posiciones con su material real. Se elimina el patrón legacy macho/hembra por MATNR.

```sql
SELECT P.MANDT, P.EBELN, P.EBELP, P.MATNR, P.TXZ01, P.WERKS, P.LGORT, P.MENGE, P.MEINS, (SELECT MIN(S.EINDT)
FROM "<SCHEMA>".EKET S
WHERE S.MANDT = P.MANDT AND S.EBELN = P.EBELN AND S.EBELP = P.EBELP) AS EINDT, P.LOEKZ, P.ELIKZ, E.BUKRS, E.AEDAT
FROM "<SCHEMA>".EKPO P
JOIN "<SCHEMA>".EKKO E ON E.MANDT = P.MANDT AND E.EBELN = P.EBELN
WHERE P.MANDT = :mandt AND E.BUKRS = :bukrs AND E.BSTYP = :doc_category AND (E.RESWK = '' OR E.RESWK IS NULL) AND E.AEDAT BETWEEN :date_from AND :date_to
ORDER BY P.MANDT, P.EBELN, P.EBELP
LIMIT :page_limit OFFSET :page_offset
```

### `purchase_order_history.v1` — `purchase_order_history`

- Tablas: `EKBE`, `EKKO` · fuente `LEGACY_CONFIRMED`
- Clave de origen: `MANDT + EBELN + EBELP + ZEKKN + VGABE + GJAHR + BELNR + BUZEI` · orden: `MANDT, EBELN, EBELP, ZEKKN, VGABE, GJAHR, BELNR, BUZEI` · página máx.: 1000
- Parámetros: `mandt`, `bukrs`, `doc_category`, `date_from`, `date_to` · fijos: `doc_category=F`
- Columnas obligatorias: `MANDT`, `EBELN`, `EBELP`, `ZEKKN`, `VGABE`, `GJAHR`, `BELNR`, `BUZEI`, `BUDAT`, `MENGE`, `SHKZG`, `BUKRS`
- Columnas opcionales (pueden venir nulas): `BEWTP`, `BWART`, `MATNR`, `WERKS`, `LFBNR`
- Estrategia: `BOUNDED_RECONCILIATION_WINDOW` sobre `BUDAT`
- Nota: Historial de la OC: entradas (S) y reversos (H). Alimenta received_quantity.

```sql
SELECT B.MANDT, B.EBELN, B.EBELP, B.ZEKKN, B.VGABE, B.GJAHR, B.BELNR, B.BUZEI, B.BEWTP, B.BWART, B.BUDAT, B.MENGE, B.SHKZG, B.MATNR, B.WERKS, B.LFBNR, E.BUKRS
FROM "<SCHEMA>".EKBE B
JOIN "<SCHEMA>".EKKO E ON E.MANDT = B.MANDT AND E.EBELN = B.EBELN
WHERE B.MANDT = :mandt AND E.BUKRS = :bukrs AND E.BSTYP = :doc_category AND (E.RESWK = '' OR E.RESWK IS NULL) AND B.BUDAT BETWEEN :date_from AND :date_to
ORDER BY B.MANDT, B.EBELN, B.EBELP, B.ZEKKN, B.VGABE, B.GJAHR, B.BELNR, B.BUZEI
LIMIT :page_limit OFFSET :page_offset
```

### `production_order.v1` — `production_order`

- Tablas: `AUFK`, `AFKO`, `AFPO` · fuente `CANDIDATE`
- Clave de origen: `MANDT + AUFNR` · orden: `MANDT, AUFNR` · página máx.: 1000
- Parámetros: `mandt`, `bukrs`, `date_from`, `date_to`
- Columnas obligatorias: `MANDT`, `AUFNR`, `BUKRS`, `WERKS`, `MATNR`, `GAMNG`, `GMEIN`, `ERDAT`
- Columnas opcionales (pueden venir nulas): `AUART`, `CHARG`, `LGORT`, `GSTRP`, `GLTRP`, `LOEKZ`, `PHAS1`, `PHAS2`, `PHAS3`, `AEDAT`
- Estrategia: `BOUNDED_RECONCILIATION_WINDOW` sobre `ERDAT`
- Nota: Órdenes de producción (AUFK con AFKO/AFPO). Fuente a validar por metadata en P5.

```sql
SELECT A.MANDT, A.AUFNR, A.AUART, A.BUKRS, A.WERKS, P.MATNR, P.CHARG, P.LGORT, K.GSTRP, K.GLTRP, K.GAMNG, K.GMEIN, A.LOEKZ, A.PHAS1, A.PHAS2, A.PHAS3, A.ERDAT, A.AEDAT
FROM "<SCHEMA>".AUFK A
JOIN "<SCHEMA>".AFKO K ON K.MANDT = A.MANDT AND K.AUFNR = A.AUFNR
JOIN "<SCHEMA>".AFPO P ON P.MANDT = A.MANDT AND P.AUFNR = A.AUFNR
WHERE A.MANDT = :mandt AND A.BUKRS = :bukrs AND P.POSNR = (SELECT MIN(X.POSNR)
FROM "<SCHEMA>".AFPO X
WHERE X.MANDT = P.MANDT AND X.AUFNR = P.AUFNR) AND (A.ERDAT BETWEEN :date_from AND :date_to OR A.AEDAT BETWEEN :date_from AND :date_to)
ORDER BY A.MANDT, A.AUFNR
LIMIT :page_limit OFFSET :page_offset
```

### `transfer_order.v1` — `transfer_order`

- Tablas: `EKPO`, `EKKO` · fuente `CANDIDATE`
- Clave de origen: `MANDT + EBELN + EBELP` · orden: `MANDT, EBELN, EBELP` · página máx.: 1000
- Parámetros: `mandt`, `bukrs`, `doc_category`, `date_from`, `date_to` · fijos: `doc_category=F`
- Columnas obligatorias: `MANDT`, `EBELN`, `EBELP`, `BUKRS`, `RESWK`, `WERKS`, `MATNR`, `MENGE`, `MEINS`
- Columnas opcionales (pueden venir nulas): `BSART`, `RESLO`, `LGORT`, `TXZ01`, `BEDAT`, `AEDAT`, `LOEKZ`, `ELIKZ`
- Estrategia: `BOUNDED_RECONCILIATION_WINDOW` sobre `AEDAT`
- Nota: Traslado = documento de compras con centro suministrador (RESWK). Sin listas de BSART ni de BWART.

```sql
SELECT P.MANDT, P.EBELN, P.EBELP, E.BUKRS, E.BSART, E.RESWK, P.RESLO, P.WERKS, P.LGORT, P.MATNR, P.TXZ01, P.MENGE, P.MEINS, E.BEDAT, E.AEDAT, P.LOEKZ, P.ELIKZ
FROM "<SCHEMA>".EKPO P
JOIN "<SCHEMA>".EKKO E ON E.MANDT = P.MANDT AND E.EBELN = P.EBELN
WHERE P.MANDT = :mandt AND E.BUKRS = :bukrs AND E.BSTYP = :doc_category AND E.RESWK <> '' AND E.AEDAT BETWEEN :date_from AND :date_to
ORDER BY P.MANDT, P.EBELN, P.EBELP
LIMIT :page_limit OFFSET :page_offset
```

### `outbound_order.v1` — `outbound_order`

- Tablas: `LIKP`, `LIPS`, `T001K` · fuente `CANDIDATE`
- Clave de origen: `MANDT + VBELN + POSNR` · orden: `MANDT, VBELN, POSNR` · página máx.: 1000
- Parámetros: `mandt`, `bukrs`, `delivery_category`, `date_from`, `date_to` · fijos: `delivery_category=J`
- Columnas obligatorias: `MANDT`, `VBELN`, `POSNR`, `MATNR`, `WERKS`, `LFIMG`, `VRKME`, `ERDAT`, `BUKRS`
- Columnas opcionales (pueden venir nulas): `LFART`, `VSTEL`, `KUNNR`, `WADAT`, `WADAT_IST`, `ARKTX`, `LGORT`, `CHARG`, `VGBEL`, `VGPOS`
- Estrategia: `BOUNDED_RECONCILIATION_WINDOW` sobre `ERDAT`
- Nota: Orden de salida = documento de entrega (candidata, Q8). No es un documento de material: MATDOC es evidencia de movimiento y va aparte.

```sql
SELECT P.MANDT, P.VBELN, P.POSNR, H.LFART, H.VSTEL, H.KUNNR, H.WADAT, H.WADAT_IST, H.ERDAT, P.MATNR, P.ARKTX, P.WERKS, P.LGORT, P.CHARG, P.LFIMG, P.VRKME, P.VGBEL, P.VGPOS, K.BUKRS
FROM "<SCHEMA>".LIPS P
JOIN "<SCHEMA>".LIKP H ON H.MANDT = P.MANDT AND H.VBELN = P.VBELN
JOIN "<SCHEMA>".T001K K ON K.MANDT = P.MANDT AND K.BWKEY = P.WERKS
WHERE P.MANDT = :mandt AND K.BUKRS = :bukrs AND H.VBTYP = :delivery_category AND H.ERDAT BETWEEN :date_from AND :date_to
ORDER BY P.MANDT, P.VBELN, P.POSNR
LIMIT :page_limit OFFSET :page_offset
```

### `material_movement.v1` — `material_movement`

- Tablas: `MATDOC` · fuente `LEGACY_CONFIRMED`
- Clave de origen: `MANDT + MBLNR + MJAHR + ZEILE` · orden: `MANDT, MBLNR, MJAHR, ZEILE` · página máx.: 1000
- Parámetros: `mandt`, `bukrs`, `date_from`, `date_to`
- Columnas obligatorias: `MANDT`, `MBLNR`, `MJAHR`, `ZEILE`, `BWART`, `MATNR`, `WERKS`, `ERFMG`, `ERFME`, `SHKZG`, `BUDAT`, `BUKRS`
- Columnas opcionales (pueden venir nulas): `LGORT`, `UMWRK`, `UMLGO`, `CHARG`, `MENGE`, `MEINS`, `BLDAT`, `CPUDT`, `EBELN`, `EBELP`, `AUFNR`, `SMBLN`, `SJAHR`, `SMBLP`
- Estrategia: `BOUNDED_RECONCILIATION_WINDOW` sobre `BUDAT`
- Nota: Documentos de material. Ventana temporal obligatoria; prohibido el scan abierto.

```sql
SELECT M.MANDT, M.MBLNR, M.MJAHR, M.ZEILE, M.BWART, M.MATNR, M.WERKS, M.LGORT, M.UMWRK, M.UMLGO, M.CHARG, M.ERFMG, M.ERFME, M.MENGE, M.MEINS, M.SHKZG, M.BUDAT, M.BLDAT, M.CPUDT, M.EBELN, M.EBELP, M.AUFNR, M.BUKRS, M.SMBLN, M.SJAHR, M.SMBLP
FROM "<SCHEMA>".MATDOC M
WHERE M.MANDT = :mandt AND M.BUKRS = :bukrs AND M.BUDAT BETWEEN :date_from AND :date_to
ORDER BY M.MANDT, M.MBLNR, M.MJAHR, M.ZEILE
LIMIT :page_limit OFFSET :page_offset
```
