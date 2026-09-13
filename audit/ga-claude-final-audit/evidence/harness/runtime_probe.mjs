import fs from 'node:fs'
const BASE = 'https://avicola.globaldv.net', API = BASE + '/api/v1'
const cred = fs.readFileSync(process.env.HOME + '/ga_uat09_credentials.txt', 'utf8')
const OP = /Operador de abuelas:\s*(\S+)/.exec(cred)?.[1], AP = /Aprobador:\s*(\S+)/.exec(cred)?.[1], PW = /Contraseña \(ambos\):\s*(\S+)/.exec(cred)?.[1]
async function login(u) { const r = await fetch(API + '/login', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ username: u, password: PW }) }); const d = await r.json(); return d.access_token }
async function api(m, p, t, b) { const r = await fetch(API + p, { method: m, headers: { authorization: 'Bearer ' + t, 'content-type': 'application/json' }, body: b ? JSON.stringify(b) : undefined }); let d = null; try { d = await r.json() } catch { }; return { status: r.status, data: d } }
const tOp = await login(OP), tAp = await login(AP)
const out = {}
out.approve127 = await api('POST', '/approvals/approve', tAp, { event_id: 127 })
for (const id of [124, 125, 126, 127, 128, 129]) { const r = await api('GET', `/operations/${id}`, tOp); out['ev' + id] = { status: r.status, st: r.data?.status, type: r.data?.event_type, lot: r.data?.lot_id, house: r.data?.house_id, farm: r.data?.farm_id, approved_by: r.data?.approved_by_id, reviewed_by: r.data?.reviewed_by_id, created_by: r.data?.created_by_id } }
out.lot66 = (await api('GET', '/lots/66', tOp)).data
out.pendingInReview = await api('GET', '/review/pending?status=in_review&limit=50', tAp)
out.approvalsPending = await api('GET', '/approvals/pending?limit=50', tAp)
out.meAp = (await api('GET', '/me', tAp)).data
console.log(JSON.stringify(out, null, 1).slice(0, 6000))
