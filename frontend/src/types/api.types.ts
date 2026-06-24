// ============================================================
// Global Avícola — API Response Types
// ============================================================

/** Standard paginated API response */
export interface PaginatedResponse<T> {
  data: T[]
  meta: {
    page: number
    page_size: number
    total: number
    next_cursor?: string
  }
}

/** Standard error response */
export interface ApiError {
  error: {
    code: string
    message: string
    details?: { field: string; message: string }[]
  }
}

/** Generic success response wrapper */
export interface ApiResponse<T> {
  data: T
}
