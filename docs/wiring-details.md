# Wiring details

The reference behind [wiring.md](../wiring.md): positions, reasons, calculations, alternatives and the full test notes. Build from wiring.md; it links here wherever you need more.

## TL;DR

- **Build from [wiring.md](../wiring.md).** Come here for the "why", exact positions and edge cases.
- **Bus facts:** OLED at 0x3C, TPS65 at 0x74 (QMK writes 0xE8), 400 kHz, pull-ups about 2.35 kΩ in total.
- **The under-plate route modifies the case.** It works with the pogo dock only.
- **USB-C safety comes in layers:** series Schottky, CC resistors removed, "NOT USB" labels. The grip side stays unprotected.
- **Old links** like `wiring.md#7-usb-c-variant`: see [old section numbers](#old-section-numbers).

**Jump to**

- Basics: [Conventions](#conventions) · [How the link works](#how-the-link-works) · [Full signal table](#full-signal-table)
- Build notes: [Keyboard side](#keyboard-side-in-depth) · [Rest side](#rest-side-in-depth) · [Electrical notes](#electrical-notes) · [USB-C in depth](#usb-c-in-depth)
- Checks and extras: [Tests in depth](#tests-in-depth) · [Other connectors](#other-connectors) · [ASCII diagrams](#ascii-diagrams) · [Old section numbers](#old-section-numbers)

## Conventions

- **Keyboard positions** are in mm, in the keyboard's top-view frame.
  - Origin: the keyboard's front-left corner.
  - X runs to the right as the typist sees it. Y runs toward the back (USB end). Z runs up.
- **Mirrored KiCad file.** The main-PCB KiCad file is drawn from the *bottom*, so its X axis is mirrored. Every position here is already converted to the top view.
- **TPS65 orientation.** "Back view" means the component side, connector edge at the top. Mounted in the rest, the touch side faces up and the connector edge faces the keyboard.
- **"Plug" has three meanings here.**
  - Dock plugs: the two hollow stubs under a dock that drop into the switch cut-outs.
  - Pogo plug: the spring-pin half of the pogo pair, on the pigtail.
  - USB-C plug: the male board's connector, in the grip.
- **Config names** in `UPPER_CASE` refer to [`config.py`](../config.py).
- **Firmware** settings are in [`firmware/`](../firmware/). The firmware is the same for both connectors.

## How the link works

The trackpad shares the OLED's I2C bus. Nothing is re-routed, no PCB traces are cut, and the OLED stays.

- **The bus already exists.** The Yakamoz drives its OLED on RP2040 I2C1: SDA = GP2 (Pico pin 4), SCL = GP3 (pin 5).
- **Pull-ups exist too:** the main PCB has 4.7 kΩ pull-ups R1/R2 to 3V3.
- **The TPS65 joins that bus.** Its controller is an IQS550.
- **Four wires are required:** SDA, SCL, 3V3, GND. QMK's `azoteq_iqs5xx` driver uses only these four. The owner uses the same four-wire setup, with the same driver, on a cost_crafter40 keyboard.
- **RDY is optional, magnetic pogo only.** It goes to GP15 (Pico pin 20).
  - With it, QMK reads the pad only while RDY is high (`POINTING_DEVICE_MOTION_PIN GP15`). This avoids clock-stretching stalls on the shared bus.
  - Without it, QMK polls the pad every 11 ms. The USB-C variant does this ([RDY over SBU](#rdy-over-sbu-advanced) is an advanced mod).
- **NRST is not connected.** It has an internal 30–60 kΩ pull-up.
- **Pointing driver.** The trackpad and a PIM447 trackball cannot both be the QMK pointing driver. Leave the trackball out, or write a `custom` driver.

#### Why sharing the bus works

| Device | 7-bit address |
|---|---|
| OLED | 0x3C |
| TPS65 | 0x74 (QMK writes the 8-bit `0xE8`) |
| Pimoroni trackball option | 0x0A |

- **Different addresses:** no two match, so each device answers only to its own.
- **QMK supports only one I2C peripheral.** Sharing I2C1 is the intended setup, not a workaround.
- **No collisions:** QMK runs all I2C transfers one after another in a single thread. The OLED and the trackpad never talk over each other.
- **The PCB was built for a second I2C device:** the trackball header TB1 is on the same SDA/SCL nets as the OLED.

#### The two connectors

- **Same base:** both docks replace the front-row centre switches SW44 and SW43. Both use the same taps, wire route and rest.
- **Magnetic pogo:** a 5-pin, 2.54 mm magnetic pogo pair.
  - The **flat-pad half** (receptacle) is press-fitted in the printed pogo dock.
  - The **spring-pin half** (plug) sits on a short pigtail, soldered to the TPS65 pads and run through the rest's internal channel.
  - Its last 15 mm of loose wire rises out of the notch and plug bay on the centre line, straight into the back of the plug. The plug hangs on the dock face over the rest's back edge.
  - With the default rest, the route from the pads to the dock face is about 52 mm.
- **USB-C:** a cheap USB-C breakout pair ([USB-C in depth](#usb-c-in-depth)).
  - The blue **female** board is captured in the USB-C dock. Its receptacle sits at the bottom of a chamfered well in the dock face.
  - The green **male** board sits in a printed grip on a short pigtail from the TPS65, through the same channel as the pogo pigtail.
  - The 3V3 line passes through a series Schottky diode at the keyboard end.

<details><summary>Overview sketch (ASCII)</summary>

```
Pico GP2/GP3/3V3/GND ── main-PCB traces (R1/R2 4.7k) ── J2/TB1 link ── switchplate ── OLED (0x3C)
   │                                                                       │
   tap B: Pico pins 4/5/36/38                     tap A: OLED header joints or switchplate TB1
   (+ RDY: Pico pin 20, any tap, pogo only)                                │
   │                                                                       │
   └──── 4-5 x 30 AWG, flat on the switchplate, under the OLED cover ──────┘
                                     │
                     dock rear channel (no case modification)
                                     │
  pogo:   dock: pogo receptacle   ◄─ magnets ─►  plug ── short pigtail ── TPS65 (0x74)
  USB-C:  dock: Schottky + female ◄─ push ───►  male in grip ── short lead ── TPS65 (0x74)
```

</details>

## Full signal table

### Connector side

| Signal (colour) | Pogo pin | USB-C pad | TPS65 pad (J1 pin) |
|---|---|---|---|
| SDA (blue) | 1 | D+ | SDA (J1-6) |
| 3V3 (red) | 2 | V, through the Schottky | VDDHI, silk "3V3" (J1-4) |
| GND (black) | 3 | G | GND (J1-3) |
| SCL (yellow) | 4 | D− | SCL (J1-5) |
| RDY (green, optional) | 5 | none ([SBU mod](#rdy-over-sbu-advanced)) | RDY (J1-1) |
| NRST | none | none | NRST (J1-2): leave unconnected |

- **Pogo pinout,** the same on both halves: 1 SDA · 2 3V3 · 3 GND · 4 SCL · 5 RDY (`CONNECTOR_PINOUT`).
  - **GND is pin 3, the centre pin.** It stays in the middle even if a half is wired mirror-image.
  - **SDA and SCL are separated** by the two power pins. This follows I2C cable practice: keep each signal next to a power or ground conductor.
- **USB-C** uses the four pads both breakout boards already have: G = GND, V = 3V3 (through the series Schottky), D+ = SDA, D− = SCL. No RDY.
- **Pogo pin 1** is the end at the typist's left when you look at the dock face from the rest. Mated pins touch each other, so the same number meets the same number on both halves.

### Keyboard tap points

- **Order of preference:** A1 (TB1), A2 (OLED header), A3 (switchplate OL1), then B (Pico pins). The columns below follow it.
- **Neither tap modifies the case.** The main-PCB OL1 alternative does.

| Signal | A1: switchplate TB1 | A2: OLED header joint | A3: switchplate OL1 | B: Pico pin |
|---|---|---|---|---|
| SDA | "SDA", Y 62.9 | "SDA", X 131.6 | "SDA", Y 46.2 | pin 4, GP2 (I2C1 SDA) |
| 3V3 | "VDD", Y 60.3 | "VCC", X 136.7 | "VCC", Y 51.2 | pin 36, 3V3(OUT) |
| GND | "GND", Y 70.5 | "GND", X 139.3 | "GND", Y 53.8 | pin 38, or any digital GND: 3, 8, 13, 18, 23, 28 |
| SCL | "SCL", Y 65.4 | "SCL", X 134.2 | "SCL", Y 48.7 | pin 5, GP3 (I2C1 SCL) |
| RDY (optional) | not on any header | not on any header | not on any header | pin 20, GP15 |
| NRST | none | none | none | none |

**Main-PCB OL1 holes** (the alternative that modifies the case): OL1-1, leftmost, X 131.6 = SDA · OL1-2, X 134.2 = SCL · OL1-3, X 136.7 = 3V3 · OL1-4, X 139.3 = GND. No RDY, no NRST.

### Positions and notes

- **Wire colours** follow the Qwiic / STEMMA QT convention: black GND, red 3V3, blue SDA, yellow SCL. The USB-C and JST-SH variants use the same colours.
- **USB-C pad names** are the boards' silk labels. The male reads V, D−, D+, G. The female may only read G, D, D, V ([how to tell the D pads apart](#usb-c-signal-mapping)).
- **OLED header joints.** The OLED module plugs into switchplate OL2, directly above main OL1, at Y 24.2 on the keyboard centre line X 135.49. Top view, left to right: SDA, SCL, VCC (3V3), GND.
- **Switchplate TB1** is at X 148.1. Its fourth hole (INT, Y 67.9) is not connected.
- **Switchplate OL1** is at X 148.3.
- **Pico pin 33 is AGND,** the ADC's ground return. Use a digital GND pin.
- **Main-PCB OL1** holes sit right below the OLED header: same X and Y, same order.
- **Pico pin positions:**
  - Left row: X 126.6. Pin 4 at Y 69.2, pin 5 at 66.7, pin 18 at 33.6, pin 20 at 28.6.
  - Right row: X 144.4. Pin 23 at Y 33.6, pin 36 at 66.7, pin 38 at 71.7.
  - Pin 1 is the back-left pin, next to the USB connector.
- **TPS65 pads, back view, left to right:** RDY, NRST, GND, VDDHI, SCL, SDA.
  - Pitch 2.0 mm. Each pad is about 0.9 × 2.6 mm.
  - The pads are 4.9–7.1 mm from the connector edge.
  - In the touch-side (front) view the order reverses to SDA … RDY. That is the order of `TP_PAD_NAMES`.

## Keyboard side in depth

### Tools and test-fit

- **Unplug USB.** Work on an anti-static mat, or at least touch something grounded first.
- **Tools:** fine-tip iron (about 330 °C), 0.5 mm solder, flux, multimeter, tweezers, keycap puller, switch puller, 1.5 mm heat-shrink, Kapton tape.
  - For tap A at the TB1 socket: a 5-pin 2.54 mm male header.
  - A needle file only for the under-plate alternative, which modifies the case.
  - **USB-C also needs** the Schottky diode and hot tweezers or a second iron, to lift two tiny resistors.
- **Print and test-fit the dock first.**
  - **Magnetic pogo:** measure your pair. It should match `DOCK_CONN_W/H/D` = 20.1 × 4.2 × 4.0 mm. Generic pairs vary. If yours differs, change those values and regenerate.
  - **USB-C:** measure both boards and set the `USBC_*` constants ([board prep](#preparing-the-breakout-boards)). Cheap boards vary by seller.

### Remove SW44 and SW43

- **Positions:** SW44 is left of centre at X 125.95; SW43 is right of centre at X 145.00. Both at Y 11.93, matrix positions [3,6] and [3,7].
- **Keymap:** MS_BTN1/MS_BTN2 sit at these positions. They go dead once the switches are pulled; trackpad taps replace them.
- **SODA layer:** these positions carry QK_AUDIO_VOICE_NEXT and QK_MUSIC_TOGGLE. The `ardakilic_trackpad` keymap copies them to [3,4] and [3,9], so they stay reachable.
- **Pulling them:** pull both keycaps, then both switches with a switch puller. The sockets are hot-swap, so there is nothing to desolder. Keep the parts.
- **Nothing needs cutting:** GP13 and GP16 lead only to empty sockets; the diodes stay.
- **The switchplate stays in place** for the recommended wiring. Only the OLED cover comes off.
- **Look into the two 14 mm cut-outs.** Underneath is the 4.0 mm gap down to the main PCB.

### Where wires can and cannot run

Under the switchplate, the upper-middle acrylic layer fills the 4.0 mm gap, except at its openings.

- **Under the dock:** a 34.1 × 16.0 × 4.0 mm pocket (X 118.9–153.1, Y 4.0–20.0).
  - A 2.1 mm acrylic finger runs from its front wall back to Y 16.1.
  - Behind the finger, a 3.9 mm passage joins the left and right halves.
  - Wires run freely here and come up into the dock.
- **The pocket is closed at the back.**
  - A **2.9 mm acrylic bar** (Y 20.0–22.9) separates it from the 12.0 × 3.6 mm slot (Y 22.9–26.5) with the main-PCB OL1 holes.
  - The Pico window starts further back, at Y 25.9, and is walled off too.
- **So no ready-made under-plate path** leads from OL1 or the Pico to the dock. There are two routes:

| Route | Taps | Case modified? |
|---|---|---|
| Over-plate (recommended) | A and B | No: only the OLED cover comes off |
| Under-plate (alternative) | main-PCB OL1 only | Yes: a notch filed into the acrylic bar |

<details><summary>Over-plate clearances</summary>

- The wires lie flat on top of the switchplate, under the raised OLED cover.
- The cover's underside is about 9.2 mm above the plate as modelled. `OLED_COVER_T` is an estimate: measure yours.
- The wires come out under the cover's front edge at Y 22.1 and cross a short strip of open plate to the dock's back face.
- **Pogo dock:** back face at Y ≈ 19.6, about 2.5 mm from the cover edge.
- **USB-C dock:** deeper. Its back face is at Y ≈ 21.5, only 0.6 mm from the cover edge. Its top stays 0.2 mm under the cover's underside, so it still fits if your cover edge sits a little further forward.
- No acrylic work is needed.

</details>

- **Under-plate:** the notch is hidden inside the case, but the whole switchplate has to come off and an internal part is altered for good.
- **RDY can only be soldered at the Pico,** which sits above the switchplate. RDY always takes the over-plate route.

#### Which dock takes which route

- **Rear wire channel** (both docks), for the over-plate route. Open at the bottom, it leaves the dock's back face at plate level on the centre line, between the two plugs.
  - Pogo dock: 3.0 × 2.8 mm (`DOCK_REAR_CH_W`/`_H`).
  - USB-C dock: 4.0 × 3.9 mm (`USBC_REAR_CH_W`/`_H`).
  - Wires lie flat on the plate; the dock presses down over them.
- **Ø 5 mm hole down into each dock plug** (`DOCK_WIRE_HOLE`), pogo dock only. For the under-plate route or a small protection board under the plate. The plugs are hollow and open at the bottom into the 4 mm gap.
- **The USB-C dock has no hole:** its female board, the retainer screws and the clip-lock prongs fill the space above the plugs. With USB-C, use tap A or B and the over-plate route.

### Tap points in detail

- **Use tap A** if one of its points is free, otherwise tap B.
- **Both sit on top of the switchplate** under the OLED cover and use the over-plate route.
- **Tap A needs only the OLED cover off** (4 screws). Its points are on the same four nets as the Pico pins.

#### Tap A: switchplate pins

Pick in this order:

1. **A1: Switchplate TB1** (trackball socket, X 148.1). Back to front: GND, INT (n/c), SCL, SDA, VDD.
   - If a female socket is fitted and no trackball is used, plug in a 5-pin male header with the wires soldered to it. **No soldering on the keyboard.**
   - Do not use INT. Leave its header pin empty or cut it off.
   - **The header is not keyed.** The wrong way round, it swaps GND and VDD (and SDA and SCL). That puts −3.3 V on the trackpad, which is rated for −0.3 V at most.
     - Mark the GND end on the header and the board with a paint dot, or use a polarized housing, or glue the header in once tested.
     - **Before every power-up after re-seating it** (for example after the OLED cover was off), check that the red wire beeps to Pico pin 36 and the black wire to pin 38. With USB-C the red wire meets the Schottky's anode: check it there, before the diode.
2. **A2: The OLED module's header-pin joints** (switchplate OL2). Solder thin wires to them.
   - Top view, left to right, X 131.6 / 134.2 / 136.7 / 139.3: **SDA, SCL, VCC, GND** (the same order as main OL1 underneath). Confirm each with the meter.
   - The shortest route: the joints are only about 5 mm behind the dock.
   - Be quick: the display glass is close. Unplug the module to solder it if you can, and note which way round it was.
3. **A3: Switchplate OL1** (alternative OLED position, X 148.3). Back to front: GND, VCC, SCL, SDA. Use it if its holes are empty.

> [!WARNING]
> **Do not tap the J2 ↔ TB1 board-to-board link.** Its pin 4 is the switchplate RGB data line (GP1).

#### Tap B: the Pico pins

Solder to the top-side joints of the Pico's header pins.

- **SDA and SCL:** pin 4 (SDA) and pin 5 (SCL), left row.
- **3V3 and GND:** pin 36 (3V3) and pin 38 (GND), right row. Pin 23 or pin 18 (both GND, Y 33.6) is closer to the front.
- **Unplug the OLED module** while you work: it covers the front of the Pico.
- **Never bridge pins 36, 37 and 38.** Pin 37 is 3V3_EN: shorted to GND, it switches the 3V3 regulator off.
- **Pins 39 (VSYS) and 40 (VBUS) are 5 V.** Never connect them to the trackpad, with either connector.

### RDY wire

- **Magnetic pogo only.** Solder a green 30 AWG wire to Pico pin 20 = GP15.
- It is the front-most pin of the left row (X 126.6, Y 28.6), at the Pico's front-left corner.
- It is **not on any header**, so you must solder at the Pico.
- Route it over the plate to the dock with the other wires.
- Skip RDY: leave dock pin 5 empty.
- **USB-C:** skip it. The standard USB-C build has no RDY ([SBU mod](#rdy-over-sbu-advanced)).

### Over-plate route

For taps A and B.

1. Run the wires flat on the switchplate, under the cover:
   - from TB1 or switchplate OL1: forward along the free strip between the Pico and the right-hand key block (X ≈ 146–153);
   - from the OLED header: straight forward;
   - from the Pico pins: forward the same way, without lifting the OLED module.
2. Bring them out under the cover's front edge (Y 22.1) and across the open plate to the dock's back face. They enter the **rear wire channel**, centred on the keyboard centre line.
3. Keep them flat and tack them down with Kapton. Black Kapton hides the short visible stretch.
4. Do not run them over the Pico's USB connector, or under the OLED module where they would lift it.
5. Refit the OLED module (the right way round) and the cover.

### Under-plate alternative (modifies the case)

- **Only if you accept modifying the case,** and only with the magnetic pogo dock (the USB-C dock has no wire hole into its plugs).
- **Cost:** a notch filed into the 2.9 mm acrylic bar of the upper-middle frame, and a full teardown with every switch still in the plate.
- **Gain:** the four wires are hidden. RDY still comes over the plate from the Pico.
- **Why OL1:** in a switchplate build the OLED plugs into switchplate OL2, directly above main OL1. A socket on main OL1 would not fit in the 4 mm gap. So OL1's four plated holes are a ready-made tap: top view, left to right, SDA, SCL, 3V3, GND, at Y 24.2.

<details><summary>Under-plate steps (full teardown)</summary>

1. **Open the keyboard.**
   1. Remove the 4 screws of the OLED cover and lift it off.
   2. Unplug the OLED module. Note which way round it was.
   3. Pull the Pico straight up out of its two female headers. Rock it gently from end to end. The USB end faces the back.
   4. Remove the keycaps around the 8 switchplate screws. The screws sit at Y ≈ 21.5 and Y ≈ 59.5, each at the corner of four keys. Remove the screws.
   5. Lift the switchplate evenly, with all switches still in it. The switch pins slide out of the hot-swap sockets, and the switchplate's J2 pins slide out of the Mill-Max socket at TB1.
   6. Lift the 4 mm upper-middle acrylic frame off the main PCB.
2. **Confirm the holes are empty.**
   - From the top, look at the main PCB at X 131.6–139.3, Y 24.2: the centre line, just behind the two removed switches.
   - Open plated rings: free. Solder cones or cut pins: something is soldered there. Then use tap A or B.
3. **Identify pin 1 with a continuity tester** (USB unplugged).
   1. One probe on Pico pin 4 (SDA). The Pico is out, so use its female-header socket 4, the 4th from the back in the left row. Touch each OL1 hole: the one that beeps is **OL1-1 = SDA**.
   2. Repeat with Pico pin 5 for **SCL**, pin 36 for 3V3 (5th from the back, right row) and pin 38 for GND (3rd from the back, right row).
   3. Cross-check with resistance: the SDA and SCL holes each read about **4.7 kΩ to the 3V3 hole**, through R1 and R2.
   4. From the underside the left-to-right order looks mirrored. Trust the meter, never the position.
4. **File the notch.** Put the upper-middle frame on a flat surface.
   - In the 2.9 mm bar between the OL1 slot and the 2-key pocket, file a notch **about 4 mm wide and 2–2.5 mm deep** on the face that lies on the main PCB.
   - Anywhere along the OL1 slot, for example centred at X 133.
   - Support the frame while filing: the bar is thin. Deburr the edges.
5. **Solder 4 × 30 AWG silicone wires,** each about 8 cm, into the OL1 holes from the top.
   - 1 SDA blue · 2 SCL yellow · 3 3V3 red · 4 GND black.
   - Keep the joints low, under 1 mm. The switchplate OL2 socket's solder tails hang down into the same slot, right above these holes.
   - Bend each wire flat toward the notch straight away and cover the joints with Kapton, so no wire leans onto a neighbouring tail.
   - Trim anything that pokes out underneath.
6. **Dress the wires.**
   1. Lay them through the notch into the pocket, flat on the main PCB.
   2. Put Kapton over the empty SW44/SW43 socket holes in the pocket floor: those are live matrix nets.
   3. Put the frame back, wires in the notch.
7. **Reassemble.**
   1. Lower the switchplate. Line up all the switch pins and the J2 pins, then press evenly.
   2. Check that no wire is trapped between the layers: a trapped wire can short.
   3. Refit the screws, the Pico (USB at the back), the OLED and the cover.
   4. The four wires now wait in the pocket under the empty cut-outs. They go up into the pogo dock through the Ø 5 mm hole in either plug.

- **RDY on this route:** GP13 and GP16 are freed by the removed switches and reachable in the pocket from their empty sockets. Using one for RDY means changing the firmware matrix and `POINTING_DEVICE_MOTION_PIN`. This project's firmware uses GP15 (Pico pin 20, over the plate).

</details>

### Pogo receptacle notes

- **N/S keying:** an N/S-keyed pair (MG005 / Adafruit 5413: magnets in both halves) meets only one way round; reversed, it repels.
- **Check this with your pair** before you rely on it. A pair that mates either way round is unsafe ([pogo hot-plug](#hot-plug-magnetic-pogo), [bom.md](bom.md#2a-magnetic-pogo-connector)).
- **Pin 1:** a paint-pen dot on the same end of both halves marks pin 1 (SDA), at the typist's left.
- **Not "next to the N magnet":** do not use that pin as pin 1 on both halves. On the MG005 drawing, the pogo half's N end meets the pad half's S end.
- **Wire entry:** taps A and B and RDY enter through the rear channel at plate level. Under-plate wires come up through the Ø 5 mm hole in a dock plug.
- **Pin-1 triangle:** a small triangle on the dock's top face, above pin 1 (SDA, the −X end, at the typist's left).
- **Heat:** tails are 1.75 mm. Tin each wire first and spend only 2–3 s per joint: NdFeB magnets lose strength when hot. Shrink the tubing over each joint.
- **Continuity:** check each pad to its tap point, and that neighbouring pads do *not* beep ([beep tests](#beep-tests-magnetic-pogo)).
- **Press-fit:**
  - Flat face toward the rest, flush with the dock face, pin 1 on the left seen from the rest.
  - Pull the slack back as you press.
  - Loose? A drop of hot glue or CA behind it.
  - Hot glue over the tails inside the dock is the strain relief.
- **Clips:**
  - Press both dock plugs into the cut-outs until the clips snap under the 1.2 mm plate.
  - Check the dock sits flat and no wire is pinched (over-plate wires inside the rear channel).
  - The catches are angled at 45°, so a firm straight pull (about 20 N) takes the dock out without opening the case.

### Wire choice

Both connectors.

- **Use 28–30 AWG silicone stranded wire.** Very flexible, and it handles soldering heat well.
- **Inside the keyboard: 30 AWG** (about 0.8 mm outer diameter).
  - Five fit the pogo dock's 3.0 × 2.8 mm rear channel in two layers.
  - USB-C needs only four; its channel is 4.0 × 3.9 mm.
- **Five 28 AWG wires are a tight fit.** Kynar wire-wrap wire is thinner still.

## Rest side in depth

### The rest's pocket

It gives you room to work:

- **Ledge:** a 2 mm support ledge around the module edge.
- **Relief:** 1.6 mm under the component area.
- **Solder well:** 3.5 mm deep, under the pads and the ZIF connector (`POCKET_WELL_*`).
- **S-groove** in the well floor, deeper, for the sleeved cable as strain relief (`CABLE_CHANNEL_W` 4.5 mm wide, sideways offset `CABLE_SBEND` 5 mm). It:
  - starts at the back of the well on the centre line;
  - runs toward the typist past the pads;
  - jogs 5 mm toward the pad side;
  - ends about 10 mm in front of the pads, where the cable sleeve should end.
- **Tunnel:** short and enclosed (4.5 × 4.0 mm), under the back rim.
- **Riser and notch:** the tunnel rises through a riser into a U-notch (6 mm wide, 4 mm deep) at the back-top edge on the centre line (`CABLE_NOTCH_*`).
- **Plug bay:** shallow, around the notch (26 × 7 × 2 mm, `PLUG_BAY_*`, floor at z 9.8).
  - The docked pogo plug's strain-relief zone hangs over it, 2.2 mm above its floor.
  - With USB-C, the plugged grip floats above it and the wires turn down into the riser.

**Solder the connector last.** The pogo plug (20 × 4.2 mm) does not fit through the tunnel. Neither does the USB-C male board.

### Pigtail length

The pogo plug hangs on the dock face, right above the rest's back edge, so the pigtail is short. With the default rest, pads → dock face is about 52 mm. Verify prints it as "route length fits the pigtail".

| Stretch | Length (default) | What it is |
|---|---|---|
| Pads → groove end | ≈ 14 mm of route | bare wires, looping from the pads to the sleeve end |
| Groove + tunnel | ≈ 18 mm (glass) / 17 mm (bare) | sleeved, clamped in the S-groove |
| Tunnel → riser → plug tails | 15 mm (`CABLE_PLUG_LOOSE_LEN`) | pogo: bare wires rising straight into the back of the plug |

- **USB-C's last stretch is longer:** 15 mm of route (`CABLE_PLUG_LOOSE_LEN`) up the riser, into the grip's underside and over the push rib to the male pads, plus a 12 mm slack S-loop (`USBC_WIRE_SLACK`). That is 27 mm of loose wire beyond the sleeve end.
- **USB-C route,** pads → male board: about 49 mm (glass) / 48 mm (bare), or 61 / 60 mm with the slack.

### Full rest-side steps

The short version is [wiring.md Step 3](../wiring.md#step-3-rest-side-trackpad-pigtail). Here is everything.

<details><summary>Steps 1–5: pigtail, pads, insulation, route, strain relief (both connectors)</summary>

1. **Prepare the pigtail.**
   - Cut 5 × 28 AWG silicone wires (4 for USB-C), `CABLE_PIGTAIL_LEN` = 120 mm each. That is far more than the route needs, so they are easy to handle. You cut them to length later (pogo step 6, or the grip steps).
   - Twist loosely. Sleeve **about 18 mm** of the bundle (3 mm braid or 3–4 mm heat-shrink), starting about 15 mm from the module end. The sleeved part must stay ≤ 3.5 mm across (`CABLE_D`).
   - Everything else stays bare. The last stretch before the plug or male board must be loose single wires: they turn straight up through the riser and the plug bay, and a sleeve does not fit there.
2. **Solder to the TPS65 pads.**
   1. Lay the module touch side down on a clean cloth, connector edge away from you. **Keep the adhesive liner on:** it protects the adhesive from flux and fingers.
   2. Left to right the pads are **RDY · NRST · GND · VDDHI (3V3) · SCL · SDA**.
   3. Put Kapton over the ZIF connector J1 first. It is unused, and sits just below the pads in this view.
   4. Pre-tin both pads and wires.
   5. Solder: RDY green (optional, pogo only; USB-C leaves RDY empty), **NRST nothing**, GND black, VDDHI red, SCL yellow, SDA blue.
   6. Lay each wire flat along its pad, pointing **toward you**: toward the module centre, away from the connector edge, not standing up. In the rest the sleeved cable arrives from that side along the groove, and the wires pass over the taped J1.
3. **Insulate.**
   - Check for bridges under magnification.
   - Kapton over the six pads.
   - A thin bead of hot glue (or UV resin) where the wires leave the pads.
   - Keep wires and glue **inside the well footprint.** The well is 3.5 mm deep; everywhere else under the module there is only the 1.6 mm relief or the flat ledge.
4. **Route the cable.**
   - Thread the free end from the solder well along the centre-line end of the groove, into the tunnel, up the riser, and out of the notch at the back-top edge.
   - Pull until the sleeve's front end sits at the groove's end and its back end inside the tunnel, just before the riser. The module can still lie next to the rest for the next steps.
5. **Add strain relief.**
   - Press the sleeved part into the S-groove, the sleeve ending at the groove's end. Fix it with a few drops of hot glue, or neutral-cure silicone (not acetic RTV, which is corrosive).
   - Let the bare wires loop gently from there to the pads.
   - A pull on the plug or grip must stop at the rest, never at the 0.9 mm pads.
   - Nothing may rise above the ledge.

</details>

<details><summary>Step 6: solder the pogo plug (spring-pin half)</summary>

The plug exits downward (`PLUG_EXIT = 'down'`). The loose wires come up out of the riser about 2 mm in front of the plug's tails and turn straight back into them at connector height.

1. **Cut to length.** Set the rest in front of the keyboard (1.5 mm gap) with the dock fitted. Hold the plug mated to the receptacle. Lead each wire up out of the notch and back to its tail, add about 3 mm for the joint, and cut. Unplug the plug to solder it.
2. Slide 1.5 mm heat-shrink onto each wire. **Do not fit a large sleeve over the plug:** there is no room, because the plug hangs over the plug bay.
3. Solder pin 1 (the end you marked) = SDA blue, 2 = 3V3 red, 3 = GND black, 4 = SCL yellow, 5 = RDY green or nothing. The tails are 1.75 mm long. Spend only 2–3 s per joint (NdFeB magnets).
4. Shrink each joint. A thin bead of hot glue or UV resin across the tails is the strain relief.
5. **Keep the tails, joints, heat-shrink and glue within 3 mm behind the housing and 6 mm tall, centred on the connector axis** (`PLUG_RELIEF_L/H`). Verify checks that envelope: it clears the bay floor by 2.2 mm. Anything bigger can touch the rest and push the plug off the dock.
6. **Mate the pair and check end to end** ([beep tests](#beep-tests-magnetic-pogo)). This is what catches a mirror-image half.

</details>

<details><summary>Step 7: bond the glass (and the bare variant)</summary>

1. Clean the back of the glass with isopropyl alcohol and let it dry.
2. Peel the module's liner by its pull tab.
3. Put the glass face down on a clean, soft cloth. Lower the module onto it adhesive side down, aligned to all four edges. Both parts are 65 × 49 mm with corners of about R4.
   - Check the glass corner radius with a caliper or radius gauge first: the supplier does not publish it. The pocket's corners are R2.5 (`POCKET_CORNER_R`), so any corner of R1.65 or more fits.
4. Start from one short edge and roll down, so no air is trapped. **Air gaps reduce sensitivity.** Azoteq says to remove them completely.
5. Press firmly over the bare-PCB areas (never on the components) for about 30 s. 3M 468MP keeps gaining strength for about a day.

- **`bare` variant:** the paper liner makes a poor touch surface. Peel it and stick a thin film onto the adhesive instead: matte PET/PC or a textured PEI sheet, about 0.1–0.15 mm thick. The surface is designed to sit 0.15 mm below the rim (`TP_SURFACE_RECESS`).

</details>

<details><summary>Step 8: seat the module</summary>

1. Lower it into the pocket touch side up, connector edge toward the back (the keyboard). Fold the bare pad wires into the well as you go. The sleeve is already glued in the groove.
2. Press only in the middle, **never on the glass edges**.
3. It must lie flat on the ledge. If it rocks, a wire or glue blob is on the ledge: lift it out and re-dress.
4. The module is top-loaded and nothing pulls it upward, so friction is usually enough. To fix it, use 2–3 small squares of thin (≤ 0.1 mm) double-sided tape on the ledge, not on the glass.
5. **To remove it,** push gently with a pen from below through the two Ø 6 mm push holes (`PUSH_HOLE_POS`). They sit on bare PCB, clear of the components.

</details>

<details><summary>Step 9: dock the pogo plug</summary>

- Set the rest 1.5 mm in front of the keyboard (`REST_KEYBOARD_GAP`). The plug mates with the dock face, 0.6 mm behind the keyboard front, and hangs over the plug bay. The loose wires drop straight down into the riser.
- The plug must not rest on the rest or lift it. If it does, the strain-relief blob is too big (step 6).
- **Never lay the plug (with its magnets) on the glass:** metal near the pad disturbs tracking.
- Docked, its two magnets sit about 7 mm from the module. That is accepted: they do not move while the pad is powered, and the controller calibrates at power-up. Check for drift at the first power-up ([first power-up](#first-power-up)).

</details>

## Electrical notes

These apply to both connectors. USB-C adds its own: [the Schottky](#the-series-schottky-on-3v3), [it is not USB](#it-is-not-usb-chargers-and-laptops), [USB-C hot-plug](#hot-plug-usb-c).

### 3.3 V only

- **Supply range:** the TPS65 runs from 1.65–3.6 V, and 3.6 V is its absolute maximum. The RP2040 GPIOs are not 5 V tolerant.
- **Power the trackpad from Pico pin 36 = 3V3(OUT) only.** Never VBUS (pin 40) or VSYS (pin 39).
- **USB-C:** the 3V3 wire passes through a series Schottky at the keyboard end, so the pad gets about 3.0–3.1 V. Well inside 1.65–3.6 V.
- **Current:** about 2.2 mA (typical) while tracking. Negligible next to the 12 switchplate RGB LEDs and the OLED on the same 3V3 rail.

### Pull-ups

- **The parts involved:**
  - The main PCB has **R1/R2 = 4.7 kΩ** (SDA and SCL to 3V3).
  - The keycapsss photo of the TPS65 shows two 4.7 kΩ resistors, so the module **very likely has its own 4.7 kΩ** pull-ups.
  - The OLED module may have pull-ups too.
- **Expected value:** 4.7k ∥ 4.7k ≈ 2.35 kΩ. Ideal for 400 kHz.
  - Target: about 1.5–3.3 kΩ.
  - Absolute minimum: about 1 kΩ, because (3.3 − 0.4) V / 3 mA ≈ 0.97 kΩ.

#### How to measure

USB unplugged, meter on the 20 kΩ range.

1. **Red probe on 3V3, black on SDA.** On the keyboard: Pico pins 36 and 4 (or the matching tap-A points). Repeat for SCL.
   - This polarity keeps the chips' protection diodes reverse-biased. Swapped probes can give a misleadingly low reading.
2. First with the trackpad unplugged. Expect about 4.7 kΩ, or less if the OLED module adds its own.
3. On the trackpad alone: VDDHI pad → SDA pad. About 4.7 kΩ means the module has pull-ups.
4. Again with the trackpad plugged in. With USB-C, the Schottky sits between the keyboard's 3V3 and the module's pull-ups, so this reading can come out higher. Trust steps 2 and 3.

#### What to do with the result

| Total, pad plugged in | Action |
|---|---|
| about 1.5–3.3 kΩ | Nothing to do. |
| ≥ about 4 kΩ (no pull-ups on the module) | Add 4.7 kΩ from SDA and from SCL to 3V3 at the dock, or set `#define I2C1_CLOCK_SPEED 100000`. |
| < about 1.2 kΩ | Too strong. Remove one set (usually the OLED module's). Do not add more. |

> [!NOTE]
> **USB-C:** pull extra resistors up to the female board's V pad (the diode's cathode side), not to Pico 3V3. See [I2C levels with the diode](#the-series-schottky-on-3v3).

### Bus speed and cable length

- **Speed:** QMK's RP2040 default is 400 kHz.
- **Length:** the whole link is about 10–20 cm. That is 5–10 cm inside the keyboard (more from TB1 than from the OLED header) plus the short pigtail (about 5 cm).
- **Capacitance:** with the OLED and the PCB, roughly 50–100 pF, far below the 400 pF limit. The USB-C boards add less than 1 pF per line.
- **Rise time** ≈ 0.85 · R · C. At 2.35 kΩ and 100 pF: about 200 ns, inside Fast-mode's 300 ns limit.
- **If the OLED or the pad misbehaves,** set `#define I2C1_CLOCK_SPEED 100000` (or 200000). The cost is slower OLED refresh.
- **Pigtail limit:** do not go much past about 30 cm without lowering the bus speed or strengthening the pull-ups.
- **Keep the I2C wires away from** the RGB data line (GP1) and the buzzer (GP9).

### Optional protection parts

At the dock, on the keyboard side: the keyboard half is live and exposed whenever the rest is unplugged, so protection belongs there.

| Part | Where | Worth it when |
|---|---|---|
| 100 Ω in series with SDA, SCL (and RDY), 0805 | in line, receptacle → bus | you hot-plug often |
| TVS array ST USBLC6-4SC6 (SOT-23-6) | at the receptacle | dry or carpeted rooms, or pads touched a lot |
| PTC polyfuse, about 0.1 A hold (or at least 10 Ω), in 3V3 | at the receptacle | the magnets may collect steel debris |
| 100 kΩ RDY pull-down | at the receptacle | only for other firmware |

<details><summary>Why each part helps</summary>

- **100 Ω series resistors:** cheap insurance against hot-plug spikes and ESD current into the RP2040 pins. They raise the low level by only about 0.1 V. Recommended if you hot-plug often.
- **USBLC6-4SC6 TVS array,** dead-bugged on a scrap of perfboard: the TPS65 is rated only ±2 kV HBM. Connect the I/O pins to SDA, SCL and RDY, VBUS to 3V3, GND to GND. Check the pinout in the ST datasheet. With USB-C, the two-line USBLC6-2SC6 is enough: it was designed for exactly these D+/D− contacts.
- **PTC polyfuse:** the magnets attract steel debris (staples, swarf, paper clips) that can bridge the exposed 3V3 and GND pads. Without the fuse, a short browns out the Pico, which then reset-loops. With it, the keyboard keeps running.
- **100 kΩ RDY pull-down:** not needed with `ardakilic_trackpad`. It sets GP15 to an input with the internal pull-down (`pointing_device_init_user()`), which keeps RDY low while the pad is unplugged. Only for other firmware that leaves the pin floating.

</details>

- **USB-C:** the receptacle's contacts are recessed and there are no magnets to collect debris, so the PTC matters less for shorts.
  - If you hot-plug, fit the PTC or a **10 Ω (0805) resistor** in the 3V3 wire, before the Schottky (Pico side). It slows the pad's power-up so plugging in cannot dip the Pico's rail ([USB-C hot-plug](#hot-plug-usb-c)).
  - The 100 Ω resistors still help.
  - The **Schottky itself is not optional.**
- **Where to put the parts:**
  - Over-plate route: in line in the wires, under the OLED cover.
  - Under-plate route (pogo dock only): on a small scrap of perfboard in the 4 mm gap. The pogo dock's plugs are hollow and open at the bottom, so taller parts can poke up into them.
- **Insulate everything:** the pocket floor carries live matrix nets.

### Hot-plug: magnetic pogo

USB-C mates GND first and has its own notes: [USB-C hot-plug](#hot-plug-usb-c).

- **Mechanically, plugging while powered is safe** with an N/S-keyed pair such as the MG005 / Adafruit 5413. It self-aligns, mates only one way round, breaks away under a pull, and is rated for 20,000 cycles.
- **A generic pair that mates either way round is not safe to plug live.** Reversed, it puts the keyboard's 3V3 on the pad's SCL, the shared SCL line on the pad's supply, and SDA on the pad's push-pull RDY output. Check that your pair repels when reversed, or plug it only with USB unplugged.
- **Electrically, a glitch is possible.** The five contacts touch in no fixed order, with no GND-first.
  - If SDA or SCL touches before GND/VDDHI, the bus is briefly dragged low.
  - That can corrupt one OLED transfer, or hang the shared bus for a moment.
  - The OLED heals itself: QMK clears its dirty flags only after a successful transfer. A permanently stuck bus is rare; re-plugging USB clears it.
- **QMK itself never retries a pad that was missing at boot.** After a re-plug the pad also comes back with factory settings.
  - The firmware in [`firmware/`](../firmware/) adds a **re-init** that detects the pad and reconfigures it about a second after it is plugged in.
  - Without that re-init, re-plug USB after connecting the pad.
- **Safest routine:** unplug USB, connect or disconnect the trackpad, plug USB back in.

## USB-C in depth

The short version is [wiring.md Step 2b](../wiring.md#step-2b-usb-c-dock) (the dock) and [Step 3](../wiring.md#step-3-rest-side-trackpad-pigtail), Part B (the grip). The diagram is [wiring-usbc.svg](wiring-usbc.svg). USB-C reuses the keyboard taps and wire route, and most of the rest-side steps.

### Why the female half goes in the keyboard

- **Two cheap breakout boards mate directly,** with no cable between them:
  - the blue **female** board (receptacle) sits in the USB-C dock (`stl/ithalat-dock-usbc.stl`). Its mouth is flush with the floor of a chamfered well in the dock face; a screwed-down retainer holds it;
  - the green **male** board (plug) sits in a printed grip (`stl/ithalat-usbc-grip-top.stl` and `stl/ithalat-usbc-grip-bottom.stl`) at the end of a short pigtail from the TPS65.
- **Only the four big pads** both boards already have are used. No fine-pitch soldering.
- **Female in the keyboard, male on the rest,** because:
  - the receptacle sits inside the dock, behind a printed shoulder, so the dock takes the plugging forces. A plug sticking out of the dock would act as a lever: every knock would wrench the keyboard-side board;
  - the rest is the part that moves, so it gets the part you hold: the male board in a grip you can pinch;
  - the well in front of the receptacle guides the grip's nose and takes side loads off the plug shell;
  - the female board is the larger one, and the dock has room for it. The rest's back strip, 9 mm deep in front of the trackpad pocket, does not.

#### Compared with the magnetic pogo

Full comparison: [README](../README.md#pick-your-connector).

| | USB-C |
|---|---|
| Plug in | a 5–20 N push: steady the keyboard |
| Unplug | an 8–20 N pull |
| Breakaway | none |
| RDY | none |
| Magnets near the pad | none |
| Mating order | GND first |

### USB-C signal mapping

| Pad | Signal (colour) | Keyboard side → female board | TPS65 pad |
|---|---|---|---|
| G | GND (black) | tap A GND or Pico pin 38 → G | GND (J1-3) |
| V | 3V3 (red) | tap A 3V3 or Pico pin 36 → **Schottky** (band toward the board) → V | VDDHI (J1-4), about 3.0–3.1 V |
| D+ | SDA (blue) | tap A SDA or Pico pin 4 (GP2) → D+ | SDA (J1-6) |
| D− | SCL (yellow) | tap A SCL or Pico pin 5 (GP3) → D− | SCL (J1-5) |
| none | RDY | not connected ([SBU mod](#rdy-over-sbu-advanced)) | RDY (J1-1): leave empty |
| none | NRST | none | NRST (J1-2): leave empty |

On the rest side, the male board's G, V, D+ and D− go to the same TPS65 pads.

- **These four pads are all the trackpad needs.** VBUS carries the supply, GND the ground, and the D+/D− pair the two I2C lines.
- **Either way up.** The female board joins both receptacle D+ contacts (A6, B6) and both D− contacts (A7, B7), so the plug works either way up. A few cheap boards wire only one pair; the [beep test](#beep-tests-usb-c) checks both orientations.
- **Female silk reads only "D, D"?** Mate the two bare boards and beep each female D pad against the male's labelled D+. The one that beeps is D+: mark it with a paint pen. What matters: the wire you call SDA on the keyboard meets the TPS65's SDA pad.
- **Why SDA and SCL go on D+ and D−:**
  - those pads are already broken out on both boards, and reversible on the female;
  - in the contact row they sit between CC and SBU, away from VBUS;
  - the boards mate directly, with no cable, so SDA and SCL share only a few millimetres of contacts. Crosstalk is negligible (about 0.3 pF).
- **Bus timing is unchanged.** The boards add less than 1 pF and less than 50 mΩ per line, so 400 kHz is fine.
- **Firmware:** identical to the pogo build. Leave `POINTING_DEVICE_MOTION_PIN` undefined (the default): there is no RDY wire.

### The series Schottky on 3V3

#### Why it is needed

- **It looks like a port.** The dock's socket looks exactly like a USB-C port. Sooner or later someone plugs a phone cable or charger into it.
- An A-to-C cable from a PC, or any simple USB charger, always puts 5 V on VBUS.
- Without the diode, that 5 V lands straight on the Pico's 3V3 rail. The RP2040 (3.63 V max), its flash, the OLED and the switchplate LEDs on that rail would likely die.
- With the diode, the 5 V is blocked: the diode is reverse-biased and the Pico never sees it.
- The pad still gets enough. The diode drops about 0.2–0.3 V at the pad's 2–4 mA, so VDDHI sits at about **3.0–3.1 V**. The TPS65 runs from 1.65 V to 3.6 V.

#### Which part

Any small Schottky:

| Part | Package | Notes |
|---|---|---|
| **1N5817** (20 V) or **1N5819** (40 V) | axial DO-41, about 5.2 × Ø2.7 mm | **recommended** |
| **SS14** | SMA | also recommended |
| **BAT54** (single) | SOT-23 | only together with the PTC |

- **1N5817 / 1N5819:** 1 A, about 0.2 V at 3 mA. The easiest to solder. Sleeve it with heat-shrink.
- **SS14:** 1 A, about 0.2 V. A small SMD part.
- **BAT54:** the single diode, not BAT54A, C or S (pairs with other pinouts). A 200 mA part dropping about 0.3 V. Use it only with the [PTC](#optional-protection-parts). Solder it onto a scrap of perfboard or dead-bug it.
- **No ordinary silicon diode** (1N4148, 1N4001). It drops about 0.7 V, which leaves the I2C lines further above the pad's supply than its rating allows.

<details><summary>Why the current rating matters</summary>

- The dock's V pad is live, at about 3.2 V, whenever the keyboard is on.
- A V–G short in the receptacle (a bent contact, debris), or a USB-C gadget plugged into the "port" that draws from VBUS, pulls the Pico regulator's current through the diode.
- A 1 A Schottky shrugs that off.
- A BAT54 can fail short. Then the 5 V protection is gone with no visible sign.
- Repeat the diode-mode check ([USB-C beep tests](#beep-tests-usb-c), step 1) after any short.

</details>

> [!WARNING]
> **Polarity:** the **anode** goes to the Pico's 3V3 (pin 36 or the tap-A 3V3 point). The **cathode**, the end with the band, goes to the female board's V pad. **The band goes toward the V pad.**

#### Where it goes

- **In the USB-C dock:** across the female board between the receptacle's legs and the pads, in a cradle under the retainer. Its centre sits about 10 mm behind the well floor.
- **Cradle size:** `USBC_DIODE`, sized for the DO-41 body (5.2 × Ø2.7 mm). For a SOT-23 BAT54, set `USBC_DIODE=(3.0, 1.4)`.
- Put Kapton tape on the board under it.
- **Does not fit?** The preview's Schottky dimension row says so. Then put it inline in the red wire under the OLED cover instead.
- **Either way:**
  - put it at the **keyboard end,** never on the rest. It protects the keyboard, because the keyboard half is the one that looks like a USB port;
  - sleeve both joints and the leads with heat-shrink;
  - inline under the OLED cover, keep it flat and as close to the tap as you can.

#### What it does not protect

There is no diode on the pad side. Plugging the rest's grip into a real USB port can still kill the TPS65 ([it is not USB](#it-is-not-usb-chargers-and-laptops)).

<details><summary>I2C levels with the diode</summary>

- The keyboard's pull-ups go to 3.3 V; the module's own 4.7 kΩ pull-ups go to VDDHI. So the bus idles between the two: at about VDDHI + Vf/2.
- That is only 0.1–0.15 V above the pad's ~3.05 V supply, well inside its "supply + 0.3 V" input rating.
- Without the module's pull-ups it would idle a full Vf (0.2–0.35 V) above VDDHI. That is why extra pull-ups go to the V pad, not to Pico 3V3 ([pull-ups](#pull-ups)).
- Any current into the pad stays at microamps (the IQS550 allows ±5 mA). No change is needed.
- A 1N5817 or SS14 (about 0.2 V) keeps the gap smaller than a BAT54 (about 0.3 V).

</details>

### Preparing the breakout boards

Do this before anything is soldered to the boards.

1. **Measure both boards** with calipers. Cheap boards vary by seller.
   - **Female:** board length, width and thickness; receptacle shell width, height and length; how far its mouth sticks out past the board's front edge.
   - **Male:** board length, width and thickness; plug shell width and height; insertion length (the exposed shell in front of the board, about 6.65 mm).
   - Each has a `USBC_*` constant in [`config.py`](../config.py), marked "measure your boards". Set them, regenerate, print, test-fit before you solder:
     - the female board sits against the dock's shoulder, receptacle mouth flush with the well floor;
     - the grip closes around the male board with only the crush ribs under the board resisting (the screws squeeze them).
2. **Remove the two CC resistors from the female board.**
   - **Why:** most 4-pad female boards carry two 5.1 kΩ resistors ("Rd"), one from each CC contact to GND. A laptop or USB-C charger reads them as "a phone is connected" and switches its 5 V on. Without them, a USB-C source never powers the dock. The diode would still block it: this is a second layer.
   - **Spot them:** usually the only two tiny resistors, next to the receptacle. Marked 512 (3-digit code) or 5101 (4-digit). Very small (0402) ones are often unmarked.
   - **Confirm with the meter,** board unpowered: each reads about 5.1 kΩ from a CC leg of the receptacle to the G pad.
   - **Remove them** with hot tweezers, two irons, or by heating one end and flicking the part off. Do not lift the pads.
   - **Check afterwards:** no resistance left between the CC legs and G (open).
3. **Remove any resistor from the male board.** Some carry a 56 kΩ (marked 563) from CC to VBUS, or a 5.1 kΩ (512 / 5101) from CC to GND. The 5.1 kΩ matters most: with it fitted, plugging the grip into a laptop or charger can make that port switch 5 V straight onto the trackpad.
4. **Check each board alone,** meter in continuity mode:
   - **female:** V–G, D–D, V–D and G–D must not beep. The shell usually beeps to G; if not, it floats, which is fine: do not bridge it;
   - **male:** V–G, D+–D−, V–D and G–D must not beep. The plug shell usually beeps to G (same rule if not).
5. **Label both halves** "NOT USB" once built.

### Dock and retainer, full steps

Start with the four wires (black GND, red 3V3, blue SDA, yellow SCL) at tap A or B, routed over the plate to the rear channel. No green RDY wire.

<details><summary>All seven dock steps</summary>

1. **Deburr and test-fit first.**
   - The well's bottom wall and the window floor print as bridges: scrape off any sag or strings.
   - Measure the OLED cover: the dock needs its underside about 9.2 mm above the plate (a 3 mm cover on M2x10 standoffs, its top 24 mm above the keyboard's underside). Then its front-edge position does not matter.
   - Seat the bare female board. It drops in from the top, receptacle first into the U-slot window in the front shoulder, where two vertical crush ribs grip the shell sides, until the board's front edge rests against the shoulder and the board lies on its rim.
   - The receptacle mouth must sit flush with the well floor. Proud or recessed: fix the `USBC_*` board constants and reprint. A recessed mouth shortens how far the plug goes in, and the contacts become unreliable.
2. **Fit the diode.**
   - Heat-shrink over the red wire.
   - Solder the **anode** (plain end) to the red wire.
   - The cathode (band) goes to the V pad: its own lead if it reaches, or a short red jumper.
   - Shrink both joints.
   - Keep the leads short, so the body lies across the board between the receptacle's legs and the pads, where the retainer's cradle covers it.
   - Does not fit the cradle? Put it inline in the red wire under the OLED cover now.
3. **Solder the female board.**
   - First check every receptacle shell leg is soldered (cheap boards sometimes skip the rear pair): the unplug pull goes through them into the board and the shoulder.
   - Slide 1.5 mm heat-shrink onto each wire.
   - black → G, red (from the cathode) → V, blue → D+, yellow → D−.
   - Silk only "D, D": use the pad you identified as D+ for blue.
   - Keep the joints low and flat: the board sits close to the dock walls.
4. **Beep the keyboard half** ([USB-C beep tests](#beep-tests-usb-c), step 1) before you close anything.
5. **Capture the board.** Press it in from the top, receptacle first through the window in the front shoulder, so the mouth meets the well floor.
   - The board's front edge bears on the 1.5 mm shoulder, its rear edge on the 1.25 mm rear stop.
   - Lead the four wires out through the rear channel.
   - Glue alone or crush ribs are not enough. Unplugging pulls on the receptacle with up to 20 N; only the shoulder, a mechanical stop, keeps that force off the solder joints. The retainer holds the board down (step 7).
6. **Clip the dock in,** as for the pogo dock. Press both plugs into the cut-outs until the clips snap under the plate. Check it sits flat and no wire is pinched.
7. **Fit the retainer** (`stl/ithalat-usbc-retainer.stl`). Press it in from the top until flush with the dock top. Drive its two M2x4 self-tapping screws through the arms into the dock.
   - It holds the board down by its rim, presses the receptacle shell onto the board with three small ribs, closes the window over the receptacle and covers the diode.
   - Its two prongs slide into the gaps behind the back clip blades, so the blades cannot flex: that locks the dock.
   - The USB-C dock also has flatter catch faces (30° from horizontal, not 45°), so its clips hold harder. A 20 N pull a few millimetres above the plate would pop the pogo dock's 45° clips; the 30° catches alone hold it with a margin of 1.65.
   - **To take the dock out:** undo the two screws, lever the retainer up at the two pry notches at its arm ends, then pull the dock straight up (about 24 N).

</details>

### Grip, full steps

First do rest-side steps 1–5 with four wires (no green RDY). Then these, in this order: bonding the glass last keeps flux and epoxy off it.

<details><summary>All eight grip steps</summary>

1. **Plan the slack.** On unplugging, the grip moves 10.65 mm back before the plug clears the well (6.2 mm seated depth + the 4.45 mm well), so its wires need a slack loop.
   - They leave through the grip's underside, straight above the rest's notch and riser. The slack folds into the plug bay in an S.
   - Slack loop: 12 mm (`USBC_WIRE_SLACK`; verify checks it covers the 10.65 mm). Loose length, sleeve end → male board: 27 mm (15 mm of route + 12 mm of slack).
2. **Cut to length.** Rest 1.5 mm in front of the keyboard, USB-C dock fitted. Hold the bare male board plugged into the dock. Lead each wire up out of the notch to its pad with the slack loop in place, add about 3 mm for the joint, cut. Unplug.
3. **Prepare the wires.**
   - Nothing has to be threaded through the grip first: the wires drop into the open lower half when you close it.
   - **Do not sleeve the four wires** where the grip holds them. Its clamp pinches the bare 28 AWG silicone wires side by side (a 0.8 mm slot for 0.9 mm wires).
   - Slide 1.5 mm heat-shrink onto each wire for the pad joints.
4. **Solder the male board.**
   - black → G, red → V, blue → D+, yellow → D−.
   - Solder each wire on the **front half** of its pad (nearer the plug). Lay it back over the rear half toward the middle.
   - Why: the wires fan in from the pad row to the grip's wire band, and the board's rear edge sits only 0.1 mm from the push rib.
   - Shrink each joint.
5. **Close the grip.**
   - **Beep both ways up first.** Plug the bare, soldered board into the dock both ways up and beep end to end each way ([USB-C beep tests](#beep-tests-usb-c), step 3). The grip goes in only one way up, so this is the only chance to catch a female board that wires only one D pair.
   - **Mix a little 2-part epoxy** (5-minute is fine; CA bonds poorly to PETG and is no substitute).
     - Fill the key groove around the plug shell inside the nose of the bottom half.
     - Run a bead where the shell meets the board, top and bottom.
     - Keep epoxy off the exposed shell and out of its mouth.
     - Cured, it locks the shell to the grip, so the unplug pull goes from the grip straight into the shell, not through the board or a joint.
   - **Lay the board in the bottom half,** pads up.
     - The shell goes into the nose cavity, through the tight collar at its rear.
     - The board lies on its two pairs of crush ribs, and its rear edge sits against the push rib.
     - The shell sticks out of the nose by 6.5 mm.
   - **Lead the four wires** side by side over the push rib (the band there is as wide as the pad row).
     - Then down the 0.8 mm slot behind it, which narrows to 4.2 mm. They leave through the grip's underside.
     - A pull on the wires must stop at this clamp, never at the pads.
   - **Put the top half on** the two pegs.
     - Drive the two M2x4 self-tapping pan-head screws in from below until the heads sit in their counterbores.
     - The screws crush the ribs under the board's edge strips, which clamps the board even if your slicer rounds the faces by a layer.
     - Let the epoxy cure before the first plug-in.
6. **Beep end to end** once more with the grip closed.
7. **Bond the glass and seat the module** (rest-side steps 7 and 8).
8. **Plug in.** The plugged grip must float clear of the rest top, by about 1.6 mm. If it touches the rest, or its wires pull it down, re-dress the slack loop.

</details>

### Plugging and unplugging USB-C

USB-C needs a real push and a real pull. The keyboard slides on its feet at only a few newtons, so your free hand steadies it. Nothing breaks away.

**To plug in**

1. Hold the **grip** by its finger ridges, between thumb and index finger. Never hold the wires.
2. Steady the keyboard with your other hand: palm on the keycaps of the left half, or fingertips hooked behind the keycaps next to the dock.
3. Line the grip's nose up with the well. The chamfer catches it within about ±1 mm.
4. Push **straight in** along the connector axis until it seats: about 10.5 mm of travel from the well's mouth, the last 6.2 mm into the receptacle, 5–20 N. Do not rock it or push at an angle.

**To unplug**

1. Brace a fingertip on the finger-brace flats: the 11 mm wide strips of flat dock face left and right of the well's chamfer.
2. With the same hand, pinch the grip between thumb and index finger and pull **straight back**. The force stays inside your hand, so neither the keyboard nor the dock clips take it.
3. Never pull the wires. Never lever the grip up, down or sideways.

**Rules**

- **Always unplug before you move or lift the rest.** No breakaway: pulling the rest away drags the keyboard along, or yanks the grip out against the dock clips.
- **Plug straight in,** never at an angle.
- **Unplugged grip:** let it rest on the back edge of the rest. No harm: the pad is off.

### It is not USB: chargers and laptops

After the changes, neither half is a USB port. **Label both:** a small sticker or paint-pen text **NOT USB** on the dock's top face and on the grip.

| Plugged in | Result |
|---|---|
| Simple USB charger, A-to-C cable, into the dock | Diode blocks 5 V. OLED and pad stop. No damage. |
| PC or laptop, A-to-C cable, into the dock | Diode blocks 5 V. Bus misbehaves. No damage expected. |
| Laptop, phone or USB-C charger, C-to-C, into the dock | Source sees nothing, keeps 5 V off. |
| Fast charger (QC and similar) into the dock | Stays at 5 V; the diode blocks it. |
| A USB-C gadget (light, fan, drive) into the dock | May draw from 3V3 through the diode. Keyboard may brown out. |
| **The rest's grip** into a laptop, phone or charger | **Not protected.** Can kill the TPS65. |

<details><summary>What happens in each case</summary>

- **Simple charger into the dock:** the diode blocks the 5 V. Most simple chargers also short D+ to D−, which shorts SDA to SCL. The OLED freezes and the pad stops while the charger is in. Nothing is damaged. Unplug it; if the OLED stays frozen, re-plug the keyboard's USB.
- **PC or laptop via A-to-C into the dock:** the diode blocks the 5 V. The host's D+/D− lines meet the I2C lines, so the bus misbehaves while it is plugged in. No damage is expected.
- **USB-C source via C-to-C into the dock:** the female's 5.1 kΩ resistors are gone, so the source sees nothing and keeps its 5 V off. If they were still fitted, it would switch 5 V on, and the diode would block it.
- **Fast charger into the dock:** the idle I2C lines never send the handshake that raises the voltage. It stays at 5 V, which the diode blocks.
- **USB-C gadget into the dock:** it may draw from the keyboard's 3V3 through the diode, because the dock's V pad is live. Nothing is damaged with a 1 A Schottky (1N5817, SS14); the keyboard may brown out. Unplug it.
- **The grip into a laptop, phone or charger:** there is no diode on the pad side.
  - A proper USB-C port keeps its 5 V off, as long as the male board's 5.1 kΩ resistor is removed.
  - An old always-on port, or a C-to-A adapter on a charger, puts 5 V straight on the TPS65 (3.6 V max) and kills it.
  - Never plug the grip into anything but the dock.

</details>

- **The well helps a little.** It is deeper and narrower than most USB-C cable plugs' moulded bodies, so many real cables cannot reach the contacts. The well is 11.64 × 5.95 mm and 4.45 mm deep; slim overmoulds still fit. Do not rely on it.

### Hot-plug: USB-C

- **USB-C mates in a fixed order.** The receptacle's GND and VBUS contacts touch first, the signal contacts second. On removal the signals break first. Grounded shells touch even earlier.
- **So SDA and SCL never reach the pad before its ground and supply.** Better than the pogo pair, whose contacts meet in no fixed order.
- **Plugging the pad in while the keyboard is on is fine.** The firmware's re-init finds the pad within about 1–1.5 s ([timing](../firmware/README.md#hot-plug-behaviour-and-limits)).
- **QMK itself never retries a pad that was missing at boot.** The firmware in [`firmware/`](../firmware/) adds that, as for the pogo.

> [!TIP]
> **If you hot-plug, fit a 10 Ω (0805) resistor in the 3V3 wire, before the Schottky, or the [PTC](#optional-protection-parts).**

<details><summary>Why: inrush</summary>

- With only the diode in the way, the pad's decoupling capacitors charge from the Pico's 3V3 within microseconds of VBUS mating.
- That can dip the Pico's rail by a few tenths of a volt, toward the flash chip's 2.7 V minimum. It can glitch the OLED or, rarely, reset the keyboard.
- The pad's controller also wants its supply to rise no faster than about 20 µs per volt for a clean power-on reset. NRST is not wired, so a bad start can only be cleared by re-plugging.
- The 10 Ω resistor drops about 40 mV at 4 mA and, with the module's ~4.7 µF, slows the rise to roughly 50 µs per volt.

</details>

### RDY over SBU (advanced)

> [!NOTE]
> **Not recommended.**
>
> - **Not needed:** the firmware runs fine without RDY. It times its reads to the pad's report window. RDY would only avoid clock-stretching waits on the shared bus.
> - **Hard to do:** the mod needs fine-pitch soldering on a part you pull at up to 20 N.
> - **Firmware:** leave `POINTING_DEVICE_MOTION_PIN` undefined unless you do it.

- **Use an SBU contact for RDY.** Leave both CC contacts open on both halves.
- **Why not CC:** it would work electrically, but with RDY on CC an unpowered TPS65 can look like a phone to a laptop. If the grip were plugged into one, the laptop might switch its 5 V on.

1. **Remove every CC resistor** on both boards ([board prep](#preparing-the-breakout-boards)), so CC stays open.
2. **Female:** bridge SBU1 (A8) and SBU2 (B8) with a short insulated wire, so RDY works in both orientations. Solder a green wire to the bridge.
3. **Male:** solder a fine wire to the SBU tail (A8) in the plug's top row.
   - Counting from either end of the row hits A5 (CC) or A8 (SBU): confirm it with the meter against the female's bridged SBU pads.
   - The tails are 0.5 mm apart. Afterwards, check that A8 does not beep to A7 (D−) or A9 (VBUS).
4. **Fit a 2.2 kΩ resistor in series at each end:** female side → Pico pin 20 (GP15), male side → TPS65 RDY pad. SBU sits next to VBUS in the contact row, and a twist or debris can short them. The resistors keep that harmless.
5. **Define `POINTING_DEVICE_MOTION_PIN GP15`** in the firmware ([`firmware/README.md`](../firmware/README.md)).
6. **Beep-test RDY end to end** in both orientations. Check it does not beep to V or G.

## Tests in depth

The short checklists are in [wiring.md Step 4](../wiring.md#step-4-test-before-power-up).

### Beep tests: magnetic pogo

Before power, USB unplugged.

1. **Keyboard half, pad by pad:** pad 1 ↔ Pico pin 4 · pad 2 ↔ pin 36 · pad 3 ↔ pin 38 · pad 4 ↔ pin 5 · pad 5 ↔ pin 20 (if wired). Each pair beeps.
2. **No shorts between neighbours:** 1–2, 2–3, 3–4 and 4–5 must *not* beep.
   - Between 3V3 and GND (2–3) the meter may show a rising value as it charges the decoupling capacitors. Normal. A steady reading near 0 Ω is a short.
3. **Rest half:** each spring pin ↔ its TPS65 pad; NRST connected to nothing; no shorts between neighbours.
4. **Mated, end to end:** Pico pin 4 ↔ TPS65 SDA pad, pin 36 ↔ VDDHI, pin 38 ↔ GND, pin 5 ↔ SCL, pin 20 ↔ RDY.
   - A mirror-image half shows up here as SDA↔RDY and 3V3↔SCL.
   - **Do not power up until this passes.** A reversed or mirrored half puts 3V3 on the pad's SCL and the shared SCL line on its supply. The pad's inputs are rated for no more than its supply + 0.3 V, and the OLED's bus stops working too.
5. **Measure the pull-ups** ([pull-ups](#pull-ups)).

### Beep tests: USB-C

Before power, USB unplugged.

1. **Keyboard half** (female board in the dock, wired to the tap):
   - G pad ↔ Pico pin 38: beeps.
   - D+ pad ↔ Pico pin 4 (SDA): beeps. D− pad ↔ pin 5 (SCL): beeps.
   - **Diode,** meter in diode mode: red probe on Pico pin 36, black on the V pad: about 0.15–0.35 V. Swapped: open (OL).
     - Beeps both ways: the diode is shorted or bypassed.
     - Open both ways: a joint is broken.
     - Forward value only with the probes swapped: the diode is in backwards.
     - Repeat after any short at the dock or the grip: a diode that failed short beeps both ways and no longer blocks 5 V.
   - No shorts: G–V, G–D+, G–D−, V–D+, V–D− and D+–D− must not beep.
   - Shell ↔ G: usually beeps. If not, the shell floats, which is fine: do not bridge it.
2. **Rest half** (male board soldered, grip still open if possible):
   - male G ↔ TPS65 GND, V ↔ VDDHI, D+ ↔ SDA, D− ↔ SCL: each beeps.
   - TPS65 NRST and RDY connected to nothing.
   - No shorts between the four pads. V–G may show a value that rises as the meter charges the module's capacitor; a steady reading near 0 Ω is a short.
   - Plug shell ↔ G: usually beeps; if not, it floats, which is fine.
3. **Mated, end to end, both orientations.** The grip fits the well only one way up, so do the two-way check with the bare, soldered male board before you close the grip: plug in and check, pull out, turn over, plug in and check again. After closing the grip, check once more.
   - Pico pin 4 ↔ TPS65 SDA, pin 5 ↔ SCL, pin 38 ↔ GND: each beeps.
   - Diode mode, red on Pico pin 36, black on TPS65 VDDHI: about 0.15–0.35 V.
   - SDA–SCL, SDA–GND, SCL–GND, VDDHI–SDA and VDDHI–SCL: no beep.
   - SDA or SCL works only one way up? The female board wires only one D pair. If the working way is the way the grip holds the board (pads up), carry on. Otherwise replace the female board.
4. **Do not power up until step 3 passes.**

### First power-up

Both connectors. With USB-C, the grip is plugged in.

1. Flash the trackpad firmware ([`firmware/`](../firmware/)).
2. **Connect the trackpad first, then plug in USB.**
3. The OLED must come up exactly as before.
4. Measure **VDDHI–GND at the TPS65 pads.** Never above 3.6 V.
   - Magnetic pogo: **3.2–3.4 V**.
   - USB-C: **about 3.0–3.1 V** (2.9–3.25 V is fine), because of the Schottky. It reads higher while the pad idles. If it equals the Pico's 3V3 exactly, the diode is shorted or bypassed: fix that before you rely on the 5 V protection.
   - Nothing should get warm.
5. **Gestures:**
   - one finger moves the cursor;
   - a tap is a left click;
   - a two-finger tap is a right click;
   - a two-finger drag scrolls;
   - press and hold: rest a finger for about 0.5 s, then move. That drags with the left button held until you lift (`AZOTEQ_IQS5XX_PRESS_AND_HOLD_ENABLE`, on by default).
6. **Drift check with the plug docked** (magnetic pogo). The plug's two magnets sit about 7 mm from the module (verify's `plug magnets -> TPS65 outline` WARN), closer than the 15 mm keep-out for loose metal (`TP_METAL_KEEPOUT`).
   - Leave the pad untouched for 30 s: the cursor must not creep.
   - Slide a finger slowly along the back edge (nearest the plug), then the front edge: both must track equally smoothly.
   - Drift or jitter near the back: re-plug the pad so it recalibrates at power-up. Still there: raise `TP_BACK_MARGIN` to move the pad away from the plug.
   - USB-C has no magnets. Its plug shell is about 13 mm from the module, the male board's copper pads about 5.5 mm. The same quick check does no harm.
7. **Wrong axis directions** are fixed in firmware (`AZOTEQ_IQS5XX_ROTATION_90/180/270`), not with wiring.

### QMK console

1. Build with `CONSOLE_ENABLE = yes` and `#define POINTING_DEVICE_DEBUG`.
2. Watch with QMK Toolbox's console, or `qmk console` from a native QMK install. Docker Desktop on macOS cannot see USB HID devices.
3. What the messages mean:
   - A steady stream of `IQS5XX - get report failed`: the pad is NACKing. Check power, wiring and pull-ups.
   - No messages and no movement usually means init failed at boot, so the pad is never polled. Re-plug USB with the pad connected, or rely on the firmware's re-init.
4. **Tap-latch check.** On QMK 0.34.0 and later, tap once in a text editor. If text selection then follows the cursor, the button is latched. The firmware notes describe the fix ([firmware/README.md, Tap-latch finding](../firmware/README.md#tap-latch-finding-qmk--0340)).

### I2C scan sketch

A keymap helper. Bind it to a spare key, or call it once from `keyboard_post_init_user()` after a short delay. You should see **0x3C** (OLED) and **0x74** (TPS65).

<details><summary>The sketch (not compiled)</summary>

```c
// Sketch, not compiled. Needs CONSOLE_ENABLE = yes.
#include "i2c_master.h"
#include "print.h"

static bool i2c_present(uint8_t addr7) {
    if (i2c_ping_address(addr7 << 1, 10) == I2C_STATUS_SUCCESS) return true;
    wait_us(200);                        // the IQS5xx may NACK the first address while waking
    return i2c_ping_address(addr7 << 1, 10) == I2C_STATUS_SUCCESS;
}

void i2c_scan(void) {
    for (uint8_t a = 0x08; a <= 0x77; a++) {
        if (i2c_present(a)) uprintf("I2C: device at 0x%02X\n", a);
    }
}
```

</details>

- **A miss for 0x74 is not conclusive.** QMK's `i2c_ping_address` reads an 8-bit register; the IQS5xx uses 16-bit registers and clock stretching. Confirm with a real read, which the driver's init already does.
- **Hot-plug test.** With the pad running, unplug it and plug it back in while powered. The cursor should work again within about 1–2 s (if the firmware's re-init is present; [timing](../firmware/README.md#hot-plug-behaviour-and-limits)). The OLED may flicker once.

## Other connectors

### JST-SH 4-pin, Qwiic or STEMMA QT

- **Pinout:** 1 GND (black) · 2 3V3 (red) · 3 SDA (blue) · 4 SCL (yellow). Same colours as above.
- **What to change:**
  - Build with `--connector jst_sh4` (or the old `DOCK_CONN_TYPE = 'jst_sh4'`). That writes `stl/ithalat-dock-jst.stl`.
  - Use a side-entry SM04B-SRSS-TB header on a small adapter in the dock.
  - Connect it to the TPS65 pads with an off-the-shelf Qwiic/STEMMA QT cable (50–200 mm). You can cut the cable and solder its free end to the pads.
- **Pros:** cheap, standard, easy to buy.
- **Cons:**
  - no published mating-cycle rating: treat it as tens of cycles;
  - the plug is small and fiddly;
  - it does not break away: a yank pulls on 28–32 AWG crimps;
  - no RDY. A JST-SH 6-pin works, but you would have to define and document your own pinout.
- **Plug and unplug only with USB disconnected.**

### Why not TRRS

TRRS is the 3.5 mm jack.

- **The contacts slide across each other** on insertion, so 3V3, GND and the signals short against each other for a moment.
- **QMK's split-keyboard docs** call TRRS "not hot pluggable".
- **Only 4 contacts:** no room for RDY.

### How USB-C answers the old objections

Earlier versions of this guide advised against USB-C. It is now a supported variant, because each objection has an answer:

- **"A real USB cable or charger puts 5 V on a 3.3 V-only bus."** The series Schottky at the keyboard end blocks it. The CC resistors are removed, so USB-C sources keep their 5 V off. Both halves are labelled. The pad side stays unprotected: never plug the grip into anything but the dock.
- **"C-to-C cables pair D+ and D− as one twisted pair, which maximises crosstalk."** There is no cable. The boards mate directly, so SDA and SCL share only a few millimetres of contacts (about 0.3 pF).
- **"QMK warns against USB connectors for non-USB links."** That warning is about mix-ups. The diode and the labels deal with them.

## ASCII diagrams

Text versions of [wiring.svg](wiring.svg) and [wiring-usbc.svg](wiring-usbc.svg).

### Magnetic pogo diagram

<details><summary>Show the diagram</summary>

```
 YAKAMOZ (keyboard)
 ──────────────────────────────────────────────────────────────────────────────────────────

                          3V3      3V3       OLED 0x3C (switchplate OL2,
                           │        │        via J2 <-> TB1, same nets)
                       [R1 4.7k][R2 4.7k]      SDA SCL 3V3 GND
                           │        │           │   │   │   │      tap A (switchplate)
 Pico pin 4  GP2  SDA ─────●────────┼───────────●───┼───┼───┼───── OLED/TB1 SDA ────┐
 Pico pin 5  GP3  SCL ──────────────●───────────────●───┼───┼───── OLED/TB1 SCL ────┼─┐
 Pico pin 36 3V3(OUT) ──────────────────────────────────●───┼───── OLED/TB1 3V3 ────┼─┼─┐
 Pico pin 38 GND      ──────────────────────────────────────●───── OLED/TB1 GND ────┼─┼─┼─┐
                                                                                    │ │ │ │    4-5 x 30 AWG silicone,
 Pico pin 20 GP15 RDY (optional, solder at the Pico)  ──────────────────────────────┼─┼─┼─┼─┐  flat over the switchplate,
                                                                                    │ │ │ │ │  under the OLED cover, into
                                                                                    │ │ │ │ │  the dock's rear channel
                                                                                    │ │ │ │ │  (no case modification)
                              ┌── DOCK (replaces SW44 + SW43) ──────────────┐       │ │ │ │ │
                              │  receptacle (flat-pad half), pressed in     │       │ │ │ │ │
                              │                                             │       │ │ │ │ │
                              │  pad 1  SDA  blue                           ├───────┘ │ │ │ │
                              │  pad 2  3V3  red                            ├─────────┼─┘ │ │
                              │  pad 3  GND  black                          ├─────────┼───┘ │
                              │  pad 4  SCL  yellow                         ├─────────┘     │
                              │  pad 5  RDY  green (optional)               ├───────────────┘
                              │                                             │
                              └──────────────────────┬──────────────────────┘
                                                 N ║║║║║ S   magnetic, keyed (N <-> S), 20k cycles
                                                 S ║║║║║ N
                               plug = spring-pin half, pins 1..5 = SDA 3V3 GND SCL RDY
                                                   │││││   short pigtail, 5 x 28 AWG (≈ 52 mm route)
                                                   │││││   plug bay -> riser -> tunnel -> S-groove
                                                   ▼▼▼▼▼
 ITHALAT (wrist rest)
 ──────────────────────────────────────────────────────────────────────────────────────────
              ┌─ TPS65, back view: connector edge up (faces the keyboard when mounted) ─────┐
              │         RDY   NRST   GND    VDDHI   SCL     SDA     (2.0 mm pitch)          │
              │         green  NC    black  red     yellow  blue                            │
              │                 [ J1 ZIF, unused ]                                          │
              │   IQS550 @ 0x74 (QMK 0xE8), likely 4.7k pull-ups on the module              │
              │                                                                             │
              └─────────────────────────────────────────────────────────────────────────────┘

 ● = junction   ┼ = crossing (no connection)
 Taps:  A = OLED header joints or switchplate TB1 / OL1 · B = the same four wires straight from
        Pico pins 4/5/36/38 · alternative (modifies the case) = main-PCB OL1, under the plate
 Rules: 3.3 V only (never VBUS/VSYS) · NRST unconnected · effective pull-up ≈ 2.35 kΩ
        safest hot-plug = with USB unplugged · 4-wire minimum = drop RDY, all else identical
```

</details>

### USB-C diagram

<details><summary>Show the diagram</summary>

```
 YAKAMOZ (keyboard)
 ──────────────────────────────────────────────────────────────────────────────────────────

                          3V3      3V3       OLED 0x3C (switchplate OL2,
                           │        │        via J2 <-> TB1, same nets)
                       [R1 4.7k][R2 4.7k]      SDA SCL 3V3 GND
                           │        │           │   │   │   │      tap A (switchplate)
 Pico pin 4  GP2  SDA ─────●────────┼───────────●───┼───┼───┼───── OLED/TB1 SDA ────┐
 Pico pin 5  GP3  SCL ──────────────●───────────────●───┼───┼───── OLED/TB1 SCL ────┼─┐
 Pico pin 36 3V3(OUT) ──────────────────────────────────●───┼───── OLED/TB1 3V3 ────┼─┼─┐
 Pico pin 38 GND      ──────────────────────────────────────●───── OLED/TB1 GND ────┼─┼─┼─┐
                                                                                    │ │ │ │    4 x 30 AWG silicone,
 Pico pin 20 GP15: not used (no RDY on USB-C)                                       │ │ │ │    flat over the switchplate,
                                                                                    │ │ │ │    under the OLED cover, into
                                                                                    │ │ │ │    the dock's rear channel
                              ┌── USB-C DOCK (replaces SW44 + SW43) ────────┐       │ │ │ │
                              │  female breakout (blue), both Rd removed    │       │ │ │ │
                              │                                             │       │ │ │ │
                              │  D+  SDA  blue    ◄─────────────────────────├───────┘ │ │ │
                              │  V   3V3  red     ◄──┤◄── Schottky ◄────────├─────────┼─┘ │
                              │  G   GND  black   ◄─────────────────────────├─────────┼───┘
                              │  D−  SCL  yellow  ◄─────────────────────────├─────────┘
                              │      shell = GND (on most boards)           │
                              │  receptacle mouth flush with the floor of   │
                              │  a chamfered well in the dock face          │
                              └──────────────────────┬──────────────────────┘
                                                ┌────┴────┐   GND and VBUS mate first, signals second
                                                │  USB-C  │   push 5-20 N in, pull 8-20 N out, no breakaway
                                                └────┬────┘
                               male breakout (green): shell epoxied in the grip, wires clamped
                               pads  V = 3V3 · D− = SCL · D+ = SDA · G = GND
                                                    ││││   short lead, 4 x 28 AWG, slack loop in the plug bay
                                                    ││││   riser -> tunnel -> S-groove
                                                    ▼▼▼▼
 ITHALAT (wrist rest)
 ──────────────────────────────────────────────────────────────────────────────────────────
              ┌─ TPS65, back view: connector edge up (faces the keyboard when mounted) ─────┐
              │         RDY   NRST   GND    VDDHI   SCL     SDA     (2.0 mm pitch)          │
              │         NC    NC     black  red     yellow  blue                            │
              │                 [ J1 ZIF, unused ]                                          │
              │   IQS550 @ 0x74 (QMK 0xE8), VDDHI ≈ 3.0-3.1 V after the Schottky            │
              │                                                                             │
              └─────────────────────────────────────────────────────────────────────────────┘

 ● = junction   ┼ = crossing (no connection)   ┤◄ = Schottky: anode toward Pico 3V3, band toward V
 Rules: NOT USB, label both halves · Rd removed on the female, any CC resistor removed on the male
        no RDY: leave POINTING_DEVICE_MOTION_PIN undefined · beep-test both plug orientations
        hold the grip, never the wires · steady the keyboard to plug in · unplug before moving
```

</details>

## Old section numbers

wiring.md used to be one long file with numbered sections. Here is where each one went.

| Old section | Now |
|---|---|
| Wiring at a glance, How to use this guide | [wiring.md TL;DR](../wiring.md#tldr), [The wires](../wiring.md#the-wires) |
| Conventions | [Conventions](#conventions) |
| §1 Overview | [How the link works](#how-the-link-works) |
| §2 Signal table | [wiring.md The wires](../wiring.md#the-wires), [Full signal table](#full-signal-table) |
| §3 Keyboard side, §3.1–3.4 | [wiring.md Step 1](../wiring.md#step-1-keyboard-side-both-connectors), [Keyboard side in depth](#keyboard-side-in-depth) |
| §3.3 Where wires can (and cannot) run | [Where wires can and cannot run](#where-wires-can-and-cannot-run) |
| §3.4 alternative: main-PCB OL1 | [Under-plate alternative](#under-plate-alternative-modifies-the-case) |
| §3.5 Magnetic pogo receptacle and dock | [wiring.md Step 2a](../wiring.md#step-2a-magnetic-pogo-dock), [Pogo receptacle notes](#pogo-receptacle-notes) |
| §4 Wrist-rest side | [wiring.md Step 3](../wiring.md#step-3-rest-side-trackpad-pigtail), [Rest side in depth](#rest-side-in-depth) |
| §5 Electrical notes | [Electrical notes](#electrical-notes) |
| §5 Hot-plug | [Hot-plug: magnetic pogo](#hot-plug-magnetic-pogo) |
| §6 Test procedure | [wiring.md Step 4](../wiring.md#step-4-test-before-power-up), [Tests in depth](#tests-in-depth) |
| §7 USB-C variant, §7.1–7.3 | [wiring.md Step 2b](../wiring.md#step-2b-usb-c-dock), [USB-C in depth](#usb-c-in-depth) |
| §7.4 Prepare the breakout boards | [Preparing the breakout boards](#preparing-the-breakout-boards) |
| §7.5 Keyboard side: diode, female board, dock | [Dock and retainer, full steps](#dock-and-retainer-full-steps) |
| §7.6 Rest side: male board in the grip | [wiring.md Step 3](../wiring.md#step-3-rest-side-trackpad-pigtail) (Part B), [Grip, full steps](#grip-full-steps) |
| §7.7 Test procedure (USB-C) | [Beep tests: USB-C](#beep-tests-usb-c) |
| §7.8 Plugging and unplugging | [wiring.md Plugging](../wiring.md#plugging-and-unplugging), [USB-C detail](#plugging-and-unplugging-usb-c) |
| §7.9 It is not USB | [It is not USB](#it-is-not-usb-chargers-and-laptops) |
| §7.10 Hot-plug (USB-C) | [Hot-plug: USB-C](#hot-plug-usb-c) |
| §7.11 RDY over SBU | [RDY over SBU](#rdy-over-sbu-advanced) |
| §8 Other connectors | [Other connectors](#other-connectors) |
| Example parts and where to buy | [where-to-buy.md](where-to-buy.md) (same sub-headings) |
| §9 ASCII diagrams | [ASCII diagrams](#ascii-diagrams) |
