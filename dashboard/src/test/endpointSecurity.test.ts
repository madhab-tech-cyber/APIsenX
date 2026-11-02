import { describe, expect, it } from 'vitest'
import { apiEndpoints } from '../endpointData'

describe('Endpoint security controls', () => {
  it('marks protected endpoints as authentication-required', () => {
    const protectedEndpoints = apiEndpoints.filter(
      (endpoint) => endpoint.status === 'Protected',
    )

    expect(protectedEndpoints.length).toBeGreaterThan(0)
    expect(protectedEndpoints.every((endpoint) => endpoint.authRequired)).toBe(true)
  })

  it('requires authentication for the high-risk admin endpoint', () => {
    const adminEndpoint = apiEndpoints.find(
      (endpoint) => endpoint.endpoint === '/api/admin',
    )

    expect(adminEndpoint).toBeDefined()
    expect(adminEndpoint?.risk).toBe('High')
    expect(adminEndpoint?.authRequired).toBe(true)
  })
})
