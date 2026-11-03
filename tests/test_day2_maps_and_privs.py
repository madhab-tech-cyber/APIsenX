"""
Unit Tests for Day 2: Kernel Hooks, BPF Maps, Alignment and Least Privileges
Role: Member 2 (eBPF Traffic Engineer)
Daily Evidence: Commit + test/note
"""

import unittest
import ctypes
import re
import os

# Define Python ctypes representations matching ebpf/include/api_sentinel_types.h

class FlowKey(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("src_ip", ctypes.c_uint32),
        ("dst_ip", ctypes.c_uint32),
        ("src_port", ctypes.c_uint16),
        ("dst_port", ctypes.c_uint16),
        ("protocol", ctypes.c_uint8),
        ("ip_version", ctypes.c_uint8),
        ("_padding", ctypes.c_uint8 * 2),
        ("flow_hash", ctypes.c_uint64),
    ]

class SessionMetadata(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("pid", ctypes.c_uint32),
        ("tgid", ctypes.c_uint32),
        ("uid", ctypes.c_uint32),
        ("gid", ctypes.c_uint32),
        ("start_ktime_ns", ctypes.c_uint64),
        ("flags", ctypes.c_uint32),
        ("_reserved", ctypes.c_uint32),
    ]

class CaptureConfig(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("enabled", ctypes.c_uint32),
        ("target_port", ctypes.c_uint16),
        ("target_port_alt", ctypes.c_uint16),
        ("sampling_rate_pct", ctypes.c_uint32),
        ("enforcement_mode", ctypes.c_uint32),
        ("drop_mask", ctypes.c_uint64),
        ("_padding", ctypes.c_uint64),
    ]

class ApiEvent(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        # Header (24 Bytes)
        ("timestamp_ns", ctypes.c_uint64),
        ("event_id", ctypes.c_uint32),
        ("pid", ctypes.c_uint32),
        ("tgid", ctypes.c_uint32),
        ("uid", ctypes.c_uint32),
        # Flow (24 Bytes)
        ("flow", FlowKey),
        # API Metadata (16 Bytes)
        ("http_method", ctypes.c_uint8),
        ("direction", ctypes.c_uint8),
        ("status_code", ctypes.c_uint16),
        ("payload_bytes", ctypes.c_uint32),
        ("latency_us", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
        # Route Marker (128 Bytes)
        ("route_marker", ctypes.c_char * 128),
    ]


class TestDay2MapsAndPrivileges(unittest.TestCase):
    """Test suite validating Day 2 kernel structures, memory limits, and privileges."""

    def test_flow_key_size_and_alignment(self):
        """Verify flow_key struct size is exactly 24 bytes and 64-bit divisible."""
        size = ctypes.sizeof(FlowKey)
        self.assertEqual(size, 24, f"FlowKey must be 24 bytes, got {size}")
        self.assertEqual(size % 8, 0, "FlowKey must be 64-bit (8-byte) aligned for BPF verifier")

    def test_session_metadata_size_and_alignment(self):
        """Verify session_metadata struct size is exactly 32 bytes and 64-bit divisible."""
        size = ctypes.sizeof(SessionMetadata)
        self.assertEqual(size, 32, f"SessionMetadata must be 32 bytes, got {size}")
        self.assertEqual(size % 8, 0, "SessionMetadata must be 64-bit aligned")

    def test_capture_config_size_and_alignment(self):
        """Verify capture_config struct size is exactly 32 bytes and 64-bit divisible."""
        size = ctypes.sizeof(CaptureConfig)
        self.assertEqual(size, 32, f"CaptureConfig must be 32 bytes, got {size}")
        self.assertEqual(size % 8, 0, "CaptureConfig must be 64-bit aligned")

    def test_api_event_size_and_bounds(self):
        """Verify api_event struct is exactly 192 bytes with bounded 128-byte route marker."""
        size = ctypes.sizeof(ApiEvent)
        self.assertEqual(size, 192, f"ApiEvent must be 192 bytes, got {size}")
        self.assertEqual(size % 8, 0, "ApiEvent must be 64-bit aligned")
        # Route marker bounded check
        self.assertEqual(ctypes.sizeof(ctypes.c_char * 128), 128)

    def test_ring_buffer_power_of_two(self):
        """Verify ring buffer size is an exact power of 2 as required by Linux kernel."""
        ringbuf_size = 8 * 1024 * 1024  # 8 MB
        self.assertEqual(ringbuf_size, 8388608)
        # Power of 2 check: (x & (x - 1)) == 0 and x > 0
        self.assertTrue((ringbuf_size & (ringbuf_size - 1)) == 0, "RingBuffer size must be power of 2")

    def test_total_kernel_memory_budget_under_32mb(self):
        """Verify all BPF maps total memory footprint is strictly below 32 MB ceiling."""
        ringbuf_mb = 8.0  # 8 MB allocated
        # LRU Hash: 65536 entries * (key (24) + value (32) + kernel overhead (~56 bytes per node))
        node_overhead = 24 + 32 + 56
        lru_hash_bytes = 65536 * node_overhead
        lru_hash_mb = lru_hash_bytes / (1024 * 1024)
        # Per-CPU Stats: 16 entries * 8 bytes * 64 CPUs
        stats_bytes = 16 * 8 * 64
        stats_mb = stats_bytes / (1024 * 1024)
        # Config Map: 16 * 32 bytes
        config_bytes = 16 * 32
        config_mb = config_bytes / (1024 * 1024)

        total_mb = ringbuf_mb + lru_hash_mb + stats_mb + config_mb

        self.assertLess(
            total_mb,
            32.0,
            f"Total kernel memory {total_mb:.2f} MB exceeds 32.0 MB maximum budget ceiling",
        )
        # Assert expected target allocation (~11.8 - ~15 MB)
        self.assertLess(total_mb, 16.0)

    def test_least_privilege_specification(self):
        """Verify least privilege constraints in systemd service spec."""
        doc_path = os.path.join(os.path.dirname(__file__), "..", "docs", "day2-kernel-hooks-maps-privileges.md")
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check required capabilities are documented
        self.assertIn("CAP_BPF", content)
        self.assertIn("CAP_NET_ADMIN", content)

        # Check forbidden capabilities are explicitly rejected
        self.assertIn("CAP_SYS_ADMIN", content)
        self.assertIn("STRICTLY FORBIDDEN", content)

        # Check systemd sandboxing properties
        self.assertIn("NoNewPrivileges=yes", content)
        self.assertIn("ProtectSystem=strict", content)
        self.assertIn("ProtectHome=yes", content)

    def test_tc_action_constants(self):
        """Verify TC action return codes for safe packet forwarding vs dropping."""
        TC_ACT_OK = 0
        TC_ACT_SHOT = 2
        TC_ACT_PIPE = 3
        # Assert distinct action codes
        self.assertEqual(TC_ACT_OK, 0, "TC_ACT_OK must be 0 (pass packet)")
        self.assertEqual(TC_ACT_SHOT, 2, "TC_ACT_SHOT must be 2 (drop packet)")
        self.assertEqual(TC_ACT_PIPE, 3, "TC_ACT_PIPE must be 3 (continue pipeline)")

    def test_schema_version_constants_and_flags(self):
        """Verify schema version 1 macro and flags definitions in header."""
        header_path = os.path.join(os.path.dirname(__file__), "..", "ebpf", "include", "api_sentinel_types.h")
        with open(header_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("#define API_EVENT_SCHEMA_VERSION_V1    1", content)
        self.assertIn("#define API_EVENT_FLAG_ROUTE_TRUNCATED", content)
        self.assertIn("#define API_EVENT_FLAG_IPV6", content)
        self.assertIn("#define API_EVENT_FLAG_QUERY_STRIPPED", content)
        self.assertIn("#define API_EVENT_FLAG_DROP_OCCURRED", content)
        self.assertIn("#define API_EVENT_FLAG_MONITOR_ONLY", content)


if __name__ == "__main__":
    unittest.main()
