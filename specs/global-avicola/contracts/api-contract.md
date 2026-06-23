# API Contract — Global Avícola

> **Spec Kit:** `/speckit.plan` Phase 1 output
> **Base URL:** `/api/v1`
> **Auth:** Bearer JWT
> **Format:** JSON

---

## Auth

```
POST   /api/v1/auth/login              # Login (username, password)
POST   /api/v1/auth/refresh            # Refresh token
POST   /api/v1/auth/logout             # Logout
GET    /api/v1/auth/me                 # Current user profile
```

## Users & Roles

```
GET    /api/v1/users                   # List users (filters, pagination)
POST   /api/v1/users                   # Create user
GET    /api/v1/users/{id}              # Get user
PUT    /api/v1/users/{id}              # Update user
DELETE /api/v1/users/{id}              # Deactivate user (soft)
GET    /api/v1/roles                   # List roles
POST   /api/v1/roles                   # Create role
PUT    /api/v1/roles/{id}              # Update role
GET    /api/v1/permissions             # Available permissions list
```

## Masters

```
GET    /api/v1/masters/companies
POST   /api/v1/masters/companies
GET    /api/v1/masters/farms
POST   /api/v1/masters/farms
GET    /api/v1/masters/houses?farm_id=
POST   /api/v1/masters/houses
GET    /api/v1/masters/hatcheries
GET    /api/v1/masters/incubators
GET    /api/v1/masters/hatchers
GET    /api/v1/masters/genetic-lines
GET    /api/v1/masters/breeds
GET    /api/v1/masters/productive-phases
GET    /api/v1/masters/suppliers
GET    /api/v1/masters/feed-types
GET    /api/v1/masters/vaccines
GET    /api/v1/masters/medications
GET    /api/v1/masters/mortality-causes
GET    /api/v1/masters/cull-causes
GET    /api/v1/masters/transports
GET    /api/v1/masters/processing-plants
GET    /api/v1/masters/rejection-reasons
GET    /api/v1/masters/correction-types
```

## SAP References

```
GET    /api/v1/sap/references?type=&search=
POST   /api/v1/sap/references/import
GET    /api/v1/sap/sync/jobs
GET    /api/v1/sap/sync/jobs/{id}
POST   /api/v1/sap/sync/export
GET    /api/v1/sap/errors
```

## Lots

```
GET    /api/v1/lots?farm_id=&phase=&status=&search=
POST   /api/v1/lots
GET    /api/v1/lots/{id}
PUT    /api/v1/lots/{id}
POST   /api/v1/lots/{id}/close
POST   /api/v1/lots/activate-manual
GET    /api/v1/lots/{id}/balances
GET    /api/v1/lots/{id}/phases
GET    /api/v1/lots/{id}/timeline
```

## Operations

```
POST   /api/v1/operations/feed
POST   /api/v1/operations/weight
POST   /api/v1/operations/mortality
POST   /api/v1/operations/cull
POST   /api/v1/operations/vaccination
POST   /api/v1/operations/medication
POST   /api/v1/operations/bird-reception
POST   /api/v1/operations/bird-distribution
POST   /api/v1/operations/bird-transfer
POST   /api/v1/operations/bird-exit
POST   /api/v1/operations/egg-collection
POST   /api/v1/operations/egg-classification
POST   /api/v1/operations/egg-dispatch
POST   /api/v1/operations/egg-reception-hatchery
POST   /api/v1/operations/incubation-load
POST   /api/v1/operations/ovoscopy
POST   /api/v1/operations/transfer-hatcher
POST   /api/v1/operations/birth
POST   /api/v1/operations/chick-dispatch
POST   /api/v1/operations/farm-inspection
POST   /api/v1/operations/transport-inspection
POST   /api/v1/operations/hatchery-inspection
POST   /api/v1/operations/grandparent-import
POST   /api/v1/operations/lot-closure
GET    /api/v1/operations?lot_id=&farm_id=&event_type=&status=&date_from=&date_to=
GET    /api/v1/operations/{id}
PUT    /api/v1/operations/{id}          # Only if status=DRAFT or REGISTERED
POST   /api/v1/operations/{id}/submit   # Submit to review
DELETE /api/v1/operations/{id}          # Soft delete (audited)
```

## Review Center

```
GET    /api/v1/review/pending?farm_id=&lot_id=&event_type=&date_from=&date_to=
POST   /api/v1/review/batches
GET    /api/v1/review/batches/{id}
POST   /api/v1/review/batches/{id}/start
POST   /api/v1/review/batches/{id}/return    # Return to operator
POST   /api/v1/review/batches/{id}/complete  # Complete review
```

## Corrections

```
POST   /api/v1/corrections               # Create correction (audited)
GET    /api/v1/corrections/{event_id}     # View corrections for an event
```

## Approvals

```
GET    /api/v1/approvals/pending
POST   /api/v1/approvals/{event_id}/approve
POST   /api/v1/approvals/{event_id}/reject
POST   /api/v1/approvals/batch-approve
POST   /api/v1/approvals/consolidate
```

## Audit

```
GET    /api/v1/audit?user_id=&lot_id=&farm_id=&action=&date_from=&date_to=
GET    /api/v1/audit/{id}
GET    /api/v1/audit/event/{event_id}/timeline
```

## Reports & Dashboard

```
GET    /api/v1/dashboard/mobile
GET    /api/v1/dashboard/admin
GET    /api/v1/reports/lot/{id}
GET    /api/v1/reports/kpis/mortality
GET    /api/v1/reports/kpis/feed-conversion
GET    /api/v1/reports/kpis/egg-production
GET    /api/v1/reports/kpis/hatchery
GET    /api/v1/reports/sap-comparison
GET    /api/v1/reports/export/{type}?format=excel|pdf
```

## Standard Response Formats

### Success (single)
```json
{ "data": { ... } }
```

### Success (list)
```json
{ "data": [...], "meta": { "page": 1, "page_size": 20, "total": 150 } }
```

### Error
```json
{ "error": { "code": "VALIDATION_ERROR", "message": "Human-readable error message", "details": [...] } }
```

### HTTP Status Codes
- `200` Success
- `201` Created
- `400` Validation error / Business rule violation
- `401` Unauthenticated
- `403` Forbidden (insufficient permissions)
- `404` Not found
- `409` Conflict (duplicate, idempotency)
- `422` Unprocessable entity
- `500` Internal server error
