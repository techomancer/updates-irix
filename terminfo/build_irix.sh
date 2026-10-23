#!/bin/bash
# build_irix.sh - Orchestrate modern terminfo build & verification for SGI IRIX 6.5.22m
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
IRIX_SH="/home/dbehr/gits/iris/tools/irix-sh.py"

echo "=== 1. Generating modern terminfo source ==="
python3 "$SCRIPT_DIR/generate_terminfo.py"

rm -rf "$SCRIPT_DIR/build"
mkdir -p "$SCRIPT_DIR/build/terminfo"

cat << 'EOF' > "$SCRIPT_DIR/build/guest_build.sh"
#!/bin/sh
set -e
STAGE=/tmp/terminfo_build
SHARED=/shared/updates-irix/terminfo

echo "--- Compiling terminfo database ---"
rm -rf "$STAGE"
mkdir -p "$STAGE"
TERMINFO="$STAGE" tic "$SHARED/modern_terms.ti" 2>&1

echo "--- Copying compiled terminfo to shared build ---"
cp -r "$STAGE"/* "$SHARED/build/terminfo/"
rm -rf "$STAGE"

echo "--- Verifying compiled terminals in guest ---"
for t in xterm-256color screen-256color tmux-256color alacritty kitty foot rxvt-unicode-256color; do
    c=`TERMINFO="$SHARED/build/terminfo" TERM=$t tput colors 2>/dev/null || echo FAIL`
    echo "Terminal $t: $c colors"
done
echo "TERMINFO_BUILD_SUCCESS"
EOF

chmod +x "$SCRIPT_DIR/build/guest_build.sh"

echo "=== 2. Executing terminfo build & verification inside IRIX guest ==="
"$IRIX_SH" --timeout 300 run "sh /shared/updates-irix/terminfo/build/guest_build.sh"

echo "========================================================="
echo "   Terminfo modernization completed successfully!        "
echo "========================================================="
