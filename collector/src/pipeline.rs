//! Bounded normalization, flow-level correlation and event batching.

use std::collections::{HashMap, HashSet, VecDeque};
use std::time::{Duration, Instant};

use chrono::{DateTime, Utc};
use uuid::Uuid;

use crate::delivery::{DeliveryError, DeliveryOutcome, DeliveryWorker};
use crate::event::{EventInput, NormalizedEvent};
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

struct CorrelationTable {
    entries: HashMap<u64, (Uuid, Instant)>,
    capacity: usize,
    ttl: Duration,
}

impl CorrelationTable {
    fn id_for(&mut self, flow_hash: u64, now: Instant) -> Uuid {
        if flow_hash == 0 {
            return Uuid::new_v4();
        }
        if let Some((id, last_seen)) = self.entries.get_mut(&flow_hash) {
            if now.saturating_duration_since(*last_seen) < self.ttl {
                *last_seen = now;
                return *id;
            }
        }
        if self.entries.len() >= self.capacity && !self.entries.contains_key(&flow_hash) {
            if let Some(oldest) = self
                .entries
                .iter()
                .min_by_key(|(_, (_, seen))| *seen)
                .map(|(key, _)| *key)
            {
                self.entries.remove(&oldest);
            }
        }
        let id = Uuid::new_v4();
        self.entries.insert(flow_hash, (id, now));
        id
    }
}

pub struct Collector<T: AnalyticsTransport> {
    config: CollectorConfig,
    correlations: CorrelationTable,
    pending: VecDeque<NormalizedEvent>,
    first_pending_at: Option<Instant>,
    delivery: DeliveryWorker<T>,
    metrics: Metrics,
}

impl<T: AnalyticsTransport> Collector<T> {
    pub fn new(
        config: CollectorConfig,
        delivery: DeliveryWorker<T>,
    ) -> Result<Self, CollectorError> {
        if !config.validate() {
            return Err(CollectorError::Configuration);
        }
        let correlations = CorrelationTable {
            entries: HashMap::new(),
            capacity: config.max_flows,
            ttl: config.flow_ttl,
        };
        Ok(Self {
            config,
            correlations,
            pending: VecDeque::new(),
            first_pending_at: None,
            delivery,
            metrics: Metrics::default(),
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
        event.correlation_id = self.correlations.id_for(decoded.flow_hash, now);
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
    fn flow_correlation_is_stable_within_ttl_only() {
        let now = Instant::now();
        let mut table = CorrelationTable {
            entries: HashMap::new(),
            capacity: 2,
            ttl: Duration::from_secs(1),
        };
        let first = table.id_for(42, now);
        assert_eq!(first, table.id_for(42, now + Duration::from_millis(500)));
        assert_ne!(first, table.id_for(42, now + Duration::from_secs(2)));
        assert_ne!(first, table.id_for(0, now));
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
