# ithalat bill of materials

Everything you buy, print and use to build the *ithalat* rest and its trackpad link to the [Yakamoz](https://github.com/ozkan/Yakamoz) keyboard.

Wiring steps are in [wiring.md](../wiring.md). Every dimension comes from [`config.py`](../config.py).

## TL;DR

- **Pick one connector:** magnetic pogo ([2a](#2a-magnetic-pogo-connector)) or USB-C ([2b](#2b-usb-c-connector)). Everything else is shared. [Pick your connector](../README.md#pick-your-connector) compares them.
- **Magnetic pogo: ≈ €40–50** plus the glass (€6.90). You need an N/S-keyed 5-pin magnetic pair (Adafruit 5413, US$6.95, or [cheaper](#7-cheaper-magnetic-options)).
- **USB-C: ≈ €35–45** plus the glass (€6.90). You need two small 4-pad breakout boards, a Schottky diode (required), 4 M2 screws and epoxy.
- **Shared parts:** TPS65 trackpad (€12), silicone wire, heat-shrink, Kapton, 6 bumpers and filament. Optional: glass, steel ballast, protection parts, a pin header for the TB1 socket tap.
- **Optional soft top:** about 29 g of non-conductive TPU 95A–98A for the insert. That is ≈ 30–38 TL of a 988–1,096 TL spool in Turkey ([§4](#4-mechanical-parts)).
- **Optional thin soft top:** the thin insert needs about 23 g (≈ 24–31 TL). It is the cheaper one to reprint and replace.
- **Prices** are rough late-2026 retail, without shipping. Check listings before you order.

**Jump to**

- [Shopping checklists](#shopping-checklists)
- [About the prices](#about-the-prices)
- [1. Trackpad](#1-trackpad)
- [2a. Magnetic pogo connector](#2a-magnetic-pogo-connector) · [2b. USB-C connector](#2b-usb-c-connector) · [2c. Wire and consumables](#2c-wire-sleeve-and-consumables-both-connectors)
- [3. Optional protection parts](#3-optional-protection-parts-keyboard-side-at-the-dock)
- [4. Mechanical parts](#4-mechanical-parts) · [TPU filament (soft top)](#tpu-filament-soft-top-only) · [5. Tools](#5-tools-and-consumables-not-in-the-cost)
- [6. Cost summary](#6-cost-summary-approximate)
- [7. Cheaper magnetic options](#7-cheaper-magnetic-options)

## Shopping checklists

Tick off what you have. Details for each part are in the sections below.

### Both connectors

- [ ] 1 × **TPS65 trackpad module** (keycapsss KC10195_65, variant "TPS65") – [§1](#1-trackpad)
- [ ] 1 × **glass overlay** for the `glass` variant, *or* a thin touch film for `bare` – [§1](#1-trackpad)
- [ ] ~1 m **silicone wire**, 30 AWG and 28 AWG, 4–5 colours – [§2c](#2c-wire-sleeve-and-consumables-both-connectors)
- [ ] ~5 cm **braided PET sleeve**, 3 mm (or 3–4 mm heat-shrink)
- [ ] **Heat-shrink** assortment, Kapton tape, hot glue or neutral-cure silicone
- [ ] 6 × **silicone bumpers**, Ø10 mm, your keyboard's bumper height + 0.6 mm – [§4](#4-mechanical-parts)
- [ ] **Filament**, PLA or PETG, non-conductive
- [ ] Optional: 2 × **steel bars**, 78 × 20 × 5 mm (ballast)
- [ ] Optional: thin double-sided tape, ≤ 0.1 mm
- [ ] Optional, soft top only: **TPU filament**, 95A–98A, non-conductive, dark or mid colour (about 29 g; thin insert about 23 g) – [§4](#4-mechanical-parts)
- [ ] Optional, soft top only: contact cement or a flexible glue, for a permanent insert (the thin insert needs none)
- [ ] Optional: **protection parts** – [§3](#3-optional-protection-parts-keyboard-side-at-the-dock)
- [ ] Optional: 1 × **5-pin 2.54 mm straight male pin header**, only for tap A at the switchplate TB1 socket (USB-C uses four of its pins) – [§2a](#2a-magnetic-pogo-connector)

### Magnetic pogo only

- [ ] 1 pair **5-pin 2.54 mm magnetic pogo connector**, N/S keyed (Adafruit 5413, or an alternative) – [§2a](#2a-magnetic-pogo-connector)

### USB-C only

- [ ] 1 × **USB-C female breakout**, 4 pads (G, D, D, V) – [§2b](#2b-usb-c-connector)
- [ ] 1 × **USB-C male breakout**, 4 pads (V, D−, D+, G)
- [ ] 1 × **Schottky diode**: 1N5817, 1N5819 or SS14 (required)
- [ ] 4 × **M2 × 4 self-tapping pan-head screws**
- [ ] ~1 g **2-part epoxy**
- [ ] 2 × **"NOT USB" labels**
- [ ] ~3 cm **3 mm heat-shrink**

## About the prices

- **Rough retail prices** from late 2026. They exclude shipping and duties.
- **EUR prices** come from EU shops, USD prices from US shops.
- **Turkish prices (TL)** were checked on 2026-11-15 (TPU filament: 2026-11-18; three spools rechecked on 2026-11-19, unchanged). They include KDV (VAT) and use 1 USD ≈ 50.3 TL.
- **Check current listings** before you order.
- **Example listings** with links, prices and stock for every connector part, the diode, the trackpad, screws and wire: [where-to-buy.md](where-to-buy.md).

## 1. Trackpad

| Qty | Part | Buy | ≈ Price |
|---|---|---|---|
| 1 | **Azoteq TPS65 module** | keycapsss **KC10195_65**, variant "TPS65" | €12.00 incl. VAT |
| 1 | **Glass overlay** (`glass` only) | keycapsss KC10195_65, variant **"TPS65 Glass Overlay"** | €6.90 |
| (1) | Thin touch film (`bare` only) | any | €2–5 |

> [!WARNING]
> **The TPS65 is 3.3 V only** (1.65–3.6 V). Never wire it to 5 V.

**TPS65 module**

- **Specs:** IQS550 controller, 65 × 49 mm, ZIF version, 3M 468MP adhesive with liner.
- **Part number:** Azoteq TPS65-201A-x. Mouser lists TPS65-201A-S.
- **I2C address:** 0x74.
- **Pads:** we use its six 2.0 mm solder pads. The ZIF connector J1 is not used.

**Glass overlay**

- **Size:** 65 × 49 × 1.1 mm, black, rounded edges, no adhesive.
- **Variant:** for the `glass` variant only. Skip it for `bare`.
- **Bonding:** it sticks to the module's own adhesive, with no air gap.
- **Feel:** one buyer found the glass "sticky" for fine movements.

**Touch film (`bare` variant)**

- **Material:** matte PET/PC or textured PEI sheet, 0.1–0.15 mm.
- **Use:** it goes over the module's adhesive instead of glass.

## 2. Connector and cable

- **Buy one connector:** [2a](#2a-magnetic-pogo-connector) *or* [2b](#2b-usb-c-connector).
- **Everyone needs** [2c](#2c-wire-sleeve-and-consumables-both-connectors) (wire and consumables).

### 2a. Magnetic pogo connector

| Qty | Part | Buy | ≈ Price |
|---|---|---|---|
| 1 pair | **Magnetic pogo connector**, 5-pin, 2.54 mm, straight | **Adafruit 5413** | US$6.95 |
| (1 pair) | *Generic alternative:* 5-pin 2.54 mm magnetic pair | AliExpress, LCSC and many others; cheaper ones in [§7](#7-cheaper-magnetic-options) | US$1–4 |
| (1) | 5-pin 2.54 mm straight male pin header | any | cents |

> [!IMPORTANT]
> **Buy an N/S-keyed pair:** magnets in both halves, so the reversed orientation repels. A pair that mates either way round puts 3V3 on the pad's SCL when reversed ([wiring.md, Step 2a](../wiring.md#step-2a-magnetic-pogo-dock); [pogo hot-plug](wiring-details.md#hot-plug-magnetic-pogo)). Check this before you buy more than one.

**Adafruit 5413**

- **Two halves:** a flat-pad half and a spring-pin half.
- **Flat-pad half** goes in the keyboard dock. The spring-pin half goes on the pigtail.
- **Housing:** 20.08 × 4.20 × 4.00 mm. The dock pocket is sized for it (`DOCK_CONN_W/H/D` = 20.1/4.2/4.0).
- **Rating:** 20,000 cycles min, 2 A, 50 ± 15 gf per pin.
- **Keying:** by N/S magnets.
- **Right-angle version:** Adafruit 5359.
- **Magnets near the pad:** check for drift at first power-up ([drift check](wiring-details.md#first-power-up)).

<details><summary>Maker part numbers and the magnet distance</summary>

- **Maker part:** MG005 from Shenzhen Weilichuang. Pad half drawing C-8200121-5, pogo half C-8100389-5.
- **Distance:** when docked, the plug's two magnets sit about 7 mm from the trackpad.
- That is closer than the 15 mm rule for loose metal.
- It is accepted because the magnets do not move while the pad is powered.

</details>

**Generic pair**

- **Search for:** "2.54 mm 5-pin magnetic pogo connector, male + female".
- **Must be** 5 pins at 2.54 mm and N/S keyed (see the box above).
- **Measure the housing.** If it is not about 20 × 4.2 × 4 mm, change `DOCK_CONN_W/H/D` and regenerate the dock.

**Pin header (optional)**

- **Only for** tap A at the switchplate TB1 socket. Solder the wires to the header and plug it in. No soldering on the keyboard.
- **Not keyed:** mark its GND end ([wiring.md, Step 1](../wiring.md#step-1-keyboard-side-both-connectors)).
- **USB-C** uses it too, with four wires.

### 2b. USB-C connector

| Qty | Part | Buy | ≈ Price |
|---|---|---|---|
| 1 | **USB-C female breakout**, 4 pads (G, D, D, V), blue | the board you own, or a generic one | owned |
| 1 | **USB-C male breakout**, 4 pads (V, D−, D+, G), green | the board you own, or a generic one | owned |
| (1 pair) | New pair, if you need one | see [New pair](#new-pair) below | ≈ 57 TL in Turkey (checked 2026-11-15); ≈ US$2–5 abroad |
| 1 | **Schottky diode** (required) | 1N5817, 1N5819 or SS14 | cents |
| ~3 cm | Heat-shrink, 3 mm | the assortment in [§2c](#2c-wire-sleeve-and-consumables-both-connectors) | — |
| 4 | **M2 × 4 self-tapping pan-head screws** | e.g. Elecrow PKA07804P | cents |
| ~1 g | **2-part epoxy** (5-minute is fine) | any | — |
| 2 | **"NOT USB" labels** | small sticker or paint pen | — |

> [!WARNING]
> **The Schottky diode is required.** It blocks the 5 V of a real USB cable or charger plugged into the dock. Do not use a silicon diode (1N4148, 1N4001).

**Female board (goes in the keyboard dock)**

- **Generic name:** "USB-C female 4-pin breakout board". In Turkey: Motorobit's 4-pin panel board ([examples](where-to-buy.md#usb-c-connector-parts)).
- **Layout:** the receptacle is top-mounted at the board's front edge.
- **Must have D pads.** That makes it a 16- or 24-pin receptacle, not a 6-pin power-only one.
- **Remove its two 5.1 kΩ CC resistors** ([wiring.md, Step 2b](../wiring.md#step-2b-usb-c-dock)).
- **Measure yours** and set the `USBC_*` constants. Typical board: about 12–14 × 13–16 × 1.0 mm. Typical shell: about 8.94 × 3.26 mm, 7.35 mm long.

**Male board (goes in the printed grip on the rest)**

- **Generic name:** "USB-C male plug breakout board, 4 pads". In Turkey: Motorobit's "Type-C Erkek USB Şase" ([examples](where-to-buy.md#usb-c-connector-parts)).
- **Layout:** the plug is straddle-mounted on a small board.
- **Remove any 56 kΩ (563) or 5.1 kΩ (512 / 5101) resistor.**
- **Measure yours.** Typical board: about 16–17.1 × 8–8.64 mm. Plug shell: about 8.25 × 2.40 mm. Insertion length: about 6.65 mm.

<a id="new-pair"></a>**New pair**

- **Turkey:** Motorobit ["Type-C Erkek USB Şase"](https://www.motorobit.com/type-c-erkek-usb-sase) (male, 7.42 TL) and ["Panel Tipi Type-C Dişi USB Şase 4-Pin"](https://www.motorobit.com/panel-tipi-type-c-disi-usb-sase-4-pin-siyah) (female, 49.44 TL; take it off its faceplate).
- **Abroad:** Kunkune, Tinkersphere, Adafruit 5180, TinyTronics.
- **All listings:** [where-to-buy.md](where-to-buy.md).
- **Pick the small 4-pad boards.**
- **Avoid large test boards:** the AliExpress "Type-C male to female 24P test PCB board" listings and Motorobit's 24-pin test boards. They have 2 × 13 header holes (about 35 × 20 mm) and fit neither the dock nor the grip.
- **Sizes differ from the defaults:** measure the boards and set the `USBC_*` constants.

**Schottky diode**

- **Best:** 1N5817 (20 V) or 1N5819 (40 V), axial DO-41, body about 5.2 × Ø2.7 mm. Or SS14 (SMA).
- **Why these:** they are 1 A parts with about 0.2 V drop at the pad's 3 mA.
- **BAT54 also works:** the single diode, not BAT54A/C/S, in SOT-23. It is a 200 mA part with about 0.3 V drop. Use it only together with the PTC in [§3](#3-optional-protection-parts-keyboard-side-at-the-dock).
- **Polarity:** in series with 3V3 at the keyboard end. Anode toward the Pico, band (cathode) toward the female's V pad.
- **Where it sits:** across the female board, in a cradle under the USB-C retainer. The cradle fits DO-41 by default. For a BAT54, set `USBC_DIODE=(3.0, 1.4)`.

**Heat-shrink, 3 mm**

- **Use:** over the diode leads and joints.
- **Not on the four wires inside the grip:** its clamp pinches the bare wires.

**M2 screws**

- **Spec:** M2 × 4, pan head ≤ Ø3.8 mm, self-tapping (thread-forming for plastic).
- **Example:** Elecrow PKA07804P (200 pcs, US$2). No Turkish shop checked lists M2 self-tapping screws.
- **Two close the grip halves** from below: Ø1.6 pilot holes in the top half, Ø3.9 × 1.4 mm counterbores in the bottom half.
- **Two hold the retainer** down in the dock: Ø3.9 × 1.4 mm counterbores in its arms, Ø1.6 × 4 mm pilot holes in the dock.

**Epoxy**

- **Use:** bonds the male plug's shell into the key groove in the grip's nose.
- **Bead:** also run a bead where the shell meets the board. The unplug pull then goes from the grip straight into the shell.
- **Not CA glue:** it bonds poorly to PETG and is not a substitute.

**"NOT USB" labels**

- **Where:** one on the dock's top face, one on the grip.
- **Why:** neither half is a USB port any more ([wiring.md, Safety first](../wiring.md#safety-first)).

> [!NOTE]
> **No RDY wire on USB-C.** The magnetic pogo's optional RDY wire has no USB-C equivalent in the standard build. The firmware does not need it.

### 2c. Wire, sleeve and consumables (both connectors)

| Qty | Part | Buy | ≈ Price |
|---|---|---|---|
| ~1 m total, 4–5 colours | **Silicone stranded wire**: 30 AWG (keyboard internal), 28 AWG (pigtail) | multi-colour silicone wire kit | €5–10 per kit |
| (~15 cm) | *Alternative pigtail:* ready-made 28 AWG flexible cable, OD ≤ 3.5 mm | any | €2–4 |
| ~5 cm | Braided PET sleeve, 3 mm (or 3–4 mm heat-shrink) | any | €2 |
| 1 set | **Heat-shrink**, 1.5 mm and 3–4 mm | assortment box | €3–6 |
| 1 roll | **Kapton (polyimide) tape**, 10 mm | any | €3 |
| — | Hot glue, or neutral-cure silicone (not acetic RTV) | — | — |

**Wire colours**

| Signal | Colour |
|---|---|
| SDA | blue |
| 3V3 | red |
| GND | black |
| SCL | yellow |
| RDY (pogo only) | green |

**Silicone wire**

- **Why silicone:** very flexible and heat-proof.
- **Outer diameter:** about 0.8 mm (30 AWG) or 0.9–1.0 mm (28 AWG).
- **Pogo dock:** five 30 AWG wires fit its 3.0 × 2.8 mm rear channel.
- **USB-C dock:** its rear channel is 4.0 × 3.9 mm (`USBC_REAR_CH_W`/`_H`).
- **Turkey:** on 2026-11-15 no Turkish shop checked had 26–30 AWG silicone wire in stock.
- **Solid-core 30 AWG wire-wrap wire** (direnc.net) is fine inside the keyboard. It is not fine for the pigtail, which flexes ([examples](where-to-buy.md#shared-parts-both-connectors)).

**Alternative pigtail cable**

- **Cores:** 5-core for the pogo, 4-core for USB-C.
- **Must fit** `CABLE_D` = 3.5 mm and the 4.5 mm channel.
- **Strip the jacket** off the loose end, because the cores rise singly through the riser. Pogo: the last 15 mm (`CABLE_PLUG_LOOSE_LEN`). USB-C: the slack loop as well.
- **Flexibility matters more than shielding:** a stiff cable pushes the light rest around.

**Sleeve**

- **Use:** sleeves the ~18 mm of pigtail that is clamped in the rest's S-groove and tunnel.
- **Size:** the sleeved bundle must be ≤ 3.5 mm.
- **Routing:** the pigtail never runs outside the rest.

**Heat-shrink**

- **1.5 mm** for each joint.
- **3–4 mm** for the pigtail sleeve (if you do not use braid) and for the USB-C diode.
- **Slide every piece on *before* you solder.**
- **Pogo: no large sleeve over the plug.** Its tails, joints and glue must stay within 3 mm behind the housing and 6 mm tall (`PLUG_RELIEF_L/H`).

**Kapton tape**

- **Insulates** joints and the pocket floor (live matrix nets).
- **Tacks** the wires down.
- **Colour:** add black tape if you want it hidden.

**Hot glue or silicone**

- **Strain relief** in the rest's S-groove and behind the receptacle tails.
- **Pogo:** a thin bead across the plug's tails, inside the 3 × 6 mm envelope.

## 3. Optional protection parts (keyboard side, at the dock)

- **When each part is worth fitting:** [wiring-details.md, Optional protection parts](wiring-details.md#optional-protection-parts).
- **All of these are optional.** They go on the keyboard side, at the dock.

> [!IMPORTANT]
> **With USB-C, the Schottky in [§2b](#2b-usb-c-connector) is required**, not optional. The parts below come on top.

| Qty | Part | Example | Does what | ≈ Price |
|---|---|---|---|---|
| 1 | **TVS array, 4 lines**, SOT-23-6 | **ST USBLC6-4SC6** | ESD protection | €0.30–0.60 |
| 2–3 | **100 Ω resistor**, 0805 or 0603 | any 1 % thick-film | hot-plug spikes | cents |
| 1 | **PTC resettable fuse**, about 0.1 A hold | Littelfuse 0805L010 | shorts on 3V3 | €0.20–0.50 |
| (0) | 100 kΩ resistor, 0805 | any | RDY pull-down (not needed) | cents |
| 0–2 | 4.7 kΩ resistor, 0805 | any | extra pull-ups | cents |
| (1) | 10 Ω resistor, 0805 | any | USB-C hot-plug | cents |
| 1 | 1 µF X7R capacitor, 0603/0805 | any | VDDHI decoupling | cents |
| 1 | Scrap of perfboard, about 10 × 8 mm | any | carrier | — |

**TVS array**

- **Alternative:** USBLC6-2SC6 for SDA/SCL only. That is enough for USB-C.
- **Why:** ESD protection for the exposed pads. The TPS65 is rated only ±2 kV HBM.
- **Wiring:** I/O pins to SDA, SCL and RDY. VBUS to 3V3. GND to GND.
- **Check the pinout** in the datasheet.

**100 Ω resistors**

- **Where:** in series with SDA and SCL (and RDY with the pogo), between the connector and the bus.
- **Why:** protects against hot-plug spikes.

**PTC fuse**

- **Examples:** Littelfuse 0805L010 (0805) or Bourns MF-MSMF010 (1812). Check the datasheet.
- **Where:** in series with 3V3.
- **Why:** steel debris attracted by the pogo magnets can short the exposed pads. The fuse keeps the Pico running if it does.
- **Minimum alternative:** a 10 Ω resistor.
- **USB-C:** less needed (recessed contacts, no magnets). If you fit one, put it before the Schottky.

**100 kΩ resistor (RDY pull-down, pogo)**

- **Not needed with the `ithalat` keymap.** It enables the RP2040's internal pull-down on GP15.
- **Only for** other firmware that leaves RDY floating.

**4.7 kΩ resistors (extra SDA/SCL pull-ups to 3V3)**

- **Only fit them if the measured total is ≥ about 4 kΩ** with the pad plugged in.
- **USB-C:** pull them up to the female board's V pad (the diode's cathode side), not to Pico 3V3. Then the bus never idles above the pad's supply.

**10 Ω resistor (USB-C builds that hot-plug)**

- **Where:** in series with the 3V3 wire, before the Schottky. Or use the PTC instead.
- **Why:** it drops about 40 mV and slows the pad's power-up. Plugging in then does not dip the Pico's 3V3 rail ([wiring.md, Plugging and unplugging](../wiring.md#plugging-and-unplugging)).

**1 µF capacitor**

- **Use:** optional VDDHI decoupling at the module.
- **Probably already there:** Azoteq recommends 1 µF, and the module probably has it.

**Perfboard scrap**

- **Carrier** for the TVS and resistors, and for an SS14 or BAT54 diode if you use one.

## 4. Mechanical parts

| Qty | Part | Spec | ≈ Price |
|---|---|---|---|
| 6 | **Silicone bumpers**, self-adhesive, Ø 10 mm (`BUMPER_D`) | your keyboard's bumper height + 0.6 mm | €3–5 per sheet |
| 2 (optional) | **Steel flat bar ballast**, 78 × 20 × 5 mm (`BALLAST_SIZE`) | mild steel, cut to 78 mm | €3–6 per metre of bar |
| — | **Filament: PLA or PETG**, non-conductive | see the [per-part list](#filament-per-printed-part) | €20–25/kg spool, about €3–5 used |
| (1, soft top only) | **Filament: TPU 95A–98A**, non-conductive | about 29 g for the insert, plus purge on a multi-material printer; the thin insert about 23 g ([TPU notes](#tpu-filament-soft-top-only)) | 988.60–1,096 TL per 750 g–1 kg spool in Turkey ([where to buy](where-to-buy.md#tpu-filament-tpu-top-only)); ≈ 30–38 TL used (thin insert: ≈ 24–31 TL, [per spool](where-to-buy.md#cost-per-insert)) |
| (optional, soft top) | **Contact cement** (polychloroprene, for example Pattex or UHU Kontakt), or a flexible glue | only for a permanent TPU insert; the pegs hold it otherwise. The thin insert is meant to stay glue-free | not checked (hardware store) |
| 0 | **Screws, nuts, inserts:** none for the rest and the pogo dock | — | €0 |
| (1) | Thin double-sided tape, ≤ 0.1 mm | any; for the pocket ledge (not under either TPU insert: it would leave a step at the seams) | €2 |

**Bumpers**

- **Height = your keyboard's bumper height + 0.6 mm** (`BUMPER_RECESS`).
- **Example:** keyboard on 2.0 mm bumpers → use 2.6 mm (2.5–2.7 mm) on the rest.
- **Set** `KEYBOARD_BUMPER_H` to your measured value. The preview's print notes give the exact height.
- **Type:** the same as the keyboard's (its BOM lists 8 silicone bumpers).
- **Default layout:** 4 corners plus front and back middle (`BUMPER_POSITIONS = None`).

<details><summary>Why +0.6 mm</summary>

- The bumpers sit in 0.6 mm locating recesses, so the rest's top lines up with the switchplate top.
- Bumpers of the keyboard's own height would leave the rest 0.6 mm low.

</details>

**Steel ballast (optional)**

- **Material:** mild steel (for example S235), 20 × 5 mm flat bar, cut to 78 mm and deburred.
- **Pocket:** 78.5 × 20.5 × 5.25 mm each, so a longer bar does not fit.
- **Weight:** about 61.2 g each, 122 g per pair (7.85 g/cm³).
- **Placement:** one pocket under each wrist zone, left and right.
- **Distance:** at least 20 mm from the trackpad (`BALLAST_MIN_DIST_FROM_TP`), because loose metal near the pad disturbs it.
- **Finish:** paint or tape the bar against rust.
- **Fixing:** a few dots of silicone, CA or epoxy. Or close the pockets with the anti-slip pad ([reference.md, Ballast](reference.md#ballast)).
- **Lead** is not recommended.
- **Skip it:** set `BALLAST_ENABLED = False`, or print with higher infill.

<details><summary>Why 78 mm, and what happens if it does not fit</summary>

- 78 mm is the longest bar that keeps the 20 mm distance, the 3 mm wall at the bed and the 3 mm top skin with the default rest.
- If you change the rest so that a bar no longer fits, `generate.py` shortens it or makes its pocket shallower (`BALLAST_AUTO_SHORTEN`).
- It logs this, and verify WARNs.
- The log and `build/manifest.json` give the final size.

</details>

**Filament**

- **Non-conductive only:** no carbon-fibre or metal fill near the pad.
- **PETG** copes better with warm wrists and is less brittle.
- **No supports:** the trackpad pocket opens upward. The docks print upside down, also without supports.

<a id="tpu-filament-soft-top-only"></a>**TPU filament (soft top only)**

- **What it is for:** the optional TPU insert or the thin TPU insert ([README, Smooth top](../README.md#smooth-top-tpu-insert)).
- **How much:** about 29 g per TPU insert, about 23 g per thin insert. Any spool listed is plenty for many inserts.
- **Hardness:** 95A–98A. Softer grades feel nicer, but the 85A and 87A spools checked in Turkey were out of stock on 2026-11-18. The insert's thickness and 10 % gyroid give the cushion. The thin insert gives the same touch with almost no cushion.
- **Non-conductive only:** never carbon, CF, ESD/antistatic, conductive, metal-filled or glitter TPU. Bambu "TPU for AMS" (68D) is nearly rigid, so it gives no cushion.
- **Colour:** dark or mid. White and natural TPU turn yellow and show skin oil.
- **Type:** polyether TPU resists sweat (hydrolysis) better than polyester TPU over years. The Turkish listings do not say which they are.
- **Skin contact:** none of the Turkish listings claim a skin-contact certification (ISO 10993).
- **Dry it** before printing: 55–70 °C for 4–8 h.

**No screws for the rest and the pogo dock**

- **Module:** drops into its pocket. Optionally use 2–3 small squares of ≤ 0.1 mm double-sided tape on the ledge.
- **Dock:** snaps into the two switch cut-outs.
- **Ballast:** glued in.
- **USB-C:** see the screw row in [§2b](#2b-usb-c-connector).

**Double-sided tape**

- **Use:** optional module retention on the pocket ledge.
- **Never apply it to the glass.**

### Filament per printed part

- **Estimates.** `build/manifest.json` has the solid volumes.
- **Not the same as the part masses:** [reference.md, Mass](reference.md#mass) gives the USB-C dock as about 6.3 g, the grip 1.2 g and the retainer 1.2 g (solid PLA).

| Part | STL | Connector | ≈ Filament | Notes |
|---|---|---|---|---|
| Rest | `stl/ithalat-glass.stl` or `stl/ithalat-bare.stl` | both | 100–160 g | 15–40 % gyroid infill, 4 perimeters |
| Rest base, soft top (instead of the rest) | `stl/ithalat-glass-tpu-base.stl` or `stl/ithalat-bare-tpu-base.stl` | both | 100–135 g PETG/PLA | as the rest |
| TPU insert, soft top | `stl/ithalat-tpu-insert.stl` | both | ≈ 29 g TPU (28–30 g at 5–15 % gyroid) | 10 % gyroid, 2–3 walls, top ≥ 1.2 mm, flat side down; 0.1 mm layers on base and insert |
| Rest base, thin soft top (instead of the rest) | `stl/ithalat-glass-tpu-thin-base.stl` or `stl/ithalat-bare-tpu-thin-base.stl` | both | 105–125 g PETG/PLA | as the rest, at 0.1–0.12 mm layers |
| Thin TPU insert, thin soft top | `stl/ithalat-tpu-thin-insert.stl` | both | ≈ 23 g TPU | as loaded (already lying on its underside), 0.2 mm layers (0.12 mm on base and insert for flusher seams), 2 walls, 10 % gyroid, top ≥ 1.2 mm |
| Pogo dock | `stl/ithalat-dock-pogo.stl` | pogo | ≈ 5 g | PETG recommended for its snap blades |
| USB-C dock | `stl/ithalat-dock-usbc.stl` | USB-C | ≈ 6.5 g | PETG recommended |
| USB-C grip, top and bottom | `stl/ithalat-usbc-grip-top.stl`, `stl/ithalat-usbc-grip-bottom.stl` | USB-C | ≈ 1.3 g | 100 % infill |
| USB-C retainer (board hold-down + clip lock) | `stl/ithalat-usbc-retainer.stl` | USB-C | ≈ 1.3 g | PETG, 100 % infill, prints upside down |

## 5. Tools and consumables (not in the cost)

- [ ] **Soldering kit:** fine-tip iron, 0.5 mm solder, flux and solder wick.
- [ ] **Multimeter** with continuity, diode and ohms ranges. The diode range checks the USB-C Schottky.
- [ ] **Hand tools:** tweezers, flush cutters, wire stripper for 28–30 AWG.
- [ ] **USB-C only:** hot tweezers or a second iron, to lift the tiny CC resistors off the breakout boards.
- [ ] **Keycap puller and switch puller.** The switches are hot-swap, so nothing is desoldered.
- [ ] **Isopropyl alcohol** and a lint-free cloth for bonding the glass.
- [ ] **Heat gun** or hot-air station for the heat-shrink.

> [!NOTE]
> **No needle file needed** for the recommended wiring. You need one only for the alternative under-plate route ([wiring-details.md, Under-plate alternative](wiring-details.md#under-plate-alternative-modifies-the-case)). That route modifies the case: a notch filed into an internal acrylic bar.

## 6. Cost summary (approximate)

| Group | Magnetic pogo | USB-C |
|---|---|---|
| TPS65 module | €12 | €12 |
| Glass overlay (`glass` variant only, not in the total) | €6.90 | €6.90 |
| Connector | US$7 (Adafruit)<br>US$1–4 (generic)<br>216 TL (Motorobit)<br>about 58–78 TL DIY ([§7](#7-cheaper-magnetic-options)) | US$0 with your boards<br>new pair: about 57 TL in Turkey (Motorobit) or US$2–5 abroad<br>plus a diode (cents) |
| Wire, sleeve, heat-shrink, Kapton | €10–15 | €10–15 |
| Optional protection parts | €1–2 | €1–2 |
| Bumpers | €3–5 | €3–5 |
| Steel ballast (optional) | €3–6 | €3–6 |
| Filament used | €3–5 | €3–5 |
| TPU for the soft top (optional, not in the total) | ≈ 30–38 TL (TPU insert) or ≈ 24–31 TL (thin insert) used; a spool: 988.60–1,096 TL | ≈ 30–38 TL (TPU insert) or ≈ 24–31 TL (thin insert) used; a spool: 988.60–1,096 TL |
| **Total** | **≈ €40–50** plus the glass (€6.90), excluding shipping | **≈ €35–45** plus the glass (€6.90), excluding shipping |

## 7. Cheaper magnetic options

- **Why:** the Adafruit pair costs about US$7. These options give you the magnetic snap and the breakaway for less.
- **Date:** found on 2026-11-15. Turkish prices include KDV; shipping is extra.
- **More listings** for every connector part (pogo pairs, DIY pins and magnets, USB-C breakout boards, the Schottky): [where-to-buy.md](where-to-buy.md).
- **Cheapest of all:** the USB-C pair you may already own ([§2b](#2b-usb-c-connector)). It costs nothing extra, but it does not snap on or break away.

| Option | What you buy | Price on 2026-11-15 |
|---|---|---|
| **DIY magnetic pogo** | 5 pogo pins, 4 small NdFeB magnets, a perfboard strip, a holder you print | **≈ 58 TL (≈ US$1.15)** per connector as designed; **≈ 78 TL (≈ US$1.55)** with in-stock parts |
| **Motorobit 5-pin 2.54 mm magnetic set** | ready-made male + female pair ([listing](https://www.motorobit.com/5-pin-254mm-pogo-pin-manyetik-konnektor-takimi)) | **216.30 TL** (180.25 + KDV) ≈ US$4.30 |
| **AliExpress generic 2.54 mm 5-pin magnetic pair** | ready-made pair, e.g. [this listing](https://www.aliexpress.com/item/1005002180522253.html) | not shown (see below) |

**DIY magnetic pogo: price notes**

- **As designed:** 5 mm pins and 4 × 2 mm magnets. Both were out of stock on 2026-11-15.
- **With in-stock parts:** 3 mm pins and Ø2 × 3 mm magnets.
- **Amortised:** the per-connector prices above are amortised.
- **Minimum spend:** ≈ 111 TL (90.74 + 4 × 1.24 + 15.45 TL), or ≈ 146 TL (120.98 + 8 × 1.24 + 15.45 TL) with in-stock parts. That buys enough pins for two connectors. Shipping from two shops comes on top.
- **Parts and design notes:** [below](#diy-magnetic-pogo-the-parts).

**Motorobit set**

- **Stock:** only 4 in stock on that day.
- **Rating:** 10,000 cycles, 45 ± 10 gf per pin, 2 A.
- **Check** that it repels when reversed (N/S keyed), and measure the housing.
- **4-pin set:** the 4-pin set from the same shop is listed at 20 × 4 × 4 mm, close to the dock pocket.

**AliExpress pair**

- **Variant:** pick the straight board-mount 5-pin variant.
- **Price:** AliExpress prices load only in a browser, so none is shown. Search snippets suggested about US$1.4–1.7 for the cheapest variants (not confirmed).
- **Same checks:** N/S keyed, and a housing of about 20 × 4.2 × 4 mm, or change `DOCK_CONN_W/H/D`.

### DIY magnetic pogo: the parts

| Part | Qty | Price |
|---|---|---|
| Pogo pins, 5 mm | 5 | 45.37 TL for 5 (3 mm pins: 60.49 TL) |
| NdFeB discs, 4 × 2 mm (or 5 × 2 mm) | 4 | 4.96 TL (Ø2 × 3 mm: 9.92 TL) |
| Perfboard for the flat pads | 1 strip | about 8 TL per connector |
| **Total** | | **≈ 58 TL ≈ US$1.15** per connector as designed; **≈ 78 TL ≈ US$1.55** with the in-stock 3 mm pins and Ø2 × 3 mm magnets |

**Pogo pins**

- **Spec:** 5.0 mm long, 3.5 mm compressed (1.5 mm travel), tip Ø0.9, barrel Ø1.5, flange Ø2.0, 0.8 mm tail ([drawing](https://pdf.direnc.net/upload/22113-pogo-pin-size.pdf)).
- **Listing:** direnc.net ["5mm Pogo Pin Konnektör - 10 Adet"](https://www.direnc.net/5mm-pogo-pim-konnektor-10-adet), stock code 22113: 90.74 TL per 10 (75.61 + KDV).
- **Out of stock on 2026-11-15.**
- **In stock that day:** the [3 mm pin](https://www.direnc.net/3mm-pogo-pim-100-adet) (stock code 22112), 120.98 TL per 10. Same tip, barrel and flange, but only 0.65 mm travel (see "GND first" below).

**Magnets**

- **Placement:** 2 in the dock half, 2 in the plug.
- **Listing:** Motorobit [4 × 2 mm discs](https://www.motorobit.com/4x2mm-neodymium-strong-magnet): 1.24 TL each (1.03 + KDV).
- **Out of stock on 2026-11-15**, like the 5 × 2 mm and most other small sizes.
- **In stock that day:** [Ø2 × 3 mm discs](https://www.motorobit.com/2x3mm-neodymium-strong-magnet), 1.24 TL each, much weaker. Plan on two per magnet position (8 in total).

**Perfboard**

- **Listing:** Motorobit [2 × 8 cm double-sided epoxy perfboard](https://www.motorobit.com/2x8cm-epoxy-cift-tarafli-delikli-plaket): 15.45 TL, in stock.
- **direnc.net:** its 2 × 8 board was out of stock; its 6 × 13 board was 24.20 TL.

### DIY design notes

- **Holder:** print Ø1.6 mm holes at 2.54 mm pitch, with a Ø2.1 mm counterbore for the pin flanges.
- **Holder size:** five pins span 10.2 mm. With two 4 × 2 mm magnets and walls, the holder is about 22 × 4.8 mm. Ø2 × 3 mm magnets need their own holes.
- **Not modelled:** the generator does not model this holder. Set `DOCK_CONN_W/H/D` to your holder's outside size, so the pogo dock's pocket fits it.
- **GND first:** recess the signal pins 0.3–0.5 mm behind GND, with 3V3 in between. GND then touches first and leaves last.
- **3 mm pins** (0.65 mm travel): use steps of about 0.2 mm. The MG005 has no fixed order.
- **Keying:** fit the dock magnets N-out on the left and S-out on the right, and the plug's the other way round. A plug turned over then repels.
- **Pin side:** keep the flat pads on the dock (flush, easy to wipe) and the springs on the pigtail, as with the MG005.
- **Protection still applies:** the pads are exposed live contacts. See [§3](#3-optional-protection-parts-keyboard-side-at-the-dock) and [wiring-details.md, Optional protection parts](wiring-details.md#optional-protection-parts).
- **Hold:** the magnets should pull at least twice as hard as all the pin springs push together.
- **Chamfers:** add printed chamfers so the plug centres itself.
- **Wear:** tinned perfboard pads oxidise and wear. Re-tin them now and then, or order a small gold-plated (ENIG) pad board.
- **Magnets near the pad:** the same caveat as the MG005 applies. Smaller 4 × 2 mm magnets are better than the MG005's here.
