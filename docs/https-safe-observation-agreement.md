# HTTPS-Safe Observation Agreement & Boundary Definition

**Signatories:**
- **Member 1:** Team Lead & Security Architect (`member1/security-architecture`)
- **Member 2:** eBPF Traffic Engineer (`member2/ebpf-capture`)
- **Member 5:** Mock API & Integration Lead (`member5/mock-api`)

**Date:** 2026-10-27
**Scope:** Interface `IF-02` (Mock API -> Approved Observation Point) and `IF-03` (Observation Point -> eBPF Sensor)
**Security Level:** Baseline Hardening — Zero Cryptographic Tampering

---

## 1. Core Principle: Zero Compromise of Cryptographic Guarantees

API-Sentinel establishes a non-negotiable architectural invariant:
> **API-Sentinel does not weaken TLS, disable ciphers, downgrade protocols, or inject Man-in-the-Middle (MITM) CA certificates into the operating system or application runtimes.**

All encrypted network communications on port 443 (or other TLS ports) remain cryptographically sound.

---

## 2. Technical Clarification: Limits of Network-Level (TC) Observation

A critical security and engineering requirement is acknowledging what network-level packet capture can and cannot see:

| Network Observation Target | Wire State on Port 443 | What eBPF TC Classifier Can Observe | What eBPF TC Classifier CANNOT Observe |
|---|---|---|---|
| **TLS Handshake** | Plaintext (TLS 1.2/1.3 Handshake ClientHello) | Server Name Indication (SNI), ALPN negotiation (`h2`, `http/1.1`), TLS version, cipher negotiation | Pre-master secret, session keys, application data |
| **TLS Application Data** | **Ciphertext (AES-GCM / ChaCha20-Poly1305)** | IP 5-tuple, packet timing, packet length, TCP window size, TCP flags | **HTTP Method** (`GET`, `POST`), **URL Path / Route**, **HTTP Headers**, **Status Codes**, **Payloads** |

### Formal Statement:
API-Sentinel **does not claim that network-level eBPF filters (TC/clsact) on encrypted packets expose HTTP routes or API transaction semantics**. Any claim that packet-level inspection of TLS ciphertext yields HTTP routes is technically false and rejected by Member 1 and Member 2.

---

## 3. Agreed HTTPS-Safe Observation Points

To achieve 100% API route discovery and shadow API detection for HTTPS workloads without compromising encryption, Members 1, 2, and 5 agree on the following approved observation points:

### Observation Point A: Reverse Proxy Cleartext Egress (Primary Standard)
In production microservice architectures (Kubernetes, Service Mesh, Docker Compose):
1. External clients connect over HTTPS/TLS to the Ingress Controller / Reverse Proxy (Envoy, Nginx, Traefik, or Cloudflare Tunnel).
2. The Reverse Proxy terminates TLS and forwards the cleartext HTTP request over local network namespaces (`lo`, unix domain socket, or pod `veth`) to the internal FastAPI service (e.g., `http://127.0.0.1:8000` or `http://mock-api:8080`).
3. **The eBPF TC sensor attaches to the internal cleartext interface** (`lo` or `veth`), capturing pristine HTTP metadata post-decryption.
4. **Security Advantage:** Zero access to private TLS keys; no performance overhead on cryptography; zero risk of TLS downgrades.

### Observation Point B: Application Boundary Uprobes (Alternative for Direct TLS)
If the API service terminates TLS in-process without an external reverse proxy:
1. eBPF uprobes attach to user-space cryptography libraries (OpenSSL/BoringSSL) at `SSL_read` and `SSL_write` return points, or as an ASGI middleware hook in FastAPI.
2. Plaintext buffers are observed immediately after user-space decryption, before application routing.
3. **Security Advantage:** Keys are never inspected, dumped, or exported.

---

## 4. Privacy & Telemetry Redaction Rules

Regardless of the observation point, all telemetry emitted to the BPF RingBuffer (`struct api_event`) strictly adheres to Section 3 of `data-classification-policy.md`:

| Category | Telemetry Status | In-Kernel Enforcement Mechanism |
|---|:---:|---|
| **Credentials & Auth Tokens** | **STRICTLY EXCLUDED** | The sensor inspects only the request-line (`METHOD URI HTTP/1.1`). It never parses or buffers header lines (`Authorization: Bearer ...`, `X-API-Key`). |
| **Cookies** | **STRICTLY EXCLUDED** | `Cookie:` header is completely bypassed; zero cookie tokens are recorded. |
| **Request & Response Bodies** | **STRICTLY EXCLUDED** | JSON, XML, or form bodies are never copied. Only the total byte length (`payload_bytes`) is recorded for rate calculation. |
| **Query Parameter Values** | **STRICTLY STRIPPED** | The route parser truncates the URI at the `'?'` delimiter. `/api/v1/orders?user=123&token=xyz` is emitted as `/api/v1/orders` and tagged with `API_EVENT_FLAG_QUERY_STRIPPED`. |
| **Unapproved Raw Paths** | **BOUNDED & TRUNCATED** | Maximum path length is strictly bounded to 127 ASCII characters. Oversized routes are safely null-terminated and flagged with `API_EVENT_FLAG_ROUTE_TRUNCATED`. |

---

## 5. Verification & Compliance Sign-Off

- **Member 1 (Security Architect):** Confirms observation architecture preserves TLS integrity and satisfies data classification policies.
- **Member 2 (eBPF Traffic Engineer):** Implemented in-kernel redaction in `ebpf/src/api_sentinel_sensor.c` and validated via `tests/test_working_sensor_runtime.py`.
- **Member 5 (Mock API Engineer):** Configured local FastAPI test harness on port 8000/8080 to support cleartext internal observation testing.
