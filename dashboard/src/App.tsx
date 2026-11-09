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

const coverageOrder = ['regression_tested', 'partial', 'not_assessed'] as const

function coverageCounts() {
  const counts: Record<string, number> = {}
  for (const mapping of owaspMapping.mappings) {
    counts[mapping.coverage] = (counts[mapping.coverage] ?? 0) + 1
  }
  return counts
}

function severityCounts() {
  const counts: Record<AlertSeverity, number> = { Critical: 0, High: 0, Medium: 0, Low: 0 }
  for (const alert of securityAlerts) counts[alert.severity] += 1
  return counts
}

function LogoMark() {
  return (
    <svg className="logo-mark" viewBox="0 0 32 32" aria-hidden="true">
      <path
        d="M16 2 28 6v8c0 7.5-5 13.4-12 16C9 27.4 4 21.5 4 14V6Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.4"
      />
      <circle cx="16" cy="14" r="4.4" fill="currentColor" />
    </svg>
  )
}

function App() {
  const [severityFilter, setSeverityFilter] = useState<'All' | AlertSeverity>('All')
  const [statusFilter, setStatusFilter] = useState<'All' | AlertStatus>('All')
  const filteredAlerts = securityAlerts.filter(
    (alert) =>
      (severityFilter === 'All' || alert.severity === severityFilter) &&
      (statusFilter === 'All' || alert.status === statusFilter),
  )
  const coverage = coverageCounts()
  const totalMappings = owaspMapping.mappings.length
  const severities = severityCounts()
  const maxLatency = Math.max(...healthMetrics.map((metric) => metric.latencyMs))
  const openAlerts = securityAlerts.filter((alert) => alert.status !== 'Resolved').length

  return (
    <div className="shell">
      <aside className="rail">
        <div className="brand">
          <LogoMark />
          <div>
            <p className="brand-name">API-Sentinel</p>
            <p className="brand-sub">Secure API Security Dashboard</p>
          </div>
        </div>

        <nav className="rail-nav" aria-label="Dashboard sections">
          <a href="#overview">Overview</a>
          <a href="#owasp">OWASP Coverage</a>
          <a href="#endpoints">Endpoints</a>
          <a href="#alerts">Alerts</a>
          <a href="#evidence">Evidence</a>
          <a href="#health">Health</a>
        </nav>

        <div className="rail-foot">
          <p className="rail-label">Posture</p>
          <p className="posture">
            <span className="posture-dot" aria-hidden="true" />
            AP-1.0 · monitor_only
          </p>
          <p className="data-source-badge">{DATA_SOURCE_LABEL}</p>
          <p className="rail-note" role="status">
            Source state: {dashboardSource.state}. {dashboardSource.message}
          </p>
        </div>
      </aside>

      <div className="main">
        <div className="boundary" role="status">
          Synthetic fixture data - not live security status
        </div>

        <main className="content">
          <section id="overview" className="block">
            <div className="block-head">
              <h2 className="block-title">Security Overview</h2>
              <p className="block-kicker">
                Fixture snapshot · {securityAlerts.length} alerts · {apiEndpoints.length}{' '}
                endpoints · {healthMetrics.length} services
              </p>
            </div>

            <div className="overview-grid">
              <div className="panel panel-alerts">
                <p className="panel-label">Alerts by severity</p>
                <p className="panel-big">
                  {openAlerts}
                  <span className="panel-big-sub"> open / investigating</span>
                </p>
                <div className="sev-bars">
                  {(Object.keys(severities) as AlertSeverity[]).map((severity) => (
                    <div className="sev-row" key={severity}>
                      <span
                        className={`sev-dot sev-${severity.toLowerCase()}`}
                        aria-hidden="true"
                      />
                      <span className="sev-name">{severity}</span>
                      <span className="sev-track">
                        <span
                          className={`sev-fill sev-${severity.toLowerCase()}`}
                          style={{
                            width: `${Math.max(
                              8,
                              (severities[severity] / Math.max(1, securityAlerts.length)) * 100,
                            )}%`,
                          }}
                        />
                      </span>
                      <span className="sev-count">{severities[severity]}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="panel panel-coverage">
                <p className="panel-label">OWASP coverage</p>
                <p className="panel-big">
                  {coverage['regression_tested'] ?? 0}
                  <span className="panel-big-sub"> of {totalMappings} regression tested</span>
                </p>
                <div className="coverage-bar" role="img" aria-label="Coverage breakdown">
                  {coverageOrder.map((key) => (
                    <span
                      key={key}
                      className={`coverage-seg seg-${key}`}
                      style={{ width: `${((coverage[key] ?? 0) / totalMappings) * 100}%` }}
                    />
                  ))}
                </div>
                <ul className="coverage-legend">
                  {coverageOrder.map((key) => (
                    <li key={key}>
                      <span className={`legend-swatch seg-${key}`} aria-hidden="true" />
                      {key.replaceAll('_', ' ')} — {coverage[key] ?? 0}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="panel panel-live">
                <p className="panel-label">Live posture — awaiting management API</p>
                <dl className="live-list">
                  {securityMetrics.map((metric) => (
                    <div className="live-row" key={metric.label}>
                      <dt>{metric.label}</dt>
                      <dd>{metric.value}</dd>
                    </div>
                  ))}
                </dl>
                <p className="live-note">
                  These four values are only ever reported by the live source. In fixture mode
                  the dashboard shows the state, never an invented number.
                </p>
              </div>
            </div>
          </section>

          <section id="owasp" className="block">
            <div className="block-head">
              <h2 className="block-title">OWASP API Security Top 10 (2023)</h2>
              <p className="block-kicker">What the lab API demonstrably does about each risk</p>
            </div>
            <div className="owasp-list">
              {owaspMapping.mappings.map((mapping, index) => (
                <article className="owasp-row" key={mapping.id}>
                  <span className="owasp-index">{String(index + 1).padStart(2, '0')}</span>
                  <div className="owasp-main">
                    <h3>
                      <span className="owasp-id">{mapping.id}</span> {mapping.name}
                    </h3>
                    <p>{mapping.example.expected_result}</p>
                  </div>
                  <span className={`coverage coverage-${mapping.coverage}`}>
                    {mapping.coverage.replaceAll('_', ' ')}
                  </span>
                </article>
              ))}
            </div>
            <p className="mapping-disclaimer">{owaspMapping.disclaimer}</p>
          </section>

          <section id="endpoints" className="block">
            <div className="block-head">
              <h2 className="block-title">
                Endpoint Inventory <span className="fixture-label">(Synthetic)</span>
              </h2>
              <p className="block-kicker">Routes under observation in the lab</p>
            </div>
            <div className="table-wrap">
              <table className="table">
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
                      <td className="mono">{endpoint.endpoint}</td>
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
            </div>
            <p className="table-note">
              These fixtures provide no contract classification. The protected inventory contract
              supports documented, method not documented, path not documented, and visibility
              unavailable; deprecated status is not part of that contract. Live values are not
              wired.
            </p>
          </section>

          <section id="alerts" className="block">
            <div className="block-head">
              <h2 className="block-title">
                Alerts &amp; Triage <span className="fixture-label">(Synthetic)</span>
              </h2>
              <p className="block-kicker">Detections waiting on a human decision</p>
            </div>
            <div className="table-wrap">
              <div className="alert-filters">
                <label>
                  Severity
                  <select
                    aria-label="Filter alerts by severity"
                    value={severityFilter}
                    onChange={(event) =>
                      setSeverityFilter(event.target.value as 'All' | AlertSeverity)
                    }
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
                    onChange={(event) =>
                      setStatusFilter(event.target.value as 'All' | AlertStatus)
                    }
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
              <table className="table">
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
                          <span
                            className={`sev-dot sev-${alert.severity.toLowerCase()}`}
                            aria-hidden="true"
                          />
                          {alert.severity}
                        </span>
                      </td>
                      <td>
                        <strong>{alert.title}</strong>
                        <span className="row-id">{alert.id}</span>
                      </td>
                      <td className="mono">{alert.endpoint}</td>
                      <td>{alert.status}</td>
                      <td className="mono">{alert.detectedAt}</td>
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
            </div>
          </section>

          <section id="evidence" className="block">
            <div className="block-head">
              <h2 className="block-title">
                Security Evidence <span className="fixture-label">(Synthetic)</span>
              </h2>
              <p className="block-kicker">Masked records behind the alerts</p>
            </div>
            <div className="table-wrap">
              <table className="table">
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
                          <span
                            className={`sev-dot sev-${evidence.severity.toLowerCase()}`}
                            aria-hidden="true"
                          />
                          {evidence.severity}
                        </span>
                      </td>
                      <td>
                        <strong>{evidence.finding}</strong>
                        <span className="row-id">{evidence.id}</span>
                      </td>
                      <td className="mono">{evidence.endpoint}</td>
                      <td>{evidence.evidenceType}</td>
                      <td className="mono evidence-value">{evidence.maskedEvidence}</td>
                      <td className="mono">{evidence.capturedAt}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section id="health" className="block">
            <div className="block-head">
              <h2 className="block-title">
                Performance &amp; Health <span className="fixture-label">(Synthetic)</span>
              </h2>
              <p className="block-kicker">Component latency, relative to the slowest service</p>
            </div>
            <div className="table-wrap">
              <table className="table">
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
                      <td>
                        <span className="latency">
                          <span className="latency-track">
                            <span
                              className="latency-fill"
                              style={{ width: `${(metric.latencyMs / maxLatency) * 100}%` }}
                            />
                          </span>
                          <span className="mono">{metric.latencyMs} ms</span>
                        </span>
                      </td>
                      <td className="mono">{metric.uptime}</td>
                      <td className="mono">{metric.lastChecked}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </main>
      </div>
    </div>
  )
}

export default App
