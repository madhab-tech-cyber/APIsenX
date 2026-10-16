import './App.css'
import { securityMetrics } from './securityData'
import { apiEndpoints } from './endpointData'
import { securityAlerts } from './alertData'

function App() {
  return (
    <div className="dashboard">
      <header className="topbar">
        <h1>API-Sentinel</h1>
        <p>Secure API Security Dashboard</p>
      </header>

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

        <h2 className="section-title">Endpoint Inventory</h2>

        <section className="endpoint-table-card">
          <table className="endpoint-table">
            <thead>
              <tr>
                <th>Method</th>
                <th>Endpoint</th>
                <th>Authentication</th>
                <th>Status</th>
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

        <h2 className="section-title">Alerts &amp; Triage</h2>

        <section className="alerts-table-card">
          <table className="alerts-table">
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
              {securityAlerts.map((alert) => (
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
            </tbody>
          </table>
        </section>

        <h2 className="section-title">Security Views</h2>

        <section className="views">
          <article className="view-card">
            <h3>Security Evidence</h3>
            <p>Inspect masked evidence supporting security findings.</p>
          </article>

          <article className="view-card">
            <h3>Performance &amp; Health</h3>
            <p>Monitor service health and security-related metrics.</p>
          </article>
        </section>
      </main>
    </div>
  )
}

export default App
