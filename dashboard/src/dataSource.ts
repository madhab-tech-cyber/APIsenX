// Data-source seam for the dashboard.
//
// "fixture" (the default) renders the bundled synthetic data modules
// (securityData, endpointData, alertData, evidenceData, healthData).
// "live" is reserved for the analytics management API: it is NOT wired yet,
// and the label says so — fixture data must never be mistaken for live
// telemetry in a demo or a review.
export type DataSource = 'fixture' | 'live'

const requested = import.meta.env.VITE_DATA_SOURCE as string | undefined

export const DATA_SOURCE: DataSource = requested === 'live' ? 'live' : 'fixture'

export const DATA_SOURCE_LABEL =
  DATA_SOURCE === 'live'
    ? 'Data source: LIVE (not yet wired — showing fixtures)'
    : 'Data source: FIXTURE (synthetic demo data)'
