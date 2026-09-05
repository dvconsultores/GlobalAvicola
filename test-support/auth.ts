/**
 * Autenticación compartida para las suites E2E — `GA-REM-016 AC06`.
 *
 * Antes, cada spec repetía su propio login y la suite heredada arrastraba credenciales
 * literales (`admin` / `admin123`) de usuarios que ya no existen: la siembra crea
 * `test_admin`, `test_operator` y `test_approver`, con contraseñas que el arnés genera por
 * ejecución. Ese desfase dejó **once** casos fallando sin que el sistema tuviera nada malo.
 *
 * Las credenciales vienen del entorno y nunca del repositorio (`GA-REM-004`). Si faltan, se
 * falla con un mensaje que dice qué hacer, en lugar de intentar el login y dejar un error
 * incomprensible tres afirmaciones más abajo.
 */
import { expect, type Page } from '@playwright/test'

export type Rol = 'admin' | 'operator' | 'approver'

const USUARIOS: Record<Rol, { usuario: string; variable: string }> = {
  admin: { usuario: 'test_admin', variable: 'GA_TEST_ADMIN_PASSWORD' },
  operator: { usuario: 'test_operator', variable: 'GA_TEST_OPERATOR_PASSWORD' },
  approver: { usuario: 'test_approver', variable: 'GA_TEST_APPROVER_PASSWORD' },
}

/** Credenciales del rol pedido, tomadas del entorno. */
export function credenciales(rol: Rol = 'admin'): { usuario: string; clave: string } {
  const { usuario, variable } = USUARIOS[rol]
  const clave = process.env[variable]
  if (!clave) {
    throw new Error(
      `${variable} no está definida. Ejecute la suite con \`bash scripts_e2e.sh\`, ` +
        'que genera las credenciales de prueba y siembra los usuarios.',
    )
  }
  return { usuario, clave }
}

/**
 * Entra por la interfaz, como lo haría una persona.
 *
 * Se autentica por la pantalla y no inyectando un token porque varias de las pruebas que
 * dependen de esto comprueban comportamiento de la propia interfaz; un atajo por API las
 * dejaría en un estado que ningún usuario real alcanza.
 */
export async function entrar(page: Page, rol: Rol = 'admin'): Promise<void> {
  const { usuario, clave } = credenciales(rol)

  await page.goto('/login')
  await page
    .getByLabel(/usuario|username/i)
    .fill(usuario)
    .catch(async () => {
      await page.locator('input[name="username"], input#login-username').first().fill(usuario)
    })
  await page.locator('input[type="password"]').first().fill(clave)
  await page.locator('button[type="submit"]').first().click()

  await expect(
    page,
    `el login de ${usuario} debe llevar fuera de /login`,
  ).not.toHaveURL(/\/login/, { timeout: 20_000 })
}
