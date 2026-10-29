/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
/* Copyright (c) 2026 API-Sentinel Team */
/* Member 2 — eBPF Capture (Bounded Linux Sensor) */

#define __KERNEL__ 1

#include "../include/api_sentinel_types.h"

/* Provide BPF map and helper declarations compatible with libbpf and standard clang */
#ifndef BPF_MAP_TYPE_RINGBUF
#define BPF_MAP_TYPE_RINGBUF 27
#endif
#ifndef BPF_MAP_TYPE_LRU_HASH
#define BPF_MAP_TYPE_LRU_HASH 10
#endif
#ifndef BPF_MAP_TYPE_PERCPU_ARRAY
#define BPF_MAP_TYPE_PERCPU_ARRAY 6
#endif
#ifndef BPF_MAP_TYPE_ARRAY
#define BPF_MAP_TYPE_ARRAY 2
#endif

#ifndef SEC
#define SEC(NAME) __attribute__((section(NAME), used))
#endif

#ifndef __uint
#define __uint(name, val) int (*name)[val]
#endif
#ifndef __type
#define __type(name, val) typeof(val) *name
#endif

/* Networking definitions */
#ifndef TC_ACT_OK
#define TC_ACT_OK 0
#endif
#ifndef TC_ACT_SHOT
#define TC_ACT_SHOT 2
#endif

#ifndef ETH_P_IP
#define ETH_P_IP 0x0800
#endif
#ifndef ETH_P_IPV6
#define ETH_P_IPV6 0x86DD
#endif
#ifndef IPPROTO_TCP
#define IPPROTO_TCP 6
#endif

#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
#define bpf_htons(x) ((__u16)((((__u16)(x) & 0xff00) >> 8) | (((__u16)(x) & 0x00ff) << 8)))
#define bpf_ntohs(x) bpf_htons(x)
#define bpf_htonl(x) ((__u32)((((__u32)(x) & 0xff000000) >> 24) | \
                              (((__u32)(x) & 0x00ff0000) >> 8)  | \
                              (((__u32)(x) & 0x0000ff00) << 8)  | \
                              (((__u32)(x) & 0x000000ff) << 24)))
#define bpf_ntohl(x) bpf_htonl(x)
#else
#define bpf_htons(x) (x)
#define bpf_ntohs(x) (x)
#define bpf_htonl(x) (x)
#define bpf_ntohl(x) (x)
#endif

/* Linux sk_buff layout abstraction for TC filters */
struct __sk_buff {
    __u32 len;
    __u32 pkt_type;
    __u32 mark;
    __u32 queue_mapping;
    __u32 protocol;
    __u32 vlan_present;
    __u32 vlan_tci;
    __u32 vlan_proto;
    __u32 priority;
    __u32 ingress_ifindex;
    __u32 ifindex;
    __u32 tc_index;
    __u32 cb[5];
    __u32 hash;
    __u32 tc_classid;
    __u32 data;
    __u32 data_end;
    __u32 napi_id;
};

/* L2 Ethernet header */
struct ethhdr {
    unsigned char h_dest[6];
    unsigned char h_source[6];
    __u16 h_proto;
} __attribute__((packed));

/* L3 IPv4 header */
struct iphdr {
    __u8 ihl:4, version:4;
    __u8 tos;
    __u16 tot_len;
    __u16 id;
    __u16 frag_off;
    __u8 ttl;
    __u8 protocol;
    __u16 check;
    __u32 saddr;
    __u32 daddr;
} __attribute__((packed));

/* L3 IPv6 header */
struct ipv6hdr {
    __u8 priority:4, version:4;
    __u8 flow_lbl[3];
    __u16 payload_len;
    __u8 nexthdr;
    __u8 hop_limit;
    __u8 saddr[16];
    __u8 daddr[16];
} __attribute__((packed));

/* L4 TCP header */
struct tcphdr {
    __u16 source;
    __u16 dest;
    __u32 seq;
    __u32 ack_seq;
    __u16 res1:4, doff:4, fin:1, syn:1, rst:1, psh:1, ack:1, urg:1, ece:1, cwr:1;
    __u16 window;
    __u16 check;
    __u16 urg_ptr;
} __attribute__((packed));

/* BPF Helper function prototypes (Linux ABI) */
static void *(*bpf_ringbuf_reserve)(void *ringbuf, __u64 size, __u64 flags) = (void *)131;
static void (*bpf_ringbuf_submit)(void *data, __u64 flags) = (void *)132;
static void (*bpf_ringbuf_discard)(void *data, __u64 flags) = (void *)133;
static __u64 (*bpf_ktime_get_ns)(void) = (void *)5;
static void *(*bpf_map_lookup_elem)(void *map, const void *key) = (void *)1;
static long (*bpf_map_update_elem)(void *map, const void *key, const void *value, __u64 flags) = (void *)2;

/* BPF Maps defined according to Section 3 of Day 2 Specification */
#define EVENTS_RINGBUF_SIZE       (8 * 1024 * 1024) /* 8 MB power-of-2 */
#define SESSIONS_MAP_MAX_ENTRIES  65536             /* 64K connections */
#define CONFIG_MAP_MAX_ENTRIES    16
#define STATS_MAP_MAX_ENTRIES     STAT_MAX_METRICS  /* 16 per-CPU counters */

/* Map 1: Ring Buffer for Kernel -> User Event Telemetry */
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, EVENTS_RINGBUF_SIZE);
} api_sentinel_events SEC(".maps");

/* Map 2: LRU Hash for Active Flow-to-Session Correlation */
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, SESSIONS_MAP_MAX_ENTRIES);
    __type(key, struct flow_key);
    __type(value, struct session_metadata);
} api_sentinel_sessions SEC(".maps");

/* Map 3: Per-CPU Array for Zero-Lock Monotonic Performance Metrics */
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, STATS_MAP_MAX_ENTRIES);
    __type(key, __u32);
    __type(value, __u64);
} api_sentinel_stats SEC(".maps");

/* Map 4: Array for Policy & Runtime Capture Configuration */
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, CONFIG_MAP_MAX_ENTRIES);
    __type(key, __u32);
    __type(value, struct capture_config);
} api_sentinel_config SEC(".maps");

/* Map 5: Shared atomic event sequence across ingress and egress CPUs. */
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, __u64);
} api_sentinel_event_sequence SEC(".maps");

/* Helper to atomically increment per-CPU stat counter */
static __attribute__((always_inline)) void increment_stat(__u32 index)
{
    __u32 key = index;
    __u64 *val = bpf_map_lookup_elem(&api_sentinel_stats, &key);
    if (val) {
        *val += 1;
    }
}

/*
 * Allocate a shared sequence before ring-buffer reservation. If reservation
 * fails, the resulting gap and STAT_RINGBUF_DROPS both record the loss. The
 * 32-bit wire field is a modulo counter; consumers must not infer request IDs.
 */
static __attribute__((always_inline)) int next_event_id(__u32 *event_id)
{
    __u32 key = 0;
    __u64 *sequence = bpf_map_lookup_elem(&api_sentinel_event_sequence, &key);
    if (!sequence)
        return 0;
    /* Wire IDs use the low 32 bits; zero is valid at modulo wraparound. */
    *event_id = (__u32)(__sync_fetch_and_add(sequence, 1) + 1);
    return 1;
}

/* Helper to parse HTTP method tokens safely within packet bounds */
static __attribute__((always_inline)) __u8 parse_http_method(const char *payload, const void *data_end)
{
    if ((const void *)(payload + 4) > data_end)
        return METHOD_UNKNOWN;

    if (payload[0] == 'G' && payload[1] == 'E' && payload[2] == 'T' && payload[3] == ' ')
        return METHOD_GET;
    if (payload[0] == 'P' && payload[1] == 'U' && payload[2] == 'T' && payload[3] == ' ')
        return METHOD_PUT;

    if ((const void *)(payload + 5) > data_end)
        return METHOD_UNKNOWN;

    if (payload[0] == 'P' && payload[1] == 'O' && payload[2] == 'S' && payload[3] == 'T' && payload[4] == ' ')
        return METHOD_POST;
    if (payload[0] == 'H' && payload[1] == 'E' && payload[2] == 'A' && payload[3] == 'D' && payload[4] == ' ')
        return METHOD_HEAD;

    if ((const void *)(payload + 6) > data_end)
        return METHOD_UNKNOWN;

    if (payload[0] == 'P' && payload[1] == 'A' && payload[2] == 'T' && payload[3] == 'C' && payload[4] == 'H' && payload[5] == ' ')
        return METHOD_PATCH;

    if ((const void *)(payload + 7) > data_end)
        return METHOD_UNKNOWN;

    if (payload[0] == 'D' && payload[1] == 'E' && payload[2] == 'L' && payload[3] == 'E' && payload[4] == 'T' && payload[5] == 'E' && payload[6] == ' ')
        return METHOD_DELETE;

    if ((const void *)(payload + 8) > data_end)
        return METHOD_UNKNOWN;

    if (payload[0] == 'O' && payload[1] == 'P' && payload[2] == 'T' && payload[3] == 'I' && payload[4] == 'O' && payload[5] == 'N' && payload[6] == 'S' && payload[7] == ' ')
        return METHOD_OPTIONS;

    return METHOD_UNKNOWN;
}

/* Helper to get offset to URI path after method token */
static __attribute__((always_inline)) __u32 get_method_offset(__u8 method)
{
    switch (method) {
        case METHOD_GET:     return 4;
        case METHOD_PUT:     return 4;
        case METHOD_POST:    return 5;
        case METHOD_HEAD:    return 5;
        case METHOD_PATCH:   return 6;
        case METHOD_DELETE:  return 7;
        case METHOD_OPTIONS: return 8;
        default:             return 0;
    }
}

/*
 * Primary Ingress Classifier Hook
 * SEC("tc") or SEC("classifier/ingress")
 * Attach Point: Direct network interface (clsact qdisc ingress)
 * Operational Guarantee: Monitor-only (always returns TC_ACT_OK)
 */
SEC("classifier/ingress")
int api_sentinel_tc_ingress(struct __sk_buff *skb)
{
    void *data = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;

    increment_stat(STAT_TOTAL_PACKETS);

    /* 1. Parse L2 Ethernet header */
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return TC_ACT_OK;

    __u16 h_proto = bpf_ntohs(eth->h_proto);

    /* 2. Parse L3 IP header (IPv4 or IPv6) */
    struct flow_key flow = {0};
    void *l4_header = 0;

    if (h_proto == ETH_P_IP) {
        struct iphdr *iph = (void *)(eth + 1);
        if ((void *)(iph + 1) > data_end)
            return TC_ACT_OK;

        if (iph->ihl < 5) {
            increment_stat(STAT_MALFORMED_PACKETS);
            return TC_ACT_OK;
        }

        if (iph->protocol != IPPROTO_TCP)
            return TC_ACT_OK;

        flow.src_ip = iph->saddr;
        flow.dst_ip = iph->daddr;
        flow.protocol = IPPROTO_TCP;
        flow.ip_version = 4;

        l4_header = (void *)iph + (iph->ihl * 4);
    } else if (h_proto == ETH_P_IPV6) {
        struct ipv6hdr *ip6h = (void *)(eth + 1);
        if ((void *)(ip6h + 1) > data_end)
            return TC_ACT_OK;

        if (ip6h->nexthdr != IPPROTO_TCP)
            return TC_ACT_OK;

        /* Store lower 32 bits of IPv6 addresses into flow key, flag as IPv6 */
        flow.src_ip = *(__u32 *)&ip6h->saddr[12];
        flow.dst_ip = *(__u32 *)&ip6h->daddr[12];
        flow.protocol = IPPROTO_TCP;
        flow.ip_version = 6;

        /* Calculate flow hash covering full 128-bit addresses */
        flow.flow_hash = (*(__u64 *)&ip6h->saddr[0]) ^ (*(__u64 *)&ip6h->daddr[0]) ^
                         (*(__u64 *)&ip6h->saddr[8]) ^ (*(__u64 *)&ip6h->daddr[8]);

        l4_header = (void *)(ip6h + 1);
    } else {
        /* Non-IP packet, ignore safely */
        return TC_ACT_OK;
    }

    /* 3. Parse L4 TCP header */
    struct tcphdr *tcph = l4_header;
    if ((void *)(tcph + 1) > data_end)
        return TC_ACT_OK;

    flow.src_port = tcph->source;
    flow.dst_port = tcph->dest;

    __u32 tcp_hdr_len = tcph->doff * 4;
    if (tcp_hdr_len < sizeof(struct tcphdr)) {
        increment_stat(STAT_MALFORMED_PACKETS);
        return TC_ACT_OK;
    }

    void *payload = (void *)tcph + tcp_hdr_len;
    if (payload > data_end)
        return TC_ACT_OK;

    /* 4. Filter by target API port */
    __u16 dst_port_host = bpf_ntohs(flow.dst_port);
    __u32 config_key = 0;
    struct capture_config *cfg = bpf_map_lookup_elem(&api_sentinel_config, &config_key);
    __u16 target_port = cfg ? cfg->target_port : 80;
    __u16 target_port_alt = cfg ? cfg->target_port_alt : 8080;

    /* Default monitored ports: target_port (80), alt (8080), or 8000/5000 in lab */
    if (dst_port_host != target_port && dst_port_host != target_port_alt &&
        dst_port_host != 8000 && dst_port_host != 5000 && dst_port_host != 80) {
        return TC_ACT_OK;
    }

    /* 5. Detect HTTP Method */
    __u8 method = parse_http_method((const char *)payload, data_end);
    if (method == METHOD_UNKNOWN) {
        /* Not an HTTP request start, pass without recording */
        return TC_ACT_OK;
    }

    /* 6. Extract sanitized Route Marker */
    __u32 method_off = get_method_offset(method);
    const char *uri_start = (const char *)payload + method_off;
    if ((void *)uri_start >= data_end)
        return TC_ACT_OK;

    /* Allocate the shared sequence before reserve so failed reserves leave a gap. */
    __u32 event_id = 0;
    if (!next_event_id(&event_id)) {
        increment_stat(STAT_MALFORMED_PACKETS);
        return TC_ACT_OK;
    }

    /* 7. Zero-Copy Reserve Event in BPF RingBuffer */
    struct api_event *event = bpf_ringbuf_reserve(&api_sentinel_events, sizeof(struct api_event), 0);
    if (!event) {
        /* Backpressure: ringbuffer is saturated */
        increment_stat(STAT_RINGBUF_DROPS);
        return TC_ACT_OK;
    }

    /* Clear every byte, including flow padding and unused route bytes. */
    __builtin_memset(event, 0, sizeof(*event));
    event->event_id = event_id;
    event->timestamp_ns = bpf_ktime_get_ns();
    event->pid = 0;
    event->tgid = 0;
    event->uid = 0;

    /* Correlate session metadata from LRU map if available */
    struct session_metadata *sess = bpf_map_lookup_elem(&api_sentinel_sessions, &flow);
    if (sess) {
        event->pid = sess->pid;
        event->tgid = sess->tgid;
        event->uid = sess->uid;
    }

    event->flow = flow;
    event->http_method = method;
    event->direction = DIRECTION_INGRESS;
    event->status_code = 0;
    event->payload_bytes = (__u32)((unsigned long)data_end - (unsigned long)payload);
    event->latency_us = 0;

    __u32 event_flags = API_EVENT_FLAG_MONITOR_ONLY;
    if (flow.ip_version == 6)
        event_flags |= API_EVENT_FLAG_IPV6;

    /* Copy URI path, stopping at '?', whitespace, or buffer boundary (Privacy Rule) */
    #pragma unroll
    for (int i = 0; i < ROUTE_MARKER_MAX_LEN - 1; i++) {
        const char *p = uri_start + i;
        if ((void *)(p + 1) > data_end) {
            event->route_marker[i] = '\0';
            break;
        }

        char c = *p;
        if (c == ' ' || c == '\r' || c == '\n') {
            event->route_marker[i] = '\0';
            break;
        } else if (c == '?') {
            /* Privacy boundary: Strip query parameters to prevent token/secret leakage */
            event->route_marker[i] = '\0';
            event_flags |= API_EVENT_FLAG_QUERY_STRIPPED;
            break;
        } else {
            event->route_marker[i] = c;
        }

        if (i == ROUTE_MARKER_MAX_LEN - 2) {
            event->route_marker[ROUTE_MARKER_MAX_LEN - 1] = '\0';
            event_flags |= API_EVENT_FLAG_ROUTE_TRUNCATED;
        }
    }
    event->route_marker[ROUTE_MARKER_MAX_LEN - 1] = '\0';

    /* Pack schema version (V1) and flags into 32-bit flags field */
    event->flags = PACK_API_EVENT_FLAGS(API_EVENT_SCHEMA_VERSION_V1, event_flags);

    /* Submit event to ring buffer */
    bpf_ringbuf_submit(event, 0);
    increment_stat(STAT_API_EVENTS_EMITTED);

    return TC_ACT_OK;
}

/*
 * Egress Classifier Hook (Response Observation)
 * SEC("classifier/egress")
 * Monitors HTTP response status codes and calculates latency
 */
SEC("classifier/egress")
int api_sentinel_tc_egress(struct __sk_buff *skb)
{
    void *data = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;

    increment_stat(STAT_TOTAL_PACKETS);

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return TC_ACT_OK;

    if (bpf_ntohs(eth->h_proto) != ETH_P_IP)
        return TC_ACT_OK;

    struct iphdr *iph = (void *)(eth + 1);
    if ((void *)(iph + 1) > data_end || iph->protocol != IPPROTO_TCP)
        return TC_ACT_OK;

    struct tcphdr *tcph = (void *)iph + (iph->ihl * 4);
    if ((void *)(tcph + 1) > data_end)
        return TC_ACT_OK;

    __u32 tcp_hdr_len = tcph->doff * 4;
    void *payload = (void *)tcph + tcp_hdr_len;
    if (payload >= data_end)
        return TC_ACT_OK;

    /* Check for "HTTP/1.1 " response prefix */
    const char *resp = (const char *)payload;
    if ((void *)(resp + 12) > data_end)
        return TC_ACT_OK;

    if (resp[0] == 'H' && resp[1] == 'T' && resp[2] == 'T' && resp[3] == 'P' &&
        resp[4] == '/' && resp[5] == '1' && resp[6] == '.' && resp[7] == '1' && resp[8] == ' ') {
        /* Parse 3-digit status code */
        __u16 code = 0;
        char c1 = resp[9], c2 = resp[10], c3 = resp[11];
        if (c1 >= '0' && c1 <= '9' && c2 >= '0' && c2 <= '9' && c3 >= '0' && c3 <= '9') {
            code = (c1 - '0') * 100 + (c2 - '0') * 10 + (c3 - '0');
        }

        if (code > 0) {
            __u32 event_id = 0;
            if (!next_event_id(&event_id)) {
                increment_stat(STAT_MALFORMED_PACKETS);
                return TC_ACT_OK;
            }
            struct api_event *event = bpf_ringbuf_reserve(&api_sentinel_events, sizeof(struct api_event), 0);
            if (event) {
                /* Prevent stale kernel bytes from entering the ring-buffer record. */
                __builtin_memset(event, 0, sizeof(*event));
                event->event_id = event_id;
                event->timestamp_ns = bpf_ktime_get_ns();
                event->flow.src_ip = iph->saddr;
                event->flow.dst_ip = iph->daddr;
                event->flow.src_port = tcph->source;
                event->flow.dst_port = tcph->dest;
                event->flow.protocol = IPPROTO_TCP;
                event->flow.ip_version = 4;
                event->http_method = METHOD_UNKNOWN;
                event->direction = DIRECTION_EGRESS;
                event->status_code = code;
                event->payload_bytes = (__u32)((unsigned long)data_end - (unsigned long)payload);
                event->flags = PACK_API_EVENT_FLAGS(API_EVENT_SCHEMA_VERSION_V1, API_EVENT_FLAG_MONITOR_ONLY);
                event->route_marker[0] = '\0';
                bpf_ringbuf_submit(event, 0);
                increment_stat(STAT_API_EVENTS_EMITTED);
            } else {
                increment_stat(STAT_RINGBUF_DROPS);
            }
        }
    }

    return TC_ACT_OK;
}

char _license[] SEC("license") = "Dual BSD/GPL";
