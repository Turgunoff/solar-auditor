const BASE = ''

async function parseError(res) {
  try {
    const data = await res.json()
    return data.detail || JSON.stringify(data)
  } catch {
    return res.statusText || 'Request failed'
  }
}

export async function getHealth() {
  const res = await fetch(`${BASE}/api/v1/health`)
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function getStatus(probe = false) {
  const q = probe ? '?probe=true' : ''
  const res = await fetch(`${BASE}/api/v1/status${q}`)
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function getPresets() {
  const res = await fetch(`${BASE}/api/v1/presets`)
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function processPreset(presetId) {
  const res = await fetch(`${BASE}/api/v1/process/preset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ preset_id: presetId }),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function processUpload(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/api/v1/process/upload`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function processMap({ lat, lng, zoom }) {
  // Fetch Static Maps in the browser so HTTP-referrer–restricted keys work.
  const key = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || ''
  if (!key) throw new Error('VITE_GOOGLE_MAPS_API_KEY is empty')

  const staticUrl =
    'https://maps.googleapis.com/maps/api/staticmap' +
    `?center=${encodeURIComponent(`${lat},${lng}`)}` +
    `&zoom=${zoom}` +
    '&size=640x640&scale=2&maptype=satellite' +
    `&key=${encodeURIComponent(key)}`

  const imgRes = await fetch(staticUrl)
  if (!imgRes.ok) {
    const text = await imgRes.text().catch(() => '')
    throw new Error(`Static Maps ${imgRes.status}: ${text.slice(0, 200) || imgRes.statusText}`)
  }
  const blob = await imgRes.blob()
  const form = new FormData()
  form.append('file', new File([blob], 'map-satellite.jpg', { type: blob.type || 'image/jpeg' }))
  form.append('lat', String(lat))
  form.append('lng', String(lng))
  form.append('zoom', String(zoom))

  const res = await fetch(`${BASE}/api/v1/process/map-upload`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export function pdfUrl(projectId) {
  return `${BASE}/api/v1/export-pdf/${projectId}`
}

export function assetUrl(path) {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return path
}

export async function refineLayout(payload) {
  const res = await fetch(`${BASE}/api/v1/process/refine`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function getAssumptionDefaults() {
  const res = await fetch(`${BASE}/api/v1/assumptions/defaults`)
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}

export async function submitLead(lead) {
  const res = await fetch(`${BASE}/api/v1/leads`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(lead),
  })
  if (!res.ok) throw new Error(await parseError(res))
  return res.json()
}
