# Data Model — Global Avícola

> **Spec Kit:** `/speckit.plan` Phase 1 output
> **Date:** 2026-06-22

---

## 1. Core Entities

### 1.1 Company
```
Company(id, name, tax_id, country, currency, sap_config:JSON, approval_levels:int, is_active, created_at)
```

### 1.2 Farm
```
Farm(id, company_id→Company, name, code, location, farm_type:enum, is_active, created_at)
```

### 1.3 House
```
House(id, farm_id→Farm, name, capacity, house_type:enum, is_active, created_at)
```

### 1.4 Hatchery
```
Hatchery(id, company_id→Company, name, code, location, is_active)
  ├── Incubator(id, hatchery_id→Hatchery, name, capacity, is_active)
  └── Hatcher(id, hatchery_id→Hatchery, name, capacity, is_active)
```

### 1.5 Lot (Central Aggregate)
```
Lot(id, company_id→Company, lot_code, genetic_line_id→GeneticLine,
    breed_id→Breed, bird_type:enum, sex:enum, current_phase_id→ProductivePhase,
    current_farm_id→Farm, current_house_id→House, sap_reference_id→SapReference,
    status:enum, activation_type:enum, start_date, end_date, age_days:calculated,
    created_at, updated_at)
  ├── LotPhase(id, lot_id→Lot, phase_id→ProductivePhase, start_date, end_date,
  │            start_population_male, start_population_female, start_weight_avg)
  ├── OpeningBalance(id, lot_id→Lot (unique), activation_date, phase_at_activation,
  │                  age_days, initial_male_count, initial_female_count,
  │                  accumulated_mortality_male/female, accumulated_culls,
  │                  accumulated_feed_kg, current_avg_weight, ...)
  └── OperationalEvent (many)
```

### 1.6 OperationalEvent (Central Event Aggregate)
```
OperationalEvent(id, lot_id→Lot, phase_id→LotPhase, farm_id→Farm,
                 house_id→House, event_type:enum, event_date, event_time,
                 sap_document_ref→SapReference, status:enum,
                 registered_by→User, reviewed_by→User, approved_by→User,
                 review_batch_id→ReviewBatch, created_at, updated_at, version:int)
  ├── BirdMovement(id, event_id→OperationalEvent, sex, quantity, avg_weight)
  ├── EggMovement(id, event_id→OperationalEvent, egg_type:enum, quantity, avg_weight)
  ├── FeedMovement(id, event_id→OperationalEvent, feed_type_id→FeedType, quantity_kg)
  └── HatcheryMovement(id, event_id→OperationalEvent, hatchery_id, incubator_id, parameters:JSON)
```

### 1.7 Approval Workflow
```
ReviewBatch(id, company_id→Company, batch_type:enum, status:enum, created_by→User, created_at)
  └── ApprovalStep(id, review_batch_id→ReviewBatch, step_number, step_type:enum,
                   assigned_to→User, status:enum, started_at, completed_at)
       └── ApprovalAction(id, approval_step_id→ApprovalStep, action_type:enum,
                          performed_by→User, performed_at, comments,
                          rejection_reason_id→RejectionReason)
            └── CorrectionLog(id, approval_action_id→ApprovalAction,
                             event_id→OperationalEvent, field_name,
                             original_value:JSON, corrected_value:JSON,
                             corrected_by→User, correction_reason, comments)
```

### 1.8 Audit
```
AuditLog(id, company_id→Company, user_id→User, action:enum, entity_type, entity_id:UUID,
         lot_id→Lot, farm_id→Farm, house_id→House, module, previous_state:JSON,
         new_state:JSON, previous_values:JSON, new_values:JSON, change_reason,
         comments, sap_reference_id→SapReference, ip_address, user_agent,
         created_at:microsecond, is_sensitive)
```

### 1.9 SAP Integration
```
SapReference(id, company_id→Company, reference_type:enum, sap_id, sap_description,
             local_alias, raw_data:JSON, is_active, last_synced_at)
SapSyncJob(id, company_id→Company, direction:enum, status:enum, total_records,
           processed_records, error_records, started_at, completed_at)
  └── SapPayload(id, sync_job_id→SapSyncJob, consolidated_movement_id, sap_document_type,
                 sap_reference_id, payload_data:JSON, idempotency_key:SHA256,
                 status:enum, sent_at, confirmed_at, retry_count, max_retries)
       └── SapResponse(id, sap_payload_id→SapPayload (unique), sap_document_id,
                       response_status:enum, response_code, response_message, response_data:JSON)
ConsolidatedMovement(id, company_id→Company, review_batch_id→ReviewBatch,
                     lot_id→Lot, movement_type:enum, sap_reference, summary_data:JSON,
                     status:enum, consolidated_by→User, consolidated_at, sent_to_sap_at)
```

### 1.10 Traceability Bridges (Trazabilidad Generacional)

Cross-lot bridge entities that connect production generations.

```
EggBatch(source_lot_id→Lot, hatchery_lot_id→Lot, dispatch_event_id→OperationalEvent,
         reception_event_id→OperationalEvent, quantity_dispatched:int,
         quantity_received:int?, dispatch_date, reception_date?, notes?, created_at)

ChickBatch(hatchery_lot_id→Lot, broiler_lot_id→Lot, dispatch_event_id→OperationalEvent,
           reception_event_id→OperationalEvent, egg_batch_id→EggBatch,
           quantity_dispatched:int, quantity_received:int?, dispatch_date,
           reception_date?, notes?, created_at)
```

**Generational chain:** `Lot(production)` → `EggBatch` → `Lot(hatchery)` → `ChickBatch` → `Lot(broiler)`

Endpoints: `GET /lots/{id}/traceability` returns the full ancestry tree.

---

## 2. Event Types Enum

```python
class EventType(str, Enum):
    BIRD_RECEPTION = "bird_reception"
    BIRD_DISTRIBUTION = "bird_distribution"
    BIRD_TRANSFER = "bird_transfer"
    FEED_REGISTRATION = "feed_registration"
    WEIGHT_RECORDING = "weight_recording"
    MORTALITY_RECORDING = "mortality_recording"
    CULL_RECORDING = "cull_recording"
    VACCINATION = "vaccination"
    MEDICATION = "medication"
    FARM_INSPECTION = "farm_inspection"
    TRANSPORT_INSPECTION = "transport_inspection"
    EGG_COLLECTION = "egg_collection"
    EGG_CLASSIFICATION = "egg_classification"
    EGG_DISPATCH = "egg_dispatch"
    EGG_RECEPTION_HATCHERY = "egg_reception_hatchery"
    INCUBATION_LOAD = "incubation_load"
    OVOSCOPY = "ovoscopy"
    TRANSFER_TO_HATCHER = "transfer_to_hatcher"
    BIRTH_REGISTRATION = "birth_registration"
    CHICK_DISPATCH = "chick_dispatch"
    BIRD_EXIT = "bird_exit"
    LOT_CLOSURE = "lot_closure"
    GRANDPARENT_IMPORT = "grandparent_import"
    HATCHERY_INSPECTION = "hatchery_inspection"
```

## 3. Status Enum (13 states)

```python
class EventStatus(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"
    RETURNED = "returned"
    CORRECTED = "corrected"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONSOLIDATED = "consolidated"
    SENT_TO_SAP = "sent_to_sap"
    SAP_CONFIRMED = "sap_confirmed"
    SAP_ERROR = "sap_error"
    CANCELLED = "cancelled"
```

## 4. Key Design Decisions

1. **Unified model**: One `OperationalEvent` table with `event_type` discriminator replaces 12+ legacy tables
2. **Event sourcing light**: Balances are calculated from events, not stored as editable fields
3. **Soft delete**: All entities use `is_active` + audit log instead of physical DELETE
4. **Optimistic locking**: `version` field on OperationalEvent for concurrent write protection
5. **Idempotency**: SHA-256 hash of (lot_id + event_type + event_date + sap_reference + data) as idempotency key
6. **Immutable audit**: AuditLog records are created once and never modified or deleted
