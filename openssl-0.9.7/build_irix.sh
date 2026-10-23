#!/bin/bash
# build_irix.sh - Orchestrate OpenSSL 0.9.7 Modernization & Hardening
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== 1. Staging source tree & generating guest script ==="
python3 "$SCRIPT_DIR/generate_build.py"

echo "=== 2. Executing build inside IRIX guest ==="
"$TOP_DIR/guest_run.sh" --timeout 2700 openssl-0.9.7 "sh /shared/updates-irix/openssl-0.9.7/build/guest_build.sh"

echo "=== Creating symlinks on host ==="
(cd "$SCRIPT_DIR/build" && ln -sf libcrypto.so.0.9.7 libcrypto.so.0 && ln -sf libcrypto.so.0 libcrypto.so)
(cd "$SCRIPT_DIR/build" && ln -sf libssl.so.0.9.7 libssl.so.0 && ln -sf libssl.so.0 libssl.so)
(cd "$SCRIPT_DIR/build/32" && ln -sf libcrypto.so.0.9.7 libcrypto.so.0 && ln -sf libcrypto.so.0 libcrypto.so)
(cd "$SCRIPT_DIR/build/32" && ln -sf libssl.so.0.9.7 libssl.so.0 && ln -sf libssl.so.0 libssl.so)
(cd "$SCRIPT_DIR/build/64" && ln -sf libcrypto.so.0.9.7 libcrypto.so.0 && ln -sf libcrypto.so.0 libcrypto.so)
(cd "$SCRIPT_DIR/build/64" && ln -sf libssl.so.0.9.7 libssl.so.0 && ln -sf libssl.so.0 libssl.so)

echo "=== 3. Running host ELF ABI comparison against original IRIX libraries ==="
python3 "$TOP_DIR/irix_lib_audit.py" compare-tree "$SCRIPT_DIR/orig" "$SCRIPT_DIR/build"

echo "=== 4. Auditing N64 DSOs ==="
python3 "$TOP_DIR/irix_lib_audit.py" audit "$SCRIPT_DIR/build/64/libcrypto.so.0.9.7" > /dev/null
python3 "$TOP_DIR/irix_lib_audit.py" audit "$SCRIPT_DIR/build/64/libssl.so.0.9.7" > /dev/null
echo "N64 DSOs audit: PASS"

echo "========================================================="
echo "  OpenSSL 0.9.7 modernization completed successfully!    "
echo "========================================================="
