import { describe, expect, it } from 'vitest'
import { friendlyError } from './friendlyError.js'

describe('friendlyError', () => {
  it('maps no-roof to guidance', () => {
    const e = friendlyError(new Error('SAM 3.1 returned no usable roof boxes'))
    expect(e.title).toContain('No roof')
    expect(e.hint.length).toBeGreaterThan(10)
  })

  it('maps battery validation', () => {
    expect(friendlyError('offgrid systems need battery_kwh > 0').title).toContain('Battery')
  })

  it('maps unknown region', () => {
    expect(friendlyError("unknown region: 'atlantis'").title).toContain('region')
  })

  it('falls back for unknown errors', () => {
    const e = friendlyError('something odd')
    expect(e.title).toContain('Something')
    expect(e.raw).toBe('something odd')
  })
})
