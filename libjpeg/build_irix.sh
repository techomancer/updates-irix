#!/bin/bash
# build_irix.sh - Build modernized libjpeg-turbo 2.1.5.1 for IRIX 6.5.22m
# maintaining 100% binary compatibility with SGI IRIX 6.5 ABI (v6a / v6b dual)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== 1. Staging source tree ==="
rm -rf "$SCRIPT_DIR/build"
mkdir -p "$SCRIPT_DIR/build/src"
mkdir -p "$SCRIPT_DIR/build/32"
mkdir -p "$SCRIPT_DIR/build/64"

# Copy pristine upstream submodule sources
cp -r "$SCRIPT_DIR/libjpeg-turbo"/* "$SCRIPT_DIR/build/src/"

# Apply IRIX ABI & dual-version patch
echo "=== 2. Applying IRIX ABI & dual-compatibility patch ==="
cd "$SCRIPT_DIR/build/src"
patch -p1 < "$SCRIPT_DIR/patches/irix-abi.patch"

# Copy configured headers
cp "$SCRIPT_DIR/patches/jconfig.h" "$SCRIPT_DIR/build/src/"
cp "$SCRIPT_DIR/patches/jconfigint.h" "$SCRIPT_DIR/build/src/"
cp "$SCRIPT_DIR/patches/jversion.h" "$SCRIPT_DIR/build/src/"

# Generate guest build script
echo "=== 3. Generating guest build script ==="
cat << 'EOF' > "$SCRIPT_DIR/build/guest_build.sh"
#!/bin/sh
set -e

PROJ_SHARED=/shared/updates-irix/libjpeg
WORK=/tmp/libjpeg_build
STAGE="$PROJ_SHARED/build"

rm -rf "$WORK"
mkdir -p "$WORK/src" "$WORK/o32" "$WORK/n32" "$WORK/64" "$WORK/test"
mkdir -p "$STAGE" "$STAGE/32" "$STAGE/64"

cp "$PROJ_SHARED"/build/src/* "$WORK/src/"
cp "$PROJ_SHARED"/test_abi_compat.c "$WORK/test/"

SRCS="jcapimin.c jcapistd.c jccoefct.c jccolor.c jcdctmgr.c jchuff.c \
      jcicc.c jcinit.c jcmainct.c jcmarker.c jcmaster.c jcomapi.c jcparam.c \
      jcphuff.c jcprepct.c jcsample.c jctrans.c jdapimin.c jdapistd.c jdatadst.c \
      jdatasrc.c jdcoefct.c jdcolor.c jddctmgr.c jdhuff.c jdicc.c jdinput.c \
      jdmainct.c jdmarker.c jdmaster.c jdmerge.c jdphuff.c jdpostct.c jdsample.c \
      jdtrans.c jerror.c jfdctflt.c jfdctfst.c jfdctint.c jidctflt.c jidctfst.c \
      jidctint.c jidctred.c jquant1.c jquant2.c jutils.c jmemmgr.c jmemnobs.c \
      jsimd_none.c jaricom.c jcarith.c jdarith.c"

WOFF="-woff 1116,1174,1209,1233,1499,1552,1685,3170,3187,3968,3970"

echo "=== [Guest] 1. Building O32 (-o32 -mips2) ==="
cd "$WORK/o32"
for s in $SRCS; do
    cc -o32 -mips2 -O2 -Olimit 2000 -KPIC $WOFF -I"$WORK/src" -c "$WORK/src/$s"
done
ar rc libjpeg.a *.o
ld -elf -_SYSTYPE_SVR4 -mips2 -o32 -shared -soname libjpeg.so -quickstart_info \
   -check_registry /usr/lib/so_locations -o libjpeg.so -all libjpeg.a \
   -L/usr/lib -dont_warn_unused -Bdynamic -lc -warn_unused -no_unresolved -set_version sgi1.0
/usr/etc/rqs32 -f libjpeg.so

echo "=== [Guest] 2. Building N32 (-n32 -mips3) ==="
cd "$WORK/n32"
for s in $SRCS; do
    cc -n32 -mips3 -O2 -KPIC $WOFF -I"$WORK/src" -c "$WORK/src/$s"
done
ar rc libjpeg.a *.o
ld -elf -_SYSTYPE_SVR4 -mips3 -n32 -shared -soname libjpeg.so -quickstart_info \
   -check_registry /usr/lib32/so_locations -o libjpeg.so -all libjpeg.a \
   -L/usr/lib32 -dont_warn_unused -Bdynamic -lc -warn_unused -no_unresolved -set_version sgi1.0
/usr/etc/rqs32 -f libjpeg.so

echo "=== [Guest] 3. Building N64 (-64 -mips3) ==="
cd "$WORK/64"
for s in $SRCS; do
    cc -64 -mips3 -O2 -KPIC $WOFF -I"$WORK/src" -c "$WORK/src/$s"
done
ar rc libjpeg.a *.o
ld -elf -_SYSTYPE_SVR4 -mips3 -64 -shared -soname libjpeg.so -quickstart_info \
   -check_registry /usr/lib64/so_locations -o libjpeg.so -all libjpeg.a \
   -L/usr/lib64 -dont_warn_unused -Bdynamic -lc -warn_unused -no_unresolved -set_version sgi1.0
/usr/etc/rqs64 -f libjpeg.so

echo "=== [Guest] 4. Copying built DSOs and archives to shared stage ==="
cp "$WORK/o32/libjpeg.so" "$STAGE/libjpeg.so"
cp "$WORK/o32/libjpeg.a"  "$STAGE/libjpeg.a"
cp "$WORK/n32/libjpeg.so" "$STAGE/32/libjpeg.so"
cp "$WORK/n32/libjpeg.a"  "$STAGE/32/libjpeg.a"
cp "$WORK/64/libjpeg.so"  "$STAGE/64/libjpeg.so"
cp "$WORK/64/libjpeg.a"   "$STAGE/64/libjpeg.a"
cp "$WORK/src/jpeglib.h" "$WORK/src/jconfig.h" "$WORK/src/jmorecfg.h" "$WORK/src/jerror.h" "$STAGE/"

echo "=== [Guest] 5. Running ABI & Functional Verification Tests ==="
cd "$WORK/test"

echo "--- Testing O32 ---"
cc -o32 -mips2 -I"$WORK/src" test_abi_compat.c -L"$WORK/o32" -ljpeg -o test_o32
LD_LIBRARY_PATH="$WORK/o32" ./test_o32

echo "--- Testing N32 ---"
cc -n32 -mips3 -I"$WORK/src" test_abi_compat.c -L"$WORK/n32" -ljpeg -o test_n32
LD_LIBRARYN32_PATH="$WORK/n32" ./test_n32

echo "--- Testing N64 ---"
cc -64 -mips3 -I"$WORK/src" test_abi_compat.c -L"$WORK/64" -ljpeg -o test_n64
LD_LIBRARY64_PATH="$WORK/64" ./test_n64

echo "=== [Guest] 6. Live System Integration Test: imgcopy to JPEG ==="
LD_LIBRARYN32_PATH="$WORK/n32" /usr/sbin/imgcopy /usr/share/data/images/TestPattern.rgb /tmp/test_pattern.jpg
LD_LIBRARYN32_PATH="$WORK/n32" /usr/sbin/imginfo -v /tmp/test_pattern.jpg
rm -f /tmp/test_pattern.jpg

echo "=== [Guest] All builds and tests passed successfully! ==="
EOF

chmod +x "$SCRIPT_DIR/build/guest_build.sh"

echo "=== 4. Executing build inside IRIX guest ==="
"$TOP_DIR/guest_run.sh" --timeout 900 libjpeg "sh /shared/updates-irix/libjpeg/build/guest_build.sh"

echo "=== 5. Running host ELF ABI comparison against original IRIX libraries ==="
python3 "$TOP_DIR/irix_lib_audit.py" compare-tree "$SCRIPT_DIR/orig" "$SCRIPT_DIR/build"
echo "=== 6. Auditing N64 DSO ==="
python3 "$TOP_DIR/irix_lib_audit.py" audit "$SCRIPT_DIR/build/64/libjpeg.so" > /dev/null
echo "N64 DSO audit: PASS"

echo "========================================================="
echo "  libjpeg modernization completed successfully!          "
echo "========================================================="
