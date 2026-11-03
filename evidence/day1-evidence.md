# Day 1 Evidence: Prerequisites Verification & Capture Design Note

**Date:** Project Day 1  
**Member:** Member 2 (eBPF Traffic Engineer)  
**Assigned Task:** Verify Linux/eBPF prerequisites and create capture design note.  
**Branch:** `member2/ebpf-capture`  
**Daily Evidence Requirement:** Commit + test/note  

---

## 1. Work Summary

1. **Capture Design Note (`docs/day1-capture-design-note.md`):**
   - Defined core observation mission: low-overhead, kernel-space API metadata telemetry.
   - Formalized approved metadata boundary (L4 5-tuple, process ID/UID, method token, route marker, status, length).
   - Enforced strict privacy rule: zero extraction of credentials, authorization headers, or request/response bodies.
   - Documented encrypted traffic (TLS) boundaries and rationale for not weakening TLS or injecting MITM certs.
   - Selected BPF RingBuffer (`BPF_MAP_TYPE_RINGBUF`) over Perf Buffers (32x memory reduction, ordered events, atomic drop tracking).

2. **Prerequisites Auditor (`scripts/check_prereqs.py` & `scripts/check_prereqs.sh`):**
   - Automated checks for Kernel version (>= 5.8.0 minimum, >= 5.15.0 LTS recommended).
   - Automated verification for required kernel options (`CONFIG_BPF=y`, `CONFIG_BPF_SYSCALL=y`, `CONFIG_BPF_JIT=y`, `CONFIG_DEBUG_INFO_BTF=y`, `CONFIG_NET_CLS_ACT=y`, `CONFIG_NET_CLS_BPF=y`).
   - BTF / CO-RE support check for portable bytecode.

3. **Test Suite Execution (`tests/test_day1_prerequisites.py`):**
   - 7 unit tests verifying parsing, validation, threshold checks, and failure handling.
   - Result: 7/7 tests passed.

---

## 2. Test Execution Output

```
test_full_prerequisite_audit_fail_on_missing_btf (tests.test_day1_prerequisites.TestDay1Prerequisites.test_full_prerequisite_audit_fail_on_missing_btf)
Verify audit failure when BTF support is missing. ... ok
test_full_prerequisite_audit_fail_on_old_kernel (tests.test_day1_prerequisites.TestDay1Prerequisites.test_full_prerequisite_audit_fail_on_old_kernel)
Verify audit failure when kernel version is below 5.8 (no ringbuffer). ... ok
test_full_prerequisite_audit_pass (tests.test_day1_prerequisites.TestDay1Prerequisites.test_full_prerequisite_audit_pass)
Verify end-to-end prerequisite audit pass on target environment. ... ok
test_kconfig_parsing_and_mandatory_checks (tests.test_day1_prerequisites.TestDay1Prerequisites.test_kconfig_parsing_and_mandatory_checks)
Verify detection of compliant and missing kernel configuration flags. ... ok
test_kernel_version_parsing_invalid (tests.test_day1_prerequisites.TestDay1Prerequisites.test_kernel_version_parsing_invalid)
Verify error handling on malformed kernel version strings. ... ok
test_kernel_version_parsing_valid (tests.test_day1_prerequisites.TestDay1Prerequisites.test_kernel_version_parsing_valid)
Verify proper parsing of various kernel version strings. ... ok
test_kernel_version_threshold_evaluation (tests.test_day1_prerequisites.TestDay1Prerequisites.test_kernel_version_threshold_evaluation)
Verify evaluation of minimum (5.8.0) and recommended (5.15.0) versions. ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.069s

OK
```

---

## 3. Security Checklist Self-Audit (Day 1)

- [x] No secret, token, password, private key, personal data or sensitive capture is staged.
- [x] Inputs, errors and logs are safe for this component.
- [x] Design excludes payload bodies and authorization headers from observation buffers.
- [x] Tests cover allowed, denied, and malformed kernel configurations.
- [x] Dependencies and requirements strictly limited to approved least-privilege interfaces.

---

## 4. Next Step Handoff

- **Day 2 Task:** Document required kernel hooks, maps, and least privileges (`CAP_BPF`, `CAP_NET_ADMIN`).
