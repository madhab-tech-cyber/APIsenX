export type EvidenceSeverity = 'Low' | 'Medium' | 'High' | 'Critical'

export type EvidenceType = 'Request Pattern' | 'Authentication Event' | 'Access Control'

export type SecurityEvidence = {
  id: string
  finding: string
  endpoint: string
  evidenceType: EvidenceType
  severity: EvidenceSeverity
  maskedEvidence: string
  capturedAt: string
}

export const securityEvidence: SecurityEvidence[] = [
  {
    id: 'EVD-001',
    finding: 'Repeated unauthorized access attempts',
    endpoint: '/api/admin',
    evidenceType: 'Access Control',
    severity: 'Critical',
    maskedEvidence: 'GET /api/admin ? 401 × 12 from [MASKED]',
    capturedAt: '2026-10-16 09:42',
  },
  {
    id: 'EVD-002',
    finding: 'Suspicious request pattern',
    endpoint: '/api/users',
    evidenceType: 'Request Pattern',
    severity: 'High',
    maskedEvidence: 'GET /api/users?id=[MASKED] ? repeated enumeration',
    capturedAt: '2026-10-16 09:35',
  },
  {
    id: 'EVD-003',
    finding: 'Multiple failed authentication attempts',
    endpoint: '/api/login',
    evidenceType: 'Authentication Event',
    severity: 'Medium',
    maskedEvidence: 'POST /api/login ? 401 × 7 from [MASKED]',
    capturedAt: '2026-10-16 09:21',
  },
]
