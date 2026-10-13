# eBPF Observation Layer

**Owner:** Member 2 (eBPF Traffic Engineer)  
**Mission:** Build bounded, least-privilege Linux/eBPF observation and approved enforcement hooks. Do not capture unnecessary payloads or weaken TLS.

## Directory Structure
- `include/api_sentinel_types.h`: C structures and alignment definitions (`flow_key`, `session_metadata`, `api_event`, `capture_config`).
- `include/api_sentinel_maps.h`: BPF map definitions conforming to `libbpf` / Aya conventions (`RINGBUF`, `LRU_HASH`, `PERCPU_ARRAY`, `ARRAY`).

## Design Invariants
1. **Memory Ceiling:** Total kernel-space memory across all maps is statically bounded to **~11.8 MB** (well below the 32 MB project budget).
2. **Alignment:** All user-kernel communication structures are aligned to 64-bit boundaries with explicit padding.
3. **Safety:** All pointer arithmetic within packet parsing routines must be checked against `data_end` before memory dereferencing.
4. **Least Privileges:** Designed to run with only `CAP_BPF` + `CAP_NET_ADMIN` without requiring root or `CAP_SYS_ADMIN`.
