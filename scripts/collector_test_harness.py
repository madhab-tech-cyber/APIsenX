#!/usr/bin/env python3
"""
Collector Test Harness (Member 3 Ingest Contract Verification)
Role: Member 2 (eBPF Traffic Engineer) & Member 3 (Collector Lead)
Branch: member2/ebpf-capture

Acts as the consumer-side reference implementation for the Producer/Consumer Contract.
Validates wire format, schema version, field offsets, endianness decoding,
sequence tracking, and drop semantics.
"""

import sys
import os
import struct
import socket
import json

# Wire struct layout matching ebpf/include/api_sentinel_types.h (192 bytes)
# Header: timestamp_ns (Q), event_id (I), pid (I), tgid (I), uid (I) -> 24 bytes
# Flow: src_ip (I - BE), dst_ip (I - BE), src_port (H - BE), dst_port (H - BE), protocol (B), ip_version (B), pad (2s), flow_hash (Q) -> 24 bytes
# Metadata: http_method (B), direction (B), status_code (H), payload_bytes (I), latency_us (I), flags (I) -> 16 bytes
# Route marker: 128 bytes (128s)
# Total: 24 + 24 + 16 + 128 = 192 bytes

WIRE_FORMAT = "=QIIII" + "IIHHBB2sQ" + "BBHIII" + "128s"
WIRE_RECORD_SIZE = struct.calcsize(WIRE_FORMAT)

SCHEMA_VERSION_MASK = 0xFF000000
SCHEMA_VERSION_SHIFT = 24
EXPECTED_SCHEMA_VERSION = 1

FLAG_ROUTE_TRUNCATED = 1 << 0
FLAG_IPV6            = 1 << 1
FLAG_QUERY_STRIPPED  = 1 << 2
FLAG_DROP_OCCURRED   = 1 << 3
FLAG_MONITOR_ONLY    = 1 << 4

HTTP_METHODS = {
    0: "UNKNOWN",
    1: "GET",
    2: "POST",
    3: "PUT",
    4: "DELETE",
    5: "PATCH",
    6: "HEAD",
    7: "OPTIONS",
}

class IngestContractValidator:
    def __init__(self):
        self.last_seq = None
        self.total_received = 0
        self.total_drops = 0
        self.schema_violations = 0
        self.events = []

    def decode_raw_event(self, raw_bytes):
        """Decode raw binary event from BPF ring buffer adhering to exact wire contract."""
        if len(raw_bytes) != WIRE_RECORD_SIZE:
            raise ValueError(f"Record size mismatch: expected {WIRE_RECORD_SIZE} bytes, got {len(raw_bytes)}")

        unpacked = struct.unpack(WIRE_FORMAT, raw_bytes)

        # 1. Header (Host byte order)
        timestamp_ns = unpacked[0]
        event_id = unpacked[1]
        pid = unpacked[2]
        tgid = unpacked[3]
        uid = unpacked[4]

        # 2. Flow key (Network byte order for IP & ports, Host byte order for hash)
        raw_src_ip = unpacked[5]
        raw_dst_ip = unpacked[6]
        raw_src_port = unpacked[7]
        raw_dst_port = unpacked[8]
        protocol = unpacked[9]
        ip_version = unpacked[10]
        padding = unpacked[11]
        flow_hash = unpacked[12]

        # Explicit Endianness Conversion
        # In the wire format, IP and ports were stored in network byte order (Big Endian)
        src_ip_str = socket.inet_ntoa(struct.pack("!I", socket.ntohl(raw_src_ip)))
        dst_ip_str = socket.inet_ntoa(struct.pack("!I", socket.ntohl(raw_dst_ip)))
        src_port = socket.ntohs(raw_src_port)
        dst_port = socket.ntohs(raw_dst_port)

        # 3. Protocol Metadata (Host byte order)
        http_method_id = unpacked[13]
        direction = unpacked[14]
        status_code = unpacked[15]
        payload_bytes = unpacked[16]
        latency_us = unpacked[17]
        flags = unpacked[18]

        # Extract schema version from flags high byte
        schema_version = (flags & SCHEMA_VERSION_MASK) >> SCHEMA_VERSION_SHIFT
        if schema_version != EXPECTED_SCHEMA_VERSION:
            self.schema_violations += 1
            raise ValueError(f"Incompatible schema version: got {schema_version}, expected {EXPECTED_SCHEMA_VERSION}")

        # 4. Route marker (ASCII string, null-terminated)
        raw_route = unpacked[19]
        route_marker = raw_route.split(b"\x00", 1)[0].decode("ascii", errors="replace")

        # Check for privacy violations: route MUST NOT contain query parameters '?' or secret keywords
        if "?" in route_marker:
            raise ValueError(f"Privacy boundary failure: unstripped query parameter detected in route: {route_marker}")

        # Sequence gaps are diagnostic only; aggregate kernel drop counters are authoritative.
        # Use modulo-2^32 arithmetic and ignore ambiguous backward/restart jumps.
        dropped_in_gap = 0
        if self.last_seq is not None:
            gap = (event_id - self.last_seq - 1) & 0xFFFFFFFF
            if gap < 0x80000000:
                dropped_in_gap = gap
                self.total_drops += dropped_in_gap
        self.last_seq = event_id
        self.total_received += 1

        decoded = {
            "schema_version": schema_version,
            "event_id": event_id,
            "timestamp_ns": timestamp_ns,
            "pid": pid,
            "tgid": tgid,
            "uid": uid,
            "flow": {
                "src_ip": src_ip_str,
                "dst_ip": dst_ip_str,
                "src_port": src_port,
                "dst_port": dst_port,
                "protocol": protocol,
                "ip_version": ip_version,
                "flow_hash": flow_hash,
            },
            "http_method": HTTP_METHODS.get(http_method_id, f"UNKNOWN({http_method_id})"),
            "direction": "INGRESS" if direction == 0 else "EGRESS",
            "status_code": status_code,
            "payload_bytes": payload_bytes,
            "latency_us": latency_us,
            "flags": {
                "raw": flags,
                "route_truncated": bool(flags & FLAG_ROUTE_TRUNCATED),
                "ipv6": bool(flags & FLAG_IPV6),
                "query_stripped": bool(flags & FLAG_QUERY_STRIPPED),
                "drop_occurred": bool(flags & FLAG_DROP_OCCURRED),
                "monitor_only": bool(flags & FLAG_MONITOR_ONLY),
            },
            "route_marker": route_marker,
            "dropped_in_gap": dropped_in_gap,
        }
        self.events.append(decoded)
        return decoded

    def get_summary(self):
        return {
            "total_received": self.total_received,
            "total_drops": self.total_drops,
            "schema_violations": self.schema_violations,
            "events_captured": len(self.events),
        }

if __name__ == "__main__":
    validator = IngestContractValidator()
    print(f"[*] Initialized Ingest Contract Validator (Expected Wire Size: {WIRE_RECORD_SIZE} bytes)")
    print(f"[*] Ready to validate ring buffer events from Member 2 sensor.")
