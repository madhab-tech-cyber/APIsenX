export type SecurityMetric = {
  label: string
  value: number | string
}

export const securityMetrics: SecurityMetric[] = [
  { label: 'Protected Endpoints', value: 0 },
  { label: 'Open Alerts', value: 0 },
  { label: 'Critical Findings', value: 0 },
  { label: 'System Health', value: 'Healthy' },
]
