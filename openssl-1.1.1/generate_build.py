#!/usr/bin/env python3
"""
generate_build.py - Staging and MIPSpro Build Generator for OpenSSL 1.1.1w
Produces optimized native IRIX 6.5.22m compilation script for N32 and N64 ABIs.
Configured with pure C routines (no-asm) for exact NIST bit-level correctness
across big-endian MIPS architectures.
"""

import os
import sys
import shutil
import subprocess
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_DIR = os.path.dirname(SCRIPT_DIR)
SUBMODULE_DIR = os.path.join(SCRIPT_DIR, "openssl")
BUILD_DIR = os.path.join(SCRIPT_DIR, "build")
SRC_STAGE = os.path.join(BUILD_DIR, "src")

def stage_sources():
    print("=== 1. Staging pristine source tree ===")
    os.makedirs(BUILD_DIR, exist_ok=True)
    if not os.path.exists(SRC_STAGE):
        print("  Copying submodule tree to build/src...")
        shutil.copytree(SUBMODULE_DIR, SRC_STAGE, symlinks=True, ignore=shutil.ignore_patterns(".git", "*.o", "*.a", "*.so*"))
    else:
        print("  (Source tree already staged, reusing)")

    print("=== 2. Pre-generating headers and pure C configuration on host ===")
    # Run Configure with no-asm to use verified bit-exact C routines
    subprocess.run(["perl", "./Configure", "irix-mips3-cc", "no-asm"], cwd=SRC_STAGE, check=True)

    # Generate headers
    subprocess.run(["make", "build_generated", "apps/progs.h", "crypto/buildinf.h"], cwd=SRC_STAGE, check=True)

    print("=== 3. Updating multi-ABI configuration headers ===")
    # Patch opensslconf.h for dual N32 / N64 ABI support
    conf_h = os.path.join(SRC_STAGE, "include", "openssl", "opensslconf.h")
    with open(conf_h, "r") as f:
        conf_data = f.read()

    multi_abi_block = """
#ifndef OPENSSLDIR
# define OPENSSLDIR "/usr/local/ssl"
#endif
#ifndef ENGINESDIR
# define ENGINESDIR "/usr/local/lib/engines-1.1"
#endif

#if !defined(OPENSSL_SYS_UEFI)
# undef BN_LLONG
# if defined(_MIPS_SZLONG) && _MIPS_SZLONG == 64
#  define SIXTY_FOUR_BIT_LONG
#  undef SIXTY_FOUR_BIT
#  undef THIRTY_TWO_BIT
# else
#  undef SIXTY_FOUR_BIT_LONG
#  define SIXTY_FOUR_BIT
#  undef THIRTY_TWO_BIT
# endif
#endif
"""
    conf_data = re.sub(
        r"#if !defined\(OPENSSL_SYS_UEFI\).*?#endif",
        multi_abi_block.strip(),
        conf_data,
        flags=re.DOTALL
    )
    with open(conf_h, "w") as f:
        f.write(conf_data)

    # Patch bn_conf.h
    bn_conf_h = os.path.join(SRC_STAGE, "include", "crypto", "bn_conf.h")
    with open(bn_conf_h, "r") as f:
        bn_data = f.read()

    bn_multi_abi = """
#if defined(_MIPS_SZLONG) && _MIPS_SZLONG == 64
# define SIXTY_FOUR_BIT_LONG
# undef SIXTY_FOUR_BIT
# undef THIRTY_TWO_BIT
#else
# undef SIXTY_FOUR_BIT_LONG
# define SIXTY_FOUR_BIT
# undef THIRTY_TWO_BIT
#endif
"""
    bn_data = re.sub(
        r"#undef SIXTY_FOUR_BIT_LONG.*?#undef THIRTY_TWO_BIT",
        bn_multi_abi.strip(),
        bn_data,
        flags=re.DOTALL
    )
    with open(bn_conf_h, "w") as f:
        f.write(bn_data)

def parse_makefile_objects():
    mf_path = os.path.join(SRC_STAGE, "Makefile")
    with open(mf_path, "r") as f:
        content = f.read()

    def get_objs(target):
        m = re.search(r"^" + re.escape(target) + r":(.*?)(?=\n[A-Za-z0-9_./$-]+:|\n\n|\Z)", content, re.MULTILINE | re.DOTALL)
        if not m:
            return []
        raw = m.group(1).replace("\\\n", " ").strip()
        objs = [o for o in raw.split() if o.endswith(".o")]
        return objs

    crypto_objs = get_objs("libcrypto.a")
    ssl_objs = get_objs("libssl.a")
    app_objs = get_objs("apps/openssl") + get_objs("apps/libapps.a")
    app_objs = sorted(list(set(app_objs)))

    crypto_c = []
    for o in crypto_objs:
        c = o.replace(".o", ".c")
        if os.path.exists(os.path.join(SRC_STAGE, c)):
            crypto_c.append(c)
        else:
            print(f"Warning: missing {c}")

    ssl_c = []
    for o in ssl_objs:
        c = o.replace(".o", ".c")
        if os.path.exists(os.path.join(SRC_STAGE, c)):
            ssl_c.append(c)

    app_c = []
    for o in app_objs:
        c = o.replace(".o", ".c")
        if os.path.exists(os.path.join(SRC_STAGE, c)):
            app_c.append(c)

    return crypto_c, [], ssl_c, app_c

def make_batches(items, size=25):
    return [items[i:i + size] for i in range(0, len(items), size)]

def generate_guest_script(crypto_c, crypto_s, ssl_c, app_c):
    print("=== 4. Generating optimized guest build script ===")
    guest_sh = os.path.join(BUILD_DIR, "guest_build.sh")

    crypto_batches = make_batches(crypto_c, 25)
    ssl_batches = make_batches(ssl_c, 25)
    app_batches = make_batches(app_c, 25)

    with open(guest_sh, "w") as f:
        f.write("""#!/bin/sh
# guest_build.sh - Native IRIX 6.5.22m MIPSpro build of OpenSSL 1.1.1w (N32, N64)
set -e

PROJ_SHARED=/shared/updates-irix/openssl-1.1.1
STAGE="$PROJ_SHARED/build"
WORK=/tmp/openssl_111_build

mkdir -p "$WORK/src" "$WORK/n32/crypto_obj" "$WORK/n32/ssl_obj" "$WORK/64/crypto_obj" "$WORK/64/ssl_obj" "$WORK/test"
mkdir -p "$STAGE/32" "$STAGE/64" "$STAGE/include"

echo "=== [Guest] Copying source tree to /tmp for fast compilation ==="
cp -r "$PROJ_SHARED"/build/src/* "$WORK/src/"
cp -r "$PROJ_SHARED"/build/src/include/* "$WORK/src/include/"
cp "$PROJ_SHARED"/test_crypto111.c "$WORK/test/"

INCS="-I$WORK/src -I$WORK/src/include -I$WORK/src/crypto -I$WORK/src/crypto/modes -I$WORK/src/crypto/ec -I$WORK/src/crypto/ec/curve448 -I$WORK/src/crypto/ec/curve448/arch_32"
DEFS="-DB_ENDIAN -DOPENSSL_PIC -DOPENSSL_NO_ASM -D_SGI_MP_SOURCE -DNDEBUG"
WOFF="-woff 1185,1174,1209,1499,1552,3187,3968,3970"
""")

        abis = [
            ("n32", "-c99 -n32 -mips3 -O2 -use_readonly_const -G0 -rdata_shared", "/usr/lib32/so_locations", "/usr/lib32", "rqs32"),
            ("64",  "-c99 -64 -mips4 -O2 -use_readonly_const -G0 -rdata_shared",  "/usr/lib64/so_locations", "/usr/lib64", "rqs64")
        ]

        for abi, cflags, so_loc, libdir, rqs in abis:
            abi_dir = "$STAGE/32" if abi == "n32" else "$STAGE/64"
            abi_flag = "-n32" if abi == "n32" else "-64"
            isa_flag = "-mips3" if abi == "n32" else "-mips4"

            f.write(f'\necho "=== [Guest] Building {abi.upper()} ({cflags}) ==="\n')

            # Build crypto
            f.write(f'cd "$WORK/{abi}/crypto_obj"\n')
            f.write(f'if [ -f "$WORK/{abi}/libcrypto.so.1.1" ]; then\n')
            f.write(f'    echo "  -> {abi.upper()} libcrypto already built, skipping compilation"\n')
            f.write('else\n')
            f.write('    echo "  Compiling libcrypto C sources..."\n')
            for batch in crypto_batches:
                first_o = os.path.basename(batch[0]).replace(".c", ".o")
                files = " ".join([f'"$WORK/src/{c}"' for c in batch])
                f.write(f'    if [ ! -f "{first_o}" ]; then cc {cflags} -KPIC $DEFS $WOFF $INCS -c {files}; fi\n')

            f.write(f'    ar rc "$WORK/{abi}/libcrypto.a" *.o\n')
            f.write(f'    cd "$WORK/{abi}"\n')
            f.write(f'    ld -elf -_SYSTYPE_SVR4 {isa_flag} {abi_flag} -shared \\\n')
            f.write(f'       -soname libcrypto.so.1.1 -quickstart_info -check_registry {so_loc} \\\n')
            f.write(f'       -o libcrypto.so.1.1 -all libcrypto.a -L{libdir} \\\n')
            f.write('       -dont_warn_unused -Bdynamic -lpthread -lc -warn_unused\n')
            f.write(f'    /usr/etc/{rqs} -f libcrypto.so.1.1 || true\n')
            f.write(f'    ln -sf libcrypto.so.1.1 "$WORK/{abi}/libcrypto.so"\n')
            f.write('fi\n')

            # Build ssl
            f.write(f'cd "$WORK/{abi}/ssl_obj"\n')
            f.write(f'if [ -f "$WORK/{abi}/libssl.so.1.1" ]; then\n')
            f.write(f'    echo "  -> {abi.upper()} libssl already built, skipping compilation"\n')
            f.write('else\n')
            f.write('    echo "  Compiling libssl C sources..."\n')
            for batch in ssl_batches:
                first_o = os.path.basename(batch[0]).replace(".c", ".o")
                files = " ".join([f'"$WORK/src/{c}"' for c in batch])
                f.write(f'    if [ ! -f "{first_o}" ]; then cc {cflags} -KPIC $DEFS $WOFF $INCS -c {files}; fi\n')

            f.write(f'    ar rc "$WORK/{abi}/libssl.a" *.o\n')
            f.write(f'    cd "$WORK/{abi}"\n')
            f.write(f'    ld -elf -_SYSTYPE_SVR4 {isa_flag} {abi_flag} -shared \\\n')
            f.write(f'       -soname libssl.so.1.1 -quickstart_info -check_registry {so_loc} \\\n')
            f.write(f'       -o libssl.so.1.1 -all libssl.a -L. -L{libdir} \\\n')
            f.write('       -dont_warn_unused -Bdynamic -lcrypto -lpthread -lc -warn_unused\n')
            f.write(f'    /usr/etc/{rqs} -f libssl.so.1.1 || true\n')
            f.write(f'    ln -sf libssl.so.1.1 "$WORK/{abi}/libssl.so"\n')
            f.write('fi\n')

        # Build apps/openssl CLI (N32)
        f.write("""
echo "=== [Guest] Building openssl CLI binary (N32) ==="
mkdir -p "$WORK/apps_build"
cd "$WORK/apps_build"
if [ -f "$WORK/apps_build/openssl" ]; then
    echo "  -> openssl CLI already built, skipping compilation"
else
""")
        for batch in app_batches:
            first_o = os.path.basename(batch[0]).replace(".c", ".o")
            files = " ".join([f'"$WORK/src/{c}"' for c in batch])
            f.write(f'    if [ ! -f "{first_o}" ]; then cc -c99 -n32 -mips3 -O2 $WOFF $DEFS $INCS -I"$WORK/src/apps" -c {files}; fi\n')

        f.write("""    cc -n32 -mips3 -O2 *.o -L"$WORK/n32" -Wl,-rpath,"$WORK/n32" -lssl -lcrypto -lpthread -o openssl
    rm -f *.o
fi

echo "=== [Guest] Copying built libraries and binary to shared stage ==="
# N32
cp "$WORK/n32/libcrypto.so.1.1" "$STAGE/32/libcrypto.so.1.1"
cp "$WORK/n32/libcrypto.a"      "$STAGE/32/libcrypto.a"
cp "$WORK/n32/libssl.so.1.1"    "$STAGE/32/libssl.so.1.1"
cp "$WORK/n32/libssl.a"         "$STAGE/32/libssl.a"
cp "$WORK/apps_build/openssl"   "$STAGE/32/openssl"

# N64
cp "$WORK/64/libcrypto.so.1.1"  "$STAGE/64/libcrypto.so.1.1"
cp "$WORK/64/libcrypto.a"       "$STAGE/64/libcrypto.a"
cp "$WORK/64/libssl.so.1.1"     "$STAGE/64/libssl.so.1.1"
cp "$WORK/64/libssl.a"          "$STAGE/64/libssl.a"

# Multi-ABI Headers
cp -r "$WORK/src/include/openssl" "$STAGE/include"

echo "=== [Guest] Running Modern Cryptography Verification Tests ==="
cd "$WORK/test"

echo "--- Testing N32 ---"
cc -c99 -n32 -mips3 $INCS test_crypto111.c -L"$WORK/n32" -Wl,-rpath,"$WORK/n32" -lssl -lcrypto -lpthread -o test_n32
LD_LIBRARYN32_PATH="$WORK/n32" ./test_n32

echo "--- Testing N64 ---"
cc -c99 -64 -mips4 $INCS test_crypto111.c -L"$WORK/64" -Wl,-rpath,"$WORK/64" -lssl -lcrypto -lpthread -o test_n64
LD_LIBRARY64_PATH="$WORK/64" ./test_n64

echo "--- Testing openssl CLI binary (N32) ---"
LD_LIBRARYN32_PATH="$WORK/n32" "$WORK/apps_build/openssl" version -a
echo "Testing CLI SHA-256:"
echo "Hello Silicon Graphics" | LD_LIBRARYN32_PATH="$WORK/n32" "$WORK/apps_build/openssl" dgst -sha256

echo "=== [Guest] OpenSSL 1.1.1w builds and verification tests completed successfully! ==="
""")

    os.chmod(guest_sh, 0o755)

def main():
    stage_sources()
    crypto_c, crypto_s, ssl_c, app_c = parse_makefile_objects()
    print(f"Verified {len(crypto_c)} crypto C sources, {len(crypto_s)} asm modules, {len(ssl_c)} ssl sources, {len(app_c)} app sources.")
    generate_guest_script(crypto_c, crypto_s, ssl_c, app_c)
    print("Done! Ready to execute guest_build.sh on IRIX.")

if __name__ == "__main__":
    main()
