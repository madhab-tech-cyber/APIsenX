import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from '../App'
import owaspMapping from '../../../docs/owasp-api-security-mapping.json'
import { securityEvidence } from '../evidenceData'

describe('API-Sentinel dashboard', () => {
  it('renders all major security views', () => {
    render(<App />)

    expect(screen.getByRole('heading', { level: 2, name: 'Security overview' })).toBeInTheDocument()
    expect(screen.getByText('Endpoint Inventory')).toBeInTheDocument()
    expect(screen.getByText('Alerts & Triage')).toBeInTheDocument()
    expect(screen.getByText('Security Evidence')).toBeInTheDocument()
    expect(screen.getByText('Performance & Health')).toBeInTheDocument()
    expect(screen.getByRole('table', { name: 'Synthetic endpoint inventory examples' })).toBeInTheDocument()
    expect(screen.getByRole('table', { name: 'Security alerts and triage status' })).toBeInTheDocument()
    expect(screen.getByRole('table', { name: 'Masked synthetic security evidence' })).toBeInTheDocument()
    expect(screen.getByRole('table', { name: 'Synthetic component performance and health' })).toBeInTheDocument()
    expect(screen.getByText('OWASP API Security Top 10 (2023)')).toBeInTheDocument()
    expect(screen.getAllByText('Unavailable in fixture')).toHaveLength(3)
    expect(screen.getByText(/deprecated status is not part of that contract/i)).toBeInTheDocument()
    for (const mapping of owaspMapping.mappings) {
      expect(screen.getByText(mapping.id)).toBeInTheDocument()
      expect(screen.getByText(mapping.name)).toBeInTheDocument()
      expect(screen.getByText(mapping.example.expected_result)).toBeInTheDocument()
      expect(
        screen.getAllByText(mapping.coverage.replaceAll('_', ' ')).length,
      ).toBeGreaterThan(0)
    }
    expect(screen.getByText(owaspMapping.disclaimer)).toBeInTheDocument()
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

  it('renders only the supplied masked evidence fixture values', () => {
    render(<App />)

    for (const evidence of securityEvidence) {
      expect(screen.getAllByText(evidence.maskedEvidence).length).toBeGreaterThan(0)
    }
    expect(document.body.textContent).not.toMatch(/Bearer\s+[A-Za-z0-9._-]{12,}/i)
    expect(document.body.textContent).not.toMatch(/[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/)
  })

  it('filters synthetic alerts by severity and triage status', () => {
    render(<App />)

    fireEvent.change(screen.getByLabelText('Filter alerts by severity'), {
      target: { value: 'Critical' },
    })
    expect(screen.getByText('ALT-001')).toBeInTheDocument()
    expect(screen.queryByText('ALT-002')).not.toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Filter alerts by triage status'), {
      target: { value: 'Resolved' },
    })
    expect(screen.getByText('No synthetic alerts match these filters.')).toBeInTheDocument()
    expect(screen.getByText('0 synthetic alerts shown')).toBeInTheDocument()
  })
})
