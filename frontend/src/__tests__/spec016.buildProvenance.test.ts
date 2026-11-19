/**
 * SPEC 016 §B — Procedencia exacta del build (frontend/CI).
 *
 * Cubre tres ACs:
 *  - AC-VP-05: contrato sobre los archivos (Dockerfiles con `ARG GIT_SHA` + `LABEL` OCI,
 *    nginx sirviendo `/version.json` sin caché y los cuatro workflows pasando `build-args`).
 *  - AC-VP-03: `vite build` REAL con `GIT_SHA`/`BUILD_TIME` en el entorno ⇒ `dist/version.json`
 *    y el bundle contienen el SHA exacto.
 *  - AC-VP-07: `scripts/verify_runtime_sha.sh` contra un servidor simulado — PASS con SHA
 *    igual, FAIL con `unknown`, FAIL con árboles distintos y PASS tree-equal con commits reales.
 */
import { describe, it, expect } from 'vitest'
import { execFileSync, spawn, spawnSync } from 'node:child_process'
import { createServer } from 'node:http'
import { mkdtempSync, readFileSync, readdirSync, rmSync } from 'node:fs'
import os from 'node:os'
import path from 'node:path'

const FRONTEND_DIR = process.cwd()
const REPO_ROOT = path.resolve(FRONTEND_DIR, '..')
// Se compone por segmentos para no arrastrar rutas absolutas del entorno de ejecución.
const WORKFLOWS_DIR = path.join(REPO_ROOT, '.github', 'workflows')
const VERIFY_SCRIPT = path.join(REPO_ROOT, 'scripts', 'verify_runtime_sha.sh')

const BUILD_SHA = '0123456789abcdef0123456789abcdef01234567'
const BUILD_TIME = '2026-11-18T00:00:00Z'
const ABSENT_SHA = 'ffffffffffffffffffffffffffffffffffffffff'

const WORKFLOWS = [
  'docker-push-backend.yml',
  'docker-push-backend-dev.yml',
  'docker-push-frontend.yml',
  'docker-push-frontend-dev.yml',
]

function readRepoFile(...segments: string[]): string {
  return readFileSync(path.join(REPO_ROOT, ...segments), 'utf8')
}

/** Bloque de un paso de YAML: la clave dada y todas las líneas más indentadas que siguen. */
function yamlBlock(text: string, keyPattern: RegExp): string {
  const lines = text.split('\n')
  const start = lines.findIndex((line) => keyPattern.test(line))
  if (start === -1) return ''
  const indent = lines[start].search(/\S/)
  const block = [lines[start]]
  for (const line of lines.slice(start + 1)) {
    if (line.trim() === '') {
      block.push(line)
      continue
    }
    if (line.search(/\S/) <= indent) break
    block.push(line)
  }
  return block.join('\n')
}

function git(args: string[]): string | undefined {
  const result = spawnSync('git', args, { cwd: REPO_ROOT, encoding: 'utf8' })
  return result.status === 0 ? result.stdout.trim() || undefined : undefined
}

describe('AC-VP-05 · procedencia declarada en las imágenes', () => {
  it('backend/Dockerfile recibe el SHA por build-arg y lo publica como etiqueta OCI', () => {
    const dockerfile = readRepoFile('backend', 'Dockerfile')
    expect(dockerfile).toMatch(/^ARG GIT_SHA=/m)
    expect(dockerfile).toMatch(/^ARG BUILD_TIME=/m)
    expect(dockerfile).toContain('org.opencontainers.image.revision')
    expect(dockerfile).toContain('org.opencontainers.image.created')
  })

  it('frontend/Dockerfile inyecta el SHA antes de `npm run build` y etiqueta la imagen', () => {
    const dockerfile = readRepoFile('frontend', 'Dockerfile')
    expect(dockerfile).toMatch(/^ARG GIT_SHA=/m)
    expect(dockerfile).toMatch(/^ARG BUILD_TIME=/m)
    expect(dockerfile).toContain('org.opencontainers.image.revision')
    expect(dockerfile).toContain('org.opencontainers.image.created')

    // El ARG debe existir ANTES del build: si va después, `dist/version.json` sale `unknown`.
    const argIndex = dockerfile.indexOf('ARG GIT_SHA=')
    const buildIndex = dockerfile.indexOf('RUN npm run build')
    expect(argIndex).toBeGreaterThan(-1)
    expect(buildIndex).toBeGreaterThan(argIndex)
  })

  it('nginx.conf sirve /version.json sin caché y repite el header de tipo de contenido', () => {
    const conf = readRepoFile('frontend', 'nginx.conf')
    const block = yamlBlock(conf, /^\s*location = \/version\.json\s*\{/)

    expect(conf).toMatch(/location = \/version\.json\s*\{/)
    expect(block).toContain('Cache-Control "no-store"')
    // `add_header` en un `location` anula los del `server`: el header debe repetirse aquí.
    expect(block).toContain('X-Content-Type-Options "nosniff"')
    expect(block).toContain('try_files $uri =404')
  })

  describe.each(WORKFLOWS)('workflow %s', (workflowName) => {
    it('pasa GIT_SHA y BUILD_TIME como build-args y guarda github.sha', () => {
      const workflow = readFileSync(path.join(WORKFLOWS_DIR, workflowName), 'utf8')

      const buildArgs = yamlBlock(workflow, /^\s*build-args:/)
      expect(buildArgs).not.toBe('')
      expect(buildArgs).toContain('GIT_SHA=${{ github.sha }}')
      expect(buildArgs).toContain('BUILD_TIME=')

      // Paso que calcula la fecha UTC del build.
      expect(workflow).toContain('Compute build provenance')
      expect(workflow).toMatch(/id:\s*prov/)
      expect(workflow).toContain('steps.prov.outputs.build_time')

      // Paso de guardia: sin `github.sha` el build no se puede certificar.
      expect(workflow).toContain('Guard - build SHA must be present')
      expect(workflow).toContain('github.sha')
    })
  })
})

describe('AC-VP-03 · el build real emite la procedencia', () => {
  it(
    'vite build con GIT_SHA/BUILD_TIME deja version.json y el SHA en el bundle',
    () => {
      const tmpRoot = mkdtempSync(path.join(os.tmpdir(), 'ga-prov-'))
      const outDir = path.join(tmpRoot, 'dist')

      try {
        execFileSync(
          path.join(FRONTEND_DIR, 'node_modules', '.bin', 'vite'),
          ['build', '--outDir', outDir, '--emptyOutDir'],
          {
            cwd: FRONTEND_DIR,
            env: { ...process.env, GIT_SHA: BUILD_SHA, BUILD_TIME: BUILD_TIME },
            encoding: 'utf8',
            stdio: 'pipe',
            timeout: 170_000,
          },
        )

        const versionJson = JSON.parse(readFileSync(path.join(outDir, 'version.json'), 'utf8'))
        expect(versionJson).toEqual({ git_sha: BUILD_SHA, build_time: BUILD_TIME })

        const assetsDir = path.join(outDir, 'assets')
        const jsAssets = readdirSync(assetsDir).filter((file) => file.endsWith('.js'))
        expect(jsAssets.length).toBeGreaterThan(0)

        // `__GA_BUILD_SHA__` se sustituye por `define`: la cadena literal viaja en el bundle.
        const bundleCarriesSha = jsAssets.some((file) =>
          readFileSync(path.join(assetsDir, file), 'utf8').includes(BUILD_SHA),
        )
        expect(bundleCarriesSha).toBe(true)
      } finally {
        rmSync(tmpRoot, { recursive: true, force: true })
      }
    },
    180_000,
  )
})

describe('AC-VP-07 · guardia de paridad scripts/verify_runtime_sha.sh', () => {
  interface VersionServer {
    baseUrl: string
    close: () => Promise<void>
  }

  async function startVersionServer(gitSha: string): Promise<VersionServer> {
    const server = createServer((request, response) => {
      const body =
        request.url === '/api/v1/version'
          ? { git_sha: gitSha, build_time: BUILD_TIME, environment: 'uat' }
          : request.url === '/version.json'
            ? { git_sha: gitSha, build_time: BUILD_TIME }
            : null

      if (body === null) {
        response.writeHead(404, { 'Content-Type': 'application/json' })
        response.end('{"detail":"not found"}')
        return
      }

      response.writeHead(200, { 'Content-Type': 'application/json' })
      response.end(JSON.stringify(body))
    })

    await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve))
    const address = server.address()
    const port = typeof address === 'object' && address !== null ? address.port : 0

    return {
      baseUrl: `http://127.0.0.1:${port}`,
      close: () => new Promise<void>((resolve) => server.close(() => resolve())),
    }
  }

  async function runGuard(gitSha: string, expectedSha: string) {
    const server = await startVersionServer(gitSha)
    try {
      // `spawn` asíncrono (no `spawnSync`): el servidor simulado vive en ESTE proceso y un
      // `spawnSync` bloquearía el bucle de eventos, dejándolo sin responder y al `curl`
      // esperando hasta agotar el tiempo.
      return await new Promise<{ status: number | null; stdout: string; stderr: string }>(
        (resolve, reject) => {
          const child = spawn('bash', [VERIFY_SCRIPT, server.baseUrl, expectedSha], {
            cwd: REPO_ROOT,
          })
          let stdout = ''
          let stderr = ''
          child.stdout.on('data', (chunk) => {
            stdout += String(chunk)
          })
          child.stderr.on('data', (chunk) => {
            stderr += String(chunk)
          })
          child.on('error', reject)
          child.on('close', (status) => resolve({ status, stdout, stderr }))
        },
      )
    } finally {
      await server.close()
    }
  }

  it('SHA igual al esperado ⇒ exit 0 y PASS', async () => {
    const result = await runGuard(BUILD_SHA, BUILD_SHA)
    expect(result.stdout).toContain(`SOURCE_SHA=${BUILD_SHA}`)
    expect(result.stdout).toContain(`BACKEND_RUNTIME_SHA=${BUILD_SHA}`)
    expect(result.stdout).toContain(`FRONTEND_RUNTIME_SHA=${BUILD_SHA}`)
    expect(result.stdout).toContain('DEPLOYMENT_PARITY=PASS')
    expect(result.status).toBe(0)
  })

  it('runtime `unknown` ⇒ exit 2 y FAIL (no se puede certificar)', async () => {
    const result = await runGuard('unknown', BUILD_SHA)
    expect(result.stdout).toContain('BACKEND_RUNTIME_SHA=unknown')
    expect(result.stdout).toContain('DEPLOYMENT_PARITY=FAIL (unknown)')
    expect(result.status).toBe(2)
  })

  it('SHA distinto y árboles distintos (commits inexistentes) ⇒ exit 1 y FAIL', async () => {
    const result = await runGuard(ABSENT_SHA, BUILD_SHA)
    expect(result.stdout).toContain(`BACKEND_RUNTIME_SHA=${ABSENT_SHA}`)
    expect(result.stdout).toContain('DEPLOYMENT_PARITY=FAIL')
    expect(result.stdout).not.toContain('DEPLOYMENT_PARITY=PASS')
    expect(result.status).toBe(1)
  })

  const headSha = git(['rev-parse', 'HEAD'])
  const parentSha = git(['rev-parse', 'HEAD~1'])
  const treesEqual =
    headSha !== undefined &&
    parentSha !== undefined &&
    spawnSync('git', ['diff', '--quiet', 'HEAD~1', 'HEAD', '--', 'backend/', 'frontend/'], {
      cwd: REPO_ROOT,
    }).status === 0

  // El caso tree-equal solo tiene sentido si en ESTE repo el commit siguiente no toca
  // `backend/` ni `frontend/`; si no, se salta declarándolo.
  it.skipIf(!treesEqual)(
    'runtime en un commit anterior con árboles iguales ⇒ exit 0 y PASS (tree-equal)',
    async () => {
      const result = await runGuard(parentSha as string, headSha as string)
      expect(result.stdout).toContain(`SOURCE_SHA=${headSha}`)
      expect(result.stdout).toContain(`BACKEND_RUNTIME_SHA=${parentSha}`)
      expect(result.stdout).toContain('DEPLOYMENT_PARITY=PASS (tree-equal')
      expect(result.status).toBe(0)
    },
  )
})

/**
 * SPEC 017 — contrato de imágenes y convergencia main/develop.
 *
 * Trabaja sobre los archivos como TEXTO (sin dependencia YAML nueva): lo que se
 * certifica es que el repositorio declara un único contrato de tags —`main` →
 * `latest` + `sha-<7>`, `develop` → `dev` + `sha-<7>`— y que el compose de UAT
 * pide exactamente ese tag (`develop` no existe como tag en el registro).
 */
describe('SPEC 017 · contrato de imagenes y convergencia', () => {
  const DEV_WORKFLOWS = ['docker-push-backend-dev.yml', 'docker-push-frontend-dev.yml']
  const MAIN_WORKFLOWS = ['docker-push-backend.yml', 'docker-push-frontend.yml']

  function readWorkflow(workflowName: string): string {
    return readFileSync(path.join(WORKFLOWS_DIR, workflowName), 'utf8')
  }

  /** Disparadores declarados: el bloque `on:` completo, hasta la siguiente clave de primer nivel. */
  function triggerBlock(text: string): string {
    const lines = text.split('\n')
    const start = lines.findIndex((line) => /^on\s*:/.test(line))
    if (start === -1) return ''

    const inline = lines[start].replace(/^on\s*:/, '').trim()
    // `on: [push, workflow_dispatch]` — todo el bloque cabe en la propia línea.
    if (inline !== '') return inline

    const block: string[] = []
    for (const line of lines.slice(start + 1)) {
      if (line.trim() === '') {
        block.push(line)
        continue
      }
      if (line.search(/\S/) === 0) break // siguiente clave de primer nivel (`env:`, `jobs:`…)
      block.push(line)
    }
    return block.join('\n')
  }

  function imageLines(): string[] {
    return readRepoFile('docker-compose.develop.yml')
      .split('\n')
      .filter((line) => /^\s*image:/.test(line))
  }

  describe.each(WORKFLOWS)('AC-C-01 · workflow %s', (workflowName) => {
    it('construye en cada push (sin filtro de rutas) y conserva la procedencia', () => {
      const workflow = readWorkflow(workflowName)
      const onBlock = triggerBlock(workflow)

      // El disparador debe existir y no puede filtrar por rutas: un push sin build deja el
      // SHA de la rama distinto del SHA del runtime.
      expect(onBlock).not.toBe('')
      expect(onBlock).not.toMatch(/^\s*paths(-ignore)?\s*:/m)

      // Manual sigue disponible, pero no sustituye al build por push.
      expect(onBlock).toMatch(/workflow_dispatch/)

      const buildArgs = yamlBlock(workflow, /^\s*build-args:/)
      expect(buildArgs).not.toBe('')
      expect(buildArgs).toContain('GIT_SHA=${{ github.sha }}')

      expect(workflow).toContain('Guard - build SHA must be present')
    })
  })

  describe.each(DEV_WORKFLOWS)('AC-C-02 · workflow %s', (workflowName) => {
    it('publica `dev` + sha y nunca `latest` ni `develop`', () => {
      const workflow = readWorkflow(workflowName)

      expect(workflow).toContain(
        "type=raw,value=dev,enable=${{ github.ref == 'refs/heads/develop' }}",
      )
      expect(workflow).not.toContain('value=latest')
      expect(workflow).not.toContain('value=develop')
    })
  })

  describe.each(MAIN_WORKFLOWS)('AC-C-02 · workflow %s', (workflowName) => {
    it('publica `latest` + sha y nunca `dev` ni `develop`', () => {
      const workflow = readWorkflow(workflowName)

      expect(workflow).toContain('value=latest')
      expect(workflow).not.toContain('value=dev,')
      expect(workflow).not.toContain('value=develop')
    })
  })

  it('AC-C-03 · docker-compose.develop.yml pide `:dev` en las tres imágenes', () => {
    const images = imageLines()

    expect(images).toHaveLength(3)

    // 2 backend (api + telegram-bot que comparte imagen) y 1 frontend.
    const backendImages = images.filter((line) => line.includes('globalavicola-backend:dev'))
    const frontendImages = images.filter((line) => line.includes('globalavicola-frontend:dev'))
    expect(backendImages).toHaveLength(2)
    expect(frontendImages).toHaveLength(1)

    // `develop` no es un tag del registro: pedirlo produce `manifest unknown`.
    for (const line of images) {
      expect(line).not.toContain(':develop')
    }
  })

  it('AC-C-04 · docs/DEPLOYMENT_CONTRACT.md declara el contrato completo', () => {
    const doc = readRepoFile('docs', 'DEPLOYMENT_CONTRACT.md')

    expect(doc).toContain('latest')
    expect(doc).toContain('dev')
    expect(doc).toContain('sha-')
    expect(doc).toContain('verify_runtime_sha.sh')
  })
})
