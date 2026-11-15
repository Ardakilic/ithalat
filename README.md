# ithalat - a wrist rest with a built-in trackpad for the Yakamoz keyboard

[![Preview (GitHub Pages)](https://github.com/Ardakilic/ithalat/actions/workflows/pages.yml/badge.svg)](https://github.com/Ardakilic/ithalat/actions/workflows/pages.yml)

**ithalat** is a parametric, 3D-printed wrist rest that sits flush against
the front of the [Yakamoz](https://github.com/ozkan/Yakamoz) keyboard, with an
**Azoteq TPS65** I2C trackpad (65 x 49 mm) built into its middle. You print it in a **glass**
variant (for the 1.1 mm glass overlay) or a **bare** variant, and you link it
to the keyboard with one of two connectors: a 5-pin **magnetic pogo** pair or a
cheap **USB-C breakout pair**. The rest is pluggable: it is not fixed to the
keyboard, and the firmware picks the trackpad up again when you plug it back
in. The trackpad shares the OLED's I2C bus, and the OLED keeps working.
Every dimension comes from one file, [`config.py`](config.py); nothing is
modelled by hand.

**[Open the live 3D preview](https://ardakilic.github.io/ithalat/)**

[![The ithalat live preview: the glass rest with the magnetic pogo connector in front of a Yakamoz keyboard](docs/preview.png)](https://ardakilic.github.io/ithalat/)

**Status: design stage.** The generated parts pass 365 automated geometry
checks, and the firmware compiles and passes simulated tests. No complete
ithalat build on a real Yakamoz (printed, wired and used) is documented yet,
so print one dock first as a fit test before you order everything.

## Contents

- [Live preview](#live-preview)
- [What "ithalat" means](#what-ithalat-means)
- [Built for Yakamoz](#built-for-yakamoz)
- [Features](#features)
- [What you need](#what-you-need)
- [Pick your connector](#pick-your-connector)
- [What to print](#what-to-print)
- [Quick start](#quick-start)
- [Wiring and where to buy](#wiring-and-where-to-buy)
- [Firmware](#firmware)
- [Building from source](#building-from-source)
- [How the online preview is built](#how-the-online-preview-is-built)
- [Safety notes](#safety-notes)
- [Documentation](#documentation)
- [Repository layout](#repository-layout)
- [Credits](#credits)
- [License](#license)

## Live preview

- **Online:** <https://ardakilic.github.io/ithalat/>. GitHub Actions rebuilds
  this page from source on every push, so it always matches the code in this
  repository.
- **What it shows:** all four combinations (glass or bare rest, magnetic pogo
  or USB-C connector), with x-ray, explode and section-cut views, the
  underside, filament colours, dimensions, the parts with their masses, the
  pinout and the print notes.
- **Offline:** open [`preview/index.html`](preview/index.html) in a browser
  after cloning. It is one file, but it loads three.js and the fonts from a
  CDN, so it needs an internet connection and WebGL.

## What "ithalat" means

*ithalat* is Turkish for "import". The project is named this way because,
since January 2026, people in Turkey cannot import anything internationally,
and all vendors have closed shipping to Turkey because of this.

## Built for Yakamoz

ithalat is an add-on for **[Yakamoz](https://github.com/ozkan/Yakamoz)**, the
50-key ortholinear keyboard designed by [ozkan](https://github.com/ozkan). Yakamoz
runs on a Raspberry Pi Pico with QMK and has an OLED display, hot-swap sockets
and an acrylic case. Its build guide is at <https://ozkancelik.com/yakamoz/>
and its QMK firmware at <https://github.com/ozkan/Yakamoz-qmk>. All credit for
the keyboard goes to its author.

- **You need a built Yakamoz.** ithalat is only the wrist rest, the trackpad
  link and a keymap; it is not a keyboard.
- **The case is not modified.** You pull the two centre switches of the front
  (bottom) row, SW44 and SW43, and a printed dock clips into their switch
  cut-outs. You take off the OLED cover to run four wires under it; nothing is
  cut, filed or drilled, and you can undo it all.
- **Yakamoz has its own license.** Per its Readme, the Yakamoz keyboard is
  licensed under
  [Creative Commons Attribution-NonCommercial 4.0 International](https://creativecommons.org/licenses/by-nc/4.0/)
  (CC BY-NC 4.0), and its PCB design can be freely reproduced, modified and
  manufactured for personal use.

## Features

- **Parametric.** One source of truth, [`config.py`](config.py), for every
  dimension. Any constant can be overridden from the command line, and the
  parts regenerate in seconds.
- **Ergonomic shape.** A crowned, crease-free top modelled on a classic walnut
  keyboard rest. The back edge and the trackpad sit level with the switchplate
  (11.8 mm), so your thumbs slide from the front row onto the pad without a
  step, and the front drops to 6.5 mm to keep your wrists low.
- **Trackpad pocket.** The TPS65 drops in from the top onto a flat ledge, with
  its surface 0.15 mm below the rim. No glue and no screws; two holes from
  below push it out again.
- **Glass or bare.** One rest STL per variant: for the 1.1 mm glass overlay,
  or for the bare module (or a thin film).
- **Two connectors.** Magnetic pogo (snaps on, breaks away safely) or a USB-C
  breakout pair (cheapest, no magnets near the pad). Same rest, same wiring
  inside the keyboard, same firmware.
- **Pluggable and hot-plug aware.** The keymap re-detects a re-plugged pad
  within about 1.3 s; stock QMK only looks for it at boot.
- **OLED keeps working.** The trackpad (0x74) shares the OLED's (0x3C) I2C bus
  on GP2/GP3, and the OLED shows `Pad: on` / `Pad: --`.
- **No case modification.** The dock clips into the two empty switch cut-outs
  and can be removed again.
- **Hidden cable.** A short pigtail runs from the trackpad through an internal
  channel and leaves through a notch in the back-top edge, right below the
  dock, so it is never pinched between the rest and the keyboard.
- **Optional ballast and bumpers.** Pockets for two steel bars (about 122 g)
  keep the light rest from sliding; six recesses take silicone bumpers.
- **Self-checking.** `make verify` measures the generated meshes: the default
  build passes 365 checks, with 5 advisory warnings.
- **Reproducible.** Everything runs in a pinned Docker image, and the STLs
  reproduce byte for byte on the same CPU architecture.

## What you need

The full list, with part numbers, alternatives and costs, is in
[docs/bom.md](docs/bom.md). In short:

- **A built Yakamoz keyboard** and a switch puller (the switches are hot-swap).
- **An Azoteq TPS65 trackpad module** (for example keycapsss KC10195_65,
  variant "TPS65"). It is a **3.3 V only** part. Add the 65 x 49 x 1.1 mm
  glass overlay for the glass variant. No Turkish shop that was checked sells
  the TPS65 or its glass ([where to buy](wiring.md#shared-parts-both-connectors)).
- **One connector:**
  - **Magnetic pogo:** a 5-pin, 2.54 mm, N/S-keyed magnetic pogo pair
    (Adafruit 5413 / MG005, a generic pair, the Motorobit set, or the DIY
    version in [docs/bom.md §7](docs/bom.md#7-cheaper-magnetic-options)).
  - **USB-C:** a female and a male 4-pad USB-C breakout board, a Schottky
    diode (1N5817, 1N5819 or SS14), **4 x M2x4 self-tapping screws** and
    **2-part epoxy**.
- **Wire and consumables:** very flexible 28 AWG and 30 AWG silicone wire,
  a short braided sleeve, heat-shrink and Kapton tape.
- **Filament:** PETG (recommended, especially for the docks) or PLA. It must be
  **non-conductive**: no carbon-fibre or metal fill near the trackpad.
- **Optional:** two 78 x 20 x 5 mm steel bars as ballast, and six Ø10 mm
  silicone bumpers 0.6 mm taller than the keyboard's own.
- **Tools:** a fine-tip soldering iron, a multimeter, flush cutters and a
  wire stripper.

## Pick your connector

The rest links to the keyboard through one of two connectors. Both carry the
same four I2C wires, use the same taps inside the keyboard and run the same
firmware. Both work with the same rest STL. Only the dock and the parts at the
end of the pigtail differ.

| | **Magnetic pogo** (default) | **USB-C breakout pair** |
|---|---|---|
| Keyboard half | flat-pad half of a 5-pin magnetic pogo pair, pressed into the pogo dock | blue **female** USB-C breakout board, captured in the USB-C dock behind a chamfered well |
| Rest half | spring-pin plug on a short pigtail | green **male** USB-C breakout board inside a printed **grip** |
| Parts cost | US$6.95 (Adafruit 5413), US$1–4 generic, 216 TL (Motorobit), about 58–78 TL DIY ([bom.md §7](docs/bom.md#7-cheaper-magnetic-options)) | about US$0 with the boards you own; a new pair is about 57 TL in Turkey (Motorobit) or US$2–5 abroad, plus a Schottky diode (cents) |
| Plugging in | snaps on by itself and self-aligns: **5/5** | a firm, straight push (5–20 N) while your other hand steadies the keyboard: **about 3/5** |
| Unplugging | lets go at a few newtons | 8–20 N: brace a fingertip on the dock face and pull the grip straight back |
| Breakaway | **yes**: a snag or moving the rest just pops it off | **no**: unplug before you move the rest, or it drags the keyboard along |
| RDY wire | yes (optional pin 5) | no; the firmware works without it (it times its reads to the pad's report window), RDY only avoids clock-stretching waits on the shared bus |
| Metal near the pad | two magnets about 7.35 mm from the module (accepted; verify warns) | no magnets; the plug shell sits about 13 mm from the module and the male board's copper pads about 5.5 mm (verify notes both as advisories) |
| Contacts | exposed flat pads on the dock face; the magnets pick up steel debris | recessed in the receptacle; GND mates first |
| Mix-up risk | none: nothing else fits it | the dock socket looks like a USB port. A series Schottky diode protects the keyboard; label both halves "NOT USB" |
| Rated cycles | 20,000 | 10,000 |
| Print | rest + `stl/ithalat-dock-pogo.stl` | rest + `stl/ithalat-dock-usbc.stl` + `stl/ithalat-usbc-grip-top.stl` + `stl/ithalat-usbc-grip-bottom.stl` + `stl/ithalat-usbc-retainer.stl` |
| Parts list | [bom.md §2a](docs/bom.md#2a-magnetic-pogo-connector) | [bom.md §2b](docs/bom.md#2b-usb-c-connector) |
| Wiring | [wiring.md §3.5](wiring.md#35-magnetic-pogo-solder-the-receptacle-and-fit-the-dock), [§4](wiring.md#4-wrist-rest-side-step-by-step) | [wiring.md §7](wiring.md#7-usb-c-variant) |

The rest is `stl/ithalat-glass.stl` or `stl/ithalat-bare.stl`, whichever
matches your trackpad, for either connector.

**Choose the pogo** if the rest should come and go with one hand and break away
safely when something snags. **Choose USB-C** if you already own the breakout
boards, want the cheapest build or want no magnets near the pad, and you accept
a two-handed plug-in. With USB-C, always hold the grip, never the wires, and
plug and pull in a straight line ([wiring.md §7.8](wiring.md#78-plugging-and-unplugging)).

## What to print

The STLs in [`stl/`](stl/) are committed and always match the default
configuration. They are already in their print orientation.

| STL | Magnetic pogo | USB-C | What it is |
|---|:---:|:---:|---|
| [`ithalat-glass.stl`](stl/ithalat-glass.stl) **or** [`ithalat-bare.stl`](stl/ithalat-bare.stl) | yes | yes | the rest, for the TPS65 with or without the glass overlay |
| [`ithalat-dock-pogo.stl`](stl/ithalat-dock-pogo.stl) | yes | | keyboard dock that holds the pogo receptacle |
| [`ithalat-dock-usbc.stl`](stl/ithalat-dock-usbc.stl) | | yes | keyboard dock that holds the female USB-C board |
| [`ithalat-usbc-retainer.stl`](stl/ithalat-usbc-retainer.stl) | | yes | holds the female board down and locks the dock's clips (2 x M2x4) |
| [`ithalat-usbc-grip-top.stl`](stl/ithalat-usbc-grip-top.stl) | | yes | upper half of the grip around the male board |
| [`ithalat-usbc-grip-bottom.stl`](stl/ithalat-usbc-grip-bottom.stl) | | yes | lower half of the grip (2 x M2x4) |

The USB-C build also needs **4 x M2x4 self-tapping pan-head screws** (two for
the retainer, two for the grip) and **2-part epoxy** for the plug shell in the
grip. The rest and the pogo dock need no screws.

Key print settings: no supports; print as exported (the rest bottom down, the
docks upside down); 0.12–0.16 mm layers; PETG for the docks, because their
snap blades bend across the layer lines. Print one dock first as a fit test.
The full table is in [docs/reference.md, Printing](docs/reference.md#printing).

## Quick start

1. **Pick your connector:** [magnetic pogo or USB-C](#pick-your-connector).
2. **Buy the parts** for that connector: [docs/bom.md](docs/bom.md), with
   example links in [where to buy](wiring.md#example-parts-and-where-to-buy).
   If you use USB-C boards, measure them and regenerate first
   ([wiring.md §7.4](wiring.md#74-prepare-the-breakout-boards)).
3. **Print** the rest variant that matches your trackpad and the parts for your
   connector ([What to print](#what-to-print)).
4. **Wire it:** keyboard side, connector half and dock, then the pigtail in the
   rest. Follow [wiring.md](wiring.md); the short version is the
   [assembly order](docs/reference.md#assembly-order).
5. **Flash the firmware:** the `ardakilic_trackpad` QMK keymap
   ([Firmware](#firmware)).
6. **Test before you power it, then plug in:** run the beep test
   ([pogo: wiring.md §6](wiring.md#6-test-procedure),
   [USB-C: wiring.md §7.7](wiring.md#77-test-procedure-usb-c)), plug the pad in
   before the first power-up, wait for `Pad: on` on the OLED and do the
   [30-second calibration](firmware/README.md#calibration-30-seconds).

## Wiring and where to buy

**[wiring.md](wiring.md)** is the complete wiring guide for both connectors:
the pinout, the tap points inside the keyboard, soldering steps, electrical
notes and the test procedures. Diagrams:
[magnetic pogo](docs/wiring.svg) and [USB-C](docs/wiring-usbc.svg).

The signals at a glance:

| Signal | Pico pin | Magnetic pogo pin | USB-C breakout pad | TPS65 pad |
|---|---|---|---|---|
| SDA | GP2 (pin 4) | 1 | D+ | SDA |
| 3V3 | 3V3(OUT) (pin 36), **never 5 V** | 2 | V, through a series Schottky diode | VDDHI |
| GND | GND | 3 | G | GND |
| SCL | GP3 (pin 5) | 4 | D− | SCL |
| RDY (optional) | GP15 (pin 20) | 5 | none | RDY |

Example parts, including USB-C breakout boards and magnetic pogo connectors,
with links: **[where to buy](wiring.md#example-parts-and-where-to-buy)**. The
full bill of materials with costs per connector is in
[docs/bom.md](docs/bom.md).

## Firmware

The firmware is a QMK keymap, `ardakilic_trackpad`, in
[`firmware/`](firmware/). It is the same for both connectors. Details,
calibration and the test checklist are in
**[firmware/README.md](firmware/README.md)**.

- **What it adds:** the Azoteq TPS65 through QMK's `azoteq_iqs5xx` pointing
  driver on the OLED's I2C bus. A one-finger tap is a left click, a two-finger
  tap a right click, and press-and-hold drags. Two fingers scroll. The pad
  takes over the mouse buttons (`MS_BTN1`/`MS_BTN2`) of the two removed
  switches, and their SODA-layer functions are copied to other keys.
- **Hot-plug:** the keymap notices when the pad is plugged in or out and
  re-initialises it ([details](firmware/README.md#hot-plug-behaviour-and-limits)).
- **Prebuilt images:** [`firmware/build/yakamoz_ardakilic_trackpad.uf2`](firmware/build/yakamoz_ardakilic_trackpad.uf2)
  (with the trackpad) and [`firmware/build/yakamoz_ardakilic.uf2`](firmware/build/yakamoz_ardakilic.uf2)
  (the baseline `ardakilic` keymap without it). To flash, double-tap reset (or
  use `QK_BOOT` on the SODA layer) and drop the `.uf2` onto the `RPI-RP2`
  drive.
- **Build it yourself (Docker only):** `cd firmware && ./build.sh`. It builds
  inside the official `ghcr.io/qmk/qmk_cli` image against upstream QMK, with
  `keyboards/yakamoz` from [Ardakilic/qmk_firmware](https://github.com/Ardakilic/qmk_firmware)
  and the baseline keymap from [Ardakilic/qmk_userspace](https://github.com/Ardakilic/qmk_userspace).
  `./test.sh` (after `./build.sh`, which it reuses) runs the simulated
  trackpad scenario tests.
- **Status:** the firmware compiles cleanly and passes the simulated scenario
  tests, but it has not run on a real Yakamoz with a real TPS65 yet. Work
  through the [test checklist](firmware/README.md#test-checklist-after-flashing)
  after the first flash.

## Building from source

You only need this if you change the design or want to rebuild the STLs and
the preview. Only Docker and `make` are needed. Every command runs in the
pinned `ithalat-build` image (python:3.14-slim +
numpy/shapely/trimesh/manifold3d/matplotlib); nothing is installed on your
machine.

```sh
git clone https://github.com/Ardakilic/ithalat.git
cd ithalat
make all        # image -> generate -> verify -> preview
open preview/index.html   # macOS; xdg-open on Linux, or double-click the file
```

### Make targets

| Target | What it does |
|---|---|
| `make` / `make all` | `image`, `generate`, `verify`, `preview` in that order |
| `make image` | builds the `ithalat-build` Docker image from `Dockerfile` + `requirements.txt` |
| `make generate` | runs `generate.py`: writes `stl/*.stl` and `build/manifest.json`, prints sizes, volumes, triangle counts and the dimension summary |
| `make verify` | runs `tools/verify.py` on the STLs and the manifest; exits 1 on any failure |
| `make preview` | runs `tools/build_preview.py`: writes `preview/index.html` and `build/artifact.html` from the manifest |
| `make site` | assembles `_site/` the way GitHub Pages serves it (`preview/index.html` as `index.html`, the STLs in `stl/`, `.nojekyll`); run `make all` first |
| `make shell` | interactive shell in the build image (for debugging) |
| `make clean` | deletes `build/`, `_site/` and the `__pycache__` folders |
| `make distclean` | `clean`, plus the committed deliverables (`stl/ithalat-*.stl`, `preview/index.html`) |

Every target runs as your user (`-u $(id -u):$(id -g)`), so the outputs are not owned by root.

The build outputs (every STL, `build/manifest.json`, the coordinate frame and
the print orientations) are listed in
[docs/reference.md, Outputs](docs/reference.md#outputs).

### Overrides

```sh
make generate verify GEN_ARGS="--glass-t 0.7"            # thinner glass (e.g. Azoteq's 0.7 mm option)
make generate verify GEN_ARGS="--depth 90"               # deeper rest
make generate verify GEN_ARGS="--height 13 --depth 90 --connector pogo5"   # taller, deeper rest (pogo only: at 13 mm the USB-C grip no longer clears the rest)
make generate verify GEN_ARGS="--engrave-face top --no-ballast"
make generate verify GEN_ARGS="--set KEYBOARD_HEIGHT=12.2"   # re-measured keyboard: REST_HEIGHT and the dock follow
make generate verify GEN_ARGS="--connector usbc"         # only the USB-C dock and grip (plus the rests)
make generate verify GEN_ARGS="--connector pogo5 --connector jst_sh4"   # pogo dock + Qwiic / JST-SH dock
make generate verify GEN_ARGS="--set 'REST_PROFILE=[(0,11.8),(30,11.8),(85,6.0)]'"
make preview                                             # refresh the preview for the new build
```

**Connectors.** `CONNECTORS` in `config.py` lists the connector variants to
build. The default is `('pogo5', 'usbc')`, and the first entry is the one the
preview shows first. The names are `pogo5` (magnetic pogo), `usbc` (USB-C
breakout pair) and `jst_sh4` (Qwiic / JST-SH, still selectable). Each one
writes its own dock (`stl/ithalat-dock-pogo.stl`, `-usbc.stl`, `-jst.stl`), and
`usbc` also writes its grip parts. `--connector NAME` restricts the list for one
run and can be repeated. The old `--set DOCK_CONN_TYPE='jst_sh4'` still works:
on its own, it builds just that connector.

Flags: `--height` (REST_HEIGHT), `--depth`, `--width`, `--glass-t`,
`--tp-back-margin`, `--engrave-face bottom|top`, `--engrave-text`,
`--no-ballast`, `--no-dock`, `--connector NAME` (repeatable),
`--mesh-edge-len`. The repeatable `--set NAME=VALUE` sets **any** constant in
`config.py`; the value is a Python literal. Unknown names are rejected. Every
constant is listed in
[docs/reference.md, Configuration reference](docs/reference.md#configuration-reference).

- **Quote values that contain parentheses, quotes or spaces** inside `GEN_ARGS`, as in the last examples above.
- **Derived values are recomputed after the overrides**, unless you override them yourself. These are `REST_WIDTH`, `REST_HEIGHT`, `REST_BACK_HEIGHT`, `TP_CENTER_X`, `VARIANTS`, `CABLE_TUNNEL_H`, `CABLE_NOTCH_LEN`, `PLUG_BAY_L`, `DOCK_CENTER_X`, `DOCK_SWITCH_CENTER_Y`, `DOCK_PLATE_T`, `DOCK_UNDERPLATE_GAP`, `KB_X0`, `CABLE_NOTCH_X` and `PLUG_BODY` (the `DERIVED` table in `config.py`). For example, `--glass-t` really changes the glass pocket.
- **Pass the same `GEN_ARGS` to `generate` and `verify`.** `verify` measures the STLs in `stl/` against the config, so stale STLs fail.
- **Regenerate the defaults before committing:** `make generate verify preview` with no `GEN_ARGS`. The output is byte-identical for the same config and image.

### Verification in short

`make verify` measures the meshes themselves (ray casts, slices,
point-in-solid tests, signed distances): mesh health, sizes, the trackpad
pocket, the cable path, the plug clearance, the underside, every dock, the USB-C
parts and the assembled positions. The default build passes **365 checks with
5 advisory warnings** (the pogo plug magnets and the USB-C metal distances near
the pad). It exits 1 on any failure. The full list of checks is in
[docs/reference.md, Verification](docs/reference.md#verification).

### Pinned toolchain

The toolchain is pinned (Python 3.14, numpy 2.5.3, shapely 2.1.2, trimesh 5.1.0,
manifold3d 3.5.3, mapbox_earcut 2.1.0, matplotlib 3.11.2, plus rtree, scipy and
networkx for the verifier), so the STLs reproduce byte for byte on the same CPU
architecture. An x86_64 machine (such as the GitHub Actions runner) can split a
few triangles of an arm64-built STL along the other diagonal: same vertices,
volume and geometry, different bytes. To bump a pin, run `make all` and commit
the regenerated STLs together with the change.

## How the online preview is built

The page at <https://ardakilic.github.io/ithalat/> is built by GitHub Actions
from [`.github/workflows/pages.yml`](.github/workflows/pages.yml) on every
push to `main` (and on demand from the Actions tab). The workflow uses the same
Docker build image and `make` targets as a local build: `make image`, then
`make generate verify preview site`. It regenerates the parts and
`build/manifest.json`, runs the self-test, rebuilds the preview with
`tools/build_preview.py` and deploys it to GitHub Pages. **If
`tools/verify.py` fails, nothing is deployed** and the last good page stays up.
The job summary lists any regenerated file that differs from the committed copy.

- The site also serves the STLs, at
  `https://ardakilic.github.io/ithalat/stl/<file>.stl`. The STL links on the
  page itself download the committed files from this repository.
- The committed [`preview/index.html`](preview/index.html) is the same page for
  offline use.
- The badge at the top of this README shows the state of the last run.

If you fork the repository, enable Pages in **Settings > Pages** with
**Source: GitHub Actions**, and your fork publishes its own preview.

## Safety notes

- **Never plug the USB-C halves into real USB.** After the conversion, neither
  half is a USB port: the dock carries I2C and 3.3 V, not USB. The Schottky
  diode protects the keyboard from a charger's 5 V, but the grip on the rest has
  no protection: plugging it into a laptop, phone or charger can put 5 V on the
  trackpad and kill it. Label both halves **"NOT USB"**
  ([wiring.md §7.9](wiring.md#79-it-is-not-usb-labels-chargers-and-laptops)).
- **The TPS65 is a 3.3 V part** (3.6 V max). Power it from the Pico's 3V3(OUT)
  only, never from 5 V, VSYS or VBUS.
- **Solder with the keyboard unplugged** from USB, and beep-test the wiring
  before the first power-up.
- **Keep metal away from the pad:** no conductive or metal-filled filament, and
  no loose steel, magnets or coins within about 15 mm of the module. It does not
  damage anything, but it disturbs the capacitive sensing.
- **Pogo pads are exposed live contacts,** and the magnets pick up steel
  debris. The optional protection parts (TVS, series resistors, a PTC fuse) are
  in [wiring.md §5](wiring.md#5-electrical-notes) and
  [docs/bom.md §3](docs/bom.md#3-optional-protection-parts-keyboard-side-at-the-dock).

## Documentation

| Where | What |
|---|---|
| [wiring.md](wiring.md) (diagrams: [pogo](docs/wiring.svg), [USB-C](docs/wiring-usbc.svg)) | wiring, pinout, soldering steps, electrical notes, test procedure and [example parts with where to buy](wiring.md#example-parts-and-where-to-buy), for both connectors |
| [docs/bom.md](docs/bom.md) | bill of materials and costs, per connector |
| [docs/reference.md](docs/reference.md) | the detailed reference: [design rationale](docs/reference.md#design-rationale), [outputs](docs/reference.md#outputs), [verification](docs/reference.md#verification), [variants](docs/reference.md#variants), [the docks](docs/reference.md#the-docks), [configuration reference](docs/reference.md#configuration-reference), [printing](docs/reference.md#printing), [assembly order](docs/reference.md#assembly-order), [ballast and bumpers](docs/reference.md#ballast-and-bumpers), [glass handling](docs/reference.md#glass-handling), [troubleshooting](docs/reference.md#troubleshooting) |
| [firmware/README.md](firmware/README.md) | QMK keymap `ardakilic_trackpad` (azoteq_iqs5xx driver, hot-plug, calibration); the same firmware for both connectors |
| [preview/index.html](preview/index.html), [online](https://ardakilic.github.io/ithalat/) | interactive 3D preview of the assembly; switch between the glass/bare variants and the two connectors |

## Repository layout

| Path | Role |
|---|---|
| `config.py` | every dimension (single source of truth) |
| `generate.py` | CLI: builds all parts for every connector in `CONNECTORS`, writes STLs + `build/manifest.json` |
| `geometry/rest.py` | outline, C1 top surface, pocket, cable, underside |
| `geometry/dock.py` | keyboard docks (plugs, snap clips, connector pocket or USB-C well, wire paths) |
| `geometry/plug.py` | pigtail plug envelope (housing + strain relief) and the per-variant cable route |
| `geometry/connectors.py` | connector variants: ids, labels, per-connector config copies, pin tables, the pogo / JST hardware envelopes |
| `geometry/usbc.py` | USB-C variant: dock well, shoulder window with crush ribs and board pocket, screwed retainer with shell press ribs, lock prongs and diode cradle, grip clamshell (epoxy key groove, clamp ribs, collar), hardware boxes, retention and hold-down calculation, cable route to the male pads |
| `geometry/common.py`, `geometry/text.py`, `geometry/cfg.py` | helpers, engraving text (matplotlib TextPath), config loading/overrides |
| `tools/verify.py` | geometry and assembly self-test |
| `tools/build_preview.py`, `preview/template.html` | preview builder |
| `preview/index.html` | the built preview (committed) |
| `stl/` | the committed STLs for the default config |
| `wiring.md`, `docs/wiring.svg`, `docs/wiring-usbc.svg` | wiring guide and diagrams (pogo, USB-C) |
| `docs/bom.md` | bill of materials |
| `docs/preview.png` | screenshot of the live preview, shown at the top of this README (not regenerated by the build) |
| `docs/reference.md` | detailed reference (design, verification, config, printing, assembly, troubleshooting) |
| `firmware/` | QMK keymap `ardakilic_trackpad`, `build.sh`, `test.sh`, scenario tests, prebuilt `.uf2` images in `firmware/build/` |
| `.github/workflows/pages.yml` | GitHub Actions workflow that builds and deploys the online preview |
| `Dockerfile`, `requirements.txt`, `Makefile` | pinned build environment |
| `build/`, `_site/` | scratch outputs (git-ignored): the manifest and artifact page, and the Pages site from `make site` |

## Credits

- **[ozkan](https://github.com/ozkan)** for the [Yakamoz](https://github.com/ozkan/Yakamoz)
  keyboard that ithalat is built around. The keyboard dimensions come from its
  KiCad and DXF files.
- **Azoteq** for the TPS65 trackpad module and its IQS550 controller, the
  datasheets and the application notes (AZD068 for the metal keep-out).
- **[QMK](https://qmk.fm/)** for the firmware and its `azoteq_iqs5xx` pointing
  driver.
- **[three.js](https://threejs.org/)** for the 3D preview.
- **[trimesh](https://trimesh.org/), [manifold3d](https://github.com/elalish/manifold),
  [shapely](https://shapely.readthedocs.io/)**, numpy, scipy and matplotlib,
  which generate and verify the geometry.

## License

ithalat is a **non-commercial** project. The exact license text will be added
as a `LICENSE` file.

- **The hardware design is non-commercial.** This covers the generator
  (`config.py`, `generate.py`, `geometry/`, `tools/`), the STLs in `stl/`, the
  preview, `wiring.md`, the diagrams and the other docs. You may build, modify
  and share them for personal, non-commercial use, with attribution.
  Commercial use is not permitted: that includes selling printed parts, kits,
  assembled units or the files themselves.
- **`firmware/` is excluded.** It is QMK keymap code (Copyright ozkan and
  contributors) licensed under
  [GPL-2.0-or-later](https://github.com/qmk/qmk_firmware/blob/master/LICENSE),
  and the prebuilt `.uf2` images are built from QMK. The GPL governs their use,
  including commercial use; the non-commercial terms above do not apply to them.

These parts keep their own licenses:

- **Yakamoz keyboard:** the keyboard design by ozkan is licensed under
  [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/), per the
  [Yakamoz Readme](https://github.com/ozkan/Yakamoz).
- **Firmware:** GPL-2.0-or-later, as described above.
- **three.js:** the preview loads three.js (MIT license) from a CDN; it is not
  part of this repository.
