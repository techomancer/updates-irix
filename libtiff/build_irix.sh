#!/bin/sh
# build_irix.sh - Build modernized libtiff 3.9.7 + CVE fixes (o32, n32, n64)
# with MIPSpro 7.4.4m inside the IRIX 6.5.22m guest.
set -e

PROJ_SHARED=/shared/updates-irix/libtiff
WORK=/tmp/libtiff_build
STAGE="$PROJ_SHARED/build"

rm -rf "$WORK"
mkdir -p "$WORK/src" "$WORK/o32" "$WORK/n32" "$WORK/64" "$WORK/test" "$WORK/stub64"
mkdir -p "$STAGE" "$STAGE/32" "$STAGE/64"

# Copy staged source and ABI test into /tmp/libtiff_build
cp "$PROJ_SHARED"/build/src/* "$WORK/src/"
cp "$PROJ_SHARED"/test_abi_compat.c "$WORK/test/"

SRCS="tif_aux.c tif_close.c tif_codec.c tif_color.c tif_compress.c tif_dir.c \
      tif_dirinfo.c tif_dirread.c tif_dirwrite.c tif_dumpmode.c tif_error.c \
      tif_extension.c tif_fax3.c tif_fax3sm.c tif_flush.c tif_getimage.c \
      tif_jpeg.c tif_luv.c tif_lzw.c tif_next.c tif_open.c tif_packbits.c \
      tif_pixarlog.c tif_predict.c tif_print.c tif_read.c tif_strip.c \
      tif_swab.c tif_thunder.c tif_tile.c tif_unix.c tif_version.c \
      tif_warning.c tif_write.c tif_zip.c"

OBJS="tif_aux.o tif_close.o tif_codec.o tif_color.o tif_compress.o tif_dir.o \
      tif_dirinfo.o tif_dirread.o tif_dirwrite.o tif_dumpmode.o tif_error.o \
      tif_extension.o tif_fax3.o tif_fax3sm.o tif_flush.o tif_getimage.o \
      tif_jpeg.o tif_luv.o tif_lzw.o tif_next.o tif_open.o tif_packbits.o \
      tif_pixarlog.o tif_predict.o tif_print.o tif_read.o tif_strip.o \
      tif_swab.o tif_thunder.o tif_tile.o tif_unix.o tif_version.o \
      tif_warning.o tif_write.o tif_zip.o"

WOFF="-woff 1116,1174,1209,1233,1499,1552,1685,3170,3187,3968,3970"

echo "=== 1. Building O32 (-o32 -mips2) ==="
cd "$WORK/o32"
for s in $SRCS; do
    cc -o32 -mips2 -O2 -KPIC -I"$WORK/src" -c "$WORK/src/$s"
done
ar rc libtiff.a $OBJS
ld -elf -_SYSTYPE_SVR4 -mips2 -o32 -shared -soname libtiff.so -quickstart_info \
   -check_registry /usr/lib/so_locations -o libtiff.so -all libtiff.a \
   -L/usr/lib -dont_warn_unused -Bdynamic -ljpeg -lm -lc -warn_unused -no_unresolved -set_version sgi1.1
/usr/etc/rqs32 -f libtiff.so

echo "=== 2. Building N32 (-n32 -mips3) ==="
cd "$WORK/n32"
for s in $SRCS; do
    cc -n32 -mips3 -O2 -KPIC $WOFF -I"$WORK/src" -c "$WORK/src/$s"
done
ar rc libtiff.a $OBJS
ld -elf -_SYSTYPE_SVR4 -mips3 -n32 -shared -soname libtiff.so -quickstart_info \
   -check_registry /usr/lib32/so_locations -o libtiff.so -all libtiff.a \
   -L/usr/lib32 -dont_warn_unused -Bdynamic -ljpeg -lm -lc -warn_unused -no_unresolved -set_version sgi1.1
/usr/etc/rqs32 -f libtiff.so

echo "=== 3. Building N64 (-64 -mips3) ==="
cd "$WORK/64"
# SGI shipped libjpeg.so in o32 & n32 only; build a stub libjpeg.so for n64 link resolution
cat << 'EOF' > "$WORK/stub64/stub.c"
void jpeg_abort(void){}
void jpeg_CreateCompress(void){}
void jpeg_CreateDecompress(void){}
void jpeg_destroy(void){}
void jpeg_finish_compress(void){}
void jpeg_finish_decompress(void){}
void jpeg_read_header(void){}
void jpeg_read_raw_data(void){}
void jpeg_read_scanlines(void){}
void jpeg_resync_to_restart(void){}
void jpeg_set_colorspace(void){}
void jpeg_set_defaults(void){}
void jpeg_set_quality(void){}
void jpeg_start_compress(void){}
void jpeg_start_decompress(void){}
void jpeg_std_error(void){}
void jpeg_suppress_tables(void){}
void jpeg_write_raw_data(void){}
void jpeg_write_scanlines(void){}
void jpeg_write_tables(void){}
EOF
cc -64 -mips3 -c "$WORK/stub64/stub.c" -o "$WORK/stub64/stub.o"
ld -elf -_SYSTYPE_SVR4 -mips3 -64 -shared -soname libjpeg.so -o "$WORK/stub64/libjpeg.so" "$WORK/stub64/stub.o"

for s in $SRCS; do
    cc -64 -mips3 -O2 -KPIC $WOFF -I"$WORK/src" -c "$WORK/src/$s"
done
ar rc libtiff.a $OBJS
ld -elf -_SYSTYPE_SVR4 -mips3 -64 -shared -soname libtiff.so -quickstart_info \
   -T 0x2130000 -o libtiff.so -all libtiff.a \
   -L"$WORK/stub64" -L/usr/lib64 -dont_warn_unused -Bdynamic -ljpeg -lm -lc -warn_unused -no_unresolved -set_version sgi1.1
LD_LIBRARY64_PATH="$WORK/stub64" /usr/etc/rqs64 -f libtiff.so

echo "=== 4. Copying built libraries to $STAGE ==="
cp "$WORK/o32/libtiff.so" "$WORK/o32/libtiff.a" "$STAGE/"
cp "$WORK/n32/libtiff.so" "$WORK/n32/libtiff.a" "$STAGE/32/"
cp "$WORK/64/libtiff.so"  "$WORK/64/libtiff.a"  "$STAGE/64/"
cp "$WORK/stub64/libjpeg.so" "$STAGE/64/libjpeg.so"
cp "$WORK/src/tiff.h" "$WORK/src/tiffio.h" "$WORK/src/tiffvers.h" "$WORK/src/tiffconf.h" "$STAGE/"

echo "=== 5. Compiling & Running ABI Compatibility Tests Across All 3 ABIs ==="
cd "$WORK/test"
cc -o32 -mips2 -O2 -I"$WORK/src" -o test_abi_o32 test_abi_compat.c -L"$WORK/o32" -L/usr/lib -ltiff -ljpeg -lm
cc -n32 -mips3 -O2 $WOFF -I"$WORK/src" -o test_abi_n32 test_abi_compat.c -L"$WORK/n32" -L/usr/lib32 -ltiff -ljpeg -lm
cc -64  -mips3 -O2 $WOFF -I"$WORK/src" -o test_abi_64 test_abi_compat.c -L"$WORK/64" -L"$WORK/stub64" -L/usr/lib64 -ltiff -ljpeg -lm

echo "--- Running test_abi_n32 against ORIGINAL /usr/lib32/libtiff.so (3.4beta037) ---"
./test_abi_n32

echo "--- Running test_abi_n32 against MODERNIZED n32/libtiff.so (3.9.7+ABI+CVE) ---"
LD_LIBRARYN32_PATH="$WORK/n32" ./test_abi_n32

echo "--- Running test_abi_o32 against MODERNIZED o32/libtiff.so (3.9.7+ABI+CVE) ---"
LD_LIBRARY_PATH="$WORK/o32" ./test_abi_o32

echo "--- Running test_abi_64 against MODERNIZED 64/libtiff.so (3.9.7+ABI+CVE) ---"
LD_LIBRARY64_PATH="$WORK/64:$WORK/stub64" ./test_abi_64

echo "=== 6. Testing Live IRIX System Binaries (imginfo / imgcopy via libiflTIFF.so + libxtiff.so) ==="
rm -f /tmp/sample.tif /tmp/sample_copy.tif
# Convert SGI RGB test image to TIFF with modernized n32 libtiff.so
LD_LIBRARYN32_PATH="$WORK/n32" /usr/sbin/imgcopy /usr/share/data/images/TestPattern.rgb /tmp/sample.tif
echo "--- imginfo on /tmp/sample.tif with MODERNIZED n32 libtiff.so ---"
LD_LIBRARYN32_PATH="$WORK/n32" /usr/sbin/imginfo /tmp/sample.tif
echo "--- imgcopy /tmp/sample.tif -> /tmp/sample_copy.tif with MODERNIZED n32 libtiff.so ---"
LD_LIBRARYN32_PATH="$WORK/n32" /usr/sbin/imgcopy /tmp/sample.tif /tmp/sample_copy.tif
LD_LIBRARYN32_PATH="$WORK/n32" /usr/sbin/imginfo /tmp/sample_copy.tif
rm -f /tmp/sample.tif /tmp/sample_copy.tif

echo "=== BUILD AND VERIFICATION COMPLETE ==="
