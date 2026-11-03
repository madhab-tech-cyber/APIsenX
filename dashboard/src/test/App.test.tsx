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

  it('labels the configured data source honestly', () => {
    render(<App />)

    expect(screen.getAllByText('Data source: FIXTURE (synthetic demo data)').length).toBeGreaterThan(0)
  })

  it('clearly identifies unavailable management API and synthetic data', () => {
    render(<App />)

    const statusMessages = screen.getAllByRole('status')

    expect(
      statusMessages.some(
        (element) =>
          element.textContent === 'Synthetic fixture data - not live security status',
      ),
    ).toBe(true)

    expect(
      statusMessages.some(
        (element) =>
          element.textContent ===
          'Source state: unavailable. Management API unavailable; dashboard is showing synthetic fixture data.',
      ),
    ).toBe(true)
  })
})
