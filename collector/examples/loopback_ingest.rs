//! One synthetic Rust-to-Python IF-04 lab handoff. No eBPF sensor is involved.

use std::collections::HashSet;
use std::error::Error;
use std::time::{Duration, Instant};

use api_sentinel_collector::delivery::{DeliveryOutcome, DeliveryWorker, RetryConfig};
use api_sentinel_collector::event::{Direction, EventInput, Method, NormalizedEvent};
use api_sentinel_collector::pipeline::{Collector, CollectorConfig};
use api_sentinel_collector::transport::{
    AnalyticsTransport, EventBatch, LoopbackAnalytics, TransportError,
};
use chrono::Utc;

fn main() -> Result<(), Box<dyn Error>> {
    let token = std::env::var("APISENTINEL_INGEST_TOKEN")?;
    let source_id = std::env::var("APISENTINEL_SOURCE_ID")?;
    let url = std::env::var("APISENTINEL_INGEST_URL")
        .unwrap_or_else(|_| "http://127.0.0.1:8001/v1/batches".into());
    let transport = LoopbackAnalytics::new(&url, &token, &source_id, Duration::from_secs(1))
        .map_err(|error| format!("loopback transport configuration: {error:?}"))?;
    let retry = RetryConfig {
        max_queued_batches: 2,
        max_attempts: 2,
        initial_delay: Duration::from_millis(100),
        max_delay: Duration::from_millis(100),
    };
    let config = CollectorConfig {
        source_id: source_id.clone(),
        approved_routes: HashSet::from(["/orders/{orderId}".into()]),
        max_pending_events: 4,
        batch_size: 1,
        max_batch_wait: Duration::from_millis(100),
        max_flows: 1,
        flow_ttl: Duration::from_secs(1),
    };
    let worker = DeliveryWorker::new(transport, retry)
        .map_err(|error| format!("retry configuration: {error:?}"))?;
    let mut collector = Collector::new(config, worker)
        .map_err(|error| format!("collector configuration: {error:?}"))?;
    let mut record = [0_u8; 192];
    record[0..8].copy_from_slice(&1_u64.to_ne_bytes());
    record[8..12].copy_from_slice(&1_u32.to_ne_bytes());
    record[48] = 1; // GET
    record[49] = 0; // ingress
    record[64..81].copy_from_slice(b"/orders/{orderId}");
    let now = Instant::now();
    collector
        .ingest(&record, now, Utc::now())
        .map_err(|error| format!("synthetic record rejected: {error:?}"))?;
    let outcome = collector
        .tick(now, Utc::now())
        .map_err(|error| format!("batch processing failed: {error:?}"))?;
    if outcome.delivery != DeliveryOutcome::Delivered {
        return Err(format!("batch not delivered: {:?}", outcome.delivery).into());
    }
    let event = NormalizedEvent::new(EventInput {
        source_id: source_id.clone(),
        sequence: 2,
        monotonic_ns: 2,
        direction: Direction::Ingress,
        method: Method::Get,
        status_code: None,
        route_template: Some("/orders/{orderId}".into()),
        observed_at: Utc::now(),
    });
    let batch = EventBatch::new(vec![event], Utc::now())
        .map_err(|error| format!("batch construction: {error:?}"))?;
    let sender = LoopbackAnalytics::new(&url, &token, &source_id, Duration::from_secs(1))
        .map_err(|error| format!("loopback transport configuration: {error:?}"))?;
    sender
        .send(&batch)
        .map_err(|error| format!("first send failed: {error:?}"))?;
    sender
        .send(&batch)
        .map_err(|error| format!("idempotent replay failed: {error:?}"))?;

    let first = if token.starts_with('x') { 'y' } else { 'x' };
    let wrong_token = format!("{first}{}", "x".repeat(31));
    let wrong_sender =
        LoopbackAnalytics::new(&url, &wrong_token, &source_id, Duration::from_secs(1))
            .map_err(|error| format!("negative transport setup: {error:?}"))?;
    if wrong_sender.send(&batch) != Err(TransportError::Rejected) {
        return Err("receiver did not reject invalid credential".into());
    }
    let mut wrong_source_batch = batch.clone();
    wrong_source_batch.events[0].source_id = "other_source".into();
    let wrong_source_sender =
        LoopbackAnalytics::new(&url, &token, "other_source", Duration::from_secs(1))
            .map_err(|error| format!("negative source setup: {error:?}"))?;
    if wrong_source_sender.send(&wrong_source_batch) != Err(TransportError::Rejected) {
        return Err("receiver did not reject wrong source".into());
    }
    println!(
        "synthetic loopback ack, idempotent retry, invalid credential and wrong source passed; no sensor or enforcement involved"
    );
    Ok(())
}
