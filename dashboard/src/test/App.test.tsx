import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from '../App'

describe('API-Sentinel dashboard', () => {
  it('renders all major security views', () => {
    render(<App />)

    expect(screen.getByText('Security Overview')).toBeInTheDocument()
    expect(screen.getByText('Endpoint Inventory')).toBeInTheDocument()
    expect(screen.getByText('Alerts & Triage')).toBeInTheDocument()
    expect(screen.getByText('Security Evidence')).toBeInTheDocument()
    expect(screen.getByText('Performance & Health')).toBeInTheDocument()
  })
})
