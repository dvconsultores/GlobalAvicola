# SAP-SOAP · 06_SAP_SOAP_REQUEST_RESPONSE_EXAMPLES

Fecha: 2026-09-22 · Ejemplos completos (§34) para 6 operaciones: Request Envelope + Response Envelope + Fault. **Sin credenciales reales** (placeholder `X-AUTH-PLACEHOLDER`). Namespace ilustrativo: `urn:globalavicola:sap:inbound:v1`.

---

## 1 · `GetCompanies`

**Request**
```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ga="urn:globalavicola:sap:inbound:v1">
  <soapenv:Header/>
  <soapenv:Body>
    <ga:GetCompaniesRequest>
      <ga:Header>
        <ga:RequestId>REQ-20260922-0001</ga:RequestId>
        <ga:SchemaVersion>1.0</ga:SchemaVersion>
        <ga:ClientSystem>GLOBAL_AVICOLA</ga:ClientSystem>
        <ga:Language>ES</ga:Language>
        <ga:ChangedSince>2026-09-01T00:00:00Z</ga:ChangedSince>
        <ga:PageNumber>1</ga:PageNumber>
        <ga:PageSize>100</ga:PageSize>
      </ga:Header>
    </ga:GetCompaniesRequest>
  </soapenv:Body>
</soapenv:Envelope>
```

**Response**
```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ga="urn:globalavicola:sap:inbound:v1">
  <soapenv:Body>
    <ga:GetCompaniesResponse>
      <ga:Header>
        <ga:RequestId>REQ-20260922-0001</ga:RequestId>
        <ga:ResponseTimestamp>2026-09-22T10:15:03Z</ga:ResponseTimestamp>
        <ga:Success>true</ga:Success>
        <ga:ErrorCode/>
        <ga:ErrorMessage/>
        <ga:SchemaVersion>1.0</ga:SchemaVersion>
        <ga:RecordCount>2</ga:RecordCount>
        <ga:HasMore>false</ga:HasMore>
        <ga:ContinuationToken/>
      </ga:Header>
      <ga:Records>
        <ga:Company>
          <ga:MANDT>120</ga:MANDT>
          <ga:COMPANY_CODE>1000</ga:COMPANY_CODE>
          <ga:NAME>LIDER POLLO C.A.</ga:NAME>
          <ga:COUNTRY>VE</ga:COUNTRY>
          <ga:CURRENCY>VES</ga:CURRENCY>
          <ga:ACTIVE_STATUS>ACTIVE</ga:ACTIVE_STATUS>
        </ga:Company>
        <ga:Company>
          <ga:MANDT>120</ga:MANDT>
          <ga:COMPANY_CODE>2000</ga:COMPANY_CODE>
          <ga:NAME>AVICOLA EJEMPLO C.A.</ga:NAME>
          <ga:COUNTRY>VE</ga:COUNTRY>
          <ga:CURRENCY>VES</ga:CURRENCY>
          <ga:ACTIVE_STATUS>ACTIVE</ga:ACTIVE_STATUS>
        </ga:Company>
      </ga:Records>
      <ga:ContinuationToken/>
    </ga:GetCompaniesResponse>
  </soapenv:Body>
</soapenv:Envelope>
```

## 2 · `GetStorageLocations`

**Request**
```xml
<ga:GetStorageLocationsRequest xmlns:ga="urn:globalavicola:sap:inbound:v1">
  <ga:Header>
    <ga:RequestId>REQ-20260922-0002</ga:RequestId>
    <ga:SchemaVersion>1.0</ga:SchemaVersion>
    <ga:ClientSystem>GLOBAL_AVICOLA</ga:ClientSystem>
    <ga:Plant>3000</ga:Plant>
    <ga:PageSize>100</ga:PageSize>
    <ga:PageNumber>1</ga:PageNumber>
  </ga:Header>
</ga:GetStorageLocationsRequest>
```

**Response**
```xml
<ga:GetStorageLocationsResponse xmlns:ga="urn:globalavicola:sap:inbound:v1">
  <ga:Header>
    <ga:RequestId>REQ-20260922-0002</ga:RequestId>
    <ga:ResponseTimestamp>2026-09-22T10:16:40Z</ga:ResponseTimestamp>
    <ga:Success>true</ga:Success>
    <ga:SchemaVersion>1.0</ga:SchemaVersion>
    <ga:RecordCount>1</ga:RecordCount>
    <ga:HasMore>false</ga:HasMore>
  </ga:Header>
  <ga:Records>
    <ga:StorageLocation>
      <ga:MANDT>120</ga:MANDT>
      <ga:PLANT>3000</ga:PLANT>
      <ga:STORAGE_LOCATION>1006</ga:STORAGE_LOCATION>
      <ga:NAME>INCUBADORA 1</ga:NAME>
      <ga:ACTIVE_STATUS>ACTIVE</ga:ACTIVE_STATUS>
    </ga:StorageLocation>
  </ga:Records>
</ga:GetStorageLocationsResponse>
```

## 3 · `GetPurchaseOrders`

**Request**
```xml
<ga:GetPurchaseOrdersRequest xmlns:ga="urn:globalavicola:sap:inbound:v1">
  <ga:Header>
    <ga:RequestId>REQ-20260922-0003</ga:RequestId>
    <ga:SchemaVersion>1.0</ga:SchemaVersion>
    <ga:ClientSystem>GLOBAL_AVICOLA</ga:ClientSystem>
    <ga:CompanyCode>1000</ga:CompanyCode>
    <ga:FromDate>2026-09-01</ga:FromDate>
    <ga:ToDate>2026-09-22</ga:ToDate>
    <ga:PageSize>50</ga:PageSize>
    <ga:PageNumber>1</ga:PageNumber>
  </ga:Header>
</ga:GetPurchaseOrdersRequest>
```

**Response**
```xml
<ga:GetPurchaseOrdersResponse xmlns:ga="urn:globalavicola:sap:inbound:v1">
  <ga:Header>
    <ga:RequestId>REQ-20260922-0003</ga:RequestId>
    <ga:ResponseTimestamp>2026-09-22T10:18:11Z</ga:ResponseTimestamp>
    <ga:Success>true</ga:Success>
    <ga:SchemaVersion>1.0</ga:SchemaVersion>
    <ga:RecordCount>1</ga:RecordCount>
    <ga:HasMore>true</ga:HasMore>
    <ga:ContinuationToken>CT-OPAQUE-9f3c...ab12</ga:ContinuationToken>
  </ga:Header>
  <ga:Records>
    <ga:PurchaseOrder>
      <ga:MANDT>120</ga:MANDT>
      <ga:PO_NUMBER>4500015040</ga:PO_NUMBER>
      <ga:COMPANY_CODE>1000</ga:COMPANY_CODE>
      <ga:VENDOR>100123</ga:VENDOR>
      <ga:DOCUMENT_TYPE>NB</ga:DOCUMENT_TYPE>
      <ga:DOCUMENT_DATE>2026-09-05</ga:DOCUMENT_DATE>
      <ga:CURRENCY>USD</ga:CURRENCY>
      <ga:STATUS>OPEN</ga:STATUS>
      <ga:Items>
        <ga:Item>
          <ga:PO_ITEM>00010</ga:PO_ITEM>
          <ga:MATERIAL>000000000000110001</ga:MATERIAL>
          <ga:PLANT>4100</ga:PLANT>
          <ga:QUANTITY>15000.000</ga:QUANTITY>
          <ga:UNIT>ST</ga:UNIT>
          <ga:DELIVERY_DATE>2026-09-30</ga:DELIVERY_DATE>
        </ga:Item>
        <ga:Item>
          <ga:PO_ITEM>00020</ga:PO_ITEM>
          <ga:MATERIAL>000000000000110000</ga:MATERIAL>
          <ga:PLANT>4100</ga:PLANT>
          <ga:QUANTITY>5000.000</ga:QUANTITY>
          <ga:UNIT>ST</ga:UNIT>
          <ga:DELIVERY_DATE>2026-09-30</ga:DELIVERY_DATE>
        </ga:Item>
      </ga:Items>
    </ga:PurchaseOrder>
  </ga:Records>
</ga:GetPurchaseOrdersResponse>
```

## 4 · `GetProductionOrders`

**Request**
```xml
<ga:GetProductionOrdersRequest xmlns:ga="urn:globalavicola:sap:inbound:v1">
  <ga:Header>
    <ga:RequestId>REQ-20260922-0004</ga:RequestId>
    <ga:SchemaVersion>1.0</ga:SchemaVersion>
    <ga:ClientSystem>GLOBAL_AVICOLA</ga:ClientSystem>
    <ga:Plant>3000</ga:Plant>
    <ga:FromDate>2026-09-15</ga:FromDate>
    <ga:ToDate>2026-09-22</ga:ToDate>
    <ga:PageSize>50</ga:PageSize>
  </ga:Header>
</ga:GetProductionOrdersRequest>
```

**Response**
```xml
<ga:GetProductionOrdersResponse xmlns:ga="urn:globalavicola:sap:inbound:v1">
  <ga:Header>
    <ga:RequestId>REQ-20260922-0004</ga:RequestId>
    <ga:ResponseTimestamp>2026-09-22T10:20:31Z</ga:ResponseTimestamp>
    <ga:Success>true</ga:Success>
    <ga:SchemaVersion>1.0</ga:SchemaVersion>
    <ga:RecordCount>1</ga:RecordCount>
    <ga:HasMore>false</ga:HasMore>
  </ga:Header>
  <ga:Records>
    <ga:ProductionOrder>
      <ga:ORDER_NUMBER>700300000256</ga:ORDER_NUMBER>
      <ga:PLANT>3000</ga:PLANT>
      <ga:MATERIAL>000000000000120000</ga:MATERIAL>
      <ga:BATCH>P260922A</ga:BATCH>
      <ga:START_DATE>2026-09-20</ga:START_DATE>
      <ga:END_DATE>2026-09-27</ga:END_DATE>
      <ga:PLANNED_QUANTITY>18000.000</ga:PLANNED_QUANTITY>
      <ga:UNIT>ST</ga:UNIT>
      <ga:STATUS>RELEASED</ga:STATUS>
      <ga:DESTINATION_STORAGE>1006</ga:DESTINATION_STORAGE>
    </ga:ProductionOrder>
  </ga:Records>
</ga:GetProductionOrdersResponse>
```

## 5 · `GetOutboundOrders`

**Request**
```xml
<ga:GetOutboundOrdersRequest xmlns:ga="urn:globalavicola:sap:inbound:v1">
  <ga:Header>
    <ga:RequestId>REQ-20260922-0005</ga:RequestId>
    <ga:SchemaVersion>1.0</ga:SchemaVersion>
    <ga:ClientSystem>GLOBAL_AVICOLA</ga:ClientSystem>
    <ga:Plant>3000</ga:Plant>
    <ga:FromDate>2026-09-20</ga:FromDate>
    <ga:ToDate>2026-09-22</ga:ToDate>
    <ga:PageSize>50</ga:PageSize>
  </ga:Header>
</ga:GetOutboundOrdersRequest>
```

**Response**
```xml
<ga:GetOutboundOrdersResponse xmlns:ga="urn:globalavicola:sap:inbound:v1">
  <ga:Header>
    <ga:RequestId>REQ-20260922-0005</ga:RequestId>
    <ga:ResponseTimestamp>2026-09-22T10:22:05Z</ga:ResponseTimestamp>
    <ga:Success>true</ga:Success>
    <ga:SchemaVersion>1.0</ga:SchemaVersion>
    <ga:RecordCount>1</ga:RecordCount>
    <ga:HasMore>false</ga:HasMore>
  </ga:Header>
  <ga:Records>
    <ga:OutboundOrder>
      <ga:ORDER_NUMBER>700300000301</ga:ORDER_NUMBER>
      <ga:DOCUMENT_TYPE>OUT_CHICKS</ga:DOCUMENT_TYPE>
      <ga:SOURCE_PLANT>3000</ga:SOURCE_PLANT>
      <ga:DESTINATION_PLANT>4100</ga:DESTINATION_PLANT>
      <ga:MATERIAL>000000000000120005</ga:MATERIAL>
      <ga:BATCH>P260922A</ga:BATCH>
      <ga:QUANTITY>17500.000</ga:QUANTITY>
      <ga:UNIT>ST</ga:UNIT>
      <ga:DOCUMENT_DATE>2026-09-22</ga:DOCUMENT_DATE>
      <ga:STATUS>POSTED</ga:STATUS>
      <ga:PRODUCTION_ORDER>700300000256</ga:PRODUCTION_ORDER>
    </ga:OutboundOrder>
  </ga:Records>
</ga:GetOutboundOrdersResponse>
```

## 6 · `GetTransferOrders`

**Request**
```xml
<ga:GetTransferOrdersRequest xmlns:ga="urn:globalavicola:sap:inbound:v1">
  <ga:Header>
    <ga:RequestId>REQ-20260922-0006</ga:RequestId>
    <ga:SchemaVersion>1.0</ga:SchemaVersion>
    <ga:ClientSystem>GLOBAL_AVICOLA</ga:ClientSystem>
    <ga:CompanyCode>1000</ga:CompanyCode>
    <ga:FromDate>2026-09-01</ga:FromDate>
    <ga:ToDate>2026-09-22</ga:ToDate>
    <ga:PageSize>50</ga:PageSize>
  </ga:Header>
</ga:GetTransferOrdersRequest>
```

**Response**
```xml
<ga:GetTransferOrdersResponse xmlns:ga="urn:globalavicola:sap:inbound:v1">
  <ga:Header>
    <ga:RequestId>REQ-20260922-0006</ga:RequestId>
    <ga:ResponseTimestamp>2026-09-22T10:24:47Z</ga:ResponseTimestamp>
    <ga:Success>true</ga:Success>
    <ga:SchemaVersion>1.0</ga:SchemaVersion>
    <ga:RecordCount>1</ga:RecordCount>
    <ga:HasMore>false</ga:HasMore>
  </ga:Header>
  <ga:Records>
    <ga:TransferOrder>
      <ga:TRANSFER_NUMBER>4500016001</ga:TRANSFER_NUMBER>
      <ga:DOCUMENT_NUMBER>4900120490</ga:DOCUMENT_NUMBER>
      <ga:MOVEMENT_TYPE>641</ga:MOVEMENT_TYPE>
      <ga:MATERIAL>000000000000105012</ga:MATERIAL>
      <ga:MATERIAL_DESCRIPTION>ALIMENTO INICIADOR</ga:MATERIAL_DESCRIPTION>
      <ga:SOURCE_COMPANY>1000</ga:SOURCE_COMPANY>
      <ga:SOURCE_PLANT>1000</ga:SOURCE_PLANT>
      <ga:DESTINATION_COMPANY>1000</ga:DESTINATION_COMPANY>
      <ga:DESTINATION_PLANT>4100</ga:DESTINATION_PLANT>
      <ga:QUANTITY>12500.000</ga:QUANTITY>
      <ga:UNIT>KG</ga:UNIT>
      <ga:DOCUMENT_DATE>2026-09-21</ga:DOCUMENT_DATE>
      <ga:POSTING_DATE>2026-09-21</ga:POSTING_DATE>
      <ga:STATUS>POSTED</ga:STATUS>
    </ga:TransferOrder>
  </ga:Records>
</ga:GetTransferOrdersResponse>
```

## 7 · Ejemplo de SOAP Fault (técnico)

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <soapenv:Fault>
      <faultcode>soapenv:Server</faultcode>
      <faultstring>TEMPORARY_UNAVAILABLE</faultstring>
      <detail>
        <ga:FaultDetail xmlns:ga="urn:globalavicola:sap:inbound:v1">
          <ga:ErrorCode>TEMPORARY_UNAVAILABLE</ga:ErrorCode>
          <ga:ErrorMessage>SAP en mantenimiento; reintentar más tarde</ga:ErrorMessage>
          <ga:CorrelationId>SOLP-20260922-102500-7f3a</ga:CorrelationId>
        </ga:FaultDetail>
      </detail>
    </soapenv:Fault>
  </soapenv:Body>
</soapenv:Envelope>
```

## 8 · Ejemplo de error funcional (respuesta normal, no Fault)

```xml
<ga:GetPurchaseOrdersResponse xmlns:ga="urn:globalavicola:sap:inbound:v1">
  <ga:Header>
    <ga:RequestId>REQ-20260922-0007</ga:RequestId>
    <ga:ResponseTimestamp>2026-09-22T10:26:00Z</ga:ResponseTimestamp>
    <ga:Success>false</ga:Success>
    <ga:ErrorCode>INVALID_FILTER</ga:ErrorCode>
    <ga:ErrorMessage>Rango de fechas inválido: FromDate posterior a ToDate</ga:ErrorMessage>
    <ga:SchemaVersion>1.0</ga:SchemaVersion>
    <ga:RecordCount>0</ga:RecordCount>
    <ga:HasMore>false</ga:HasMore>
  </ga:Header>
  <ga:Records/>
</ga:GetPurchaseOrdersResponse>
```

**Nota**: los valores de ejemplo (nombres, códigos, batch) son **ilustrativos**, derivados de patrones legacy identificados como `LEGACY_CONFIRMED`; no constituyen datos reales ni contrato de datos.
