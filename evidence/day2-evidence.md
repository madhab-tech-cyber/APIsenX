# Day 2 Evidence: Kernel Hooks, BPF Maps & Least Privileges Specification

**Date:** Project Day 2  
**Member:** Member 2 (eBPF Traffic Engineer)  
**Assigned Task:** Document required kernel hooks, maps and least privileges.  
**Branch:** `member2/ebpf-capture`  
**Daily Evidence Requirement:** Commit + test/note  

---

## 1. Work Summary

1. **Kernel Hooks & Maps Specification (`docs/day2-kernel-hooks-maps-privileges.md`):**
   - Evaluated 5 hook types: TC (`clsact`), Socket Filter, SockOps, Syscall Tracepoints, Kprobes.
   - Selected TC ingress/egress as primary observation & enforcement hook (<15ns overhead, allows packet dropping via `TC_ACT_SHOT`).
   - Selected Syscall Tracepoints (`sys_enter_accept4`, `sys_enter_connect`) and SockOps for zero-fragility process identity correlation (PID, TGID, UID).
   - Designed 4 BPF maps (`api_sentinel_events` RingBuffer, `api_sentinel_sessions` LRU Hash, `api_sentinel_stats` Per-CPU Array, `api_sentinel_config` Array).
   - Total kernel memory across all maps bounded to **~11.8 MB**, well within the 32 MB budget ceiling.

2. **C Verifier-Compliant Header Definitions (`ebpf/include/`):**
   - `api_sentinel_types.h`: Defined 64-bit aligned structures (`flow_key`: 24B, `session_metadata`: 32B, `api_event`: 192B with 128B bounded route marker, `capture_config`: 32B).
   - `api_sentinel_maps.h`: BPF map definitions conforming to `libbpf` `SEC(".maps")` declarations.

3. **Least Privileges & Systemd Hardening Profile:**
   - Formalized minimal Linux capabilities: granted only `CAP_BPF` + `CAP_NET_ADMIN`.
   - Explicitly eliminated `CAP_SYS_ADMIN` and full root runtime access.
   - Designed drop-privilege lifecycle to switch user-space daemon to unprivileged user `apisentinel` (UID 998).
   - Created hardened `api-sentinel.service` profile with `NoNewPrivileges=yes`, `ProtectSystem=strict`, `ProtectHome=yes`, `PrivateTmp=yes`.

4. **Automated Verification Tests (`tests/test_day2_maps_and_privs.py` & `tests/test_security_rules.py`):**
   - Validated struct sizes, 64-bit alignment, power-of-2 ring buffer dimensions, and memory ceilings.
   - Automated security scanner verified zero leaked keys, secrets, tokens, or raw pcaps.
   - Total 18 tests passed in 0.048s.

---

## 2. Test Execution Output

```
test_full_prerequisite_audit_fail_on_missing_btf (test_day1_prerequisites.TestDay1Prerequisites.test_full_prerequisite_audit_fail_on_missing_btf) ... ok
test_full_prerequisite_audit_fail_on_old_kernel (test_day1_prerequisites.TestDay1Prerequisites.test_full_prerequisite_audit_fail_on_old_kernel) ... ok
test_full_prerequisite_audit_pass (test_day1_prerequisites.TestDay1Prerequisites.test_full_prerequisite_audit_pass) ... ok
test_kconfig_parsing_and_mandatory_checks (test_day1_prerequisites.TestDay1Prerequisites.test_kconfig_parsing_and_mandatory_checks) ... ok
test_kernel_version_parsing_invalid (test_day1_prerequisites.TestDay1Prerequisites.test_kernel_version_parsing_invalid) ... ok
test_kernel_version_parsing_valid (test_day1_prerequisites.TestDay1Prerequisites.test_kernel_version_parsing_valid) ... ok
test_kernel_version_threshold_evaluation (test_day1_prerequisites.TestDay1Prerequisites.test_kernel_version_threshold_evaluation) ... ok
test_api_event_size_and_bounds (test_day2_maps_and_privs.TestDay2MapsAndPrivileges.test_api_event_size_and_bounds) ... ok
test_capture_config_size_and_alignment (test_day2_maps_and_privs.TestDay2MapsAndPrivileges.test_capture_config_size_and_alignment) ... ok
test_flow_key_size_and_alignment (test_day2_maps_and_privs.TestDay2MapsAndPrivileges.test_flow_key_size_and_alignment) ... ok
test_least_privilege_specification (test_day2_maps_and_privs.TestDay2MapsAndPrivileges.test_least_privilege_specification) ... ok
test_ring_buffer_power_of_two (test_day2_maps_and_privs.TestDay2MapsAndPrivileges.test_ring_buffer_power_of_two) ... ok
test_session_metadata_size_and_alignment (test_day2_maps_and_privs.TestDay2MapsAndPrivileges.test_session_metadata_size_and_alignment) ... ok
test_tc_action_constants (test_day2_maps_and_privs.TestDay2MapsAndPrivileges.test_tc_action_constants) ... ok
test_total_kernel_memory_budget_under_32mb (test_day2_maps_and_privs.TestDay2MapsAndPrivileges.test_total_kernel_memory_budget_under_32mb) ... ok
test_gitignore_covers_sensitive_artifacts (test_security_rules.TestSecurityAndCompliance.test_gitignore_covers_sensitive_artifacts) ... ok
test_no_pcap_files_tracked (test_security_rules.TestSecurityAndCompliance.test_no_pcap_files_tracked) ... ok
test_zero_staged_secrets_or_private_keys (test_security_rules.TestSecurityAndCompliance.test_zero_staged_secrets_or_private_keys) ... ok

----------------------------------------------------------------------
Ran 18 tests in 0.048s

OK
```

---

## 3. Security Checklist Self-Audit (Day 2)

- [x] **No secrets or private keys staged:** Verified by `test_security_rules.py`.
- [x] **Least Privileges:** `CAP_BPF` and `CAP_NET_ADMIN` defined; `CAP_SYS_ADMIN` rejected.
- [x] **Safe inputs & bounds:** All struct sizes divisible by 8; route marker fixed to 128 bytes.
- [x] **Memory safety:** LRU hash table automatically limits kernel memory under DoS attack.
- [x] **Reproducible evidence:** Test run and verification logged in `day2-maps-privileges-test.log`.

---

## 4. Next Step Handoff

- **Day 3 Task:** Create Rust/eBPF workspace and minimal loadable program.
- **Handoff Target:** Member 3 (Collector Lead) has received `api_event` layout and RingBuffer specs.
