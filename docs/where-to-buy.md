# Where to buy

Example shops for every ithalat part, with prices and stock checked on 2026-11-15 (TPU filament: 2026-11-18).

## TL;DR

- **Examples only.** Checked on 2026-11-15, the TPU filament on 2026-11-18. Prices and stock change: check each listing before you order.
- **Turkish shops first,** then international ones.
- **Measure before you buy.** Pogo pair vs `DOCK_CONN_W/H/D`; USB-C boards vs `USBC_*`.
- **No Turkish shop** checked sells the TPS65, its glass or M2 self-tapping screws.
- **TPU for the optional soft top:** 95A–98A is in stock in Turkey (Porima 98A is made in Turkey). The softer spools checked were out of stock.
- **Quantities and costs** are in [bom.md](bom.md). Wiring steps are in [wiring.md](../wiring.md).

**Jump to**

- Connector: [USB-C parts](#usb-c-connector-parts) · [Magnetic pogo parts](#magnetic-pogo-connector-parts) · [DIY magnetic pogo parts](#diy-magnetic-pogo-parts)
- Everyone: [Shared parts](#shared-parts-both-connectors) · [Could not be checked](#could-not-be-checked)
- Optional: [TPU filament (soft top)](#tpu-filament-tpu-top-only)

## Before you order

Turkish local vendors are listed first: the project is named *ithalat* (Turkish for "import") because, since January 2026, people in Turkey cannot import anything internationally, and all vendors have closed shipping to Turkey because of this ([what the name means](../README.md#what-ithalat-means)).

- **Measure first.** Pogo pair vs `DOCK_CONN_W/H/D` (20.1 × 4.2 × 4.0 mm); USB-C boards vs the `USBC_*` constants in [`config.py`](../config.py).
- **Prices:** TL prices include KDV (VAT). Shipping is extra everywhere.
- **Stock:** as each shop showed on 2026-11-15, or 2026-11-18 for the TPU filament (counts in brackets). Every listing was opened on its date. Out-of-stock parts stay listed: they may come back.
- **Full parts list,** with quantities and rough prices: [bom.md](bom.md).

## USB-C connector parts

Buy the **small 4-pad boards** (V, G, D+, D−). Defaults: female `USBC_F_BOARD` = 13.0 × 13.5 × 1.0 mm, male `USBC_M_BOARD` = 8.64 × 16.5 × 0.8 mm (plug included). Measure, set `USBC_*`, remove the CC resistors.

| Part | Shop | Price | Note |
|---|---|---|---|
| [Type-C Erkek USB Şase](https://www.motorobit.com/type-c-erkek-usb-sase): male | Motorobit (TR) | 7.42 TL | In stock (2302) |
| [Panel Tipi Type-C Dişi USB Şase 4-Pin - Siyah](https://www.motorobit.com/panel-tipi-type-c-disi-usb-sase-4-pin-siyah): female | Motorobit (TR) | 49.44 TL | In stock (19) |
| [Type-C Dip Dönüştürücü - USB C Breakout Modülü](https://www.motorobit.com/type-c-dip-donusturucu-usb-c-breakout-modulu): female, 8 pins | Motorobit (TR) | 43.26 TL | In stock (271) |
| [USB Erkek Type-C Tipi Kılıflı Soket](https://www.motorobit.com/usb-erkek-type-c-tipi-kilifli-soket): male, shelled | Motorobit (TR) | 24.72 TL | In stock (1239) |
| [DIY 24pin USB 3.1 Type-C Male Female Socket Adapter](https://kunkune.co.uk/shop/electronic-components/diy-24pin-usb-3-1-type-c-usb-c-male-female-socket-adapter-plug-connector/) | Kunkune (UK) | £0.90 each (10+: £0.81) | Stock not listed |
| [Male USB C Breakout Board (TS3551)](https://tinkersphere.com/mini-usb/3551-usb-31-type-c-male-breakout-board.html) | Tinkersphere (US) | US$3.49 | In stock (16) |
| [Simple USB C Socket Breakout (5180)](https://www.adafruit.com/product/5180): female | Adafruit (US) | US$1.75 (10+: US$1.58) | In stock |
| [USB-C 2.0 Female to DIP Adapter](https://www.tinytronics.nl/en/cables-and-connectors/connectors/usb/usb-c-2.0-female-to-dip-adapter) | TinyTronics (NL) | €0.90 | In stock (500+) |
| [Type-C USB2 Female to DIP 4-Pin Adapter, pack of 20](https://electropeak.com/type-c-usb2-female-to-dip-4-pin-adapter-breakout-board) | Electropeak | from US$0.09 each | In stock |

> [!WARNING]
> **Do not buy** 24P male/female test boards with 2 × 13 header holes.
>
> - **Too big:** at about 35 × 20 mm they fit neither the dock nor the grip.
> - **Example:** [this AliExpress listing](https://www.aliexpress.com/item/1005006267969256.html) ("Type-C Male to Female USB 3.1 Test PCB Board Adapter Type C 24P 2.54mm", price not shown: prices load only in a browser). Listed so you can recognise them.
> - **Motorobit's 24-pin test boards** are large strip boards too.

<details><summary>Notes on the USB-C parts</summary>

- **Motorobit male:** pads V, G, D−, D+, on a small green board. Same type as the reference build. Remove the 56 kΩ (563) resistor if fitted. Size not listed: compare with `USBC_M_BOARD`.
- **Motorobit female:** pads V, D−, D+, G, purple, on a panel faceplate (black: 19 in stock; [white](https://www.motorobit.com/panel-tipi-type-c-disi-usb-sase-4-pin-beyaz): same price, 23 in stock). The faceplate with its two screw holes is wider than the board: take the board off it. Size not listed: compare with `USBC_F_BOARD`. Check for CC resistors and remove them.
- **Motorobit 8-pin female:** GND, VBUS, CC1, SBU2, D−, D+, SBU1, CC2; 20 × 14 mm. Larger than the default: set the `USBC_F_*` constants and regenerate the dock. Remove its two CC resistors. Also breaks out CC and SBU ([RDY over SBU](wiring-details.md#rdy-over-sbu-advanced)).
- **Motorobit shelled male:** a small 4-pin plug board in a plastic shell. Alternative only: the grip replaces the shell, so use just the board. Check its pads; remove any 56 kΩ resistor.
- **Kunkune (international):** full title "DIY 24pin USB 3.1 Type-C USB-C Male Female Socket Adapter Plug Connector". 4 pads (V, D−, D+, G). Pick "Male Plug" or "Female Socket". Size not listed: measure.
- **Tinkersphere (international):** male, 4 pads (GND, D+, D−, VCC), 17 × 9 × 2.5 mm with the plug, close to `USBC_M_BOARD`. The white housing is not needed. Check for a 56 kΩ resistor.
- **Adafruit 5180 (international):** female, 4 pins, no CC resistors, 14.5 × 9.2 mm. Narrower than the default: set `USBC_F_*` and regenerate. Nothing to remove.
- **TinyTronics (international):** female, 4 pins, no CC resistors, 14 × 12 mm, close to `USBC_F_BOARD`. Pad order not listed: beep it out.
- **Electropeak (international):** female, 4 pins, 12 × 13.8 × 1.6 mm, sold in multiples of 20 (full title "... Breakout Board - Pack of 20"). Closest footprint to `USBC_F_BOARD`, but 1.6 mm thick, not 1.0 mm: set the thickness. Pad order and CC resistors not stated: check both.

</details>

## Magnetic pogo connector parts

A 5-pin, 2.54 mm pair of about 20 × 4.2 × 4 mm fits the pogo dock as it is. It must be **N/S keyed**: a reversed plug repels.

| Part | Shop | Price | Note |
|---|---|---|---|
| [5-Pin 2.54mm Pogo Pin Manyetik Konnektör Takımı](https://www.motorobit.com/5-pin-254mm-pogo-pin-manyetik-konnektor-takimi) | Motorobit (TR) | 216.30 TL | In stock, only 4 |
| [DIY Magnetic Connector - Straight Angle Five Contact Pins (5413)](https://www.adafruit.com/product/5413) | Adafruit (US) | US$6.95 (10+: US$6.26) | In stock; reference |
| [5-position 2.54 mm board-mount pogo pair, 2 A](https://www.aliexpress.com/item/1005002180522253.html) | AliExpress | not shown | Browser-only prices |

<details><summary>Notes on the pogo parts</summary>

- **Motorobit:** straight male + female pair, 2 A, 10,000 cycles, 45 ± 10 gf per pin. Size and N/S keying not stated: check that reversed repels, and measure against `DOCK_CONN_W/H/D`. The eared ("Kulaklı") version was out of stock; a 90° version was 327.54 TL (18 in stock).
- **Adafruit 5413 (MG005, international):** the reference part. The pocket is sized for its 20.08 × 4.20 × 4.00 mm housing. Right-angle: [Adafruit 5359](https://www.adafruit.com/product/5359), also US$6.95, in stock.
- **AliExpress (international):** full title "1 pair magnetic connector spring Pogo Pin 5 position Pitch 2.54 MM board mount male female probe data power charge 2Amp". Title and photo checked. Several variants (board-mount straight, eared, cabled): pick the straight board-mount 5-pin pair. Check the keying, measure it. Visitors from Turkey go to tr.aliexpress.com.
- **direnc.net** no longer lists magnetic connectors: on 2026-11-15 its 5-pin eared set and its 4- and 5-pin round sets redirected to the home page.

</details>

## DIY magnetic pogo parts

For the home-made connector in [bom.md, 7. Cheaper magnetic options](bom.md#7-cheaper-magnetic-options): five pogo pins, small magnets and perfboard in a printed holder.

| Part | Shop | Price | Note |
|---|---|---|---|
| [5mm Pogo Pin Konnektör - 10 Adet](https://www.direnc.net/5mm-pogo-pim-konnektor-10-adet) | direnc.net (TR) | 90.74 TL / 10 | **Out of stock** |
| [3mm Pogo Pin Konnektör - 10 Adet](https://www.direnc.net/3mm-pogo-pim-100-adet) | direnc.net (TR) | 120.98 TL / 10 | In stock (10 packs) |
| [4X2mm Neodymium Strong Magnet](https://www.motorobit.com/4x2mm-neodymium-strong-magnet) | Motorobit (TR) | 1.24 TL each | **Out of stock** |
| [2x3mm Neodymium Strong Magnet](https://www.motorobit.com/2x3mm-neodymium-strong-magnet) | Motorobit (TR) | 1.24 TL each | In stock (3459) |
| [2x8cm Epoxy Çift Taraflı Delikli Plaket](https://www.motorobit.com/2x8cm-epoxy-cift-tarafli-delikli-plaket) | Motorobit (TR) | 15.45 TL | In stock (857) |
| [4mm x 2mm N52 Rare Earth Neodymium Magnet Discs](https://www.jc-magnetics.com/Magnet-N52-4mm-2mm-Discs) | JC Magnetics (US) | US$0.30 (100+: US$0.17) | In stock; min. 50 |

<details><summary>Notes on the DIY parts</summary>

- **5 mm pins (10 pcs):** 1.5 mm travel. The pin the DIY design was drawn for: tip Ø0.9, barrel Ø1.5, flange Ø2.0, stock code 22113. The 7, 10 and 12 mm pins were out of stock too.
- **3 mm pins (10 pcs):** 0.65 mm travel; same tip, barrel and flange (stock code 22112). The GND-first step between the pins shrinks to about 0.2 mm.
- **4 × 2 mm NdFeB disc:** the size the holder was drawn for. Out of stock, like 5 × 2, 6 × 2 and most small sizes.
- **Ø2 × 3 mm NdFeB disc:** the only small disc magnet in stock in Turkey. Much weaker than 4 × 2 mm: use two per magnet position, and check the magnets pull at least twice as hard as the five springs push.
- **2 × 8 cm double-sided perfboard:** the flat-pad half. direnc.net's 2 × 8 board was out of stock. Re-tin the pads now and then.
- **JC Magnetics (international):** 4 × 2 mm N52 discs, minimum order 50.

</details>

## Shared parts (both connectors)

No Turkish shop checked (direnc.net, Motorobit, Robotistan, Robo90, Samm) sells the TPS65 trackpad or M2 self-tapping screws, so those rows come after the Turkish ones.

| Part | Shop | Price | Note |
|---|---|---|---|
| [1N5817 20V 1A DO-41 Schottky Diyot](https://www.motorobit.com/1n5817-20v-1a-do-41-schottky-diyot) | Motorobit (TR) | 1.24 TL | In stock (943) |
| [1N5817 1A 20V Schottky Diyot](https://www.direnc.net/1n5817-1a-20v-schottky-diyot) | direnc.net (TR) | 2.27 TL | In stock |
| [SS14 1A 40V Schottky Diyot DO-214AC](https://www.direnc.net/ss14-1a-40v-schottky-diyot-do-214ac) | direnc.net (TR) | 1.78 TL | In stock |
| [30 AWG Silikon Kablo Siyah - 100 Metre](https://www.motorobit.com/30-awg-silikon-kablo-siyah-100-metre) | Motorobit (TR) | 1050.60 TL | **Out of stock** |
| [30AWG 250 Metre Kırmızı Kablo Sarma Teli](https://www.direnc.net/30awg-250-metre-kirmizi-kablo-sarma-teli) | direnc.net (TR) | 453.69 TL | In stock |
| [TPS65 trackpad module (KC10195_65)](https://keycapsss.com/Azoteq-ProxSense-I2C-Touch-Sensor-Module-Capacitive-Trackpad/KC10195-65) | Keycapsss (DE) | €12.00 | In stock |
| [TPS65 Glass Overlay](https://keycapsss.com/Azoteq-ProxSense-I2C-Touch-Sensor-Module-Capacitive-Trackpad/KC10195-65-GLASS) | Keycapsss (DE) | €6.90 | In stock |
| [Schottky Diode (COM-10926)](https://www.sparkfun.com/schottky-diode.html): 1N5819 | SparkFun (US) | US$0.30 | In stock |
| [M2 Screw (200pcs) - 4mm](https://www.elecrow.com/m2-screw-4mm.html) | Elecrow | US$2.00 / 200 | In stock |
| [Silicone wire 30 AWG, 50 ft, black (3164)](https://www.adafruit.com/product/3164) | Adafruit (US) | US$4.95 | In stock |
| [Silicone ribbon cable, 4 × 28 AWG, 1 m (3891)](https://www.adafruit.com/product/3891) | Adafruit (US) | US$1.95 | In stock |

<details><summary>Notes on the shared parts</summary>

- **1N5817 (Motorobit):** 20 V 1 A, DO-41. Required for USB-C: anode toward the Pico, band toward the female board's V pad.
- **SS14 (direnc.net):** 40 V 1 A, SMA, surface-mount. Motorobit also has the [SS14](https://www.motorobit.com/ss14-40v-1a-schottky-diyot) at 1.85 TL. See [bom.md, 2b. USB-C connector](bom.md#2b-usb-c-connector).
- **30 AWG silicone, 100 m reel (Motorobit):** out of stock in every colour, as were its 28 and 26 AWG reels and direnc.net's 30 AWG silicone set. No Turkish shop checked had 26–30 AWG silicone wire.
- **30 AWG wire-wrap, 250 m (direnc.net):** single solid core; red, yellow, blue, green and black in stock. The only thin wire in stock in Turkey. Fine inside the keyboard, not for the pigtail: a solid core breaks when it flexes.
- **TPS65 (Keycapsss, international):** IQS550, 65 × 49 mm. Full title "Azoteq ProxSense I2C Touch Sensor Module / Capacitive Trackpad, variant TPS65 (KC10195_65)". Delivery 1–3 working days in Germany, 4–7 in the EU, 10–14 elsewhere.
- **Glass overlay (Keycapsss, international):** 65 × 49 × 1.1 mm, "variant TPS65 Glass Overlay". Glass variant only. One buyer found the glass "sticky" for fine movements.
- **1N5819 (SparkFun, international):** 40 V 1 A. An accepted alternative to the 1N5817.
- **M2 × 4 mm screws (Elecrow, international):** self-tapping, pan-head, Phillips, 304 stainless, 200 pcs. USB-C only (4 needed). Head diameter not stated: the counterbores take heads up to Ø3.8 mm.
- **Adafruit 3164 (international):** "Silicone Cover Stranded-Core Wire - 50ft 30AWG Black", 15.2 m, 0.8 mm outer diameter, for the wires inside the keyboard. Other colours: 3165–3169.
- **Adafruit 3891 (international):** "Silicone Cover Stranded-Core Ribbon Cable - 4 Wires 1 Meter Long - 28AWG Black". The wires peel apart; four cores suit the USB-C pigtail. 30 AWG version: [Adafruit 3889](https://www.adafruit.com/product/3889), also US$1.95.

</details>

## TPU filament (TPU top only)

Only for the optional [soft top](../README.md#smooth-top-tpu-insert). Checked on 2026-11-18.

- **Buy:** TPU **95A–98A**, **non-conductive**, in a **dark or mid colour**.
- **How much:** the insert needs about 30 g, so any spool below is plenty.
- **Not:** "conductive", "ESD", "antistatic", carbon / CF, metal-filled or glitter TPU, or Bambu "TPU for AMS" (68D, nearly rigid).

| Product | Shop | Shore | Price | Stock |
|---|---|---|---|---|
| [Porima 3D 1.75mm TPU 98A Filament - Siyah](https://www.robotistan.com/porima3d-175mm-tpu98a-filament-siyah) | Robotistan (TR) | 98A | 988.60 TL / 750 g | In stock |
| [Porima TPU Flex 98A 1.75mm Siyah RAL9005 Filament 1 Kg](https://www.n11.com/urun/porima-tpu-flex-98a-175mm-siyah-ral9005-filament-1-kg-53031280?magaza=nova3dteknoloji) | n11, seller nova3dteknoloji (TR) | 98A | 1,096.00 TL / 1 kg (list 1,299.00) | In stock (13) |
| [Filamix Siyah TPU 95A Esnek Filament 1.75mm 1 Kg](https://www.idefix.com/filamix-siyah-tpu-95a-esnek-filament-175mm-1-kg-p-28061698) | idefix (TR) | 95A | 1,035.12 TL in the basket (list 1,089.60) / 1 kg | In stock |
| [Beta TPU 95A Filament White](https://3dultra.com.tr/beta-tpu-95a-filament-white) | 3D Ultra (TR) | 95A | 1,026.00 TL / 800 g | In stock (18); white, not recommended |
| [Porima 3D 1.75mm TPU 98A Filament - Beyaz](https://www.robotistan.com/porima3d-175mm-tpu98a-filament-beyaz) | Robotistan (TR) | 98A | 988.60 TL / 750 g | In stock; white, not recommended |
| [Esun eFlex 1.75mm (TPU-87A) Natural Filament](https://motorobit.com/esun-eflex-1-75mm-tpu-87a-natural-filament-en) | Motorobit (TR) | 87A | 1,928.16 TL / 1 kg | **Out of stock** |
| [Bedrock Ultrafuse TPU 85A Naturel Filament 1.75mm 750 gr](https://www.robotistan.com/bedrock-ultrafuse-tpu-85a-naturel-filament-175mm-750-gr) | Robotistan (TR) | 85A | not shown | **Out of stock** |
| [Porima TPU Flex 98A Filament](https://porima3d.com/products/porima-tpu-flex-esnek-98a-filament) | Porima, the maker (TR) | 98A | 884.16 TL / 1 kg | **Out of stock** (all 6 colours) |
| [Porima Easy Flex Filament](https://porima3d.com/products/porima-easy-flex-filament) | Porima, the maker (TR) | not stated | 846.72 TL / 0.5 kg | **Out of stock** |

<details><summary>Notes on the TPU filament</summary>

- **Porima 98A, black (Robotistan):** the default pick. Porima is a Turkish maker. Hotend 220–240 °C, bed 50–70 °C. About 1,318 TL per kg. The page carries a "Tükendi" (sold out) box, but it is hidden; the listing data and the add-to-cart button say in stock.
- **Porima 98A, 1 kg (n11):** the same maker on a 1 kg spool, and the cheapest 98A per kg.
- **Filamix 95A (idefix):** the softest grade in stock. Nozzle 210–250 °C, bed 40–60 °C. Origin not stated.
- **White spools (3D Ultra, Robotistan):** in stock, but white TPU turns yellow and shows skin oil, so they are not for the top. The other Beta 95A colours on 3D Ultra were sold out.
- **Softer grades (eSUN 87A, Ultrafuse 85A):** out of stock. They feel softer, but are tackier and need a direct-drive extruder.
- **Porima's own shop:** every TPU listing was out of stock. It describes its flexible range as Shore 94A–98A; the Easy Flex hardness is not stated. Buy Porima through the resellers above.
- **Unsure whether a black TPU conducts?** Print a small scrap and measure it with a multimeter: it should read open (MΩ or more).

</details>

## Could not be checked

> [!NOTE]
> **Could not be checked:** these listings were not verified.
>
> - **Mouser** lists the trackpad as TPS65-201A-S, but its page blocked automated access, so that listing is *unverified*.
> - **DigiKey** lists the same part as obsolete.
> - **Tayda, Botland, supermagnete** and a few other shops also blocked the check.
> - **AliExpress** shows prices only in a browser.
> - **Contact cement** (optional, for a permanent TPU insert): the Koçtaş and Çiçeksepeti listings blocked the check on 2026-11-18. It is a common hardware-store item, for example Pattex or UHU Kontakt.
