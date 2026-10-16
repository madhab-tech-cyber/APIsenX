export type AlertSeverity = 'Low' | 'Medium' | 'High' | 'Critical'

export type AlertStatus = 'Open' | 'Investigating' | 'Resolved'

export type SecurityAlert = {
  id: string
  severity: AlertSeverity
  title: string
  endpoint: string
  status: AlertStatus
  detectedAt: string
}

export const securityAlerts: SecurityAlert[] = [
  {
    id: 'ALT-001',
    severity: 'Critical',
    title: 'Repeated unauthorized access attempts',
    endpoint: '/api/admin',
    status: 'Open',
    detectedAt: '2026-10-16 09:42',
  },
  {
    id: 'ALT-002',
    severity: 'High',
    title: 'Suspicious request pattern detected',
    endpoint: '/api/users',
    status: 'Investigating',
    detectedAt: '2026-10-16 09:35',
  },
  {
    id: 'ALT-003',
    severity: 'Medium',
    title: 'Multiple failed authentication attempts',
    endpoint: '/api/login',
    status: 'Open',
    detectedAt: '2026-10-16 09:21',
  },
]
