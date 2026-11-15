# ithalat bill of materials

This is everything you need for the *ithalat* wrist rest and its trackpad link to the [Yakamoz](https://github.com/ozkan/Yakamoz) keyboard. Wiring instructions are in [wiring.md](../wiring.md), and every dimension comes from [`config.py`](../config.py).

You need **one** of the two connectors: the magnetic pogo pair (§2a) or the USB-C breakout pair (§2b). [Pick your connector](../README.md#pick-your-connector) compares them. Everything else is shared.

**About the prices:** they are rough retail prices from late 2026 and exclude shipping and duties. EUR prices come from EU shops and USD prices from US shops. Turkish prices (TL) were checked on 2026-11-15, include KDV (VAT) and use 1 USD ≈ 50.3 TL. Check current listings before you order. Example listings with links, prices and stock for every connector part, the diode, the trackpad, screws and wire are in [wiring.md, Example parts and where to buy](../wiring.md#example-parts-and-where-to-buy).

## 1. Trackpad

| Qty | Part | Example / part number | Notes | ≈ Price |
|---|---|---|---|---|
| 1 | **Azoteq TPS65 trackpad module**: IQS550, 65 × 49 mm, ZIF version, 3M 468MP adhesive with liner | keycapsss **KC10195_65**, variant "TPS65". This is Azoteq TPS65-201A-x; Mouser lists TPS65-201A-S. | **3.3 V only** (1.65–3.6 V). I2C address 0x74. Six 2.0 mm solder pads, which we use. The ZIF connector J1 is not used. | €12.00 incl. VAT |
| 1 | **Glass overlay**, 65 × 49 × 1.1 mm, black, rounded edges, no adhesive | keycapsss KC10195_65, variant **"TPS65 Glass Overlay"** | For the `glass` variant only; skip it for `bare`. It is bonded with the module's own adhesive, with no air gap. One buyer found the glass "sticky" for fine movements. | €6.90 |
| (1) | Thin touch film for the `bare` variant: matte PET/PC or textured PEI sheet, 0.1–0.15 mm | any | Goes over the module's adhesive instead of glass. | €2–5 |

## 2. Connector and cable

### 2a. Magnetic pogo connector

| Qty | Part | Example / part number | Notes | ≈ Price |
|---|---|---|---|---|
| 1 pair | **Magnetic pogo connector, 5-pin, 2.54 mm, straight**: flat-pad half plus spring-pin half | **Adafruit 5413**. Maker part **MG005** from Shenzhen Weilichuang: pad half drawing C-8200121-5, pogo half C-8100389-5. A right-angle version is **Adafruit 5359**. | Housing **20.08 × 4.20 × 4.00 mm**, which the dock pocket is sized for (`DOCK_CONN_W/H/D` = 20.1/4.2/4.0). Rated 20,000 cycles min, 2 A, 50 ± 15 gf per pin. Keyed by N/S magnets. The flat-pad half goes in the keyboard dock; the spring-pin half goes on the pigtail. When docked, the plug's two magnets sit about 7 mm from the trackpad, closer than the 15 mm rule for loose metal; that is accepted because they do not move while the pad is powered (check for drift at first power-up, [wiring.md §6](../wiring.md#6-test-procedure)). | US$6.95 |
| (1 pair) | *Generic alternative:* "2.54 mm 5-pin magnetic pogo connector, male + female" | AliExpress, LCSC and many other sellers; cheaper sources in §7 | It must be 5 pins at 2.54 mm and **N/S keyed: magnets in both halves, so the reversed orientation repels**. Check that before you buy more than one. A pair that mates either way round puts 3V3 on the pad's SCL when reversed ([wiring.md §5](../wiring.md#hot-plug)). **Measure the housing.** If it is not about 20 × 4.2 × 4 mm, change `DOCK_CONN_W/H/D` and regenerate the dock. | US$1–4 |
| (1) | 5-pin 2.54 mm straight male pin header | any | For tap A at the switchplate TB1 socket: solder the wires to it and plug it in, with no soldering on the keyboard. **It is not keyed**, so mark its GND end ([wiring.md §3.4](../wiring.md#34-choose-a-tap-point)). The USB-C build uses it too, with four wires. | cents |

### 2b. USB-C connector

| Qty | Part | Example / part number | Notes | ≈ Price |
|---|---|---|---|---|
| 1 | **USB-C female breakout board, 4 pads (G, D, D, V)**, blue | the board you already own; generic "USB-C female 4-pin breakout board"; in Turkey, Motorobit's 4-pin panel board ([examples](../wiring.md#usb-c-connector-parts)) | Goes in the keyboard dock. The receptacle is top-mounted at the board's front edge. The board is about 12–14 × 13–16 × 1.0 mm; the shell about 8.94 × 3.26 mm and 7.35 mm long. **Measure yours** and set the `USBC_*` constants. It must have D pads, which makes it a 16- or 24-pin receptacle, not a 6-pin power-only one. Remove its two 5.1 kΩ CC resistors ([wiring.md §7.4](../wiring.md#74-prepare-the-breakout-boards)). | owned |
| 1 | **USB-C male breakout board, 4 pads (V, D−, D+, G)**, green | the board you already own; generic "USB-C male plug breakout board, 4 pads"; in Turkey, Motorobit's "Type-C Erkek USB Şase" ([examples](../wiring.md#usb-c-connector-parts)) | Goes in the printed grip on the rest. The plug is straddle-mounted on a small board, about 16–17.1 × 8–8.64 mm. Plug shell about 8.25 × 2.40 mm, insertion length about 6.65 mm. **Measure yours.** Remove any 56 kΩ (563) or 5.1 kΩ (512 / 5101) resistor. | owned |
| (1 pair) | New pair, if you need one | Turkey: Motorobit ["Type-C Erkek USB Şase"](https://www.motorobit.com/type-c-erkek-usb-sase) (male, 7.42 TL) and ["Panel Tipi Type-C Dişi USB Şase 4-Pin"](https://www.motorobit.com/panel-tipi-type-c-disi-usb-sase-4-pin-siyah) (female, 49.44 TL; take it off its faceplate). Abroad: Kunkune, Tinkersphere, Adafruit 5180, TinyTronics. All of them are in [wiring.md, USB-C connector parts](../wiring.md#usb-c-connector-parts). | Pick the **small 4-pad boards**. The AliExpress "Type-C male to female 24P test PCB board" listings, and Motorobit's 24-pin test boards, are large boards with 2 × 13 header holes (about 35 × 20 mm) that fit neither the dock nor the grip. Sizes differ from the defaults: measure the boards and set the `USBC_*` constants. | ≈ 57 TL in Turkey (checked 2026-11-15); ≈ US$2–5 abroad |
| 1 | **Schottky diode** | **1N5817** (20 V) or **1N5819** (40 V), axial DO-41, body about 5.2 × Ø2.7 mm, or **SS14** (SMA). These are 1 A parts with about 0.2 V drop at the pad's 3 mA. A **BAT54 (the single diode, not BAT54A/C/S)** in SOT-23 works too, but it is a 200 mA part with about 0.3 V drop: use it only together with the PTC in §3 | **Required.** In series with 3V3 at the keyboard end: anode toward the Pico, band (cathode) toward the female's V pad. It blocks the 5 V of a real USB cable or charger plugged into the dock. Do not use a silicon diode (1N4148, 1N4001). It lies across the female board in a cradle under the USB-C retainer (DO-41 by default; for a BAT54 set `USBC_DIODE=(3.0, 1.4)`). | cents |
| ~3 cm | Heat-shrink, 3 mm | from the assortment in §2c | Over the diode leads and joints. Not on the four wires inside the grip: its clamp pinches the bare wires. | — |
| 4 | **M2 × 4 self-tapping pan-head screws** (thread-forming for plastic) | M2 × 4, pan head ≤ Ø3.8 mm, e.g. Elecrow PKA07804P (200 pcs, US$2). No Turkish shop checked lists M2 self-tapping screws. | Two close the grip halves from below (Ø1.6 pilot holes in the top half, Ø3.9 × 1.4 mm counterbores in the bottom half). Two hold the retainer down in the dock (Ø3.9 × 1.4 mm counterbores in its arms, Ø1.6 × 4 mm pilot holes in the dock). | cents |
| ~1 g | **2-part epoxy** (5-minute is fine) | any | Bonds the male plug's shell into the key groove in the grip's nose and runs a bead where the shell meets the board, so the unplug pull goes from the grip straight into the shell. CA bonds poorly to PETG and is not a substitute. | — |
| 2 | **"NOT USB" labels** | small sticker or paint pen | One on the dock's top face, one on the grip. Neither half is a USB port any more ([wiring.md §7.9](../wiring.md#79-it-is-not-usb-labels-chargers-and-laptops)). | — |

The magnetic pogo's optional RDY wire has no USB-C equivalent in the standard build. The firmware does not need it.

### 2c. Wire, sleeve and consumables (both connectors)

| Qty | Part | Example / part number | Notes | ≈ Price |
|---|---|---|---|---|
| ~1 m total, 4–5 colours | **Silicone stranded wire, 30 AWG** (keyboard internal) and **28 AWG** (pigtail) | Multi-colour silicone wire kit. Colours: **blue SDA, red 3V3, black GND, yellow SCL**, plus **green RDY** for the pogo. | Very flexible and heat-proof. About 0.8 mm (30 AWG) or 0.9–1.0 mm (28 AWG) outer diameter. Five 30 AWG wires fit the pogo dock's 3.0 × 2.8 mm rear channel; the USB-C dock's is 4.0 × 3.9 mm (`USBC_REAR_CH_W`/`_H`). On 2026-11-15 no Turkish shop checked had 26–30 AWG silicone wire in stock; solid-core 30 AWG wire-wrap wire (direnc.net) is fine inside the keyboard but not for the pigtail, which flexes ([examples](../wiring.md#shared-parts-both-connectors)). | €5–10 per kit |
| (~15 cm) | *Alternative pigtail:* ready-made 5-core (pogo) or 4-core (USB-C) 28 AWG flexible cable, OD ≤ 3.5 mm | any | Must fit `CABLE_D` = 3.5 mm and the 4.5 mm channel. Strip the jacket off the loose end (pogo: the last 15 mm, `CABLE_PLUG_LOOSE_LEN`; USB-C: the slack loop as well), because the cores rise singly through the riser. Flexibility matters more than shielding, because a stiff cable pushes the light rest around. | €2–4 |
| ~5 cm | Braided PET sleeve, 3 mm (or 3–4 mm heat-shrink) | any | Sleeves the ~18 mm of pigtail that is clamped in the rest's S-groove and tunnel. The sleeved bundle must be ≤ 3.5 mm. The pigtail never runs outside the rest. | €2 |
| 1 set | **Heat-shrink**: 1.5 mm (each joint) and 3–4 mm (pigtail sleeve if you do not use braid; the USB-C diode) | assortment box | Slide every piece on *before* you solder. **Pogo: no large sleeve over the plug.** Its tails, joints and glue must stay within 3 mm behind the housing and 6 mm tall (`PLUG_RELIEF_L/H`). | €3–6 |
| 1 roll | **Kapton (polyimide) tape**, 10 mm, plus black if you want it hidden | any | Insulates joints and the pocket floor (live matrix nets), and tacks the wires down. | €3 |
| — | Hot glue, or neutral-cure silicone (not acetic RTV) | — | Strain relief in the rest's S-groove and behind the receptacle tails; with the pogo, a thin bead across the plug's tails, inside the 3 × 6 mm envelope. | — |

## 3. Optional protection parts (keyboard side, at the dock)

See [wiring.md §5](../wiring.md#5-electrical-notes) for when each part is worth fitting. With USB-C, the Schottky in §2b is **required**, not optional; the parts below come on top.

| Qty | Part | Example | Purpose | ≈ Price |
|---|---|---|---|---|
| 1 | **TVS array, 4 lines**, SOT-23-6 | **ST USBLC6-4SC6**, or USBLC6-2SC6 for SDA/SCL only (enough for USB-C) | ESD protection for the exposed pads. The TPS65 is rated only ±2 kV HBM. Connect the I/O pins to SDA, SCL and RDY, VBUS to 3V3 and GND to GND. Check the pinout in the datasheet. | €0.30–0.60 |
| 2–3 | **100 Ω resistor**, 0805 or 0603 | any 1 % thick-film | In series with SDA and SCL (and RDY with the pogo), between the connector and the bus. Protects against hot-plug spikes. | cents |
| 1 | **PTC resettable fuse, about 0.1 A hold** | e.g. Littelfuse 0805L010 (0805) or Bourns MF-MSMF010 (1812); check the datasheet | In series with 3V3. Steel debris attracted by the pogo magnets can short the exposed pads; the fuse keeps the Pico running if it does. A 10 Ω resistor is the minimum alternative. Less needed with USB-C (recessed contacts, no magnets); if you fit one, put it before the Schottky. | €0.20–0.50 |
| (0) | 100 kΩ resistor, 0805 | any | RDY pull-down (pogo). **Not needed with `ardakilic_trackpad`**, which enables the RP2040's internal pull-down on GP15. Only for other firmware that leaves RDY floating. | cents |
| 0–2 | 4.7 kΩ resistor, 0805 | any | Extra SDA/SCL pull-ups to 3V3. **Only fit them if the measured total is ≥ about 4 kΩ** with the pad plugged in. With USB-C, pull them up to the female board's **V pad** (the diode's cathode side), not to Pico 3V3, so the bus never idles above the pad's supply. | cents |
| (1) | 10 Ω resistor, 0805 | any | USB-C builds that hot-plug: in series with the 3V3 wire, before the Schottky (or use the PTC). It drops about 40 mV and slows the pad's power-up, so plugging in does not dip the Pico's 3V3 rail ([wiring.md §7.10](../wiring.md#710-hot-plug)). | cents |
| 1 | 1 µF X7R capacitor, 0603/0805 | any | Optional VDDHI decoupling at the module. Azoteq recommends 1 µF, and the module probably has it already. | cents |
| 1 | Scrap of perfboard, about 10 × 8 mm | any | Carrier for the TVS and resistors, and for an SS14 or BAT54 diode if you use one. | — |

## 4. Mechanical parts

| Qty | Part | Spec | Notes | ≈ Price |
|---|---|---|---|---|
| 6 | **Silicone bumpers, self-adhesive, Ø 10 mm** (`BUMPER_D`) | **Height = your keyboard's bumper height + 0.6 mm** (`BUMPER_RECESS`). For example, if the keyboard sits on 2.0 mm bumpers, use 2.6 mm (2.5–2.7 mm) on the rest. Set `KEYBOARD_BUMPER_H` to your measured value and the preview's print notes give the exact height. | Use the same type as the keyboard (its BOM lists 8 silicone bumpers). The bumpers sit in 0.6 mm locating recesses, so the rest's top lines up with the switchplate top. Bumpers of the keyboard's own height would leave the rest 0.6 mm low. The default layout is 4 corners plus front and back middle (`BUMPER_POSITIONS = None`). | €3–5 per sheet |
| 2 (optional) | **Steel flat bar ballast, 78 × 20 × 5 mm** (`BALLAST_SIZE`) | Mild steel (for example S235), 20 × 5 mm flat bar cut to **78 mm** and deburred. Each pocket is 78.5 × 20.5 × 5.25 mm, so a longer bar does not fit. About **61.2 g each, 122 g per pair** (7.85 g/cm³). | One pocket under each wrist zone, left and right, at least **20 mm from the trackpad** (`BALLAST_MIN_DIST_FROM_TP`), because loose metal near the pad disturbs it. 78 mm is the longest bar that keeps that distance, the 3 mm wall at the bed and the 3 mm top skin with the default rest. If you change the rest so that a bar no longer fits, `generate.py` shortens it or makes its pocket shallower (`BALLAST_AUTO_SHORTEN`), logs it, and verify WARNs; the log and `build/manifest.json` give the final size. Paint or tape the bar against rust, and fix it with a few dots of silicone. Lead is not recommended. Set `BALLAST_ENABLED = False`, or print with higher infill, to do without. | €3–6 per metre of bar |
| — | **Filament: PLA or PETG**, *non-conductive* (no carbon-fibre or metal fill near the pad) | See the per-part list below. | PETG copes better with warm wrists and is less brittle. The trackpad pocket opens upward and needs no supports. The docks print upside down, also without supports. | €20–25/kg spool, about €3–5 used |
| 0 | **Screws, nuts, inserts: none for the rest and the pogo dock** | — | The module drops into its pocket (optionally with 2–3 small squares of ≤ 0.1 mm double-sided tape on the ledge), the dock snaps into the two switch cut-outs, and the ballast is glued in. For USB-C, see the fastener row in §2b. | €0 |
| (1) | Thin double-sided tape, ≤ 0.1 mm | any | Optional module retention on the pocket ledge. Never apply it to the glass. | €2 |

**Filament per printed part** (estimates; `build/manifest.json` has the solid volumes):

| Part | STL | Connector | ≈ Filament | Notes |
|---|---|---|---|---|
| Rest | `stl/ithalat-glass.stl` or `stl/ithalat-bare.stl` | both | 100–160 g | 15–40 % gyroid infill, 4 perimeters |
| Pogo dock | `stl/ithalat-dock-pogo.stl` | pogo | ≈ 5 g | PETG recommended for its snap blades |
| USB-C dock | `stl/ithalat-dock-usbc.stl` | USB-C | ≈ 6.5 g | PETG recommended |
| USB-C grip, top and bottom | `stl/ithalat-usbc-grip-top.stl`, `stl/ithalat-usbc-grip-bottom.stl` | USB-C | ≈ 1.3 g | 100 % infill |
| USB-C retainer (board hold-down + clip lock) | `stl/ithalat-usbc-retainer.stl` | USB-C | ≈ 1.3 g | PETG, 100 % infill, prints upside down |

## 5. Tools and consumables (not in the cost)

- Fine-tip soldering iron, 0.5 mm solder, flux and solder wick.
- Multimeter with continuity, diode and ohms ranges. The diode range checks the USB-C Schottky.
- Tweezers, flush cutters, wire stripper for 28–30 AWG.
- USB-C only: hot tweezers or a second iron, to lift the tiny CC resistors off the breakout boards.
- Keycap puller and switch puller. The switches are hot-swap, so nothing is desoldered.
- No needle file is needed for the recommended wiring. You need one only for the alternative under-plate route in [wiring.md §3.4](../wiring.md#34-choose-a-tap-point), which modifies the case (a notch filed into an internal acrylic bar).
- Isopropyl alcohol and a lint-free cloth for bonding the glass.
- Heat gun or hot-air station for the heat-shrink.

## 6. Cost summary (approximate)

| Group | Magnetic pogo | USB-C |
|---|---|---|
| TPS65 module + glass overlay | €12 + €6.90 glass | €12 + €6.90 glass |
| Connector | US$7 (Adafruit) / US$1–4 (generic) / 216 TL (Motorobit) / about 58–78 TL DIY (§7) | US$0 with your boards / a new pair about 57 TL in Turkey (Motorobit) or US$2–5 abroad, plus a diode (cents) |
| Wire, sleeve, heat-shrink, Kapton | €10–15 | €10–15 |
| Optional protection parts | €1–2 | €1–2 |
| Bumpers | €3–5 | €3–5 |
| Steel ballast (optional) | €3–6 | €3–6 |
| Filament used | €3–5 | €3–5 |
| **Total** | **≈ €40–50 plus the glass (€6.90), excluding shipping** | **≈ €35–45 plus the glass (€6.90), excluding shipping** |

## 7. Cheaper magnetic options

The Adafruit pair costs about US$7. If you want the magnetic snap and the breakaway for less, these are the options found on **2026-11-15**. Turkish prices include KDV; shipping is extra. More example listings for every connector part (pogo pairs, DIY pins and magnets, USB-C breakout boards, the Schottky) are in [wiring.md, Example parts and where to buy](../wiring.md#example-parts-and-where-to-buy).

| Option | What you buy | Price on 2026-11-15 | Notes |
|---|---|---|---|
| **DIY magnetic pogo** | 5 pogo pins, 4 small NdFeB magnets and a strip of perfboard for the pad half, in a holder you print yourself | **≈ 58 TL (≈ US$1.15) per connector** as designed (5 mm pins, 4 × 2 mm magnets; both were out of stock on 2026-11-15), or **≈ 78 TL (≈ US$1.55)** with the parts that were in stock (3 mm pins, Ø2 × 3 mm magnets). Amortised; the minimum spend is ≈ 111 TL (90.74 + 4 × 1.24 + 15.45 TL) or ≈ 146 TL (120.98 + 8 × 1.24 + 15.45 TL), enough pins for two connectors, plus shipping from two shops | details below |
| **Motorobit 5-pin 2.54 mm magnetic set** | ready-made male + female pair ([listing](https://www.motorobit.com/5-pin-254mm-pogo-pin-manyetik-konnektor-takimi)) | **216.30 TL** (180.25 + KDV) ≈ US$4.30; only 4 in stock on that day | Rated 10,000 cycles, 45 ± 10 gf per pin, 2 A. Check that it repels when reversed (N/S keyed), and measure the housing. The 4-pin set from the same shop is listed at 20 × 4 × 4 mm, close to the dock pocket. |
| **AliExpress generic 2.54 mm 5-pin magnetic pair** | ready-made pair, e.g. [this listing](https://www.aliexpress.com/item/1005002180522253.html) (pick the straight board-mount 5-pin variant) | Not shown: AliExpress prices load only in a browser. Search snippets suggested about US$1.4–1.7 for the cheapest variants (not confirmed) | Same checks: N/S keyed, and a housing of about 20 × 4.2 × 4 mm, or change `DOCK_CONN_W/H/D`. |

**DIY magnetic pogo, the parts:**

| Part | Listing | Price |
|---|---|---|
| 5 pogo pins: 5.0 mm long, 3.5 mm compressed (1.5 mm travel), tip Ø0.9, barrel Ø1.5, flange Ø2.0, 0.8 mm tail ([drawing](https://pdf.direnc.net/upload/22113-pogo-pin-size.pdf)) | direnc.net ["5mm Pogo Pin Konnektör - 10 Adet"](https://www.direnc.net/5mm-pogo-pim-konnektor-10-adet), stock code 22113: **90.74 TL per 10** (75.61 + KDV). **Out of stock on 2026-11-15.** In stock that day: the [3 mm pin](https://www.direnc.net/3mm-pogo-pim-100-adet) (stock code 22112), 120.98 TL per 10, with the same tip, barrel and flange but only 0.65 mm travel (see "GND first" below) | 45.37 TL for 5 (3 mm pins: 60.49 TL) |
| 4 NdFeB discs, 4 × 2 mm (or 5 × 2 mm): 2 in the dock half, 2 in the plug | Motorobit [4 × 2 mm discs](https://www.motorobit.com/4x2mm-neodymium-strong-magnet): **1.24 TL each** (1.03 + KDV). **Out of stock on 2026-11-15**, like the 5 × 2 mm and most other small sizes. In stock that day: [Ø2 × 3 mm discs](https://www.motorobit.com/2x3mm-neodymium-strong-magnet), 1.24 TL each, much weaker: plan on two per magnet position (8 in total) | 4.96 TL (Ø2 × 3 mm: 9.92 TL) |
| Perfboard for the flat pads | Motorobit [2 × 8 cm double-sided epoxy perfboard](https://www.motorobit.com/2x8cm-epoxy-cift-tarafli-delikli-plaket): **15.45 TL**, in stock (direnc.net's 2 × 8 board was out of stock; its 6 × 13 board was 24.20 TL) | about 8 TL per connector |
| **Total** | | **≈ 58 TL ≈ US$1.15 per connector as designed; ≈ 78 TL ≈ US$1.55 with the in-stock 3 mm pins and Ø2 × 3 mm magnets** |

**DIY design notes:**

- **Holder.** Print Ø1.6 mm holes at 2.54 mm pitch with a Ø2.1 mm counterbore for the pin flanges. Five pins span 10.2 mm. With two 4 × 2 mm magnets and walls, the holder is about 22 × 4.8 mm; Ø2 × 3 mm magnets need their own holes. The generator does not model this holder: set `DOCK_CONN_W/H/D` to your holder's outside size so the pogo dock's pocket fits it.
- **GND first.** Recess the signal pins 0.3–0.5 mm behind GND, with 3V3 in between, so GND touches first and leaves last. With the 3 mm pins (0.65 mm travel), use steps of about 0.2 mm. The MG005 has no fixed order.
- **Keying.** Fit the dock magnets N-out on the left and S-out on the right, and the plug's the other way round. A plug turned over then repels.
- **Pin side.** Keep the flat pads on the dock (flush, easy to wipe) and the springs on the pigtail, as with the MG005. The protection advice in [wiring.md §5](../wiring.md#5-electrical-notes) still applies, because the pads are exposed live contacts.
- **Hold.** The magnets should pull at least twice as hard as all the pin springs push together. Add printed chamfers so the plug centres itself.
- **Wear.** Tinned perfboard pads oxidise and wear. Re-tin them now and then, or order a small gold-plated (ENIG) pad board.
- **Magnets near the pad.** The same caveat as the MG005 applies. Smaller 4 × 2 mm magnets are better than the MG005's here.

The cheapest option of all is the USB-C pair you may already own (§2b). It costs nothing extra, but it does not snap on or break away.
