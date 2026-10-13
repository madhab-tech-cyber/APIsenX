# Day 2: Kernel Hooks, BPF Maps & Least Privileges Specification

**Document ID:** API-SENTINEL-SPEC-002  
**Author:** Member 2 (eBPF Traffic Engineer)  
**Branch:** `member2/ebpf-capture`  
**Phase:** Foundation (Day 2 of 30)  
**Target Delivery:** Member 1 (Policy Approval), Member 3 (Collector Lead), Member 4 (Schema Lead), Member 6 (Health Metrics Lead)

---

## 1. Scope & Technical Objectives

On Day 2 of the API-Sentinel foundation phase, this specification defines the kernel-level execution model:
1. **Hook Selection:** Evaluate and specify exact Linux kernel hook points for capturing API transaction metadata and supporting future rate limiting / enforcement (Day 16-18).
2. **BPF Map Architectures:** Define schema, memory bounds, eviction strategies, and allocation ceilings for all in-kernel state tables.
3. **Least Privilege Model:** Document precise Linux capabilities (`CAP_BPF`, `CAP_NET_ADMIN`), privilege-dropping mechanisms, and hardened systemd service profiles to eliminate `CAP_SYS_ADMIN` and root runtime dependencies.

---

## 2. Kernel Hook Architecture & Trade-Off Matrix

```
       [ Ingress Packets from NIC ]
                     |
                     v
   +------------------------------------+
   | Hook 1: TC (Traffic Control clsact)|  <-- Primary observation & enforcement hook
   | SEC("tc/ingress")                  |      - Parses L2/L3/L4 headers
   | Return: TC_ACT_OK / TC_ACT_SHOT    |      - Bounded HTTP method detection
   +-----------------+------------------+
                     |
                     v
       [ Network Stack Routing/TCP ]
                     |
                     v
   +------------------------------------+
   | Hook 2: SockOps (Connection State) |  <-- TCP connection lifecycle tracking
   | SEC("sockops")                     |      - Active/passive connection establishment
   | Event: BPF_SOCK_OPS_*_ESTABLISHED  |      - Populates session tracking table
   +-----------------+------------------+
                     |
                     v
   +------------------------------------+
   | Hook 3: Syscall Tracepoints        |  <-- Process context correlation
   | SEC("tracepoint/syscalls/sys_enter")|     - sys_enter_accept4 / sys_enter_connect
   | Context: PID, TGID, UID, Comm      |      - Correlates socket tuple with process
   +------------------------------------+
```

### 2.1 Hook Comparison & Selection Rationale

| Hook Point | Program Type | Attachment Target | Overhead | Mutability (Enforcement) | Decision |
|:---|:---|:---|:---:|:---:|:---|
| **Traffic Control (TC clsact)** | `BPF_PROG_TYPE_SCHED_CLS` | Direct network interface (`eth0`, `lo`) | `< 15 ns/pkt` | **Yes** (`TC_ACT_SHOT`, `TC_ACT_OK`) | **Selected (Primary)**: Captures ingress/egress API frames and provides future enforcement mechanism. |
| **Socket Filter** | `BPF_PROG_TYPE_SOCKET_FILTER` | Raw socket or cgroup | `< 25 ns/pkt` | **No** (Read-only) | **Secondary/Fallback**: Safe monitoring fallback, but cannot drop malicious packets. |
| **SockOps** | `BPF_PROG_TYPE_SOCK_OPS` | Cgroup socket operations | `< 30 ns/conn` | Indirect (TCP options) | **Selected**: Correlates socket 4-tuples with TCP handshake lifecycle and socket cookies. |
| **Tracepoints (Syscall)** | `BPF_PROG_TYPE_TRACEPOINT` | `syscalls/sys_enter_accept4`, `sys_enter_connect` | `< 40 ns/call` | **No** (Observability only) | **Selected**: Correlates network connections with process PID, TGID, UID, and container cgroups. |
| **Kprobes (Kernel Internal)** | `BPF_PROG_TYPE_KPROBE` | `tcp_v4_connect`, `tcp_rcv_established` | `< 60 ns/call` | Unsafe for production | **Excluded**: Fragile ABI across kernel revisions; tracepoints are preferred. |

---

## 3. BPF Maps Architecture & Memory Budget

To guarantee bounded kernel memory consumption (< 32 MB ceiling) and prevent Denial-of-Service attacks against the observation layer, all BPF maps are statically bounded.

### 3.1 BPF Maps Specification Table

| Map Identifier | Map Type | Key Type / Size | Value Type / Size | Max Entries | Estimated Memory | Purpose |
|:---|:---|:---:|:---:|:---:|:---:|:---|
| `api_sentinel_events` | `BPF_MAP_TYPE_RINGBUF` | N/A (FIFO ring) | `struct api_event` (192 B) | 8,388,608 B (8 MB) | **8.0 MB** | Zero-copy kernel-to-user event stream to Member 3 collector. |
| `api_sentinel_sessions`| `BPF_MAP_TYPE_LRU_HASH`| `struct flow_key` (24 B)| `struct session_metadata` (32 B)| 65,536 entries | **~3.7 MB** | Tracks active TCP connections with process ID; LRU auto-evicts under load. |
| `api_sentinel_stats` | `BPF_MAP_TYPE_PERCPU_ARRAY`| `__u32` (4 B) | `__u64` (8 B) | 16 entries (per core) | **~0.1 MB** (64 cores) | Lockless telemetry counters (events emitted, dropped, malformed). |
| `api_sentinel_config` | `BPF_MAP_TYPE_ARRAY` | `__u32` (4 B) | `struct capture_config` (32 B)| 16 entries | **< 1 KB** | Dynamic filtering rules (target ports, sampling rate, enforcement flag). |
| **Total Kernel Memory**| | | | | **~11.8 MB** | **Well within 32 MB maximum memory budget.** |

### 3.2 Detailed Map Descriptions

#### 1. `api_sentinel_events` (`BPF_MAP_TYPE_RINGBUF`)
- **Capacity:** 8,388,608 bytes (8 MB), page-aligned.
- **Producer:** Kernel-space eBPF TC classifier reserves space via `bpf_ringbuf_reserve()`.
- **Consumer:** Member 3's user-space collector polls via `bpf_ringbuf_poll()` / `epoll`.
- **Drop Accounting:** If the ring buffer is saturated, `bpf_ringbuf_reserve()` returns NULL. The probe immediately increments the per-CPU drop counter in `api_sentinel_stats`.

#### 2. `api_sentinel_sessions` (`BPF_MAP_TYPE_LRU_HASH`)
- **Key:** `struct flow_key` (Source IP, Destination IP, Source Port, Destination Port, Protocol).
- **Value:** `struct session_metadata` (PID, TGID, UID, GID, Start Timestamp, Flags).
- **Eviction Strategy:** `BPF_MAP_TYPE_LRU_HASH` automatically purges the least-recently used entry when 65,536 entries are exceeded. This eliminates state table exhaustion vulnerabilities during high-frequency SYN floods.

#### 3. `api_sentinel_stats` (`BPF_MAP_TYPE_PERCPU_ARRAY`)
- **Design:** Allocates separate counter arrays per CPU core. Lookups and increments occur without spinlocks or atomic CAS instructions, eliminating CPU cache-line bouncing.
- **Metric Indices:**
  - `0`: `STAT_TOTAL_PACKETS`
  - `1`: `STAT_API_EVENTS_EMITTED`
  - `2`: `STAT_RINGBUF_DROPS`
  - `3`: `STAT_MALFORMED_PACKETS`
  - `4`: `STAT_ENFORCEMENT_DROPS`

#### 4. `api_sentinel_config` (`BPF_MAP_TYPE_ARRAY`)
- **Key:** Config slot (`0`: Default capture configuration).
- **Value:** `struct capture_config` containing enabled status, monitored ports (e.g., 80, 8080, 8000), sampling rate (1-100%), and operational mode (0 = Observe Only, 1 = Enforcement Enabled).

---

## 4. Kernel Event Schema & Alignment

All structures transferred across the kernel-user boundary are explicitly padded to 64-bit (8-byte) boundaries. This ensures compatibility with the BPF verifier and avoids unaligned memory faults on ARM64 and x86_64 architectures.

### 4.1 `struct flow_key` (24 bytes)
```c
struct flow_key {
    __u32 src_ip;          /* IPv4 Source Address */
    __u32 dst_ip;          /* IPv4 Destination Address */
    __u16 src_port;        /* Source Port (Network Byte Order) */
    __u16 dst_port;        /* Destination Port (Network Byte Order) */
    __u8  protocol;        /* IP Protocol (IPPROTO_TCP) */
    __u8  ip_version;      /* 4 = IPv4, 6 = IPv6 */
    __u8  _padding[2];     /* Explicit alignment padding */
    __u64 flow_hash;       /* Hardware / calculated hash */
};
```

### 4.2 `struct session_metadata` (32 bytes)
```c
struct session_metadata {
    __u32 pid;             /* Process ID */
    __u32 tgid;            /* Thread Group ID */
    __u32 uid;             /* User ID owning socket */
    __u32 gid;             /* Group ID owning socket */
    __u64 start_ktime_ns;  /* Connection start timestamp */
    __u32 flags;           /* Bitmask: TLS, Ingress, Sensitive */
    __u32 _reserved;       /* Alignment padding */
};
```

### 4.3 `struct api_event` (192 bytes)
```c
struct api_event {
    /* Event Header (24 bytes) */
    __u64 timestamp_ns;    /* Kernel monotonic timestamp */
    __u32 event_id;        /* Sequential event counter */
    __u32 pid;             /* Process ID */
    __u32 tgid;            /* Thread Group ID */
    __u32 uid;             /* User ID */

    /* Network Flow Information (24 bytes) */
    struct flow_key flow;

    /* API Protocol Metadata (16 bytes) */
    __u8  http_method;     /* 1=GET, 2=POST, 3=PUT, 4=DELETE, etc. */
    __u8  direction;       /* 0=Ingress, 1=Egress */
    __u16 status_code;     /* HTTP status code (if egress response) */
    __u32 payload_bytes;   /* L4 payload length in bytes */
    __u32 latency_us;      /* Calculated request-response latency */
    __u32 flags;           /* Flag mask (e.g. truncated route) */

    /* Bounded Route Marker (128 bytes) */
    char  route_marker[128]; /* Truncated URL path string (null-terminated) */
};
```

---

## 5. Least Privileges & Capability Bounding

### 5.1 Capability Matrix

Traditional eBPF tools improperly run as full `root` with `CAP_SYS_ADMIN`. API-Sentinel strictly enforces least privileges:

| Linux Capability | Permitted Scope | Rejected Privileges |
|:---|:---|:---|
| **`CAP_BPF`** | Loading BPF programs, creating BPF maps, verifying bytecode | Cannot modify network routes, mount filesystems, or debug arbitrary processes |
| **`CAP_NET_ADMIN`** | Attaching/detaching TC filters to network interfaces | Cannot manipulate root filesystem, audit logs, or system devices |
| **`CAP_PERFMON`** (optional) | Accessing kernel performance counters and tracepoints | Cannot perform kernel memory writes |
| **`CAP_SYS_ADMIN`** | **STRICTLY FORBIDDEN** | Monolithic superuser access is never granted |

### 5.2 Privilege Dropping Daemon Lifecycle

1. **Bootstrap Phase (Privileged Startup):**
   - The user-space daemon launches with only ambient capabilities `CAP_BPF` and `CAP_NET_ADMIN`.
   - The daemon opens and pins BPF maps under `/sys/fs/bpf/api_sentinel/` and attaches TC filters.
2. **Runtime Phase (Unprivileged Execution):**
   - The daemon immediately calls `setgid(998)` and `setuid(998)` to permanently switch to dedicated unprivileged user `apisentinel`.
   - BPF file descriptors remain open across the privilege drop.
   - All subsequent packet processing and event consumer loops run entirely unprivileged.

### 5.3 Systemd Hardening Profile (`api-sentinel.service`)

```ini
[Unit]
Description=API-Sentinel eBPF Traffic Observation Daemon
After=network.target

[Service]
Type=simple
User=apisentinel
Group=apisentinel

# Capability Restrictions (Least Privilege)
AmbientCapabilities=CAP_BPF CAP_NET_ADMIN
CapabilityBoundingSet=CAP_BPF CAP_NET_ADMIN
NoNewPrivileges=yes

# Sandboxing & Filesystem Protection
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
PrivateDevices=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictNamespaces=yes

# Network & Memory Hardening
RestrictAddressFamilies=AF_INET AF_INET6 AF_NETLINK AF_UNIX
MemoryDenyWriteExecute=yes
LockPersonality=yes

ExecStart=/usr/local/bin/api-sentinel-collector
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

---

## 6. Verifier Safety Constraints Checklist

Every eBPF program deployed in API-Sentinel must satisfy the kernel BPF verifier:
- [x] **Bounded Loops:** No unbounded loops; all iterations must be constant-bounded (`#pragma unroll`).
- [x] **Pointer Validation:** Every packet pointer dereference must be preceded by an explicit bounds check against `data_end`:
  ```c
  if ((void *)(cursor + sizeof(*header)) > data_end)
      return TC_ACT_OK;
  ```
- [x] **Null Pointers:** Map lookup results must be checked for NULL before dereferencing:
  ```c
  struct session_metadata *sess = bpf_map_lookup_elem(&api_sentinel_sessions, &key);
  if (!sess)
      return TC_ACT_OK;
  ```
- [x] **Stack Limit:** Maximum stack frame size per program is strictly `< 512 bytes`. Large structures must be stored in per-CPU scratch maps or ring buffers.

---

## 7. Team Handoffs

- **Member 1 (Policy Approval):** Review and approve `CAP_BPF` + `CAP_NET_ADMIN` capability set and rejection of `CAP_SYS_ADMIN`.
- **Member 3 (Collector Lead):** Hand off `struct api_event` and `api_sentinel_events` ring buffer polling parameters.
- **Member 4 (Discovery Lead):** Confirm 128-byte route marker bounds and HTTP method token definitions.
- **Member 6 (Health Metrics Lead):** Confirm `api_sentinel_stats` per-CPU metric indices for Prometheus metrics exporter.
