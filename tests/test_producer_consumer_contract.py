"""
Unit Tests for Producer/Consumer Contract (Member 2 Sensor <-> Member 3 Collector)
Role: Member 2 (eBPF Traffic Engineer)
Validates schema version, record size, field offsets, endianness, flags,
source/boot identity, sequence, and drop semantics.
"""

import unittest
import ctypes
import struct
import socket
import os
import sys

# Add scripts directory to path for IngestContractValidator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from collector_test_harness import (
    IngestContractValidator,
    WIRE_RECORD_SIZE,
    EXPECTED_SCHEMA_VERSION,
    FLAG_ROUTE_TRUNCATED,
    FLAG_IPV6,
    FLAG_QUERY_STRIPPED,
    FLAG_DROP_OCCURRED,
    FLAG_MONITOR_ONLY,
)

# C-type definitions matching ebpf/include/api_sentinel_types.h
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

class ApiEvent(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("timestamp_ns", ctypes.c_uint64),
        ("event_id", ctypes.c_uint32),
        ("pid", ctypes.c_uint32),
        ("tgid", ctypes.c_uint32),
        ("uid", ctypes.c_uint32),
        ("flow", FlowKey),
        ("http_method", ctypes.c_uint8),
        ("direction", ctypes.c_uint8),
        ("status_code", ctypes.c_uint16),
        ("payload_bytes", ctypes.c_uint32),
        ("latency_us", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
        ("route_marker", ctypes.c_char * 128),
    ]


class TestProducerConsumerContract(unittest.TestCase):
    """Rigorous contract verification between Member 2 (Sensor) and Member 3 (Collector)."""

    def setUp(self):
        self.validator = IngestContractValidator()

    def test_record_size_is_strictly_192_bytes(self):
        """Contract requirement: Record size must be exactly 192 bytes."""
        ctypes_size = ctypes.sizeof(ApiEvent)
        self.assertEqual(ctypes_size, 192, f"ApiEvent ctypes size must be 192 bytes, got {ctypes_size}")
        self.assertEqual(WIRE_RECORD_SIZE, 192, f"Wire record size must be 192 bytes, got {WIRE_RECORD_SIZE}")
        self.assertEqual(ctypes_size % 8, 0, "Wire record must be 64-bit aligned for kernel ring buffer")

    def test_exact_field_offsets(self):
        """Contract requirement: Exact field offsets must match between producer and consumer."""
        expected_offsets = {
            "timestamp_ns": 0,
            "event_id": 8,
            "pid": 12,
            "tgid": 16,
            "uid": 20,
            "flow": 24,
            "http_method": 48,
            "direction": 49,
            "status_code": 50,
            "payload_bytes": 52,
            "latency_us": 56,
            "flags": 60,
            "route_marker": 64,
        }

        for field_name, expected_offset in expected_offsets.items():
            actual_offset = getattr(ApiEvent, field_name).offset
            self.assertEqual(
                actual_offset,
                expected_offset,
                f"Field offset mismatch for '{field_name}': expected {expected_offset}, got {actual_offset}"
            )

        # Verify internal flow_key offsets relative to struct start
        flow_offsets = {
            "src_ip": 24,
            "dst_ip": 28,
            "src_port": 32,
            "dst_port": 34,
            "protocol": 36,
            "ip_version": 37,
            "_padding": 38,
            "flow_hash": 40,
        }
        for field_name, expected_abs_offset in flow_offsets.items():
            rel_offset = getattr(FlowKey, field_name).offset
            abs_offset = getattr(ApiEvent, "flow").offset + rel_offset
            self.assertEqual(
                abs_offset,
                expected_abs_offset,
                f"FlowKey field '{field_name}' absolute offset mismatch: expected {expected_abs_offset}, got {abs_offset}"
            )

    def test_schema_version_packing_and_extraction(self):
        """Contract requirement: Schema version must be version 1 encoded in flags high byte."""
        raw_flags = (EXPECTED_SCHEMA_VERSION << 24) | FLAG_MONITOR_ONLY
        extracted_version = (raw_flags >> 24) & 0xFF
        self.assertEqual(extracted_version, 1, "Schema version must be 1")

        # Create synthetic valid event
        event = ApiEvent()
        event.timestamp_ns = 1000000000
        event.event_id = 1
        event.flags = raw_flags
        event.flow.src_port = socket.htons(8080)
        event.flow.dst_port = socket.htons(80)
        event.route_marker = b"/api/v1/orders"

        raw_bytes = bytes(event)
        decoded = self.validator.decode_raw_event(raw_bytes)
        self.assertEqual(decoded["schema_version"], 1)
        self.assertTrue(decoded["flags"]["monitor_only"])
        self.assertEqual(decoded["route_marker"], "/api/v1/orders")

    def test_endianness_conversion_network_vs_host(self):
        """
        Contract requirement: Verify network byte order (Big Endian) for ports and IPs,
        and host byte order for timestamps and counters.
        """
        event = ApiEvent()
        # Source port = 8080 (0x1F90). In network byte order (BE), bytes are [0x1F, 0x90]
        event.flow.src_port = socket.htons(8080)
        # Dest port = 80 (0x0050). In network byte order (BE), bytes are [0x00, 0x50]
        event.flow.dst_port = socket.htons(80)
        event.flags = (1 << 24)

        raw_bytes = bytes(event)

        # Dest port is at offset 34 (2 bytes)
        raw_dst_port_bytes = raw_bytes[34:36]
        self.assertEqual(raw_dst_port_bytes, b"\x00\x50", "Port 80 must be stored in Big Endian (Network Order) [0x00, 0x50]")

        # If a naive consumer reads offset 34 as Little Endian, it would get 0x5000 = 20480
        naive_le_port = struct.unpack("<H", raw_dst_port_bytes)[0]
        self.assertEqual(naive_le_port, 20480, "Demonstrating naive Little Endian read produces corrupt port 20480")

        # The contract validator properly performs ntohs and gets 80
        decoded = self.validator.decode_raw_event(raw_bytes)
        self.assertEqual(decoded["flow"]["dst_port"], 80, "Validator must decode dst_port as 80 using ntohs")
        self.assertEqual(decoded["flow"]["src_port"], 8080, "Validator must decode src_port as 8080 using ntohs")

    def test_sequence_monotonicity_and_loss_detection(self):
        """Contract requirement: Monotonic sequence counter and drop gap detection."""
        def make_event(seq_id):
            e = ApiEvent()
            e.event_id = seq_id
            e.flags = (1 << 24)
            e.route_marker = b"/api/v1/status"
            return bytes(e)

        # Send event 1 and 2 (no drops)
        d1 = self.validator.decode_raw_event(make_event(1))
        self.assertEqual(d1["dropped_in_gap"], 0)

        d2 = self.validator.decode_raw_event(make_event(2))
        self.assertEqual(d2["dropped_in_gap"], 0)

        # Send event 5 (events 3 and 4 were dropped due to ring buffer pressure)
        d5 = self.validator.decode_raw_event(make_event(5))
        self.assertEqual(d5["dropped_in_gap"], 2, "Must detect gap of 2 dropped events")
        self.assertEqual(self.validator.total_drops, 2)

    def test_sequence_wraparound_is_handled_modulo_32_bits(self):
        """The 32-bit wire sequence may wrap; wrap itself is not a loss."""
        def make_event(seq_id):
            event = ApiEvent()
            event.event_id = seq_id
            event.flags = (1 << 24) | FLAG_MONITOR_ONLY
            event.flow.ip_version = 4
            event.route_marker = b"/api/v1/status"
            return bytes(event)

        self.validator.decode_raw_event(make_event(0xFFFFFFFE))
        self.assertEqual(
            self.validator.decode_raw_event(make_event(0xFFFFFFFF))["dropped_in_gap"], 0
        )
        self.assertEqual(
            self.validator.decode_raw_event(make_event(0))["dropped_in_gap"], 0
        )
        self.assertEqual(self.validator.total_drops, 0)

        # One missing ID across wrap is reported as one diagnostic gap.
        self.validator = IngestContractValidator()
        self.validator.decode_raw_event(make_event(0xFFFFFFFE))
        decoded = self.validator.decode_raw_event(make_event(0))
        self.assertEqual(decoded["dropped_in_gap"], 1)
        self.assertEqual(self.validator.total_drops, 1)

    def test_rejection_of_incompatible_schema_version(self):
        """Contract requirement: Reject events with schema version != 1."""
        event = ApiEvent()
        event.flags = (2 << 24)  # Schema version 2 (unsupported)

        with self.assertRaises(ValueError) as ctx:
            self.validator.decode_raw_event(bytes(event))
        self.assertIn("Incompatible schema version", str(ctx.exception))
        self.assertEqual(self.validator.schema_violations, 1)

    def test_rejection_of_corrupt_record_size(self):
        """Contract requirement: Reject events with size != 192 bytes."""
        with self.assertRaises(ValueError) as ctx:
            self.validator.decode_raw_event(b"\x00" * 128)
        self.assertIn("Record size mismatch", str(ctx.exception))

    def test_privacy_boundary_query_stripping_enforcement(self):
        """Contract requirement: Collector strictly rejects raw query parameters in route."""
        event = ApiEvent()
        event.flags = (1 << 24)
        event.route_marker = b"/api/v1/users?token=secret123"

        with self.assertRaises(ValueError) as ctx:
            self.validator.decode_raw_event(bytes(event))
        self.assertIn("Privacy boundary failure", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
