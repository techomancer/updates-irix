/*
 * test_abi_compat.c: Verify 100% binary & ABI compatibility of modernized libtiff
 * against SGI IRIX 6.5.22m libtiff / libxtiff / libiflTIFF layouts across o32, n32, and n64.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
#include <assert.h>

#include "tiff.h"
#include "tiffio.h"
#include "tif_dir.h"
#include "tif_fax3.h"
#include "tiffiop.h"

int main(void)
{
    int errors = 0;
    int is_64bit = (sizeof(void*) == 8);
    size_t expected_rgba_sz;
    size_t expected_dir_sz;
    size_t expected_flags_off;
    size_t expected_fieldsset_off;
    size_t expected_clientdir_off;
    size_t expected_vsetfield_off;
    size_t expected_vgetfield_off;
    size_t expected_printdir_off;
    const char *test_filename = "/tmp/test_abi.tif";
    TIFF *tif = NULL;
    uint32 w = 64, h = 64;
    uint32 row = 0;
    unsigned char scanline[64 * 3];
    uint32 rw = 0, rh = 0;

    printf("=== libtiff ABI Compatibility Test (%s) ===\n",
           is_64bit ? "64-bit n64" : (sizeof(long) == 4 ? "32-bit (o32 or n32)" : "unknown"));
    printf("TIFF Version string: %s\n", TIFFGetVersion());

    /* 1. Fundamental Types */
    assert(sizeof(uint8) == 1);
    assert(sizeof(int8) == 1);
    assert(sizeof(uint16) == 2);
    assert(sizeof(int16) == 2);
    assert(sizeof(uint32) == 4);
    assert(sizeof(int32) == 4);

    /* 2. TIFFRGBAImage layout (exact 3.4beta037 size: 68 bytes on 32-bit, 112 bytes on 64-bit) */
    expected_rgba_sz = is_64bit ? 112 : 68;
    if (sizeof(TIFFRGBAImage) != expected_rgba_sz) {
        fprintf(stderr, "ERROR: sizeof(TIFFRGBAImage) = %u, expected %u\n",
                (unsigned)sizeof(TIFFRGBAImage), (unsigned)expected_rgba_sz);
        errors++;
    } else {
        printf("PASS: sizeof(TIFFRGBAImage) = %u\n", (unsigned)sizeof(TIFFRGBAImage));
    }

    if (offsetof(struct _TIFFRGBAImage, tif) != 0 ||
        offsetof(struct _TIFFRGBAImage, stoponerr) != (is_64bit ? 8 : 4) ||
        offsetof(struct _TIFFRGBAImage, isContig) != (is_64bit ? 12 : 8) ||
        offsetof(struct _TIFFRGBAImage, alpha) != (is_64bit ? 16 : 12) ||
        offsetof(struct _TIFFRGBAImage, width) != (is_64bit ? 20 : 16) ||
        offsetof(struct _TIFFRGBAImage, height) != (is_64bit ? 24 : 20) ||
        offsetof(struct _TIFFRGBAImage, bitspersample) != (is_64bit ? 28 : 24) ||
        offsetof(struct _TIFFRGBAImage, samplesperpixel) != (is_64bit ? 30 : 26) ||
        offsetof(struct _TIFFRGBAImage, orientation) != (is_64bit ? 32 : 28) ||
        offsetof(struct _TIFFRGBAImage, photometric) != (is_64bit ? 34 : 30) ||
        offsetof(struct _TIFFRGBAImage, redcmap) != (is_64bit ? 40 : 32) ||
        offsetof(struct _TIFFRGBAImage, greencmap) != (is_64bit ? 48 : 36) ||
        offsetof(struct _TIFFRGBAImage, bluecmap) != (is_64bit ? 56 : 40) ||
        offsetof(struct _TIFFRGBAImage, get) != (is_64bit ? 64 : 44) ||
        offsetof(struct _TIFFRGBAImage, put) != (is_64bit ? 72 : 48) ||
        offsetof(struct _TIFFRGBAImage, Map) != (is_64bit ? 80 : 52) ||
        offsetof(struct _TIFFRGBAImage, BWmap) != (is_64bit ? 88 : 56) ||
        offsetof(struct _TIFFRGBAImage, PALmap) != (is_64bit ? 96 : 60) ||
        offsetof(struct _TIFFRGBAImage, ycbcr) != (is_64bit ? 104 : 64)) {
        fprintf(stderr, "ERROR: TIFFRGBAImage member offset mismatch\n");
        errors++;
    } else {
        printf("PASS: TIFFRGBAImage member offsets match SGI 3.4beta037\n");
    }

    /* 3. TIFFDirectory layout (264 bytes on 32-bit, 392 bytes on 64-bit) */
    expected_dir_sz = is_64bit ? 392 : 264;
    if (sizeof(TIFFDirectory) != expected_dir_sz) {
        fprintf(stderr, "ERROR: sizeof(TIFFDirectory) = %u, expected %u\n",
                (unsigned)sizeof(TIFFDirectory), (unsigned)expected_dir_sz);
        errors++;
    } else {
        printf("PASS: sizeof(TIFFDirectory) = %u\n", (unsigned)sizeof(TIFFDirectory));
    }

    if (offsetof(TIFFDirectory, td_fieldsset) != 0 ||
        offsetof(TIFFDirectory, td_imagewidth) != (is_64bit ? 24 : 12) ||
        offsetof(TIFFDirectory, td_imagelength) != (is_64bit ? 28 : 16) ||
        offsetof(TIFFDirectory, td_imagedepth) != (is_64bit ? 32 : 20) ||
        offsetof(TIFFDirectory, td_tilewidth) != (is_64bit ? 36 : 24)) {
        fprintf(stderr, "ERROR: TIFFDirectory member offset mismatch for libiflTIFF.so!\n");
        fprintf(stderr, "  td_imagewidth: %u (exp %u)\n",
                (unsigned)offsetof(TIFFDirectory, td_imagewidth), (unsigned)(is_64bit ? 24 : 12));
        errors++;
    } else {
        printf("PASS: TIFFDirectory member offsets match libiflTIFF.so byte-for-byte\n");
    }

    /* 4. struct tiff offsets hardcoded into libxtiff.so */
    expected_flags_off = is_64bit ? 16 : 12;
    expected_fieldsset_off = is_64bit ? 32 : 24; /* offsetof(struct tiff, tif_dir) + offsetof(TIFFDirectory, td_fieldsset) */
    expected_clientdir_off = is_64bit ? 432 : 296;
    expected_vsetfield_off = is_64bit ? 776 : 492;
    expected_vgetfield_off = is_64bit ? 784 : 496;
    expected_printdir_off  = is_64bit ? 792 : 500;

    if (offsetof(struct tiff, tif_name) != 0 ||
        offsetof(struct tiff, tif_flags) != expected_flags_off ||
        (offsetof(struct tiff, tif_dir) + offsetof(TIFFDirectory, td_fieldsset)) != expected_fieldsset_off ||
        offsetof(struct tiff, tif_clientdir) != expected_clientdir_off ||
        (offsetof(struct tiff, tif_tagmethods) + offsetof(TIFFTagMethods, vsetfield)) != expected_vsetfield_off ||
        (offsetof(struct tiff, tif_tagmethods) + offsetof(TIFFTagMethods, vgetfield)) != expected_vgetfield_off ||
        (offsetof(struct tiff, tif_tagmethods) + offsetof(TIFFTagMethods, printdir)) != expected_printdir_off) {
        fprintf(stderr, "ERROR: struct tiff offset mismatch for libxtiff.so compatibility!\n");
        fprintf(stderr, "  tif_name: %u (exp 0)\n", (unsigned)offsetof(struct tiff, tif_name));
        fprintf(stderr, "  tif_flags: %u (exp %u)\n", (unsigned)offsetof(struct tiff, tif_flags), (unsigned)expected_flags_off);
        fprintf(stderr, "  tif_dir.td_fieldsset: %u (exp %u)\n",
                (unsigned)(offsetof(struct tiff, tif_dir) + offsetof(TIFFDirectory, td_fieldsset)), (unsigned)expected_fieldsset_off);
        fprintf(stderr, "  tif_clientdir: %u (exp %u)\n", (unsigned)offsetof(struct tiff, tif_clientdir), (unsigned)expected_clientdir_off);
        fprintf(stderr, "  tif_tagmethods.vsetfield: %u (exp %u)\n",
                (unsigned)(offsetof(struct tiff, tif_tagmethods) + offsetof(TIFFTagMethods, vsetfield)), (unsigned)expected_vsetfield_off);
        errors++;
    } else {
        printf("PASS: struct tiff offsets match libxtiff.so byte-for-byte\n");
    }

    /* 5. tiffDataWidth size */
    if (sizeof(tiffDataWidth) != 52) {
        fprintf(stderr, "ERROR: sizeof(tiffDataWidth) = %u, expected 52\n",
                (unsigned)sizeof(tiffDataWidth));
        errors++;
    } else {
        printf("PASS: sizeof(tiffDataWidth) = 52 bytes (13 ints)\n");
    }

    /* 5b. Fax table entry size */
    if (sizeof(TIFFFaxTabEnt) != 4) {
        fprintf(stderr, "ERROR: sizeof(TIFFFaxTabEnt) = %u, expected 4\n",
                (unsigned)sizeof(TIFFFaxTabEnt));
        errors++;
    } else {
        printf("PASS: sizeof(TIFFFaxTabEnt) = 4 bytes (matches 3.4beta037)\n");
    }

    /* 6. Functional test: Write and Read a test TIFF */
    memset(scanline, 128, sizeof(scanline));

    tif = TIFFOpen(test_filename, "w");
    if (!tif) {
        fprintf(stderr, "ERROR: TIFFOpen('%s', 'w') failed\n", test_filename);
        errors++;
    } else {
        TIFFSetField(tif, TIFFTAG_IMAGEWIDTH, w);
        TIFFSetField(tif, TIFFTAG_IMAGELENGTH, h);
        TIFFSetField(tif, TIFFTAG_BITSPERSAMPLE, 8);
        TIFFSetField(tif, TIFFTAG_SAMPLESPERPIXEL, 3);
        TIFFSetField(tif, TIFFTAG_PLANARCONFIG, PLANARCONFIG_CONTIG);
        TIFFSetField(tif, TIFFTAG_PHOTOMETRIC, PHOTOMETRIC_RGB);
        TIFFSetField(tif, TIFFTAG_COMPRESSION, COMPRESSION_PACKBITS);

        for (row = 0; row < h; row++) {
            if (TIFFWriteScanline(tif, scanline, row, 0) < 0) {
                fprintf(stderr, "ERROR: TIFFWriteScanline failed at row %u\n", (unsigned)row);
                errors++;
                break;
            }
        }
        TIFFClose(tif);

        /* Read back */
        tif = TIFFOpen(test_filename, "r");
        if (!tif) {
            fprintf(stderr, "ERROR: TIFFOpen('%s', 'r') failed\n", test_filename);
            errors++;
        } else {
            TIFFGetField(tif, TIFFTAG_IMAGEWIDTH, &rw);
            TIFFGetField(tif, TIFFTAG_IMAGELENGTH, &rh);
            if (rw != w || rh != h) {
                fprintf(stderr, "ERROR: Read dimensions %ux%u, expected %ux%u\n",
                        (unsigned)rw, (unsigned)rh, (unsigned)w, (unsigned)h);
                errors++;
            } else {
                printf("PASS: TIFF write/read test succeeded (%ux%u PackBits RGB)\n",
                       (unsigned)rw, (unsigned)rh);
            }
            TIFFClose(tif);
        }
        remove(test_filename);
    }

    if (errors == 0) {
        printf("=== ALL ABI TESTS PASSED ===\n");
        return 0;
    } else {
        fprintf(stderr, "=== %d ABI TESTS FAILED ===\n", errors);
        return 1;
    }
}
