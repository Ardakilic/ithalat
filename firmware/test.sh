#!/usr/bin/env bash
# Host-side scenario tests for the trackpad code, run inside ghcr.io/qmk/qmk_cli (docker only).
#
# Uses QMK's own gtest harness with the REAL quantum/pointing_device/pointing_device.c and the REAL
# drivers/sensors/azoteq_iqs5xx.c on top of a simulated IQS5xx on a mocked I2C bus
# (tests/azoteq_scenarios/iqs5xx_bus_mock.c: register behaviour plus a communication-window / RDY
# model with clock-stretching and lost-cycle accounting). Four builds:
#   stock     - QMK as is. Expected to FAIL TapClicksAndReleases / TwoFingerTapRightClicksAndReleases
#               on QMK >= 0.34.0 (the tap-latch bug) and to show that a pad plugged in after boot is
#               never picked up (PadPluggedAfterBoot passes by asserting INIT_FAILED).
#   control   - plus the keymap block (below) with TRACKPAD_NO_TAP_LATCH_FIX defined: hot-plug
#               works, the tap tests fail. Shows what the workaround fixes.
#   fixed     - plus the POINTING_DEVICE_ENABLE block extracted verbatim from
#               qmk_userspace/keyboards/yakamoz/keymaps/ardakilic_trackpad/keymap.c, no RDY wire
#               (driver polls every 11 ms). Must pass everything.
#   fixed_rdy - the same block with POINTING_DEVICE_MOTION_PIN defined (RDY wire; gpio_read_pin()
#               reads the simulated RDY line). Must pass everything.
# stock and control are informational; the exit code reflects fixed and fixed_rdy only.
# This is a simulation, not a hardware test.
#
# Needs the qmk_firmware clone made by ./build.sh (same WORK_DIR default).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="${WORK_DIR:-${TMPDIR:-/tmp}/yakamoz-qmk-build}"
QMK_IMAGE="${QMK_IMAGE:-ghcr.io/qmk/qmk_cli:latest}"
KEYMAP_C="$SCRIPT_DIR/qmk_userspace/keyboards/yakamoz/keymaps/ardakilic_trackpad/keymap.c"
Q="$WORK_DIR/qmk_firmware"
VARIANTS="stock control fixed fixed_rdy"

[ -f "$Q/Makefile" ] || { echo "error: $Q not found - run ./build.sh first (same WORK_DIR)" >&2; exit 1; }
WORK_DIR="$(cd "$WORK_DIR" && pwd)"

for v in $VARIANTS; do
    d="$Q/tests/pointing/azoteq_scn_$v"
    rm -rf "$d"
    mkdir -p "$d"
    cp "$SCRIPT_DIR/tests/azoteq_scenarios/iqs5xx_bus_mock.c" "$SCRIPT_DIR/tests/azoteq_scenarios/test_scenarios.cpp" "$d/"
    cat > "$d/test.mk" <<EOF
POINTING_DEVICE_ENABLE = yes
POINTING_DEVICE_DRIVER = azoteq_iqs5xx
MOUSEKEY_ENABLE = yes
SRC += tests/pointing/azoteq_scn_$v/iqs5xx_bus_mock.c
EOF
    # Mirrors the trackpad settings of ardakilic_trackpad/config.h that matter here.
    cat > "$d/config.h" <<'EOF'
#pragma once
#include "test_common.h"
#define AZOTEQ_IQS5XX_TPS65
#define AZOTEQ_IQS5XX_PRESS_AND_HOLD_ENABLE true
#define TRACKPAD_CPI 500
#define TRACKPAD_HOTPLUG_INTERVAL_MS 1000
EOF
    if [ "$v" != stock ]; then
        echo "#define SCENARIO_FIXED" >> "$d/config.h"
        echo "SRC += tests/pointing/azoteq_scn_$v/keymap_trackpad_block.c" >> "$d/test.mk"
        {
            echo "// Extracted verbatim from ardakilic_trackpad/keymap.c (first POINTING_DEVICE_ENABLE block)"
            echo '#include "quantum.h"'
            awk '/^#ifdef POINTING_DEVICE_ENABLE$/ && !done {on=1} on {print} /^#endif \/\/ POINTING_DEVICE_ENABLE$/ && on {on=0; done=1}' "$KEYMAP_C"
        } > "$d/keymap_trackpad_block.c"
    fi
    if [ "$v" = control ]; then
        echo "#define TRACKPAD_NO_TAP_LATCH_FIX" >> "$d/config.h"
    fi
    if [ "$v" = fixed_rdy ]; then
        # The test platform has no GPIO layer: route the RDY pin to the simulated pad.
        cat >> "$d/config.h" <<'EOF'
#define POINTING_DEVICE_MOTION_PIN 15
#ifdef __cplusplus
extern "C" {
#endif
int iqs_mock_rdy(void);
#ifdef __cplusplus
}
#endif
#define gpio_read_pin(pin) iqs_mock_rdy()
#define gpio_set_pin_input(pin) ((void)0)
#define gpio_set_pin_input_low(pin) ((void)0)
#define gpio_set_pin_input_high(pin) ((void)0)
EOF
    fi
done

docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp/home -v "$WORK_DIR":/work -w /work/qmk_firmware "$QMK_IMAGE" bash -c '
mkdir -p "$HOME"; git config --global --add safe.directory "*"
filter() { grep -E "^\[|Failure|Expected|Actual|error" "$1" || true; }
echo "================ stock QMK (informational: tap tests are expected to FAIL on QMK >= 0.34.0)"
make -s test:pointing/azoteq_scn_stock COLOR=false > /tmp/stock.log 2>&1 || true
filter /tmp/stock.log
echo "================ keymap block with TRACKPAD_NO_TAP_LATCH_FIX (informational control: tap/hold tests are expected to FAIL)"
make -s test:pointing/azoteq_scn_control COLOR=false > /tmp/control.log 2>&1 || true
filter /tmp/control.log
rc=0
echo "================ ardakilic_trackpad keymap block, no RDY wire (must pass)"
make -s test:pointing/azoteq_scn_fixed COLOR=false > /tmp/fixed.log 2>&1 || rc=1
filter /tmp/fixed.log
echo "================ ardakilic_trackpad keymap block with POINTING_DEVICE_MOTION_PIN / RDY (must pass)"
make -s test:pointing/azoteq_scn_fixed_rdy COLOR=false > /tmp/fixed_rdy.log 2>&1 || rc=1
filter /tmp/fixed_rdy.log
echo "================ result: $([ $rc = 0 ] && echo PASS || echo FAIL) (fixed + fixed_rdy)"
exit $rc
'
