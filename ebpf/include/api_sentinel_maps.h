/* SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause) */
/* Copyright (c) 2026 API-Sentinel Team */
#ifndef __API_SENTINEL_MAPS_H__
#define __API_SENTINEL_MAPS_H__

#include "api_sentinel_types.h"

/* Memory Size & Capacity Bounds */
#define EVENTS_RINGBUF_SIZE       (8 * 1024 * 1024) /* 8 MB Power-of-2 page-aligned */
#define SESSIONS_MAP_MAX_ENTRIES  65536             /* 64K connections */
#define CONFIG_MAP_MAX_ENTRIES    16
#define STATS_MAP_MAX_ENTRIES     STAT_MAX_METRICS  /* 16 per-CPU counters */

#ifdef __KERNEL__
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

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

#endif /* __KERNEL__ */

#endif /* __API_SENTINEL_MAPS_H__ */
