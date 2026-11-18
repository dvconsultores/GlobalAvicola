import { test, expect } from '@playwright/test';
import * as fs from 'node:fs';
import { API, cabeceraAdmin, crearEscenario, crearMaestros, hoy, sufijo } from '../test-support/e2e-api';
import { entrar } from '../test-support/auth';

const PREFIJO = 'S1P18D';
const OUT = 'audit/ga-uat-breeder-cria-s1-2026-11-10/evidence';
const SHOTS = `${OUT}/screenshots`;

type Escenario = { companyId: number; farmId: number; houseId: number; lotId: number; codigo: string };
type Resultados = Record<string, { ok: boolean; detalle: string }>;
const resultados: Resultados = {};
const incidencias: string[] = [];

let esc: Escenario;
let vacunaId: number;
let eventoCorregidoId: number;
let eventoEnRevisionId: number;
let loteInfo: any = {}, reporteLote: any = {};
let traducciones: any = {};

function anotar(clave: string, ok: boolean, detalle: string) {
  resultados[clave] = { ok, detalle };
  if (!ok) incidencias.push(`${clave}: ${detalle}`);
}

test.describe('P18D UAT S1 — reportes, i18n y UX', () => {
  test.describe.configure({ mode: 'serial' });

  test.beforeAll(async ({ request }) => {
    const admin = await cabeceraAdmin(request);
    await request.patch(`${API}/business-units/breeder/enable`, { headers: admin, failOnStatusCode: false });
    esc = (await crearEscenario(request, admin, PREFIJO, 'breeder')) as Escenario;
    fs.mkdirSync(SHOTS, { recursive: true });

    const maestros = await crearMaestros(request, admin, PREFIJO);
    vacunaId = maestros.vacunaId;

    const recepcion = {
      event_type: 'bird_reception',
      lot_id: esc.lotId,
      farm_id: esc.farmId,
      house_id: esc.houseId,
      event_date: hoy(),
      received_total: 1000,
      dead_on_arrival: 15,
      rejected_on_arrival: 5,
      bird_movements: [
        { sex: 'male', quantity: 100, avg_weight: 2.0 },
        { sex: 'female', quantity: 880, avg_weight: 1.8 },
      ],
    };
    const rec = await request.post(`${API}/operations`, { headers: admin, data: recepcion, failOnStatusCode: false });
    if (!rec.ok()) throw new Error(`recepción fallo ${rec.status()} ${await rec.text()}`);

    for (let i = 0; i < 2; i++) {
      const m = await request.post(`${API}/operations`, {
        headers: admin,
        data: {
          event_type: 'mortality_recording',
          lot_id: esc.lotId,
          event_date: hoy(),
          bird_movements: [{ sex: 'male', quantity: 3 }],
        },
        failOnStatusCode: false,
      });
      if (!m.ok()) throw new Error(`mortalidad ${i} fallo ${m.status()} ${await m.text()}`);
    }

    const crearVac = async () =>
      request.post(`${API}/operations`, {
        headers: admin,
        data: { event_type: 'vaccination', lot_id: esc.lotId, event_date: hoy(), vaccine_id: vacunaId },
        failOnStatusCode: false,
      });

    // Evento A: corregido (listo para aprobar)
    const va = await crearVac();
    if (!va.ok()) throw new Error(`vacunación A fallo ${va.status()} ${await va.text()}`);
    eventoCorregidoId = (await va.json()).id;
    await request.post(`${API}/operations/${eventoCorregidoId}/submit`, { headers: admin, failOnStatusCode: false });
    await request.post(`${API}/review/start/${eventoCorregidoId}`, { headers: admin, failOnStatusCode: false });
    const corr = await request.post(`${API}/corrections`, {
      headers: admin,
      data: {
        event_id: eventoCorregidoId,
        field_name: 'observations',
        original_value: '',
        corrected_value: 'revisado',
        reason: 'Corrección de prueba UAT',
      },
      failOnStatusCode: false,
    });
    if (!corr.ok()) throw new Error(`corrección fallo ${corr.status()} ${await corr.text()}`);

    // Evento B: en revisión (historial)
    const vb = await crearVac();
    if (!vb.ok()) throw new Error(`vacunación B fallo ${vb.status()} ${await vb.text()}`);
    eventoEnRevisionId = (await vb.json()).id;
    await request.post(`${API}/operations/${eventoEnRevisionId}/submit`, { headers: admin, failOnStatusCode: false });
    await request.post(`${API}/review/start/${eventoEnRevisionId}`, { headers: admin, failOnStatusCode: false });

    const lote = await request.get(`${API}/lots/${esc.lotId}`, { headers: admin, failOnStatusCode: false });
    if (lote.ok()) loteInfo = await lote.json();
    const rep = await request.get(`${API}/reports/lot/${esc.lotId}`, { headers: admin, failOnStatusCode: false });
    if (rep.ok()) reporteLote = await rep.json();

    try {
      traducciones = JSON.parse(fs.readFileSync('frontend/public/locales/es/translation.json', 'utf8'));
    } catch {
      traducciones = {};
    }
  });

  test.afterAll(async () => {
    fs.mkdirSync(SHOTS, { recursive: true });
    fs.writeFileSync(
      `${OUT}/e2e_p18d_reportes_i18n_ux.json`,
      JSON.stringify(
        {
          proceso: 'P18D UAT S1 — reportes / i18n / UX',
          fecha: new Date().toISOString(),
          escenario: { prefijo: PREFIJO, lotId: esc?.lotId, codigo: esc?.codigo, sufijo: sufijo() },
          eventoCorregidoId,
          eventoEnRevisionId,
          resultados,
          incidencias,
        },
        null,
        2,
      ),
    );
  });

  test('P4a — /reports: select de lote real y KPIs del lote elegido', async ({ page }) => {
    await entrar(page, 'admin');
    const reqs: string[] = [];
    page.on('request', (r) => { if (r.url().includes('/reports')) reqs.push(r.url()); });
    await page.goto('/reports');
    await expect(page.locator('text=No se pudieron cargar los datos')).toHaveCount(0);
    const sel = page.locator('select[data-filtro="lote"]');
    await expect(sel).toBeVisible();
    const opcion = sel.locator('option').filter({ hasText: esc.codigo });
    const nOpciones = await opcion.count();
    if (nOpciones < 1) throw new Error(`el select de lote no contiene la opción ${esc.codigo}`);
    await sel.selectOption(String(esc.lotId));
    await page.waitForTimeout(1500);
    const kpis = reqs.some((u) => u.includes('/reports/kpis') && u.includes(`lot_id=${esc.lotId}`));
    const weekly = reqs.some((u) => u.includes(`/reports/lot/${esc.lotId}/weekly`));
    const ajeno = reqs.some((u) => u.includes('lot_id=2')) && esc.lotId !== 2;
    anotar('P4a', kpis && weekly && !ajeno, `kpis=${kpis} weekly=${weekly} lot_id=2=${ajeno} opciones=${nOpciones}`);
    expect(kpis, 'petición a /reports/kpis con el lote del escenario').toBe(true);
    expect(weekly, 'petición a /reports/lot/<id>/weekly').toBe(true);
    expect(ajeno, 'no debe consultar lot_id=2').toBe(false);
  });

  test('P4b — entradas de menú Producción y Mortalidad llevan a /reports sin error', async ({ page }) => {
    await entrar(page, 'admin');
    const detalle: string[] = [];
    const irA = async (etiqueta: string, patron: RegExp) => {
      await page.goto('/reports');
      const hub = page.getByRole('link', { name: 'Reportes' }).first();
      if (await hub.count()) await hub.click();
      else await page.goto('/menu/reports');
      await page.waitForURL(/\/menu\/reports/, { timeout: 10000 }).catch(() => {});
      const entrada = page.getByText(patron).first();
      await expect(entrada, `entrada de menú «${etiqueta}» en el hub de Reportes`).toBeVisible({ timeout: 15000 });
      await entrada.click();
      await page.waitForURL(/\/reports/, { timeout: 10000 });
      await page.waitForTimeout(800);
      const error = await page.locator('text=No se pudieron cargar los datos').count();
      detalle.push(`${etiqueta}->${new URL(page.url()).pathname} error=${error}`);
      expect(error, `«${etiqueta}» no debe mostrar estado de error`).toBe(0);
    };
    await irA('Producción', /Producci.n/);
    await irA('Mortalidad', /Mortalidad/);
    anotar('P4b', true, detalle.join(' | '));
  });

  test('P4c — desde el lote, enlace al reporte y «Volver» regresa al lote', async ({ page }) => {
    await entrar(page, 'admin');
    await page.goto(`/lots/${esc.lotId}`);
    const enlace = page.locator(`a[href="/reports/lot/${esc.lotId}"]`).first();
    await expect(enlace).toBeVisible({ timeout: 15000 });
    await enlace.click();
    await expect(page).toHaveURL(new RegExp(`/reports/lot/${esc.lotId}$`), { timeout: 15000 });
    const volver = page.locator('[data-testid="back-navigation"]').first();
    await expect(volver).toBeVisible({ timeout: 10000 });
    await volver.click();
    await expect(page).toHaveURL(new RegExp(`/lots/${esc.lotId}$`), { timeout: 15000 });
    anotar('P4c', true, `enlace -> /reports/lot/${esc.lotId} y «Volver» -> /lots/${esc.lotId}`);
  });

  test('P4d — /reports/lot/<id> muestra datos traducidos sin claves crudas', async ({ page }) => {
    await entrar(page, 'admin');
    await page.goto(`/reports/lot/${esc.lotId}`);
    await expect(page.getByRole('heading', { level: 1 }).filter({ hasText: esc.codigo })).toBeVisible({ timeout: 15000 });
    const cuerpo = await page.locator('body').innerText();
    const esperado: Record<string, string> = {
      activo: 'Activo',
      codigo: esc.codigo,
      tipo: (traducciones?.birdTypes?.breeder as string) ?? 'Reproductoras',
      granja: (loteInfo?.farm_name as string) ?? '',
      galpon: (loteInfo?.house_name as string) ?? '',
    };
    const tipos = Object.keys(reporteLote?.event_summary?.by_type ?? {});
    const tipoEsperado = (k: string) => (traducciones?.eventsShort?.[k] as string) ?? k;
    const faltan = Object.entries(esperado).filter(([, v]) => v && !cuerpo.includes(v)).map(([k, v]) => `${k}«${v}»`);
    const faltanTipos = tipos.filter((k) => !cuerpo.includes(tipoEsperado(k)));
    if (tipos.length === 0) incidencias.push('P4d: el reporte del lote no devolvió event_summary.by_type');
    const crudas = [...tipos.filter((k) => cuerpo.includes(k)), /\b(in_review|active)\b/.test(cuerpo) ? 'estadoEnIngles' : ''].filter(Boolean);
    anotar('P4d', faltan.length === 0 && faltanTipos.length === 0 && crudas.length === 0,
      `tipos=[${tipos.join(',')}] faltan=[${[...faltan, ...faltanTipos.map((k) => `evento«${tipoEsperado(k)}»`)].join(', ')}] crudas=[${crudas.join(',')}]`);
    expect(faltan, 'textos traducidos visibles').toEqual([]);
    expect(faltanTipos, 'tipos de evento traducidos').toEqual([]);
    expect(crudas, 'sin claves crudas de evento ni estados en inglés').toEqual([]);
  });

  test('P4e — exportación Excel y PDF del reporte de lote', async ({ page }) => {
    await entrar(page, 'admin');
    await page.goto(`/reports/lot/${esc.lotId}`);
    await expect(page.getByRole('heading', { level: 1 }).filter({ hasText: esc.codigo })).toBeVisible({ timeout: 15000 });
    const detalles: string[] = [];
    const comprobar = async (boton: RegExp, ext: string) => {
      const [download] = await Promise.all([
        page.waitForEvent('download', { timeout: 20000 }),
        page.getByRole('button', { name: boton }).first().click(),
      ]);
      const nombre = download.suggestedFilename();
      const ruta = await download.path();
      const tam = ruta ? fs.statSync(ruta).size : 0;
      detalles.push(`${nombre} (${tam} bytes)`);
      expect(nombre.toLowerCase().endsWith(ext), `nombre ${ext}`).toBe(true);
      expect(tam, `tamaño de ${nombre}`).toBeGreaterThan(0);
    };
    await comprobar(/^Excel$/, '.xlsx');
    await comprobar(/^PDF$/, '.pdf');
    await page.screenshot({ path: `${SHOTS}/p18d_reporte_lote.png`, fullPage: true });
    expect(fs.existsSync(`${SHOTS}/p18d_reporte_lote.png`), 'captura guardada').toBe(true);
    anotar('P4e', true, detalles.join(' | '));
  });

  test('P5a — historial de acciones traducido en /review/<id>', async ({ page }) => {
    await entrar(page, 'admin');
    await page.goto(`/review/${eventoEnRevisionId}`);
    await page.waitForLoadState('networkidle').catch(() => {});
    await expect(page.getByText('Historial de Acciones').first()).toBeVisible({ timeout: 15000 });
    const cuerpo = await page.locator('body').innerText();
    const iniciada = cuerpo.includes('Revisión iniciada');
    const cruda = cuerpo.includes('started_review');
    const estadoCrudo = /\bin_review\b/.test(cuerpo);
    anotar('P5a', iniciada && !cruda && !estadoCrudo, `iniciada=${iniciada} started_review=${cruda} in_review=${estadoCrudo}`);
    expect(cruda, 'no debe aparecer la clave cruda started_review').toBe(false);
    expect(iniciada, 'debe verse «Revisión iniciada»').toBe(true);
    expect(estadoCrudo, 'el estado no debe mostrarse como in_review').toBe(false);
  });

  test('P5b — filtro de lote en /review valida sin llamar a la API con abc', async ({ page }) => {
    await entrar(page, 'admin');
    const urls: string[] = [];
    page.on('request', (r) => { if (r.url().includes('lot_id=')) urls.push(r.url()); });
    await page.goto('/review');
    const input = page.getByPlaceholder('ID del lote').first();
    await expect(input).toBeVisible({ timeout: 15000 });
    await input.fill('abc');
    await page.waitForTimeout(900);
    const pistas = await page.locator('[data-testid="lot-filter-hint"]').count();
    const llamadaInvalida = urls.some((u) => u.includes('lot_id=abc'));
    const cuerpo = await page.locator('body').innerText();
    const errorVisible = cuerpo.includes('Input should') || cuerpo.includes('Valor no válido');
    anotar('P5b', pistas === 1 && !llamadaInvalida && !errorVisible,
      `pistas=${pistas} llamadaAbc=${llamadaInvalida} errorVisible=${errorVisible}`);
    expect(pistas, 'exactamente una pista de filtro').toBe(1);
    expect(llamadaInvalida, 'no debe llamar con lot_id=abc').toBe(false);
    expect(errorVisible, 'sin toast de validación crudo').toBe(false);
    urls.length = 0;
    await input.fill('');
    await input.fill('12');
    await page.waitForTimeout(1200);
    const valida = urls.some((u) => u.includes('lot_id=12'));
    anotar('P5b.12', valida, `peticiones con lot_id=12: ${valida}`);
    expect(valida, 'debe pedir el listado con lot_id=12').toBe(true);
  });

  test('P5c — el toast se dibuja por encima del overlay del diálogo y el rechazo se completa', async ({ page, request }) => {
    // `F9`: `/approvals` está paginada y en la corrida completa hay muchos eventos
    // corregidos de otros procesos; se filtra por el lote del escenario para que la
    // fila buscada esté en la primera página.
    const filtrarPorLote = async () => {
      const filtro = page.getByPlaceholder('ID del lote').first();
      await expect(filtro).toBeVisible({ timeout: 15000 });
      await filtro.fill(String(esc.lotId));
      await page.waitForTimeout(700); // debounce 400 ms + red
    };

    await entrar(page, 'approver');
    await page.goto('/approvals');
    await filtrarPorLote();
    let fila = page.getByRole('row').filter({ hasText: `#${eventoCorregidoId}` });
    let visible = await fila.first().isVisible().catch(() => false);
    if (!visible) {
      await entrar(page, 'admin');
      await page.goto('/approvals');
      await filtrarPorLote();
      fila = page.getByRole('row').filter({ hasText: `#${eventoCorregidoId}` });
      visible = await fila.first().isVisible().catch(() => false);
      incidencias.push('P5c: el aprobador sembrado no veía el panel; se usó admin');
    }
    expect(visible, `evento #${eventoCorregidoId} visible en /approvals`).toBe(true);
    await fila.first().getByRole('button', { name: /^Rechazar$/ }).click();

    // `F8`: el diálogo de rechazo debe traer el campo de motivo. Sin él los handlers caían
    // siempre en «al menos 10 caracteres» y el usuario no podía rechazar nunca.
    const dialogo = page.getByRole('dialog').first();
    await expect(dialogo).toBeVisible({ timeout: 10000 });
    const motivo = dialogo.locator('[data-testid="reject-reason"]');
    await expect(motivo).toBeVisible({ timeout: 5000 });

    // (i) Motivo demasiado corto ⇒ aviso visible, y el toast NO queda bajo el overlay.
    await motivo.fill('corto');
    await dialogo.getByRole('button', { name: /^Rechazar$/ }).click();
    const contenedor = page.locator('[data-testid="toast-container"]').first();
    await expect(contenedor).toBeVisible({ timeout: 10000 });
    await expect(
      page.getByText('El motivo debe tener al menos 10 caracteres').first(),
      'el motivo corto debe avisarse en el toast',
    ).toBeVisible({ timeout: 10000 });
    // El hit-test se hace con el toast ya asentado: `animate-slide-in` lo dibuja entrando
    // desde fuera del viewport (0,25 s), y medir a mitad de animación da un punto fuera de
    // pantalla donde `elementFromPoint` no devuelve nada útil.
    await page.waitForTimeout(400);
    const info = await page.evaluate(() => {
      const cont = document.querySelector('[data-testid="toast-container"]') as HTMLElement | null;
      if (!cont) return { z: null as string | null, sobre: false, texto: '', hit: 'sin-contenedor', punto: '' };
      const z = getComputedStyle(cont).zIndex;
      const hijo = (cont.firstElementChild as HTMLElement | null) ?? cont;
      const r = hijo.getBoundingClientRect();
      const x = r.x + r.width / 2;
      const y = r.y + r.height / 2;
      const hit = document.elementFromPoint(x, y) as HTMLElement | null;
      return {
        z,
        sobre: !!(hit && cont.contains(hit)),
        texto: (cont.innerText || '').slice(0, 120),
        hit: hit ? `${hit.tagName}.${String(hit.className).slice(0, 90)}` : 'null',
        punto: `${Math.round(x)},${Math.round(y)} de ${window.innerWidth}x${window.innerHeight}`,
      };
    });
    anotar('P5c', info.z === '70' && info.sobre,
      `zIndex=${info.z} sobreOverlay=${info.sobre} toast=${info.texto} hit=${info.hit} punto=${info.punto}`);
    expect(info.z, 'zIndex del contenedor de toasts').toBe('70');
    expect(info.sobre, `el centro del primer toast no debe caer en el overlay (hit=${info.hit} en ${info.punto})`).toBe(true);

    // (ii) Motivo válido ⇒ el rechazo se completa y el estado queda en `rejected`.
    await expect(dialogo).toBeVisible({ timeout: 5000 });
    await motivo.fill('Rechazo UAT: datos inconsistentes');
    await dialogo.getByRole('button', { name: /^Rechazar$/ }).click();
    const admin = await cabeceraAdmin(request);
    await expect.poll(async () => {
      const r = await request.get(`${API}/operations/${eventoCorregidoId}`, { headers: admin });
      return r.ok() ? (await r.json()).status : `HTTP ${r.status()}`;
    }, { timeout: 15000, message: 'el evento rechazado debe quedar en estado rejected' }).toBe('rejected');
    anotar('P5c.rechazo', true, `evento #${eventoCorregidoId} rechazado con motivo válido`);
  });

});
