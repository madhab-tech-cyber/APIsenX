//! Bounded retry state. The caller drives `tick`; no thread sleeps or grows
//! an unbounded queue while analytics is unavailable.

use std::collections::VecDeque;
use std::time::{Duration, Instant};

use crate::transport::{AnalyticsTransport, EventBatch, TransportError};

#[derive(Clone, Copy, Debug)]
pub struct RetryConfig {
    pub max_queued_batches: usize,
    pub max_attempts: u32,
    pub initial_delay: Duration,
    pub max_delay: Duration,
}

impl RetryConfig {
    pub fn validate(&self) -> Result<(), DeliveryError> {
        if !(1..=1024).contains(&self.max_queued_batches)
            || !(1..=10).contains(&self.max_attempts)
            || self.initial_delay.is_zero()
            || self.max_delay < self.initial_delay
            || self.max_delay > Duration::from_secs(60)
        {
            return Err(DeliveryError::Configuration);
        }
        Ok(())
    }
}

#[derive(Debug, PartialEq, Eq)]
pub enum DeliveryError {
    Configuration,
    QueueFull,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DeliveryOutcome {
    Empty,
    Deferred,
    Delivered,
    RetryScheduled,
    Exhausted,
}

struct Pending {
    batch: EventBatch,
    attempts: u32,
    next_due: Instant,
}

pub struct DeliveryWorker<T: AnalyticsTransport> {
    transport: T,
    config: RetryConfig,
    pending: VecDeque<Pending>,
}

impl<T: AnalyticsTransport> DeliveryWorker<T> {
    pub fn new(transport: T, config: RetryConfig) -> Result<Self, DeliveryError> {
        config.validate()?;
        Ok(Self {
            transport,
            config,
            pending: VecDeque::new(),
        })
    }

    pub fn enqueue(&mut self, batch: EventBatch, now: Instant) -> Result<(), DeliveryError> {
        if self.pending.len() >= self.config.max_queued_batches {
            return Err(DeliveryError::QueueFull);
        }
        self.pending.push_back(Pending {
            batch,
            attempts: 0,
            next_due: now,
        });
        Ok(())
    }

    pub fn queued_batches(&self) -> usize {
        self.pending.len()
    }

    pub fn tick(&mut self, now: Instant) -> DeliveryOutcome {
        let Some(front) = self.pending.front_mut() else {
            return DeliveryOutcome::Empty;
        };
        if now < front.next_due {
            return DeliveryOutcome::Deferred;
        }
        match self.transport.send(&front.batch) {
            Ok(()) => {
                self.pending.pop_front();
                DeliveryOutcome::Delivered
            }
            Err(error) => {
                if !retryable(&error) {
                    self.pending.pop_front();
                    return DeliveryOutcome::Exhausted;
                }
                front.attempts += 1;
                if front.attempts >= self.config.max_attempts {
                    self.pending.pop_front();
                    DeliveryOutcome::Exhausted
                } else {
                    let shift = (front.attempts - 1).min(20);
                    let delay = self
                        .config
                        .initial_delay
                        .checked_mul(1_u32 << shift)
                        .unwrap_or(self.config.max_delay)
                        .min(self.config.max_delay);
                    front.next_due = now.checked_add(delay).unwrap_or(now);
                    DeliveryOutcome::RetryScheduled
                }
            }
        }
    }
}

/// Keep error categories bounded; callers must not log URLs or response bodies.
pub fn retryable(error: &TransportError) -> bool {
    matches!(
        error,
        TransportError::Timeout | TransportError::Remote | TransportError::Acknowledgement
    )
}

#[cfg(test)]
mod tests {
    use std::sync::Mutex;

    use chrono::Utc;
    use uuid::Uuid;

    use super::*;
    use crate::event::{Direction, EventInput, Method, NormalizedEvent};

    struct ScriptedTransport {
        results: Mutex<VecDeque<Result<(), TransportError>>>,
        sent: Mutex<Vec<Uuid>>,
    }

    impl AnalyticsTransport for ScriptedTransport {
        fn send(&self, batch: &EventBatch) -> Result<(), TransportError> {
            self.sent.lock().unwrap().push(batch.batch_id);
            self.results.lock().unwrap().pop_front().unwrap_or(Ok(()))
        }
    }

    fn batch() -> EventBatch {
        EventBatch::new(
            vec![NormalizedEvent::new(EventInput {
                source_id: "lab_1".into(),
                sequence: 1,
                monotonic_ns: 1,
                direction: Direction::Ingress,
                method: Method::Get,
                status_code: None,
                route_template: None,
                observed_at: Utc::now(),
            })],
            Utc::now(),
        )
        .unwrap()
    }

    fn config() -> RetryConfig {
        RetryConfig {
            max_queued_batches: 1,
            max_attempts: 3,
            initial_delay: Duration::from_millis(10),
            max_delay: Duration::from_millis(40),
        }
    }

    #[test]
    fn timeout_then_reconnect_reuses_batch_id() {
        let transport = ScriptedTransport {
            results: Mutex::new(VecDeque::from([Err(TransportError::Timeout), Ok(())])),
            sent: Mutex::new(Vec::new()),
        };
        let now = Instant::now();
        let mut worker = DeliveryWorker::new(transport, config()).unwrap();
        worker.enqueue(batch(), now).unwrap();
        assert_eq!(worker.tick(now), DeliveryOutcome::RetryScheduled);
        assert_eq!(
            worker.tick(now + Duration::from_millis(9)),
            DeliveryOutcome::Deferred
        );
        assert_eq!(
            worker.tick(now + Duration::from_millis(10)),
            DeliveryOutcome::Delivered
        );
        assert_eq!(worker.queued_batches(), 0);
        let sent = worker.transport.sent.lock().unwrap();
        assert_eq!(sent.len(), 2);
        assert_eq!(sent[0], sent[1]);
    }

    #[test]
    fn queue_is_bounded_and_retry_exhausts() {
        let transport = ScriptedTransport {
            results: Mutex::new(VecDeque::from([
                Err(TransportError::Remote),
                Err(TransportError::Remote),
                Err(TransportError::Remote),
            ])),
            sent: Mutex::new(Vec::new()),
        };
        let now = Instant::now();
        let mut worker = DeliveryWorker::new(transport, config()).unwrap();
        worker.enqueue(batch(), now).unwrap();
        assert_eq!(worker.enqueue(batch(), now), Err(DeliveryError::QueueFull));
        assert_eq!(worker.tick(now), DeliveryOutcome::RetryScheduled);
        assert_eq!(
            worker.tick(now + Duration::from_millis(10)),
            DeliveryOutcome::RetryScheduled
        );
        assert_eq!(
            worker.tick(now + Duration::from_millis(30)),
            DeliveryOutcome::Exhausted
        );
        assert_eq!(worker.queued_batches(), 0);
    }
}
