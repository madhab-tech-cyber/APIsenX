#!/usr/bin/env bash
# SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
# API-Sentinel eBPF Scoped Cleanup Script
# Role: Member 2 (eBPF Traffic Engineer)
# Removes only this project's recorded programs and pinned maps.

set -euo pipefail

INTERFACE="${1:-lo}"
PIN_DIR="/sys/fs/bpf/api_sentinel"

echo "[*] Cleaning up API-Sentinel sensor from interface '${INTERFACE}'..."

# 1. Remove API-Sentinel specific TC filter
if tc filter show dev "${INTERFACE}" ingress 2>/dev/null | grep -q "bpf"; then
    tc filter del dev "${INTERFACE}" ingress prio 1 handle 1 bpf 2>/dev/null || true
    echo "[+] Removed API-Sentinel TC filter from '${INTERFACE}'"
fi

# 2. Unpin only API-Sentinel maps
if [ -d "${PIN_DIR}" ]; then
    rm -f "${PIN_DIR}/api_sentinel_events" \
          "${PIN_DIR}/api_sentinel_sessions" \
          "${PIN_DIR}/api_sentinel_stats" \
          "${PIN_DIR}/api_sentinel_config"
    rmdir "${PIN_DIR}" 2>/dev/null || true
    echo "[+] Unpinned API-Sentinel maps from ${PIN_DIR}"
fi

echo "[+] Scoped cleanup completed. Unrelated system filters and maps untouched."
