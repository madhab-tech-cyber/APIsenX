//! Checked decoding of Member 2's proposed native-endian 192-byte C record.
//! This parser does not claim the Linux ring-buffer map is available yet.

use std::collections::HashSet;

use crate::event::{Direction, Method};

pub const EVENT_BYTES: usize = 192;
const ROUTE_START: usize = 64;
const ROUTE_END: usize = 192;

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum DecodeError {
    Length,
    Method,
    Direction,
    Status,
    Flags,
    RouteTermination,
    RouteEncoding,
}

#[derive(Clone, Debug)]
pub struct KernelEvent {
    pub sequence: u32,
    pub monotonic_ns: u64,
    /// Source-local hint only; never forwarded or persisted.
    pub flow_hash: u64,
    pub direction: Direction,
    pub method: Method,
    pub status_code: Option<u16>,
    /// Present only if the marker exactly matches a reviewed template.
    pub route_template: Option<String>,
}

/// `approved_routes` must be supplied from a reviewed, versioned configuration.
/// Unknown concrete paths are not forwarded because they may contain identifiers.
pub fn decode(
    record: &[u8],
    approved_routes: &HashSet<String>,
) -> Result<KernelEvent, DecodeError> {
    if record.len() != EVENT_BYTES {
        return Err(DecodeError::Length);
    }
    let monotonic_ns = u64::from_ne_bytes(record[0..8].try_into().unwrap());
    let sequence = u32::from_ne_bytes(record[8..12].try_into().unwrap());
    let flow_hash = u64::from_ne_bytes(record[40..48].try_into().unwrap());
    let method = match record[48] {
        0 => Method::Unknown,
        1 => Method::Get,
        2 => Method::Post,
        3 => Method::Put,
        4 => Method::Delete,
        5 => Method::Patch,
        6 => Method::Head,
        7 => Method::Options,
        _ => return Err(DecodeError::Method),
    };
    let direction = match record[49] {
        0 => Direction::Ingress,
        1 => Direction::Egress,
        _ => return Err(DecodeError::Direction),
    };
    let status = u16::from_ne_bytes(record[50..52].try_into().unwrap());
    let status_code = match (direction, status) {
        (Direction::Ingress, 0) => None,
        (Direction::Egress, 100..=599) => Some(status),
        _ => return Err(DecodeError::Status),
    };
    let flags = u32::from_ne_bytes(record[60..64].try_into().unwrap());
    if flags != 0 {
        // Member 2 has not assigned flag bits yet. Never guess their meaning.
        return Err(DecodeError::Flags);
    }
    let route_bytes = &record[ROUTE_START..ROUTE_END];
    let terminator = route_bytes
        .iter()
        .position(|byte| *byte == 0)
        .ok_or(DecodeError::RouteTermination)?;
    let route =
        std::str::from_utf8(&route_bytes[..terminator]).map_err(|_| DecodeError::RouteEncoding)?;
    if !route.is_ascii()
        || route
            .bytes()
            .any(|byte| byte.is_ascii_control() || byte == b'?' || byte == b'#')
    {
        return Err(DecodeError::RouteEncoding);
    }
    let route_template = approved_routes.get(route).cloned();
    Ok(KernelEvent {
        sequence,
        monotonic_ns,
        flow_hash,
        direction,
        method,
        status_code,
        route_template,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn valid_record() -> [u8; EVENT_BYTES] {
        let mut record = [0_u8; EVENT_BYTES];
        record[0..8].copy_from_slice(&42_u64.to_ne_bytes());
        record[8..12].copy_from_slice(&7_u32.to_ne_bytes());
        record[48] = 1;
        record[49] = 0;
        record[64..81].copy_from_slice(b"/orders/{orderId}");
        record
    }

    fn routes() -> HashSet<String> {
        HashSet::from(["/orders/{orderId}".to_string()])
    }

    #[test]
    fn decodes_valid_record_without_private_flow_fields() {
        let event = decode(&valid_record(), &routes()).unwrap();
        assert_eq!(event.sequence, 7);
        assert_eq!(event.route_template.as_deref(), Some("/orders/{orderId}"));
    }

    #[test]
    fn refuses_malformed_length_enum_and_unterminated_route() {
        assert!(matches!(
            decode(&valid_record()[..191], &routes()),
            Err(DecodeError::Length)
        ));
        let mut record = valid_record();
        record[48] = 99;
        assert!(matches!(
            decode(&record, &routes()),
            Err(DecodeError::Method)
        ));
        record = valid_record();
        record[64..].fill(b'x');
        assert!(matches!(
            decode(&record, &routes()),
            Err(DecodeError::RouteTermination)
        ));
    }

    #[test]
    fn concrete_path_is_not_forwarded() {
        let mut record = valid_record();
        record[64..].fill(0);
        record[64..75].copy_from_slice(b"/orders/123");
        assert!(decode(&record, &routes()).unwrap().route_template.is_none());
    }

    #[test]
    fn rejects_unknown_flags_and_status() {
        let mut record = valid_record();
        record[60] = 1;
        assert!(matches!(
            decode(&record, &routes()),
            Err(DecodeError::Flags)
        ));
        record = valid_record();
        record[50..52].copy_from_slice(&200_u16.to_ne_bytes());
        assert!(matches!(
            decode(&record, &routes()),
            Err(DecodeError::Status)
        ));
    }
}
