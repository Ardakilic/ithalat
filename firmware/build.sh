#!/usr/bin/env bash
# Yakamoz + Azoteq TPS65 ("ithalat") firmware: reproducible, docker-only build.
#
# What it does (everything except the final copy runs inside ghcr.io/qmk/qmk_cli):
#   1. clones/updates qmk/qmk_firmware (shallow, with submodules) into $WORK_DIR/qmk_firmware
#   2. fetches the Yakamoz keyboard definition from ozkan's Yakamoz-qmk repo (pinned commit) and
#      copies it to keyboards/yakamoz (Yakamoz is not in upstream QMK)
#   3. copies this repo's keymap(s) from firmware/qmk_userspace/keyboards/yakamoz/keymaps/
#   4. runs `qmk compile -kb yakamoz -km <keymap>` for every keymap in $KEYMAPS
#   5. copies the resulting .uf2 files to $OUT_DIR and prints the firmware sizes
#
# Idempotent: re-running reuses the clone, resets it to $QMK_REF, re-copies the keyboard and keymaps.
# Nothing is installed on the host; the only host requirements are bash and docker.
#
# Usage:
#   ./build.sh                                   # build the ithalat keymap against upstream master
#   QMK_REF=<sha|branch|tag> ./build.sh           # pin QMK (recommended for reproducibility)
#   WORK_DIR=/some/scratch OUT_DIR=/some/out ./build.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---- parameters (override via environment) --------------------------------------------------
WORK_DIR="${WORK_DIR:-${TMPDIR:-/tmp}/yakamoz-qmk-build}"   # clone + build tree (kept OUTSIDE the repo)
OUT_DIR="${OUT_DIR:-$SCRIPT_DIR/build}"                       # where the .uf2 files end up
USERSPACE_DIR="${USERSPACE_DIR:-$SCRIPT_DIR/qmk_userspace}"   # this repo's userspace-style keymaps
QMK_IMAGE="${QMK_IMAGE:-ghcr.io/qmk/qmk_cli:latest}"
QMK_REPO="${QMK_REPO:-https://github.com/qmk/qmk_firmware.git}"
QMK_REF="${QMK_REF:-master}"
KB_REPO="${KB_REPO:-https://github.com/ozkan/Yakamoz-qmk.git}"            # ozkan's own QMK repo
KB_REF="${KB_REF:-d6b621203df789b1e4e60b1fd6343ee378c649f3}"              # its master, 2024-06-30
KB_PATH="${KB_PATH:-yakamoz}"                                              # keyboard folder in KB_REPO
KEYMAPS="${KEYMAPS:-ithalat}"
DOCKER_PULL="${DOCKER_PULL:-missing}"   # always | missing | never

command -v docker >/dev/null 2>&1 || { echo "error: docker is required" >&2; exit 1; }
[ -d "$USERSPACE_DIR/keyboards/yakamoz/keymaps" ] || { echo "error: $USERSPACE_DIR/keyboards/yakamoz/keymaps not found" >&2; exit 1; }

mkdir -p "$WORK_DIR" "$OUT_DIR"
WORK_DIR="$(cd "$WORK_DIR" && pwd)"
OUT_DIR="$(cd "$OUT_DIR" && pwd)"
USERSPACE_DIR="$(cd "$USERSPACE_DIR" && pwd)"

case "$DOCKER_PULL" in
    always) docker pull "$QMK_IMAGE" ;;
    missing) docker image inspect "$QMK_IMAGE" >/dev/null 2>&1 || docker pull "$QMK_IMAGE" ;;
    never) ;;
    *) echo "error: DOCKER_PULL must be always|missing|never" >&2; exit 1 ;;
esac

echo "== image:     $QMK_IMAGE"
echo "== work dir:  $WORK_DIR"
echo "== out dir:   $OUT_DIR"
echo "== qmk:       $QMK_REPO @ $QMK_REF"
echo "== keyboard:  $KB_REPO @ $KB_REF ($KB_PATH)"
echo "== keymaps:   $KEYMAPS"

# The container runs as the calling user so that files in the bind mounts stay owned by them.
docker run --rm \
    --user "$(id -u):$(id -g)" \
    -e HOME=/tmp/home \
    -e QMK_REPO="$QMK_REPO" -e QMK_REF="$QMK_REF" \
    -e KB_REPO="$KB_REPO" -e KB_REF="$KB_REF" -e KB_PATH="$KB_PATH" \
    -e KEYMAPS="$KEYMAPS" \
    -v "$WORK_DIR":/work \
    -v "$USERSPACE_DIR":/userspace:ro \
    -v "$OUT_DIR":/out \
    -w /work \
    "$QMK_IMAGE" bash -euo pipefail -c '
mkdir -p "$HOME"
git config --global --add safe.directory "*"
git config --global advice.detachedHead false
git config --global init.defaultBranch main

# fetch_ref <dir> <repo> <ref> [sparse paths...]: shallow checkout of one commit (sha, branch or tag)
fetch_ref() {
    local dir="$1" repo="$2" ref="$3"; shift 3
    # Another repo than last time: start over (a partial clone cannot switch its promisor remote).
    if [ -d "$dir/.git" ] && [ "$(git -C "$dir" remote get-url origin 2>/dev/null)" != "$repo" ]; then
        rm -rf "$dir"
    fi
    if [ ! -d "$dir/.git" ]; then
        git init -q "$dir"
        git -C "$dir" remote add origin "$repo"
    fi
    if [ "$#" -gt 0 ]; then
        git -C "$dir" sparse-checkout set --no-cone "$@"
        git -C "$dir" fetch -q --depth 1 --filter=blob:none origin "$ref"
    else
        git -C "$dir" fetch -q --depth 1 origin "$ref"
    fi
    git -C "$dir" checkout -q -f FETCH_HEAD
    git -C "$dir" clean -ffdq
}

echo "== [1/4] qmk_firmware"
fetch_ref /work/qmk_firmware "$QMK_REPO" "$QMK_REF"
git -C /work/qmk_firmware submodule sync -q --recursive
git -C /work/qmk_firmware submodule update -q --init --recursive --depth 1 --jobs 8
QMK_SHA="$(git -C /work/qmk_firmware rev-parse HEAD)"
echo "   qmk_firmware HEAD: $QMK_SHA ($(git -C /work/qmk_firmware log -1 --format=%cs))"
git -C /work/qmk_firmware submodule status | sed "s/^/   /"

echo "== [2/4] keyboards/yakamoz from $KB_REPO"
fetch_ref /work/src_keyboard "$KB_REPO" "$KB_REF" "/$KB_PATH/"
rm -rf /work/qmk_firmware/keyboards/yakamoz
cp -R "/work/src_keyboard/$KB_PATH" /work/qmk_firmware/keyboards/yakamoz
# Current QMK only detects keyboards that have a keyboard.json (lib/python/qmk/path.py).
# The definition in ozkan/Yakamoz-qmk still uses info.json (same schema), so rename it in the build copy.
if [ ! -f /work/qmk_firmware/keyboards/yakamoz/keyboard.json ] && [ -f /work/qmk_firmware/keyboards/yakamoz/info.json ]; then
    echo "   renaming info.json -> keyboard.json in the build copy"
    mv /work/qmk_firmware/keyboards/yakamoz/info.json /work/qmk_firmware/keyboards/yakamoz/keyboard.json
fi
# The stock keymaps there (default, default_trackball, vial*) still use keycodes that current QMK
# removed (RGB_xxx, KC_MS_BTN2), so they do not build any more. Drop them so that only the keymaps
# of this repo exist in the build tree.
rm -rf /work/qmk_firmware/keyboards/yakamoz/keymaps
mkdir -p /work/qmk_firmware/keyboards/yakamoz/keymaps

echo "== [3/4] keymaps from this repo"
for km in /userspace/keyboards/yakamoz/keymaps/*/; do
    [ -d "$km" ] || continue
    name="$(basename "$km")"
    cp -R "$km" "/work/qmk_firmware/keyboards/yakamoz/keymaps/$name"
    echo "   + $name"
done

echo "== [4/4] compile"
cd /work/qmk_firmware
export QMK_HOME=/work/qmk_firmware
qmk config user.qmk_home=/work/qmk_firmware >/dev/null
# Make sure the python deps match this qmk_firmware revision (ephemeral, inside the container only).
python3 -m pip install -q --user --disable-pip-version-check -r requirements.txt >/dev/null 2>&1 || true
rc=0
: > /work/sizes.txt
for km in $KEYMAPS; do
    echo "---- qmk compile -kb yakamoz -km $km"
    # Always start from fresh objects and never pick up a stale .uf2 from an earlier run.
    rm -rf ".build/obj_yakamoz_$km" ".build/yakamoz_$km".* "yakamoz_$km.uf2"
    ok=1
    qmk compile -kb yakamoz -km "$km" 2>&1 | tee "/work/compile_$km.log" || ok=0
    # QMK builds with -Werror; also refuse any warning that might slip through.
    if grep -q -E "\[ERRORS\]|\[WARNINGS\]|error:|warning:" "/work/compile_$km.log"; then ok=0; fi
    if [ "$ok" = 1 ] && [ -f "yakamoz_$km.uf2" ]; then
        cp "yakamoz_$km.uf2" "/out/yakamoz_$km.uf2"
        sz="$(arm-none-eabi-size ".build/yakamoz_$km.elf" | tail -1 | awk "{print \"text=\" \$1 \" data=\" \$2 \" bss=\" \$3}")"
        uf2="$(stat -c %s "yakamoz_$km.uf2")"
        echo "$km: $sz (bytes, arm-none-eabi-size); uf2 file ${uf2} bytes" | tee -a /work/sizes.txt
    else
        echo "!! $km FAILED (see $km log above)" | tee -a /work/sizes.txt
        rc=1
    fi
done
echo "== qmk_firmware: $QMK_SHA" | tee -a /work/sizes.txt
exit $rc
'

echo "== sizes"
cat "$WORK_DIR/sizes.txt"
echo "== artifacts in $OUT_DIR:"
ls -l "$OUT_DIR"/*.uf2 2>/dev/null || true
