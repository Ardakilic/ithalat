# Yakamoz firmware: Azoteq TPS65 trackpad ("ithalat") + OLED

QMK keymap `ithalat` for [Yakamoz](https://github.com/ozkan/Yakamoz) (Raspberry Pi Pico / RP2040). It is ozkan's stock `default` keymap plus the ithalat trackpad, and the SH1107 OLED keeps working.

## TL;DR

- **What it is:** the stock keymap from [ozkan/Yakamoz-qmk](https://github.com/ozkan/Yakamoz-qmk) plus an Azoteq TPS65 trackpad (IQS550 controller) in the ithalat rest, on a pluggable cable. Nothing else changes, apart from a small OLED layer-line fix ([What changes vs. stock](#what-changes-vs-stock)).
- **Trackpad:** tap = left click, 2-finger tap = right click, press-and-hold = drag, 2-finger scroll. The OLED shows `Pad: on` / `Pad: --`.
- **Flash it:** drop the prebuilt `build/yakamoz_ithalat.uf2` onto `RPI-RP2`. No build needed ([Flash it](#flash-it)).
- **Two keys go:** the dock replaces the two front-row centre switches. Their functions move to the Adjust layer or to the pad ([Removed keys](#removed-keys)).
- **Build it:** `./build.sh`, Docker only ([Building locally](#building-locally-docker-only)).
- **Test it:** `./test.sh`, Docker only, after `./build.sh` ([Scenario tests](#scenario-tests-simulation)).
- **Both connectors:** the same firmware works with the magnetic pogo and USB-C. Hot-plug works on both.
- **License:** GPL-2.0-or-later, not the repo's MIT ([License](#license)).

> [!WARNING]
> **Not tested on hardware.**
>
> - **Checked so far:** everything here was compiled and checked against the QMK sources. The trackpad behaviour was also exercised in a host-side simulation ([Scenario tests](#scenario-tests-simulation)).
> - **Not yet done:** nothing has run on a real Yakamoz with a real TPS65.
> - **So:** work through the [test checklist](#test-checklist-after-flashing) on first flash.

**Jump to**

- [Flash it](#flash-it) · [What changes vs. stock](#what-changes-vs-stock) · [Removed keys](#removed-keys)
- [Wiring summary](#wiring-summary-firmware-view)
- [Building locally](#building-locally-docker-only) · [Using it in a QMK userspace](#using-it-in-a-qmk-userspace)
- [Config knobs](#config-knobs-ithalatconfigh)
- [Calibration (30 seconds)](#calibration-30-seconds)
- [Hot-plug behaviour and limits](#hot-plug-behaviour-and-limits)
- [Scenario tests](#scenario-tests-simulation) · [Test checklist after flashing](#test-checklist-after-flashing) · [Known open points](#known-open-points)
- [Files in this folder](#files-in-this-folder) · [Tap-latch finding](#tap-latch-finding-qmk--0340)
- [License](#license)

This folder is part of [ithalat](../README.md). The physical wiring is in [wiring.md](../wiring.md).

## Flash it

Wired the rest already? Beep-test the wiring first ([wiring.md, Step 4](../wiring.md#step-4-test-before-power-up)).

1. **Get the file:** `firmware/build/yakamoz_ithalat.uf2`. It is prebuilt and committed (QMK master `33292390974c`, keyboard from `ozkan/Yakamoz-qmk@d6b6212`).
2. **Enter the bootloader**, any of:
   - double-tap reset (`RP2040_BOOTLOADER_DOUBLE_TAP_RESET`);
   - hold `Tab` while plugging in USB (Bootmagic);
   - on the running keyboard: Adjust + `Tab` (`QK_BOOT`). Adjust = hold `Lower` and `Raise`.
3. **Copy it:** drop the `.uf2` onto the `RPI-RP2` drive.
4. **Plug the pad in:** unplug USB, connect the pad, plug USB back in. This is required for the pogo the first time; USB-C mates GND first ([checklist step 2](#test-checklist-after-flashing)). Wait for `Pad: on` on the OLED.
5. **Check it:** do the [calibration](#calibration-30-seconds) and the [test checklist](#test-checklist-after-flashing).

> [!TIP]
> **Works on an unmodified Yakamoz too.** Every stock keycode stays where it was. Without a pad the OLED shows `Pad: --` and the keyboard behaves like stock. So there is no separate stock image ([why](#keyboard-source)).

## What changes vs. stock

- **Diff base:** `yakamoz/keymaps/default` in [ozkan/Yakamoz-qmk](https://github.com/ozkan/Yakamoz-qmk) @ `d6b6212` (its `master`, 2024-06-30).
- **Nothing removed:** every stock line is still there (one OLED line is fixed in place). The changes are additions, keycode renames, three keycodes on Adjust keys that were transparent, and that OLED fix.

| Area | Change |
|---|---|
| Layers (Qwerty, Colemak, Dvorak, Lower, Raise, Adjust) | unchanged, except the renames and the 3 Adjust copies below |
| Keycode renames | `RGB_xxx` → `UG_xxx`, `KC_MS_BTN2` → `MS_BTN2`: same functions, new names |
| Adjust layer | copies of the removed keys' functions: `QK_BOOT` on `Tab`, `DB_TOGG` on `Esc`, `KC_SCRL` on `Caps` |
| OLED (picture, layer, caps) | unchanged, except the layer line now shows the selected Colemak/Dvorak base layer (fix); plus one line `Pad: on` / `Pad: --` |
| Audio (Imperial March), RGB, WPM, caps LED GP25 | unchanged |
| `rules.mk` | adds the azoteq pointing driver |
| `config.h` | adds the trackpad settings |
| `keymap.c` | adds init, hot-plug and tap-latch code |

<details><summary>Every change in full</summary>

**Keycode renames**

- QMK removed the old names in its 2025-08-31 breaking-changes release ([#25444](https://github.com/qmk/qmk_firmware/pull/25444)). The unmodified stock keymap no longer compiles on current QMK (`'RGB_VAI' undeclared`, `'KC_MS_BTN2' undeclared`).
- `RGB_VAI`/`RGB_VAD` → `UG_VALU`/`UG_VALD`, `RGB_SAI`/`RGB_SAD` → `UG_SATU`/`UG_SATD`, `RGB_HUI`/`RGB_HUD` → `UG_HUEU`/`UG_HUED`, `RGB_MOD` → `UG_NEXT`, `RGB_TOG` → `UG_TOGG`, `KC_MS_BTN2` → `MS_BTN2`.

**Adjust layer:** see [Removed keys](#removed-keys).

**OLED (SH1107 64x128, VS Code picture, layer, caps)**

- **Layer line fix:** stock reads `get_highest_layer(layer_state)`. The `Qwerty`/`Colemak`/`Dvorak` keys set the default layer, which lives in `default_layer_state`, so stock showed `L: QWERTY` whenever `Lower`/`Raise` were not held. It now reads `layer_state | default_layer_state`, the pattern QMK's own docs use (`docs/features/rgb_matrix.md`).
- **Caps line pinned to line 11** (one added `oled_set_cursor(0, 10)`, part of the fix). The 10-character `L: COLEMAK` would push it to line 12, and the screen is not cleared between frames, so a layer change left a stale second caps line. Stock never showed `COLEMAK`, so it never hit this.
- One new line `Pad: on` / `Pad: --` on text line 14.
- Lines 0-7 are the picture, 9 the layer and 11 caps. `Caps: OFF  ` wraps its last blank onto line 12, so line 14 is always free.
- The line is 10 characters, so it is fully overwritten every frame.

**`rules.mk`**

- Adds `POINTING_DEVICE_ENABLE = yes` and `POINTING_DEVICE_DRIVER = azoteq_iqs5xx`.

**`config.h`**

- Adds `AZOTEQ_IQS5XX_TPS65`.
- Adds the I2C bus (`I2CD1`, GP2/GP3, the existing OLED bus) and `I2C1_CLOCK_SPEED 400000`.
- Adds an optional RDY pin (commented out) and rotation options (commented out).
- Adds `TRACKPAD_CPI 500`, `TRACKPAD_HOTPLUG_INTERVAL_MS 1000` and `AZOTEQ_IQS5XX_PRESS_AND_HOLD_ENABLE true`.

**`keymap.c`**

- `pointing_device_init_user()` re-applies CPI and acknowledges the pad's reset flag.
- `matrix_scan_user()` runs the hot-plug check and the tap-latch workaround. It runs before `pointing_device_task()` in each main-loop pass (see [Tap-latch finding](#tap-latch-finding-qmk--0340)).
- `pointing_device_task_user()` records which buttons came from the pad.
- `pointing_device_keycode_handler()` replaces QMK's weak one (same logic), so an `MS_BTNx` key does not drop a drag.
- The trackpad code is inside `#ifdef POINTING_DEVICE_ENABLE`. The stock keymap defines none of these four functions.

</details>

### Removed keys

The dock replaces the two front-row centre switches, SW44 (`[3,6]`, left of centre) and SW43 (`[3,7]`, right of centre).

| Switch | Stock: base layers | Stock: Adjust | Now |
|---|---|---|---|
| SW44 `[3,6]` | `KC_SCRL` (Scroll Lock) | `QK_BOOT` (bootloader) | Scroll Lock: Adjust + `Caps`. Bootloader: Adjust + `Tab` |
| SW43 `[3,7]` | `MS_BTN2` (right click) | `DB_TOGG` (debug) | Right click: 2-finger tap. Debug: Adjust + `Esc` |

- **Adjust = hold `Lower` and `Raise`.** The copies sit in its left column, which was transparent.
- **Originals stay in place,** so the keymap still works on an unmodified board.
- **Left click:** the stock keymap has no left-click key. Tap the pad.
- **Drag:** press-and-hold on the pad (enabled by default, see [Config knobs](#config-knobs-ithalatconfigh)).
- **Side effect:** Adjust + `Tab` / `Esc` / `Caps` no longer fall through to `` ` `` / `Delete` / Caps Lock.

### Keyboard source

- **Where `keyboards/yakamoz` comes from:** `yakamoz/` in [ozkan/Yakamoz-qmk](https://github.com/ozkan/Yakamoz-qmk), pinned to `d6b6212`. That is the keyboard's own QMK repo. Yakamoz is not in upstream QMK.
- **One fix in the build copy:** `build.sh` renames `info.json` → `keyboard.json`. Current QMK only finds keyboards that have a `keyboard.json` (`lib/python/qmk/path.py`). The content is unchanged.

<details><summary>Why not another copy, and why the stock keymaps are not built</summary>

- **`user_song_list.h` is needed.** The keyboard's `config.h` sets the startup song to `STAR_WARS_IMPERIAL_MARCH`, which only `yakamoz/user_song_list.h` defines. Copies of `keyboards/yakamoz` without that file (some QMK forks have one) fail with `'STAR_WARS_IMPERIAL_MARCH' undeclared` as soon as a keymap enables audio, as the stock keymap does.
- **The stock keymaps do not build on current QMK.** `default`, `default_trackball` and `vial*` still use the removed `RGB_xxx` / `KC_MS_BTN2` names. `build.sh` drops them from the build copy; only the keymap of this folder is built.
- **Other source?** `KB_REPO`, `KB_REF` and `KB_PATH` override it ([Building locally](#building-locally-docker-only)).

</details>

<details><summary>Why there is no stock image</summary>

- **`ithalat` already behaves like stock without a pad:** every stock keycode is in place. The trackpad code then only pings the pad's address once a second, which an absent pad NACKs at once.
- **A "stock" image would not be stock either:** the unmodified stock keymap no longer compiles on current QMK (see Keycode renames above).
- **One image** is less to keep in sync.

</details>

## Wiring summary (firmware view)

- **Shared bus:** the trackpad shares the OLED's I2C bus.
- **One peripheral:** QMK's `i2c_master` drives only one I2C peripheral.
- **No address clash:** OLED 0x3C, TPS65 0x74.
- **Full wiring guide:** [wiring.md, The wires](../wiring.md#the-wires).

| Signal | Pico | Pogo pin (both halves) | USB-C breakout pad |
|---|---|---|---|
| SDA | GP2 (pin 4) | 1 | D+ |
| 3V3 | 3V3(OUT) (pin 36) | 2 | V, via a series Schottky |
| GND | any GND (e.g. pin 38) | 3 | G |
| SCL | GP3 (pin 5) | 4 | D− |
| RDY (optional) | GP15 (pin 20) | 5 | none |

> [!WARNING]
> **3V3 only: never 5 V / VBUS.** With USB-C, 3V3 reaches the V pad through a series Schottky diode.

### Connector choice

- **Same firmware:** the rest connects through a magnetic pogo pair or a USB-C breakout pair. The keymap and the firmware are identical for both, and hot-plug works on both.
- **USB-C has no RDY wire:** leave `POINTING_DEVICE_MOTION_PIN` undefined (the default).
- **RDY is not needed:** the firmware times its reads to the pad's report window. RDY would only avoid clock-stretching waits on the shared bus.
- **RDY over USB-C:** an optional SBU mod adds it ([wiring-details.md, RDY over SBU](../docs/wiring-details.md#rdy-over-sbu-advanced)).
- **USB-C voltage:** the pad runs at about 3.0–3.1 V after the diode. That changes nothing for the firmware.
- **Porting trackpad code from another RP2040 board?** Skip its `I2C1_SDA_PIN GP18` / `I2C1_SCL_PIN GP19`. On Yakamoz those are matrix columns 8 and 9. No keymap-level `mcuconf.h` is needed: the keyboard's own enables `RP_I2C_USE_I2C1`.

## Building locally (docker only)

```sh
cd firmware
./build.sh                                  # the ithalat keymap, QMK master, output in firmware/build/
QMK_REF=33292390974c75362ca30873c482d052e0bd7a63 ./build.sh   # the exact QMK commit verified here
WORK_DIR=/path/to/scratch ./build.sh        # where qmk_firmware is cloned (default: $TMPDIR/yakamoz-qmk-build)
```

- **Docker only:** the script runs everything inside `ghcr.io/qmk/qmk_cli` (verified with image digest `sha256:b7d7fa8f…`).
- **Strict:** any `warning:` or `error:` counts as a failure.
- **Idempotent:** re-runs reset the clone to `QMK_REF` and re-copy everything.
- **Reproducible:** two runs on the same commits give a byte-identical `.uf2`.
- **Output:** `build.sh` overwrites `build/yakamoz_ithalat.uf2`.

<details><summary>What the script does, step by step</summary>

1. A shallow clone of `qmk/qmk_firmware` with submodules at `QMK_REF`.
2. `yakamoz/` from `ozkan/Yakamoz-qmk@d6b6212` (`KB_REPO`, `KB_REF`, `KB_PATH`), copied to `keyboards/yakamoz`, with `info.json` renamed to `keyboard.json` and the stock keymaps dropped ([Keyboard source](#keyboard-source)).
3. The keymap in `qmk_userspace/keyboards/yakamoz/keymaps/ithalat/`.
4. `qmk compile -kb yakamoz -km ithalat`, with fresh objects every time.

</details>

## Using it in a QMK userspace

The simplest route is `./build.sh` (above), which needs only Docker. To build the keymap from your own [QMK userspace](https://docs.qmk.fm/newbs_external_userspace) instead:

1. **Copy the folder:**
   ```sh
   cp -R firmware/qmk_userspace/keyboards/yakamoz/keymaps/ithalat \
         <path to the qmk_userspace>/keyboards/yakamoz/keymaps/
   ```
2. **Put the keyboard into your QMK tree:** copy `yakamoz/` from [ozkan/Yakamoz-qmk](https://github.com/ozkan/Yakamoz-qmk) to `qmk_firmware/keyboards/yakamoz` and rename its `info.json` to `keyboard.json`.
3. **Register the build target** (after step 2: `qmk userspace-add` rejects `-kb yakamoz` until the keyboard is installed). Either run `qmk userspace-add -kb yakamoz -km ithalat`, or add this entry to `build_targets` in `qmk.json`:
   ```json
   ["yakamoz", "ithalat"]
   ```
4. **Build it** with up-to-date submodules: `qmk compile -kb yakamoz -km ithalat`.

> [!NOTE]
> **A userspace holds keymaps, not keyboards.** QMK looks for keyboard definitions only in `qmk_firmware/keyboards/` (checked on master `33292390974c`). So step 2 is needed.

## Config knobs (`ithalat/config.h`)

All knobs are also documented inline in `config.h`.

| Define | Default | What it does |
|---|---|---|
| `AZOTEQ_IQS5XX_ROTATION_90` / `_180` / `_270` | none (factory axes) | rotates the axes |
| `TRACKPAD_CPI` | `500` | cursor speed |
| `I2C1_CLOCK_SPEED` | `400000` | I2C bus speed |
| `POINTING_DEVICE_MOTION_PIN` | commented out (`GP15`) | optional RDY line |
| `AZOTEQ_IQS5XX_PRESS_AND_HOLD_ENABLE` | `true` | press-and-hold drag |
| `TRACKPAD_HOTPLUG_INTERVAL_MS` | `1000` | how often presence and reset are checked |
| `TRACKPAD_NO_TAP_LATCH_FIX` | undefined | disables the tap-latch workaround |

**Rotation** (`AZOTEQ_IQS5XX_ROTATION_*`)

- **Use at most one.**
- **Scrolling rotates too:** the rotation is done inside the IQS5xx.
- **How to pick:** see [Calibration](#calibration-30-seconds).

**`TRACKPAD_CPI`**

- **Re-applied** after every (re)init.
- **500 CPI** = 1280 × 965 counts over 65 × 49 mm.
- **`0`** keeps the pad's native ~1200 CPI.

**`I2C1_CLOCK_SPEED`**

- **Drop to `100000`** if the cable is unreliable: cursor stutter or jumps, OLED garbage, or `Pad:` flickering.
- **Cost:** 100 kHz makes OLED refreshes take ~4× more bus time.

**`POINTING_DEVICE_MOTION_PIN`** (optional TPS65 RDY line)

- **Define it only when the wire is connected.** With the pin defined and RDY not wired, the pad is never read.
- **USB-C:** it has no RDY wire, so leave it undefined there.
- **Do not define `_ACTIVE_LOW`:** IQS5xx RDY is active-high.
- **Pull-down:** the keymap adds an internal pull-down, so an unplugged cable reads "no data".

<details><summary>Why active-high, and what changes with RDY defined</summary>

- IQS5xx RDY is active-high, and QMK's azoteq branch is already active-high.
- `pointing_device.h` defines `POINTING_DEVICE_MOTION_PIN_ACTIVE_LOW` for many sensors but not for `azoteq_iqs5xx`.
- `pointing_device.c` then reads `if (gpio_read_pin(POINTING_DEVICE_MOTION_PIN))`. So **do not** define `_ACTIVE_LOW`.
- With RDY defined, the driver's automatic 11 ms polling throttle is dropped (`azoteq_iqs5xx.h`: `#if !defined(POINTING_DEVICE_TASK_THROTTLE_MS) && !defined(POINTING_DEVICE_MOTION_PIN)`).
- `pointing_device_task()` then sends on every main-loop pass and reads the pad only while RDY is high.
- The keymap's button release and hot-plug check run in `matrix_scan_user()`, before that read, and act only while RDY is high too.
- So holds stay pressed and the check needs no forced read.

</details>

**`AZOTEQ_IQS5XX_PRESS_AND_HOLD_ENABLE`**

- **Why:** drag-and-drop without a click key (stock has no left-click key, and its right-click key is removed).
- **How:** rest one finger without moving for **~450 ms**, then move with the left button held. Lift to release.
- **Timing:** Tap time + Hold time (datasheet 6.2). Driver defaults: `AZOTEQ_IQS5XX_TAP_TIME` 150 ms + `AZOTEQ_IQS5XX_HOLD_TIME` 300 ms.
- **Change the delay:** define `AZOTEQ_IQS5XX_HOLD_TIME`.
- **Unwanted clicks when you rest a finger?** Comment the line out. Drag is then impossible unless you put `MS_BTN1` on a reachable key (a held keyboard mouse button is never released by the tap-latch workaround).

**`TRACKPAD_NO_TAP_LATCH_FIX`**

- **Only if** QMK fixes the driver and you want the code out.

**More defaults in `keymap.c`** (`#ifndef`, override if needed)

| Define | Default |
|---|---|
| `TRACKPAD_HOTPLUG_SETTLE_MS` | 250 |
| `TRACKPAD_HOTPLUG_RETRY_MS` | 5000 |
| `TRACKPAD_I2C_TIMEOUT_MS` | 12 |
| `TRACKPAD_ALIGN_MAX_WAIT_MS` | 50 |

**Not supported**

- **Trackball and trackpad together.** `POINTING_DEVICE_DRIVER` takes exactly one driver, so this keymap replaces the optional Pimoroni trackball (`keymaps/default_trackball`). Running both would need `POINTING_DEVICE_DRIVER = custom` with code that merges the two reports.
- **Two I2C buses.**

## Calibration (30 seconds)

- **Mounting:** touch side up, with the module's connector long edge facing the keyboard (away from you).
- **Default axes:** a reasoned guess ([why](#why-the-default-is-a-guess)).

**Steps**

1. **Flash**, plug the pad in, and wait for `Pad: on`.
2. **Slide one finger** slowly to the right.
3. **Then slide away from you** (toward the keyboard).
4. **Compare** with the table below and set the fix in `config.h`.
5. **Rebuild** with `./build.sh` (about a minute).
6. **Enter the bootloader:** Adjust + `Tab` (`QK_BOOT`), or double-tap reset.
7. **Flash:** drop the `.uf2` onto `RPI-RP2`.

| What the cursor does | Fix in `config.h` |
|---|---|
| right, then up | correct, nothing to do |
| left, then down (both reversed) | `#define AZOTEQ_IQS5XX_ROTATION_180` |
| moves vertically when you slide right (axes swapped) | `#define AZOTEQ_IQS5XX_ROTATION_90`; if both directions are then reversed, use `_270` instead |
| only one axis reversed (a mirror; not expected) | `#define POINTING_DEVICE_INVERT_X` or `_INVERT_Y` |

- **`_INVERT_X` / `_INVERT_Y`** are QMK generic. They apply to the cursor only, not to scrolling.

> [!TIP]
> **Scroll feels inverted?** Scroll direction is the driver's: `h`/`v` = finger X/Y delta. Change the host's mouse scrolling setting.

### Why the default is a guess

The Azoteq module datasheet does not document where the IQS550's (0,0) is relative to the connector.

<details><summary>The reasoning behind the default</summary>

- The driver's rotation code **toggles** the module's own XY-config bits (`azoteq_iqs5xx_set_xy_config()`: `if (flip_x) config.flip_x = !config.flip_x; …`). With no define, the TPS65's factory axes are kept.
- Natively, X runs along the 65 mm edge. QMK's TPS65 profile pairs `WIDTH_MM 65` with `RESOLUTION_X 3072`.
- QMK's three rotation options are pure rotations: switch plus one flip, or both flips. None of them is a mirror. That implies the factory frame is not mirrored when seen from the touch side.
- So the only real unknown is which long edge is "up". The default assumes the connector edge is "up", which matches this mounting.

</details>

## Hot-plug behaviour and limits

- **Plug in:** the pad is usable after about 0.25–1.25 s plus init.
  - The slowest case is about 1.25 s plus the ~111 ms init.
  - Other pages round this figure: about a second, about 1.3 s, 1–1.5 s, ~1.5 s or 1–2 s. This section is the reference.
- **Unplug:** the pad is marked absent within about 1 s.
- **OLED** shows the state: `Pad: on` / `Pad: --`.
- **One ~111 ms hitch** per plug-in ([Limits and risks](#limits-and-risks)).
- **If in doubt:** plug the pad in with the keyboard's USB disconnected. The firmware handles both cases.

### Why the keymap has to do it

- **QMK initialises pointing devices only at boot.**
- If the pad is missing then, `pointing_device_init()` sets `POINTING_DEVICE_STATUS_INIT_FAILED`.
- `pointing_device_task()` then returns early for the rest of the session:

```c
if (pointing_device_get_status() != POINTING_DEVICE_STATUS_SUCCESS) {
    return false;
}
```

- **Core has no retry on purpose.** PR #25315 leaves it to user code.

### How the check works

- **When:** `matrix_scan_user()` runs `trackpad_hotplug_task()` at most once per `TRACKPAD_HOTPLUG_INTERVAL_MS`.
- **Order:** QMK calls `matrix_scan_user()` from `matrix_task()` (`matrix_scan()` → `matrix_scan_kb()` → `matrix_scan_user()`). So it runs in the same main-loop pass as `pointing_device_task()`, but before it.

**While the pad is not running**

1. **Probe:** the keymap probes `0x74` with `i2c_ping_address()`. It retries once after 200 µs, because the IQS5xx NACKs the first address while in low power.
2. **Confirm:** it checks the product number (IQS550/572/525).
3. **Cheap when absent:** an absent pad NACKs its address immediately. Two attempts cost well under 1 ms per second, and the driver is not polled at all.
4. **Settle:** the pad must answer twice, 250 ms apart (the connector may still be mating).
5. **Init:** the keymap calls `pointing_device_init()` again. That runs the driver's init and then `pointing_device_init_user()`, which re-applies CPI and acknowledges the reset flag.

**While the pad is running**

- **Read:** the keymap reads System Info 0 (`0x000F`).
- **No answer = unplugged.** The keymap sets the status to `FAILED` (which stops the driver hitting a missing device every 11 ms), releases any pad button and sends the report.
- **`SHOW_RESET` (bit 7) set = power-cycled.** The pad was re-plugged faster than the check interval, or its watchdog fired, and the QMK settings are gone. The keymap re-initialises.
- **Re-init fails** (e.g. the contact drops during it): the driver stops sending, so the keymap releases any pad button and sends the report, as on unplug. Buttons held by keys stay pressed.
- **Reset ack:** after every init the flag is acknowledged via System Control 0 (`0x0431`, bit 7 `ACK_RESET`, write `0x80`; the other bits are no-op commands when 0).

<details><summary>Timing: how the read avoids stalling the shared bus</summary>

- The read waits for the pad's communication window.
- **Without RDY:** one report period (10 ms) after the driver's last poll, i.e. just before its next one.
- **With RDY wired:** while RDY is high, which `matrix_scan_user()` sees before the driver's read in the same pass uses the window up.
- The window is left open. The driver's poll in the same or the next pass reads that cycle's data and ends it.
- So the check should add no clock stretching on the shared bus and loses no report cycle (a tap is reported in one cycle only).
- In the simulation, 10 s of running gives 0 forced reads and 0 lost cycles in both builds.
- **Fallback:** only if no open window is seen within `TRACKPAD_ALIGN_MAX_WAIT_MS` (50 ms; e.g. RDY defined but the wire broken) is a forced read done. The pad stretches SCL for up to one report period until its window opens, and that window is also left to the driver.

</details>

### Limits and risks

> [!WARNING]
> **Never wire the pad to 5 V.** And remember: I2C is not designed for hot-plugging. If in doubt, plug the pad in with the keyboard's USB disconnected; the firmware handles both cases.

- **Latency:** after plugging in, the pad is usable after about 0.25–1.25 s plus init. After unplugging, it is marked absent within about 1 s. The OLED shows the state (`Pad: on` / `Pad: --`).
- **One ~111 ms hitch per plug-in.** The driver's init blocks: soft reset, then `wait_ms(100)`, then `wait_ms(11)`.
  - A key pressed *and* released entirely inside that window can be missed. Held keys are not affected.
  - Booting without the pad also costs those 100 ms once. That is existing QMK behaviour.
- **Electrical:** if SDA/SCL touch before GND and 3V3, the pad can be briefly back-powered, and a transfer on the shared bus can be corrupted.
  - An OLED block that fails is retried automatically.
  - A bus held low by a confused device cannot be fixed in firmware: replug USB.
- **Flaky contact:** if init fails while the pad still answers, it is retried every 5 s, not every second, to avoid repeated 111 ms hitches.
- **One pad only:** the check assumes a single IQS5xx at the default address. `AZOTEQ_IQS5XX_ADDRESS` is honoured if you define it.

## Scenario tests (simulation)

- **Run:** `./test.sh` (docker only; needs the clone from `./build.sh`).
- **What it builds:** QMK's gtest harness with the real `pointing_device.c` and `azoteq_iqs5xx.c`, on top of a simulated IQS5xx on a mocked I2C bus.
- **Keymap code:** the trackpad block is extracted verbatim from `ithalat/keymap.c`.
- **Files:** `test.sh` and `tests/azoteq_scenarios/` (with and without the RDY wire).
- **Four variants:** `test.sh` builds the four below. The exit code reflects the two "must pass" ones.

| Variant | What it is | Must pass? | Result on `33292390974c` |
|---|---|---|---|
| **stock** | QMK as is | no (informational) | 1 of 3 pass (the 2 tap tests fail, as expected) |
| **control** | the block with `TRACKPAD_NO_TAP_LATCH_FIX`; shows what the workaround fixes | no (informational) | 7 of 16 pass |
| **block, no RDY** | polled every 11 ms | yes | 16 of 16 pass |
| **block + RDY** | with `POINTING_DEVICE_MOTION_PIN`; `gpio_read_pin()` reads the simulated RDY line | yes | 16 of 16 pass |

> [!NOTE]
> **It is a model.** It covers the chip's register and window behaviour. It does not model bit-level I2C timing, the pad's own I2C timeout or electrical effects.

<details><summary>How the simulated pad works</summary>

- The simulated pad models the communication window.
- A window opens 10 ms after the previous one was ended, and RDY is high while it is open.
- A transfer outside the window is a forced read: the clock is stretched and the simulated time advances.
- A tap is reported in one cycle only, so a window ended without its data being read loses that cycle.
- The test loop calls `matrix_scan_user()` before `keyboard_task()` in every pass, because QMK's test matrix (`CUSTOM_MATRIX = yes`) has an empty `matrix_scan_kb()`.

</details>

<details><summary>Results on 33292390974c (full table)</summary>

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
| MouseKeyDuringDragKeepsTheDragHeld (40 `MS_BTN2` taps during a hold: button 1 pressed and released once) | – | **FAIL** | pass | pass |
| MouseKeyTapInTheReadWindowKeepsTheDragHeld (a macro key does `tap_code(MS_BTN1)` whenever the pad's window is open during a hold: button 1 pressed and released once) | – | **FAIL** | pass | pass |
| FailedReinitReleasesTheDragButKeepsKeyButtons (pad drag + `MS_BTN2` key) | – | **FAIL** (button 1 still latched from earlier tests) | pass | pass |
| FailedReinitReleasesPadButtonKeepsKeyButton1 (pad button 2 + `MS_BTN1` key) | – | pass | pass | pass |

**MouseKeyDuringDragKeepsTheDragHeld and the two FailedReinit tests** fail in both "must pass" builds without the mouse-key and failed-re-init handling (12 of 15, before MouseKeyTapInTheReadWindowKeepsTheDragHeld was added).

**MouseKeyTapInTheReadWindowKeepsTheDragHeld** fails in both "must pass" builds without the mouse-key handling. It also fails with the handler's first version, which added the pad's buttons before the key's own transition (15 of 16).

**The first version of this trackpad code** had the release and the hot-plug check in `housekeeping_task_user()`.

- It passes "block, no RDY".
- It fails "block + RDY" in PressAndHoldStaysPressedUntilLifted (click stream).
- It also fails HotplugCheckNeitherStallsTheBusNorLosesACycle: 10 forced reads, 100 ms of clock stretching and 10 lost cycles in 10 s.

</details>

## Test checklist after flashing

Do these in order on first flash.

1. [ ] **Without the pad plugged in:**
   - The keyboard types normally, the startup song (Imperial March) plays, and the OLED shows the picture, layer, caps and `Pad: --`.
   - Layers, RGB and audio behave as stock. Adjust + `Qwerty`/`Colemak`/`Dvorak` still switch the base layer, and the OLED keeps showing it after `Lower` and `Raise` are released.
   - Adjust + `Caps` toggles Scroll Lock. (Adjust + `Tab` enters the bootloader, so try that one last.)
2. [ ] **Plug the pad in:**
   - **Pogo:** USB disconnected the first time, because the pogo does not mate GND first.
   - **USB-C:** mates GND first. If you hot-plug it, fit the 10 Ω resistor or PTC in its 3V3 wire ([wiring.md, Plugging and unplugging](../wiring.md#plugging-and-unplugging)).
   - On power-up, `Pad: on` appears and the cursor moves.
   - Then try a live plug: `Pad: on` within ~1.5 s, with at most one short typing hitch.
3. [ ] **Direction:** do the [calibration](#calibration-30-seconds).
4. [ ] **Tap:**
   - Tap in a text editor, then move: no text selection (the button was released).
   - Tap on a desktop icon, then move: nothing is dragged.
5. [ ] **Two-finger tap and press-and-hold drag:**
   - A two-finger tap opens a context menu once. A left click afterwards works normally.
   - **Press-and-hold drag:** rest one finger on a window title bar or file icon for ~0.5 s without moving, then move. It is dragged in one piece (no flicker, no repeated clicks), and it drops when you lift the finger.
6. [ ] **Two-finger scroll**, vertical and horizontal. Check the direction and speed.
7. [ ] **Unplug** while idle and while touching:
   - `Pad: --` within ~1 s, no stuck button on the host, and the keyboard and OLED keep working.
   - Replug: `Pad: on`.
8. [ ] **OLED:** no corrupted blocks during cursor movement. It sleeps after 15 s of no input, and moving on the pad wakes it.
9. [ ] **Speed:** adjust `TRACKPAD_CPI` if needed (default 500; `0` keeps the pad's native ~1200).
10. [ ] **Long session:** if the cursor stutters or `Pad:` flickers, switch to `I2C1_CLOCK_SPEED 100000`. Check the pull-ups (the keyboard's 4.7k in parallel with the module's ~4.7k).
11. [ ] **Optional RDY (pogo only):**
    - Wire connector pin 5 to GP15.
    - Uncomment `POINTING_DEVICE_MOTION_PIN GP15` and rebuild.
    - Repeat steps 2, 4, 5 (including the press-and-hold drag: one smooth drag, not a stream of clicks) and 7.

## Known open points

- **Factory axis orientation:** best guess, see [Calibration](#calibration-30-seconds).
- **Nothing timed on hardware.** That includes the claim that the running-state check adds no clock stretching (shown only in the simulation), and the I2C signal integrity of either connector (pogo or USB-C) at 400 kHz.
- **Dropped drags:** a dropped I2C read during a press-and-hold drag releases the button for one read (see the caveat under [Tap-latch finding](#tap-latch-finding-qmk--0340)). If the pogo cable turns out flaky, this shows as dropped drags.
- **Needs mousekey:** the tap-latch workaround depends on `MOUSEKEY_ENABLE` (set in the keyboard's `rules.mk`) to tell keyboard buttons from pad buttons. Without mousekey, a held keyboard mouse button would be released after one report.
- **Pinned QMK:** built and tested against QMK master `33292390974c`. Later QMK changes to the azoteq driver or pointing core may change the picture. Re-run `./build.sh` and `./test.sh` after bumping QMK.

## Files in this folder

| Path | What |
|---|---|
| `qmk_userspace/keyboards/yakamoz/keymaps/ithalat/keymap.c` | the stock `default` keymap plus the trackpad code and an OLED status line |
| `.../ithalat/config.h` | the stock config plus the trackpad settings |
| `.../ithalat/rules.mk` | the stock rules plus the pointing-device driver |
| `build.sh` | reproducible docker-only build |
| `test.sh`, `tests/azoteq_scenarios/` | docker-only scenario tests |
| `build/yakamoz_ithalat.uf2` | prebuilt image, committed for flashing without a build; anything else in `build/` is git-ignored |

- **Layout:** the folder layout matches a QMK userspace, so the keymap folder can be copied straight into one.
- **Prebuilt image:** QMK master `33292390974c`, keyboard `ozkan/Yakamoz-qmk@d6b6212`. `build.sh` overwrites it.

### Firmware size

QMK master `33292390974c`, measured with `arm-none-eabi-size`:

| keymap | text | bss | .uf2 |
|---|---|---|---|
| stock `default` (renames only, not shipped) | 48 160 B | 265 024 B | 96 768 B |
| `ithalat` | 50 976 B (+2 816 B) | 265 016 B | 102 400 B |

- **Not a concern:** the Pico has 2 MB of flash.

## Tap-latch finding (QMK ≥ 0.34.0)

- **Problem:** on QMK ≥ 0.34.0, the `azoteq_iqs5xx` driver never releases a tap's button. A tap click stays latched.
- **Fix:** this keymap releases the pad's buttons itself. Keymap only, public API only, and it keeps `POINTING_DEVICE_DRIVER = azoteq_iqs5xx`.
- **Other keymaps:** any other keymap that uses the `azoteq_iqs5xx` driver with tap gestures on QMK ≥ 0.34.0 latches taps the same way. The same two functions fix it there.

### The cause

- **Verified real** against QMK master `33292390974c` (2026-11-12).
- **Commit:** `0d401d1182`, "Preserve Azoteq mouse buttons (#26248)", merged 2026-06-13.
- **Versions:** it is contained in tag `0.34.0` and not in `0.33.13` (checked with `gh api compare`).
- **The change:** one line in `drivers/sensors/azoteq_iqs5xx.c`. The report now starts from the incoming buttons instead of from an empty report.
- **Result:** a tap's BUTTON1 is sent once and then fed back into the driver on every poll, and it is never released.
- **Only release path:** `pointing_device_keycode_handler()` (lines 574-579), which runs on a real `MS_BTN1` key release. The stock keymap has no such key.
- **Side effect:** `pointing_device_send()` keeps returning true while a button is held. So the pointing device counts as "active" and the OLED never times out.

<details><summary>Code evidence and upstream history</summary>

The changed line:

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

- QMK's own tests for #26248 (`tests/pointing/azoteq_iqs5xx/`) only check that incoming buttons are preserved. None checks that a tap is released.
- The closed alternative PR #26357 said the same: "gesture-generated clicks would then remain latched".

</details>

### The workaround

- **Record:** `pointing_device_task_user()` stores `buttons & ~mousekey_get_report().buttons`, i.e. the buttons that no key holds, which are the pad's.
- **Release:** `matrix_scan_user()` removes those bits from the report with `pointing_device_get_report()` and `pointing_device_set_report()`, just before the driver reads the pad again. That read then starts without them.
- **Timing:** it runs in `matrix_task()`, before `pointing_device_task()` in the same main-loop pass.
  - **Without RDY:** it removes them in the next pass. `pointing_device_task()` is throttled to 11 ms and returns before sending anything until its next poll, which reads the pad first.
  - **With `POINTING_DEVICE_MOTION_PIN`:** it removes them only while RDY is high, i.e. in the pass where the driver reads. There is no throttle then: `pointing_device_task()` sends on every pass but reads only while RDY is high.
  - **Why not later:** a release done after the send (the first version of this code did it in `housekeeping_task_user()`) reached the host in the passes between two reads. A press-and-hold then became a ~100 Hz click stream.
- **Mouse keys in between:** an `MS_BTNx` key sends its report at once (`register_mouse()` → `pointing_device_keycode_handler()`), also between the release and the driver's read. The keymap replaces QMK's weak handler with the same logic, but that report still carries the pad buttons removed since the last read; they are removed again right after. They are added after the key's own press or release, so releasing an `MS_BTN1` key does not release a drag the pad still holds.

### What the host sees

- **Tap:** a press, then a release one report (10-11 ms) later. That is the same timing as before 0.34.0.
- **Press-and-hold:** one press and one release, with or without RDY. The pad re-asserts the gesture on every read, and an unchanged report is not resent.
- **Keyboard mouse buttons** (for example the stock right-click key on an unmodified board) are untouched. Pressing one during a drag does not drop the drag.
- **QMK < 0.34.0:** the workaround is a no-op, because the driver ignores incoming buttons there.

> [!NOTE]
> **Caveat: a failed read can drop a drag.**
>
> - **Cause:** if one driver read fails during a drag (I2C error, e.g. a flaky pogo contact), the driver returns only the incoming buttons.
> - **Effect:** the host sees a release and, at the next good read, a new press, so the dragged item may drop.
> - **Not new:** QMK < 0.34.0 did the same, because its driver started every report from an empty one.
> - **Pinned by** scenario test `OneFailedReadDuringHoldReleasesOnce`.

<details><summary>Two rejected alternatives</summary>

- **Switching to `POINTING_DEVICE_DRIVER = custom`** with a driver wrapper. It works, but it changes the driver selection.
- **Re-pointing the internal `pointing_device_driver` symbol,** which is not part of any header.

</details>

## License

- **`firmware/` is GPL-2.0-or-later.** QMK is [GPL-2.0-or-later](https://github.com/qmk/qmk_firmware/blob/master/LICENSE), and this keymap is ozkan's GPL stock keymap plus the trackpad code (`keymap.c` header: "Copyright 2023 ozkan").
- **The prebuilt `.uf2` image** in `build/` is built from QMK and the Yakamoz keyboard definition, so it falls under the GPL too.
- **The root MIT [LICENSE](../LICENSE) does not cover** `firmware/` or the `.uf2` image.
