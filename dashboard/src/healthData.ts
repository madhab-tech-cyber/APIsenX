export type HealthStatus = 'Healthy' | 'Degraded' | 'Unhealthy'

export type HealthMetric = {
  service: string
  status: HealthStatus
  latencyMs: number
  uptime: string
  lastChecked: string
}

export const healthMetrics: HealthMetric[] = [
  {
    service: 'API Gateway',
    status: 'Healthy',
    latencyMs: 42,
    uptime: '99.98%',
    lastChecked: '2026-10-16 10:58',
  },
  {
    service: 'Threat Detection',
    status: 'Healthy',
    latencyMs: 86,
    uptime: '99.95%',
    lastChecked: '2026-10-16 10:57',
  },
  {
    service: 'Event Collector',
    status: 'Degraded',
    latencyMs: 214,
    uptime: '99.71%',
    lastChecked: '2026-10-16 10:56',
  },
]
