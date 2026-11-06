export type SecurityMetric = {
  label: string
  value: number | string
}

export const securityMetrics: SecurityMetric[] = [
  { label: 'Protected Endpoints', value: 'Unavailable' },
  { label: 'Open Alerts', value: 'Unavailable' },
  { label: 'Critical Findings', value: 'Unavailable' },
  { label: 'System Health', value: 'Unmeasured' },
]
