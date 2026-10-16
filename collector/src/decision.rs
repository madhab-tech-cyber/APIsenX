//! Day 10 decision parsing and structural validation only. Nothing in this
//! module applies a decision to traffic or verifies its cryptographic origin.

use chrono::{DateTime, Duration, Utc};
use serde::Deserialize;
use uuid::Uuid;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DecisionAction {
    Allow,
    Alert,
    Deny,
    RateLimit,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DecisionTarget {
    pub method: String,
    pub route_template: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RateLimit {
    pub requests: u32,
    pub per_seconds: u32,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProposedDecision {
    pub schema_name: String,
    pub schema_version: String,
    pub decision_id: Uuid,
    pub correlation_id: Uuid,
    pub policy_id: String,
    pub policy_version: String,
    pub issuer: String,
    pub key_id: String,
    pub issued_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
    pub action: DecisionAction,
    pub reason_code: String,
    pub target: DecisionTarget,
    pub approval_id: Option<String>,
    pub rollback_id: Option<String>,
    pub limit: Option<RateLimit>,
    pub signature: String,
}

#[derive(Debug, PartialEq, Eq)]
pub enum DecisionError {
    Malformed,
    Version,
    Time,
    Target,
    Approval,
    Limit,
    Metadata,
}

impl ProposedDecision {
    /// This does not authenticate the issuer, signature, approval reference or
    /// target binding. It cannot authorize active enforcement.
    pub fn parse_for_dry_run(json: &[u8], now: DateTime<Utc>) -> Result<Self, DecisionError> {
        if json.len() > 8192 {
            return Err(DecisionError::Malformed);
        }
        let decision: Self = serde_json::from_slice(json).map_err(|_| DecisionError::Malformed)?;
        decision.validate_structure(now)?;
        Ok(decision)
    }

    fn validate_structure(&self, now: DateTime<Utc>) -> Result<(), DecisionError> {
        if self.schema_name != "enforcement_decision" || self.schema_version != "1.0" {
            return Err(DecisionError::Version);
        }
        if self.issued_at > now + Duration::seconds(30)
            || self.expires_at <= now
            || self.expires_at <= self.issued_at
            || self.expires_at - self.issued_at > Duration::minutes(5)
        {
            return Err(DecisionError::Time);
        }
        if !matches!(
            self.target.method.as_str(),
            "GET" | "POST" | "PUT" | "DELETE" | "PATCH" | "HEAD" | "OPTIONS"
        ) || self.target.route_template.is_empty()
            || self.target.route_template.len() > 128
            || !self.target.route_template.starts_with('/')
            || self.target.route_template.contains(['*', '?', '#'])
        {
            return Err(DecisionError::Target);
        }
        if self.policy_id.is_empty()
            || self.policy_version.is_empty()
            || self.issuer.is_empty()
            || self.key_id.is_empty()
            || self.signature.is_empty()
            || self.reason_code.is_empty()
            || self.reason_code.len() > 64
            || !self
                .reason_code
                .bytes()
                .all(|b| b.is_ascii_uppercase() || b.is_ascii_digit() || b == b'_')
        {
            return Err(DecisionError::Metadata);
        }
        match self.action {
            DecisionAction::Deny | DecisionAction::RateLimit => {
                if self.approval_id.as_deref().unwrap_or("").is_empty()
                    || self.rollback_id.as_deref().unwrap_or("").is_empty()
                {
                    return Err(DecisionError::Approval);
                }
            }
            _ => {}
        }
        match (self.action, &self.limit) {
            (DecisionAction::RateLimit, Some(limit))
                if (1..=100_000).contains(&limit.requests)
                    && (1..=3600).contains(&limit.per_seconds) => {}
            (DecisionAction::RateLimit, _) | (_, Some(_)) => return Err(DecisionError::Limit),
            _ => {}
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use serde_json::{json, Value};

    use super::*;

    fn decision(action: &str, now: DateTime<Utc>) -> Value {
        json!({
            "schema_name": "enforcement_decision", "schema_version": "1.0",
            "decision_id": Uuid::new_v4(), "correlation_id": Uuid::new_v4(),
            "policy_id": "AP-1.0", "policy_version": "1.0", "issuer": "lab_analytics",
            "key_id": "lab_key_1", "issued_at": now, "expires_at": now + Duration::minutes(1),
            "action": action, "reason_code": "LAB_RULE", "target": {"method": "GET", "route_template": "/orders/{orderId}"},
            "signature": "test-only-placeholder"
        })
    }

    fn parse(value: Value, now: DateTime<Utc>) -> Result<ProposedDecision, DecisionError> {
        ProposedDecision::parse_for_dry_run(&serde_json::to_vec(&value).unwrap(), now)
    }

    #[test]
    fn parses_allow_and_alert_for_observation() {
        let now = Utc::now();
        assert_eq!(
            parse(decision("allow", now), now).unwrap().action,
            DecisionAction::Allow
        );
        assert_eq!(
            parse(decision("alert", now), now).unwrap().action,
            DecisionAction::Alert
        );
    }

    #[test]
    fn deny_needs_approval_and_rollback_references_even_in_dry_run() {
        let now = Utc::now();
        assert_eq!(
            parse(decision("deny", now), now).unwrap_err(),
            DecisionError::Approval
        );
        let mut value = decision("deny", now);
        value["approval_id"] = json!("M1-approval-pending");
        value["rollback_id"] = json!("RB-1");
        assert_eq!(parse(value, now).unwrap().action, DecisionAction::Deny);
    }

    #[test]
    fn rejects_unknown_action_expired_and_broad_target() {
        let now = Utc::now();
        assert_eq!(
            parse(decision("block_everything", now), now).unwrap_err(),
            DecisionError::Malformed
        );
        assert_eq!(
            parse(decision("allow", now - Duration::minutes(10)), now).unwrap_err(),
            DecisionError::Time
        );
        let mut value = decision("alert", now);
        value["target"]["route_template"] = json!("/*");
        assert_eq!(parse(value, now).unwrap_err(), DecisionError::Target);
    }
}
