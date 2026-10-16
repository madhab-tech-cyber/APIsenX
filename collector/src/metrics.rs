//! Safe aggregate counters. No route, source, subject, flow or credential labels.

use std::time::Duration;

use serde::Serialize;

/// Processing latency buckets: <=1, 5, 10, 50, 100, 500, 1000 us, >1 ms.
pub const LATENCY_BUCKET_US: [u64; 7] = [1, 5, 10, 50, 100, 500, 1000];

#[derive(Clone, Debug, Default, Serialize)]
pub struct Metrics {
    pub records_seen: u64,
    pub records_accepted: u64,
    pub decode_rejected: u64,
    pub queue_rejected: u64,
    pub route_unavailable: u64,
    pub batches_enqueued: u64,
    pub batches_delivered: u64,
    pub batches_retry_scheduled: u64,
    pub batches_exhausted: u64,
    pub processing_latency_buckets: [u64; 8],
    pub pending_events: usize,
    pub queued_batches: usize,
}

impl Metrics {
    pub fn observe_processing(&mut self, duration: Duration) {
        let us = duration.as_micros() as u64;
        let bucket = LATENCY_BUCKET_US
            .iter()
            .position(|limit| us <= *limit)
            .unwrap_or(7);
        self.processing_latency_buckets[bucket] =
            self.processing_latency_buckets[bucket].saturating_add(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn metrics_are_bounded_and_privacy_safe() {
        let mut metrics = Metrics::default();
        metrics.observe_processing(Duration::from_micros(6));
        metrics.observe_processing(Duration::from_millis(2));
        assert_eq!(metrics.processing_latency_buckets[2], 1);
        assert_eq!(metrics.processing_latency_buckets[7], 1);
        let json = serde_json::to_string(&metrics).unwrap();
        assert!(!json.contains("source_id"));
        assert!(!json.contains("route_template"));
    }
}
