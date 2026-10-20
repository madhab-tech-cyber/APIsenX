//! Local Day 7 microbenchmark: sensor record decode + event creation + JSON.
//! It excludes ring-buffer poll, queues, TLS, analytics and the mock API.

use std::collections::HashSet;
use std::hint::black_box;
use std::time::Instant;

use api_sentinel_collector::event::{EventInput, NormalizedEvent};
use api_sentinel_collector::wire::{decode, EVENT_BYTES};
use chrono::Utc;

fn record() -> [u8; EVENT_BYTES] {
    let mut bytes = [0_u8; EVENT_BYTES];
    bytes[0..8].copy_from_slice(&42_u64.to_ne_bytes());
    bytes[8..12].copy_from_slice(&7_u32.to_ne_bytes());
    bytes[48] = 1; // GET
    bytes[64..81].copy_from_slice(b"/orders/{orderId}");
    bytes
}

fn percentile(sorted: &[u128], numerator: usize) -> u128 {
    let index = (sorted.len() - 1) * numerator / 100;
    sorted[index]
}

fn main() {
    let routes = HashSet::from(["/orders/{orderId}".to_string()]);
    let bytes = record();
    let samples = 100_000;
    let warmup = 10_000;
    let mut latencies = Vec::with_capacity(samples);
    let mut checksum = 0_usize;
    let mut measured_start = None;
    for i in 0..(warmup + samples) {
        if i == warmup {
            measured_start = Some(Instant::now());
        }
        let start = Instant::now();
        let decoded = decode(black_box(&bytes), black_box(&routes)).expect("valid fixture");
        let event = NormalizedEvent::new(EventInput {
            source_id: "lab_collector_1".into(),
            sequence: decoded.sequence,
            monotonic_ns: decoded.monotonic_ns,
            direction: decoded.direction,
            method: decoded.method,
            status_code: decoded.status_code,
            route_template: decoded.route_template,
            observed_at: Utc::now(),
        });
        let json = serde_json::to_vec(&event).expect("serializable event");
        checksum = checksum.wrapping_add(black_box(json.len()));
        let elapsed = start.elapsed().as_nanos();
        if i >= warmup {
            latencies.push(elapsed);
        }
    }
    let wall_time = measured_start.expect("warmup complete").elapsed();
    latencies.sort_unstable();
    let throughput = (samples as f64) / wall_time.as_secs_f64();
    println!("samples={samples} warmup={warmup} checksum={checksum}");
    println!(
        "p50_us={:.3} p95_us={:.3} p99_us={:.3} max_us={:.3} throughput_events_per_s={:.0}",
        percentile(&latencies, 50) as f64 / 1000.0,
        percentile(&latencies, 95) as f64 / 1000.0,
        percentile(&latencies, 99) as f64 / 1000.0,
        latencies[samples - 1] as f64 / 1000.0,
        throughput
    );
}
