import './App.css'
import { useState } from 'react'
import { DATA_SOURCE_LABEL } from './dataSource'
import { securityMetrics } from './securityData'
import { apiEndpoints } from './endpointData'
import { securityAlerts } from './alertData'
import type { AlertSeverity, AlertStatus } from './alertData'
import { securityEvidence } from './evidenceData'
import { healthMetrics } from './healthData'
import type { DashboardSource } from './sourceState'
import owaspMapping from '../../docs/owasp-api-security-mapping.json'

const dashboardSource: DashboardSource = {
  state: 'unavailable',
  message: 'Management API unavailable; dashboard is showing synthetic fixture data.',
}

function App() {
  const [severityFilter, setSeverityFilter] = useState<'All' | AlertSeverity>('All')
  const [statusFilter, setStatusFilter] = useState<'All' | AlertStatus>('All')
  const filteredAlerts = securityAlerts.filter(
    (alert) =>
      (severityFilter === 'All' || alert.severity === severityFilter) &&
      (statusFilter === 'All' || alert.status === statusFilter),
  )

  return (
    <div className="dashboard">
      <header className="topbar">
        <h1>API-Sentinel</h1>
        <p>Secure API Security Dashboard</p>
        <p className="data-source-badge">{DATA_SOURCE_LABEL}</p>
      </header>

      <div className="data-boundary" role="status">
        Synthetic fixture data - not live security status
      </div>

      <div className="data-boundary" role="status">
        Source state: {dashboardSource.state}. {dashboardSource.message}
      </div>

      <main className="content">
        <h2 className="section-title">Security Overview</h2>

        <section className="metrics">
          {securityMetrics.map((metric) => (
            <article className="metric-card" key={metric.label}>
              <p className="metric-label">{metric.label}</p>
              <div
                className={`metric-value${metric.label === 'System Health' ? ' metric-status' : ''}`}
              >
                {metric.value}
              </div>
            </article>
          ))}
        </section>

        <h2 className="section-title">OWASP API Security Top 10 (2023)</h2>
        <section className="owasp-grid" aria-label="OWASP API Security Top 10 coverage">
          {owaspMapping.mappings.map((mapping) => (
            <article className="owasp-card" key={mapping.id}>
              <div className="owasp-heading">
                <span className="owasp-id">{mapping.id}</span>
                <span className={`coverage coverage-${mapping.coverage}`}>
                  {mapping.coverage.replaceAll('_', ' ')}
                </span>
              </div>
              <h3>{mapping.name}</h3>
              <p>{mapping.example.expected_result}</p>
            </article>
          ))}
        </section>
        <p className="mapping-disclaimer">{owaspMapping.disclaimer}</p>

        <h2 className="section-title">
          Endpoint Inventory <span className="fixture-label">(Synthetic)</span>
        </h2>

        <section className="endpoint-table-card">
          <table className="endpoint-table">
            <caption>Synthetic endpoint inventory examples</caption>
            <thead>
              <tr>
                <th>Method</th>
                <th>Endpoint</th>
                <th>Authentication</th>
                <th>Status</th>
                <th>Contract classification</th>
                <th>Risk</th>
              </tr>
            </thead>
            <tbody>
              {apiEndpoints.map((endpoint) => (
                <tr key={`${endpoint.method}-${endpoint.endpoint}`}>
                  <td>
                    <span className={`method method-${endpoint.method.toLowerCase()}`}>
                      {endpoint.method}
                    </span>
                  </td>
                  <td className="endpoint-name">{endpoint.endpoint}</td>
                  <td>{endpoint.authRequired ? 'Required' : 'Public'}</td>
                  <td>{endpoint.status}</td>
                  <td>{endpoint.classification ?? 'Unavailable in fixture'}</td>
                  <td>
                    <span className={`risk risk-${endpoint.risk.toLowerCase()}`}>
                      {endpoint.risk}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
        <p className="inventory-note">
          These fixtures provide no contract classification. The protected inventory contract
          supports documented, method not documented, path not documented, and visibility
          unavailable; deprecated status is not part of that contract. Live values are not wired.
        </p>

        <h2 className="section-title">
          Alerts &amp; Triage <span className="fixture-label">(Synthetic)</span>
        </h2>

        <section className="alerts-table-card">
          <div className="alert-filters">
            <label>
              Severity
              <select
                aria-label="Filter alerts by severity"
                value={severityFilter}
                onChange={(event) => setSeverityFilter(event.target.value as 'All' | AlertSeverity)}
              >
                <option value="All">All severities</option>
                <option value="Critical">Critical</option>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </label>
            <label>
              Triage status
              <select
                aria-label="Filter alerts by triage status"
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value as 'All' | AlertStatus)}
              >
                <option value="All">All statuses</option>
                <option value="Open">Open</option>
                <option value="Investigating">Investigating</option>
                <option value="Resolved">Resolved</option>
              </select>
            </label>
            <p className="alert-result-count" role="status" aria-live="polite">
              {filteredAlerts.length} synthetic alerts shown
            </p>
          </div>
          <table className="alerts-table">
            <caption>Security alerts and triage status</caption>
            <thead>
              <tr>
                <th>Severity</th>
                <th>Alert</th>
                <th>Endpoint</th>
                <th>Status</th>
                <th>Detected</th>
              </tr>
            </thead>
            <tbody>
              {filteredAlerts.map((alert) => (
                <tr key={alert.id}>
                  <td>
                    <span className={`severity severity-${alert.severity.toLowerCase()}`}>
                      {alert.severity}
                    </span>
                  </td>
                  <td>
                    <strong>{alert.title}</strong>
                    <span className="alert-id">{alert.id}</span>
                  </td>
                  <td className="endpoint-name">{alert.endpoint}</td>
                  <td>{alert.status}</td>
                  <td>{alert.detectedAt}</td>
                </tr>
              ))}
              {filteredAlerts.length === 0 && (
                <tr>
                  <td className="empty-state" colSpan={5} role="status">
                    No synthetic alerts match these filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </section>

        <h2 className="section-title">
          Security Evidence <span className="fixture-label">(Synthetic)</span>
        </h2>

        <section className="evidence-table-card">
          <table className="evidence-table">
            <caption>Masked synthetic security evidence</caption>
            <thead>
              <tr>
                <th>Severity</th>
                <th>Finding</th>
                <th>Endpoint</th>
                <th>Evidence Type</th>
                <th>Masked Evidence</th>
                <th>Captured</th>
              </tr>
            </thead>
            <tbody>
              {securityEvidence.map((evidence) => (
                <tr key={evidence.id}>
                  <td>
                    <span className={`severity severity-${evidence.severity.toLowerCase()}`}>
                      {evidence.severity}
                    </span>
                  </td>
                  <td>
                    <strong>{evidence.finding}</strong>
                    <span className="alert-id">{evidence.id}</span>
                  </td>
                  <td className="endpoint-name">{evidence.endpoint}</td>
                  <td>{evidence.evidenceType}</td>
                  <td className="evidence-value">{evidence.maskedEvidence}</td>
                  <td>{evidence.capturedAt}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <h2 className="section-title">
          Performance &amp; Health <span className="fixture-label">(Synthetic)</span>
        </h2>

        <section className="health-table-card">
          <table className="health-table">
            <caption>Synthetic component performance and health</caption>
            <thead>
              <tr>
                <th>Service</th>
                <th>Status</th>
                <th>Latency</th>
                <th>Uptime</th>
                <th>Last Checked</th>
              </tr>
            </thead>
            <tbody>
              {healthMetrics.map((metric) => (
                <tr key={metric.service}>
                  <td>
                    <strong>{metric.service}</strong>
                  </td>
                  <td>
                    <span className={`health-status health-${metric.status.toLowerCase()}`}>
                      {metric.status}
                    </span>
                  </td>
                  <td>{metric.latencyMs} ms</td>
                  <td>{metric.uptime}</td>
                  <td>{metric.lastChecked}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </main>
    </div>
  )
}

export default App
