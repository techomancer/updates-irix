#!/bin/bash
# build_irix.sh - Build modern tcsh 6.24.16 for SGI IRIX 6.5.22m
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
IRIX_SH="/home/dbehr/gits/iris/tools/irix-sh.py"

mkdir -p "$SCRIPT_DIR/build"

echo "=== Building tcsh 6.24.16 in IRIX guest ==="
cat << 'EOF' > "$SCRIPT_DIR/build/guest_build.sh"
#!/bin/sh
set -e
WORK=/tmp/tcsh_build
SHARED=/shared/updates-irix/tcsh

rm -rf "$WORK"
mkdir -p "$WORK"

echo "--- Staging sources to local /tmp ---"
cp -r "$SHARED/tcsh"/* "$WORK/"

cd "$WORK"

echo "--- Applying IRIX patches ---"
for p in "$SHARED"/patches/*.patch; do
    if test -f "$p"; then
        echo "Applying $(basename "$p")..."
        patch -p1 < "$p"
    fi
done

echo "--- Configuring tcsh for IRIX 6.5 N32 MIPS4 ---"
CC="cc -n32 -mips4" CFLAGS="-O3" LDFLAGS="-n32 -mips4" ./configure --prefix=/usr --disable-nls-catalogs

echo "--- Building tcsh with MIPSpro ---"
make BUILD_CATALOGS=no

echo "--- Verifying tcsh ---"
./tcsh -c 'echo $version'
./tcsh -c 'builtins' >/dev/null
./tcsh -c 'bindkey -l' >/dev/null

echo "--- Copying binary to shared build directory ---"
cp "$WORK/tcsh" "$SHARED/build/tcsh"
echo "=== tcsh build completed successfully ==="
EOF

chmod +x "$SCRIPT_DIR/build/guest_build.sh"

"$TOP_DIR/guest_run.sh" --timeout 600 tcsh \
    "cp /shared/updates-irix/tcsh/build/guest_build.sh /tmp/guest_build_tcsh.sh && chmod a+x /tmp/guest_build_tcsh.sh && /bin/sh /tmp/guest_build_tcsh.sh 2>&1"

echo ">>> tcsh 6.24.16 build complete: $SCRIPT_DIR/build/tcsh"
