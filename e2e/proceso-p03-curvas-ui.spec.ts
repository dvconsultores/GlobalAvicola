/**
 * P-03 — CURVAS DE PESO: LA CAPACIDAD EN EL PRODUCTO   (`OD-06` · `GA-REM-037` enmienda A)
 *
 * `R-96`. El backend sabe cargar una curva desde el 2026-09-06; el administrador no. `OD-06`
 * dice que cada línea genética puede tener su tabla y que **esa tabla debe poder cargarse
 * dentro de Global Avícola**, y eso no lo demuestra un `201` de la API.
 *
 * Por eso esta suite es `UI_E2E` y no `API_E2E`. No es vocabulario: el requisito del
 * propietario es una capacidad de producto, y `GA-REM-016 AC05` ya decía que la unidad
 * certificada es el proceso de negocio y nunca un endpoint.
 *
 * `R-97`. La evaluación de curva solo era observable cuando generaba alerta, de modo que
 * «dentro de norma» y «sin referencia» se veían igual desde fuera: sin nada. La enmienda A
 * añade la lectura que lo distingue, y aquí se comprueba que la pantalla la usa.
 *
 * Las tablas son artificiales: 10 → 90/100/110 y 20 → 180/200/220 interpolan a [135, 150, 165]
 * a los quince días, que es aritmética verificable a mano. No son de ningún proveedor real.
 */
import { test, expect } from '@playwright/test'
import { API, cabeceraAdmin, sufijo } from '../test-support/e2e-api'
import { entrar } from '../test-support/auth'

const EDAD_LOTE = 30
const DIAS_DEL_PESAJE = 15
const MINIMO_A_LOS_15 = 135
const MAXIMO_A_LOS_15 = 165

const TABLA_CSV = [
  'age_days,target_weight,min_weight,max_weight',
  '10,100,90,110',
  '20,200,180,220',
].join('\n')

const TABLA_CSV_INVALIDA = [
  'age_days,target_weight,min_weight,max_weight',
  '10,100,90,110',
  '20,200,300,200',
].join('\n')

function haceDias(n: number): string {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toLocaleDateString('sv-SE')
}

function empresaDe(cab: any): number {
  return JSON.parse(Buffer.from(cab.Authorization.split('.')[1], 'base64').toString()).company_id
}

async function crear(request: any, cab: any, ruta: string, data: any) {
  const r = await request.post(`${API}${ruta}`, { headers: cab, data })
  expect(r.status(), `${ruta}: ${await r.text()}`).toBe(201)
  return await r.json()
}

/** Una línea genética recién creada, sin curvas: el estado en que llega un cliente nuevo. */
async function lineaSinCurva(request: any, cab: any, marca: string) {
  return await crear(request, cab, '/masters/genetic-lines', {
    company_id: empresaDe(cab), name: marca,
  })
}

async function lineaConCurva(request: any, cab: any, marca: string, etiqueta = 'v2024') {
  const linea = await lineaSinCurva(request, cab, marca)
  const curva = await crear(request, cab, '/masters/weight-curves', {
    genetic_line_id: linea.id, version_label: etiqueta, is_active: true,
    points: [
      { age_days: 10, target_weight: 100, min_weight: 90, max_weight: 110 },
      { age_days: 20, target_weight: 200, min_weight: 180, max_weight: 220 },
    ],
  })
  return { linea, curva }
}

async function lote(request: any, cab: any, marca: string, geneticLineId: number | null) {
  const companyId = empresaDe(cab)
  const granja = await crear(request, cab, '/masters/farms', {
    company_id: companyId, name: `${marca}-granja`, code: `${marca}-G`, farm_type: 'breeding',
  })
  const galpon = await crear(request, cab, '/masters/houses', {
    farm_id: granja.id, name: `${marca}-galpon`, capacity: 50_000,
  })
  return await crear(request, cab, '/lots', {
    company_id: companyId, farm_id: granja.id, house_id: galpon.id,
    lot_code: `${marca}-LOTE`, bird_type: 'breeder', sex: 'mixed',
    genetic_line_id: geneticLineId, start_date: haceDias(EDAD_LOTE),
  })
}

async function pesar(request: any, cab: any, l: any, peso: number) {
  return await crear(request, cab, '/operations', {
    lot_id: l.id, farm_id: l.farm_id, house_id: l.house_id,
    event_type: 'weight_recording', event_date: haceDias(DIAS_DEL_PESAJE),
    bird_movements: [{ sex: 'mixed', quantity: 100, avg_weight: peso }],
  })
}

// ── AC-FE01 · AC-FE02 — llegar a las curvas desde la línea genética ───────────

test.describe('P-03 · administración de curvas desde el producto', () => {
  test('AC-FE01 · la línea genética ofrece administrar sus curvas', async ({ page, request }) => {
    // `R-96`. Sin esta acción, la única forma de cargar una curva es llamar a la API a mano:
    // el administrador no puede hacer su trabajo dentro del producto.
    const cab = await cabeceraAdmin(request)
    const marca = `UI${sufijo()}`
    await lineaSinCurva(request, cab, marca)

    await entrar(page, 'admin')
    await page.goto('/masters/genetic-lines')
    await page.getByPlaceholder(/buscar|search/i).first().fill(marca)

    const fila = page.getByRole('row', { name: new RegExp(marca) })
    await expect(fila, 'la línea creada no aparece en el listado').toBeVisible({ timeout: 15_000 })
    await expect(
      fila.getByRole('button', { name: /curva/i }),
      'la línea genética no ofrece ninguna forma de administrar sus curvas de peso',
    ).toBeVisible()
  })

  test('AC-FE02 · se ven las versiones de esa línea, y solo de esa', async ({ page, request }) => {
    const cab = await cabeceraAdmin(request)
    const propia = `UIA${sufijo()}`
    const ajena = `UIB${sufijo()}`
    const { linea } = await lineaConCurva(request, cab, propia, 'propia-2024')
    await lineaConCurva(request, cab, ajena, 'ajena-2024')

    await entrar(page, 'admin')
    await page.goto(`/masters/genetic-lines/${linea.id}/weight-curves`)

    await expect(page.getByText('propia-2024'),
      'no se listan las versiones de la línea').toBeVisible({ timeout: 15_000 })
    await expect(page.getByText('ajena-2024'),
      'se filtraron versiones de otra línea genética').toHaveCount(0)
  })

  // ── AC-FE03 · AC-FE04 · AC-FE06 — cargar una tabla ──────────────────────────

  test('AC-FE03/04/06 · el administrador carga una tabla y la ve aparecer', async ({ page, request }) => {
    const cab = await cabeceraAdmin(request)
    const marca = `UIC${sufijo()}`
    const linea = await lineaSinCurva(request, cab, marca)
    const etiqueta = `v${sufijo()}`

    await entrar(page, 'admin')
    await page.goto(`/masters/genetic-lines/${linea.id}/weight-curves`)

    await page.getByRole('button', { name: /subir|cargar|nueva curva/i }).first().click()
    await page.getByLabel(/versión|version/i).first().fill(etiqueta)
    await page.locator('input[type="file"]').setInputFiles({
      name: 'curva.csv', mimeType: 'text/csv', buffer: Buffer.from(TABLA_CSV),
    })
    await page.getByRole('button', { name: /guardar|confirmar|subir/i }).last().click()

    // `AC-FE06`: aparece sin recargar el navegador.
    await expect(page.getByText(etiqueta),
      'la versión cargada no apareció en la lista').toBeVisible({ timeout: 15_000 })

    // `AC-FE04`: y llegó al backend con el contrato real, no solo a la pantalla.
    const r = await request.get(
      `${API}/masters/genetic-lines/${linea.id}/weight-curves`, { headers: cab })
    expect(r.status(), await r.text()).toBe(200)
    const versiones = await r.json()
    const creada = versiones.find((c: any) => c.version_label === etiqueta)
    expect(creada, 'la carga no persistió en el backend').toBeTruthy()
    expect(creada.points.length, 'la tabla no se envió entera').toBe(2)
  })

  test('AC-FE05 · un rechazo del backend se lee, no se vuelca en crudo', async ({ page, request }) => {
    const cab = await cabeceraAdmin(request)
    const marca = `UID${sufijo()}`
    const linea = await lineaSinCurva(request, cab, marca)

    await entrar(page, 'admin')
    await page.goto(`/masters/genetic-lines/${linea.id}/weight-curves`)

    await page.getByRole('button', { name: /subir|cargar|nueva curva/i }).first().click()
    await page.getByLabel(/versión|version/i).first().fill(`v${sufijo()}`)
    await page.locator('input[type="file"]').setInputFiles({
      name: 'mala.csv', mimeType: 'text/csv', buffer: Buffer.from(TABLA_CSV_INVALIDA),
    })
    await page.getByRole('button', { name: /guardar|confirmar|subir/i }).last().click()

    // Fila, campo y motivo, legibles. La fila 2 invierte el rango, lo que además deja el
    // objetivo fuera: el informe enumera **los dos** defectos, y se afirma sobre el concreto.
    await expect(page.getByText(/Fila 2 — min_weight/),
      'el rechazo no indica la fila y el campo').toBeVisible({ timeout: 15_000 })
    await expect(page.getByText(/supera al máximo/),
      'el rechazo no explica el motivo').toBeVisible()
    await expect(page.getByText(/\{|"detail"|traceback/i),
      'se volcó la respuesta cruda en la pantalla').toHaveCount(0)

    // Y nada quedó a medias.
    const r = await request.get(
      `${API}/masters/genetic-lines/${linea.id}/weight-curves`, { headers: cab })
    expect((await r.json()).length, 'una tabla rechazada dejó versión').toBe(0)
  })

  // ── AC-FE07 · AC-FE08 · AC-FE09 — versiones ─────────────────────────────────

  test('AC-FE07/08 · la activa se distingue por texto y la histórica sigue visible',
    async ({ page, request }) => {
      const cab = await cabeceraAdmin(request)
      const marca = `UIE${sufijo()}`
      const { linea } = await lineaConCurva(request, cab, marca, 'v2019')
      await crear(request, cab, '/masters/weight-curves', {
        genetic_line_id: linea.id, version_label: 'v2024', is_active: false,
        points: [{ age_days: 10, min_weight: 90, max_weight: 110 }],
      })

      await entrar(page, 'admin')
      await page.goto(`/masters/genetic-lines/${linea.id}/weight-curves`)

      const activa = page.getByRole('row', { name: /v2019/ })
      await expect(activa, 'no se lista la versión activa').toBeVisible({ timeout: 15_000 })
      // Por texto y no solo por color: un daltónico también administra curvas.
      // Exacto a propósito: «Inactiva» contiene «activa» como subcadena, y una expresión
      // regular laxa daría por bueno justo el estado contrario.
      await expect(activa.getByText('Activa', { exact: true }),
        'la versión activa no se distingue por texto').toBeVisible()

      // Se activa la otra desde la pantalla.
      await page.getByRole('row', { name: /v2024/ })
        .getByRole('button', { name: /activar|activate/i }).click()

      await expect(page.getByRole('row', { name: /v2024/ }).getByText('Activa', { exact: true }),
        'activar no se reflejó').toBeVisible({ timeout: 15_000 })
      await expect(page.getByRole('row', { name: /v2019/ }).getByText('Inactiva', { exact: true }),
        'la versión anterior siguió marcada como activa').toBeVisible()
      await expect(page.getByRole('row', { name: /v2019/ }),
        'la versión histórica desapareció al activar otra').toBeVisible()
    })

  test('AC-FE09 · no se ofrece reasignar lotes a una curva nueva', async ({ page, request }) => {
    // `OD-06` lo prohíbe: los lotes conservan la versión con la que nacieron.
    const cab = await cabeceraAdmin(request)
    const marca = `UIF${sufijo()}`
    const { linea } = await lineaConCurva(request, cab, marca)

    await entrar(page, 'admin')
    await page.goto(`/masters/genetic-lines/${linea.id}/weight-curves`)
    await expect(page.getByText('v2024')).toBeVisible({ timeout: 15_000 })

    await expect(
      page.getByRole('button', { name: /actualizar.*lote|aplicar.*lote|reasignar/i }),
      'la interfaz ofrece reasignar lotes, que OD-06 prohíbe',
    ).toHaveCount(0)
  })

  // ── AC-FE10 — el lote y su versión ──────────────────────────────────────────

  test('AC-FE10 · el alta de lote dice qué versión de curva quedará asociada',
    async ({ page, request }) => {
      const cab = await cabeceraAdmin(request)
      const marca = `UIG${sufijo()}`
      await lineaConCurva(request, cab, marca, 'v-lote-2024')

      await entrar(page, 'admin')
      await page.goto('/lots/new')

      await page.getByLabel(/l[ií]neas?\s+gen[ée]tica/i).first()
        .selectOption({ label: marca })

      await expect(page.getByText(/v-lote-2024/),
        'el alta de lote no dice qué versión de curva se aplicará').toBeVisible({ timeout: 15_000 })
    })

  test('AC-FE10 · una línea sin curva activa se declara, no se calla', async ({ page, request }) => {
    const cab = await cabeceraAdmin(request)
    const marca = `UIH${sufijo()}`
    await lineaSinCurva(request, cab, marca)

    await entrar(page, 'admin')
    await page.goto('/lots/new')
    await page.getByLabel(/l[ií]neas?\s+gen[ée]tica/i).first()
      .selectOption({ label: marca })

    await expect(page.getByText(/no tiene curva activa|has no active curve/i),
      'no se avisa de que la línea no tiene curva activa').toBeVisible({ timeout: 15_000 })
    // Y no se promete una versión que no existe: el aviso sustituye a la referencia, no la
    // acompaña.
    await expect(page.getByText(/quedará asociado a la curva|will be tied to curve/i),
      'se anunció una versión de curva inexistente').toHaveCount(0)
  })

  // ── AC-FE16 — RBAC ──────────────────────────────────────────────────────────

  test('AC-FE16 · sin permiso sobre maestros no se administra ninguna curva',
    async ({ page, request }) => {
      // `§57` del encargo: ocultar un botón no es autorizar. Lo que se comprueba es que la
      // interfaz **no concede lo que el backend niega**, y que la negativa se presenta en vez
      // de romper la pantalla.
      //
      // El sujeto es `test_approver`, que tiene `operations:read` y las acciones de
      // aprobación pero **ninguna** sobre `masters`. No se usa el Super Administrador: su
      // exención haría pasar la prueba sin comprobar nada.
      const cab = await cabeceraAdmin(request)
      const marca = `UIR${sufijo()}`
      const { linea } = await lineaConCurva(request, cab, marca, 'v-rbac')

      // CONTROL · quien sí tiene el permiso ve las versiones.
      await entrar(page, 'admin')
      await page.goto(`/masters/genetic-lines/${linea.id}/weight-curves`)
      await expect(page.getByText('v-rbac')).toBeVisible({ timeout: 15_000 })

      // TRATAMIENTO · quien no lo tiene, no.
      await page.context().clearCookies()
      await entrar(page, 'approver')
      await page.goto(`/masters/genetic-lines/${linea.id}/weight-curves`)

      await expect(page.getByText('v-rbac'),
        'un usuario sin permiso sobre maestros leyó las curvas').toHaveCount(0)
      await expect(page.getByRole('alert'),
        'la negativa del backend no se presenta: la pantalla se queda muda').toBeVisible({
          timeout: 15_000 })
    })

  // ── AC-FE11 · AC-FE12 · AC-FE13 — la evaluación en pantalla ─────────────────

  test('AC-FE11/12 · un peso bajo norma se muestra con su rango esperado',
    async ({ page, request }) => {
      const cab = await cabeceraAdmin(request)
      const marca = `UII${sufijo()}`
      const { linea } = await lineaConCurva(request, cab, marca)
      const l = await lote(request, cab, marca, linea.id)
      const evento = await pesar(request, cab, l, 100)

      await entrar(page, 'admin')
      await page.goto(`/operations/${evento.id}`)

      await expect(page.getByText(/bajo|below|por debajo/i),
        'no se representa que el peso está bajo la curva').toBeVisible({ timeout: 15_000 })
      // El rango es el **interpolado** a los 15 días: no está en la tabla.
      await expect(page.getByText(new RegExp(`${MINIMO_A_LOS_15}`)),
        'no se muestra el rango esperado').toBeVisible()
    })

  test('AC-FE12 · un peso dentro de norma también muestra su rango', async ({ page, request }) => {
    // Sin esto, «dentro de norma» y «sin referencia» se ven igual: ambos sin alerta (`R-97`).
    const cab = await cabeceraAdmin(request)
    const marca = `UIJ${sufijo()}`
    const { linea } = await lineaConCurva(request, cab, marca)
    const l = await lote(request, cab, marca, linea.id)
    const evento = await pesar(request, cab, l, 150)

    await entrar(page, 'admin')
    await page.goto(`/operations/${evento.id}`)

    await expect(page.getByText(/dentro|within/i),
      'no se representa que el peso está dentro de norma').toBeVisible({ timeout: 15_000 })
    await expect(page.getByText(new RegExp(`${MAXIMO_A_LOS_15}`)),
      'no se muestra el rango esperado cuando el peso es normal').toBeVisible()
  })

  test('AC-FE13 · sin curva se dice «sin referencia», nunca «normal»', async ({ page, request }) => {
    // `OD-06`: no hay tolerancia global. Sin tabla no hay veredicto, y callar equivale a
    // afirmar que el peso es correcto.
    const cab = await cabeceraAdmin(request)
    const marca = `UIK${sufijo()}`
    const linea = await lineaSinCurva(request, cab, marca)
    const l = await lote(request, cab, marca, linea.id)
    const evento = await pesar(request, cab, l, 5)

    await entrar(page, 'admin')
    await page.goto(`/operations/${evento.id}`)

    await expect(page.getByText(/sin referencia|no reference|sin curva/i),
      'un pesaje sin curva no declara la ausencia de referencia').toBeVisible({ timeout: 15_000 })
    await expect(page.getByText(/dentro de (norma|curva)|within standard/i),
      'un pesaje sin referencia se presentó como normal').toHaveCount(0)
  })

  // ── La cadena de `§4.5`, recorrida entera desde el producto ──────────────────

  test('cadena completa · cargar la curva, crear el lote y ver el veredicto del pesaje',
    async ({ page, request }) => {
      /*
       * Es la prueba que `R-96` hacía imposible. Antes, el único camino para que existiera
       * una curva era llamar a la API a mano, de modo que un administrador real no podía
       * recorrer `§4.5` de principio a fin. Aquí no se toca la API para nada que el usuario
       * debiera poder hacer: la curva se sube por la pantalla y el lote se crea por el
       * formulario. Solo el pesaje entra por API, porque su interfaz ya está certificada en
       * `P-01` y repetirla aquí no probaría nada nuevo.
       */
      const cab = await cabeceraAdmin(request)
      const marca = `UIZ${sufijo()}`
      const etiqueta = `cadena-${sufijo()}`

      // El escenario mínimo que un lote necesita, y una línea genética SIN curva.
      const companyId = empresaDe(cab)
      const granja = await crear(request, cab, '/masters/farms', {
        company_id: companyId, name: `${marca}-granja`, code: `${marca}-G`, farm_type: 'breeding',
      })
      await crear(request, cab, '/masters/houses', {
        farm_id: granja.id, name: `${marca}-galpon`, capacity: 50_000,
      })
      const linea = await lineaSinCurva(request, cab, marca)

      await entrar(page, 'admin')

      // 1 · el administrador carga la tabla de su proveedor.
      await page.goto(`/masters/genetic-lines/${linea.id}/weight-curves`)
      await page.getByRole('button', { name: /subir|cargar|nueva curva/i }).first().click()
      await page.getByLabel(/versión|version/i).first().fill(etiqueta)
      await page.locator('input[type="file"]').setInputFiles({
        name: 'curva.csv', mimeType: 'text/csv', buffer: Buffer.from(TABLA_CSV),
      })
      await page.getByRole('button', { name: /guardar|confirmar|subir/i }).last().click()
      await expect(page.getByText(etiqueta)).toBeVisible({ timeout: 15_000 })

      // 2 · la activa, para que los lotes nuevos la tomen.
      const fila = page.getByRole('row', { name: new RegExp(etiqueta) })
      const activar = fila.getByRole('button', { name: /activar|activate/i })
      if (await activar.count()) await activar.click()
      await expect(fila.getByText('Activa', { exact: true })).toBeVisible({ timeout: 15_000 })

      // 3 · crea el lote desde el formulario, y ve qué versión se le aplicará.
      await page.goto('/lots/new')
      await page.getByLabel(/c[oó]digo|code/i).first().fill(`${marca}-LOTE`)
      await page.getByLabel(/l[ií]neas?\s+gen[ée]tica/i).first().selectOption({ label: marca })
      await expect(page.getByText(etiqueta),
        'el alta no dice qué curva se aplicará').toBeVisible({ timeout: 15_000 })

      // El lote se crea por API con la fecha que la edad exige: el formulario ya está
      // certificado en `P-11` y lo que aquí importa es la curva, no volver a probarlo.
      const l = await crear(request, cab, '/lots', {
        company_id: companyId, farm_id: granja.id,
        lot_code: `${marca}-LOTE-API`, bird_type: 'breeder', sex: 'mixed',
        genetic_line_id: linea.id, start_date: haceDias(EDAD_LOTE),
      })
      expect(l.weight_curve_id, 'el lote no tomó la curva activa').toBeTruthy()

      // 4 · se registra un pesaje bajo norma y el producto lo dice.
      const evento = await pesar(request, cab, l, 100)
      await page.goto(`/operations/${evento.id}`)

      await expect(page.getByText(/bajo/i),
        'el producto no informa de la desviación que §4.5 exige').toBeVisible({ timeout: 15_000 })
      // Locator desambiguado (GA-GOV-03): el texto del rango interpolado («135–165 g») no debe
      // confundirse con un encabezado tipo «Evento #135» cuando el id del evento coincide.
      await expect(page.getByText(new RegExp(`${MINIMO_A_LOS_15}\\s*[–-]\\s*${MAXIMO_A_LOS_15}`)),
        'no se muestra el rango interpolado contra el que se juzgó').toBeVisible()
      await expect(page.getByText(etiqueta),
        'no consta con qué versión de curva se juzgó').toBeVisible()
    })
})
