#!/bin/sh
# build_irix.sh - Build modernized libpng 1.2.59 + 2025-2026 CVE fixes (o32, n32, n64)
# with MIPSpro 7.4.4m inside the IRIX 6.5.22m guest.
set -e

PROJ_SHARED=/shared/updates-irix/libpng
ZLIB_SHARED=/shared/updates-irix/zlib
WORK=/tmp/libpng_build
STAGE="$PROJ_SHARED/build"

rm -rf "$WORK"
mkdir -p "$WORK/src" "$WORK/o32" "$WORK/n32" "$WORK/64" "$WORK/test"
mkdir -p "$STAGE" "$STAGE/32" "$STAGE/64"

# Copy staged (already patched on host) source into /tmp/libpng_build/src
cp "$PROJ_SHARED"/build/src/* "$WORK/src/"
cp "$PROJ_SHARED"/test_abi_compat.c "$WORK/test/"

# Ensure modernized zlib headers and libraries are available if built
ZLIB_INC="$ZLIB_SHARED/build"
if [ ! -f "$ZLIB_INC/zlib.h" ]; then
    ZLIB_INC="/usr/include"
fi

OBJS="png.o pngset.o pngget.o pngrutil.o pngtrans.o pngwutil.o pngread.o pngrio.o pngwio.o pngwrite.o pngrtran.o pngwtran.o pngmem.o pngerror.o pngpread.o"
SRCS="png.c pngset.c pngget.c pngrutil.c pngtrans.c pngwutil.c pngread.c pngrio.c pngwio.c pngwrite.c pngrtran.c pngwtran.c pngmem.c pngerror.c pngpread.c"

WOFF="-woff 1116,1174,1209,1233,1499,1552,1685,3170,3968,3970"

echo "=== 1. Building O32 (-o32 -mips2) ==="
cd "$WORK/o32"
ZLIB_LIB_O32="$ZLIB_SHARED/build"
[ -f "$ZLIB_LIB_O32/libz.so" ] || ZLIB_LIB_O32="/usr/lib"
for s in $SRCS; do
    cc -o32 -mips2 -O2 -KPIC -I"$WORK/src" -I"$ZLIB_INC" -c "$WORK/src/$s"
done
ar rc libpng.a $OBJS
ld -elf -_SYSTYPE_SVR4 -mips2 -o32 -shared -soname libpng.so -quickstart_info \
   -check_registry /usr/lib/so_locations -o libpng.so -all libpng.a \
   -L"$ZLIB_LIB_O32" -dont_warn_unused -Bdynamic -lz -lm -lc -warn_unused -no_unresolved -set_version sgi1.0
LD_LIBRARY_PATH="$ZLIB_LIB_O32" /usr/etc/rqs32 -f libpng.so

echo "=== 2. Building N32 (-n32 -mips3) ==="
cd "$WORK/n32"
ZLIB_LIB_N32="$ZLIB_SHARED/build/32"
[ -f "$ZLIB_LIB_N32/libz.so" ] || ZLIB_LIB_N32="/usr/lib32"
for s in $SRCS; do
    cc -n32 -mips3 -O2 -KPIC $WOFF -I"$WORK/src" -I"$ZLIB_INC" -c "$WORK/src/$s"
done
ar rc libpng.a $OBJS
ld -elf -_SYSTYPE_SVR4 -mips3 -n32 -shared -soname libpng.so -quickstart_info \
   -check_registry /usr/lib32/so_locations -o libpng.so -all libpng.a \
   -L"$ZLIB_LIB_N32" -dont_warn_unused -Bdynamic -lz -lm -lc -warn_unused -no_unresolved -set_version sgi1.0
LD_LIBRARYN32_PATH="$ZLIB_LIB_N32" /usr/etc/rqs32 -f libpng.so

echo "=== 3. Building N64 (-64 -mips3) ==="
cd "$WORK/64"
ZLIB_LIB_64="$ZLIB_SHARED/build/64"
[ -f "$ZLIB_LIB_64/libz.so" ] || ZLIB_LIB_64="$ZLIB_SHARED/orig/64"
for s in $SRCS; do
    cc -64 -mips3 -O2 -KPIC $WOFF -I"$WORK/src" -I"$ZLIB_INC" -c "$WORK/src/$s"
done
ar rc libpng.a $OBJS
ld -elf -_SYSTYPE_SVR4 -mips3 -64 -shared -soname libpng.so -quickstart_info \
   -check_registry /usr/lib64/so_locations -o libpng.so -all libpng.a \
   -L"$ZLIB_LIB_64" -dont_warn_unused -Bdynamic -lz -lm -lc -warn_unused -no_unresolved -set_version sgi1.0
LD_LIBRARY64_PATH="$ZLIB_LIB_64" /usr/etc/rqs64 -f libpng.so

echo "=== 4. Copying built libraries to $STAGE ==="
cp "$WORK/o32/libpng.so" "$WORK/o32/libpng.a" "$STAGE/"
cp "$WORK/n32/libpng.so" "$WORK/n32/libpng.a" "$STAGE/32/"
cp "$WORK/64/libpng.so"  "$WORK/64/libpng.a"  "$STAGE/64/"
cp "$WORK/src/png.h" "$WORK/src/pngconf.h" "$STAGE/"

echo "=== 5. Compiling & Running Legacy Header (1.2.5) ABI & CVE Tests ==="
cd "$WORK/test"
cc -o32 -mips2 -O2 -I/usr/include test_abi_compat.c -L/usr/lib -lpng -lz -lm -o test_abi_o32
cc -n32 -mips3 -O2 $WOFF -I/usr/include test_abi_compat.c -L/usr/lib32 -lpng -lz -lm -o test_abi_n32
cc -64  -mips3 -O2 $WOFF -I/usr/include test_abi_compat.c -L"$WORK/64" -L"$ZLIB_LIB_64" -lpng -lz -lm -o test_abi_64

echo "--- Running test_abi_n32 against ORIGINAL /usr/lib32/libpng.so (1.2.6) ---"
./test_abi_n32

echo "--- Running test_abi_n32 against MODERNIZED n32/libpng.so (1.2.59+CVE) ---"
LD_LIBRARYN32_PATH="$WORK/n32:$ZLIB_LIB_N32" ./test_abi_n32

echo "--- Running test_abi_o32 against MODERNIZED o32/libpng.so (1.2.59+CVE) ---"
LD_LIBRARY_PATH="$WORK/o32:$ZLIB_LIB_O32" ./test_abi_o32

echo "--- Running test_abi_64 against MODERNIZED 64/libpng.so (1.2.59+CVE) ---"
LD_LIBRARY64_PATH="$WORK/64:$ZLIB_LIB_64" ./test_abi_64

echo "=== 6. Running Upstream pngtest Across All 3 ABIs ==="
for abi in o32 n32 64; do
    echo "--- Upstream pngtest ($abi) ---"
    cd "$WORK/$abi"
    cp "$WORK/src/pngtest.png" .
    if [ "$abi" = "o32" ]; then
        CFLAGS="-o32 -mips2 -O2"
        LFLAGS="-L. -L$ZLIB_LIB_O32 -lpng -lz -lm"
        LENV="LD_LIBRARY_PATH=$WORK/o32:$ZLIB_LIB_O32"
    elif [ "$abi" = "n32" ]; then
        CFLAGS="-n32 -mips3 -O2 $WOFF"
        LFLAGS="-L. -L$ZLIB_LIB_N32 -lpng -lz -lm"
        LENV="LD_LIBRARYN32_PATH=$WORK/n32:$ZLIB_LIB_N32"
    else
        CFLAGS="-64 -mips3 -O2 $WOFF"
        LFLAGS="-L. -L$ZLIB_LIB_64 -lpng -lz -lm"
        LENV="LD_LIBRARY64_PATH=$WORK/64:$ZLIB_LIB_64"
    fi
    cc $CFLAGS -I"$WORK/src" -I"$ZLIB_INC" "$WORK/src/pngtest.c" $LFLAGS -o pngtest_sh
    env "$LENV" ./pngtest_sh pngtest.png
done

echo "=== 7. Testing Live IRIX System Binaries (imginfo / imgcopy via libiflPNG.so) ==="
LD_LIBRARYN32_PATH="$WORK/n32:$ZLIB_LIB_N32" /usr/sbin/imginfo "$WORK/src/pngtest.png"
rm -f /tmp/test_ifl_out.png
LD_LIBRARYN32_PATH="$WORK/n32:$ZLIB_LIB_N32" /usr/sbin/imgcopy "$WORK/src/pngtest.png" /tmp/test_ifl_out.png
LD_LIBRARYN32_PATH="$WORK/n32:$ZLIB_LIB_N32" /usr/sbin/imginfo /tmp/test_ifl_out.png
rm -f /tmp/test_ifl_out.png

echo "ALL LIBPNG BUILDS AND TESTS COMPLETED SUCCESSFULLY!"
