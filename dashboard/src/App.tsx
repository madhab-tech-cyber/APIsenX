import './App.css'
import { securityMetrics } from './securityData'

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

        <h2 className="section-title">Security Views</h2>

        <section className="views">
          <article className="view-card">
            <h3>Endpoint Inventory</h3>
            <p>Review protected and observed API endpoints.</p>
          </article>

          <article className="view-card">
            <h3>Alerts &amp; Triage</h3>
            <p>Review security alerts and investigation status.</p>
          </article>

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
