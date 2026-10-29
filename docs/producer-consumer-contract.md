# Producer/Consumer Contract: eBPF Sensor <-> User-Space Collector

**Producer:** Member 2 (eBPF Traffic Engineer / `member2/ebpf-capture`)
**Consumer:** Member 3 (Rust Collector Engineer / `member3/rust-enforcement`)
**Interface ID:** `IF-03` (defined in `docs/integration-data-flow.md`)
**Status:** Formalized & Validated Contract Baseline
**Date:** 2026-10-27

---

## 1. Executive Summary & Architecture

This contract establishes the exact wire-level interface between the in-kernel eBPF observation sensor (`ebpf/src/api_sentinel_sensor.c`) and the user-space Rust collector daemon (`collector/`).

```
+---------------------------------------------------------------------------------+
|                               LINUX KERNEL SPACE                                |
|                                                                                 |
|  [ Ingress Packet on clsact ]                                                   |
|             |                                                                   |
|             v                                                                   |
|  +---------------------------------------------------------------------------+  |
|  | eBPF Classifier: api_sentinel_tc_ingress (ebpf/src/api_sentinel_sensor.c)  |  |
|  | - Strips query parameters (?token=...) and excludes bodies/credentials   |  |
|  | - Populates struct api_event (Network Byte Order for IP/Ports)            |  |
|  | - Encodes Schema Version 1 into flags high byte                           |  |
|  +-------------------------------------+-------------------------------------+  |
|                                        |                                        |
|                     bpf_ringbuf_reserve() fails (full)?                         |
|                     /                         \                                 |
|                   YES                          NO                               |
|                   /                             \                               |
|        +---------------------+          +------------------------------------+  |
|        | Increment per-CPU   |          | bpf_ringbuf_submit()               |  |
|        | STAT_RINGBUF_DROPS  |          | into api_sentinel_events (8 MB)    |  |
|        +---------------------+          +-----------------+------------------+  |
+-----------------------------------------------------------|---------------------+
                                                            | Zero-Copy RingBuffer
                                                            v
+---------------------------------------------------------------------------------+
|                                USER SPACE DAEMON                                |
|                                                                                 |
|  +---------------------------------------------------------------------------+  |
|  | Member 3 Collector Daemon (runs unprivileged as apisentinel, UID 998)     |  |
|  | - Polls /sys/fs/bpf/api_sentinel/api_sentinel_events via epoll            |  |
|  | - Verifies schema_version == 1; rejects incompatible versions             |  |
|  | - Performs explicit Endianness Conversion: ntohs(port), ntohl(ip)         |  |
|  | - Maps monotonic timestamp_ns to UTC using host boot_time                 |  |
|  | - Detects drops via sequence gap: event_id != last_id + 1                 |  |
|  | - Forwards normalized IF-04 batches to Member 4 Analytics                 |  |
|  +---------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------+
```

---

## 2. The Pitfall: Why Proposed Collector Records Must Not Be Assumed to Match the Sensor

In distributed and systems programming, a common failure mode is assuming that a collector's proposed high-level object layout directly mirrors the low-level kernel wire struct.

| Attribute | Collector Proposed Ingest Model (Rust / User Space) | Sensor Native Wire Struct (C / eBPF Kernel) | Architectural Mismatch / Resolution |
|---|---|---|---|
| **Port Endianness** | Native Host Endian (`u16`, Little Endian on x86) | **Network Byte Order (Big Endian)** (`__be16`) | If collector does not use `u16::from_be()`, port 80 (`0x0050`) is read as 20,480 (`0x5000`)! |
| **IP Endianness** | String representation or native integer | **Network Byte Order (Big Endian)** (`__be32`) | Collector must use `u32::from_be()` before formatting to `std::net::Ipv4Addr`. |
| **Timestamp Clock** | UTC Wall-Clock (`chrono::DateTime<Utc>`) | **Monotonic Nanoseconds** (`bpf_ktime_get_ns()`) | Kernel cannot safely read UTC wall-clock without drift. Collector must calculate `boot_time_utc + timestamp_ns`. |
| **Schema Version** | Standalone field at offset 0 | **Embedded in `flags` high byte (bits 24..31)** | Placing a separate 4-byte field at offset 0 would shift all subsequent field offsets, causing verifier faults and alignment bugs. |
| **Identity** | 128-bit Host UUID or container string | **Numeric Context (PID, TGID, UID, Flow Hash)** | Kernel cannot allocate heap strings. The collector enriches numeric IDs with container metadata. |
| **Memory Alignment** | Compiler-dependent struct packing | **Strict 64-bit boundary alignment (192 bytes)** | Raw casting in Rust requires `#[repr(C)]` with exact padding matching C ABI. |

---

## 3. Wire Record Specification (`struct api_event`)

- **Total Wire Record Size:** Exactly **192 bytes**.
- **Alignment:** 64-bit (8-byte) aligned.
- **Wire Schema Version:** **1** (`API_EVENT_SCHEMA_VERSION_V1`).

### 3.1 Field-by-Field Offset and Endianness Table

| Offset (Bytes) | Field Name | C Type | Rust FFI Type | Size | Endianness | Description |
|:---:|---|---|---|:---:|---|---|
| **0** | `timestamp_ns` | `__u64` | `u64` | 8 | Host Endian | Monotonic nanoseconds since system boot (`bpf_ktime_get_ns()`). |
| **8** | `event_id` | `__u32` | `u32` | 4 | Host Endian | Monotonic per-sensor sequence number for gap/loss detection. |
| **12** | `pid` | `__u32` | `u32` | 4 | Host Endian | Process ID from socket correlation (0 if unassociated). |
| **16** | `tgid` | `__u32` | `u32` | 4 | Host Endian | Thread Group ID. |
| **20** | `uid` | `__u32` | `u32` | 4 | Host Endian | User ID owning the socket. |
| **24** | `flow.src_ip` | `__u32` | `u32` | 4 | **Big Endian (BE)** | IPv4 source address in network byte order. |
| **28** | `flow.dst_ip` | `__u32` | `u32` | 4 | **Big Endian (BE)** | IPv4 destination address in network byte order. |
| **32** | `flow.src_port` | `__u16` | `u16` | 2 | **Big Endian (BE)** | TCP source port in network byte order (`htons`). |
| **34** | `flow.dst_port` | `__u16` | `u16` | 2 | **Big Endian (BE)** | TCP destination port in network byte order (`htons`). |
| **36** | `flow.protocol` | `__u8` | `u8` | 1 | Host Endian | IP protocol number (`6` = TCP). |
| **37** | `flow.ip_version` | `__u8` | `u8` | 1 | Host Endian | IP version: `4` for IPv4, `6` for IPv6. |
| **38** | `flow._padding` | `__u8[2]` | `[u8; 2]` | 2 | None | Explicit padding for 64-bit alignment (must be `0x0000`). |
| **40** | `flow.flow_hash` | `__u64` | `u64` | 8 | Host Endian | Calculated flow hash (covers full 128-bit IPs for IPv6). |
| **48** | `http_method` | `__u8` | `u8` | 1 | Host Endian | Enum: 1=GET, 2=POST, 3=PUT, 4=DELETE, 5=PATCH, 6=HEAD, 7=OPTIONS. |
| **49** | `direction` | `__u8` | `u8` | 1 | Host Endian | 0 = Ingress, 1 = Egress. |
| **50** | `status_code` | `__u16` | `u16` | 2 | Host Endian | HTTP response status code (0 on ingress, 200-599 on egress). |
| **52** | `payload_bytes` | `__u32` | `u32` | 4 | Host Endian | Total L4 TCP payload bytes. |
| **56** | `latency_us` | `__u32` | `u32` | 4 | Host Endian | Calculated request-to-response latency in microseconds. |
| **60** | `flags` | `__u32` | `u32` | 4 | Host Endian | Bitmask containing Schema Version (bits 24-31) and status flags. |
| **64** | `route_marker` | `char[128]` | `[u8; 128]` | 128 | ASCII | Null-terminated bounded URI path (query parameters stripped). |
| **Total** | | | | **192** | | **Strictly 64-bit aligned, exactly 192 bytes.** |

---

## 4. Schema Versioning & Flags Specification

The 32-bit `flags` field (at offset 60) encodes both the schema version and event operational metadata:

```
 31                     24 23                                    5   4   3   2   1   0
+-------------------------+---------------------------------------+---+---+---+---+---+---+
|   SCHEMA_VERSION (8b)   |             RESERVED (19b)            | M | D | Q | 6 | T |
+-------------------------+---------------------------------------+---+---+---+---+---+---+
```

- **Bits 31-24 (Mask `0xFF000000`):** `SCHEMA_VERSION`
  - Current value: `0x01` (`API_EVENT_SCHEMA_VERSION_V1`).
  - Macro: `GET_API_EVENT_SCHEMA_VERSION(flags) = (flags >> 24) & 0xFF`.
  - **Consumer Contract:** If `schema_version != 1`, Member 3 collector MUST reject and quarantine the event, incrementing `STAT_SCHEMA_REJECTIONS`.
- **Bit 0 (`0x00000001`):** `API_EVENT_FLAG_ROUTE_TRUNCATED` — URL path exceeded 127 bytes and was safely terminated.
- **Bit 1 (`0x00000002`):** `API_EVENT_FLAG_IPV6` — Flow is IPv6.
- **Bit 2 (`0x00000004`):** `API_EVENT_FLAG_QUERY_STRIPPED` — Sensitive query string (`?token=...`) was stripped at probe time.
- **Bit 3 (`0x00000008`):** `API_EVENT_FLAG_DROP_OCCURRED` — Preceding event was lost due to ring buffer saturation.
- **Bit 4 (`0x00000010`):** `API_EVENT_FLAG_MONITOR_ONLY` — Sensor operated in monitor-only mode.

---

## 5. Sequence, Loss, and Drop Semantics

1. **Monotonic Sequence (`event_id`):**
   - The sensor increments `event_id` sequentially for every emitted event.
   - The collector tracks `last_event_id`.
   - If `current_event_id > last_event_id + 1`, a sequence gap occurred:
     $$\text{dropped\_events} = \text{current\_event\_id} - (\text{last\_event\_id} + 1)$$
2. **Atomic RingBuffer Drop Accounting:**
   - When the 8 MB ring buffer is full, `bpf_ringbuf_reserve()` returns `NULL`.
   - The probe immediately increments the per-CPU counter `api_sentinel_stats[STAT_RINGBUF_DROPS]`.
   - The sensor NEVER blocks, loops, or panics in kernel space; it returns `TC_ACT_OK` to preserve network throughput.
3. **Recovery:**
   - Once the user-space collector drains events, the ring buffer frees capacity.
   - The sensor resumes event delivery on the next packet.
   - The collector detects the sequence gap, records drop telemetry, and alerts downstream Member 4 analytics.

---

## 6. Host & Boot Identity Binding

1. **Boot Identity:**
   - The sensor's `timestamp_ns` is anchored to Linux system boot time (`bpf_ktime_get_ns()`).
   - At startup, the user-space loader/collector reads the host boot ID:
     ```bash
     cat /proc/sys/kernel/random/boot_id
     ```
   - Monotonic nanoseconds are converted to UTC wall-clock time by adding system boot timestamp from `/proc/stat` (`btime`).
2. **Session Identity:**
   - Connection lifecycle is tracked in `api_sentinel_sessions` LRU hash map using `struct flow_key` as key and `struct session_metadata` (PID, TGID, UID) as value.

---

## 7. Rust Ingestion Implementation Guide (Member 3 Reference)

```rust
// Proposed Rust FFI definition for Member 3
#[repr(C, packed)]
pub struct WireApiEvent {
    pub timestamp_ns: u64,
    pub event_id: u32,
    pub pid: u32,
    pub tgid: u32,
    pub uid: u32,
    // Flow key (24 bytes)
    pub src_ip: u32,       // Big Endian
    pub dst_ip: u32,       // Big Endian
    pub src_port: u16,     // Big Endian
    pub dst_port: u16,     // Big Endian
    pub protocol: u8,
    pub ip_version: u8,
    pub _padding: [u8; 2],
    pub flow_hash: u64,
    // Protocol metadata (16 bytes)
    pub http_method: u8,
    pub direction: u8,
    pub status_code: u16,
    pub payload_bytes: u32,
    pub latency_us: u32,
    pub flags: u32,
    // Bounded route marker (128 bytes)
    pub route_marker: [u8; 128],
}

impl WireApiEvent {
    pub fn schema_version(&self) -> u8 {
        ((self.flags >> 24) & 0xFF) as u8
    }

    pub fn src_port_host(&self) -> u16 {
        u16::from_be(self.src_port)
    }

    pub fn dst_port_host(&self) -> u16 {
        u16::from_be(self.dst_port)
    }
}
```

---

## 8. Producer/Consumer Verification Evidence

- **Unit Test Suite:** `tests/test_producer_consumer_contract.py`
  - Validates exact 192-byte record size.
  - Validates exact field offsets 0 through 192.
  - Proves big-endian port decoding (`80` vs naive `20480`).
  - Proves sequence gap and drop detection.
  - Proves rejection of incompatible schema versions.
- **Reference Harness:** `scripts/collector_test_harness.py`
