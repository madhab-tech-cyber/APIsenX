export type EndpointStatus = 'Protected' | 'Monitored'

export type EndpointRisk = 'Low' | 'Medium' | 'High'

export type ApiEndpoint = {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  endpoint: string
  authRequired: boolean
  status: EndpointStatus
  risk: EndpointRisk
}

export const apiEndpoints: ApiEndpoint[] = [
  {
    method: 'GET',
    endpoint: '/api/users',
    authRequired: true,
    status: 'Protected',
    risk: 'Low',
  },
  {
    method: 'POST',
    endpoint: '/api/login',
    authRequired: false,
    status: 'Monitored',
    risk: 'Medium',
  },
  {
    method: 'GET',
    endpoint: '/api/admin',
    authRequired: true,
    status: 'Protected',
    risk: 'High',
  },
]
