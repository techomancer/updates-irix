/*
 * test_abi_compat.c - IRIX 6.5.22m libjpeg ABI and Functional Verification Test
 *
 * Verifies byte-for-byte ABI structure sizes and member offsets against
 * SGI IRIX 6.5.22m libjpeg.so (v6a, JPEG_LIB_VERSION 61), tests version
 * compatibility (accepting both 61 and 62), and performs an end-to-end
 * compression/decompression cycle.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>

#include "jconfig.h"
#include "jpeglib.h"
#include "jerror.h"

/* Internal constants and exported global object declarations */
#define CSTATE_START  100
#define DSTATE_START  200
extern const int jpeg_natural_order[];
extern const char * const jpeg_std_message_table[];

#define CHECK(cond, msg) do { \
    if (!(cond)) { \
        fprintf(stderr, "FAIL: %s (line %d)\n", msg, __LINE__); \
        exit(1); \
    } \
} while (0)

#define CHECK_OFFSET(s, m, expected, label) do { \
    size_t off = offsetof(s, m); \
    if (off != (expected)) { \
        fprintf(stderr, "FAIL: offset of %s is %u, expected %u\n", \
                label, (unsigned)off, (unsigned)(expected)); \
        exit(1); \
    } \
} while (0)

static void test_struct_sizes_and_offsets(void)
{
    printf("--- Checking Structure Sizes and Member Offsets ---\n");

#if defined(_MIPS_SZLONG) && _MIPS_SZLONG == 64
    /* 64-bit ABI (n64) */
    CHECK(sizeof(struct jpeg_compress_struct) == 496,
          "sizeof(struct jpeg_compress_struct) must be 496 bytes on n64");
    CHECK(sizeof(struct jpeg_decompress_struct) == 624,
          "sizeof(struct jpeg_decompress_struct) must be 624 bytes on n64");

    CHECK_OFFSET(struct jpeg_compress_struct, dest, 32, "compress.dest");
    CHECK_OFFSET(struct jpeg_compress_struct, image_width, 40, "compress.image_width");
    CHECK_OFFSET(struct jpeg_compress_struct, image_height, 44, "compress.image_height");
    CHECK_OFFSET(struct jpeg_compress_struct, input_components, 48, "compress.input_components");
    CHECK_OFFSET(struct jpeg_compress_struct, in_color_space, 52, "compress.in_color_space");
    CHECK_OFFSET(struct jpeg_compress_struct, input_gamma, 56, "compress.input_gamma");
    CHECK_OFFSET(struct jpeg_compress_struct, data_precision, 64, "compress.data_precision");
    CHECK_OFFSET(struct jpeg_compress_struct, num_components, 68, "compress.num_components");
    CHECK_OFFSET(struct jpeg_compress_struct, jpeg_color_space, 72, "compress.jpeg_color_space");
    CHECK_OFFSET(struct jpeg_compress_struct, comp_info, 80, "compress.comp_info");
    CHECK_OFFSET(struct jpeg_compress_struct, quant_tbl_ptrs, 88, "compress.quant_tbl_ptrs");
    CHECK_OFFSET(struct jpeg_compress_struct, raw_data_in, 248, "compress.raw_data_in");
    CHECK_OFFSET(struct jpeg_compress_struct, write_JFIF_header, 280, "compress.write_JFIF_header");
    CHECK_OFFSET(struct jpeg_compress_struct, density_unit, 284, "compress.density_unit");
    CHECK_OFFSET(struct jpeg_compress_struct, X_density, 286, "compress.X_density");
    CHECK_OFFSET(struct jpeg_compress_struct, Y_density, 288, "compress.Y_density");
    CHECK_OFFSET(struct jpeg_compress_struct, write_Adobe_marker, 292, "compress.write_Adobe_marker");
    CHECK_OFFSET(struct jpeg_compress_struct, next_scanline, 296, "compress.next_scanline");
    CHECK_OFFSET(struct jpeg_compress_struct, progressive_mode, 300, "compress.progressive_mode");
    CHECK_OFFSET(struct jpeg_compress_struct, master, 424, "compress.master");
    CHECK_OFFSET(struct jpeg_compress_struct, entropy, 488, "compress.entropy");

    CHECK_OFFSET(struct jpeg_decompress_struct, src, 32, "decompress.src");
    CHECK_OFFSET(struct jpeg_decompress_struct, image_width, 40, "decompress.image_width");
    CHECK_OFFSET(struct jpeg_decompress_struct, image_height, 44, "decompress.image_height");
    CHECK_OFFSET(struct jpeg_decompress_struct, num_components, 48, "decompress.num_components");
    CHECK_OFFSET(struct jpeg_decompress_struct, out_color_space, 56, "decompress.out_color_space");
    CHECK_OFFSET(struct jpeg_decompress_struct, output_width, 128, "decompress.output_width");
    CHECK_OFFSET(struct jpeg_decompress_struct, output_scanline, 160, "decompress.output_scanline");
    CHECK_OFFSET(struct jpeg_decompress_struct, master, 528, "decompress.master");
    CHECK_OFFSET(struct jpeg_decompress_struct, cquantize, 608, "decompress.cquantize");
    CHECK_OFFSET(struct jpeg_decompress_struct, prof_info, 616, "decompress.prof_info");

#else
    /* 32-bit ABI (o32 / n32) */
    CHECK(sizeof(struct jpeg_compress_struct) == 360,
          "sizeof(struct jpeg_compress_struct) must be 360 bytes on 32-bit");
    CHECK(sizeof(struct jpeg_decompress_struct) == 464,
          "sizeof(struct jpeg_decompress_struct) must be 464 bytes on 32-bit");

    CHECK_OFFSET(struct jpeg_compress_struct, dest, 20, "compress.dest");
    CHECK_OFFSET(struct jpeg_compress_struct, image_width, 24, "compress.image_width");
    CHECK_OFFSET(struct jpeg_compress_struct, image_height, 28, "compress.image_height");
    CHECK_OFFSET(struct jpeg_compress_struct, input_components, 32, "compress.input_components");
    CHECK_OFFSET(struct jpeg_compress_struct, in_color_space, 36, "compress.in_color_space");
    CHECK_OFFSET(struct jpeg_compress_struct, input_gamma, 40, "compress.input_gamma");
    CHECK_OFFSET(struct jpeg_compress_struct, data_precision, 48, "compress.data_precision");
    CHECK_OFFSET(struct jpeg_compress_struct, num_components, 52, "compress.num_components");
    CHECK_OFFSET(struct jpeg_compress_struct, jpeg_color_space, 56, "compress.jpeg_color_space");
    CHECK_OFFSET(struct jpeg_compress_struct, comp_info, 60, "compress.comp_info");
    CHECK_OFFSET(struct jpeg_compress_struct, quant_tbl_ptrs, 64, "compress.quant_tbl_ptrs");
    CHECK_OFFSET(struct jpeg_compress_struct, raw_data_in, 168, "compress.raw_data_in");
    CHECK_OFFSET(struct jpeg_compress_struct, write_JFIF_header, 200, "compress.write_JFIF_header");
    CHECK_OFFSET(struct jpeg_compress_struct, density_unit, 204, "compress.density_unit");
    CHECK_OFFSET(struct jpeg_compress_struct, X_density, 206, "compress.X_density");
    CHECK_OFFSET(struct jpeg_compress_struct, Y_density, 208, "compress.Y_density");
    CHECK_OFFSET(struct jpeg_compress_struct, write_Adobe_marker, 212, "compress.write_Adobe_marker");
    CHECK_OFFSET(struct jpeg_compress_struct, next_scanline, 216, "compress.next_scanline");
    CHECK_OFFSET(struct jpeg_compress_struct, progressive_mode, 220, "compress.progressive_mode");
    CHECK_OFFSET(struct jpeg_compress_struct, master, 324, "compress.master");
    CHECK_OFFSET(struct jpeg_compress_struct, entropy, 356, "compress.entropy");

    CHECK_OFFSET(struct jpeg_decompress_struct, src, 20, "decompress.src");
    CHECK_OFFSET(struct jpeg_decompress_struct, image_width, 24, "decompress.image_width");
    CHECK_OFFSET(struct jpeg_decompress_struct, image_height, 28, "decompress.image_height");
    CHECK_OFFSET(struct jpeg_decompress_struct, num_components, 32, "decompress.num_components");
    CHECK_OFFSET(struct jpeg_decompress_struct, out_color_space, 40, "decompress.out_color_space");
    CHECK_OFFSET(struct jpeg_decompress_struct, output_width, 112, "decompress.output_width");
    CHECK_OFFSET(struct jpeg_decompress_struct, output_scanline, 140, "decompress.output_scanline");
    CHECK_OFFSET(struct jpeg_decompress_struct, master, 416, "decompress.master");
    CHECK_OFFSET(struct jpeg_decompress_struct, cquantize, 456, "decompress.cquantize");
    CHECK_OFFSET(struct jpeg_decompress_struct, prof_info, 460, "decompress.prof_info");
#endif

    printf("  -> Struct sizes and all 31 critical offsets MATCH SGI 6.5 ABI perfectly!\n");
}

static void test_version_acceptance(void)
{
    struct jpeg_compress_struct cinfo;
    struct jpeg_decompress_struct dinfo;
    struct jpeg_error_mgr jerr;

    printf("--- Checking Dual-Version Acceptance (61 and 62) ---\n");

    /* Version 61 (IRIX 6.5.22m stock) */
    cinfo.err = jpeg_std_error(&jerr);
    jpeg_CreateCompress(&cinfo, 61, sizeof(cinfo));
    CHECK(cinfo.is_decompressor == FALSE, "cinfo.is_decompressor must be FALSE");
    CHECK(cinfo.global_state == CSTATE_START, "cinfo.global_state must be CSTATE_START");
    jpeg_destroy_compress(&cinfo);

    dinfo.err = jpeg_std_error(&jerr);
    jpeg_CreateDecompress(&dinfo, 61, sizeof(dinfo));
    CHECK(dinfo.is_decompressor == TRUE, "dinfo.is_decompressor must be TRUE");
    CHECK(dinfo.global_state == DSTATE_START, "dinfo.global_state must be DSTATE_START");
    jpeg_destroy_decompress(&dinfo);

    /* Version 62 (v6b compatibility) */
    cinfo.err = jpeg_std_error(&jerr);
    jpeg_CreateCompress(&cinfo, 62, sizeof(cinfo));
    jpeg_destroy_compress(&cinfo);

    dinfo.err = jpeg_std_error(&jerr);
    jpeg_CreateDecompress(&dinfo, 62, sizeof(dinfo));
    jpeg_destroy_decompress(&dinfo);

    printf("  -> Both JPEG_LIB_VERSION 61 and 62 accepted successfully!\n");
}

static void test_exported_objects(void)
{
    printf("--- Checking Exported Global Objects ---\n");
    CHECK(jpeg_natural_order[0] == 0, "jpeg_natural_order[0] == 0");
    CHECK(jpeg_natural_order[1] == 1, "jpeg_natural_order[1] == 1");
    CHECK(jpeg_natural_order[2] == 8, "jpeg_natural_order[2] == 8");
    CHECK(jpeg_natural_order[3] == 16, "jpeg_natural_order[3] == 16");
    CHECK(jpeg_natural_order[4] == 9, "jpeg_natural_order[4] == 9");
    CHECK(jpeg_natural_order[5] == 2, "jpeg_natural_order[5] == 2");
    CHECK(jpeg_natural_order[63] == 63, "jpeg_natural_order[63] == 63");

    CHECK(jpeg_std_message_table != NULL, "jpeg_std_message_table != NULL");
    CHECK(jpeg_std_message_table[0] != NULL, "jpeg_std_message_table[0] != NULL");
    printf("  -> Global objects jpeg_natural_order and jpeg_std_message_table verified!\n");
}

static void test_compress_decompress_cycle(void)
{
    struct jpeg_compress_struct cinfo;
    struct jpeg_decompress_struct dinfo;
    struct jpeg_error_mgr jerr;
    unsigned char *jpeg_buf = NULL;
    unsigned long jpeg_size = 0;
    int width = 64, height = 64;
    unsigned char *raw_rgb;
    JSAMPROW row_pointer[1];
    int x, y;

    printf("--- Testing End-to-End Compression and Decompression ---\n");

    /* Create test RGB pattern (color gradient) */
    raw_rgb = (unsigned char *)malloc(width * height * 3);
    CHECK(raw_rgb != NULL, "malloc raw_rgb");
    for (y = 0; y < height; y++) {
        for (x = 0; x < width; x++) {
            raw_rgb[(y * width + x) * 3 + 0] = (unsigned char)(x * 4);
            raw_rgb[(y * width + x) * 3 + 1] = (unsigned char)(y * 4);
            raw_rgb[(y * width + x) * 3 + 2] = (unsigned char)((x + y) * 2);
        }
    }

    /* 1. Compress to memory */
    cinfo.err = jpeg_std_error(&jerr);
    jpeg_CreateCompress(&cinfo, JPEG_LIB_VERSION, sizeof(cinfo));
    jpeg_mem_dest(&cinfo, &jpeg_buf, &jpeg_size);

    cinfo.image_width = width;
    cinfo.image_height = height;
    cinfo.input_components = 3;
    cinfo.in_color_space = JCS_RGB;
    jpeg_set_defaults(&cinfo);
    jpeg_set_quality(&cinfo, 90, TRUE);

    jpeg_start_compress(&cinfo, TRUE);
    while (cinfo.next_scanline < cinfo.image_height) {
        row_pointer[0] = &raw_rgb[cinfo.next_scanline * width * 3];
        jpeg_write_scanlines(&cinfo, row_pointer, 1);
    }
    jpeg_finish_compress(&cinfo);
    jpeg_destroy_compress(&cinfo);

    CHECK(jpeg_buf != NULL && jpeg_size > 0, "compressed jpeg output not empty");
    printf("  -> Compressed %dx%d RGB to %lu bytes JPEG\n", width, height, jpeg_size);

    /* 2. Decompress from memory */
    dinfo.err = jpeg_std_error(&jerr);
    jpeg_CreateDecompress(&dinfo, JPEG_LIB_VERSION, sizeof(dinfo));
    jpeg_mem_src(&dinfo, jpeg_buf, jpeg_size);

    CHECK(jpeg_read_header(&dinfo, TRUE) == JPEG_HEADER_OK, "jpeg_read_header OK");
    CHECK(dinfo.image_width == width, "dinfo.image_width matches");
    CHECK(dinfo.image_height == height, "dinfo.image_height matches");

    jpeg_start_decompress(&dinfo);
    while (dinfo.output_scanline < dinfo.output_height) {
        unsigned char row_buf[64 * 3];
        row_pointer[0] = row_buf;
        jpeg_read_scanlines(&dinfo, row_pointer, 1);
    }
    jpeg_finish_decompress(&dinfo);
    jpeg_destroy_decompress(&dinfo);

    free(raw_rgb);
    free(jpeg_buf);
    printf("  -> Decompression verified successfully!\n");
}

int main(void)
{
    printf("=========================================\n");
    printf("  IRIX 6.5.22m libjpeg ABI & Smoke Test  \n");
    printf("=========================================\n");

    test_struct_sizes_and_offsets();
    test_version_acceptance();
    test_exported_objects();
    test_compress_decompress_cycle();

    printf("\n=== ALL ABI TESTS PASSED ===\n");
    return 0;
}
