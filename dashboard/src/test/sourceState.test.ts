import { describe, expect, it } from 'vitest'
import type { DashboardSource, DashboardSourceState } from '../sourceState'

describe('Dashboard source state model', () => {
  it('accepts all supported source states', () => {
    const states: DashboardSourceState[] = [
      'loading',
      'empty',
      'error',
      'degraded',
      'unavailable',
      'ready',
    ]

    expect(states).toHaveLength(6)
  })

  it('represents an explicit source message', () => {
    const source: DashboardSource = {
      state: 'unavailable',
      message: 'Management API unavailable',
    }

    expect(source.state).toBe('unavailable')
    expect(source.message).toBe('Management API unavailable')
  })
})
