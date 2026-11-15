# Yakamoz firmware: Azoteq TPS65 trackpad ("ithalat") + OLED

QMK keymap `ardakilic_trackpad` for [Yakamoz](https://github.com/ozkan/Yakamoz) (Raspberry Pi Pico / RP2040). It adds an Azoteq TPS65
trackpad (IQS550 controller) mounted in the "ithalat" wrist rest and connected through a pluggable
cable. The SH1107 OLED keeps working. This folder is part of [ithalat](../README.md); the physical
wiring is in [wiring.md](../wiring.md).

> **Not tested on hardware.** Everything here was compiled and checked against the QMK sources.
> The trackpad behaviour was also exercised in a host-side simulation (see
> [Scenario tests](#scenario-tests-simulation)). Nothing has run on a real Yakamoz with a real
> TPS65 yet. Work through the [test checklist](#test-checklist-after-flashing) on first flash.

## Contents

| Path | What |
|---|---|
| `qmk_userspace/keyboards/yakamoz/keymaps/ardakilic_trackpad/keymap.c` | the owner's `ardakilic` keymap plus the trackpad code (CPI, hot-plug, tap-latch workaround) and an OLED status line |
| `.../ardakilic_trackpad/config.h` | the `ardakilic` config plus the trackpad settings (all knobs are documented inline) |
| `.../ardakilic_trackpad/rules.mk` | the `ardakilic` rules plus `POINTING_DEVICE_ENABLE = yes` and `POINTING_DEVICE_DRIVER = azoteq_iqs5xx` |
| `build.sh` | reproducible docker-only build of `ardakilic` (baseline) and `ardakilic_trackpad` |
| `test.sh`, `tests/azoteq_scenarios/` | docker-only scenario tests: real QMK pointing code with a simulated IQS5xx (with and without the RDY wire) |
| `build/` | prebuilt `yakamoz_ardakilic.uf2` (baseline) and `yakamoz_ardakilic_trackpad.uf2`, committed for flashing without a build (built against QMK master `33292390974c`, see the size table below). `build.sh` overwrites them; anything else in `build/` is git-ignored |

The baseline `ardakilic` keymap lives in the owner's [Ardakilic/qmk_userspace](https://github.com/Ardakilic/qmk_userspace) repo, and `keyboards/yakamoz` comes from the [Ardakilic/qmk_firmware](https://github.com/Ardakilic/qmk_firmware) fork. The folder layout here matches a QMK userspace, so the keymap folder can be copied straight into one.

## Changes vs. `ardakilic`

The diff against `Ardakilic/qmk_userspace@ef35653` `keyboards/yakamoz/keymaps/ardakilic` adds lines, and changes exactly two: the SODA layer's bottom row and its diagram line in `keymap.c`. No original line was removed.

| Area | Change |
|---|---|
| Layers, keycodes, Turkish-Q macros | unchanged, except one SODA addition (next row). Every keycode stays where it was, so the keymap still works on an unmodified board: `MS_BTN1`/`MS_BTN2` at `[3,6]`/`[3,7]` on every layer except SODA, which has `QK_AUDIO_VOICE_NEXT`/`QK_MUSIC_TOGGLE` there. |
| SODA layer | Those two audio keycodes would be lost with the removed switches, so they are **copied** to free (previously transparent) SODA positions next to the other music/audio keys: `QK_AUDIO_VOICE_NEXT` to `[3,4]` and `QK_MUSIC_TOGGLE` to `[3,9]`. Side effect: SODA + `[3,4]` / `[3,9]` no longer falls through to the base layer's `Lower`/`Raise` keys. |
| OLED (SH1107 64x128, Darth Vader bitmap, layer, caps) | unchanged, plus one line `Pad: on` / `Pad: --` on text line 13 (lines 0-7 bitmap, 9 layer, 11-12 caps; 10 characters, so the line is fully overwritten every frame) |
| Audio (Rick Roll), WPM, caps LED GP25 | unchanged |
| `rules.mk` | adds `POINTING_DEVICE_ENABLE = yes` and `POINTING_DEVICE_DRIVER = azoteq_iqs5xx` |
| `config.h` | adds `AZOTEQ_IQS5XX_TPS65`, the I2C bus (`I2CD1`, GP2/GP3, the existing OLED bus), `I2C1_CLOCK_SPEED 400000`, an optional RDY pin (commented out), rotation options (commented out), `TRACKPAD_CPI 500`, `TRACKPAD_HOTPLUG_INTERVAL_MS 1000`, `AZOTEQ_IQS5XX_PRESS_AND_HOLD_ENABLE true` |
| `keymap.c` | `pointing_device_init_user()` re-applies CPI and acknowledges the pad's reset flag. `matrix_scan_user()` runs the hot-plug check and the tap-latch workaround (it runs before `pointing_device_task()` in each main-loop pass, see [Tap-latch finding](#tap-latch-finding-qmk--0340)). `pointing_device_task_user()` records which buttons came from the pad. The trackpad code is inside `#ifdef POINTING_DEVICE_ENABLE`. |
| Removed keys | The two front-row centre switches (SW44/SW43, matrix `[3,6]`/`[3,7]`) are **physically removed** to make room for the connector dock. The trackpad replaces their `MS_BTN1`/`MS_BTN2`: 1-finger tap = left click, 2-finger tap = right click, press-and-hold = left button held for drag-and-drop (enabled by default, see knobs). Their SODA functions are copied to other keys, see above. |

Firmware size (QMK master `33292390974c`, `arm-none-eabi-size`):

| keymap | text | bss | .uf2 |
|---|---|---|---|
| `ardakilic` (baseline) | 48 012 B | 265 048 B | 96 256 B |
| `ardakilic_trackpad` | 50 640 B (+2 628 B) | 265 040 B | 101 376 B |

The Pico has 2 MB of flash, so size is not a concern.

## Wiring summary (firmware view)

The trackpad **shares the OLED's I2C bus**. QMK's `i2c_master` drives only one I2C peripheral, and the addresses do not collide (OLED 0x3C, TPS65 0x74).

| Signal | Pico | Pogo pin (both halves) | USB-C breakout pad |
|---|---|---|---|
| SDA | GP2 (pin 4) | 1 | D+ |
| 3V3 | 3V3(OUT) (pin 36), **never 5 V / VBUS** | 2 | V, through a series Schottky diode |
| GND | any GND (e.g. pin 38) | 3 | G |
| SCL | GP3 (pin 5) | 4 | D− |
| RDY (optional) | GP15 (pin 20) | 5 | none |

**Connector choice.** The rest connects through either a magnetic pogo pair or a USB-C breakout pair. The keymap and the firmware are identical for both, and hot-plug works on both. The USB-C variant carries no RDY wire, so leave `POINTING_DEVICE_MOTION_PIN` undefined (the default). The firmware works without it: it times its reads to the pad's report window, and RDY would only avoid clock-stretching waits on the shared bus (an optional SBU mod adds it, [wiring.md §7.11](../wiring.md#711-optional-advanced-rdy-over-sbu)). With USB-C the pad runs at about 3.0–3.1 V after the diode, which changes nothing for the firmware.

If you port trackpad code from the owner's `cost_crafter40` keymap (another keyboard with the same TPS65 driver), do **not** copy its `I2C1_SDA_PIN GP18` / `I2C1_SCL_PIN GP19`: on Yakamoz those are matrix columns 8 and 9. The keyboard-level `mcuconf.h` in the fork already enables `RP_I2C_USE_I2C1`, so unlike cost_crafter40 no keymap-level `mcuconf.h` is needed. [wiring.md](../wiring.md) at the repo root has the physical wiring.

## Using it in a QMK userspace

The simplest route is `./build.sh` (next section), which needs only Docker. To build the keymap from your own [QMK userspace](https://docs.qmk.fm/newbs_external_userspace) instead:

1. Copy the folder:
   ```sh
   cp -R firmware/qmk_userspace/keyboards/yakamoz/keymaps/ardakilic_trackpad \
         <path to the qmk_userspace>/keyboards/yakamoz/keymaps/
   ```
2. Register the build target. Either run `qmk userspace-add -kb yakamoz -km ardakilic_trackpad`, or add this entry to `build_targets` in `qmk.json`:
   ```json
   ["yakamoz", "ardakilic_trackpad"]
   ```
3. Build it against a QMK tree that has `keyboards/yakamoz` (from the [Ardakilic/qmk_firmware](https://github.com/Ardakilic/qmk_firmware) fork) and up-to-date submodules. The fork's own CI currently needs a submodule fix first: see [Maintainer notes](#maintainer-notes-ardakilicqmk_userspace).

## Building locally (docker only)

```sh
cd firmware
./build.sh                                  # both keymaps, QMK master, output in firmware/build/
QMK_REF=33292390974c75362ca30873c482d052e0bd7a63 ./build.sh   # the exact QMK commit verified here
KEYMAPS=ardakilic_trackpad ./build.sh       # only the trackpad keymap
WORK_DIR=/path/to/scratch ./build.sh        # where qmk_firmware is cloned (default: $TMPDIR/yakamoz-qmk-build)
```

The script runs everything inside `ghcr.io/qmk/qmk_cli` (verified with image digest `sha256:b7d7fa8f…`):

- a shallow clone of `qmk/qmk_firmware` with submodules at `QMK_REF`
- `keyboards/yakamoz` from `Ardakilic/qmk_firmware@7bed308` (`FORK_REF`)
- the baseline `ardakilic` keymap from `Ardakilic/qmk_userspace@ef35653` (`USERSPACE_REF`)
- the keymaps in `qmk_userspace/keyboards/yakamoz/keymaps/`
- `qmk compile` for each keymap, with fresh objects every time

It treats any `warning:` or `error:` as a failure. It is idempotent: re-runs reset the clone to `QMK_REF` and re-copy everything.

**keyboard.json:** the fork already ships `keyboards/yakamoz/keyboard.json`, which current QMK requires (`lib/python/qmk/path.py`). No fix was needed. `build.sh` only renames `info.json` → `keyboard.json` in the scratch copy if an older definition without `keyboard.json` is used. The fork's own keymaps (`default`, `default_trackball`, `vial`) are dropped from the scratch copy because they are not built.

## Config knobs (`ardakilic_trackpad/config.h`)

| Define | Default | Notes |
|---|---|---|
| `AZOTEQ_IQS5XX_ROTATION_90` / `_180` / `_270` | none (factory axes) | Use at most one. The rotation is done inside the IQS5xx, so scrolling rotates too. See [Calibration](#calibration-30-seconds). |
| `TRACKPAD_CPI` | `500` | Re-applied after every (re)init. 500 CPI = 1280 × 965 counts over 65 × 49 mm. `0` keeps the pad's native ~1200 CPI. |
| `I2C1_CLOCK_SPEED` | `400000` | Drop to `100000` if the cable is unreliable: cursor stutter or jumps, OLED garbage, or `Pad:` flickering. 100 kHz makes OLED refreshes take ~4× more bus time. |
| `POINTING_DEVICE_MOTION_PIN` | commented out (`GP15`) | Optional TPS65 RDY line. IQS5xx RDY is active-high, and QMK's azoteq branch is already active-high: `pointing_device.h` defines `POINTING_DEVICE_MOTION_PIN_ACTIVE_LOW` for many sensors but not for `azoteq_iqs5xx`, and `pointing_device.c` then reads `if (gpio_read_pin(POINTING_DEVICE_MOTION_PIN))`. So **do not** define `_ACTIVE_LOW`. With RDY defined, the driver's automatic 11 ms polling throttle is dropped (`azoteq_iqs5xx.h`: `#if !defined(POINTING_DEVICE_TASK_THROTTLE_MS) && !defined(POINTING_DEVICE_MOTION_PIN)`): `pointing_device_task()` then sends on every main-loop pass and reads the pad only while RDY is high. The keymap's button release and hot-plug check run in `matrix_scan_user()`, before that read, and act only while RDY is high too, so holds stay pressed and the check needs no forced read. The keymap adds an internal pull-down so an unplugged cable reads "no data". Define it only when the wire is connected: with the pin defined and RDY not wired, the pad is never read. The USB-C connector has no RDY wire, so leave it undefined there. |
| `AZOTEQ_IQS5XX_PRESS_AND_HOLD_ENABLE` | `true` | Drag-and-drop without the removed click keys: rest one finger without moving for **~450 ms** (Tap time + Hold time, datasheet 6.2; driver defaults `AZOTEQ_IQS5XX_TAP_TIME` 150 ms + `AZOTEQ_IQS5XX_HOLD_TIME` 300 ms), then move with the left button held; lift to release. Define `AZOTEQ_IQS5XX_HOLD_TIME` to change the delay. Comment the line out if resting a finger gives unwanted clicks; drag is then impossible unless you put `MS_BTN1` on a reachable key (a held keyboard mouse button is never released by the tap-latch workaround). |
| `TRACKPAD_HOTPLUG_INTERVAL_MS` | `1000` | How often presence and reset are checked. |
| `TRACKPAD_NO_TAP_LATCH_FIX` | undefined | Disables the tap-latch workaround (only if QMK fixes the driver and you want the code out). |

`TRACKPAD_HOTPLUG_SETTLE_MS` (250), `TRACKPAD_HOTPLUG_RETRY_MS` (5000), `TRACKPAD_I2C_TIMEOUT_MS` (12) and `TRACKPAD_ALIGN_MAX_WAIT_MS` (50) have `#ifndef` defaults in `keymap.c`.

Two things this keymap does not support: the trackball and the trackpad together, and two I2C buses. `POINTING_DEVICE_DRIVER` takes exactly one driver, so this keymap replaces the optional Pimoroni trackball (`keymaps/default_trackball`). Running both would need `POINTING_DEVICE_DRIVER = custom` with code that merges the two reports.

## Calibration (30 seconds)

The mounting in ithalat is touch side up, with the module's connector long edge facing the keyboard (away from you).

The Azoteq module datasheet does not document where the IQS550's (0,0) is relative to the connector, so the default is a reasoned guess:

- The driver's rotation code **toggles** the module's own XY-config bits (`azoteq_iqs5xx_set_xy_config()`: `if (flip_x) config.flip_x = !config.flip_x; …`). With no define, the TPS65's factory axes are kept.
- Natively, X runs along the 65 mm edge. QMK's TPS65 profile pairs `WIDTH_MM 65` with `RESOLUTION_X 3072`.
- QMK's three rotation options are pure rotations: switch plus one flip, or both flips. None of them is a mirror. That implies the factory frame is not mirrored when seen from the touch side.
- So the only real unknown is which long edge is "up". The default assumes the connector edge is "up", which matches this mounting.

Procedure: flash, plug the pad in, wait for `Pad: on`, then slide one finger slowly to the right and then away from you (toward the keyboard).

| What the cursor does | Fix in `config.h` |
|---|---|
| right, then up | correct, nothing to do |
| left, then down (both reversed) | `#define AZOTEQ_IQS5XX_ROTATION_180` |
| moves vertically when you slide right (axes swapped) | `#define AZOTEQ_IQS5XX_ROTATION_90`; if both directions are then reversed, use `_270` instead |
| only one axis reversed (a mirror; not expected) | `#define POINTING_DEVICE_INVERT_X` or `_INVERT_Y`. These are QMK generic, apply to the cursor only and not to scrolling. |

Rebuild with `KEYMAPS=ardakilic_trackpad ./build.sh` (about a minute). To enter the bootloader, double-tap reset (`RP2040_BOOTLOADER_DOUBLE_TAP_RESET`) or use `QK_BOOT` on the SODA layer. Then drop the `.uf2` onto `RPI-RP2`. Scroll direction is the driver's: `h`/`v` = finger X/Y delta. If it feels inverted, change the host's mouse scrolling setting.

## Hot-plug behaviour and limits

QMK initialises pointing devices **only at boot**. If the pad is missing then, `pointing_device_init()` sets `POINTING_DEVICE_STATUS_INIT_FAILED`, and `pointing_device_task()` returns early for the rest of the session:

```c
if (pointing_device_get_status() != POINTING_DEVICE_STATUS_SUCCESS) {
    return false;
}
```

Core has no retry on purpose. PR #25315 leaves it to user code.

`matrix_scan_user()` runs `trackpad_hotplug_task()` at most once per `TRACKPAD_HOTPLUG_INTERVAL_MS`. QMK calls `matrix_scan_user()` from `matrix_task()` (`matrix_scan()` → `matrix_scan_kb()` → `matrix_scan_user()`), so it runs in the same main-loop pass as `pointing_device_task()`, but before it:

- **While the pad is not running**, the keymap probes `0x74` with `i2c_ping_address()`, retrying once after 200 µs because the IQS5xx NACKs the first address while in low power. It then confirms the product number (IQS550/572/525). An absent pad NACKs its address immediately: two attempts cost well under 1 ms per second, and the driver is not polled at all. When the pad answers twice, 250 ms apart (the connector may still be mating), the keymap calls `pointing_device_init()` again. That runs the driver's init and then `pointing_device_init_user()`, which re-applies CPI and acknowledges the reset flag.
- **While the pad is running**, the keymap reads System Info 0 (`0x000F`).
  - No answer means the pad was unplugged. The keymap sets the status to `FAILED` (which stops the driver hitting a missing device every 11 ms), releases any pad button and sends the report.
  - `SHOW_RESET` (bit 7) set means the pad was power-cycled (re-plugged faster than the check interval) or its watchdog fired, and the QMK settings are gone. The keymap re-initialises. After every init the flag is acknowledged via System Control 0 (`0x0431`, bit 7 `ACK_RESET`, write `0x80`; the other bits are no-op commands when 0).
  - The read waits for the pad's communication window: without RDY, one report period (10 ms) after the driver's last poll, i.e. just before its next one; with RDY wired, while RDY is high, which `matrix_scan_user()` sees before the driver's read in the same pass uses the window up. The window is left open, and the driver's poll in the same or the next pass reads that cycle's data and ends it. So the check should add no clock stretching on the shared bus and loses no report cycle (a tap is reported in one cycle only). In the simulation, 10 s of running gives 0 forced reads and 0 lost cycles in both builds. Only if no open window is seen within `TRACKPAD_ALIGN_MAX_WAIT_MS` (50 ms; e.g. RDY defined but the wire broken) is a forced read done: the pad stretches SCL for up to one report period until its window opens, and that window is also left to the driver.

Limits and risks:

- **Latency:** after plugging in, the pad is usable after about 0.25–1.25 s plus init. After unplugging, it is marked absent within about 1 s. The OLED shows the state (`Pad: on` / `Pad: --`).
- **One ~111 ms hitch per plug-in.** The driver's init blocks: soft reset, then `wait_ms(100)`, then `wait_ms(11)`. A key pressed *and* released entirely inside that window can be missed; held keys are not affected. Booting without the pad also costs those 100 ms once. That is existing QMK behaviour.
- **Electrical:** I2C is not designed for hot-plugging. If SDA/SCL touch before GND and 3V3, the pad can be briefly back-powered, and a transfer on the shared bus can be corrupted. An OLED block that fails is retried automatically. A bus held low by a confused device cannot be fixed in firmware; replug USB. If in doubt, plug the pad in with the keyboard's USB disconnected; the firmware handles both cases. Never wire the pad to 5 V.
- If init fails while the pad still answers (e.g. a flaky contact), it is retried every 5 s, not every second, to avoid repeated 111 ms hitches.
- The check assumes a single IQS5xx at the default address. `AZOTEQ_IQS5XX_ADDRESS` is honoured if you define it.

## Tap-latch finding (QMK ≥ 0.34.0)

**Verified real** against QMK master `33292390974c` (2026-11-12). Commit `0d401d1182`, "Preserve Azoteq mouse buttons (#26248)", merged 2026-06-13, is contained in tag `0.34.0` and not in `0.33.13` (checked with `gh api compare`). It changed one line in `drivers/sensors/azoteq_iqs5xx.c`:

```c
// drivers/sensors/azoteq_iqs5xx.c @ 33292390974c
356 report_mouse_t azoteq_iqs5xx_get_report(report_mouse_t mouse_report) {
357     report_mouse_t temp_report = {.buttons = mouse_report.buttons};   // was: = {0};
...
369         if (base_data.gesture_events_0.single_tap || base_data.gesture_events_0.press_and_hold) {
371             temp_report.buttons = pointing_device_handle_buttons(temp_report.buttons, true, POINTING_DEVICE_BUTTON1);
```

All 8 `pointing_device_handle_buttons()` calls in the driver (lines 371-397) pass `pressed = true`. The driver never clears a button. The core then feeds the previous report back in and keeps its buttons:

```c
// quantum/pointing_device/pointing_device.c @ 33292390974c
343     local_mouse_report = pointing_device_driver->get_report(local_mouse_report);
...
246     // send it and 0 it out except for buttons, so those stay until they are explicity over-ridden using update_pointing_device
247     uint8_t buttons = local_mouse_report.buttons;
248     memset(&local_mouse_report, 0, sizeof(local_mouse_report));
249     local_mouse_report.buttons = buttons;
...
252     return should_send_report || buttons;
```

So a tap's BUTTON1 is sent once and then fed back into the driver on every poll, and it is never released. The only code that clears it is `pointing_device_keycode_handler()` (lines 574-579), which runs on a real `MS_BTN1` key release, and on this build those keys are physically gone. A side effect is that `pointing_device_send()` keeps returning true while a button is held, so the pointing device counts as "active" and the OLED never times out. QMK's own tests for #26248 (`tests/pointing/azoteq_iqs5xx/`) only check that incoming buttons are preserved; none checks that a tap is released. The closed alternative PR #26357 said the same: "gesture-generated clicks would then remain latched".

**Workaround** (keymap only; keeps `POINTING_DEVICE_DRIVER = azoteq_iqs5xx`; public API only):

- `pointing_device_task_user()` stores `buttons & ~mousekey_get_report().buttons`, i.e. the buttons that no key holds, which are the pad's.
- `matrix_scan_user()` removes those bits from the report with `pointing_device_get_report()` and `pointing_device_set_report()` just before the driver reads the pad again, so that read starts without them. It runs in `matrix_task()`, before `pointing_device_task()` in the same main-loop pass.
  - Without RDY, it removes them in the next pass. `pointing_device_task()` is throttled to 11 ms and returns before sending anything until its next poll, which reads the pad first.
  - With `POINTING_DEVICE_MOTION_PIN`, it removes them only while RDY is high, i.e. in the pass where the driver reads. There is no throttle then: `pointing_device_task()` sends on every pass but reads only while RDY is high. A release done after the send (the first version of this keymap did it in `housekeeping_task_user()`) therefore reached the host in the passes between two reads, and a press-and-hold became a ~100 Hz click stream.

What the host sees:

- A tap is a press, then a release one report (10-11 ms) later. That is the same timing as before 0.34.0.
- Press-and-hold gives one press and one release, with or without RDY: the pad re-asserts the gesture on every read and an unchanged report is not resent. **Caveat:** if one driver read fails (I2C error, e.g. a flaky pogo contact) during a drag, the driver returns only the incoming buttons, so the host sees a release and, at the next good read, a new press. The dragged item may drop. QMK < 0.34.0 did the same, because its driver started every report from an empty one. Scenario test `OneFailedReadDuringHoldReleasesOnce` pins this behaviour.
- Keyboard mouse buttons are untouched.
- On QMK < 0.34.0 it is a no-op, because the driver ignores incoming buttons there.

Two alternatives were rejected:

- Switching to `POINTING_DEVICE_DRIVER = custom` with a driver wrapper. It works, but it changes the driver selection.
- Re-pointing the internal `pointing_device_driver` symbol, which is not part of any header.

Any other keymap that uses the `azoteq_iqs5xx` driver with tap gestures on QMK ≥ 0.34.0 latches taps the same way, and the same two functions fix it there.

### Scenario tests (simulation)

`./test.sh` (docker only; needs the clone from `./build.sh`) builds QMK's gtest harness with the real `pointing_device.c` and `azoteq_iqs5xx.c` on top of a simulated IQS5xx on a mocked I2C bus. The simulated pad also models the communication window. A window opens 10 ms after the previous one was ended, and RDY is high while it is open. A transfer outside the window is a forced read: the clock is stretched and the simulated time advances. A tap is reported in one cycle only, so a window ended without its data being read loses that cycle. The keymap block is extracted verbatim from `keymap.c`. `test.sh` builds four variants; the exit code reflects the two "must pass" ones:

- **stock**: QMK as is (informational).
- **control**: the block with `TRACKPAD_NO_TAP_LATCH_FIX` (informational: shows what the workaround fixes).
- **block, no RDY**: polled every 11 ms (must pass).
- **block + RDY**: with `POINTING_DEVICE_MOTION_PIN`, `gpio_read_pin()` reads the simulated RDY line (must pass).

The test loop calls `matrix_scan_user()` before `keyboard_task()` in every pass, because QMK's test matrix (`CUSTOM_MATRIX = yes`) has an empty `matrix_scan_kb()`. Results on `33292390974c`:

| Test | stock | control | block, no RDY | block + RDY |
|---|---|---|---|---|
| TapClicksAndReleases | **FAIL**: press at t=33 ms, no release | **FAIL** | pass | pass |
| TwoFingerTapRightClicksAndReleases | **FAIL**: report `B:3`, BUTTON1 still latched from the previous test | **FAIL** | pass | pass |
| PadPluggedAfterBoot | stays `INIT_FAILED` (no recovery in core) | pass | pass: `SUCCESS`, CPI 1280×965, reset acked | pass |
| CpiAppliedAndResetAcknowledgedAtInit, AbsentPadIsProbedCheaply (≤ 2 NACKs/s, 0 driver polls), UnplugDetectedAndReplugReinitialises, ResetBetweenChecksReinitialises | – | pass | pass | pass |
| PressAndHoldStaysPressedUntilLifted (exactly one press, one release) | – | **FAIL** | pass | pass |
| KeyboardMouseButtonIsNotReleasedByTheFix | – | **FAIL** | pass | pass |
| HotplugCheckNeitherStallsTheBusNorLosesACycle (10 s running) | – | pass | pass: 0 forced, 0 lost cycles | pass: 0 forced, 0 lost cycles |
| EveryTapIsDelivered (400 taps, one every 37 ms) | – | **FAIL**: 1 press, 0 releases | pass: 400/400 | pass: 400/400 |
| OneFailedReadDuringHoldReleasesOnce (pins the known limit: 2 presses, 2 releases) | – | **FAIL** (button still latched) | pass | pass |

The first version of this keymap, with the release and the hot-plug check in `housekeeping_task_user()`, passes "block, no RDY". It fails "block + RDY" in PressAndHoldStaysPressedUntilLifted (click stream) and HotplugCheckNeitherStallsTheBusNorLosesACycle (10 forced reads, 100 ms of clock stretching and 10 lost cycles in 10 s).

This is a model of the chip's register and window behaviour. It does not model bit-level I2C timing, the pad's own I2C timeout or electrical effects.

## Test checklist after flashing

1. **Without the pad plugged in:** the keyboard types normally, the startup song plays, and the OLED shows bitmap, layer, caps and `Pad: --`. Layers, Turkish macros, audio and RGB behave as with `ardakilic`. On SODA, `[3,4]` (the `Lower` key) now cycles the audio voice and `[3,9]` (the `Raise` key) toggles music mode: these are the copies of the removed `[3,6]`/`[3,7]`.
2. **Plug the pad in** (USB disconnected the first time with the pogo, which does not mate GND first; USB-C does, but if you hot-plug it, fit the 10 Ω resistor or PTC in its 3V3 wire, [wiring.md §7.10](../wiring.md#710-hot-plug)). On power-up, `Pad: on` appears and the cursor moves. Then try a live plug: `Pad: on` within ~1.5 s, with at most one short typing hitch.
3. **Direction:** do the [calibration](#calibration-30-seconds).
4. **Tap** in a text editor, then move: no text selection (the button was released). Tap on a desktop icon, then move: nothing is dragged.
5. **Two-finger tap** opens a context menu once. A left click afterwards works normally.
   **Press-and-hold drag:** rest one finger on a window title bar or file icon for ~0.5 s without moving, then move: it is dragged in one piece (no flicker, no repeated clicks), and it drops when you lift the finger.
6. **Two-finger scroll**, vertical and horizontal. Check the direction and speed.
7. **Unplug** while idle and while touching: `Pad: --` within ~1 s, no stuck button on the host, and the keyboard and OLED keep working. Replug: `Pad: on`.
8. **OLED:** no corrupted blocks during cursor movement. It sleeps after 15 s of no input, and moving on the pad wakes it.
9. **Speed:** adjust `TRACKPAD_CPI` if needed (default 500; `0` keeps the pad's native ~1200).
10. **Long session:** if the cursor stutters or `Pad:` flickers, switch to `I2C1_CLOCK_SPEED 100000`, and check the pull-ups (the keyboard's 4.7k in parallel with the module's ~4.7k).
11. **Optional RDY (pogo only):** wire connector pin 5 to GP15, uncomment `POINTING_DEVICE_MOTION_PIN GP15`, rebuild, and repeat steps 2, 4, 5 (including the press-and-hold drag: one smooth drag, not a stream of clicks) and 7.

## Known open points

- Factory axis orientation: best guess, see [Calibration](#calibration-30-seconds).
- Nothing has been timed on hardware. That includes the claim that the running-state check adds no clock stretching (shown only in the simulation), and the I2C signal integrity of either connector (pogo or USB-C) at 400 kHz.
- A dropped I2C read during a press-and-hold drag releases the button for one read (see the caveat under [Tap-latch finding](#tap-latch-finding-qmk--0340)). If the pogo cable turns out flaky, this shows as dropped drags.
- The tap-latch workaround depends on `MOUSEKEY_ENABLE` (set in `keyboards/yakamoz/rules.mk`) to tell keyboard buttons from pad buttons. Without mousekey, a held keyboard mouse button would be released after one report.
- Built and tested against QMK master `33292390974c`. Later QMK changes to the azoteq driver or pointing core may change the picture. Re-run `./build.sh` and `./test.sh` after bumping QMK.

## Maintainer notes (Ardakilic/qmk_userspace)

These notes are for the owner's other repositories, [Ardakilic/qmk_userspace](https://github.com/Ardakilic/qmk_userspace) and the [Ardakilic/qmk_firmware](https://github.com/Ardakilic/qmk_firmware) fork. You do not need them to build or flash ithalat: `./build.sh` already works around the problem below.

### qmk_userspace CI and the fork's stale submodules

The `Ardakilic/qmk_userspace` `main` branch last built green on 2026-03-29 (run `23719399243`, at `ef35653`), before the fork sync of 2026-09-24. The latest run (`36069148228`, 2026-09-24, on the `migrate/keyboard-json` branch of the open PR #1, not on `main`) failed every ChibiOS target, `yakamoz:ardakilic` included, with:

```
./lib/chibios/os/hal/include/hal.h:136:2: error: #error "obsolete or unknown configuration file"
```

That CI builds against the fork's current `master` (`.github/workflows/build_binaries.yaml`: `qmk_repo: Ardakilic/qmk_firmware`, `qmk_ref: master`), so the next push to `main`, for example one that adds `ardakilic_trackpad`, will very likely hit the same error on every RP2040 target. The cause is that the fork (`master` @ `7bed308`, "sync fork") merged upstream's code but kept **old submodule pointers**. The new ChibiOS config templates therefore meet an old ChibiOS:

| submodule | Ardakilic/qmk_firmware | upstream master |
|---|---|---|
| `lib/chibios` | `2365f844…` | `6170ddf92d55be54c89b708d1882eea229edeb2c` |
| `lib/chibios-contrib` | `8d863d9e…` | `5a9ad82b6ba4f649cdb800e8c2bbc9be2d3ce767` |
| `lib/pico-sdk` | `a3398d8d…` | `d0c5cac430cc955b65efa0e899748853d9a80928` |

Supporting evidence: `build.sh` builds the fork's **unchanged** `keyboards/yakamoz` and the **unchanged** `ardakilic` keymap against upstream master with correct submodules, and both compile with zero warnings. The keyboard definition and keymap are fine; only the gitlinks are stale. The fork tree itself was not rebuilt locally; the error text above comes from the CI log.

Fix, in a clone of the fork (this records upstream's gitlinks):

```sh
git update-index --cacheinfo 160000,6170ddf92d55be54c89b708d1882eea229edeb2c,lib/chibios
git update-index --cacheinfo 160000,5a9ad82b6ba4f649cdb800e8c2bbc9be2d3ce767,lib/chibios-contrib
git update-index --cacheinfo 160000,d0c5cac430cc955b65efa0e899748853d9a80928,lib/pico-sdk
git update-index --cacheinfo 160000,6910c9d9165801d8827d628cb72eb7ea9dd538c5,lib/googletest
git commit -m "chore: sync submodule pointers with upstream qmk_firmware"
git push
```

The SHAs are upstream master as of 2026-11-12. For future syncs, merge `upstream/master` normally and then run `git submodule update --init --recursive`. The CI's `publish` job runs on `always()`, which is why the current `latest` release holds only the four AVR binaries.

An alternative that needs no fork maintenance (untested): build against `qmk/qmk_firmware` and use the reusable workflow's `preparation_command` to copy `keyboards/yakamoz` and `keyboards/cost_crafter40` from the fork into `./qmk_firmware/keyboards/`. That is exactly what `build.sh` does.

### cost_crafter40: tap latch and CPI

- **Tap latch.** The fork's `master` (synced 2026-09-24) contains `0d401d1182`, so the `cost_crafter40` trackpad keymap will latch taps too on its next build (see [Tap-latch finding](#tap-latch-finding-qmk--0340)). The same two functions fix it there.
- **CPI never applied.** `cost_crafter40/keymaps/ardakilic/keymap.c` (and `woodpecker`) wraps `pointing_device_set_cpi(500)` in `#ifdef POINTING_DEVICE_DRIVER`. That macro does not exist for keymap code. For this driver the build defines only `-DPOINTING_DEVICE_DRIVER_azoteq_iqs5xx`, `-DPOINTING_DEVICE_DRIVER_AZOTEQ_IQS5XX`, `-DPOINTING_DEVICE_DRIVER_NAME=azoteq_iqs5xx` and `-DPOINTING_DEVICE_ENABLE` (checked in this build's `cflags.txt`). The function-like `POINTING_DEVICE_DRIVER(name)` is private to `pointing_device.c`. The CPI line has therefore never been compiled, and that board runs at the pad's native ~1200 CPI. Fix: use `#ifdef POINTING_DEVICE_ENABLE`. Better, set the CPI in `pointing_device_init_user()` (as `ardakilic_trackpad` does), so it is re-applied after any re-init.
