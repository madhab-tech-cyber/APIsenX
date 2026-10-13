# Team Handoffs & Interface Agreements

**Role:** Member 2 (eBPF Traffic Engineer)  
**Branch:** `member2/ebpf-capture`  

This document formalizes the operational and data contracts between Member 2 and other team members according to Section 1 of the Individual Responsibility Plan.

---

## 1. Member 1 (Project Lead / Policy Approval)
- **Handoff:** BPF capability scope (`CAP_BPF` + `CAP_NET_ADMIN`), memory budgets (<32 MB), and enforcement safety boundaries.
- **Contract:** All kernel hooks run unprivileged as user `apisentinel` without `CAP_SYS_ADMIN`. Monitored ports and enforcement actions require policy approval before activation.

## 2. Member 3 (Collector Lead)
- **Handoff:** Ingest event stream from the 8 MB `api_sentinel_events` RingBuffer (`BPF_MAP_TYPE_RINGBUF`).
- **Data Structure:** `struct api_event` (192 bytes, 64-bit aligned).
- **Interface Contract:**
  - Event consumer connects via unprivileged epoll on `/sys/fs/bpf/api_sentinel/api_sentinel_events`.
  - Drops are tracked via `api_sentinel_stats[STAT_RINGBUF_DROPS]`.

## 3. Member 4 (API Discovery & Schema Lead)
- **Handoff:** Approved metadata fields for endpoint identification and shadow API mapping.
- **Data Contract:**
  - `http_method`: Enum (`GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `HEAD`, `OPTIONS`).
  - `route_marker`: Bounded null-terminated string (max 128 bytes).
  - `flow`: IP 5-tuple (`src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`).
  - `latency_us`: Monotonic delta in microseconds.

## 4. Member 5 (Traffic & Integration Testing Lead)
- **Handoff:** Traffic observation test harness.
- **Contract:** Member 5 supplies synthetic HTTP CRUD requests against monitored ports (80, 8080). Member 2 provides probe attachment scripts and assertion suites to verify 100% route capture without packet loss.

## 5. Member 6 (Observability & Health Metrics Lead)
- **Handoff:** Telemetry counters via `api_sentinel_stats` (`BPF_MAP_TYPE_PERCPU_ARRAY`).
- **Exported Metrics:**
  - `STAT_TOTAL_PACKETS`
  - `STAT_API_EVENTS_EMITTED`
  - `STAT_RINGBUF_DROPS`
  - `STAT_MALFORMED_PACKETS`
  - `STAT_ENFORCEMENT_DROPS`
