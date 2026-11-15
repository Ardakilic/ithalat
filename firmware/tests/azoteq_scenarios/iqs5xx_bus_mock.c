// Simulated IQS5xx (TPS65) on a mocked QMK I2C API, for scenario tests of the azoteq_iqs5xx driver
// together with the real quantum/pointing_device/pointing_device.c. Run with firmware/test.sh.
//
// Communication-window model (IQS5xx-B000 datasheet 8.1, 8.7, 6.1):
//   - the pad opens a window AZOTEQ_IQS5XX_REPORT_RATE ms after the previous one was ended
//     (write to 0xEEEE); RDY (iqs_mock_rdy(), active high) is high while the window is open
//   - an I2C transfer outside the window is "forced communication": the pad stretches SCL until the
//     window opens; the mock advances the simulated clock by that time (= main loop blocked)
//   - gesture events (tap, two-finger tap) belong to ONE cycle: if a window is ended without its
//     base data (0x000C) having been read, that cycle and any tap in it are lost
// Not modelled: electrical effects, bit-level I2C timing, the pad's own I2C timeout.
#include <string.h>
#include <stdbool.h>
#include <stdint.h>
#include "i2c_master.h"
#include "timer.h"
#include "drivers/sensors/azoteq_iqs5xx.h"

void advance_time(uint32_t ms); // platforms/test/timer.c

static struct {
    bool     present;
    bool     show_reset;
    bool     tap_pending;
    bool     two_tap_pending;
    int      hold_reads;
    int      fail_base_reads;
    bool     vanish_on_reset; // the next soft reset leaves the pad NACKing (connector bounce during a re-init)
    uint16_t x_res, y_res;
    // window model
    uint32_t win_open_at; // time at which the next window opens
    bool     win_open;
    bool     base_read_in_window;
    bool     tap_in_window;     // a single tap is reported in the current cycle
    bool     two_tap_in_window; // a two-finger tap is reported in the current cycle
    // counters
    uint32_t soft_resets;
    uint32_t nacks;
    uint32_t base_reads;
    uint32_t sysinfo_reads;
    uint32_t forced, stall_ms, max_stall_ms;
    uint32_t lost_cycles, lost_taps;
} m = {.present = true, .show_reset = true, .x_res = 3072, .y_res = 2048};

void iqs_mock_set_present(bool present) { m.present = present; }
void iqs_mock_power_cycle(void) { m.show_reset = true; m.x_res = 3072; m.y_res = 2048; m.tap_pending = m.two_tap_pending = false; m.hold_reads = 0; }
void iqs_mock_tap(void) { m.tap_pending = true; }
void iqs_mock_two_finger_tap(void) { m.two_tap_pending = true; }
void iqs_mock_hold(int reads) { m.hold_reads = reads; }
void iqs_mock_fail_base_reads(int n) { m.fail_base_reads = n; }
void iqs_mock_vanish_on_reset(bool on) { m.vanish_on_reset = on; }
void iqs_mock_raise_show_reset(void) { m.show_reset = true; } // reset flag only, gestures in progress go on
uint16_t iqs_mock_x_res(void) { return m.x_res; }
uint16_t iqs_mock_y_res(void) { return m.y_res; }
bool     iqs_mock_show_reset(void) { return m.show_reset; }
uint32_t iqs_mock_soft_resets(void) { return m.soft_resets; }
uint32_t iqs_mock_nacks(void) { return m.nacks; }
uint32_t iqs_mock_base_reads(void) { return m.base_reads; }
uint32_t iqs_mock_sysinfo_reads(void) { return m.sysinfo_reads; }
uint32_t iqs_mock_forced(void) { return m.forced; }
uint32_t iqs_mock_stall_ms(void) { return m.stall_ms; }
uint32_t iqs_mock_max_stall_ms(void) { return m.max_stall_ms; }
uint32_t iqs_mock_lost_cycles(void) { return m.lost_cycles; }
uint32_t iqs_mock_lost_taps(void) { return m.lost_taps; }
void     iqs_mock_clear_counters(void) {
    m.nacks = m.base_reads = m.sysinfo_reads = 0;
    m.forced = m.stall_ms = m.max_stall_ms = m.lost_cycles = m.lost_taps = 0;
}

static void update_window(void) {
    // The test fixture resets the simulated clock between tests: re-sync the window schedule.
    if (m.win_open_at > timer_read32() + AZOTEQ_IQS5XX_REPORT_RATE) m.win_open_at = timer_read32();
    if (!m.win_open && timer_read32() >= m.win_open_at) {
        m.win_open            = true;
        m.base_read_in_window = false;
        m.tap_in_window       = m.tap_pending; // gesture events are reported in ONE cycle
        m.two_tap_in_window   = !m.tap_pending && m.two_tap_pending;
        if (m.tap_in_window) m.tap_pending = false;
        if (m.two_tap_in_window) m.two_tap_pending = false;
    }
}

// RDY line, active high. Used through `#define gpio_read_pin(pin) iqs_mock_rdy()` in the RDY build.
int iqs_mock_rdy(void) {
    update_window();
    return m.present && m.win_open;
}

static void ensure_window(void) { // forced communication: clock stretching until the window opens
    update_window();
    if (!m.win_open) {
        uint32_t d = m.win_open_at - timer_read32();
        m.forced++;
        m.stall_ms += d;
        if (d > m.max_stall_ms) m.max_stall_ms = d;
        advance_time(d);
        update_window();
    }
}

static void end_window(void) {
    if (!m.win_open) return;
    if (!m.base_read_in_window) {
        m.lost_cycles++;
        if (m.tap_in_window || m.two_tap_in_window) m.lost_taps++;
    }
    m.win_open    = false;
    m.win_open_at = timer_read32() + AZOTEQ_IQS5XX_REPORT_RATE;
}

// The scenario test calls matrix_scan_user() itself (QMK's test matrix, CUSTOM_MATRIX = yes, has an
// empty matrix_scan_kb()). This weak no-op serves the stock build, which has no keymap block.
__attribute__((weak)) void matrix_scan_user(void) {}

void i2c_init(void) {}

i2c_status_t i2c_ping_address(uint8_t address, uint16_t timeout) {
    if (!m.present) {
        m.nacks++;
        return I2C_STATUS_ERROR;
    }
    ensure_window();
    return I2C_STATUS_SUCCESS;
}

i2c_status_t i2c_read_register16(uint8_t devaddr, uint16_t regaddr, uint8_t *data, uint16_t length, uint16_t timeout) {
    if (!m.present) {
        m.nacks++;
        return I2C_STATUS_ERROR;
    }
    if (regaddr == 0x000C && m.fail_base_reads > 0) { // injected transfer error (flaky cable)
        m.fail_base_reads--;
        return I2C_STATUS_TIMEOUT;
    }
    ensure_window();
    memset(data, 0, length);
    switch (regaddr) {
        case 0x0000: // product number, big-endian
            if (length >= 2) {
                data[0] = 0;
                data[1] = 40; // IQS550 (TPS65)
            }
            break;
        case 0x000C: { // base data
            azoteq_iqs5xx_base_data_t bd = {0};
            if (!m.base_read_in_window && m.tap_in_window) {
                bd.gesture_events_0.single_tap = true;
            } else if (!m.base_read_in_window && m.two_tap_in_window) {
                bd.gesture_events_1.two_finger_tap = true;
            } else if (m.hold_reads > 0) {
                bd.gesture_events_0.press_and_hold = true; // reported every cycle while held
                bd.number_of_fingers               = 1;
                m.hold_reads--;
            }
            bd.system_info_0.show_reset = m.show_reset;
            memcpy(data, &bd, length < sizeof(bd) ? length : sizeof(bd));
            m.base_read_in_window = true;
            m.base_reads++;
            break;
        }
        case 0x000F: // system info 0
            data[0] = m.show_reset ? 0x80 : 0x00;
            m.sysinfo_reads++;
            break;
        default:
            break;
    }
    return I2C_STATUS_SUCCESS;
}

i2c_status_t i2c_write_register16(uint8_t devaddr, uint16_t regaddr, const uint8_t *data, uint16_t length, uint16_t timeout) {
    if (!m.present) {
        m.nacks++;
        return I2C_STATUS_ERROR;
    }
    ensure_window();
    switch (regaddr) {
        case 0xEEEE: // end of communication window
            end_window();
            break;
        case 0x0432: // system control 1: bit1 RESET
            if (data[0] & 0x02) {
                m.soft_resets++;
                iqs_mock_power_cycle();
                if (m.vanish_on_reset) m.present = false;
            }
            break;
        case 0x0431: // system control 0: bit7 ACK_RESET
            if (data[0] & 0x80) m.show_reset = false;
            break;
        case 0x066E: // X/Y resolution, big-endian
            if (length >= 4) {
                m.x_res = ((uint16_t)data[0] << 8) | data[1];
                m.y_res = ((uint16_t)data[2] << 8) | data[3];
            }
            break;
        default:
            break;
    }
    return I2C_STATUS_SUCCESS;
}
