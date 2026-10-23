#!/usr/bin/env python3
"""
generate_build.py - Staging and MIPSpro Build Generator for OpenSSH 9.9p2
Prepares the build tree for SGI IRIX 6.5.22m native compilation with MIPSpro C99,
linked against modern OpenSSL 1.1.1w and zlib 1.3.2.
"""

import os
import sys
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_DIR = os.path.dirname(SCRIPT_DIR)
SUBMODULE_DIR = os.path.join(SCRIPT_DIR, "openssh")
BUILD_DIR = os.path.join(SCRIPT_DIR, "build")
SRC_STAGE = os.path.join(BUILD_DIR, "src")
STAGING_DIR = os.path.join(SCRIPT_DIR, "staging")

OPENSSL_DIR = os.path.join(PROJ_DIR, "openssl-1.1.1")
ZLIB_DIR = os.path.join(PROJ_DIR, "zlib")

def stage_dependencies():
    print("=== 1. Staging build dependencies (OpenSSL 1.1.1w + zlib) ===")
    os.makedirs(os.path.join(STAGING_DIR, "include", "openssl"), exist_ok=True)
    os.makedirs(os.path.join(STAGING_DIR, "lib"), exist_ok=True)

    # 1. OpenSSL headers
    ssl_src_inc = os.path.join(OPENSSL_DIR, "build", "src", "include", "openssl")
    if os.path.exists(ssl_src_inc):
        for f in os.listdir(ssl_src_inc):
            if f.endswith(".h"):
                shutil.copy2(os.path.join(ssl_src_inc, f), os.path.join(STAGING_DIR, "include", "openssl", f))
        print("  Copied OpenSSL headers to staging/include/openssl")

    # 2. zlib headers
    zlib_h = os.path.join(ZLIB_DIR, "zlib", "zlib.h")
    zconf_h = os.path.join(ZLIB_DIR, "zlib", "zconf.h")
    if os.path.exists(zlib_h) and os.path.exists(zconf_h):
        shutil.copy2(zlib_h, os.path.join(STAGING_DIR, "include", "zlib.h"))
        shutil.copy2(zconf_h, os.path.join(STAGING_DIR, "include", "zconf.h"))
        print("  Copied zlib headers to staging/include")

    # 3. OpenSSL 1.1.1 N32 libraries
    ssl_n32_lib = os.path.join(OPENSSL_DIR, "build", "32")
    if os.path.exists(os.path.join(ssl_n32_lib, "libcrypto.so.1.1")):
        shutil.copy2(os.path.join(ssl_n32_lib, "libcrypto.so.1.1"), os.path.join(STAGING_DIR, "lib", "libcrypto.so.1.1"))
        crypto_so = os.path.join(STAGING_DIR, "lib", "libcrypto.so")
        if not os.path.exists(crypto_so):
            os.symlink("libcrypto.so.1.1", crypto_so)

    if os.path.exists(os.path.join(ssl_n32_lib, "libssl.so.1.1")):
        shutil.copy2(os.path.join(ssl_n32_lib, "libssl.so.1.1"), os.path.join(STAGING_DIR, "lib", "libssl.so.1.1"))
        ssl_so = os.path.join(STAGING_DIR, "lib", "libssl.so")
        if not os.path.exists(ssl_so):
            os.symlink("libssl.so.1.1", ssl_so)

    # 4. zlib N32 library
    zlib_n32_lib = os.path.join(ZLIB_DIR, "build", "32", "libz.so.1.3.2")
    if os.path.exists(zlib_n32_lib):
        shutil.copy2(zlib_n32_lib, os.path.join(STAGING_DIR, "lib", "libz.so.1.3.2"))
        zlib_so = os.path.join(STAGING_DIR, "lib", "libz.so")
        if os.path.exists(zlib_so) or os.path.islink(zlib_so):
            os.remove(zlib_so)
        os.symlink("libz.so.1.3.2", zlib_so)
        print("  Copied OpenSSL 1.1.1 and zlib N32 DSOs to staging/lib")

def stage_openssh():
    print("=== 2. Staging OpenSSH 9.9p2 source tree ===")
    os.makedirs(SRC_STAGE, exist_ok=True)
    if not os.path.exists(os.path.join(SRC_STAGE, "Makefile")):
        for item in os.listdir(SUBMODULE_DIR):
            if item in [".git", "build"]:
                continue
            s = os.path.join(SUBMODULE_DIR, item)
            d = os.path.join(SRC_STAGE, item)
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d, symlinks=True)
            else:
                shutil.copy2(s, d)

        # Copy preconfigured Makefile, compat_Makefile, config.h
        shutil.copy2(os.path.join(SCRIPT_DIR, "Makefile"), os.path.join(SRC_STAGE, "Makefile"))
        shutil.copy2(os.path.join(SCRIPT_DIR, "compat_Makefile"), os.path.join(SRC_STAGE, "openbsd-compat", "Makefile"))
        shutil.copy2(os.path.join(SCRIPT_DIR, "config.h"), os.path.join(SRC_STAGE, "config.h"))
        print("  Installed preconfigured Makefiles and config.h into build/src")
    else:
        print("  (build/src already staged, preserving object timestamps)")

def generate_guest_script():
    print("=== 3. Generating guest build and test script ===")
    guest_sh = os.path.join(BUILD_DIR, "guest_build.sh")

    with open(guest_sh, "w") as f:
        f.write("""#!/bin/sh
# guest_build.sh - Native compilation and end-to-end verification of OpenSSH 9.9p2 on SGI IRIX
set -e

STAGE="/shared/updates-irix/openssh"
SRC="$STAGE/build/src"
OUT="$STAGE/build"

echo "=== [Guest] 1. Preparing privilege separation environment ==="
# Ensure /var/empty exists
if [ ! -d /var/empty ]; then
    mkdir -p /var/empty
    chown root:sys /var/empty
    chmod 755 /var/empty
fi

# Ensure sshd privilege separation user exists
if ! grep '^sshd:' /etc/passwd >/dev/null 2>&1; then
    echo "sshd:x:22:22:sshd privsep:/var/empty:/dev/null" >> /etc/passwd
fi

echo "=== [Guest] 2. Building OpenSSH 9.9p2 with MIPSpro C99 ==="
cd "$SRC"
make

echo "=== [Guest] 3. Staging built binaries ==="
mkdir -p "$OUT/bin" "$OUT/sbin" "$OUT/libexec"

cp "$SRC/ssh"         "$OUT/bin/"
cp "$SRC/scp"         "$OUT/bin/"
cp "$SRC/sftp"        "$OUT/bin/"
cp "$SRC/ssh-add"     "$OUT/bin/"
cp "$SRC/ssh-agent"   "$OUT/bin/"
cp "$SRC/ssh-keygen"  "$OUT/bin/"
cp "$SRC/ssh-keyscan" "$OUT/bin/"

cp "$SRC/sshd"        "$OUT/sbin/"

cp "$SRC/sshd-session"     "$OUT/libexec/"
cp "$SRC/sftp-server"      "$OUT/libexec/"
cp "$SRC/ssh-keysign"      "$OUT/libexec/"
cp "$SRC/ssh-pkcs11-helper" "$OUT/libexec/"
cp "$SRC/ssh-sk-helper"    "$OUT/libexec/"

# Install sshd-session to standard path for privsep execution
chmod 755 "$OUT/bin"/* "$OUT/sbin"/* "$OUT/libexec"/*
cp "$SRC/sshd-session" /usr/libexec/sshd-session
chmod 755 /usr/libexec/sshd-session

echo "=== [Guest] 4. Running Verification Test Suite ==="
TESTDIR="/tmp/ssh-test-$$"
mkdir -p "$TESTDIR/etc" "$TESTDIR/home"
cd "$TESTDIR"

echo "--- A. Key generation and digital signature tests ---"
"$OUT/bin/ssh-keygen" -t rsa -b 2048 -N "" -f "$TESTDIR/etc/ssh_host_rsa_key"
"$OUT/bin/ssh-keygen" -t ecdsa -b 256 -N "" -f "$TESTDIR/etc/ssh_host_ecdsa_key"
"$OUT/bin/ssh-keygen" -t ed25519 -N "" -f "$TESTDIR/etc/ssh_host_ed25519_key"

echo "OpenSSH on IRIX Verification Payload" > "$TESTDIR/payload.txt"

# Standalone ED25519 signing and verification
rm -f "$TESTDIR/payload.txt.sig"
"$OUT/bin/ssh-keygen" -Y sign -f "$TESTDIR/etc/ssh_host_ed25519_key" -n "file" "$TESTDIR/payload.txt"
"$OUT/bin/ssh-keygen" -Y check-novalidate -n "file" -s "$TESTDIR/payload.txt.sig" < "$TESTDIR/payload.txt"
echo "ED25519 Sign/Verify: PASS"

# Standalone ECDSA signing and verification
rm -f "$TESTDIR/payload.txt.sig"
"$OUT/bin/ssh-keygen" -Y sign -f "$TESTDIR/etc/ssh_host_ecdsa_key" -n "file" "$TESTDIR/payload.txt"
"$OUT/bin/ssh-keygen" -Y check-novalidate -n "file" -s "$TESTDIR/payload.txt.sig" < "$TESTDIR/payload.txt"
echo "ECDSA Sign/Verify: PASS"

# Standalone RSA signing and verification
rm -f "$TESTDIR/payload.txt.sig"
"$OUT/bin/ssh-keygen" -Y sign -f "$TESTDIR/etc/ssh_host_rsa_key" -n "file" "$TESTDIR/payload.txt"
"$OUT/bin/ssh-keygen" -Y check-novalidate -n "file" -s "$TESTDIR/payload.txt.sig" < "$TESTDIR/payload.txt"
echo "RSA Sign/Verify: PASS"

echo "--- B. Live sshd daemon, protocol negotiation & login tests ---"
# User key for loopback auth
"$OUT/bin/ssh-keygen" -t ed25519 -N "" -f "$TESTDIR/user_key"
mkdir -p /root/.ssh
chmod 700 /root/.ssh
cat "$TESTDIR/user_key.pub" > /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

cat << EOF > "$TESTDIR/etc/sshd_config"
Port 2222
HostKey $TESTDIR/etc/ssh_host_rsa_key
HostKey $TESTDIR/etc/ssh_host_ecdsa_key
HostKey $TESTDIR/etc/ssh_host_ed25519_key
AuthorizedKeysFile .ssh/authorized_keys
PermitRootLogin yes
PasswordAuthentication yes
Subsystem sftp /shared/updates-irix/openssh/build/libexec/sftp-server
EOF

# Kill any lingering test sshd
killall sshd 2>/dev/null || true

# Start sshd daemon
"$OUT/sbin/sshd" -f "$TESTDIR/etc/sshd_config"
sleep 2

# Keyscan test
echo "Running ssh-keyscan..."
"$OUT/bin/ssh-keyscan" -p 2222 127.0.0.1 > "$TESTDIR/scanned_keys"
grep "ssh-ed25519" "$TESTDIR/scanned_keys" >/dev/null
grep "ecdsa-sha2-nistp256" "$TESTDIR/scanned_keys" >/dev/null
grep "ssh-rsa" "$TESTDIR/scanned_keys" >/dev/null
echo "Keyscan: PASS (All 3 host keys negotiated)"

# Non-interactive loopback SSH execution
echo "Running loopback SSH command execution..."
RESULT=`"$OUT/bin/ssh" -n -p 2222 -i "$TESTDIR/user_key" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes root@127.0.0.1 uname -s < /dev/null`
if [ "$RESULT" != "IRIX64" ] && [ "$RESULT" != "IRIX" ]; then
    echo "SSH remote exec failed, got: $RESULT"
    exit 1
fi
echo "SSH Remote Execution: PASS ($RESULT)"

# SCP transfer test
echo "Running SCP file transfer test..."
"$OUT/bin/scp" -S "$OUT/bin/ssh" -P 2222 -i "$TESTDIR/user_key" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes /etc/passwd root@127.0.0.1:"$TESTDIR/passwd.scp"
cmp /etc/passwd "$TESTDIR/passwd.scp"
echo "SCP Transfer: PASS (File integrity verified)"

# SFTP subsystem test
echo "Running SFTP subsystem test..."
echo "ls $TESTDIR/passwd.scp" | "$OUT/bin/sftp" -S "$OUT/bin/ssh" -P 2222 -i "$TESTDIR/user_key" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes root@127.0.0.1 > "$TESTDIR/sftp.out" 2>&1
grep "passwd.scp" "$TESTDIR/sftp.out" >/dev/null
echo "SFTP Subsystem: PASS"

# Clean up daemon and test files
killall sshd 2>/dev/null || true
cd /tmp
rm -rf "$TESTDIR"

echo "=== [Guest] All OpenSSH 9.9p2 verification tests completed successfully! ==="
""")

    os.chmod(guest_sh, 0o755)

def main():
    stage_dependencies()
    stage_openssh()
    generate_guest_script()
    print("Done! Ready to execute guest_build.sh on IRIX.")

if __name__ == "__main__":
    main()
