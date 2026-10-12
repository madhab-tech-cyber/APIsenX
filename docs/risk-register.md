# Risk Register

| ID | Risk | Severity | Owner | Mitigation | Evidence | Status |
|---|---|---|---|---|---|---|
| R-001 | Sensitive data captured or logged | High | M1/M2/M4/M6 | Data minimisation, masking, leak tests, retention | Pending | Open |
| R-002 | Incorrect BOLA decision | High | M1/M4/M5 | Explicit policy matrix, labelled fixtures, negative tests | Pending | Open |
| R-003 | False-positive block causes outage | High | M1/M3 | Detection-only mode, review, rollback, failure tests | Pending | Open |
| R-004 | eBPF privilege misuse | High | M1/M2 | Minimum capabilities, verifier, bounds and stress tests | Pending | Open |
| R-005 | Vulnerable dependency | High | M1/M6 | Lock files, update automation, SBOM and scans | Pending | Open |
| R-006 | HTTPS observation assumption is invalid | Medium | M1/M2/M5 | Approved observation point and documented limitation | Pending | Open |

Update this table whenever a design, dependency, interface, test result, or security finding changes the risk.

