# Day 1: Linux/eBPF Prerequisites & Capture Design Note

**Document ID:** API-SENTINEL-DESIGN-001  
**Author:** Member 2 (eBPF Traffic Engineer)  
**Branch:** `member2/ebpf-capture`  
**Phase:** Foundation (Day 1 of 30)  
**Target Delivery:** Member 1 (Policy Approval), Member 3 (Collector Lead), Member 4 (Schema Lead)

---

## 1. Executive Summary & Objective

API-Sentinel requires a production-grade, low-overhead observation layer deployed inside the Linux kernel to intercept, parse, and export API transaction metadata for shadow API detection and authorization enforcement.

As the **eBPF Traffic Engineer (Member 2)**, the primary mission is to:
> *Build a safe, low-overhead Linux/eBPF observation layer that supplies only the approved metadata required for API discovery and enforcement.*

This document establishes:
1. **Target system prerequisites** (kernel version, BTF, compiler toolchain, runtime subsystems).
2. **Metadata boundaries** ensuring privacy-by-design and zero extraction of credentials or raw payloads.
3. **Observation architecture & event streaming** utilizing BPF ring buffers.
4. **Limits of observing encrypted traffic** without compromising cryptographic guarantees.
5. **Team handoffs and integration interfaces**.

---

## 2. Linux & eBPF Prerequisites Specification

### 2.1 Kernel Requirements Matrix

| Subsystem / Feature | Minimum Version | Recommended | Rationale |
|:---|:---:|:---:|:---|
| **Linux Kernel** | `5.8.0` | `5.15.0+ LTS` or `6.x` | Introduces `BPF_MAP_TYPE_RINGBUF` and granular `CAP_BPF` |
| **BPF Type Format (BTF)** | `5.4.0` | `5.8.0+` | Requires `/sys/kernel/btf/vmlinux` for Compile-Once Run-Everywhere (CO-RE) |
| **Ring Buffer (`BPF_MAP_TYPE_RINGBUF`)** | `5.8.0` | `5.15.0+` | Lockless, multi-producer single-consumer ring buffer replacing memory-heavy perf buffers |
| **Granular Capabilities** | `5.8.0` | `5.15.0+` | `CAP_BPF` + `CAP_NET_ADMIN` replaces monolithic root / `CAP_SYS_ADMIN` |
| **Traffic Control (TC cls_bpf)** | `4.18.0` | `5.10.0+` | Direct ingress/egress frame classification with `clsact` qdisc |

### 2.2 Mandatory Kernel Configuration Flags

The target Linux environment must be compiled with the following flags enabled:

```ini
# Core BPF Subsystem
CONFIG_BPF=y
CONFIG_BPF_SYSCALL=y
CONFIG_BPF_JIT=y
CONFIG_BPF_JIT_ALWAYS_ON=y

# BPF Type Format (CO-RE)
CONFIG_DEBUG_INFO_BTF=y
CONFIG_DEBUG_INFO_BTF_MODULES=y

# Networking & TC Hooks
CONFIG_NET_CLS_ACT=y
CONFIG_NET_CLS_BPF=y
CONFIG_NET_SCH_INGRESS=m/y
CONFIG_NET_SCH_EGRESS=y
CONFIG_SOCK_CGROUP_DATA=y

# Tracing & Events
CONFIG_KPROBES=y
CONFIG_UPROBES=y
CONFIG_BPF_EVENTS=y
CONFIG_HAVE_EBPF_JIT=y
```

### 2.3 Required Toolchain & Build Dependencies

1. **Compilers & Assemblers:**
   - LLVM / Clang `>= 13.0` (with BPF target support: `llc -march=bpf`)
   - Rust toolchain (`stable` + `nightly` for BPF bytecode compilation via `bpf-linker` or `aya-bpf`)
2. **Kernel Inspection & Development Libraries:**
   - `bpftool` (matching kernel version)
   - `libbpf-dev` `>= 0.8.0`
   - Linux kernel headers: `linux-headers-$(uname -r)`
3. **Execution Runtime Environments:**
   - Linux Host / Production Container (Docker/containerd with capability bounding)
   - Development Lab: Ubuntu 22.04 LTS / 24.04 LTS with WSL2 (custom kernel) or dedicated VM / QEMU instance.

---

## 3. Capture Design & Architecture

```
+-----------------------------------------------------------------------------------+
|                                LINUX KERNEL SPACE                                 |
|                                                                                   |
|   +-----------------------+              +------------------------------------+   |
|   |  Network Interface    |              |  System Call Layer                 |   |
|   |  (tc clsact ingress)  |              |  (sys_enter_connect / accept)      |   |
|   +-----------+-----------+              +-----------------+------------------+   |
|               |                                            |                      |
|               v                                            v                      |
|   +-----------------------+              +------------------------------------+   |
|   | TC BPF Classifier     | <----------> | Socket/Process Correlator          |   |
|   | - Filter ports (80..) |              | - Look up PID, TGID, UID           |   |
|   | - Parse HTTP method   |              | - Correlate Socket 4-Tuple         |   |
|   +-----------+-----------+              +-----------------+------------------+   |
|               |                                            |                      |
|               |        +----------------------------+      |                      |
|               +------> | api_sentinel_sessions      | <----+                      |
|                        | (BPF_MAP_TYPE_LRU_HASH)    |                             |
|                        +----------------------------+                             |
|                                       |                                           |
|                                       v                                           |
|                        +----------------------------+                             |
|                        | api_sentinel_events        |                             |
|                        | (BPF_MAP_TYPE_RINGBUF)     |                             |
|                        +--------------+-------------+                             |
+---------------------------------------|-------------------------------------------+
                                        | Zero-Copy RingBuffer Event Stream
                                        v
+-----------------------------------------------------------------------------------+
|                              USER SPACE DAEMON                                    |
|                                                                                   |
|   +---------------------------------------------------------------------------+   |
|   | Member 3 Collector (Daemon running as unprivileged user: apisentinel)     |   |
|   | - Polling ringbuf epoll / sleepable wait                                  |   |
|   | - Validating bounded event lengths                                        |   |
|   | - Forwarding to Member 4 Discovery Engine & Member 6 Health Exporter      |   |
|   +---------------------------------------------------------------------------+   |
+-----------------------------------------------------------------------------------+
```

### 3.1 Kernel Observation Boundary & Privacy Constraints

In strict compliance with project working rules:
> *Never commit secrets, personal data, raw packet captures, populated .env files or private keys.*

API-Sentinel establishes a hard separation between **protocol metadata** and **sensitive payload contents**:

#### Approved Metadata (Captured & Emitted):
1. **Timestamp:** `ktime_get_ns()` (nanosecond-precision relative timestamp).
2. **Process Identity:** `tgid_pid` (Process ID & Thread Group ID), `uid_gid` (User ID).
3. **Network 5-Tuple:**
   - IP Version (IPv4 / IPv6)
   - Source IP address
   - Destination IP address
   - Source Port
   - Destination Port
   - L4 Protocol (`IPPROTO_TCP`)
4. **API Transaction Markers:**
   - HTTP Method Token (e.g. `1=GET`, `2=POST`, `3=PUT`, `4=DELETE`, `5=PATCH`, `6=HEAD`, `7=OPTIONS`)
   - Route Marker: Up to 128 bytes bounded path string or truncated route hash.
   - Payload Length: Total payload size in bytes (L4 payload length).
   - Event Direction: Ingress (0) vs Egress (1).

#### Prohibited Data (Strictly Dropped / Ignored at Probe Level):
1. **No Authorization Headers:** Headers such as `Authorization: Bearer ...`, `Cookie: ...`, `X-Api-Key` are neither extracted nor buffered.
2. **No Request/Response Bodies:** JSON, XML, or binary payloads are ignored; only byte length is captured.
3. **No Query Parameter Values:** Query string values potentially embedding API tokens or passwords are excluded from route markers.
4. **No Raw PCAP Dumps:** The observation layer emits strictly typed, structured C events rather than raw L2/L3 packet buffers.

---

## 4. Limits of Observing Encrypted Traffic (TLS)

Observing production API traffic involves encrypted streams (HTTPS/TLS 1.2/1.3). As an eBPF Traffic Engineer, the boundaries of observation must be documented clearly:

1. **Network Hook (TC/Socket Filter) Limitations:**
   - Network-level eBPF hooks inspect packets on the wire.
   - For TLS connections, the payload is ciphertext.
   - **What TC can observe:** TCP handshake timing, IP 5-tuple, TLS ClientHello Server Name Indication (SNI) and ALPN negotiation (unencrypted during handshake), packet pacing, byte counts.
   - **What TC cannot observe:** HTTP method, route, request headers, status codes.

2. **Application Layer Observation (Uprobes vs TLS Termination):**
   - In production microservice environments (Service Mesh, Ingress Gateways, Reverse Proxies like Envoy/Nginx), eBPF can observe either:
     - Cleartext traffic between the reverse proxy and internal microservices.
     - User-space probes (`uprobes`) attached to OpenSSL/BoringSSL (`SSL_read`/`SSL_write`) hooks.
   - **Security Guarantee:** API-Sentinel **never injects TLS MITM certificates or weakens cipher suites**. The Day 1-7 foundation focuses on cleartext edge/internal service traffic, with uprobe extension paths designed for Day 8-15 without cryptographic tampering.

---

## 5. Ring Buffer (`BPF_MAP_TYPE_RINGBUF`) vs Perf Buffer Comparison

| Metric / Attribute | BPF Perf Buffer (`PERF_EVENT_ARRAY`) | BPF Ring Buffer (`RINGBUF`) | Decision for API-Sentinel |
|:---|:---|:---|:---|
| **Memory Allocation** | Per-CPU buffers (e.g. 4MB × 64 cores = 256MB) | Single global circular buffer (e.g. 8MB shared) | **Ring Buffer:** 32x lower memory overhead |
| **Event Ordering** | Out-of-order across CPU cores | Strict chronological order across all cores | **Ring Buffer:** Simplifies collector reconstruction |
| **Drop Handling** | Silent per-CPU drop on contention | Atomic reservation with verifiable drop counters | **Ring Buffer:** Zero-loss visibility and auditing |
| **Zero-Copy Support** | Requires copying kernel struct to buffer | `bpf_ringbuf_reserve()` allocates buffer in-place | **Ring Buffer:** Eliminates unnecessary struct copying |
| **Kernel Support** | Linux 4.4+ | Linux 5.8+ | **Ring Buffer:** Meets our >= 5.8 prerequisite |

---

## 6. Team Handoffs & Interfaces

1. **Member 1 (Policy Approval):** Review and approve this capture design note, memory allocations (<32MB total), and capability constraints.
2. **Member 3 (Collector Lead):** Interface format definition: User-space daemon binds to `api_sentinel_events` ring buffer and ingests `struct api_event`.
3. **Member 4 (API Discovery Lead):** Confirm approved metadata fields (PID, 5-tuple, method enum, route marker length = 128 bytes).
4. **Member 5 (Traffic Simulation):** Mock HTTP test suites will generate standard CRUD requests to verify observation accuracy.
5. **Member 6 (Health & Metrics):** Export `api_sentinel_stats` per-CPU counters (events emitted, drops, verifier rejections) to Prometheus.

---

## 7. Day 1 Acceptance Criteria & Verification Evidence

- [x] Documented all Linux/eBPF kernel requirements, configs, and toolchains.
- [x] Defined approved metadata and privacy boundaries (zero secrets/payloads).
- [x] Evaluated Ring Buffer vs Perf Buffer and selected 8MB RingBuffer.
- [x] Formulated TLS observation boundaries and security posture.
- [x] Automated prerequisite verification script (`scripts/check_prereqs.py`).
- [x] Unit test passing (`tests/test_day1_prerequisites.py`).
