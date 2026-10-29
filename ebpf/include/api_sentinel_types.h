/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
/* Copyright (c) 2026 API-Sentinel Team */
#ifndef __API_SENTINEL_TYPES_H__
#define __API_SENTINEL_TYPES_H__

#ifndef __KERNEL__
#include <stdint.h>
typedef uint8_t  __u8;
typedef uint16_t __u16;
typedef uint32_t __u32;
typedef uint64_t __u64;
#endif

/* HTTP Method Enums */
enum api_http_method {
    METHOD_UNKNOWN = 0,
    METHOD_GET     = 1,
    METHOD_POST    = 2,
    METHOD_PUT     = 3,
    METHOD_DELETE  = 4,
    METHOD_PATCH   = 5,
    METHOD_HEAD    = 6,
    METHOD_OPTIONS = 7,
};

/* Event Direction */
enum api_direction {
    DIRECTION_INGRESS = 0,
    DIRECTION_EGRESS  = 1,
};

/* Operational Mode */
enum api_enforcement_mode {
    MODE_OBSERVE_ONLY   = 0,
    MODE_RATE_LIMIT     = 1,
    MODE_STRICT_ENFORCE = 2,
};

/* Metric Indices for api_sentinel_stats */
enum api_stat_index {
    STAT_TOTAL_PACKETS       = 0,
    STAT_API_EVENTS_EMITTED  = 1,
    STAT_RINGBUF_DROPS       = 2,
    STAT_MALFORMED_PACKETS   = 3,
    STAT_ENFORCEMENT_DROPS   = 4,
    STAT_MAX_METRICS         = 16,
};

#define ROUTE_MARKER_MAX_LEN 128

/* Schema Version Definitions */
#define API_EVENT_SCHEMA_VERSION_V1    1
#define API_EVENT_SCHEMA_VERSION_MASK  0xFF000000U
#define API_EVENT_SCHEMA_VERSION_SHIFT 24

/* Flag bit definitions for struct api_event.flags (lower 24 bits) */
#define API_EVENT_FLAG_ROUTE_TRUNCATED (1U << 0) /* Route marker truncated at ROUTE_MARKER_MAX_LEN - 1 */
#define API_EVENT_FLAG_IPV6            (1U << 1) /* Flow is IPv6 */
#define API_EVENT_FLAG_QUERY_STRIPPED  (1U << 2) /* Query parameter values stripped from route */
#define API_EVENT_FLAG_DROP_OCCURRED   (1U << 3) /* Preceding ring buffer drop occurred */
#define API_EVENT_FLAG_MONITOR_ONLY    (1U << 4) /* Captured in monitor-only mode */

/* Macro to pack schema version and flags into event flags */
#define PACK_API_EVENT_FLAGS(version, flags) \
    ((((__u32)(version) & 0xFFU) << API_EVENT_SCHEMA_VERSION_SHIFT) | ((__u32)(flags) & 0x00FFFFFFU))

/* Macro to extract schema version from event flags */
#define GET_API_EVENT_SCHEMA_VERSION(flags) \
    (((__u32)(flags) & API_EVENT_SCHEMA_VERSION_MASK) >> API_EVENT_SCHEMA_VERSION_SHIFT)

/* Macro to extract flag bits excluding schema version */
#define GET_API_EVENT_FLAGS(flags) \
    ((__u32)(flags) & 0x00FFFFFFU)

/* Flow Key (24 Bytes, 64-bit aligned) */
struct flow_key {
    __u32 src_ip;          /* Source IP (IPv4) */
    __u32 dst_ip;          /* Destination IP (IPv4) */
    __u16 src_port;        /* Source Port (Network Byte Order) */
    __u16 dst_port;        /* Destination Port (Network Byte Order) */
    __u8  protocol;        /* L4 Protocol (e.g. 6 = TCP) */
    __u8  ip_version;      /* IP Version (4 or 6) */
    __u8  _padding[2];     /* Alignment padding */
    __u64 flow_hash;       /* Calculated Flow Hash */
};

/* Session Metadata (32 Bytes, 64-bit aligned) */
struct session_metadata {
    __u32 pid;             /* Process ID */
    __u32 tgid;            /* Thread Group ID */
    __u32 uid;             /* User ID */
    __u32 gid;             /* Group ID */
    __u64 start_ktime_ns;  /* Connection start monotonic timestamp */
    __u32 flags;           /* Session flags */
    __u32 _reserved;       /* 64-bit boundary padding */
};

/* Runtime Configuration (32 Bytes, 64-bit aligned) */
struct capture_config {
    __u32 enabled;           /* 1 = capture active, 0 = bypassed */
    __u16 target_port;       /* Primary API port (e.g., 80) */
    __u16 target_port_alt;   /* Secondary API port (e.g., 8080) */
    __u32 sampling_rate_pct; /* 1 - 100% sampling rate */
    __u32 enforcement_mode;  /* 0 = Observe, 1 = Limit, 2 = Block */
    __u64 drop_mask;         /* Bitmask for policy rules */
    __u64 _padding;          /* Alignment padding */
};

/* Main Observation Event (192 Bytes, 64-bit aligned) */
struct api_event {
    /* Header (24 Bytes) */
    __u64 timestamp_ns;      /* Kernel monotonic timestamp */
    __u32 event_id;          /* Low 32 bits of shared atomic sequence; zero is valid */
    __u32 pid;               /* Process ID */
    __u32 tgid;              /* Thread Group ID */
    __u32 uid;               /* User ID */

    /* Network Flow (24 Bytes) */
    struct flow_key flow;

    /* Protocol Metadata (16 Bytes) */
    __u8  http_method;       /* Enum api_http_method */
    __u8  direction;         /* Enum api_direction */
    __u16 status_code;       /* HTTP status code */
    __u32 payload_bytes;     /* Payload size in bytes */
    __u32 latency_us;        /* Response latency in microseconds */
    __u32 flags;             /* Flags (e.g. truncated route) */

    /* Bounded Route Marker (128 Bytes) */
    char  route_marker[ROUTE_MARKER_MAX_LEN];
};

#endif /* __API_SENTINEL_TYPES_H__ */
