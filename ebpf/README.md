# eBPF Observation Layer & Sensor

**Owner:** Member 2 (eBPF Traffic Engineer)<br>
**Branch:** `member2/ebpf-capture`<br>
**Mission:** Build bounded, least-privilege Linux/eBPF observation and approved enforcement hooks. Do not capture unnecessary payloads or weaken TLS.

## Directory Structure
- `src/api_sentinel_sensor.c`: Bounded Linux TC ingress/egress eBPF classifier program in C.
- `include/api_sentinel_types.h`: C structures and alignment definitions (`flow_key`, `session_metadata`, `api_event`, `capture_config`).
- `include/api_sentinel_maps.h`: BPF map definitions conforming to `libbpf` conventions (`RINGBUF`, `LRU_HASH`, `PERCPU_ARRAY`, `ARRAY`).
- `Makefile`: Reproducible compilation, verification, test, and lifecycle targets.

## Design Invariants
1. **Memory Ceiling:** Total kernel-space memory across all maps is statically bounded to **~11.8 MB** (well below the 32 MB project budget).
2. **Alignment & Wire Size:** All user-kernel communication structures are aligned to 64-bit boundaries. `struct api_event` is strictly **192 bytes**.
3. **Safety & Bounds:** All pointer arithmetic within packet parsing routines is checked against `data_end` before memory dereferencing. Stack frames are strictly `< 512 bytes`.
4. **Least Privileges:** Designed to run with only `CAP_BPF` + `CAP_NET_ADMIN` without requiring root or `CAP_SYS_ADMIN`.
5. **Monitor-Only:** Returns `TC_ACT_OK` (0) in all observation paths. Does not alter or drop packets.
6. **Privacy Boundary:** Excludes authorization headers, cookies, and bodies. Automatically strips query parameters (`?key=val`) at probe level.
7. **Preserves TLS:** Does not decrypt TLS traffic or claim encrypted packets expose HTTP routes. Observes cleartext traffic at approved observation points (reverse proxy egress / loopback).

## Reproducible Build & Verification Commands

```bash
# Build eBPF sensor bytecode
make -C ebpf build

# Run verifier checks and unit/contract test suites
python -m unittest tests/test_day1_prerequisites.py \
                   tests/test_day2_maps_and_privs.py \
                   tests/test_producer_consumer_contract.py \
                   tests/test_working_sensor_runtime.py \
                   tests/test_security_rules.py

# Attach sensor to lab interface (monitor-only)
sudo python3 scripts/sensor_loader.py --attach --interface lo

# Scoped cleanup (unpins only project maps and removes only project filters)
sudo python3 scripts/sensor_loader.py --cleanup --interface lo
```
