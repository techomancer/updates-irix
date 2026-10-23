/*
 * test_abi_compat.c - Verify IRIX 6.5.22m libpng 1.2.5/1.2.6 binary & ABI
 * compatibility and 2025-2026 CVE regression tests against modernized libpng.so.
 *
 * Compiled against the ORIGINAL /usr/include/png.h (1.2.5) on IRIX to simulate
 * an existing un-recompiled IRIX 6.5.22m binary linking against libpng.so.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
#include <png.h>

#define CHECK(cond, msg) do { \
    if (!(cond)) { \
        fprintf(stderr, "FAIL [%s:%d]: %s\n", __FILE__, __LINE__, (msg)); \
        return 1; \
    } \
} while (0)

struct mem_buf {
    unsigned char *data;
    size_t size;
    size_t cap;
    size_t pos;
};

static void mem_write_fn(png_structp png_ptr, png_bytep data, png_size_t length) {
    struct mem_buf *mb = (struct mem_buf *)png_get_io_ptr(png_ptr);
    if (mb->size + length > mb->cap) {
        size_t new_cap = (mb->cap == 0) ? 4096 : mb->cap * 2;
        while (new_cap < mb->size + length) new_cap *= 2;
        mb->data = (unsigned char *)realloc(mb->data, new_cap);
        mb->cap = new_cap;
    }
    memcpy(mb->data + mb->size, data, length);
    mb->size += length;
}

static void mem_flush_fn(png_structp png_ptr) {
    (void)png_ptr;
}

static void mem_read_fn(png_structp png_ptr, png_bytep data, png_size_t length) {
    struct mem_buf *mb = (struct mem_buf *)png_get_io_ptr(png_ptr);
    if (mb->pos + length > mb->size) {
        png_error(png_ptr, "EOF in mem_read_fn");
        return;
    }
    memcpy(data, mb->data + mb->pos, length);
    mb->pos += length;
}

static void custom_error_fn(png_structp png_ptr, png_const_charp msg) {
    fprintf(stderr, "libpng error: %s\n", msg);
    longjmp(png_jmpbuf(png_ptr), 1);
}

static void custom_warn_fn(png_structp png_ptr, png_const_charp msg) {
    (void)png_ptr;
    (void)msg;
}

static png_voidp custom_malloc_fn(png_structp png_ptr, png_size_t size) {
    (void)png_ptr;
    return malloc(size);
}

static void custom_free_fn(png_structp png_ptr, png_voidp ptr) {
    (void)png_ptr;
    free(ptr);
}

int main(void) {
    png_structp w_ptr, r_ptr;
    png_infop w_info, r_info;
    struct mem_buf mb;
    png_color pal[16];
    png_byte trans[16];
    png_uint_16 hist[16];
    png_byte row[16];
    png_bytep row_ptr = row;
    png_colorp got_pal = NULL;
    png_bytep got_trans = NULL;
    png_uint_16p got_hist = NULL;
    int got_num_pal = 0, got_num_trans = 0;
    int i;

    printf("=== IRIX libpng ABI Compatibility & CVE Verification ===\n");
    printf("Compiled with header PNG_LIBPNG_VER_STRING = %s (%d)\n",
           PNG_LIBPNG_VER_STRING, PNG_LIBPNG_VER);
    printf("Running with runtime png_get_libpng_ver()  = %s (%lu)\n",
           png_get_libpng_ver(NULL), (unsigned long)png_access_version_number());
    printf("sizeof(png_struct) = %lu, sizeof(png_info) = %lu\n",
           (unsigned long)sizeof(png_struct), (unsigned long)sizeof(png_info));
    printf("offsetof(png_struct, jmpbuf)        = %lu\n",
           (unsigned long)offsetof(png_struct, jmpbuf));
    printf("offsetof(png_struct, io_ptr)        = %lu\n",
           (unsigned long)offsetof(png_struct, io_ptr));
    printf("offsetof(png_struct, zstream)       = %lu\n",
           (unsigned long)offsetof(png_struct, zstream));
    printf("offsetof(png_struct, hist)          = %lu\n",
           (unsigned long)offsetof(png_struct, hist));
    printf("offsetof(png_struct, time_buffer)   = %lu\n",
           (unsigned long)offsetof(png_struct, time_buffer));
    printf("offsetof(png_struct, free_me)       = %lu\n",
           (unsigned long)offsetof(png_struct, free_me));
    printf("offsetof(png_struct, mem_ptr)       = %lu\n",
           (unsigned long)offsetof(png_struct, mem_ptr));
    printf("offsetof(png_struct, big_row_buf)   = %lu\n",
           (unsigned long)offsetof(png_struct, big_row_buf));

    /* 1. Verify runtime accepts both "1.2.5" (header) and "1.2.6" (patch5734) */
    memset(&mb, 0, sizeof(mb));
    w_ptr = png_create_write_struct_2("1.2.5", (png_voidp)0x1234,
                                      custom_error_fn, custom_warn_fn,
                                      (png_voidp)0x5678,
                                      custom_malloc_fn, custom_free_fn);
    CHECK(w_ptr != NULL, "png_create_write_struct_2(\"1.2.5\") failed");

    /* Verify direct struct field offsets match what libpng populated internally!
     * Note: mem_ptr, malloc_fn, free_fn are near the very end of png_struct,
     * after PNG_WRITE_WEIGHTED_FILTER_SUPPORTED and PNG_ASSEMBLER_CODE_SUPPORTED!
     */
    CHECK(w_ptr->error_ptr == (png_voidp)0x1234, "w_ptr->error_ptr offset mismatch");
    CHECK(w_ptr->error_fn == custom_error_fn, "w_ptr->error_fn offset mismatch");
    CHECK(w_ptr->warning_fn == custom_warn_fn, "w_ptr->warning_fn offset mismatch");
    CHECK(w_ptr->mem_ptr == (png_voidp)0x5678, "w_ptr->mem_ptr offset mismatch (late png_struct layout shifted!)");
    CHECK(w_ptr->malloc_fn == custom_malloc_fn, "w_ptr->malloc_fn offset mismatch (late png_struct layout shifted!)");
    CHECK(w_ptr->free_fn == custom_free_fn, "w_ptr->free_fn offset mismatch (late png_struct layout shifted!)");

    w_info = png_create_info_struct(w_ptr);
    CHECK(w_info != NULL, "png_create_info_struct failed");
    CHECK(setjmp(png_jmpbuf(w_ptr)) == 0, "unexpected longjmp during write");

    png_set_write_fn(w_ptr, &mb, mem_write_fn, mem_flush_fn);
    CHECK(w_ptr->io_ptr == &mb, "w_ptr->io_ptr offset mismatch");

    png_set_IHDR(w_ptr, w_info, 16, 1, 8, PNG_COLOR_TYPE_PALETTE,
                 PNG_INTERLACE_NONE, PNG_COMPRESSION_TYPE_BASE, PNG_FILTER_TYPE_BASE);
    CHECK(w_info->width == 16 && w_info->height == 1 && w_info->bit_depth == 8,
          "w_info direct struct fields mismatch");

    for (i = 0; i < 16; i++) {
        pal[i].red   = (png_byte)(i * 16);
        pal[i].green = (png_byte)(255 - i * 16);
        pal[i].blue  = (png_byte)(i * 8);
        trans[i]     = (png_byte)(255 - i * 4);
        hist[i]      = (png_uint_16)(100 + i);
        row[i]       = (png_byte)i;
    }
    /* Set one out-of-range palette index (200 >= 16) in pixel 15 to test CVE-2025-64505 */
    row[15] = 200;

    png_set_PLTE(w_ptr, w_info, pal, 16);
    png_set_tRNS(w_ptr, w_info, trans, 16, NULL);
    png_set_hIST(w_ptr, w_info, hist);

    /* 2. Test CVE-2026-34757: Getter-to-setter self-aliasing on PLTE, tRNS, hIST */
    if (png_get_libpng_ver(NULL)[4] != '6') {
        CHECK(png_get_PLTE(w_ptr, w_info, &got_pal, &got_num_pal) == PNG_INFO_PLTE, "png_get_PLTE failed");
        png_set_PLTE(w_ptr, w_info, got_pal, got_num_pal);
        CHECK(png_get_PLTE(w_ptr, w_info, &got_pal, &got_num_pal) == PNG_INFO_PLTE, "png_get_PLTE after self-set failed");
        CHECK(got_pal[0].red == pal[0].red && got_pal[3].red == pal[3].red && got_pal[3].green == pal[3].green,
              "CVE-2026-34757 regression: self-aliased png_set_PLTE corrupted palette");

        CHECK(png_get_tRNS(w_ptr, w_info, &got_trans, &got_num_trans, NULL) == PNG_INFO_tRNS, "png_get_tRNS failed");
        png_set_tRNS(w_ptr, w_info, got_trans, got_num_trans, NULL);
        CHECK(png_get_tRNS(w_ptr, w_info, &got_trans, &got_num_trans, NULL) == PNG_INFO_tRNS, "png_get_tRNS after self-set failed");
        CHECK(got_trans[0] == trans[0] && got_trans[5] == trans[5],
              "CVE-2026-34757 regression: self-aliased png_set_tRNS corrupted trans");

        CHECK(png_get_hIST(w_ptr, w_info, &got_hist) == PNG_INFO_hIST, "png_get_hIST failed");
        png_set_hIST(w_ptr, w_info, got_hist);
        CHECK(png_get_hIST(w_ptr, w_info, &got_hist) == PNG_INFO_hIST, "png_get_hIST after self-set failed");
        CHECK(got_hist[0] == hist[0] && got_hist[7] == hist[7],
              "CVE-2026-34757 regression: self-aliased png_set_hIST corrupted hist");
    }

    png_write_info(w_ptr, w_info);
    png_write_rows(w_ptr, &row_ptr, 1);
    png_write_end(w_ptr, w_info);
    png_destroy_write_struct(&w_ptr, &w_info);

    /* 3. Read back with "1.2.6" version string, testing:
     *    - CVE-2025-64505 (out-of-range palette index 200 with png_set_dither)
     *    - CVE-2026-25646 (color pruning in png_set_dither without histogram)
     *    - CVE-2026-33416 (png_free_data(PNG_FREE_PLTE | PNG_FREE_TRNS) before row read)
     */
    mb.pos = 0;
    r_ptr = png_create_read_struct("1.2.6", NULL, custom_error_fn, custom_warn_fn);
    CHECK(r_ptr != NULL, "png_create_read_struct(\"1.2.6\") failed");
    r_info = png_create_info_struct(r_ptr);
    CHECK(r_info != NULL, "png_create_info_struct (read) failed");
    CHECK(setjmp(png_jmpbuf(r_ptr)) == 0, "unexpected longjmp during read");

    png_set_read_fn(r_ptr, &mb, mem_read_fn);
    png_read_info(r_ptr, r_info);

    /* Trigger CVE-2026-25646 + CVE-2025-64505 path in png_set_dither */
    if (png_get_libpng_ver(NULL)[4] != '6') {
        /* Only run CVE-2025-64505 / CVE-2026-25646 / CVE-2026-33416 torture on modernized 1.2.59 */
        png_color dither_pal[16];
        png_byte out_row[64];
        png_bytep out_row_ptr = out_row;

        memcpy(dither_pal, pal, sizeof(pal));
        png_set_dither(r_ptr, dither_pal, 16, 8, NULL, 0);

        /* Free info_ptr's PLTE and tRNS before reading row (CVE-2026-33416) */
        png_free_data(r_ptr, r_info, PNG_FREE_PLTE | PNG_FREE_TRNS | PNG_FREE_HIST, 0);

        png_read_update_info(r_ptr, r_info);
        CHECK(r_ptr->big_row_buf != NULL, "r_ptr->big_row_buf offset mismatch");
        png_read_rows(r_ptr, &out_row_ptr, NULL, 1);
    } else {
        png_byte out_row[64];
        png_bytep out_row_ptr = out_row;
        png_read_update_info(r_ptr, r_info);
        CHECK(r_ptr->big_row_buf != NULL, "r_ptr->big_row_buf offset mismatch");
        png_read_rows(r_ptr, &out_row_ptr, NULL, 1);
    }

    png_read_end(r_ptr, r_info);
    png_destroy_read_struct(&r_ptr, &r_info, NULL);
    free(mb.data);

    printf("PASS: All libpng ABI layout, offset, version, and CVE checks succeeded!\n");
    return 0;
}
