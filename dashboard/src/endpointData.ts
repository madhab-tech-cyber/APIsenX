export type EndpointStatus = 'Protected' | 'Monitored'

export type EndpointRisk = 'Low' | 'Medium' | 'High'
export type EndpointClassification =
  | 'documented'
  | 'method_not_documented'
  | 'path_not_documented'
  | 'visibility_unavailable'

export type ApiEndpoint = {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  endpoint: string
  authRequired: boolean
  status: EndpointStatus
  risk: EndpointRisk
  classification: EndpointClassification | null
}

export const apiEndpoints: ApiEndpoint[] = [
  {
    method: 'GET',
    endpoint: '/api/users',
    authRequired: true,
    status: 'Protected',
    risk: 'Low',
    classification: null,
  },
  {
    method: 'POST',
    endpoint: '/api/login',
    authRequired: false,
    status: 'Monitored',
    risk: 'Medium',
    classification: null,
  },
  {
    method: 'GET',
    endpoint: '/api/admin',
    authRequired: true,
    status: 'Protected',
    risk: 'High',
    classification: null,
  },
]
