import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getHealth, submitLead } from '../services/api'

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
    expect(globalThis.fetch).toHaveBeenCalledWith('/api/health')
  })

  it('submitLead posts JSON and returns server receipt', async () => {
    mockFetchOnce({ ok: true, json: { ok: true, stored: 'server' } })
    const lead = { name: 'A', email: 'a@b.co', company: '', message: 'hi' }
    const data = await submitLead(lead)
    expect(data.stored).toBe('server')
    const [url, opts] = globalThis.fetch.mock.calls[0]
    expect(url).toBe('/api/leads')
    expect(opts.method).toBe('POST')
    expect(JSON.parse(opts.body)).toMatchObject({ email: 'a@b.co' })
  })

  it('surfaces server detail on error', async () => {
    mockFetchOnce({ ok: false, status: 400, json: { detail: 'Invalid email' } })
    await expect(submitLead({})).rejects.toThrow('Invalid email')
  })
})
