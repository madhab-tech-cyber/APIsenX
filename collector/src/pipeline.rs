//! Bounded normalization and event batching. Flow identity is not request identity.

use std::collections::{HashSet, VecDeque};
use std::time::{Duration, Instant};

use chrono::{DateTime, Utc};
use uuid::Uuid;

use crate::delivery::{DeliveryError, DeliveryOutcome, DeliveryWorker};
use crate::event::{CorrelationQuality, EventInput, NormalizedEvent};
use crate::metrics::Metrics;
use crate::transport::{AnalyticsTransport, EventBatch, TransportError, MAX_BATCH_EVENTS};
use crate::wire::{decode, DecodeError};

#[derive(Clone, Debug)]
pub struct CollectorConfig {
    pub source_id: String,
    pub approved_routes: HashSet<String>,
    pub max_pending_events: usize,
    pub batch_size: usize,
    pub max_batch_wait: Duration,
    pub max_flows: usize,
    pub flow_ttl: Duration,
}

impl CollectorConfig {
    fn validate(&self) -> bool {
        !self.source_id.is_empty()
            && self.source_id.len() <= 64
            && self
                .source_id
                .bytes()
                .all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
            && (1..=65_536).contains(&self.max_pending_events)
            && (1..=MAX_BATCH_EVENTS).contains(&self.batch_size)
            && !self.max_batch_wait.is_zero()
            && (1..=65_536).contains(&self.max_flows)
            && !self.flow_ttl.is_zero()
    }
}

#[derive(Debug)]
pub enum CollectorError {
    Configuration,
    Decode(DecodeError),
    QueueFull,
    Batch(TransportError),
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct TickOutcome {
    pub batch_queued: bool,
    pub delivery: DeliveryOutcome,
}

pub struct Collector<T: AnalyticsTransport> {
    config: CollectorConfig,
    pending: VecDeque<NormalizedEvent>,
    first_pending_at: Option<Instant>,
    delivery: DeliveryWorker<T>,
    metrics: Metrics,
    last_sensor_drop_total: Option<u64>,
}

impl<T: AnalyticsTransport> Collector<T> {
    pub fn new(
        config: CollectorConfig,
        delivery: DeliveryWorker<T>,
    ) -> Result<Self, CollectorError> {
        if !config.validate() {
            return Err(CollectorError::Configuration);
        }
        Ok(Self {
            config,
            pending: VecDeque::new(),
            first_pending_at: None,
            delivery,
            metrics: Metrics::default(),
            last_sensor_drop_total: None,
        })
    }

    pub fn ingest(
        &mut self,
        record: &[u8],
        now: Instant,
        observed_at: DateTime<Utc>,
    ) -> Result<Uuid, CollectorError> {
        let started = Instant::now();
        self.metrics.records_seen = self.metrics.records_seen.saturating_add(1);
        let decoded = decode(record, &self.config.approved_routes).map_err(|error| {
            self.metrics.decode_rejected = self.metrics.decode_rejected.saturating_add(1);
            CollectorError::Decode(error)
        })?;
        if self.pending.len() >= self.config.max_pending_events {
            self.metrics.queue_rejected = self.metrics.queue_rejected.saturating_add(1);
            return Err(CollectorError::QueueFull);
        }
        if decoded.route_template.is_none() {
            self.metrics.route_unavailable = self.metrics.route_unavailable.saturating_add(1);
        }
        let mut event = NormalizedEvent::new(EventInput {
            source_id: self.config.source_id.clone(),
            sequence: decoded.sequence,
            monotonic_ns: decoded.monotonic_ns,
            direction: decoded.direction,
            method: decoded.method,
            status_code: decoded.status_code,
            route_template: decoded.route_template,
            observed_at,
        });
        event.correlation_quality = if decoded.flow_hash == 0 {
            self.metrics.correlation_unsupported =
                self.metrics.correlation_unsupported.saturating_add(1);
            CorrelationQuality::Unsupported
        } else {
            self.metrics.correlation_ambiguous =
                self.metrics.correlation_ambiguous.saturating_add(1);
            CorrelationQuality::Ambiguous
        };
        let event_id = event.event_id;
        if self.pending.is_empty() {
            self.first_pending_at = Some(now);
        }
        self.pending.push_back(event);
        self.metrics.records_accepted = self.metrics.records_accepted.saturating_add(1);
        self.metrics.observe_processing(started.elapsed());
        Ok(event_id)
    }

    pub fn tick(
        &mut self,
        now: Instant,
        observed_at: DateTime<Utc>,
    ) -> Result<TickOutcome, CollectorError> {
        let due = self.pending.len() >= self.config.batch_size
            || self.first_pending_at.is_some_and(|first| {
                now.saturating_duration_since(first) >= self.config.max_batch_wait
            });
        let mut batch_queued = false;
        if due && !self.pending.is_empty() {
            let count = self.pending.len().min(self.config.batch_size);
            let events: Vec<_> = self.pending.iter().take(count).cloned().collect();
            let batch = EventBatch::new(events, observed_at).map_err(CollectorError::Batch)?;
            match self.delivery.enqueue(batch, now) {
                Ok(()) => {
                    self.pending.drain(..count);
                    self.first_pending_at = if self.pending.is_empty() {
                        None
                    } else {
                        Some(now)
                    };
                    batch_queued = true;
                    self.metrics.batches_enqueued = self.metrics.batches_enqueued.saturating_add(1);
                }
                Err(DeliveryError::QueueFull) => {} // keep original events for the next tick
                Err(DeliveryError::Configuration) => return Err(CollectorError::Configuration),
            }
        }
        let delivery = self.delivery.tick(now);
        match delivery {
            DeliveryOutcome::Delivered => {
                self.metrics.batches_delivered = self.metrics.batches_delivered.saturating_add(1)
            }
            DeliveryOutcome::RetryScheduled => {
                self.metrics.batches_retry_scheduled =
                    self.metrics.batches_retry_scheduled.saturating_add(1)
            }
            DeliveryOutcome::Exhausted => {
                self.metrics.batches_exhausted = self.metrics.batches_exhausted.saturating_add(1)
            }
            _ => {}
        }
        Ok(TickOutcome {
            batch_queued,
            delivery,
        })
    }

    pub fn pending_events(&self) -> usize {
        self.pending.len()
    }
    pub fn queued_batches(&self) -> usize {
        self.delivery.queued_batches()
    }

    pub fn metrics(&self) -> Metrics {
        let mut snapshot = self.metrics.clone();
        snapshot.pending_events = self.pending.len();
        snapshot.queued_batches = self.delivery.queued_batches();
        snapshot
    }

    /// Called only when an attached, authenticated sensor adapter provides its
    /// aggregate drop counter. Until then loss remains explicitly unknown.
    pub fn observe_sensor_drop_total(&mut self, current: u64) {
        self.metrics
            .observe_sensor_drop_total(self.last_sensor_drop_total, current);
        self.last_sensor_drop_total = Some(current);
    }

    /// A disconnected sensor makes current loss unknown. Reattachment starts a
    /// new counter epoch, so a restarted counter is not subtracted from old data.
    pub fn mark_sensor_unavailable(&mut self) {
        self.metrics.sensor_drop_counter_available = false;
        self.last_sensor_drop_total = None;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::delivery::RetryConfig;

    struct Accept;
    impl AnalyticsTransport for Accept {
        fn send(&self, _batch: &EventBatch) -> Result<(), TransportError> {
            Ok(())
        }
    }

    fn record(flow_hash: u64, direction: u8, status: u16) -> [u8; 192] {
        let mut bytes = [0; 192];
        bytes[0..8].copy_from_slice(&42_u64.to_ne_bytes());
        bytes[8..12].copy_from_slice(&7_u32.to_ne_bytes());
        bytes[40..48].copy_from_slice(&flow_hash.to_ne_bytes());
        bytes[48] = 1;
        bytes[49] = direction;
        bytes[50..52].copy_from_slice(&status.to_ne_bytes());
        bytes[64..81].copy_from_slice(b"/orders/{orderId}");
        bytes
    }

    fn collector(batch_size: usize) -> Collector<Accept> {
        let config = CollectorConfig {
            source_id: "lab_1".into(),
            approved_routes: HashSet::from(["/orders/{orderId}".into()]),
            max_pending_events: 4,
            batch_size,
            max_batch_wait: Duration::from_secs(1),
            max_flows: 8,
            flow_ttl: Duration::from_secs(30),
        };
        let retry = RetryConfig {
            max_queued_batches: 2,
            max_attempts: 2,
            initial_delay: Duration::from_millis(10),
            max_delay: Duration::from_millis(20),
        };
        Collector::new(config, DeliveryWorker::new(Accept, retry).unwrap()).unwrap()
    }

    #[test]
    fn batches_at_threshold_and_delivers() {
        let now = Instant::now();
        let mut collector = collector(2);
        collector.ingest(&record(1, 0, 0), now, Utc::now()).unwrap();
        assert_eq!(
            collector.tick(now, Utc::now()).unwrap().delivery,
            DeliveryOutcome::Empty
        );
        collector.ingest(&record(2, 0, 0), now, Utc::now()).unwrap();
        let result = collector.tick(now, Utc::now()).unwrap();
        assert!(result.batch_queued);
        assert_eq!(result.delivery, DeliveryOutcome::Delivered);
        assert_eq!(collector.pending_events(), 0);
        let metrics = collector.metrics();
        assert_eq!(metrics.records_seen, 2);
        assert_eq!(metrics.records_accepted, 2);
        assert_eq!(metrics.batches_enqueued, 1);
        assert_eq!(metrics.batches_delivered, 1);
    }

    #[test]
    fn shared_flow_is_not_treated_as_shared_request() {
        let now = Instant::now();
        let mut collector = collector(3);
        collector
            .ingest(&record(42, 0, 0), now, Utc::now())
            .unwrap();
        collector
            .ingest(&record(42, 1, 200), now, Utc::now())
            .unwrap();
        assert!(collector
            .pending
            .iter()
            .all(|event| event.correlation_id.is_none()));
        assert!(collector
            .pending
            .iter()
            .all(|event| event.correlation_quality == CorrelationQuality::Ambiguous));
        assert_eq!(collector.metrics().correlation_ambiguous, 2);
    }

    #[test]
    fn missing_flow_is_explicitly_unsupported() {
        let mut collector = collector(2);
        collector
            .ingest(&record(0, 0, 0), Instant::now(), Utc::now())
            .unwrap();
        assert_eq!(
            collector.pending[0].correlation_quality,
            CorrelationQuality::Unsupported
        );
        assert_eq!(collector.metrics().correlation_unsupported, 1);
    }

    #[test]
    fn disconnected_sensor_does_not_report_zero_loss() {
        let mut collector = collector(2);
        assert!(!collector.metrics().sensor_drop_counter_available);
        collector.observe_sensor_drop_total(2);
        assert_eq!(collector.metrics().sensor_drops_reported, 2);
        collector.mark_sensor_unavailable();
        assert!(!collector.metrics().sensor_drop_counter_available);
        collector.observe_sensor_drop_total(1);
        assert_eq!(collector.metrics().sensor_drops_reported, 3);
    }

    #[test]
    fn batch_wait_flushes_partial_batch() {
        let now = Instant::now();
        let mut collector = collector(2);
        collector.ingest(&record(1, 0, 0), now, Utc::now()).unwrap();
        let result = collector
            .tick(now + Duration::from_secs(1), Utc::now())
            .unwrap();
        assert!(result.batch_queued);
    }

    #[test]
    fn malformed_record_is_counted_without_leaking_details() {
        let mut collector = collector(2);
        assert!(matches!(
            collector.ingest(&[0; 4], Instant::now(), Utc::now()),
            Err(CollectorError::Decode(_))
        ));
        let metrics = collector.metrics();
        assert_eq!(metrics.records_seen, 1);
        assert_eq!(metrics.decode_rejected, 1);
        assert_eq!(metrics.records_accepted, 0);
        assert_eq!(metrics.pending_events, 0);
    }
}
