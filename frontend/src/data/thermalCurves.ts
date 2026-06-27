/**
 * Ross / Cobb Technical Performance Curves
 * =========================================
 * Optimal temperature and humidity ranges per week of life.
 * Sources: Ross 308 Broiler Management Guide, Cobb 500 Broiler Guide,
 * Ross Grandparent Management Guide, Cobb Breeder Management Guide.
 *
 * All values are industry standards — adjust per farm altitude and climate.
 */

export interface WeekRange {
  tempMin: number
  tempMax: number
  humidMin: number
  humidMax: number
}

// ── Broiler Temperature Zones (°C) by week ─────────────────

export const BROILER_TEMP_ZONES: Record<number, WeekRange> = {
  1:  { tempMin: 30, tempMax: 33, humidMin: 50, humidMax: 70 },
  2:  { tempMin: 28, tempMax: 30, humidMin: 50, humidMax: 70 },
  3:  { tempMin: 26, tempMax: 28, humidMin: 50, humidMax: 70 },
  4:  { tempMin: 24, tempMax: 26, humidMin: 50, humidMax: 70 },
  5:  { tempMin: 22, tempMax: 24, humidMin: 50, humidMax: 70 },
  6:  { tempMin: 20, tempMax: 22, humidMin: 50, humidMax: 70 },
  7:  { tempMin: 18, tempMax: 22, humidMin: 55, humidMax: 75 },
  8:  { tempMin: 18, tempMax: 22, humidMin: 55, humidMax: 75 },
  9:  { tempMin: 18, tempMax: 22, humidMin: 55, humidMax: 75 },
}

// ── Breeder / Grandparent Rearing Temperature Zones (°C) ───

export const BREEDER_REARING_TEMP_ZONES: Record<number, WeekRange> = {
  1:  { tempMin: 32, tempMax: 35, humidMin: 50, humidMax: 70 },
  2:  { tempMin: 30, tempMax: 32, humidMin: 50, humidMax: 70 },
  3:  { tempMin: 28, tempMax: 30, humidMin: 50, humidMax: 70 },
  4:  { tempMin: 26, tempMax: 28, humidMin: 50, humidMax: 70 },
  5:  { tempMin: 24, tempMax: 26, humidMin: 50, humidMax: 70 },
  6:  { tempMin: 22, tempMax: 24, humidMin: 50, humidMax: 70 },
  7:  { tempMin: 21, tempMax: 23, humidMin: 50, humidMax: 70 },
  8:  { tempMin: 20, tempMax: 22, humidMin: 50, humidMax: 70 },
  9:  { tempMin: 20, tempMax: 22, humidMin: 50, humidMax: 75 },
  10: { tempMin: 20, tempMax: 22, humidMin: 50, humidMax: 75 },
  11: { tempMin: 20, tempMax: 22, humidMin: 50, humidMax: 75 },
  12: { tempMin: 20, tempMax: 22, humidMin: 50, humidMax: 75 },
  13: { tempMin: 20, tempMax: 22, humidMin: 50, humidMax: 75 },
  14: { tempMin: 20, tempMax: 22, humidMin: 50, humidMax: 75 },
  15: { tempMin: 20, tempMax: 22, humidMin: 50, humidMax: 75 },
  16: { tempMin: 20, tempMax: 22, humidMin: 50, humidMax: 75 },
  17: { tempMin: 20, tempMax: 22, humidMin: 50, humidMax: 75 },
  18: { tempMin: 20, tempMax: 22, humidMin: 50, humidMax: 75 },
  19: { tempMin: 18, tempMax: 22, humidMin: 55, humidMax: 80 },
  20: { tempMin: 18, tempMax: 22, humidMin: 55, humidMax: 80 },
  21: { tempMin: 18, tempMax: 22, humidMin: 55, humidMax: 80 },
  22: { tempMin: 18, tempMax: 22, humidMin: 55, humidMax: 80 },
  23: { tempMin: 18, tempMax: 22, humidMin: 55, humidMax: 80 },
  24: { tempMin: 18, tempMax: 22, humidMin: 55, humidMax: 80 },
}

// ── Breeder / Grandparent Production Temperature Zones (°C) ─

export const BREEDER_PRODUCTION_TEMP_ZONES: Record<number, WeekRange> = {
  1:  { tempMin: 20, tempMax: 24, humidMin: 50, humidMax: 75 },
  2:  { tempMin: 20, tempMax: 24, humidMin: 50, humidMax: 75 },
  3:  { tempMin: 18, tempMax: 22, humidMin: 50, humidMax: 75 },
  4:  { tempMin: 18, tempMax: 22, humidMin: 50, humidMax: 75 },
  // Weeks 5-40: stable 18-22°C
}

// ── Hatchery Temperature/Humidity Zones ─────────────────────

export const INCUBATOR_TEMP_ZONES: Record<string, WeekRange> = {
  setter:   { tempMin: 37.2, tempMax: 38.1, humidMin: 50, humidMax: 60 },
  hatcher:  { tempMin: 36.7, tempMax: 37.5, humidMin: 65, humidMax: 80 },
  storage:  { tempMin: 15,   tempMax: 18,   humidMin: 70, humidMax: 80 },
  transport:{ tempMin: 18,   tempMax: 22,   humidMin: 50, humidMax: 70 },
}

// ── Range Status ────────────────────────────────────────────

export type RangeStatus = 'ok' | 'warn' | 'critical'

export function tempStatus(value: number, min: number, max: number): RangeStatus {
  if (value >= min && value <= max) return 'ok'
  // Within 2°C of range → warning
  if (value >= min - 2 && value <= max + 2) return 'warn'
  return 'critical'
}

export function humidityStatus(value: number, min: number, max: number): RangeStatus {
  if (value >= min && value <= max) return 'ok'
  // Within 10% of range → warning
  if (value >= min - 10 && value <= max + 10) return 'warn'
  return 'critical'
}

/**
 * Get the appropriate temperature/humidity zone for a given bird type and week.
 * Returns a WeekRange or null if week/birdType is out of scope.
 */
export function getThermalZone(
  birdType: string,
  phase: string,
  weekNumber: number,
): WeekRange | null {
  // Broiler
  if (birdType === 'broiler' || birdType === 'engorde') {
    if (weekNumber > 9) return BROILER_TEMP_ZONES[9] // Plateau after week 9
    return BROILER_TEMP_ZONES[weekNumber] ?? null
  }

  // Rearing phases (grandparent + breeder)
  if (phase === 'rearing' || phase === 'cria') {
    if (weekNumber > 24) return BREEDER_REARING_TEMP_ZONES[24]
    return BREEDER_REARING_TEMP_ZONES[weekNumber] ?? null
  }

  // Production phases
  if (phase === 'production' || phase === 'produccion') {
    if (weekNumber > 4) return BREEDER_PRODUCTION_TEMP_ZONES[4]
    return BREEDER_PRODUCTION_TEMP_ZONES[weekNumber] ?? BREEDER_PRODUCTION_TEMP_ZONES[1]
  }

  return null
}

/**
 * Default fallback zones when week or bird type is unknown.
 * Conservative wide ranges to avoid false alerts.
 */
export const DEFAULT_THERMAL_ZONE: WeekRange = {
  tempMin: 18, tempMax: 35,
  humidMin: 40, humidMax: 90,
}
