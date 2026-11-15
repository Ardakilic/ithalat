// Scenario tests: real pointing_device.c + real azoteq_iqs5xx.c + simulated IQS5xx with a
// communication-window / RDY model (iqs5xx_bus_mock.c). Run with firmware/test.sh, which builds:
//   stock     - QMK master as is (informational)
//   control   - + the trackpad block of ardakilic_trackpad/keymap.c with TRACKPAD_NO_TAP_LATCH_FIX
//               (informational: shows what the tap-latch workaround fixes)
//   fixed     - + the trackpad block, polled every 11 ms (no RDY wire)          -> must pass
//   fixed_rdy - + the trackpad block with POINTING_DEVICE_MOTION_PIN (RDY wire) -> must pass
#include <cstdio>
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

class Azoteq : public TestFixture {
   protected:
    void SetUp() override {
        ::testing::NiceMock<TestDriver> d; // a live TestDriver is needed whenever the scan loop runs
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
#endif
