#!/bin/sh
# build_irix.sh - Build modernized zlib 1.3.2 (o32, n32, n64) with MIPSpro 7.4.4m
# Runs inside the IRIX 6.5.22m guest from /tmp, reading from /shared/updates-irix/zlib.
set -e

PROJ_SHARED=/shared/updates-irix/zlib
WORK=/tmp/zlib_build
STAGE="$PROJ_SHARED/build"

rm -rf "$WORK"
mkdir -p "$WORK/src" "$WORK/o32" "$WORK/n32" "$WORK/64" "$WORK/test"
mkdir -p "$STAGE" "$STAGE/32" "$STAGE/64"

# Copy staged (already patched on host) source into /tmp/zlib_build/src
cp "$PROJ_SHARED"/build/src/* "$WORK/src/"
cp "$PROJ_SHARED"/test_abi_compat.c "$WORK/test/"

OBJS="adler32.o compress.o crc32.o deflate.o gzclose.o gzlib.o gzread.o gzwrite.o infback.o inffast.o inflate.o inftrees.o trees.o uncompr.o zutil.o"
SRCS="adler32.c compress.c crc32.c deflate.c gzclose.c gzlib.c gzread.c gzwrite.c infback.c inffast.c inflate.c inftrees.c trees.c uncompr.c zutil.c"

COMMON_DEFS="-DZLIB_INTERNAL= -DIRIX_RELEASE_MAJOR=6 -DIRIX_RELEASE_MINOR=5 -DNDEBUG -DLIT_MEM -DHAVE_VSNPRINTF -DHAS_vsnprintf -DHAS_vsnprintf_return -DHAS_snprintf -DHAS_snprintf_return"
WOFF="-woff 1116,1233,1499,1685,3170,3968,3970"

echo "=== 1. Building O32 (-o32 -mips2) ==="
cd "$WORK/o32"
for s in $SRCS; do
    cc -o32 -mips2 -O2 -KPIC $COMMON_DEFS -I"$WORK/src" -c "$WORK/src/$s"
done
ar rc libz.a $OBJS
ld -elf -_SYSTYPE_SVR4 -mips2 -o32 -shared -soname libz.so -quickstart_info \
   -check_registry /usr/lib/so_locations -o libz.so -all libz.a \
   -dont_warn_unused -Bdynamic -lc -warn_unused -no_unresolved -set_version sgi1.0
/usr/etc/rqs32 -f libz.so

echo "=== 2. Building N32 (-n32 -mips3) ==="
cd "$WORK/n32"
for s in $SRCS; do
    cc -n32 -mips3 -O2 -KPIC $COMMON_DEFS $WOFF -I"$WORK/src" -c "$WORK/src/$s"
done
ar rc libz.a $OBJS
ld -elf -_SYSTYPE_SVR4 -mips3 -n32 -shared -soname libz.so -quickstart_info \
   -check_registry /usr/lib32/so_locations -o libz.so -all libz.a \
   -dont_warn_unused -Bdynamic -lc -warn_unused -no_unresolved -set_version sgi1.0
/usr/etc/rqs32 -f libz.so

echo "=== 3. Building N64 (-64 -mips3) ==="
cd "$WORK/64"
for s in $SRCS; do
    cc -64 -mips3 -O2 -KPIC -DLONG64 $COMMON_DEFS $WOFF -I"$WORK/src" -c "$WORK/src/$s"
done
ar rc libz.a $OBJS
ld -elf -_SYSTYPE_SVR4 -mips3 -64 -shared -soname libz.so -quickstart_info \
   -check_registry /usr/lib64/so_locations -o libz.so -all libz.a \
   -dont_warn_unused -Bdynamic -lc -warn_unused -no_unresolved -set_version sgi1.0
/usr/etc/rqs64 -f libz.so

echo "=== 4. Copying built libraries to $STAGE ==="
cp "$WORK/o32/libz.so" "$WORK/o32/libz.a" "$STAGE/"
cp "$WORK/n32/libz.so" "$WORK/n32/libz.a" "$STAGE/32/"
cp "$WORK/64/libz.so"  "$WORK/64/libz.a"  "$STAGE/64/"
cp "$WORK/src/zlib.h"  "$WORK/src/zconf.h" "$STAGE/"

echo "=== 5. Compiling & Running Legacy Header ABI Compatibility Tests ==="
cd "$WORK/test"
cc -o32 -mips2 -O2 -I/usr/include test_abi_compat.c -L/usr/lib -lz -o test_abi_o32
cc -n32 -mips3 -O2 -I/usr/include test_abi_compat.c -L/usr/lib32 -lz -o test_abi_n32
cc -64  -mips3 -O2 -I/usr/include test_abi_compat.c -L"$WORK/64" -lz -o test_abi_64

echo "--- Running test_abi_n32 against ORIGINAL /usr/lib32/libz.so (1.2.1) ---"
./test_abi_n32

echo "--- Running test_abi_n32 against MODERNIZED n32/libz.so (1.3.2) ---"
LD_LIBRARYN32_PATH="$WORK/n32" ./test_abi_n32

echo "--- Running test_abi_o32 against MODERNIZED o32/libz.so (1.3.2) ---"
LD_LIBRARY_PATH="$WORK/o32" ./test_abi_o32

echo "--- Running test_abi_64 against MODERNIZED 64/libz.so (1.3.2) ---"
LD_LIBRARY64_PATH="$WORK/64" ./test_abi_64

echo "=== 6. Running Upstream zlib 1.3.2 Test Suite (example & minigzip) ==="
for abi in o32 n32 64; do
    echo "--- Upstream test suite ($abi) ---"
    cd "$WORK/$abi"
    if [ "$abi" = "o32" ]; then
        CFLAGS="-o32 -mips2 -O2"
        LENV="LD_LIBRARY_PATH=$WORK/o32"
    elif [ "$abi" = "n32" ]; then
        CFLAGS="-n32 -mips3 -O2 $WOFF"
        LENV="LD_LIBRARYN32_PATH=$WORK/n32"
    else
        CFLAGS="-64 -mips3 -O2 $WOFF"
        LENV="LD_LIBRARY64_PATH=$WORK/64"
    fi
    cc $CFLAGS -I"$WORK/src" "$WORK/src/example.c" -L. -lz -o example_sh
    cc $CFLAGS -I"$WORK/src" "$WORK/src/minigzip.c" -L. -lz -o minigzip_sh
    env "$LENV" ./example_sh
    echo "hello world from IRIX $abi minigzip test" | env "$LENV" ./minigzip_sh | env "$LENV" ./minigzip_sh -d
done

echo "=== 7. Testing Live IRIX System Binaries Against Modernized libz.so ==="
LD_LIBRARYN32_PATH="$WORK/n32" /usr/bin/ssh -V 2>&1
rm -f /tmp/test_ssh_key /tmp/test_ssh_key.pub
LD_LIBRARYN32_PATH="$WORK/n32" /usr/bin/ssh-keygen -t rsa -b 1024 -f /tmp/test_ssh_key -N ""
rm -f /tmp/test_ssh_key /tmp/test_ssh_key.pub

echo "ALL BUILDS AND TESTS COMPLETED SUCCESSFULLY!"
