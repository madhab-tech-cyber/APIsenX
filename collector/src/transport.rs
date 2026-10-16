//! Bounded, authenticated IF-04 forwarding. The receiver contract is proposed;
//! Member 4 has not implemented or accepted it yet.

use std::io::Read;
use std::time::Duration;

use chrono::{DateTime, Utc};
use reqwest::blocking::Client;
use reqwest::Identity;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::event::NormalizedEvent;

pub const MAX_BATCH_EVENTS: usize = 256;
pub const MAX_BATCH_BYTES: usize = 1_048_576;
pub const MAX_ACK_BYTES: usize = 65_536;

#[derive(Clone, Debug, Serialize)]
pub struct EventBatch {
    pub schema_name: &'static str,
    pub schema_version: &'static str,
    pub batch_id: Uuid,
    pub created_at: DateTime<Utc>,
    pub events: Vec<NormalizedEvent>,
}

impl EventBatch {
    pub fn new(
        events: Vec<NormalizedEvent>,
        created_at: DateTime<Utc>,
    ) -> Result<Self, TransportError> {
        if events.is_empty() || events.len() > MAX_BATCH_EVENTS {
            return Err(TransportError::BatchBounds);
        }
        let batch = Self {
            schema_name: "collector_batch",
            schema_version: "1.0",
            batch_id: Uuid::new_v4(),
            created_at,
            events,
        };
        if serde_json::to_vec(&batch)
            .map_err(|_| TransportError::Serialization)?
            .len()
            > MAX_BATCH_BYTES
        {
            return Err(TransportError::BatchBounds);
        }
        Ok(batch)
    }
}

#[derive(Debug, PartialEq, Eq)]
pub enum TransportError {
    Endpoint,
    Identity,
    BatchBounds,
    Serialization,
    Timeout,
    Remote,
    Acknowledgement,
}

pub trait AnalyticsTransport {
    fn send(&self, batch: &EventBatch) -> Result<(), TransportError>;
}

#[derive(Deserialize)]
struct BatchAck {
    batch_id: Uuid,
    accepted_event_ids: Vec<Uuid>,
}

fn check_ack(batch: &EventBatch, ack: BatchAck) -> Result<(), TransportError> {
    if ack.batch_id != batch.batch_id || ack.accepted_event_ids.len() != batch.events.len() {
        return Err(TransportError::Acknowledgement);
    }
    let expected: std::collections::HashSet<_> =
        batch.events.iter().map(|event| event.event_id).collect();
    let received: std::collections::HashSet<_> = ack.accepted_event_ids.into_iter().collect();
    if expected != received || received.len() != batch.events.len() {
        return Err(TransportError::Acknowledgement);
    }
    Ok(())
}

pub struct HttpsAnalytics {
    endpoint: reqwest::Url,
    client: Client,
}

impl HttpsAnalytics {
    /// `client_identity_pem` must contain the lab client's certificate and key.
    /// Provision it at runtime; never commit or log it.
    pub fn new(
        endpoint: &str,
        client_identity_pem: &[u8],
        timeout: Duration,
    ) -> Result<Self, TransportError> {
        let endpoint = reqwest::Url::parse(endpoint).map_err(|_| TransportError::Endpoint)?;
        if endpoint.scheme() != "https"
            || endpoint.username() != ""
            || endpoint.password().is_some()
            || endpoint.query().is_some()
            || endpoint.fragment().is_some()
        {
            return Err(TransportError::Endpoint);
        }
        if timeout.is_zero() || timeout > Duration::from_secs(30) {
            return Err(TransportError::Endpoint);
        }
        let identity =
            Identity::from_pem(client_identity_pem).map_err(|_| TransportError::Identity)?;
        let client = Client::builder()
            .identity(identity)
            .https_only(true)
            .connect_timeout(timeout)
            .timeout(timeout)
            .build()
            .map_err(|_| TransportError::Identity)?;
        Ok(Self { endpoint, client })
    }
}

impl AnalyticsTransport for HttpsAnalytics {
    fn send(&self, batch: &EventBatch) -> Result<(), TransportError> {
        if batch.events.is_empty() || batch.events.len() > MAX_BATCH_EVENTS {
            return Err(TransportError::BatchBounds);
        }
        let encoded = serde_json::to_vec(batch).map_err(|_| TransportError::Serialization)?;
        if encoded.len() > MAX_BATCH_BYTES {
            return Err(TransportError::BatchBounds);
        }
        let response = self
            .client
            .post(self.endpoint.clone())
            .header("content-type", "application/json")
            .body(encoded)
            .send()
            .map_err(|error| {
                if error.is_timeout() {
                    TransportError::Timeout
                } else {
                    TransportError::Remote
                }
            })?;
        if !response.status().is_success() {
            return Err(TransportError::Remote);
        }
        let mut body = Vec::new();
        response
            .take((MAX_ACK_BYTES + 1) as u64)
            .read_to_end(&mut body)
            .map_err(|_| TransportError::Acknowledgement)?;
        if body.len() > MAX_ACK_BYTES {
            return Err(TransportError::Acknowledgement);
        }
        let ack: BatchAck =
            serde_json::from_slice(&body).map_err(|_| TransportError::Acknowledgement)?;
        check_ack(batch, ack)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::event::{Direction, EventInput, Method};

    fn batch() -> EventBatch {
        let event = NormalizedEvent::new(EventInput {
            source_id: "lab_collector_1".into(),
            sequence: 1,
            monotonic_ns: 42,
            direction: Direction::Ingress,
            method: Method::Get,
            status_code: None,
            route_template: None,
            observed_at: Utc::now(),
        });
        EventBatch::new(vec![event], Utc::now()).unwrap()
    }

    #[test]
    fn batch_and_ack_preserve_ids() {
        let batch = batch();
        let ack = BatchAck {
            batch_id: batch.batch_id,
            accepted_event_ids: vec![batch.events[0].event_id],
        };
        assert_eq!(check_ack(&batch, ack), Ok(()));
        let duplicate = BatchAck {
            batch_id: batch.batch_id,
            accepted_event_ids: vec![Uuid::new_v4()],
        };
        assert_eq!(
            check_ack(&batch, duplicate),
            Err(TransportError::Acknowledgement)
        );
    }

    #[test]
    fn refuses_empty_and_unbounded_batches() {
        assert_eq!(
            EventBatch::new(vec![], Utc::now()).unwrap_err(),
            TransportError::BatchBounds
        );
        let event = batch().events.remove(0);
        assert_eq!(
            EventBatch::new(vec![event; MAX_BATCH_EVENTS + 1], Utc::now()).unwrap_err(),
            TransportError::BatchBounds
        );
    }

    #[test]
    fn refuses_plaintext_endpoint() {
        assert_eq!(
            HttpsAnalytics::new("http://localhost/ingest", &[], Duration::from_secs(1)).err(),
            Some(TransportError::Endpoint)
        );
    }
}
