/**
 * R-220 · Lote D (D1/D2/D5) — retiro de código muerto y alineación de tipos.
 *
 * D1: los hooks sin uso (`{error}` obsoleto) y `types/api.types.ts` no deben existir.
 * D2: `auth.service.UserResponse` alineado al contrato; `lots.service` sin el `sap_reference`
 *     retirado en A10; `review.service` con enumerados tipados.
 * D5: `ProtectedRoute.roles` (chequeo muerto) fuera de `App.tsx`.
 */
import { describe, it, expect } from 'vitest'
import { existsSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const here = dirname(fileURLToPath(import.meta.url))
const src = (rel: string) => readFileSync(resolve(here, '..', rel), 'utf8')
const exists = (rel: string) => existsSync(resolve(here, '..', rel))

describe('R-220 · Lote D', () => {
  const MUERTOS = ['useApprovals', 'useLots', 'useMasters', 'useOperations', 'useReports', 'useReview', 'useSap', 'useSidebar']

  it('D1 · los hooks sin uso no existen', () => {
    for (const h of MUERTOS) expect(exists(`hooks/${h}.ts`), `hooks/${h}.ts`).toBe(false)
  })

  it('D1 · hooks vivos conservados (telegram/media-query)', () => {
    expect(exists('hooks/useTelegram.ts')).toBe(true)
    expect(exists('hooks/useMediaQuery.ts')).toBe(true)
  })

  it('D1 · `types/api.types.ts` retirado', () => {
    expect(exists('types/api.types.ts')).toBe(false)
  })

  it('D2 · UserResponse alineado con el contrato (is_super_admin, company_name)', () => {
    const s = src('services/auth.service.ts')
    expect(s).toContain('is_super_admin')
    expect(s).toContain('company_name')
  })

  it('D2 · `sap_reference` ya no viaja en LotResponse (A10)', () => {
    expect(src('services/lots.service.ts')).not.toContain('sap_reference')
  })

  it('D2 · review.service con enumerado tipado de acción', () => {
    const s = src('services/review.service.ts')
    expect(s).not.toContain('action_type: string')
    expect(s).toContain("'review_started'")
  })

  it('D5 · ProtectedRoute sin el prop `roles` muerto', () => {
    const s = src('App.tsx')
    expect(s).not.toContain('roles?: string[]')
    expect(s).not.toContain('roles && roles.length > 0')
  })
})
