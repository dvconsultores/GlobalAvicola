/**
 * SPEC 013 · AC-SS-02 (AR-21) — reconciliación acotada ante `403`.
 *
 * Un `403` significa que la UI y el backend divergieron (permisos, menús): se dispara UNA
 * rehidratación de `/me`, con throttle de 30 s, y nunca por fallos de las rutas de sesión
 * (`/me` es la propia rehidratación; `/login` y `/refresh` fallan por credenciales).
 * El error se propaga igual al llamante.
 *
 * Se usa el `api` REAL (axios) con un `adapter` falso por petición; `vi.resetModules()` +
 * import dinámico aisla `lastForbiddenAt` entre tests.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

function failing(status: number) {
  return async (config: any) => {
    const e: any = new Error(`HTTP ${status}`)
    e.config = config
    e.response = { status, data: {}, config, headers: {} }
    throw e
  }
}

async function loadApi() {
  vi.resetModules()
  return await import('../api')
}

beforeEach(() => {
  vi.useFakeTimers()
  vi.setSystemTime(new Date('2026-03-01T10:00:00Z'))
})

afterEach(() => {
  vi.useRealTimers()
  vi.resetModules()
})

describe('SPEC 013 · AC-SS-02 · 403 → rehidratación acotada', () => {
  it('un 403 sobre /lots dispara el manejador una vez y respeta el throttle de 30 s', async () => {
    const mod = await loadApi()
    const onForbidden = vi.fn()
    mod.registerForbiddenHandler(onForbidden)

    await expect(mod.default.get('/lots', { adapter: failing(403) })).rejects.toBeTruthy()
    expect(onForbidden).toHaveBeenCalledTimes(1)

    // Segundo 403 inmediato: throttled.
    await expect(mod.default.get('/lots', { adapter: failing(403) })).rejects.toBeTruthy()
    expect(onForbidden).toHaveBeenCalledTimes(1)

    // Pasados 31 s vuelve a dispararse.
    vi.setSystemTime(new Date(Date.now() + 31_000))
    await expect(mod.default.get('/lots', { adapter: failing(403) })).rejects.toBeTruthy()
    expect(onForbidden).toHaveBeenCalledTimes(2)
  })

  it('un 403 sobre /me NO dispara el manejador (es la propia rehidratación)', async () => {
    const mod = await loadApi()
    const onForbidden = vi.fn()
    mod.registerForbiddenHandler(onForbidden)

    await expect(mod.default.get('/me', { adapter: failing(403) })).rejects.toBeTruthy()
    expect(onForbidden).not.toHaveBeenCalled()
  })

  it('un 403 sobre /login y /refresh NO dispara el manejador (fallo de credenciales)', async () => {
    const mod = await loadApi()
    const onForbidden = vi.fn()
    mod.registerForbiddenHandler(onForbidden)

    await expect(mod.default.post('/login', {}, { adapter: failing(403) })).rejects.toBeTruthy()
    await expect(mod.default.post('/refresh', {}, { adapter: failing(403) })).rejects.toBeTruthy()
    expect(onForbidden).not.toHaveBeenCalled()
  })

  it('un 500 NO dispara el manejador', async () => {
    const mod = await loadApi()
    const onForbidden = vi.fn()
    mod.registerForbiddenHandler(onForbidden)

    await expect(mod.default.get('/lots', { adapter: failing(500) })).rejects.toBeTruthy()
    expect(onForbidden).not.toHaveBeenCalled()
  })

  it('sin manejador registrado un 403 no rompe la propagación del error', async () => {
    const mod = await loadApi()
    const error: any = await mod.default.get('/lots', { adapter: failing(403) }).catch((e: unknown) => e)
    expect(error.response.status).toBe(403)
  })
})
