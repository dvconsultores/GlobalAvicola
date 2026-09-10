/**
 * GA-FE-02 · Paridad i18n ES/EN de las claves nuevas (AC-UI-08/09).
 * El contrato del repo exige el mismo juego de claves en ambos idiomas.
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

function load(lang: string): any {
  return JSON.parse(readFileSync(resolve(process.cwd(), `public/locales/${lang}/translation.json`), 'utf-8'))
}

const REQUIRED_KEYS = [
  'nav.unitAccess',
  'businessUnits.grandparent',
  'businessUnits.breeder',
  'businessUnits.hatchery',
  'businessUnits.broiler',
  'admin.context.company',
  'admin.context.none',
  'admin.context.noneHint',
  'admin.units.heading',
  'admin.units.state.enabled',
  'admin.units.state.disabled',
  'admin.units.enable',
  'admin.units.disable',
  'admin.units.disableConfirmTitle',
  'admin.units.disableConfirmMessage',
  'admin.units.enableConfirmTitle',
  'admin.units.enableConfirmMessage',
  'admin.units.enabledSuccess',
  'admin.units.disabledSuccess',
  'admin.units.saveError',
  'admin.units.loadError',
  'admin.grants.heading',
  'admin.grants.unitLabel',
  'admin.grants.unitDisabledNotice',
  'admin.grants.empty',
  'admin.grants.loadError',
  'admin.grants.state.effective',
  'admin.grants.state.granted',
  'admin.grants.state.notGranted',
  'admin.grants.grant',
  'admin.grants.revoke',
  'admin.grants.revokeConfirmTitle',
  'admin.grants.revokeConfirmMessage',
  'admin.grants.grantedSuccess',
  'admin.grants.revokedSuccess',
  'admin.grants.saveError',
  'admin.forbidden',
  'users.businessUnits.open',
  'users.businessUnits.title',
  'users.businessUnits.companyState',
  'users.businessUnits.userState',
  'users.businessUnits.loadError',
  'users.businessUnits.selfNote',
  'users.businessUnits.revokedHistoric',
]

function getPath(obj: any, path: string): unknown {
  return path.split('.').reduce((acc: any, k) => (acc == null ? acc : acc[k]), obj)
}

describe('GA-FE-02 · i18n', () => {
  const es = load('es')
  const en = load('en')

  it.each(REQUIRED_KEYS)('la clave %s existe en ES y EN', (key) => {
    expect(getPath(es, key), `ES: ${key}`).toBeTruthy()
    expect(getPath(en, key), `EN: ${key}`).toBeTruthy()
  })
})
