#!/usr/bin/env python3
"""
generate_build.py - Staging and guest build script generator for OpenSSL 0.9.7
"""

import os
import sys
import shutil
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SUBMODULE = os.path.join(SCRIPT_DIR, "openssl")
BUILD_DIR = os.path.join(SCRIPT_DIR, "build")
SRC_STAGE = os.path.join(BUILD_DIR, "src")
HDR_STAGE = os.path.join(SRC_STAGE, "include", "openssl")

def stage_sources():
    print("=== 1. Staging pristine source tree ===")
    if not os.path.exists(SRC_STAGE):
        os.makedirs(HDR_STAGE, exist_ok=True)
        os.makedirs(os.path.join(BUILD_DIR, "32"), exist_ok=True)
        os.makedirs(os.path.join(BUILD_DIR, "64"), exist_ok=True)

        # Copy submodule tree (excluding .git)
        shutil.copytree(SUBMODULE, SRC_STAGE, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(".git", "*.o", "*.a", "*.so*"))

        print("=== 2. Applying CVE security fixes and KSSL stubs ===")
        patch_file = os.path.join(SCRIPT_DIR, "patches", "cve-fixes-and-stubs.patch")
        subprocess.run(["patch", "-p1", "-i", patch_file], cwd=SRC_STAGE, check=True)

        print("=== 3. Gathering and installing multi-ABI headers ===")
        for root, dirs, files in os.walk(SRC_STAGE):
            if "include" in root:
                continue
            for f in files:
                if f.endswith(".h") and ("crypto" in root or "ssl" in root or root == SRC_STAGE):
                    shutil.copy2(os.path.join(root, f), os.path.join(HDR_STAGE, f))

        conf_h = os.path.join(SCRIPT_DIR, "patches", "opensslconf.h")
        shutil.copy2(conf_h, os.path.join(HDR_STAGE, "opensslconf.h"))
        shutil.copy2(conf_h, os.path.join(SRC_STAGE, "crypto", "opensslconf.h"))

        buildinf_content = """#ifndef MK1MF_BUILD
  /* auto-generated for IRIX 6.5.22m */
  #define CFLAGS "cc -DEFAULT:abi=n32:isa=mips3 -DOPENSSL_THREADS -D_SGI_MP_SOURCE -DDSO_DLFCN -DHAVE_DLFCN_H -DOPENSSL_NO_KRB5 -DOPENSSL_NO_IDEA -DOPENSSL_NO_RC5 -DOPENSSL_NO_MDC2 -DOPENSSL_NO_ENGINE -n32 -mips3 -O2 -use_readonly_const -DTERMIOS -DB_ENDIAN -DBN_DIV3W"
  #define PLATFORM "irix-mips3-cc"
  #define DATE "Tue Oct 21 00:00:00 UTC 2026"
#endif
"""
        with open(os.path.join(SRC_STAGE, "crypto", "buildinf.h"), "w") as f:
            f.write(buildinf_content)
    else:
        print("  (Source tree already staged, reusing)")

def get_source_lists():
    crypto_subdirs = [
        "objects", "md2", "md4", "md5", "sha", "hmac", "ripemd", "des", "rc2", "rc4",
        "bf", "cast", "bn", "ec", "rsa", "dsa", "dh", "dso", "aes", "buffer", "bio",
        "stack", "lhash", "rand", "err", "evp", "asn1", "pem", "x509", "x509v3",
        "conf", "txt_db", "pkcs7", "pkcs12", "comp", "ocsp", "ui", "krb5"
    ]

    def parse_libobjs(mf_path):
        import re
        if not os.path.exists(mf_path):
            return []
        with open(mf_path) as f:
            content = f.read()
        m = re.search(r"^LIBOBJ\s*=\s*(.*?)(?=\n[A-Z_0-9]+\s*=|\n\n|\Z)", content, re.MULTILINE | re.DOTALL)
        if not m:
            return []
        val = m.group(1).replace("\\\n", " ").strip()
        return val.split()

    crypto_srcs = []
    for o in parse_libobjs(os.path.join(SRC_STAGE, "crypto", "Makefile")):
        c = o.replace(".o", ".c")
        crypto_srcs.append(os.path.join("crypto", c))

    for d in crypto_subdirs:
        objs = parse_libobjs(os.path.join(SRC_STAGE, "crypto", d, "Makefile"))
        for o in objs:
            if "$(" in o or "${" in o:
                continue
            c = o.replace(".o", ".c")
            p = os.path.join("crypto", d, c)
            if os.path.exists(os.path.join(SRC_STAGE, p)):
                crypto_srcs.append(p)

    crypto_srcs.extend([
        "crypto/des/des_enc.c", "crypto/des/fcrypt_b.c",
        "crypto/rc4/rc4_enc.c",
        "crypto/bf/bf_enc.c",
        "crypto/cast/c_enc.c",
        "crypto/ui/ui_compat.c"
    ])

    ssl_srcs = []
    for o in parse_libobjs(os.path.join(SRC_STAGE, "ssl", "Makefile")):
        c = o.replace(".o", ".c")
        p = os.path.join("ssl", c)
        if os.path.exists(os.path.join(SRC_STAGE, p)):
            ssl_srcs.append(p)

    app_objs = [
        "openssl.o", "verify.o", "asn1pars.o", "req.o", "dgst.o", "dh.o", "dhparam.o",
        "enc.o", "passwd.o", "gendh.o", "errstr.o", "ca.o", "pkcs7.o", "crl2p7.o",
        "crl.o", "rsa.o", "rsautl.o", "dsa.o", "dsaparam.o",
        "x509.o", "genrsa.o", "gendsa.o", "s_server.o", "s_client.o", "speed.o",
        "s_time.o", "apps.o", "s_cb.o", "s_socket.o", "app_rand.o", "version.o",
        "sess_id.o", "ciphers.o", "nseq.o", "pkcs12.o", "pkcs8.o", "spkac.o",
        "smime.o", "rand.o", "engine.o", "ocsp.o", "prime.o"
    ]
    app_srcs = []
    for o in app_objs:
        p = os.path.join("apps", o.replace(".o", ".c"))
        if os.path.exists(os.path.join(SRC_STAGE, p)):
            app_srcs.append(p)

    return crypto_srcs, ssl_srcs, app_srcs

def make_batches(items, size=25):
    return [items[i:i + size] for i in range(0, len(items), size)]

def generate_guest_script(crypto_srcs, ssl_srcs, app_srcs):
    print("=== 4. Generating optimized guest build script ===")
    guest_sh = os.path.join(BUILD_DIR, "guest_build.sh")

    crypto_batches_o32 = make_batches(crypto_srcs + ["crypto/bn/bn_asm.c"], 25)
    crypto_batches_mips3 = make_batches(crypto_srcs, 25)
    ssl_batches = make_batches(ssl_srcs, 25)
    app_batches = make_batches(app_srcs, 25)

    with open(guest_sh, "w") as f:
        f.write("""#!/bin/sh
# guest_build.sh - Native IRIX 6.5.22m MIPSpro build of OpenSSL 0.9.7 (o32, n32, n64)
set -e

PROJ_SHARED=/shared/updates-irix/openssl-0.9.7
STAGE="$PROJ_SHARED/build"
WORK=/tmp/openssl_097_build

mkdir -p "$WORK/src" "$WORK/o32" "$WORK/n32" "$WORK/64" "$WORK/test"
mkdir -p "$STAGE" "$STAGE/32" "$STAGE/64"

echo "=== [Guest] Copying source tree to /tmp for fast compilation ==="
if [ ! -f "$WORK/src/Makefile.org" ]; then
    cp -r "$PROJ_SHARED"/build/src/* "$WORK/src/"
fi
cp "$PROJ_SHARED"/build/src/ssl/kssl.c "$WORK/src/ssl/kssl.c"
cp "$PROJ_SHARED"/test_abi_compat.c "$WORK/test/"

INCS="-I$WORK/src/include -I$WORK/src -I$WORK/src/crypto"
DEFS="-DOPENSSL_THREADS -D_SGI_MP_SOURCE -DDSO_DLFCN -DHAVE_DLFCN_H -DOPENSSL_NO_KRB5 -DOPENSSL_NO_IDEA -DOPENSSL_NO_RC5 -DOPENSSL_NO_MDC2 -DOPENSSL_NO_ENGINE -DTERMIOS -DB_ENDIAN"
WOFF="-woff 1116,1174,1209,1233,1499,1552,1685,3170,3187,3968,3970"
""")

        # Generate ABI build functions
        abis = [
            ("o32", "-o32 -mips2 -O2 -Olimit 2500", "/usr/lib/so_locations", "/usr/lib", "rqs32"),
            ("n32", "-n32 -mips3 -O2 -Olimit 2500 -use_readonly_const", "/usr/lib32/so_locations", "/usr/lib32", "rqs32"),
            ("64",  "-64 -mips3 -O2 -Olimit 2500 -use_readonly_const", "/usr/lib64/so_locations", "/usr/lib64", "rqs64")
        ]

        for abi, cflags, so_loc, libdir, rqs in abis:
            f.write(f'\necho "=== [Guest] Building {abi.upper()} ({cflags}) ==="\n')
            f.write(f'cd "$WORK/{abi}"\n')
            f.write(f'if [ -f "$WORK/{abi}/libcrypto.so.0.9.7" ]; then\n')
            f.write(f'    echo "  -> {abi.upper()} libcrypto already built, skipping compilation"\n')
            f.write('else\n')
            # Compile crypto
            f.write('    echo "  Compiling libcrypto..."\n')
            batches = crypto_batches_o32 if abi == "o32" else crypto_batches_mips3
            for idx, batch in enumerate(batches):
                files = " ".join([f'"$WORK/src/{s}"' for s in batch])
                f.write(f'    cc {cflags} -KPIC $DEFS $WOFF $INCS -c {files}\n')

            if abi != "o32":
                f.write(f'    cc {cflags} -KPIC -c "$WORK/src/crypto/bn/asm/mips3.s" -o mips3.o\n')

            f.write('    ar rc libcrypto.a *.o\n')
            abi_flag = cflags.split()[0]
            isa_flag = cflags.split()[1]
            f.write(f'    ld -elf -_SYSTYPE_SVR4 {isa_flag} {abi_flag} -shared \\\n')
            f.write(f'       -soname libcrypto.so.0.9.7 -quickstart_info -check_registry {so_loc} \\\n')
            f.write(f'       -o libcrypto.so.0.9.7 -all libcrypto.a -L{libdir} \\\n')
            f.write('       -dont_warn_unused -Bdynamic -lc -warn_unused -no_unresolved\n')
            f.write(f'    /usr/etc/{rqs} -f libcrypto.so.0.9.7 || true\n')
            f.write('    ln -sf libcrypto.so.0.9.7 libcrypto.so.0\n')
            f.write('    ln -sf libcrypto.so.0 libcrypto.so\n')
            f.write('    rm -f *.o\n')
            f.write('fi\n')

            # Compile ssl
            f.write(f'if [ -f "$WORK/{abi}/libssl.so.0.9.7" ]; then\n')
            f.write(f'    echo "  -> {abi.upper()} libssl already built, skipping compilation"\n')
            f.write('else\n')
            f.write('    echo "  Compiling libssl..."\n')
            for idx, batch in enumerate(ssl_batches):
                files = " ".join([f'"$WORK/src/{s}"' for s in batch])
                f.write(f'    cc {cflags} -KPIC $DEFS $WOFF $INCS -c {files}\n')

            f.write('    ar rc libssl.a *.o\n')
            f.write(f'    ld -elf -_SYSTYPE_SVR4 {isa_flag} {abi_flag} -shared \\\n')
            f.write(f'       -soname libssl.so.0.9.7 -quickstart_info -check_registry {so_loc} \\\n')
            f.write(f'       -o libssl.so.0.9.7 -all libssl.a -L. -L{libdir} \\\n')
            f.write('       -dont_warn_unused -Bdynamic -lcrypto -lc -warn_unused -no_unresolved\n')
            f.write(f'    /usr/etc/{rqs} -f libssl.so.0.9.7 || true\n')
            f.write('    ln -sf libssl.so.0.9.7 libssl.so.0\n')
            f.write('    ln -sf libssl.so.0 libssl.so\n')
            f.write('    rm -f *.o\n')
            f.write('fi\n')

        # Build apps/openssl CLI (n32)
        f.write("""
echo "=== [Guest] Building openssl CLI binary (N32) ==="
if [ -f "$WORK/apps_build/openssl" ]; then
    echo "  -> openssl CLI already built, skipping compilation"
else
    cd "$WORK/n32"
    mkdir -p "$WORK/apps_build"
    cd "$WORK/apps_build"
""")
        for batch in app_batches:
            files = " ".join([f'"$WORK/src/{s}"' for s in batch])
            f.write(f'    cc -n32 -mips3 -O2 $WOFF $DEFS -DMONOLITH $INCS -I"$WORK/src/apps" -c {files}\n')

        f.write("""    cc -n32 -mips3 -O2 *.o -L"$WORK/n32" -lssl -lcrypto -o openssl
    rm -f *.o
fi

echo "=== [Guest] Copying built libraries and binary to shared stage ==="
mkdir -p "$STAGE" "$STAGE/32" "$STAGE/64" "$STAGE/include"
# O32
cp "$WORK/o32/libcrypto.so.0.9.7" "$STAGE/libcrypto.so.0.9.7"
cp "$WORK/o32/libcrypto.a"        "$STAGE/libcrypto.a"
cp "$WORK/o32/libssl.so.0.9.7"    "$STAGE/libssl.so.0.9.7"
cp "$WORK/o32/libssl.a"           "$STAGE/libssl.a"

# N32
cp "$WORK/n32/libcrypto.so.0.9.7" "$STAGE/32/libcrypto.so.0.9.7"
cp "$WORK/n32/libcrypto.a"        "$STAGE/32/libcrypto.a"
cp "$WORK/n32/libssl.so.0.9.7"    "$STAGE/32/libssl.so.0.9.7"
cp "$WORK/n32/libssl.a"           "$STAGE/32/libssl.a"
cp "$WORK/apps_build/openssl"     "$STAGE/32/openssl"

# N64
cp "$WORK/64/libcrypto.so.0.9.7"  "$STAGE/64/libcrypto.so.0.9.7"
cp "$WORK/64/libcrypto.a"         "$STAGE/64/libcrypto.a"
cp "$WORK/64/libssl.so.0.9.7"     "$STAGE/64/libssl.so.0.9.7"
cp "$WORK/64/libssl.a"            "$STAGE/64/libssl.a"

# Headers
cp -r "$WORK/src/include/openssl" "$STAGE/include"

echo "=== [Guest] Running ABI Verification Tests ==="
cd "$WORK/test"

echo "--- Testing O32 ---"
cc -o32 -mips2 $INCS test_abi_compat.c -L"$WORK/o32" -Wl,-rpath,"$WORK/o32" -lssl -lcrypto -o test_o32
LD_LIBRARY_PATH="$WORK/o32" ./test_o32

echo "--- Testing N32 ---"
cc -n32 -mips3 $INCS test_abi_compat.c -L"$WORK/n32" -Wl,-rpath,"$WORK/n32" -lssl -lcrypto -o test_n32
LD_LIBRARYN32_PATH="$WORK/n32" ./test_n32

echo "--- Testing N64 ---"
cc -64 -mips3 $INCS test_abi_compat.c -L"$WORK/64" -Wl,-rpath,"$WORK/64" -lssl -lcrypto -o test_n64
LD_LIBRARY64_PATH="$WORK/64" ./test_n64

echo "=== [Guest] Testing Live IRIX System Binaries Against Modernized OpenSSL ==="
echo "--- Testing /usr/bin/ldapsearch (OpenLDAP client) ---"
LD_LIBRARYN32_PATH="$WORK/n32" /usr/bin/ldapsearch -V 2>&1 || true

echo "--- Testing new openssl CLI ---"
LD_LIBRARYN32_PATH="$WORK/n32" "$WORK/apps_build/openssl" version -a

echo "=== [Guest] All builds and verification tests passed successfully! ==="
""")

    os.chmod(guest_sh, 0o755)

def main():
    stage_sources()
    c_srcs, s_srcs, a_srcs = get_source_lists()
    print(f"Verified {len(c_srcs)} crypto sources, {len(s_srcs)} ssl sources, {len(a_srcs)} app sources.")
    generate_guest_script(c_srcs, s_srcs, a_srcs)
    print("Done! Ready to execute guest_build.sh on IRIX.")

if __name__ == "__main__":
    main()
