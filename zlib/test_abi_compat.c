/*
 * test_abi_compat.c - IRIX Binary Compatibility & Regression Test for zlib
 *
 * IMPORTANT: Compile this against the ORIGINAL IRIX /usr/include/zlib.h (1.1.4)
 * or pass -DLEGACY_BUILD, and run it dynamically linked against the modernized
 * libz.so (1.3.2).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
#include "zlib.h"

/* Declare 1.2.1 symbols that were exported by SGI's 1.2.1 libz.so even if
   compiling against the 1.1.4 /usr/include/zlib.h header */
extern unsigned long zlibCompileFlags(void);
extern unsigned long compressBound(unsigned long sourceLen);
extern unsigned long deflateBound(z_streamp strm, unsigned long sourceLen);
extern int gzungetc(int c, gzFile file);
extern void gzclearerr(gzFile file);

/* Internal symbols exported by SGI's libz.so that must remain resolvable */
extern const char * const z_errmsg[10];
extern const unsigned char _dist_code[512];
extern const unsigned char _length_code[256];

static int failures = 0;

#define CHECK(cond, msg) do { \
    if (!(cond)) { \
        fprintf(stderr, "FAIL [%s:%d]: %s\n", __FILE__, __LINE__, msg); \
        failures++; \
    } else { \
        printf("PASS: %s\n", msg); \
    } \
} while (0)

static void test_struct_and_flags(void) {
    unsigned long flags = zlibCompileFlags();
    const char *ver = zlibVersion();
    printf("Runtime zlibVersion() = %s, Header ZLIB_VERSION = %s, flags = 0x%lx\n",
           ver, ZLIB_VERSION, flags);

    CHECK(ver[0] == '1', "Major version is '1'");

#if _MIPS_SIM == _ABI64
    CHECK(sizeof(z_stream) == 112, "sizeof(z_stream) == 112 on n64");
    CHECK(sizeof(z_off_t) == 8, "sizeof(z_off_t) == 8 on n64");
    CHECK((flags & 0xffUL) == 0xa9UL, "zlibCompileFlags low byte == 0xa9 on n64");
#else
    CHECK(sizeof(z_stream) == 56, "sizeof(z_stream) == 56 on o32/n32");
    CHECK(sizeof(z_off_t) == 4, "sizeof(z_off_t) == 4 on o32/n32");
    CHECK((flags & 0xffUL) == 0x55UL, "zlibCompileFlags low byte == 0x55 on o32/n32");
    CHECK(offsetof(z_stream, next_in) == 0, "offsetof(next_in) == 0");
    CHECK(offsetof(z_stream, avail_in) == 4, "offsetof(avail_in) == 4");
    CHECK(offsetof(z_stream, total_in) == 8, "offsetof(total_in) == 8");
    CHECK(offsetof(z_stream, next_out) == 12, "offsetof(next_out) == 12");
    CHECK(offsetof(z_stream, avail_out) == 16, "offsetof(avail_out) == 16");
    CHECK(offsetof(z_stream, total_out) == 20, "offsetof(total_out) == 20");
    CHECK(offsetof(z_stream, msg) == 24, "offsetof(msg) == 24");
    CHECK(offsetof(z_stream, state) == 28, "offsetof(state) == 28");
    CHECK(offsetof(z_stream, zalloc) == 32, "offsetof(zalloc) == 32");
    CHECK(offsetof(z_stream, zfree) == 36, "offsetof(zfree) == 36");
    CHECK(offsetof(z_stream, opaque) == 40, "offsetof(opaque) == 40");
    CHECK(offsetof(z_stream, data_type) == 44, "offsetof(data_type) == 44");
    CHECK(offsetof(z_stream, adler) == 48, "offsetof(adler) == 48");
    CHECK(offsetof(z_stream, reserved) == 52, "offsetof(reserved) == 52");
#endif
}

static void test_legacy_version_init(void) {
    z_stream strm;
    int rc;

    /* Simulate binaries compiled against 1.0.4, 1.1.4, and 1.2.1 headers */
    memset(&strm, 0, sizeof(strm));
    rc = deflateInit_(&strm, Z_DEFAULT_COMPRESSION, "1.1.4", (int)sizeof(z_stream));
    CHECK(rc == Z_OK, "deflateInit_ accepts legacy '1.1.4' version string");
    deflateEnd(&strm);

    memset(&strm, 0, sizeof(strm));
    rc = inflateInit_(&strm, "1.2.1", (int)sizeof(z_stream));
    CHECK(rc == Z_OK, "inflateInit_ accepts legacy '1.2.1' version string");
    inflateEnd(&strm);
}

static void test_checksums_and_streams(void) {
    const char *payload = "Silicon Graphics IRIX 6.5.22m Indigo2 IMPACT R10000 zlib binary compatibility test payload!";
    uLong src_len = (uLong)strlen(payload) + 1;
    uLong crc = crc32(0L, Z_NULL, 0);
    uLong adl = adler32(0L, Z_NULL, 0);
    Bytef comp[512];
    Bytef decomp[512];
    uLongf comp_len = sizeof(comp);
    uLongf decomp_len = sizeof(decomp);
    int rc;

    crc = crc32(crc, (const Bytef *)payload, (uInt)src_len);
    adl = adler32(adl, (const Bytef *)payload, (uInt)src_len);
    CHECK(crc == 0xe493ab33UL, "crc32 known-answer check on big-endian MIPS");
    CHECK(adl == 0x5daa1e3fUL, "adler32 known-answer check on big-endian MIPS");

    rc = compress2(comp, &comp_len, (const Bytef *)payload, src_len, Z_BEST_COMPRESSION);
    CHECK(rc == Z_OK, "compress2 succeeded");

    memset(decomp, 0, sizeof(decomp));
    rc = uncompress(decomp, &decomp_len, comp, comp_len);
    CHECK(rc == Z_OK && decomp_len == src_len && strcmp((char *)decomp, payload) == 0,
          "uncompress round-trip matches exact payload");
}

static void test_gzio_seek_and_tell(void) {
    const char *fname = "/tmp/test_irix_gzio.gz";
    gzFile gf;
    char buf[128];
    z_off_t pos;
    int c;

    gf = gzopen(fname, "wb6");
    CHECK(gf != NULL, "gzopen wb6");
    CHECK(gzputs(gf, "0123456789ABCDEF") == 16, "gzputs 16 bytes");
    CHECK(gzputc(gf, '!') == '!', "gzputc '!'");
    CHECK(gztell(gf) == 17, "gztell after write is 17");
    CHECK(gzclose(gf) == Z_OK, "gzclose after write");

    gf = gzopen(fname, "rb");
    CHECK(gf != NULL, "gzopen rb");
    /* Call function-entry gzgetc (as legacy 1.1.4/1.2.1 binaries do) */
    c = (gzgetc)(gf);
    CHECK(c == '0', "function-entry (gzgetc)(gf) returns '0'");
    CHECK(gzungetc('0', gf) == '0', "gzungetc('0') returns '0'");

    pos = gzseek(gf, (z_off_t)10, SEEK_SET);
    CHECK(pos == 10 && gztell(gf) == 10, "gzseek(10, SEEK_SET) with 32-bit/ABI z_off_t");

    memset(buf, 0, sizeof(buf));
    CHECK(gzread(gf, buf, 7) == 7 && strcmp(buf, "ABCDEF!") == 0,
          "gzread after gzseek reads 'ABCDEF!'");
    CHECK(gzclose(gf) == Z_OK, "gzclose after read");
    remove(fname);
}

static void test_internal_data_symbols(void) {
    CHECK(strcmp(zError(Z_DATA_ERROR), "data error") == 0, "zError(Z_DATA_ERROR) == 'data error'");
    CHECK(z_errmsg[Z_NEED_DICT - Z_DATA_ERROR] != NULL, "z_errmsg array indexing works");
    CHECK(_dist_code[0] == 0 && _length_code[0] == 0, "_dist_code and _length_code tables accessible");
}

int main(void) {
    test_struct_and_flags();
    test_legacy_version_init();
    test_checksums_and_streams();
    test_gzio_seek_and_tell();
    test_internal_data_symbols();

    if (failures == 0) {
        printf("ALL %s ABI COMPATIBILITY TESTS PASSED!\n",
#if _MIPS_SIM == _ABI64
               "N64"
#elif _MIPS_SIM == _ABIN32
               "N32"
#else
               "O32"
#endif
        );
        return 0;
    } else {
        fprintf(stderr, "%d TEST(S) FAILED!\n", failures);
        return 1;
    }
}
