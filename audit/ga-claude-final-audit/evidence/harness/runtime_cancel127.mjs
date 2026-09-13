import fs from 'node:fs'
const API = 'https://avicola.globaldv.net/api/v1'
const cred = fs.readFileSync(process.env.HOME + '/ga_uat09_credentials.txt', 'utf8')
const OP = /Operador de abuelas:\s*(\S+)/.exec(cred)?.[1], PW = /Contraseña \(ambos\):\s*(\S+)/.exec(cred)?.[1]
const l = await (await fetch(API + '/login', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ username: OP, password: PW }) })).json()
const r = await fetch(API + '/operations/127/cancel', { method: 'POST', headers: { authorization: 'Bearer ' + l.access_token } })
console.log('cancel 127 ->', r.status, (await r.text()).slice(0, 200))
const g = await (await fetch(API + '/operations/127', { headers: { authorization: 'Bearer ' + l.access_token } })).json(); console.log('estado 127:', g.status)
