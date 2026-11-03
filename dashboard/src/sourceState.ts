export type DashboardSourceState =
  | 'loading'
  | 'empty'
  | 'error'
  | 'degraded'
  | 'unavailable'
  | 'ready'

export type DashboardSource = {
  state: DashboardSourceState
  message: string
}
