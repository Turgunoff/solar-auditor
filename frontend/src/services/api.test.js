import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getHealth, refineLayout, submitLead } from '../services/api'

function mockFetchOnce({ ok, status = 200, json = {}, statusText = '' }) {
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok,
    status,
    statusText,
    json: async () => json,
  })
}

beforeEach(() => {
  vi.unstubAllGlobals()
})

describe('api service', () => {
  it('getHealth returns parsed body', async () => {
    mockFetchOnce({ ok: true, json: { status: 'ok' } })
    const data = await getHealth()
    expect(data.status).toBe('ok')
    expect(globalThis.fetch).toHaveBeenCalledWith('/api/v1/health')
  })

  it('submitLead posts JSON and returns server receipt', async () => {
    mockFetchOnce({ ok: true, json: { ok: true, stored: 'server' } })
    const lead = { name: 'A', email: 'a@b.co', company: '', message: 'hi' }
    const data = await submitLead(lead)
    expect(data.stored).toBe('server')
    const [url, opts] = globalThis.fetch.mock.calls[0]
    expect(url).toBe('/api/v1/leads')
    expect(opts.method).toBe('POST')
    expect(JSON.parse(opts.body)).toMatchObject({ email: 'a@b.co' })
  })

  it('surfaces server detail on error', async () => {
    mockFetchOnce({ ok: false, status: 400, json: { detail: 'Invalid email' } })
    await expect(submitLead({})).rejects.toThrow('Invalid email')
  })

  it('refineLayout posts polygons to the refine endpoint', async () => {
    mockFetchOnce({ ok: true, json: { layout: { total_panels: 5 }, analytics: {} } })
    const payload = {
      roof_polygons: [],
      obstacles: [],
      user_boxes: [[ [0, 0], [10, 0], [10, 10], [0, 10] ]],
      width_px: 100,
      height_px: 100,
      meters_per_pixel: 0.05,
    }
    const data = await refineLayout(payload)
    expect(data.layout.total_panels).toBe(5)
    const [url, opts] = globalThis.fetch.mock.calls[0]
    expect(url).toBe('/api/v1/process/refine')
    expect(JSON.parse(opts.body).user_boxes).toHaveLength(1)
  })
})
