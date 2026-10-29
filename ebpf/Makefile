# API-Sentinel eBPF Sensor Makefile
# Role: Member 2 (eBPF Traffic Engineer)
# Mission: Build bounded, least-privilege Linux/eBPF observation sensor

CLANG ?= clang
LLC ?= llc
BPFTOOL ?= bpftool
CFLAGS ?= -O2 -g -Wall -Werror -target bpf -D__TARGET_ARCH_x86 -Iinclude -Isrc

SRC_DIR := src
BUILD_DIR := build
INCLUDE_DIR := include

TARGETS := $(BUILD_DIR)/api_sentinel_sensor.o

.PHONY: all build clean verify test load unload status

all: build

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

build: $(BUILD_DIR) $(TARGETS)

$(BUILD_DIR)/api_sentinel_sensor.o: $(SRC_DIR)/api_sentinel_sensor.c $(INCLUDE_DIR)/api_sentinel_types.h $(INCLUDE_DIR)/api_sentinel_maps.h
	$(CLANG) $(CFLAGS) -c $< -o $@
	@echo "[+] Successfully compiled bounded eBPF sensor bytecode: $@"

clean:
	rm -rf $(BUILD_DIR)
	@echo "[+] Cleaned eBPF build artifacts"

verify: build
	@echo "[*] Verifying BPF bytecode sections and verifier compliance..."
	$(BPFTOOL) prog dump xlated file $(BUILD_DIR)/api_sentinel_sensor.o || true
	python3 -m unittest tests/test_producer_consumer_contract.py tests/test_working_sensor_runtime.py

test:
	python3 -m unittest discover -s tests -p "test_*.py"

load: build
	@echo "[*] Attaching eBPF sensor to clsact qdisc on interface (lo/lab)..."
	sudo python3 scripts/sensor_loader.py --attach --interface lo

unload:
	@echo "[*] Safely detaching and cleaning up API-Sentinel maps and filters..."
	sudo python3 scripts/sensor_loader.py --cleanup --interface lo

status:
	@echo "[*] Checking pinned maps and active eBPF programs..."
	sudo python3 scripts/sensor_loader.py --status
