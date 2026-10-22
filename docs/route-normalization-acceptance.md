# Route-Normalization Acceptance Specification

**Owner:** Member 1 - Team Lead and Security Architect

**Acceptance owner:** Member 4 - Python Detection Engineer, with Member 1 review

**Baseline date:** 2026-10-13

**Status:** Approved Day 8 acceptance baseline; implementation evidence pending

## 1. Purpose and security boundary

This specification defines deterministic acceptance behavior for converting an
observed HTTP method and request-target path into a privacy-safe route key for
OpenAPI comparison. It covers the current checked-in contract and the behavior
required when the input is unknown, malformed or hostile.

The normalizer is a classification control, not a URL router, authorization
control or input sanitizer for the mock API. A normalized match never proves
that a request was authenticated, authorized or served. Input is accepted only
from the separately approved observation boundary; this document does not
approve TLS weakening or raw traffic retention.

## 2. Approved contract and output

The template registry is compiled from the versioned `paths` and operations in
[`openapi.yaml`](openapi.yaml). For the current contract it contains:

| Canonical method | Canonical route template |
|---|---|
| `GET` | `/orders` |
| `GET` | `/orders/{orderId}` |
| `PATCH` | `/orders/{orderId}` |
| `GET` | `/admin/orders` |

Each accepted observation produces only these fields:

| Field | Required value |
|---|---|
| `method` | Validated, ASCII-uppercase method |
| `route` | Matched OpenAPI template, or `/__unknown__` when no template matches |
| `classification` | `documented`, `method_not_documented`, `path_not_documented` or `invalid` |
| `unknown_route_token` | `null` except for `path_not_documented`; then an opaque keyed fingerprint |
| `unknown_route_key_version` | `null` except for `path_not_documented`; then the non-secret HMAC key version |
| `reason_code` | Stable code describing the decision |
| `contract_version` | Immutable identifier of the OpenAPI input used for matching |

The inventory key is `(method, route, unknown_route_token,
unknown_route_key_version, contract_version)`. An invalid observation is
counted by `reason_code` but is not added to the route inventory. Raw request
targets, decoded parameter values and query data are not output fields.

## 3. Normative normalization rules

The words **MUST**, **MUST NOT** and **SHOULD** are requirements for acceptance.

1. **Bound the raw input first.** The method MUST be 1-16 ASCII bytes and match
   the HTTP token grammar. The entire request target MUST be at most 4,096 raw
   bytes. Its path component MUST be 1-2,048 raw bytes, start with `/`, contain
   at most 32 segments and contain no ASCII control character or backslash.
   Each decoded segment MUST be at most 128 UTF-8 bytes. An input outside a
   bound is `invalid` and MUST NOT be partially normalized.
2. **Separate the request target structurally.** Only the path component before
   the first literal `?` is eligible for matching. The query delimiter, names
   and values MUST NOT affect the route key, fingerprint, logs or metrics. A
   fragment delimiter `#` is invalid in an HTTP request target.
3. **Validate encoding once.** Percent triplets are decoded exactly once using
   strict UTF-8. Malformed triplets, invalid UTF-8, NUL/control characters,
   encoded `/` or `\`, and a residual percent triplet after the single decode
   are `invalid`. Hex digits are case-insensitive. There is no recursive decode.
4. **Reject ambiguous path syntax.** Empty interior segments, repeated `/`, and
   the decoded segments `.` or `..` are `invalid`. Literal or encoded traversal
   is rejected before template matching. A trailing slash is not silently
   removed: `/orders/` is a distinct, undocumented path.
5. **Canonicalize the method.** A valid method is converted to ASCII uppercase.
   Operations are documented only when explicitly present in the approved
   OpenAPI contract. In particular, `HEAD`, `OPTIONS` and `DELETE` are not
   inferred from a declared `GET`.
6. **Match complete segments.** Static template segments match decoded path
   segments exactly and case-sensitively. A parameter occupies exactly one
   complete segment. Static templates take precedence over parameter templates;
   method does not change path-template selection.
7. **Enforce parameter schemas.** A structurally matching parameter MUST meet
   the OpenAPI type, length and pattern constraints. The current `orderId` is
   1-64 ASCII characters matching `^[A-Za-z0-9-]+$`. A structurally matching
   path with an out-of-policy parameter is `invalid`, not a new route.
8. **Do not guess templates.** A path with no registry match is
   `path_not_documented` with route `/__unknown__`. The implementation MUST NOT
   generalize digit-, UUID- or entropy-looking segments into invented templates.
9. **Separate method drift from path drift.** If a valid path matches a known
   template but its method is absent from that template, preserve the template
   and emit `method_not_documented`. If both method and path are known, emit
   `documented`.
10. **Fail contract compilation safely.** Duplicate method/template entries,
    indistinguishable parameter templates at the same precedence, unsupported
    parameter schemas or an unversioned registry MUST fail startup/contract
    loading. Runtime traffic MUST NOT choose a template by map iteration order.

### Stable reason codes

| Classification | Reason code | Meaning |
|---|---|---|
| `documented` | `DOCUMENTED_OPERATION` | Method and template are declared |
| `method_not_documented` | `METHOD_NOT_IN_CONTRACT` | Template exists; method does not |
| `path_not_documented` | `PATH_NOT_IN_CONTRACT` | No approved template matches |
| `invalid` | `INVALID_METHOD` | Method grammar or length failed |
| `invalid` | `INVALID_PATH_BOUNDS` | Path byte/segment bound failed |
| `invalid` | `INVALID_PATH_ENCODING` | Percent or UTF-8 validation failed |
| `invalid` | `AMBIGUOUS_PATH_SYNTAX` | Separator, backslash or dot-segment rule failed |
| `invalid` | `INVALID_PARAMETER` | A structural template match failed its parameter schema |

## 4. Unknown-route privacy

Unknown paths can contain names, tokens and object identifiers. They MUST NOT be
stored or logged verbatim. `unknown_route_token` MUST be a deterministic keyed
fingerprint of the validated, decoded path only, using an approved secret key
and recording a non-secret key version. At least 128 bits of HMAC-SHA-256 output
MUST be retained. The key belongs in the runtime secret store, not this
repository. Plain hashing is prohibited because common paths and predictable
identifiers are enumerable.

The token permits aggregation of the same unknown path within a key version; it
is not a route template and MUST NOT be reversible. Query data is excluded from
the fingerprint. Key rotation may break cross-version correlation by design.
Access to unknown-route findings remains Restricted under
[`data-classification-policy.md`](data-classification-policy.md).

The normalizer and its error path MUST NOT emit raw paths, parameter values,
query strings, authorization headers, cookies or bodies. Metrics use only
classification, reason code and bounded counters. Diagnostic sampling requires
a separate privacy review and is disabled by default.

## 5. Acceptance cases

`token(path)` below means the opaque keyed fingerprint required by Section 4;
the literal path is shown only as synthetic test input and is never expected in
runtime output. Every case also expects the active `contract_version` and no raw
input or parameter field in the output.

### 5.1 Templates and methods

| ID | Method | Request target | Expected route | Classification / reason |
|---|---|---|---|---|
| RN-T01 | `GET` | `/orders` | `/orders` | `documented` / `DOCUMENTED_OPERATION` |
| RN-T02 | `GET` | `/orders/order-1001` | `/orders/{orderId}` | `documented` / `DOCUMENTED_OPERATION` |
| RN-T03 | `PATCH` | `/orders/A9-Z` | `/orders/{orderId}` | `documented` / `DOCUMENTED_OPERATION` |
| RN-T04 | `GET` | `/admin/orders` | `/admin/orders` | `documented` / `DOCUMENTED_OPERATION` |
| RN-T05 | `get` | `/orders` | `/orders` | canonical method `GET`; `documented` / `DOCUMENTED_OPERATION` |
| RN-T06 | `DELETE` | `/orders/order-1001` | `/orders/{orderId}` | `method_not_documented` / `METHOD_NOT_IN_CONTRACT` |
| RN-T07 | `HEAD` | `/orders` | `/orders` | `method_not_documented` / `METHOD_NOT_IN_CONTRACT` |
| RN-T08 | `GE T` | `/orders` | no inventory record | `invalid` / `INVALID_METHOD` |
| RN-T09 | 17 ASCII method bytes | `/orders` | no inventory record | `invalid` / `INVALID_METHOD` |
| RN-T10 | `GET` | `/Orders` | `/__unknown__`, `token('/Orders')` | `path_not_documented` / `PATH_NOT_IN_CONTRACT` |
| RN-T11 | `GET` | `/orders/` | `/__unknown__`, `token('/orders/')` | `path_not_documented` / `PATH_NOT_IN_CONTRACT` |

### 5.2 Query exclusion and unknown routes

| ID | Method | Request target | Expected route | Classification / reason |
|---|---|---|---|---|
| RN-Q01 | `GET` | `/orders?owner=user-a&token=synthetic-secret` | `/orders`; no query output | `documented` / `DOCUMENTED_OPERATION` |
| RN-Q02 | `GET` | `/orders/order-1001?expand=owner` | `/orders/{orderId}`; no query output | `documented` / `DOCUMENTED_OPERATION` |
| RN-Q03 | `GET` | `/orders?x=1` and `/orders?x=2` | identical `GET /orders` keys | both `documented` / `DOCUMENTED_OPERATION` |
| RN-Q04 | `POST` | `/internal/health?access_token=synthetic-secret` | `/__unknown__`, `token('/internal/health')`; no query output | `path_not_documented` / `PATH_NOT_IN_CONTRACT` |
| RN-Q05 | `GET` | request target of 4,097 raw bytes with a valid `/orders?` prefix | no inventory record; query absent | `invalid` / `INVALID_PATH_BOUNDS` |
| RN-U01 | `GET` | `/shadow/orders` | `/__unknown__`, `token('/shadow/orders')` | `path_not_documented` / `PATH_NOT_IN_CONTRACT` |
| RN-U02 | `GET` | `/orders/123/details` | `/__unknown__`, `token('/orders/123/details')` | `path_not_documented` / `PATH_NOT_IN_CONTRACT` |
| RN-U03 | `GET` | `/users/550e8400-e29b-41d4-a716-446655440000` | `/__unknown__`; no invented `/users/{id}` | `path_not_documented` / `PATH_NOT_IN_CONTRACT` |
| RN-U04 | `POST` | `/unknown/synthetic-person@example.invalid` | `/__unknown__`; raw value absent | `path_not_documented` / `PATH_NOT_IN_CONTRACT` |

### 5.3 Encoding and traversal

| ID | Method | Request target | Expected route | Classification / reason |
|---|---|---|---|---|
| RN-E01 | `GET` | `/%6Frders` | `/orders` | `documented` / `DOCUMENTED_OPERATION` |
| RN-E02 | `GET` | `/orders/order%2D1001` | `/orders/{orderId}` | `documented` / `DOCUMENTED_OPERATION` |
| RN-E03 | `GET` | `/orders/%ZZ` | no inventory record | `invalid` / `INVALID_PATH_ENCODING` |
| RN-E04 | `GET` | `/orders/%C3%28` | no inventory record | `invalid` / `INVALID_PATH_ENCODING` |
| RN-E05 | `GET` | `/orders%2Forder-1001` | no inventory record | `invalid` / `INVALID_PATH_ENCODING` |
| RN-E06 | `GET` | `/orders%5Corder-1001` | no inventory record | `invalid` / `INVALID_PATH_ENCODING` |
| RN-E07 | `GET` | `/orders/%256F%2572%2564%2565%2572` | no inventory record | `invalid` / `INVALID_PATH_ENCODING` |
| RN-E08 | `GET` | `/orders/%00` | no inventory record | `invalid` / `INVALID_PATH_ENCODING` |
| RN-X01 | `GET` | `/orders/../admin/orders` | no inventory record | `invalid` / `AMBIGUOUS_PATH_SYNTAX` |
| RN-X02 | `GET` | `/orders/%2e%2e/admin/orders` | no inventory record | `invalid` / `AMBIGUOUS_PATH_SYNTAX` |
| RN-X03 | `GET` | `/orders/./order-1001` | no inventory record | `invalid` / `AMBIGUOUS_PATH_SYNTAX` |
| RN-X04 | `GET` | `//orders` | no inventory record | `invalid` / `AMBIGUOUS_PATH_SYNTAX` |
| RN-X05 | `GET` | `/orders\\order-1001` | no inventory record | `invalid` / `AMBIGUOUS_PATH_SYNTAX` |
| RN-X06 | `GET` | `/orders#synthetic-fragment` | no inventory record | `invalid` / `AMBIGUOUS_PATH_SYNTAX` |

### 5.4 Parameter and resource bounds

| ID | Method | Request target | Expected route | Classification / reason |
|---|---|---|---|---|
| RN-B01 | `GET` | `/orders/` + `a` repeated 64 times | `/orders/{orderId}` | `documented` / `DOCUMENTED_OPERATION` |
| RN-B02 | `GET` | `/orders/` + `a` repeated 65 times | no inventory record; value absent | `invalid` / `INVALID_PARAMETER` |
| RN-B03 | `GET` | `/orders/order_1001` | no inventory record; value absent | `invalid` / `INVALID_PARAMETER` |
| RN-B04 | `GET` | `/orders/caf%C3%A9` | no inventory record; value absent | `invalid` / `INVALID_PARAMETER` |
| RN-B05 | `GET` | empty path | no inventory record | `invalid` / `INVALID_PATH_BOUNDS` |
| RN-B06 | `GET` | `/` plus 16 slash-separated segments of 127 `a` bytes (2,048 raw bytes) | `/__unknown__`, keyed token | `path_not_documented` / `PATH_NOT_IN_CONTRACT` |
| RN-B07 | `GET` | same construction with one segment at 128 `a` bytes (2,049 raw bytes) | no inventory record | `invalid` / `INVALID_PATH_BOUNDS` |
| RN-B08 | `GET` | path with 32 one-byte `a` segments | `/__unknown__`, keyed token | `path_not_documented` / `PATH_NOT_IN_CONTRACT` |
| RN-B09 | `GET` | path with 33 one-byte `a` segments | no inventory record | `invalid` / `INVALID_PATH_BOUNDS` |
| RN-B10 | `GET` | `/unknown/` plus one 128-byte ASCII segment | `/__unknown__`, keyed token | `path_not_documented` / `PATH_NOT_IN_CONTRACT` |
| RN-B11 | `GET` | `/unknown/` plus one 129-byte ASCII segment | no inventory record | `invalid` / `INVALID_PATH_BOUNDS` |

### 5.5 Privacy and determinism

| ID | Requirement | Expected result |
|---|---|---|
| RN-P01 | Normalize two observations of the same unknown path and key version | Same `unknown_route_token`; no raw path |
| RN-P02 | Normalize the same unknown path with different queries | Same token because query is excluded before fingerprinting |
| RN-P03 | Normalize two different unknown paths | Different tokens except at cryptographic collision probability |
| RN-P04 | Rotate the HMAC key version | New observations set `unknown_route_key_version` to the new non-secret version; no key material appears |
| RN-P05 | Inspect success, invalid-input and exception logs | No raw target, parameter, query, header, cookie or body appears |
| RN-P06 | Inspect metrics labels | Only bounded classification/reason labels; no path, parameter or token labels |
| RN-P07 | Load two indistinguishable parameter templates such as `/orders/{id}` and `/orders/{name}` | Contract compilation fails; runtime does not choose one |
| RN-P08 | Repeat every case with identical contract and key versions | Byte-for-byte identical normalized decision |

## 6. Required implementation evidence

Member 4 must convert every `RN-*` row into an automated test. Generated bound
cases must assert the actual byte and segment counts. Acceptance requires:

- all cases pass against a pinned OpenAPI contract version;
- contract-load ambiguity and unsupported-schema failures are tested;
- property/fuzz tests cover malformed percent input, traversal variants and
  limit-adjacent values without crashes or unbounded allocation;
- a log/metric capture proves the privacy cases across success and failure paths;
- false-positive and false-negative results are reported separately; and
- Member 1 and the producing observation/collector owner review the evidence.

This Day 8 specification establishes expected behavior only. It does not claim
that a normalizer, keyed fingerprint service or executable corpus currently
exists, and it does not close R-011 or R-013.
