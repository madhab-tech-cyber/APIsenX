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
    pub correlation_unsupported: u64,
    pub correlation_ambiguous: u64,
    /// False means no sensor loss counter has been read; zero drops cannot be inferred.
    pub sensor_drop_counter_available: bool,
    pub sensor_drops_reported: u64,
    pub sensor_drop_counter_resets: u64,
    pub batches_enqueued: u64,
    pub batches_delivered: u64,
    pub batches_retry_scheduled: u64,
    pub batches_exhausted: u64,
    pub processing_latency_buckets: [u64; 8],
    pub pending_events: usize,
    pub queued_batches: usize,
}

impl Metrics {
    /// Accept an aggregate monotonic counter from a trusted sensor adapter.
    /// Counter reset/wrap is reported as an uncertainty, never as zero loss.
    pub fn observe_sensor_drop_total(&mut self, previous: Option<u64>, current: u64) {
        self.sensor_drop_counter_available = true;
        if let Some(previous) = previous {
            if current >= previous {
                self.sensor_drops_reported = self
                    .sensor_drops_reported
                    .saturating_add(current - previous);
            } else {
                self.sensor_drop_counter_resets = self.sensor_drop_counter_resets.saturating_add(1);
            }
        } else {
            self.sensor_drops_reported = self.sensor_drops_reported.saturating_add(current);
        }
    }

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

    #[test]
    fn sensor_loss_is_unknown_until_sampled_and_reset_is_visible() {
        let mut metrics = Metrics::default();
        assert!(!metrics.sensor_drop_counter_available);
        metrics.observe_sensor_drop_total(None, 3);
        metrics.observe_sensor_drop_total(Some(3), 5);
        metrics.observe_sensor_drop_total(Some(5), 1);
        assert!(metrics.sensor_drop_counter_available);
        assert_eq!(metrics.sensor_drops_reported, 5);
        assert_eq!(metrics.sensor_drop_counter_resets, 1);
    }
}
