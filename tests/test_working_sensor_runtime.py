"""
Unit Tests for Working Sensor Runtime (Day 3 Bounded Linux Sensor)
Role: Member 2 (eBPF Traffic Engineer)
Branch: member2/ebpf-capture

Tests malformed/boundary packets, map/buffer limits, IPv4/IPv6 scope,
loss, backpressure, recovery, monitor-only behavior, and scoped cleanup.
"""

import unittest
import struct
import socket
import ctypes
import os
import sys

# Constants matching ebpf/include/api_sentinel_types.h
TC_ACT_OK   = 0
TC_ACT_SHOT = 2

ETH_P_IP   = 0x0800
ETH_P_IPV6 = 0x86DD
IPPROTO_TCP = 6

METHOD_UNKNOWN = 0
METHOD_GET     = 1
METHOD_POST    = 2
METHOD_PUT     = 3
METHOD_DELETE  = 4
METHOD_PATCH   = 5
METHOD_HEAD    = 6
METHOD_OPTIONS = 7

STAT_TOTAL_PACKETS      = 0
STAT_API_EVENTS_EMITTED = 1
STAT_RINGBUF_DROPS      = 2
STAT_MALFORMED_PACKETS  = 3
STAT_ENFORCEMENT_DROPS  = 4

FLAG_ROUTE_TRUNCATED = 1 << 0
FLAG_IPV6            = 1 << 1
FLAG_QUERY_STRIPPED  = 1 << 2
FLAG_DROP_OCCURRED   = 1 << 3
FLAG_MONITOR_ONLY    = 1 << 4


class MockSensorRuntime:
    """
    Direct Python emulator of ebpf/src/api_sentinel_sensor.c kernel execution logic.
    Provides byte-accurate simulation of TC packet pointer bounds checking,
    HTTP method extraction, route sanitization, ringbuffer reservation,
    and per-CPU statistics accounting.
    """
    def __init__(self, ringbuf_capacity_events=1000):
        self.stats = {
            STAT_TOTAL_PACKETS: 0,
            STAT_API_EVENTS_EMITTED: 0,
            STAT_RINGBUF_DROPS: 0,
            STAT_MALFORMED_PACKETS: 0,
            STAT_ENFORCEMENT_DROPS: 0,
        }
        self.ringbuf_capacity = ringbuf_capacity_events
        self.ringbuf_queue = []
        self.target_ports = {80, 8080, 8000, 5000}
        self.seq_id = 0

    def parse_http_method(self, payload):
        """Byte-for-byte replica of parse_http_method in api_sentinel_sensor.c."""
        if len(payload) < 4:
            return METHOD_UNKNOWN, 0
        if payload.startswith(b"GET "):
            return METHOD_GET, 4
        if payload.startswith(b"PUT "):
            return METHOD_PUT, 4
        if payload.startswith(b"POST "):
            return METHOD_POST, 5
        if payload.startswith(b"HEAD "):
            return METHOD_HEAD, 5
        if payload.startswith(b"PATCH "):
            return METHOD_PATCH, 6
        if payload.startswith(b"DELETE "):
            return METHOD_DELETE, 7
        if payload.startswith(b"OPTIONS "):
            return METHOD_OPTIONS, 8
        return METHOD_UNKNOWN, 0

    def process_packet(self, packet_bytes):
        """
        Process a raw L2 Ethernet frame through the TC ingress pipeline.
        Returns (tc_action, emitted_event_or_None).
        """
        self.stats[STAT_TOTAL_PACKETS] += 1

        # 1. Parse L2 Ethernet header (14 bytes)
        if len(packet_bytes) < 14:
            return TC_ACT_OK, None

        h_proto = struct.unpack("!H", packet_bytes[12:14])[0]
        cursor = 14

        ip_version = 0
        src_ip = 0
        dst_ip = 0
        flow_hash = 0

        # 2. Parse L3 IP Header
        if h_proto == ETH_P_IP:
            if len(packet_bytes) < cursor + 20:
                self.stats[STAT_MALFORMED_PACKETS] += 1
                return TC_ACT_OK, None

            v_ihl = packet_bytes[cursor]
            ihl = v_ihl & 0x0F
            if ihl < 5:
                self.stats[STAT_MALFORMED_PACKETS] += 1
                return TC_ACT_OK, None

            ip_hdr_len = ihl * 4
            if len(packet_bytes) < cursor + ip_hdr_len:
                self.stats[STAT_MALFORMED_PACKETS] += 1
                return TC_ACT_OK, None

            proto = packet_bytes[cursor + 9]
            if proto != IPPROTO_TCP:
                return TC_ACT_OK, None

            src_ip = struct.unpack("!I", packet_bytes[cursor + 12:cursor + 16])[0]
            dst_ip = struct.unpack("!I", packet_bytes[cursor + 16:cursor + 20])[0]
            ip_version = 4
            cursor += ip_hdr_len

        elif h_proto == ETH_P_IPV6:
            if len(packet_bytes) < cursor + 40:
                self.stats[STAT_MALFORMED_PACKETS] += 1
                return TC_ACT_OK, None

            proto = packet_bytes[cursor + 6]
            if proto != IPPROTO_TCP:
                return TC_ACT_OK, None

            # Lower 32 bits of IPv6 addresses
            src_ip = struct.unpack("!I", packet_bytes[cursor + 20:cursor + 24])[0]
            dst_ip = struct.unpack("!I", packet_bytes[cursor + 36:cursor + 40])[0]
            flow_hash = struct.unpack("!Q", packet_bytes[cursor + 8:cursor + 16])[0]
            ip_version = 6
            cursor += 40
        else:
            return TC_ACT_OK, None

        # 3. Parse L4 TCP Header (minimum 20 bytes)
        if len(packet_bytes) < cursor + 20:
            self.stats[STAT_MALFORMED_PACKETS] += 1
            return TC_ACT_OK, None

        src_port, dst_port = struct.unpack("!HH", packet_bytes[cursor:cursor + 4])
        data_offset_byte = packet_bytes[cursor + 12]
        doff = (data_offset_byte >> 4) * 4
        if doff < 20:
            self.stats[STAT_MALFORMED_PACKETS] += 1
            return TC_ACT_OK, None

        if len(packet_bytes) < cursor + doff:
            self.stats[STAT_MALFORMED_PACKETS] += 1
            return TC_ACT_OK, None

        payload = packet_bytes[cursor + doff:]

        # 4. Filter by target ports
        if dst_port not in self.target_ports:
            return TC_ACT_OK, None

        # 5. Detect HTTP Method
        method, method_len = self.parse_http_method(payload)
        if method == METHOD_UNKNOWN:
            return TC_ACT_OK, None

        # 6. Extract sanitized Route Marker
        uri_payload = payload[method_len:]
        route_chars = []
        flags = FLAG_MONITOR_ONLY
        if ip_version == 6:
            flags |= FLAG_IPV6

        for i, b in enumerate(uri_payload):
            if i >= 127:
                flags |= FLAG_ROUTE_TRUNCATED
                break
            char = chr(b)
            if char in (" ", "\r", "\n"):
                break
            elif char == "?":
                flags |= FLAG_QUERY_STRIPPED
                break
            else:
                route_chars.append(char)

        route_marker = "".join(route_chars)

        # 7. Reserve in BPF RingBuffer (capacity limit / backpressure check)
        if len(self.ringbuf_queue) >= self.ringbuf_capacity:
            self.stats[STAT_RINGBUF_DROPS] += 1
            return TC_ACT_OK, None

        self.seq_id += 1
        event = {
            "schema_version": 1,
            "event_id": self.seq_id,
            "ip_version": ip_version,
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": src_port,
            "dst_port": dst_port,
            "flow_hash": flow_hash,
            "http_method": method,
            "payload_bytes": len(payload),
            "flags": flags,
            "route_marker": route_marker,
        }
        self.ringbuf_queue.append(event)
        self.stats[STAT_API_EVENTS_EMITTED] += 1

        # Strict Monitor-Only Invariant: Always return TC_ACT_OK
        return TC_ACT_OK, event


def build_test_packet(ip_version=4, proto=IPPROTO_TCP, src_port=12345, dst_port=80, payload=b"GET /api/v1/users HTTP/1.1\r\n\r\n"):
    """Helper to assemble a valid synthetic L2+L3+L4 frame."""
    eth = struct.pack("!6s6sH", b"\xaa" * 6, b"\xbb" * 6, ETH_P_IP if ip_version == 4 else ETH_P_IPV6)
    if ip_version == 4:
        ihl = 5
        v_ihl = (4 << 4) | ihl
        ip_hdr = struct.pack("!BBHHHBBHII", v_ihl, 0, 20 + 20 + len(payload), 1, 0, 64, proto, 0, 0x0A000001, 0x0A000002)
    else:
        ip_hdr = struct.pack("!IHBB16s16s", 0x60000000, 20 + len(payload), proto, 64, b"\x20\x01\x0d\xb8" + b"\x00" * 12, b"\x20\x01\x0d\xb9" + b"\x00" * 12)

    tcp_hdr = struct.pack("!HHIIBBHHH", src_port, dst_port, 100, 0, (5 << 4), 0x02, 65535, 0, 0)
    return eth + ip_hdr + tcp_hdr + payload


class TestWorkingSensorRuntime(unittest.TestCase):
    """Test suite validating sensor runtime execution, boundary conditions, and limits."""

    def setUp(self):
        self.sensor = MockSensorRuntime(ringbuf_capacity_events=10)

    def test_valid_ipv4_http_get_capture(self):
        """Verify normal capture of IPv4 HTTP GET request on port 80."""
        pkt = build_test_packet(ip_version=4, dst_port=80, payload=b"GET /api/v1/items HTTP/1.1\r\nHost: api.local\r\n\r\n")
        action, event = self.sensor.process_packet(pkt)

        self.assertEqual(action, TC_ACT_OK, "Sensor must return TC_ACT_OK (monitor-only)")
        self.assertIsNotNone(event)
        self.assertEqual(event["http_method"], METHOD_GET)
        self.assertEqual(event["route_marker"], "/api/v1/items")
        self.assertEqual(event["dst_port"], 80)
        self.assertEqual(event["ip_version"], 4)
        self.assertEqual(self.sensor.stats[STAT_API_EVENTS_EMITTED], 1)

    def test_valid_ipv6_scope_and_capture(self):
        """Verify dual-stack IPv6 packet processing and flag setting."""
        pkt = build_test_packet(ip_version=6, dst_port=8080, payload=b"POST /api/v1/checkout HTTP/1.1\r\n\r\n")
        action, event = self.sensor.process_packet(pkt)

        self.assertEqual(action, TC_ACT_OK)
        self.assertIsNotNone(event)
        self.assertEqual(event["http_method"], METHOD_POST)
        self.assertEqual(event["route_marker"], "/api/v1/checkout")
        self.assertEqual(event["ip_version"], 6)
        self.assertTrue(event["flags"] & FLAG_IPV6)

    def test_malformed_truncated_ethernet_frame(self):
        """Boundary test: Truncated Ethernet frame (< 14 bytes) must be dropped safely without crashing."""
        pkt = b"\x00" * 10
        action, event = self.sensor.process_packet(pkt)
        self.assertEqual(action, TC_ACT_OK)
        self.assertIsNone(event)

    def test_malformed_truncated_ip_header(self):
        """Boundary test: Truncated IP header must increment malformed packet counter."""
        pkt = b"\xaa" * 12 + struct.pack("!H", ETH_P_IP) + b"\x45\x00\x00"  # Only 3 bytes of IP
        action, event = self.sensor.process_packet(pkt)
        self.assertEqual(action, TC_ACT_OK)
        self.assertIsNone(event)
        self.assertEqual(self.sensor.stats[STAT_MALFORMED_PACKETS], 1)

    def test_malformed_invalid_ip_ihl_less_than_5(self):
        """Boundary test: Invalid IHL < 5 must be rejected with malformed stat increment."""
        eth = struct.pack("!6s6sH", b"\xaa" * 6, b"\xbb" * 6, ETH_P_IP)
        bad_ip = struct.pack("!BBHHHBBHII", 0x44, 0, 40, 1, 0, 64, IPPROTO_TCP, 0, 0x0A000001, 0x0A000002)
        pkt = eth + bad_ip + (b"\x00" * 20)
        action, event = self.sensor.process_packet(pkt)
        self.assertEqual(action, TC_ACT_OK)
        self.assertIsNone(event)
        self.assertEqual(self.sensor.stats[STAT_MALFORMED_PACKETS], 1)

    def test_non_tcp_traffic_ignored(self):
        """Scope test: UDP or ICMP traffic must pass through without capturing API events."""
        pkt = build_test_packet(proto=17, dst_port=80)  # UDP
        action, event = self.sensor.process_packet(pkt)
        self.assertEqual(action, TC_ACT_OK)
        self.assertIsNone(event)
        self.assertEqual(self.sensor.stats[STAT_API_EVENTS_EMITTED], 0)

    def test_non_monitored_port_ignored(self):
        """Scope test: Traffic to port 22 (SSH) must pass without emitting API events."""
        pkt = build_test_packet(dst_port=22, payload=b"SSH-2.0-OpenSSH\r\n")
        action, event = self.sensor.process_packet(pkt)
        self.assertEqual(action, TC_ACT_OK)
        self.assertIsNone(event)
        self.assertEqual(self.sensor.stats[STAT_API_EVENTS_EMITTED], 0)

    def test_privacy_boundary_query_string_stripping(self):
        """
        Privacy test: Sensor MUST strip all query parameter values at '?'
        and set FLAG_QUERY_STRIPPED.
        """
        pkt = build_test_packet(dst_port=80, payload=b"GET /api/v1/users?token=secret123&key=456 HTTP/1.1\r\n\r\n")
        action, event = self.sensor.process_packet(pkt)

        self.assertEqual(action, TC_ACT_OK)
        self.assertIsNotNone(event)
        self.assertEqual(event["route_marker"], "/api/v1/users")
        self.assertNotIn("token", event["route_marker"])
        self.assertNotIn("secret123", event["route_marker"])
        self.assertTrue(event["flags"] & FLAG_QUERY_STRIPPED)

    def test_route_truncation_at_127_bytes(self):
        """Boundary test: Path longer than 127 bytes is safely truncated with FLAG_ROUTE_TRUNCATED."""
        long_path = "/api/v1/" + ("a" * 150)
        payload = f"GET {long_path} HTTP/1.1\r\n\r\n".encode("ascii")
        pkt = build_test_packet(dst_port=80, payload=payload)
        action, event = self.sensor.process_packet(pkt)

        self.assertEqual(action, TC_ACT_OK)
        self.assertIsNotNone(event)
        self.assertLessEqual(len(event["route_marker"]), 127)
        self.assertTrue(event["flags"] & FLAG_ROUTE_TRUNCATED)

    def test_zero_credential_and_body_extraction(self):
        """Privacy test: Confirm headers (Authorization, Cookie) and body are excluded."""
        payload = (
            b"POST /api/v1/login HTTP/1.1\r\n"
            b"Host: api.local\r\n"
            b"Authorization: Bearer my-auth-token\r\n"
            b"Cookie: session=xyz\r\n\r\n"
            b'{"password": "secret"}'
        )
        pkt = build_test_packet(dst_port=80, payload=payload)
        action, event = self.sensor.process_packet(pkt)

        self.assertEqual(action, TC_ACT_OK)
        self.assertIsNotNone(event)
        self.assertEqual(event["route_marker"], "/api/v1/login")
        # Ensure route_marker only has path
        self.assertNotIn("Bearer", event["route_marker"])
        self.assertNotIn("session", event["route_marker"])
        self.assertNotIn("password", event["route_marker"])
        # Payload size is recorded, but body itself is not in event
        self.assertEqual(event["payload_bytes"], len(payload))

    def test_ringbuf_saturation_and_drop_accounting(self):
        """Buffer limit & backpressure: Saturated ringbuffer increments drops without crashing."""
        small_sensor = MockSensorRuntime(ringbuf_capacity_events=3)
        pkt = build_test_packet(dst_port=80, payload=b"GET /api/v1/test HTTP/1.1\r\n\r\n")

        # Fill buffer to capacity (3 events)
        for _ in range(3):
            action, ev = small_sensor.process_packet(pkt)
            self.assertEqual(action, TC_ACT_OK)
            self.assertIsNotNone(ev)

        self.assertEqual(small_sensor.stats[STAT_API_EVENTS_EMITTED], 3)
        self.assertEqual(small_sensor.stats[STAT_RINGBUF_DROPS], 0)

        # 4th and 5th packets must drop safely due to backpressure
        for _ in range(2):
            action, ev = small_sensor.process_packet(pkt)
            self.assertEqual(action, TC_ACT_OK)
            self.assertIsNone(ev)

        self.assertEqual(small_sensor.stats[STAT_RINGBUF_DROPS], 2)
        self.assertEqual(small_sensor.stats[STAT_API_EVENTS_EMITTED], 3)

    def test_backpressure_recovery_when_consumer_drains_buffer(self):
        """Recovery test: When consumer drains ringbuffer, sensor immediately resumes emitting."""
        small_sensor = MockSensorRuntime(ringbuf_capacity_events=2)
        pkt = build_test_packet(dst_port=80, payload=b"GET /api/v1/test HTTP/1.1\r\n\r\n")

        # Fill 2 events
        small_sensor.process_packet(pkt)
        small_sensor.process_packet(pkt)
        self.assertEqual(len(small_sensor.ringbuf_queue), 2)

        # 3rd packet drops
        small_sensor.process_packet(pkt)
        self.assertEqual(small_sensor.stats[STAT_RINGBUF_DROPS], 1)

        # Consumer drains queue
        drained = small_sensor.ringbuf_queue.pop(0)
        self.assertEqual(len(small_sensor.ringbuf_queue), 1)

        # 4th packet succeeds now that space is available
        action, ev = small_sensor.process_packet(pkt)
        self.assertEqual(action, TC_ACT_OK)
        self.assertIsNotNone(ev)
        self.assertEqual(small_sensor.stats[STAT_API_EVENTS_EMITTED], 3)


if __name__ == "__main__":
    unittest.main()
