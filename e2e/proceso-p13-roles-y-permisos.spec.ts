/**
 * P-13 — AUTENTICACIÓN Y GESTIÓN DE USUARIOS   (`docs/02 §3.1`)
 *
 * `GA-REM-034` cerró tres huecos de `§3.1.3`:
 *   R-92  no había superficie para administrar roles: ni ruta ni componente
 *   R-93  `RoleUpdate` no incluía permisos: un rol nacía con los suyos para siempre
 *   R-94  no había catálogo de permisos, así que la interfaz tendría que adivinarlos
 *
 * El enforcement no se toca: `GA-REM-002` lo certificó. Esto es **administración**.
 */
import { test, expect } from '@playwright/test'
import { API, cabeceraAdmin, sufijo } from '../test-support/e2e-api'
import { entrar } from '../test-support/auth'

test.describe('P-13 · administración de roles y permisos', () => {
  test('la superficie de administración existe y muestra el catálogo', async ({ page }) => {
    // `AC04`. No había ruta: `/roles` no estaba declarada en `App.tsx`.
    await entrar(page, 'admin')
    await page.goto('/roles')

    await expect(page.getByRole('button', { name: /nuevo rol|new role/i })).toBeVisible({ timeout: 15_000 })

    await page.getByRole('button', { name: /nuevo rol|new role/i }).click()

    // `AC01` · los módulos y las acciones vienen del servidor, no de una lista escrita a mano.
    await expect(page.getByRole('checkbox', { name: 'lots:read' })).toBeVisible()
    await expect(page.getByRole('checkbox', { name: 'audit:read' })).toBeVisible()
    await expect(page.getByRole('checkbox', { name: 'operations:approve' })).toBeVisible()
  })

  test('un rol se crea desde la interfaz con los permisos marcados', async ({ page, request }) => {
    // `AC05` · `R-47`/`P0-14`: lo que la interfaz envía debe llegar al dominio. Antes
    // `authService.createRole` ni siquiera declaraba `permissions`.
    const nombre = `P13-${sufijo()}`
    await entrar(page, 'admin')
    await page.goto('/roles')
    await page.getByRole('button', { name: /nuevo rol|new role/i }).click()

    await page.getByLabel(/nombre|name/i).first().fill(nombre)
    await page.getByRole('checkbox', { name: 'lots:read' }).check()
    await page.getByRole('checkbox', { name: 'masters:update' }).check()
    await page.getByRole('button', { name: /guardar|save/i }).click()

    await expect(page.getByText(nombre)).toBeVisible({ timeout: 15_000 })

    // Y llegó al dominio con sus permisos, no solo con el nombre.
    const cab = await cabeceraAdmin(request)
    const r = await request.get(`${API}/roles`, { headers: cab })
    expect(r.status()).toBe(200)
    const rol = (await r.json()).find((x: any) => x.name === nombre)
    expect(rol, 'el rol no se persistió').toBeTruthy()
    const pares = (rol.permissions ?? []).map((p: any) => `${p.module}:${p.action}`).sort()
    expect(pares).toEqual(['lots:read', 'masters:update'])
  })

  test('editar los permisos sustituye el conjunto, no lo acumula', async ({ request }) => {
    // `AC02` por API: la persistencia se comprueba donde vive.
    const cab = await cabeceraAdmin(request)
    const creado = await request.post(`${API}/roles`, {
      headers: cab,
      data: {
        name: `P13E-${sufijo()}`, description: 'sustitución',
        permissions: [{ module: 'lots', action: 'read' }, { module: 'lots', action: 'create' }],
      },
    })
    expect(creado.status()).toBe(201)
    const id = (await creado.json()).id

    const editado = await request.put(`${API}/roles/${id}`, {
      headers: cab, data: { permissions: [{ module: 'audit', action: 'read' }] },
    })
    expect(editado.status(), await editado.text()).toBe(200)

    const listado = await request.get(`${API}/roles`, { headers: cab })
    const rol = (await listado.json()).find((x: any) => x.id === id)
    const pares = (rol.permissions ?? []).map((p: any) => `${p.module}:${p.action}`).sort()
    expect(pares, 'el conjunto debe sustituirse, no acumularse').toEqual(['audit:read'])
  })
})
