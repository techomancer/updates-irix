#!/bin/bash
# guest_run.sh - Run guest commands with isolated sandbox NFS staging
#
# Usage:
#   ./guest_run.sh [--timeout <sec>] <project> <command_to_run_in_guest>
#
# If guest/shared exists, stages the project working tree into guest/shared/updates-irix/<project>
# (strictly excluding .git), runs the command via irix-sh.py, and pulls back build/ artifacts.
set -e

TOP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GUEST_SHARED_BASE="$TOP_DIR/guest/shared"
GUEST_SHARED_DIR="$GUEST_SHARED_BASE/updates-irix"

TIMEOUT=900
if [ "$1" = "--timeout" ]; then
    TIMEOUT="$2"
    shift 2
fi

PROJ="$1"
CMD="$2"

if [ -z "$PROJ" ] || [ -z "$CMD" ]; then
    echo "Usage: $0 [--timeout <sec>] <project> <guest_command>" >&2
    exit 1
fi

IRIS_SH="${IRIX_SH:-}"
if [ -z "$IRIS_SH" ] || [ ! -x "$IRIS_SH" ]; then
    if [ -x "$TOP_DIR/../iris/tools/irix-sh.py" ]; then
        IRIS_SH="$TOP_DIR/../iris/tools/irix-sh.py"
    elif [ -x "/home/dbehr/gits/iris/tools/irix-sh.py" ]; then
        IRIS_SH="/home/dbehr/gits/iris/tools/irix-sh.py"
    else
        echo "Error: Cannot find irix-sh.py in ../iris/tools/ or /home/dbehr/gits/iris/tools/" >&2
        exit 1
    fi
fi
export IRIS_ROOT_PASSWORD="${IRIS_ROOT_PASSWORD:-p00pp00p}"

if [ -d "$GUEST_SHARED_BASE" ]; then
    echo ">>> [sandbox] Staging '$PROJ' into isolated guest/shared (excluding .git)..."
    mkdir -p "$GUEST_SHARED_DIR/$PROJ"

    # Sync project files into sandbox (never expose .git)
    rsync -a --delete \
        --exclude='.git' \
        --exclude='*.swp' \
        --exclude='*~' \
        "$TOP_DIR/$PROJ/" "$GUEST_SHARED_DIR/$PROJ/"

    # Sync dependencies if required by project
    if [ "$PROJ" = "libpng" ] || [ "$PROJ" = "libtiff" ] || [ "$PROJ" = "openssh" ]; then
        if [ -d "$TOP_DIR/zlib/build" ]; then
            mkdir -p "$GUEST_SHARED_DIR/zlib"
            rsync -a "$TOP_DIR/zlib/build" "$GUEST_SHARED_DIR/zlib/"
        fi
    fi
    if [ "$PROJ" = "libtiff" ]; then
        if [ -d "$TOP_DIR/libjpeg/build" ]; then
            mkdir -p "$GUEST_SHARED_DIR/libjpeg"
            rsync -a "$TOP_DIR/libjpeg/build" "$GUEST_SHARED_DIR/libjpeg/"
        fi
    fi
    if [ "$PROJ" = "openssh" ]; then
        if [ -d "$TOP_DIR/openssl-1.1.1/build" ]; then
            mkdir -p "$GUEST_SHARED_DIR/openssl-1.1.1"
            rsync -a "$TOP_DIR/openssl-1.1.1/build" "$GUEST_SHARED_DIR/openssl-1.1.1/"
        fi
    fi

    echo ">>> [sandbox] Executing guest command in isolated sandbox..."
    "$IRIS_SH" --timeout "$TIMEOUT" run "$CMD"

    # Pull back build artifacts if created
    if [ -d "$GUEST_SHARED_DIR/$PROJ/build" ]; then
        echo ">>> [sandbox] Collecting build artifacts from guest/shared back to $PROJ/build..."
        mkdir -p "$TOP_DIR/$PROJ/build"
        rsync -a "$GUEST_SHARED_DIR/$PROJ/build/" "$TOP_DIR/$PROJ/build/"
    fi
else
    # Fallback to direct execution if guest/shared is not configured
    echo ">>> [direct] Executing guest command directly..."
    "$IRIS_SH" --timeout "$TIMEOUT" run "$CMD"
fi
