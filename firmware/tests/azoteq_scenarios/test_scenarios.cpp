// Scenario tests: real pointing_device.c + real azoteq_iqs5xx.c + simulated IQS5xx with a
// communication-window / RDY model (iqs5xx_bus_mock.c). Run with firmware/test.sh, which builds:
//   stock     - QMK master as is (informational)
//   control   - + the trackpad block of ithalat/keymap.c with TRACKPAD_NO_TAP_LATCH_FIX
//               (informational: shows what the tap-latch workaround fixes)
//   fixed     - + the trackpad block, polled every 11 ms (no RDY wire)          -> must pass
//   fixed_rdy - + the trackpad block with POINTING_DEVICE_MOTION_PIN (RDY wire) -> must pass
#include <cstdio>
#include <vector>
#include "gtest/gtest.h"
#include "mouse_report_util.hpp"
#include "test_common.hpp"

extern "C" {
#include "pointing_device.h"
void     keyboard_task(void);
void     housekeeping_task(void);
void     advance_time(uint32_t ms);
void     matrix_scan_user(void);
void     iqs_mock_set_present(bool present);
void     iqs_mock_power_cycle(void);
void     iqs_mock_tap(void);
void     iqs_mock_two_finger_tap(void);
void     iqs_mock_hold(int reads);
void     iqs_mock_fail_base_reads(int n);
void     iqs_mock_vanish_on_reset(bool on);
void     iqs_mock_raise_show_reset(void);
int      iqs_mock_rdy(void);
void     iqs_mock_open_window_now(void);
uint16_t iqs_mock_x_res(void);
uint16_t iqs_mock_y_res(void);
bool     iqs_mock_show_reset(void);
uint32_t iqs_mock_soft_resets(void);
uint32_t iqs_mock_nacks(void);
uint32_t iqs_mock_base_reads(void);
uint32_t iqs_mock_sysinfo_reads(void);
uint32_t iqs_mock_forced(void);
uint32_t iqs_mock_stall_ms(void);
uint32_t iqs_mock_max_stall_ms(void);
uint32_t iqs_mock_lost_cycles(void);
uint32_t iqs_mock_lost_taps(void);
void     iqs_mock_clear_counters(void);
}

using testing::_;
using testing::InSequence;
using testing::Invoke;

// One main-loop pass per simulated millisecond, in firmware order. On the keyboard,
// keyboard_task() -> matrix_task() -> matrix_scan() -> matrix_scan_kb() -> matrix_scan_user() runs
// first, before pointing_device_task(); QMK's test matrix (CUSTOM_MATRIX = yes) has an empty
// matrix_scan_kb(), so the call is made here. TestFixture::idle_for() would skip it.
static void run_ms(unsigned ms) {
    for (unsigned i = 0; i < ms; i++) {
        matrix_scan_user();
        keyboard_task();
        housekeeping_task();
        advance_time(1);
    }
}

// Counts left-button presses and releases seen by the host.
struct ButtonCounter {
    int     presses  = 0;
    int     releases = 0;
    uint8_t last     = 0;
};
static void count_buttons(::testing::NiceMock<TestDriver>& driver, ButtonCounter& c) {
    ON_CALL(driver, send_mouse_mock(_)).WillByDefault(Invoke([&c](report_mouse_t& r) {
        if ((r.buttons & 1) && !(c.last & 1)) c.presses++;
        if (!(r.buttons & 1) && (c.last & 1)) c.releases++;
        c.last = r.buttons;
    }));
}

// Records every change of the button state seen by the host.
static void record_buttons(::testing::NiceMock<TestDriver>& driver, std::vector<uint8_t>& seen) {
    ON_CALL(driver, send_mouse_mock(_)).WillByDefault(Invoke([&seen](report_mouse_t& r) {
        if (seen.empty() || seen.back() != r.buttons) seen.push_back(r.buttons);
    }));
}
static int count_edges(const std::vector<uint8_t>& seen, uint8_t mask, bool pressed) {
    int     n    = 0;
    uint8_t last = 0;
    for (uint8_t b : seen) {
        if (pressed ? ((b & mask) && !(last & mask)) : (!(b & mask) && (last & mask))) n++;
        last = b;
    }
    return n;
}

class Azoteq : public TestFixture {
   protected:
    void SetUp() override {
        ::testing::NiceMock<TestDriver> d; // a live TestDriver is needed whenever the scan loop runs
        iqs_mock_vanish_on_reset(false);
        iqs_mock_set_present(true);
        if (pointing_device_get_status() != POINTING_DEVICE_STATUS_SUCCESS) {
            pointing_device_init();
        }
        run_ms(30);
    }
};

// A single tap must produce a left-button press AND a release.
TEST_F(Azoteq, TapClicksAndReleases) {
    TestDriver driver;
    InSequence s;
    EXPECT_MOUSE_REPORT(driver, (0, 0, 0, 0, 1)).Times(1);
    EXPECT_MOUSE_REPORT(driver, (0, 0, 0, 0, 0)).Times(1);
    iqs_mock_tap();
    run_ms(200);
    VERIFY_AND_CLEAR(driver);
}

TEST_F(Azoteq, TwoFingerTapRightClicksAndReleases) {
    TestDriver driver;
    InSequence s;
    EXPECT_MOUSE_REPORT(driver, (0, 0, 0, 0, 2)).Times(1);
    EXPECT_MOUSE_REPORT(driver, (0, 0, 0, 0, 0)).Times(1);
    iqs_mock_two_finger_tap();
    run_ms(200);
    VERIFY_AND_CLEAR(driver);
}

// QMK core: a pad that is missing at boot is never picked up later (no retry in core).
TEST_F(Azoteq, PadPluggedAfterBoot) {
    ::testing::NiceMock<TestDriver> driver;
    iqs_mock_set_present(false);
    pointing_device_init(); // what keyboard_init() does at boot
    EXPECT_EQ(pointing_device_get_status(), POINTING_DEVICE_STATUS_INIT_FAILED);
    run_ms(3000);
    iqs_mock_set_present(true);
    iqs_mock_power_cycle();
    run_ms(2000);
#ifdef SCENARIO_FIXED
    EXPECT_EQ(pointing_device_get_status(), POINTING_DEVICE_STATUS_SUCCESS);
    EXPECT_EQ(iqs_mock_x_res(), 1280); // TRACKPAD_CPI 500 -> 500*65*10/254
    EXPECT_EQ(iqs_mock_y_res(), 965);
    EXPECT_FALSE(iqs_mock_show_reset()); // acknowledged after init
#else
    EXPECT_EQ(pointing_device_get_status(), POINTING_DEVICE_STATUS_INIT_FAILED);
#endif
}

#ifdef SCENARIO_FIXED
TEST_F(Azoteq, CpiAppliedAndResetAcknowledgedAtInit) {
    ::testing::NiceMock<TestDriver> driver;
    pointing_device_init();
    EXPECT_EQ(iqs_mock_x_res(), 1280);
    EXPECT_EQ(iqs_mock_y_res(), 965);
    EXPECT_FALSE(iqs_mock_show_reset());
}

TEST_F(Azoteq, AbsentPadIsProbedCheaply) {
    ::testing::NiceMock<TestDriver> driver;
    iqs_mock_set_present(false);
    pointing_device_init();
    iqs_mock_clear_counters();
    run_ms(10000);
    // 10 s absent: at most 2 NACKed pings per 1 s check, no driver polling
    EXPECT_LE(iqs_mock_nacks(), 22u);
    EXPECT_EQ(iqs_mock_base_reads(), 0u);
    iqs_mock_set_present(true);
}

TEST_F(Azoteq, UnplugDetectedAndReplugReinitialises) {
    ::testing::NiceMock<TestDriver> driver;
    ASSERT_EQ(pointing_device_get_status(), POINTING_DEVICE_STATUS_SUCCESS);
    iqs_mock_set_present(false);
    run_ms(1500);
    EXPECT_NE(pointing_device_get_status(), POINTING_DEVICE_STATUS_SUCCESS);
    iqs_mock_set_present(true);
    iqs_mock_power_cycle();
    run_ms(2000);
    EXPECT_EQ(pointing_device_get_status(), POINTING_DEVICE_STATUS_SUCCESS);
    EXPECT_EQ(iqs_mock_x_res(), 1280);
    EXPECT_FALSE(iqs_mock_show_reset());
}

TEST_F(Azoteq, ResetBetweenChecksReinitialises) {
    ::testing::NiceMock<TestDriver> driver;
    ASSERT_EQ(pointing_device_get_status(), POINTING_DEVICE_STATUS_SUCCESS);
    uint32_t resets = iqs_mock_soft_resets();
    iqs_mock_power_cycle(); // quick re-plug or watchdog: settings back to NV defaults
    EXPECT_EQ(iqs_mock_x_res(), 3072);
    run_ms(1500);
    EXPECT_GT(iqs_mock_soft_resets(), resets); // driver init ran again
    EXPECT_EQ(iqs_mock_x_res(), 1280);
    EXPECT_FALSE(iqs_mock_show_reset());
    EXPECT_EQ(pointing_device_get_status(), POINTING_DEVICE_STATUS_SUCCESS);
}

// Drag: exactly one press and one release for the whole hold (with RDY too, where
// pointing_device_task() sends on every loop pass but reads the pad only while RDY is high).
TEST_F(Azoteq, PressAndHoldStaysPressedUntilLifted) {
    TestDriver driver;
    InSequence s;
    EXPECT_MOUSE_REPORT(driver, (0, 0, 0, 0, 1)).Times(1);
    EXPECT_MOUSE_REPORT(driver, (0, 0, 0, 0, 0)).Times(1);
    iqs_mock_hold(30); // ~300-330 ms of press-and-hold reports
    run_ms(600);
    VERIFY_AND_CLEAR(driver);
}

TEST_F(Azoteq, KeyboardMouseButtonIsNotReleasedByTheFix) {
    TestDriver driver;
    KeymapKey  btn = KeymapKey(0, 0, 0, MS_BTN1);
    set_keymap({btn});
    InSequence s;
    EXPECT_MOUSE_REPORT(driver, (0, 0, 0, 0, 1)).Times(1);
    EXPECT_MOUSE_REPORT(driver, (0, 0, 0, 0, 0)).Times(1);
    btn.press();
    run_ms(300); // several driver polls while the key is held
    btn.release();
    run_ms(50);
    VERIFY_AND_CLEAR(driver);
}

// The running-state hot-plug check (once per second) reads inside the pad's communication window
// and leaves the window to the driver: no forced communication (clock stretching on the shared
// bus) and no report cycle thrown away.
TEST_F(Azoteq, HotplugCheckNeitherStallsTheBusNorLosesACycle) {
    ::testing::NiceMock<TestDriver> driver;
    iqs_mock_clear_counters();
    run_ms(10000);
    printf("[ INFO     ] 10 s running: base_reads=%u sysinfo_reads=%u forced=%u stall_ms=%u lost_cycles=%u\n", iqs_mock_base_reads(), iqs_mock_sysinfo_reads(), iqs_mock_forced(), iqs_mock_stall_ms(), iqs_mock_lost_cycles());
    EXPECT_GE(iqs_mock_sysinfo_reads(), 9u); // the check really ran
    EXPECT_GE(iqs_mock_base_reads(), 900u);  // the driver read (almost) every 10 ms cycle
    EXPECT_EQ(iqs_mock_forced(), 0u);
    EXPECT_EQ(iqs_mock_lost_cycles(), 0u);
}

// Every tap reaches the host as one click, also while hot-plug checks run in between.
TEST_F(Azoteq, EveryTapIsDelivered) {
    ::testing::NiceMock<TestDriver> driver;
    ButtonCounter                   c;
    count_buttons(driver, c);
    iqs_mock_clear_counters();
    const int taps = 400;
    for (int i = 0; i < taps; i++) {
        iqs_mock_tap();
        run_ms(37); // ~15 s, a tap every 37 ms
    }
    run_ms(50);
    printf("[ INFO     ] taps=%d presses=%d releases=%d lost_taps=%u forced=%u\n", taps, c.presses, c.releases, iqs_mock_lost_taps(), iqs_mock_forced());
    EXPECT_EQ(iqs_mock_lost_taps(), 0u);
    EXPECT_EQ(c.presses, taps);
    EXPECT_EQ(c.releases, taps);
}

// Known limit, documented in firmware/README.md: one failed driver read (I2C error) during a
// press-and-hold releases the button for one read; the next good read presses it again. This is
// the same as on QMK < 0.34.0. If this test starts failing, update the README.
TEST_F(Azoteq, OneFailedReadDuringHoldReleasesOnce) {
    ::testing::NiceMock<TestDriver> driver;
    ButtonCounter                   c;
    count_buttons(driver, c);
    iqs_mock_hold(30);
    run_ms(100);
    iqs_mock_fail_base_reads(1);
    run_ms(500);
    EXPECT_EQ(c.presses, 2);
    EXPECT_EQ(c.releases, 2);
}

// An MS_BTNx key pressed and released during a drag sends reports of its own (register_mouse() ->
// pointing_device_keycode_handler()). None of them may release the pad's button 1: the host sees it
// released only once, when the pad reports the lift. Key events land on every phase of the driver's
// read cycle (13 ms key period vs. 10/11 ms reads).
TEST_F(Azoteq, MouseKeyDuringDragKeepsTheDragHeld) {
    ::testing::NiceMock<TestDriver> driver;
    KeymapKey                       btn2 = KeymapKey(0, 0, 0, MS_BTN2);
    set_keymap({btn2});
    std::vector<uint8_t> seen;
    record_buttons(driver, seen);
    iqs_mock_hold(100); // ~1 s of press-and-hold reports
    run_ms(50);
    const int key_taps = 40; // 520 ms, all inside the hold
    for (int i = 0; i < key_taps; i++) {
        btn2.press();
        run_ms(7);
        btn2.release();
        run_ms(6);
    }
    run_ms(700); // the hold ends: the pad reports the lift
    EXPECT_EQ(count_edges(seen, 1, true), 1);
    EXPECT_EQ(count_edges(seen, 1, false), 1);
    EXPECT_EQ(count_edges(seen, 2, true), key_taps);
    EXPECT_EQ(count_edges(seen, 2, false), key_taps);
    EXPECT_EQ(seen.back(), 0);
}

// A macro key that taps MS_BTN1 (press and release in one pass, like tap_code(MS_BTN1)).
extern "C" bool process_record_user(uint16_t keycode, keyrecord_t *record) {
    if (keycode == QK_USER_0) {
        if (record->event.pressed) tap_code(MS_BTN1);
        return false;
    }
    return true;
}

// MS_BTN1 tapped during a drag while the pad's communication window is open: the keymap has taken
// the pad's button 1 out of the report for the driver's read (in this pass with RDY, within 1 ms
// without), and the key reports carry it in the meantime. The key's release must not release the
// drag: the host sees button 1 released only once, when the pad reports the lift.
TEST_F(Azoteq, MouseKeyTapInTheReadWindowKeepsTheDragHeld) {
    ::testing::NiceMock<TestDriver> driver;
    KeymapKey                       macro = KeymapKey(0, 0, 0, QK_USER_0);
    set_keymap({macro});
    std::vector<uint8_t> seen;
    record_buttons(driver, seen);
    iqs_mock_hold(100); // ~1 s of press-and-hold reports
    run_ms(50);
    int  taps = 0;
    bool down = false;
    for (int i = 0; i < 600; i++) { // all inside the hold
        if (down) {
            macro.release();
            down = false;
        } else if (iqs_mock_rdy()) {
            macro.press();
            down = true;
            taps++;
        }
        run_ms(1);
    }
    run_ms(700); // the hold ends: the pad reports the lift
    EXPECT_GE(taps, 40);
    EXPECT_EQ(count_edges(seen, 1, true), 1);
    EXPECT_EQ(count_edges(seen, 1, false), 1);
    EXPECT_EQ(seen.back(), 0);
}

// Button 1 with two owners: an MS_BTN1 key is pressed during a drag, held across driver reads and
// released while the pad still holds button 1. The host must keep button 1 pressed until the pad
// reports the lift, then release it exactly once. The key events land on different phases of the
// driver's read cycle.
TEST_F(Azoteq, MouseButton1HeldAcrossReadsDuringDragKeepsTheDragHeld) {
    ::testing::NiceMock<TestDriver> driver;
    KeymapKey                       btn1 = KeymapKey(0, 0, 0, MS_BTN1);
    set_keymap({btn1});
    std::vector<uint8_t> seen;
    record_buttons(driver, seen);
    iqs_mock_hold(100); // ~1 s of press-and-hold reports
    run_ms(50);
    for (int i = 0; i < 10; i++) { // ~380 ms, all inside the hold
        const uint32_t reads = iqs_mock_base_reads();
        btn1.press();
        run_ms(23 + i % 5);
        ASSERT_GE(iqs_mock_base_reads() - reads, 2u); // held across driver reads
        btn1.release();
        run_ms(9 + i % 4);
    }
    // The pad still holds: no release of button 1 so far.
    EXPECT_EQ(count_edges(seen, 1, true), 1);
    EXPECT_EQ(count_edges(seen, 1, false), 0);
    ASSERT_FALSE(seen.empty());
    EXPECT_TRUE(seen.back() & 1);
    run_ms(800); // the hold ends: the pad reports the lift
    EXPECT_EQ(count_edges(seen, 1, true), 1);
    EXPECT_EQ(count_edges(seen, 1, false), 1);
    EXPECT_EQ(seen.back(), 0);
}

// One pass in which RDY rises after matrix_scan_user() has sampled it (low) and before
// pointing_device_task() samples it again (high), so the driver reads the pad in this pass from a
// report that the keymap did not empty. On the keyboard the two samples are part of a pass apart.
static void run_pass_rdy_rises_after_scan(void) {
    matrix_scan_user();
    iqs_mock_open_window_now();
    keyboard_task();
    housekeeping_task();
    advance_time(1);
}

// RDY build: a press-and-hold is first seen in such a read. A mouse key event before the pad's next
// window must not release the drag on the host:
//   1. MS_BTN2 pressed and released (its reports carry the pad's buttons);
//   2. MS_BTN1 held when the drag starts, released before the next window (two owners of button 1).
// The host must see button 1 released only once, at the lift. Without RDY there is no such race;
// the same steps run with the driver's first read of the hold in place of the racy read.
TEST_F(Azoteq, RdyRiseBetweenScanAndReadKeepsTheDragHeld) {
    ::testing::NiceMock<TestDriver> driver;
    KeymapKey                       btn1 = KeymapKey(0, 0, 0, MS_BTN1);
    KeymapKey                       btn2 = KeymapKey(0, 1, 0, MS_BTN2);
    set_keymap({btn1, btn2});
    std::vector<uint8_t> seen;
    record_buttons(driver, seen);
    for (int btn1_held = 0; btn1_held < 2; btn1_held++) {
        SCOPED_TRACE(btn1_held ? "MS_BTN1 held when the drag starts" : "MS_BTN2 tapped after the drag starts");
        run_ms(50);
        seen.clear();
        // Let the driver read a window: RDY then stays low for one report period.
        for (int i = 0; i < 20 && !iqs_mock_rdy(); i++) {
            run_ms(1);
        }
        run_ms(1);
#ifdef POINTING_DEVICE_MOTION_PIN
        ASSERT_FALSE(iqs_mock_rdy());
#endif
        if (btn1_held) {
            btn1.press();
            run_ms(2);
        }
        iqs_mock_hold(50); // ~500 ms of press-and-hold reports from the next read on
        const uint32_t reads = iqs_mock_base_reads();
        run_pass_rdy_rises_after_scan();
#ifdef POINTING_DEVICE_MOTION_PIN
        ASSERT_EQ(iqs_mock_base_reads() - reads, 1u); // the racy read
#endif
        for (int i = 0; i < 20 && iqs_mock_base_reads() == reads; i++) { // no RDY: the next poll
            run_ms(1);
        }
        ASSERT_FALSE(seen.empty());
        ASSERT_TRUE(seen.back() & 1); // the host has button 1
        run_ms(2);
        if (btn1_held) {
            btn1.release();
            run_ms(2);
        } else {
            btn2.press();
            run_ms(2);
            btn2.release();
            run_ms(2);
        }
        run_ms(200);
        EXPECT_EQ(count_edges(seen, 1, false), 0); // the pad still holds
        run_ms(600);                               // the hold ends: the pad reports the lift
        EXPECT_EQ(count_edges(seen, 1, true), 1);
        EXPECT_EQ(count_edges(seen, 1, false), 1);
        EXPECT_EQ(count_edges(seen, 2, true), btn1_held ? 0 : 1);
        EXPECT_EQ(count_edges(seen, 2, false), btn1_held ? 0 : 1);
        EXPECT_EQ(seen.back(), 0);
    }
}

// The pad resets during a drag (watchdog or quick re-plug, SHOW_RESET) and stops answering during
// the re-init that follows: pointing_device_init() fails and pointing_device_task() sends no more
// reports. The pad's button must still be released on the host; a mouse button held by a key stays.
TEST_F(Azoteq, FailedReinitReleasesTheDragButKeepsKeyButtons) {
    TestDriver driver;
    KeymapKey  btn2 = KeymapKey(0, 0, 0, MS_BTN2);
    set_keymap({btn2});
    InSequence s;
    EXPECT_MOUSE_REPORT(driver, (0, 0, 0, 0, 2)).Times(1); // MS_BTN2 key
    EXPECT_MOUSE_REPORT(driver, (0, 0, 0, 0, 3)).Times(1); // + pad drag (button 1)
    EXPECT_MOUSE_REPORT(driver, (0, 0, 0, 0, 2)).Times(1); // re-init failed: drag released, key kept
    EXPECT_MOUSE_REPORT(driver, (0, 0, 0, 0, 0)).Times(1); // key up
    btn2.press();
    run_ms(20);
    iqs_mock_hold(1000);
    run_ms(100);
    iqs_mock_vanish_on_reset(true);
    iqs_mock_raise_show_reset();
    // The next presence check (<= TRACKPAD_HOTPLUG_RETRY_MS after an earlier test's failed init)
    // sees SHOW_RESET and re-initialises.
    for (int i = 0; i < 6000 && pointing_device_get_status() == POINTING_DEVICE_STATUS_SUCCESS; i++) {
        run_ms(1);
    }
    run_ms(100);
    EXPECT_EQ(pointing_device_get_status(), POINTING_DEVICE_STATUS_INIT_FAILED);
    btn2.release();
    run_ms(20);
    VERIFY_AND_CLEAR(driver);
    iqs_mock_vanish_on_reset(false);
}

// Same, with a pad button 2 (a two-finger tap in every report cycle) and MS_BTN1 held by a key.
TEST_F(Azoteq, FailedReinitReleasesPadButtonKeepsKeyButton1) {
    TestDriver driver;
    KeymapKey  btn1 = KeymapKey(0, 0, 0, MS_BTN1);
    set_keymap({btn1});
    InSequence s;
    EXPECT_MOUSE_REPORT(driver, (0, 0, 0, 0, 1)).Times(1); // MS_BTN1 key
    EXPECT_MOUSE_REPORT(driver, (0, 0, 0, 0, 3)).Times(1); // + pad button 2
    EXPECT_MOUSE_REPORT(driver, (0, 0, 0, 0, 1)).Times(1); // re-init failed: pad button released, MS_BTN1 kept
    EXPECT_MOUSE_REPORT(driver, (0, 0, 0, 0, 0)).Times(1); // key up
    btn1.press();
    run_ms(20);
    for (int i = 0; i < 50; i++) {
        iqs_mock_two_finger_tap();
        run_ms(1);
    }
    iqs_mock_vanish_on_reset(true);
    iqs_mock_raise_show_reset();
    for (int i = 0; i < 6000 && pointing_device_get_status() == POINTING_DEVICE_STATUS_SUCCESS; i++) {
        iqs_mock_two_finger_tap();
        run_ms(1);
    }
    run_ms(100);
    EXPECT_EQ(pointing_device_get_status(), POINTING_DEVICE_STATUS_INIT_FAILED);
    btn1.release();
    run_ms(20);
    VERIFY_AND_CLEAR(driver);
    iqs_mock_vanish_on_reset(false);
}
#endif
