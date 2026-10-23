/*
 * test_abi_compat.c - IRIX 6.5.22m OpenSSL 0.9.7 ABI & Crypto Verification Test
 *
 * Verifies byte-exact ABI structure sizes and member offsets for OpenSSL 0.9.7
 * data structures, tests cryptographic primitives (MD5, SHA-1, AES-128-CBC, RSA),
 * validates SSL context management, and checks ABI preservation stubs.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>

#include <openssl/opensslv.h>
#include <openssl/crypto.h>
#include <openssl/bn.h>
#include <openssl/evp.h>
#include <openssl/rsa.h>
#include <openssl/dsa.h>
#include <openssl/dh.h>
#include <openssl/ssl.h>
#include <openssl/x509.h>

/* KSSL stubs declared in libssl */
extern void *kssl_ctx_new(void);
extern void *kssl_ctx_free(void *kctx);

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
    printf("--- Checking Structure Sizes and Offsets ---\n");

#if defined(_MIPS_SZLONG) && _MIPS_SZLONG == 64
    /* 64-bit ABI (n64) */
    printf("  ABI mode: N64 (64-bit)\n");
    CHECK(sizeof(BIGNUM) == 24, "sizeof(BIGNUM) must be 24 bytes on n64");
    CHECK(sizeof(EVP_MD_CTX) == 32, "sizeof(EVP_MD_CTX) must be 32 bytes on n64");

    CHECK_OFFSET(BIGNUM, d, 0, "BIGNUM.d");
    CHECK_OFFSET(BIGNUM, top, 8, "BIGNUM.top");
    CHECK_OFFSET(BIGNUM, dmax, 12, "BIGNUM.dmax");
    CHECK_OFFSET(BIGNUM, neg, 16, "BIGNUM.neg");
    CHECK_OFFSET(BIGNUM, flags, 20, "BIGNUM.flags");

    CHECK_OFFSET(EVP_MD_CTX, digest, 0, "EVP_MD_CTX.digest");
    CHECK_OFFSET(EVP_MD_CTX, engine, 8, "EVP_MD_CTX.engine");
    CHECK_OFFSET(EVP_MD_CTX, flags, 16, "EVP_MD_CTX.flags");
    CHECK_OFFSET(EVP_MD_CTX, md_data, 24, "EVP_MD_CTX.md_data");

    CHECK_OFFSET(EVP_CIPHER_CTX, cipher, 0, "EVP_CIPHER_CTX.cipher");
    CHECK_OFFSET(EVP_CIPHER_CTX, app_data, 96, "EVP_CIPHER_CTX.app_data");

    CHECK_OFFSET(RSA, n, 32, "RSA.n");
    CHECK_OFFSET(RSA, e, 40, "RSA.e");
    CHECK_OFFSET(RSA, d, 48, "RSA.d");

#else
    /* 32-bit ABI (o32 / n32) */
    printf("  ABI mode: 32-bit (o32 / n32)\n");
    CHECK(sizeof(BIGNUM) == 20, "sizeof(BIGNUM) must be 20 bytes on 32-bit");
    CHECK(sizeof(EVP_MD_CTX) == 16, "sizeof(EVP_MD_CTX) must be 16 bytes on 32-bit");

    CHECK_OFFSET(BIGNUM, d, 0, "BIGNUM.d");
    CHECK_OFFSET(BIGNUM, top, 4, "BIGNUM.top");
    CHECK_OFFSET(BIGNUM, dmax, 8, "BIGNUM.dmax");
    CHECK_OFFSET(BIGNUM, neg, 12, "BIGNUM.neg");
    CHECK_OFFSET(BIGNUM, flags, 16, "BIGNUM.flags");

    CHECK_OFFSET(EVP_MD_CTX, digest, 0, "EVP_MD_CTX.digest");
    CHECK_OFFSET(EVP_MD_CTX, engine, 4, "EVP_MD_CTX.engine");
    CHECK_OFFSET(EVP_MD_CTX, flags, 8, "EVP_MD_CTX.flags");
    CHECK_OFFSET(EVP_MD_CTX, md_data, 12, "EVP_MD_CTX.md_data");

    CHECK_OFFSET(EVP_CIPHER_CTX, cipher, 0, "EVP_CIPHER_CTX.cipher");
    CHECK_OFFSET(EVP_CIPHER_CTX, app_data, 84, "EVP_CIPHER_CTX.app_data");

    CHECK_OFFSET(RSA, n, 16, "RSA.n");
    CHECK_OFFSET(RSA, e, 20, "RSA.e");
    CHECK_OFFSET(RSA, d, 24, "RSA.d");
#endif

    printf("  -> Structure sizes and member offsets match SGI 0.9.7 ABI!\n");
}

static void test_digests(void)
{
    EVP_MD_CTX ctx;
    unsigned char md[EVP_MAX_MD_SIZE];
    unsigned int md_len;
    char hex[128];
    unsigned int i;
    const char *msg = "The quick brown fox jumps over the lazy dog";

    printf("--- Testing Message Digests (SHA-1 and MD5) ---\n");

    /* 1. SHA-1 test */
    EVP_MD_CTX_init(&ctx);
    EVP_DigestInit_ex(&ctx, EVP_sha1(), NULL);
    EVP_DigestUpdate(&ctx, msg, strlen(msg));
    EVP_DigestFinal_ex(&ctx, md, &md_len);
    EVP_MD_CTX_cleanup(&ctx);

    CHECK(md_len == 20, "SHA-1 digest length must be 20 bytes");
    for (i = 0; i < md_len; i++) sprintf(&hex[i * 2], "%02x", md[i]);
    CHECK(strcmp(hex, "2fd4e1c67a2d28fced849ee1bb76e7391b93eb12") == 0,
          "SHA-1 digest mismatch");
    printf("  -> SHA-1: %s [OK]\n", hex);

    /* 2. MD5 test */
    EVP_MD_CTX_init(&ctx);
    EVP_DigestInit_ex(&ctx, EVP_md5(), NULL);
    EVP_DigestUpdate(&ctx, msg, strlen(msg));
    EVP_DigestFinal_ex(&ctx, md, &md_len);
    EVP_MD_CTX_cleanup(&ctx);

    CHECK(md_len == 16, "MD5 digest length must be 16 bytes");
    for (i = 0; i < md_len; i++) sprintf(&hex[i * 2], "%02x", md[i]);
    CHECK(strcmp(hex, "9e107d9d372bb6826bd81d3542a419d6") == 0,
          "MD5 digest mismatch");
    printf("  -> MD5  : %s [OK]\n", hex);
}

static void test_symmetric_cipher(void)
{
    EVP_CIPHER_CTX ctx;
    unsigned char key[16] = "0123456789abcdef";
    unsigned char iv[16]  = "fedcba9876543210";
    const char *plaintext = "Silicon Graphics IRIX 6.5.22m Cryptography Subsystem Test";
    unsigned char ciphertext[128];
    unsigned char decrypted[128];
    int outlen1 = 0, outlen2 = 0;
    int cipher_len = 0, dec_len = 0;
    int plain_len = strlen(plaintext);

    printf("--- Testing Symmetric Cipher (AES-128-CBC) ---\n");

    /* Encrypt */
    EVP_CIPHER_CTX_init(&ctx);
    CHECK(EVP_EncryptInit_ex(&ctx, EVP_aes_128_cbc(), NULL, key, iv) == 1,
          "EVP_EncryptInit_ex failed");
    CHECK(EVP_EncryptUpdate(&ctx, ciphertext, &outlen1, (const unsigned char *)plaintext, plain_len) == 1,
          "EVP_EncryptUpdate failed");
    CHECK(EVP_EncryptFinal_ex(&ctx, ciphertext + outlen1, &outlen2) == 1,
          "EVP_EncryptFinal_ex failed");
    EVP_CIPHER_CTX_cleanup(&ctx);
    cipher_len = outlen1 + outlen2;

    /* Decrypt */
    outlen1 = 0; outlen2 = 0;
    EVP_CIPHER_CTX_init(&ctx);
    CHECK(EVP_DecryptInit_ex(&ctx, EVP_aes_128_cbc(), NULL, key, iv) == 1,
          "EVP_DecryptInit_ex failed");
    CHECK(EVP_DecryptUpdate(&ctx, decrypted, &outlen1, ciphertext, cipher_len) == 1,
          "EVP_DecryptUpdate failed");
    CHECK(EVP_DecryptFinal_ex(&ctx, decrypted + outlen1, &outlen2) == 1,
          "EVP_DecryptFinal_ex failed");
    EVP_CIPHER_CTX_cleanup(&ctx);

    dec_len = outlen1 + outlen2;
    decrypted[dec_len] = '\0';
    CHECK(dec_len == plain_len, "Decrypted length matches plaintext length");
    CHECK(strcmp((char *)decrypted, plaintext) == 0, "Decrypted plaintext matches original");
    printf("  -> AES-128-CBC: Encrypted %d bytes -> Decrypted %d bytes [OK]\n", plain_len, dec_len);
}

static void test_asymmetric_rsa(void)
{
    RSA *rsa;
    unsigned char msg_hash[20];
    unsigned char sig[128];
    unsigned int siglen = 0;

    printf("--- Testing Asymmetric Cryptography (RSA Keygen, Sign & Verify) ---\n");

    memset(msg_hash, 0x5a, sizeof(msg_hash));
    rsa = RSA_generate_key(1024, RSA_F4, NULL, NULL);
    CHECK(rsa != NULL, "RSA_generate_key failed");
    CHECK(RSA_size(rsa) == 128, "RSA key size must be 128 bytes (1024 bits)");

    /* Sign hash */
    CHECK(RSA_sign(NID_sha1, msg_hash, sizeof(msg_hash), sig, &siglen, rsa) == 1,
          "RSA_sign failed");
    CHECK(siglen == 128, "RSA signature length must be 128 bytes");

    /* Verify signature */
    CHECK(RSA_verify(NID_sha1, msg_hash, sizeof(msg_hash), sig, siglen, rsa) == 1,
          "RSA_verify failed");

    /* Tamper test */
    sig[10] ^= 0xff;
    CHECK(RSA_verify(NID_sha1, msg_hash, sizeof(msg_hash), sig, siglen, rsa) == 0,
          "RSA_verify must reject tampered signature");

    RSA_free(rsa);
    printf("  -> RSA 1024-bit Sign / Verify / Tamper Detection [OK]\n");
}

static void test_ssl_context_and_stubs(void)
{
    SSL_CTX *ctx;
    void *kctx;

    printf("--- Testing SSL Context & ABI Preservation Stubs ---\n");

    SSL_library_init();
    SSL_load_error_strings();

    ctx = SSL_CTX_new(SSLv23_client_method());
    CHECK(ctx != NULL, "SSL_CTX_new(SSLv23_client_method) failed");
    SSL_CTX_free(ctx);
    printf("  -> SSL_CTX_new / SSL_CTX_free [OK]\n");

    /* Verify KSSL preservation stubs */
    kctx = kssl_ctx_new();
    CHECK(kctx == NULL, "kssl_ctx_new stub must return NULL");
    kssl_ctx_free(kctx);
    printf("  -> KSSL ABI preservation stubs verified [OK]\n");
}

int main(void)
{
    printf("====================================================\n");
    printf("  IRIX 6.5.22m OpenSSL 0.9.7 ABI & Verification Test\n");
    printf("  Version: %s\n", SSLeay_version(SSLEAY_VERSION));
    printf("====================================================\n");

    test_struct_sizes_and_offsets();
    test_digests();
    test_symmetric_cipher();
    test_asymmetric_rsa();
    test_ssl_context_and_stubs();

    printf("\n=== ALL OPENSSL 0.9.7 ABI TESTS PASSED ===\n");
    return 0;
}
