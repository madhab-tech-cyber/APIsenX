use chrono::{DateTime, Utc};
use serde::Serialize;
use uuid::Uuid;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum Direction {
    Ingress,
    Egress,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum Method {
    Unknown,
    Get,
    Post,
    Put,
    Delete,
    Patch,
    Head,
    Options,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RouteQuality {
    ApprovedTemplate,
    RouteUnavailable,
}

/// The privacy-minimized IF-04 event. IDs are random and stable on retries.
#[derive(Clone, Debug, Serialize)]
pub struct NormalizedEvent {
    pub schema_name: &'static str,
    pub schema_version: &'static str,
    pub event_id: Uuid,
    pub correlation_id: Uuid,
    pub source_id: String,
    pub sensor_sequence: u32,
    pub sensor_monotonic_ns: u64,
    pub observed_at: DateTime<Utc>,
    pub direction: Direction,
    pub method: Method,
    pub status_code: Option<u16>,
    pub route_template: Option<String>,
    pub route_quality: RouteQuality,
    pub data_classification: &'static str,
}

pub struct EventInput {
    pub source_id: String,
    pub sequence: u32,
    pub monotonic_ns: u64,
    pub direction: Direction,
    pub method: Method,
    pub status_code: Option<u16>,
    pub route_template: Option<String>,
    pub observed_at: DateTime<Utc>,
}

impl NormalizedEvent {
    pub fn new(input: EventInput) -> Self {
        let route_quality = if input.route_template.is_some() {
            RouteQuality::ApprovedTemplate
        } else {
            RouteQuality::RouteUnavailable
        };
        Self {
            schema_name: "collector_event",
            schema_version: "1.0",
            event_id: Uuid::new_v4(),
            correlation_id: Uuid::new_v4(),
            source_id: input.source_id,
            sensor_sequence: input.sequence,
            sensor_monotonic_ns: input.monotonic_ns,
            observed_at: input.observed_at,
            direction: input.direction,
            method: input.method,
            status_code: input.status_code,
            route_template: input.route_template,
            route_quality,
            data_classification: "restricted",
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn event_serializes_to_proposed_contract() {
        let event = NormalizedEvent::new(EventInput {
            source_id: "lab_collector_1".into(),
            sequence: 7,
            monotonic_ns: 42,
            direction: Direction::Ingress,
            method: Method::Get,
            status_code: None,
            route_template: Some("/orders/{orderId}".into()),
            observed_at: Utc::now(),
        });
        let value = serde_json::to_value(event).unwrap();
        assert_eq!(value["schema_name"], "collector_event");
        assert_eq!(value["schema_version"], "1.0");
        assert_eq!(value["direction"], "ingress");
        assert_eq!(value["method"], "GET");
        assert_eq!(value["route_quality"], "approved_template");
        assert_eq!(value["data_classification"], "restricted");
        assert!(value.get("authorization").is_none());
    }
}
