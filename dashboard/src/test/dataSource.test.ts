import { describe, expect, it } from 'vitest'
import { DATA_SOURCE, DATA_SOURCE_LABEL } from '../dataSource'

describe('data source seam', () => {
  it('defaults to fixture data when VITE_DATA_SOURCE is unset', () => {
    expect(DATA_SOURCE).toBe('fixture')
  })

  it('labels fixture data honestly in the UI', () => {
    expect(DATA_SOURCE_LABEL).toContain('FIXTURE')
  })
})
