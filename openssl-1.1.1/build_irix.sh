#!/bin/bash
# build_irix.sh - Orchestrate OpenSSL 1.1.1w Modernization for SGI IRIX 6.5.22m
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== 1. Staging source tree & generating guest script ==="
python3 "$SCRIPT_DIR/generate_build.py"

echo "=== 2. Executing build inside IRIX guest ==="
/home/dbehr/gits/iris/tools/irix-sh.py --timeout 7200 run "sh /shared/updates-irix/openssl-1.1.1/build/guest_build.sh"

echo "=== 3. Creating symlinks on host ==="
(cd "$SCRIPT_DIR/build/32" && ln -sf libcrypto.so.1.1 libcrypto.so && ln -sf libssl.so.1.1 libssl.so)
(cd "$SCRIPT_DIR/build/64" && ln -sf libcrypto.so.1.1 libcrypto.so && ln -sf libssl.so.1.1 libssl.so)

echo "=== 4. Auditing N32 and N64 DSOs ==="
python3 "$TOP_DIR/irix_lib_audit.py" audit "$SCRIPT_DIR/build/32/libcrypto.so.1.1" > /dev/null
python3 "$TOP_DIR/irix_lib_audit.py" audit "$SCRIPT_DIR/build/32/libssl.so.1.1" > /dev/null
python3 "$TOP_DIR/irix_lib_audit.py" audit "$SCRIPT_DIR/build/64/libcrypto.so.1.1" > /dev/null
python3 "$TOP_DIR/irix_lib_audit.py" audit "$SCRIPT_DIR/build/64/libssl.so.1.1" > /dev/null
echo "DSO ELF Audit: PASS (Clean QuickStart MIPS ELF metadata)"

echo "========================================================="
echo "  OpenSSL 1.1.1w modernization completed successfully!   "
echo "========================================================="
