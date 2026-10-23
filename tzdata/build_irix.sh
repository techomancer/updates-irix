#!/bin/bash
# build_irix.sh - Build modern tzdata2026e & zic/zdump for SGI IRIX 6.5.22m
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
IRIX_SH="/home/dbehr/gits/iris/tools/irix-sh.py"

rm -rf "$SCRIPT_DIR/build"
mkdir -p "$SCRIPT_DIR/build/bin" "$SCRIPT_DIR/build/TZ"

cat << 'EOF' > "$SCRIPT_DIR/build/guest_build.sh"
#!/bin/sh
set -e
WORK=/tmp/tz_work
SHARED=/shared/updates-irix/tzdata

rm -rf "$WORK"
mkdir -p "$WORK/src" "$WORK/bin" "$WORK/TZ"

echo "--- Staging sources to local XFS /tmp ---"
cp "$SHARED/src"/* "$WORK/src/"

cd "$WORK/src"

echo "--- Compiling zic and zdump with MIPSpro c99 ---"
c99 -n32 -mips3 -O2 -DHAVE_STDINT_H=1 -DHAVE_INTTYPES_H=1 -DHAVE_SETENV=0 \
    -DREPORT_BUGS_TO='"tz@iana.org"' -woff 3604,3968 zic.c -o "$WORK/bin/zic"

c99 -n32 -mips3 -O2 -DHAVE_STDINT_H=1 -DHAVE_INTTYPES_H=1 -DHAVE_SETENV=0 \
    -DREPORT_BUGS_TO='"tz@iana.org"' -woff 3604,3968 zdump.c -o "$WORK/bin/zdump"

chmod +x "$WORK/bin/zic" "$WORK/bin/zdump"

echo "--- Compiling timezone files with zic -b fat ---"
cd "$WORK/src"
"$WORK/bin/zic" -b fat -d "$WORK/TZ" \
    africa antarctica asia australasia europe northamerica southamerica etcetera factory backward

echo "--- Copying source zone files and tables to TZ directory ---"
for tab in iso3166.tab zone.tab zone1970.tab zonenow.tab leapseconds \
           africa antarctica asia australasia backward etcetera europe factory northamerica southamerica \
           pacificnew solar87 solar88 solar89 systemv; do
    if test -f "$WORK/src/$tab"; then
        cp "$WORK/src/$tab" "$WORK/TZ/"
    fi
done

echo "--- Copying compiled binaries and TZ database to shared build ---"
cp "$WORK/bin/zic" "$WORK/bin/zdump" "$SHARED/build/bin/"
cp -r "$WORK/TZ"/* "$SHARED/build/TZ/"

echo "--- Verifying timezone operation in guest ---"
echo "Testing America/New_York:"
TZ="$WORK/TZ/America/New_York" date
echo "Testing Europe/London:"
TZ="$WORK/TZ/Europe/London" date
echo "Testing Asia/Tokyo:"
TZ="$WORK/TZ/Asia/Tokyo" date

echo "Testing zdump:"
"$WORK/bin/zdump" -v -c 2026,2027 "$WORK/TZ/America/New_York" | head -n 10

cd /tmp
rm -rf "$WORK"
echo "TZDATA_BUILD_SUCCESS"
EOF

chmod +x "$SCRIPT_DIR/build/guest_build.sh"

echo "=== Executing tzdata build inside IRIX guest ==="
"$IRIX_SH" --timeout 600 run "sh /shared/updates-irix/tzdata/build/guest_build.sh"

echo "========================================================="
echo "   tzdata2026e modernization completed successfully!     "
echo "========================================================="
