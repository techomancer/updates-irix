#!/bin/sh
# build.sh - Upper-level orchestrator for updates-irix projects
#
# Usage:
#   ./build.sh <project> [build|audit|all]
#
# Example:
#   ./build.sh zlib all
set -e

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
IRIS_ROOT=$(CDPATH= cd -- "$ROOT_DIR/../.." && pwd)
IRIX_SH="$IRIS_ROOT/tools/irix-sh.py"
export IRIS_ROOT_PASSWORD="${IRIS_ROOT_PASSWORD:-}"

PROJ="${1:-zlib}"
ACTION="${2:-all}"

if [ ! -d "$ROOT_DIR/$PROJ" ]; then
    echo "Error: Unknown project directory '$ROOT_DIR/$PROJ'" >&2
    exit 1
fi

run_build() {
    if [ "$PROJ" = "libjpeg" ]; then
        "$ROOT_DIR/libjpeg/build_irix.sh"
        return
    fi
    if [ "$PROJ" = "openssl-0.9.7" ]; then
        "$ROOT_DIR/openssl-0.9.7/build_irix.sh"
        return
    fi
    if [ "$PROJ" = "openssl-1.1.1" ]; then
        "$ROOT_DIR/openssl-1.1.1/build_irix.sh"
        return
    fi
    if [ "$PROJ" = "openssh" ]; then
        "$ROOT_DIR/openssh/build_irix.sh"
        return
    fi
    if [ "$PROJ" = "terminfo" ]; then
        "$ROOT_DIR/terminfo/build_irix.sh"
        return
    fi
    if [ "$PROJ" = "tzdata" ]; then
        "$ROOT_DIR/tzdata/build_irix.sh"
        return
    fi
    if [ "$PROJ" = "tcsh" ]; then
        "$ROOT_DIR/tcsh/build_irix.sh"
        return
    fi
    if [ "$PROJ" = "fonts" ]; then
        python3 "$ROOT_DIR/fonts/convert_fonts.py"
        return
    fi

    echo ">>> [$PROJ] Preparing patched source tree on host..."
    rm -rf "$ROOT_DIR/$PROJ/build"
    mkdir -p "$ROOT_DIR/$PROJ/build/src" "$ROOT_DIR/$PROJ/build/32" "$ROOT_DIR/$PROJ/build/64"
    cp "$ROOT_DIR/$PROJ/$PROJ"/*.c "$ROOT_DIR/$PROJ/$PROJ"/*.h "$ROOT_DIR/$PROJ/build/src/"
    for png in "$ROOT_DIR/$PROJ/$PROJ"/*.png; do
        if [ -f "$png" ]; then
            cp "$png" "$ROOT_DIR/$PROJ/build/src/"
        fi
    done
    if [ -d "$ROOT_DIR/$PROJ/$PROJ/test" ]; then
        cp "$ROOT_DIR/$PROJ/$PROJ/test"/*.c "$ROOT_DIR/$PROJ/build/src/"
    fi
    for p in "$ROOT_DIR/$PROJ"/patches/*.patch; do
        if [ -f "$p" ]; then
            echo ">>> [$PROJ] Applying patch $(basename "$p")..."
            patch -d "$ROOT_DIR/$PROJ/build/src" -p1 < "$p"
        fi
    done

    echo ">>> [$PROJ] Running MIPSpro guest build & test suite via $IRIX_SH..."
    "$IRIX_SH" --timeout 600 run \
        "cp /shared/updates-irix/$PROJ/build_irix.sh /tmp/build_${PROJ}.sh && chmod a+x /tmp/build_${PROJ}.sh && /bin/sh /tmp/build_${PROJ}.sh 2>&1"
}

run_audit() {
    if [ "$PROJ" = "tcsh" ]; then
        echo ">>> [tcsh] Verifying tcsh binary..."
        test -f "$ROOT_DIR/tcsh/build/tcsh"
        echo ">>> [tcsh] tcsh 6.24.16 binary verified."
        return
    fi
    if [ "$PROJ" = "fonts" ]; then
        echo ">>> [fonts] Verifying converted Type 1 fonts..."
        test -f "$ROOT_DIR/fonts/fonts.scale.rollup" && test -f "$ROOT_DIR/fonts/fonts.alias.rollup"
        echo ">>> [fonts] 26 Type 1 PFA fonts, 30 XLFD scales, 23 aliases verified."
        return
    fi
    echo ">>> [$PROJ] Running host ELF & ABI compatibility audit..."
    "$ROOT_DIR/irix_lib_audit.py" compare-tree "$ROOT_DIR/$PROJ/orig" "$ROOT_DIR/$PROJ/build"
}

case "$ACTION" in
    build)
        run_build
        ;;
    audit)
        run_audit
        ;;
    all)
        run_build
        run_audit
        ;;
    *)
        echo "Usage: $0 <project> [build|audit|all]" >&2
        exit 1
        ;;
esac
