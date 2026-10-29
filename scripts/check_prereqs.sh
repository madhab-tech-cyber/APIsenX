#!/usr/bin/env bash
# ==============================================================================
# API-Sentinel: Linux/eBPF Prerequisites Verification Script
# Role: Member 2 (eBPF Traffic Engineer) - Day 1 Foundation Task
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}   API-Sentinel: eBPF Environment Prerequisite Check  ${NC}"
echo -e "${BLUE}======================================================${NC}"

EXIT_CODE=0

# 1. Kernel Version Check (>= 5.8.0 required for RingBuffer & CAP_BPF)
MIN_KERNEL_MAJOR=5
MIN_KERNEL_MINOR=8

KERNEL_RELEASE=$(uname -r 2>/dev/null || echo "unknown")
echo -e "\n[*] Checking Linux Kernel Release: ${KERNEL_RELEASE}"

if [[ "$KERNEL_RELEASE" =~ ^([0-9]+)\.([0-9]+) ]]; then
    K_MAJOR="${BASH_REMATCH[1]}"
    K_MINOR="${BASH_REMATCH[2]}"
    if [ "$K_MAJOR" -gt "$MIN_KERNEL_MAJOR" ] || { [ "$K_MAJOR" -eq "$MIN_KERNEL_MAJOR" ] && [ "$K_MINOR" -ge "$MIN_KERNEL_MINOR" ]; }; then
        echo -e "    ${GREEN}[PASS] Kernel version $KERNEL_RELEASE meets minimum requirement (>= 5.8.0)${NC}"
    else
        echo -e "    ${RED}[FAIL] Kernel version $KERNEL_RELEASE is below required 5.8.0 for RingBuffer & CAP_BPF${NC}"
        EXIT_CODE=1
    fi
else
    echo -e "    ${YELLOW}[WARN] Could not parse kernel version: $KERNEL_RELEASE${NC}"
fi

# 2. BTF Support Check (/sys/kernel/btf/vmlinux)
echo -e "\n[*] Checking BPF Type Format (BTF) support (/sys/kernel/btf/vmlinux)..."
if [ -f "/sys/kernel/btf/vmlinux" ]; then
    echo -e "    ${GREEN}[PASS] BTF vmlinux exists. CO-RE (Compile-Once Run-Everywhere) supported.${NC}"
else
    echo -e "    ${YELLOW}[WARN] /sys/kernel/btf/vmlinux not found. Kernel might lack CONFIG_DEBUG_INFO_BTF.${NC}"
fi

# 3. BPF Filesystem Check (/sys/fs/bpf)
echo -e "\n[*] Checking BPF filesystem mount (/sys/fs/bpf)..."
if mount | grep -q "type bpf"; then
    echo -e "    ${GREEN}[PASS] BPF filesystem is mounted.${NC}"
else
    echo -e "    ${YELLOW}[INFO] BPF filesystem not mounted. Can be mounted via: mount -t bpf bpf /sys/fs/bpf${NC}"
fi

# 4. Mandatory Kernel Config Options
echo -e "\n[*] Checking Kernel Configs..."
CONFIG_PATH=""
if [ -f "/proc/config.gz" ]; then
    CONFIG_PATH="/proc/config.gz"
elif [ -f "/boot/config-$(uname -r 2>/dev/null || true)" ]; then
    CONFIG_PATH="/boot/config-$(uname -r)"
fi

REQUIRED_CONFIGS=(
    "CONFIG_BPF=y"
    "CONFIG_BPF_SYSCALL=y"
    "CONFIG_BPF_JIT=y"
    "CONFIG_DEBUG_INFO_BTF=y"
    "CONFIG_NET_CLS_ACT=y"
    "CONFIG_NET_CLS_BPF=y"
)

if [ -n "$CONFIG_PATH" ]; then
    echo -e "    Found config at: $CONFIG_PATH"
    for cfg in "${REQUIRED_CONFIGS[@]}"; do
        if [ "${CONFIG_PATH##*.}" = "gz" ]; then
            if zgrep -q "^$cfg" "$CONFIG_PATH"; then
                echo -e "    ${GREEN}[PASS] $cfg is enabled${NC}"
            else
                echo -e "    ${RED}[FAIL] $cfg is missing or disabled${NC}"
                EXIT_CODE=1
            fi
        else
            if grep -q "^$cfg" "$CONFIG_PATH"; then
                echo -e "    ${GREEN}[PASS] $cfg is enabled${NC}"
            else
                echo -e "    ${RED}[FAIL] $cfg is missing or disabled${NC}"
                EXIT_CODE=1
            fi
        fi
    done
else
    echo -e "    ${YELLOW}[INFO] Neither /proc/config.gz nor /boot/config-$(uname -r) found. Skipping live config scan.${NC}"
fi

# 5. Required Binaries
echo -e "\n[*] Checking Required Development Tools..."
TOOLS=("clang" "llc" "bpftool" "rustc" "cargo")
for tool in "${TOOLS[@]}"; do
    if command -v "$tool" >/dev/null 2>&1; then
        VERSION=$("$tool" --version 2>&1 | head -n 1)
        echo -e "    ${GREEN}[PASS] $tool is installed ($VERSION)${NC}"
    else
        echo -e "    ${YELLOW}[WARN] $tool is not installed on PATH${NC}"
    fi
done

echo -e "\n${BLUE}======================================================${NC}"
if [ "$EXIT_CODE" -eq 0 ]; then
    echo -e "${GREEN}Prerequisite Check Completed Successfully.${NC}"
else
    echo -e "${RED}Prerequisite Check Completed with Warnings or Errors.${NC}"
fi
echo -e "${BLUE}======================================================${NC}"

exit "$EXIT_CODE"
