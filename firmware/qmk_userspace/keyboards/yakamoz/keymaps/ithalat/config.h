/* Yakamoz 'ithalat' keymap configuration.
 *
 * = ozkan's stock 'default' keymap configuration (unchanged block below: SH1107 64x128 OLED,
 *   caps-lock LED)
 * + an Azoteq TPS65 trackpad (IQS550 controller) in the "ithalat" wrist rest, connected through a
 *   pluggable cable and sharing the OLED's I2C bus. See firmware/README.md in the ithalat repo.
 */

/* ---------------------------------------------------------------------------------------------
 * Stock 'default' configuration (verbatim, github.com/ozkan/Yakamoz-qmk yakamoz/keymaps/default)
 * ------------------------------------------------------------------------------------------- */

#ifdef OLED_ENABLE

/* OLED DRIVER CONFIG */
#define OLED_DISPLAY_64X128
#define OLED_IC OLED_IC_SH1107
/* Lowering the pre charge period fixes coil whining for the used display modules. */
#define OLED_PRE_CHARGE_PERIOD 0x22
#define OLED_VCOM_DETECT 0x35
#define OLED_TIMEOUT 15000

#endif // OLED_ENABLE

/* Indicator LEDs */
#define LED_CAPS_LOCK_PIN GP25
#define LED_PIN_ON_STATE 1

/* ---------------------------------------------------------------------------------------------
 * Azoteq TPS65 trackpad
 * ------------------------------------------------------------------------------------------- */

/* Module profile: 65 x 49 mm, native resolution 3072 x 2048 (drivers/sensors/azoteq_iqs5xx.c). */
#define AZOTEQ_IQS5XX_TPS65

/* I2C bus: the trackpad (7-bit 0x74) SHARES the existing Yakamoz OLED bus (OLED at 0x3C):
 * RP2040 I2C1, SDA = GP2 (Pico pin 4), SCL = GP3 (Pico pin 5), 4.7k pull-ups R1/R2 on the main PCB.
 * These three lines repeat keyboards/yakamoz/config.h on purpose. They are plain #defines, so if
 * the keyboard definition ever moves the bus, the build fails with a "redefined" error instead of
 * silently using other pins.
 * Do NOT copy I2C1_SDA_PIN GP18 / I2C1_SCL_PIN GP19 from other RP2040 trackpad keymaps: on
 * Yakamoz GP18/GP19 are matrix columns 8 and 9. The keyboard-level mcuconf.h already enables
 * RP_I2C_USE_I2C1, so no keymap-level mcuconf.h is needed. */
#define I2C_DRIVER I2CD1
#define I2C1_SDA_PIN GP2
#define I2C1_SCL_PIN GP3

/* Bus speed. 400 kHz is QMK's RP2040 default (platforms/chibios/chibios_config.h) and the IQS5xx
 * maximum. If the cable turns out unreliable (cursor stutter or jumps, OLED garbage, the OLED line
 * "Pad:" flickering between "on" and "--"), drop to 100 kHz: comment the first line, uncomment the
 * second. 100 kHz makes each OLED refresh block take ~4x longer on the bus. */
#define I2C1_CLOCK_SPEED 400000
// #define I2C1_CLOCK_SPEED 100000

/* Optional RDY line: TPS65 pad "RDY" -> connector pin 5 -> Pico GP15 (pin 20).
 * IQS5xx RDY is ACTIVE-HIGH (high = communication window open, IQS5xx-B000 datasheet 8.1).
 * QMK reads POINTING_DEVICE_MOTION_PIN as active-high unless POINTING_DEVICE_MOTION_PIN_ACTIVE_LOW
 * is defined, and the azoteq_iqs5xx branch of quantum/pointing_device/pointing_device.h does not
 * define it, so the polarity is already right: do NOT define POINTING_DEVICE_MOTION_PIN_ACTIVE_LOW.
 * With the pin defined, the driver's automatic 11 ms polling throttle is not applied
 * (drivers/sensors/azoteq_iqs5xx.h): pointing_device_task() runs on every main-loop pass and reads
 * the pad only while RDY is high. keymap.c does its button release and hot-plug check in
 * matrix_scan_user(), before that read, so both also act only inside the RDY window: holds stay
 * pressed and the check does not stretch the clock on the shared bus (a forced read happens only
 * if RDY stays low for TRACKPAD_ALIGN_MAX_WAIT_MS, e.g. a broken RDY wire). keymap.c also adds an
 * internal pull-down on the pin so an unplugged cable reads "no data". Leave it commented out if
 * the RDY wire is not connected: with the pin defined but not wired, the pad is never read. */
// #define POINTING_DEVICE_MOTION_PIN GP15

/* Orientation. Mounting in ithalat: touch side up, the module's connector long edge facing the
 * keyboard (away from you). With no define the driver keeps the TPS65's factory axis setup (it
 * only toggles the flip/switch bits on top of the module's own XY config, azoteq_iqs5xx.c
 * set_xy_config), which is the most likely correct choice for this mounting. If the cursor moves
 * wrong, enable AT MOST ONE of these (30-second check in firmware/README.md, "Calibration"):
 *   - left/right AND up/down both reversed                     -> ROTATION_180
 *   - axes swapped (moving right moves the cursor up or down)  -> ROTATION_90, if still wrong ROTATION_270
 * These rotate inside the IQS5xx, so two-finger scrolling is rotated too. */
// #define AZOTEQ_IQS5XX_ROTATION_180
// #define AZOTEQ_IQS5XX_ROTATION_90
// #define AZOTEQ_IQS5XX_ROTATION_270

/* Pointer speed, applied after every (re)initialisation of the pad (pointing_device_init_user()).
 * 500 is a calm starting point. Raise it if 500 feels slow; 0 keeps the pad's native ~1200 CPI. */
#define TRACKPAD_CPI 500

/* Hot-plug: how often keymap.c checks whether the pad is present / was reset (milliseconds). */
#define TRACKPAD_HOTPLUG_INTERVAL_MS 1000

/* Gestures: driver defaults (1-finger tap = left click, 2-finger tap = right click, 2-finger
 * scroll) plus press-and-hold. The stock keymap has no left-click key, and its right-click key
 * [3,7] is removed for the connector dock, so there is no physical button to hold for
 * drag-and-drop.
 * Press-and-hold replaces it: rest one finger on the pad without moving for ~450 ms (the IQS5xx
 * fires it after Tap time + Hold time, datasheet 6.2; driver defaults AZOTEQ_IQS5XX_TAP_TIME 150 ms
 * + AZOTEQ_IQS5XX_HOLD_TIME 300 ms), then move: the left button stays held until you lift the
 * finger. Comment this line out if resting a finger on the pad gives unwanted clicks or drags.
 * To change the delay, define AZOTEQ_IQS5XX_HOLD_TIME (ms) here. */
#define AZOTEQ_IQS5XX_PRESS_AND_HOLD_ENABLE true

/* Escape hatch: define this to disable the keymap-level tap-latch workaround (keymap.c). */
// #define TRACKPAD_NO_TAP_LATCH_FIX
