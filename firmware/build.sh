#!/usr/bin/env bash
# Yakamoz + Azoteq TPS65 ("ithalat") firmware: reproducible, docker-only build.
#
# What it does (everything except the final copy runs inside ghcr.io/qmk/qmk_cli):
#   1. clones/updates qmk/qmk_firmware (shallow, with submodules) into $WORK_DIR/qmk_firmware
#   2. fetches keyboards/yakamoz from the Ardakilic/qmk_firmware fork (pinned commit)
#      -> the fork is NOT used as the build tree (its ChibiOS submodules are stale, see README)
#   3. fetches the original 'ardakilic' keymap from Ardakilic/qmk_userspace (pinned commit) as baseline
#   4. copies this repo's keymap(s) from firmware/qmk_userspace/keyboards/yakamoz/keymaps/
#   5. runs `qmk compile -kb yakamoz -km <keymap>` for every keymap in $KEYMAPS
#   6. copies the resulting .uf2 files to $OUT_DIR and prints the firmware sizes
#
# Idempotent: re-running reuses the clone, resets it to $QMK_REF, re-copies the keyboard and keymaps.
# Nothing is installed on the host; the only host requirements are bash and docker.
#
# Usage:
#   ./build.sh                                   # build both keymaps against upstream master
#   QMK_REF=<sha|branch|tag> ./build.sh           # pin QMK (recommended for reproducibility)
#   KEYMAPS=ardakilic_trackpad ./build.sh         # only the trackpad keymap
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
FORK_REPO="${FORK_REPO:-https://github.com/Ardakilic/qmk_firmware.git}"
FORK_REF="${FORK_REF:-7bed308a04e06ea586efa9d9b6ec553903594edb}"            # fork master, 2026-09-24
USERSPACE_REPO="${USERSPACE_REPO:-https://github.com/Ardakilic/qmk_userspace.git}"
USERSPACE_REF="${USERSPACE_REF:-ef35653599766e6cb1c834cd192c3e39d69dd623}"  # userspace main, 2026-03-29
KEYMAPS="${KEYMAPS:-ardakilic ardakilic_trackpad}"
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
echo "== keyboard:  $FORK_REPO @ $FORK_REF (keyboards/yakamoz)"
echo "== baseline:  $USERSPACE_REPO @ $USERSPACE_REF (keyboards/yakamoz/keymaps/ardakilic)"
echo "== keymaps:   $KEYMAPS"

# The container runs as the calling user so that files in the bind mounts stay owned by them.
docker run --rm \
    --user "$(id -u):$(id -g)" \
    -e HOME=/tmp/home \
    -e QMK_REPO="$QMK_REPO" -e QMK_REF="$QMK_REF" \
    -e FORK_REPO="$FORK_REPO" -e FORK_REF="$FORK_REF" \
    -e USERSPACE_REPO="$USERSPACE_REPO" -e USERSPACE_REF="$USERSPACE_REF" \
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
    if [ ! -d "$dir/.git" ]; then
        git init -q "$dir"
        git -C "$dir" remote add origin "$repo"
    fi
    git -C "$dir" remote set-url origin "$repo"
    if [ "$#" -gt 0 ]; then
        git -C "$dir" sparse-checkout set --no-cone "$@"
        git -C "$dir" fetch -q --depth 1 --filter=blob:none origin "$ref"
    else
        git -C "$dir" fetch -q --depth 1 origin "$ref"
    fi
    git -C "$dir" checkout -q -f FETCH_HEAD
    git -C "$dir" clean -ffdq
}

echo "== [1/5] qmk_firmware"
fetch_ref /work/qmk_firmware "$QMK_REPO" "$QMK_REF"
git -C /work/qmk_firmware submodule sync -q --recursive
git -C /work/qmk_firmware submodule update -q --init --recursive --depth 1 --jobs 8
QMK_SHA="$(git -C /work/qmk_firmware rev-parse HEAD)"
echo "   qmk_firmware HEAD: $QMK_SHA ($(git -C /work/qmk_firmware log -1 --format=%cs))"
git -C /work/qmk_firmware submodule status | sed "s/^/   /"

echo "== [2/5] keyboards/yakamoz from the fork"
fetch_ref /work/src_fork "$FORK_REPO" "$FORK_REF" "/keyboards/yakamoz/"
rm -rf /work/qmk_firmware/keyboards/yakamoz
cp -R /work/src_fork/keyboards/yakamoz /work/qmk_firmware/keyboards/yakamoz
# The fork already ships keyboard.json (current QMK only detects keyboards that have one,
# lib/python/qmk/path.py). Fall back to renaming info.json if an older definition is used.
if [ ! -f /work/qmk_firmware/keyboards/yakamoz/keyboard.json ] && [ -f /work/qmk_firmware/keyboards/yakamoz/info.json ]; then
    echo "   NOTE: renaming info.json -> keyboard.json in the build copy"
    mv /work/qmk_firmware/keyboards/yakamoz/info.json /work/qmk_firmware/keyboards/yakamoz/keyboard.json
fi
# The fork keymaps (default, default_trackball, vial) are not built here; drop them so that only the
# keymaps under test exist in the build tree.
rm -rf /work/qmk_firmware/keyboards/yakamoz/keymaps
mkdir -p /work/qmk_firmware/keyboards/yakamoz/keymaps

echo "== [3/5] baseline keymap ardakilic from qmk_userspace"
fetch_ref /work/src_userspace "$USERSPACE_REPO" "$USERSPACE_REF" "/keyboards/yakamoz/keymaps/ardakilic/"
cp -R /work/src_userspace/keyboards/yakamoz/keymaps/ardakilic /work/qmk_firmware/keyboards/yakamoz/keymaps/ardakilic

echo "== [4/5] keymaps from this repo"
for km in /userspace/keyboards/yakamoz/keymaps/*/; do
    [ -d "$km" ] || continue
    name="$(basename "$km")"
    if [ "$name" = "ardakilic" ]; then
        echo "   WARNING: local keymaps/ardakilic overrides the fetched baseline"
        rm -rf /work/qmk_firmware/keyboards/yakamoz/keymaps/ardakilic
    fi
    cp -R "$km" "/work/qmk_firmware/keyboards/yakamoz/keymaps/$name"
    echo "   + $name"
done

echo "== [5/5] compile"
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
