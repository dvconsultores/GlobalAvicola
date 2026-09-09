// ============================================================
// Global Avícola — Shared Domain Types
// Centralized type definitions for core business entities.
// ============================================================

// ---- Enums ----

export type BirdType = 'grandparent' | 'breeder' | 'broiler' | 'hatchery'

export type Sex = 'male' | 'female' | 'mixed'

export type LotStatus = 'active' | 'closed' | 'cancelled'

export type FarmType = 'breeding' | 'production' | 'fattening' | 'mixed'

export type HouseType = 'open' | 'closed' | 'tunnel'

export type ViewType = 'web' | 'mobile'

export type EventStatus =
  | 'draft'
  | 'registered'
  | 'pending_review'
  | 'in_review'
  | 'returned'
  | 'corrected'
  | 'approved'
  | 'rejected'
  | 'consolidated'
  | 'sent_to_sap'
  | 'sap_confirmed'
  | 'sap_error'
  | 'cancelled'

export type EventType =
  | 'bird_reception'
  | 'bird_distribution'
  | 'bird_transfer'
  | 'bird_exit'
  | 'feed_registration'
  | 'water_consumption'
  | 'weight_recording'
  | 'mortality_recording'
  | 'cull_recording'
  | 'vaccination'
  | 'medication'
  | 'farm_inspection'
  | 'transport_inspection'
  | 'hatchery_inspection'
  | 'egg_collection'
  | 'egg_classification'
  | 'egg_dispatch'
  | 'egg_reception_hatchery'
  | 'incubation_load'
  | 'ovoscopy'
  | 'transfer_to_hatcher'
  | 'birth_registration'
  | 'chick_dispatch'
  | 'lot_closure'
  | 'grandparent_import'

// ---- Core Entities ----

export interface Company {
  id: number
  name: string
  tax_id?: string
  country?: string
  currency?: string
  is_active: boolean
}

export interface Farm {
  id: number
  company_id: number
  name: string
  code: string
  location?: string
  farm_type: FarmType
  is_active: boolean
}

export interface House {
  id: number
  farm_id: number
  name: string
  capacity: number
  house_type: HouseType
  is_active: boolean
}

export interface Lot {
  id: number
  company_id: number
  lot_code: string
  bird_type: BirdType
  status: LotStatus
  farm_id?: number
  house_id?: number
  start_date: string
  end_date?: string
  genetic_line_id?: number
  breed_id?: number
  current_phase?: string
  age_days?: number
}

export interface OperationEvent {
  id: number
  lot_id?: number
  company_id: number
  event_type: EventType
  event_date: string
  status: EventStatus
  farm_id?: number
  house_id?: number
  observations?: string
  registered_by_id: number
  bird_movements?: BirdMovement[]
  egg_movements?: EggMovement[]
  feed_movements?: FeedMovement[]
  water_liters?: number // `GA-REM-021-A` · B05 (litros)
  hatchery_params?: HatcheryParam[]
  inspection_details?: InspectionDetail[]
}

export interface BirdMovement {
  id?: number
  sex: Sex
  quantity: number
  avg_weight?: number
  week_number?: number
  breed_id?: number
}

export interface EggMovement {
  id?: number
  egg_type: string
  quantity: number
  avg_weight?: number
  classification_date?: string
}

export interface FeedMovement {
  id?: number
  feed_type_id: number
  quantity_kg: number
  sacks_count?: number
  week_number?: number
}

export interface HatcheryParam {
  id?: number
  hatchery_id?: number
  incubator_id?: number
  hatcher_id?: number
  temperature?: number
  humidity?: number
  co2?: number
  quantity_loaded?: number
  quantity_transferred?: number
}

export interface InspectionDetail {
  id?: number
  parameter: string
  value: string
  status: string
}

// ---- User & Auth ----

export interface User {
  id: number
  username: string
  first_name: string
  last_name: string
  email: string
  phone?: string
  role_id: number
  company_id: number
  view_type: ViewType
  is_active: boolean
}

export interface Role {
  id: number
  name: string
  description?: string
  is_active: boolean
}
