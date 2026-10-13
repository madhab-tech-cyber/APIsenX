"""
Unit Tests for Day 1: Linux/eBPF Prerequisites Verification
Role: Member 2 (eBPF Traffic Engineer)
Daily Evidence: Commit + test/note
"""

import unittest
import sys
import os

# Add scripts directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from check_prereqs import (
    parse_kernel_version,
    evaluate_kernel_version,
    parse_kconfig_content,
    evaluate_kconfigs,
    run_prerequisite_audit,
    MIN_KERNEL_VERSION,
    RECOMMENDED_KERNEL_VERSION,
)


class TestDay1Prerequisites(unittest.TestCase):
    """Test suite for Day 1 prerequisites auditor and capture design compliance."""

    def test_kernel_version_parsing_valid(self):
        """Verify proper parsing of various kernel version strings."""
        self.assertEqual(parse_kernel_version("5.15.0-89-generic"), (5, 15, 0))
        self.assertEqual(parse_kernel_version("6.2.16-custom"), (6, 2, 16))
        self.assertEqual(parse_kernel_version("5.8.0"), (5, 8, 0))
        self.assertEqual(parse_kernel_version("4.19.128-microsoft-standard"), (4, 19, 128))

    def test_kernel_version_parsing_invalid(self):
        """Verify error handling on malformed kernel version strings."""
        with self.assertRaises(ValueError):
            parse_kernel_version("invalid-version-string")

    def test_kernel_version_threshold_evaluation(self):
        """Verify evaluation of minimum (5.8.0) and recommended (5.15.0) versions."""
        # Obsolete kernel (< 5.8.0)
        res_old = evaluate_kernel_version((4, 19, 0))
        self.assertFalse(res_old["meets_minimum"])
        self.assertFalse(res_old["meets_recommended"])
        self.assertEqual(res_old["status"], "NON_COMPLIANT")

        # Minimum supported kernel (5.8.0)
        res_min = evaluate_kernel_version((5, 8, 0))
        self.assertTrue(res_min["meets_minimum"])
        self.assertFalse(res_min["meets_recommended"])
        self.assertEqual(res_min["status"], "COMPLIANT")

        # Recommended production kernel (5.15.0)
        res_rec = evaluate_kernel_version((5, 15, 0))
        self.assertTrue(res_rec["meets_minimum"])
        self.assertTrue(res_rec["meets_recommended"])
        self.assertEqual(res_rec["status"], "OPTIMAL")

        # Modern kernel (6.5.0)
        res_modern = evaluate_kernel_version((6, 5, 0))
        self.assertTrue(res_modern["meets_minimum"])
        self.assertTrue(res_modern["meets_recommended"])
        self.assertEqual(res_modern["status"], "OPTIMAL")

    def test_kconfig_parsing_and_mandatory_checks(self):
        """Verify detection of compliant and missing kernel configuration flags."""
        sample_compliant_kconfig = """
        CONFIG_BPF=y
        CONFIG_BPF_SYSCALL=y
        CONFIG_BPF_JIT=y
        CONFIG_DEBUG_INFO_BTF=y
        CONFIG_NET_CLS_ACT=y
        CONFIG_NET_CLS_BPF=y
        CONFIG_BPF_JIT_ALWAYS_ON=y
        CONFIG_NET_SCH_INGRESS=y
        """
        parsed = parse_kconfig_content(sample_compliant_kconfig)
        evaluation = evaluate_kconfigs(parsed)
        self.assertTrue(evaluation["passed"])
        self.assertEqual(len(evaluation["missing_mandatory"]), 0)

        # Deficient config (missing CONFIG_DEBUG_INFO_BTF and CONFIG_BPF_SYSCALL)
        deficient_kconfig = """
        CONFIG_BPF=y
        CONFIG_BPF_JIT=y
        CONFIG_NET_CLS_ACT=y
        """
        parsed_def = parse_kconfig_content(deficient_kconfig)
        eval_def = evaluate_kconfigs(parsed_def)
        self.assertFalse(eval_def["passed"])
        self.assertIn("CONFIG_DEBUG_INFO_BTF", eval_def["missing_mandatory"])
        self.assertIn("CONFIG_BPF_SYSCALL", eval_def["missing_mandatory"])

    def test_full_prerequisite_audit_pass(self):
        """Verify end-to-end prerequisite audit pass on target environment."""
        report = run_prerequisite_audit(
            kernel_version_override="5.15.0-generic",
            mock_btf=True,
        )
        self.assertTrue(report["audit_passed"])
        self.assertEqual(report["checks"]["kernel_version"]["status"], "OPTIMAL")
        self.assertEqual(report["checks"]["btf_support"]["status"], "PASS")
        self.assertEqual(report["checks"]["ring_buffer_support"]["status"], "PASS")

    def test_full_prerequisite_audit_fail_on_old_kernel(self):
        """Verify audit failure when kernel version is below 5.8 (no ringbuffer)."""
        report = run_prerequisite_audit(
            kernel_version_override="4.19.0-lts",
            mock_btf=True,
        )
        self.assertFalse(report["audit_passed"])
        self.assertEqual(report["checks"]["kernel_version"]["status"], "NON_COMPLIANT")
        self.assertEqual(report["checks"]["ring_buffer_support"]["status"], "FAIL")

    def test_full_prerequisite_audit_fail_on_missing_btf(self):
        """Verify audit failure when BTF support is missing."""
        report = run_prerequisite_audit(
            kernel_version_override="5.15.0-generic",
            mock_btf=False,
        )
        self.assertFalse(report["audit_passed"])
        self.assertEqual(report["checks"]["btf_support"]["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
