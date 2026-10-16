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

impl NormalizedEvent {
    pub fn new(
        source_id: String,
        sequence: u32,
        monotonic_ns: u64,
        direction: Direction,
        method: Method,
        status_code: Option<u16>,
        route_template: Option<String>,
        observed_at: DateTime<Utc>,
    ) -> Self {
        let route_quality = if route_template.is_some() {
            RouteQuality::ApprovedTemplate
        } else {
            RouteQuality::RouteUnavailable
        };
        Self {
            schema_name: "collector_event",
            schema_version: "1.0",
            event_id: Uuid::new_v4(),
            correlation_id: Uuid::new_v4(),
            source_id,
            sensor_sequence: sequence,
            sensor_monotonic_ns: monotonic_ns,
            observed_at,
            direction,
            method,
            status_code,
            route_template,
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
        let event = NormalizedEvent::new(
            "lab_collector_1".into(),
            7,
            42,
            Direction::Ingress,
            Method::Get,
            None,
            Some("/orders/{orderId}".into()),
            Utc::now(),
        );
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
