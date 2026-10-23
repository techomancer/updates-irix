#include <stdio.h>
#include <string.h>
#include <openssl/evp.h>

static void hex_dump(const char *label, const unsigned char *buf, size_t len) {
    printf("%s: ", label);
    for (size_t i = 0; i < len; i++) printf("%02x", buf[i]);
    printf("\n");
}

int main() {
    /* Alice private key RFC 7748 */
    const unsigned char alice_priv[32] = {
        0x77,0x07,0x6d,0x0a,0x73,0x18,0xa5,0x7d,0x3c,0x16,0xc1,0x72,0x51,0xb2,0x66,0x45,
        0xdf,0x4c,0x2f,0x87,0xeb,0xc0,0x99,0x2a,0xb1,0x77,0xfb,0xa5,0x1d,0xb9,0x2c,0x2a
    };
    /* Bob public key RFC 7748 */
    const unsigned char bob_pub[32] = {
        0xd7,0xa6,0x30,0x79,0x55,0x8b,0x78,0x3a,0xae,0xa3,0x54,0xd7,0x6c,0x4e,0xbe,0x23,
        0xab,0xdc,0xe6,0x82,0x86,0x1d,0x8e,0xb6,0xbb,0x17,0x39,0x02,0x96,0xd2,0x5f,0x13
    };
    /* Base point 9 */
    const unsigned char base_point[32] = {
        9,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0
    };

    unsigned char alice_pub[32];
    size_t pub_len = 32;

    EVP_PKEY *a_priv = EVP_PKEY_new_raw_private_key(EVP_PKEY_X25519, NULL, alice_priv, 32);
    EVP_PKEY_get_raw_public_key(a_priv, alice_pub, &pub_len);
    hex_dump("Calculated Alice pub (via keygen/ge_scalarmult_base)", alice_pub, 32);
    printf("Expected   Alice pub                                : 8520f0098930a754748b7ddcb43ef75a0dbf3a0d26381af4eba4a98eaa9b4e6a\n");

    /* Now derive with base point 9 using EVP_PKEY_derive */
    EVP_PKEY *b_base = EVP_PKEY_new_raw_public_key(EVP_PKEY_X25519, NULL, base_point, 32);
    EVP_PKEY_CTX *ctx = EVP_PKEY_CTX_new(a_priv, NULL);
    EVP_PKEY_derive_init(ctx);
    EVP_PKEY_derive_set_peer(ctx, b_base);
    unsigned char pub_from_derive[32];
    size_t dlen = 32;
    EVP_PKEY_derive(ctx, pub_from_derive, &dlen);
    hex_dump("Calculated Alice pub (via derive/x25519_scalar_mult)", pub_from_derive, 32);
    EVP_PKEY_CTX_free(ctx);
    EVP_PKEY_free(b_base);

    /* Now derive shared secret with Bob */
    EVP_PKEY *b_pub = EVP_PKEY_new_raw_public_key(EVP_PKEY_X25519, NULL, bob_pub, 32);
    ctx = EVP_PKEY_CTX_new(a_priv, NULL);
    EVP_PKEY_derive_init(ctx);
    EVP_PKEY_derive_set_peer(ctx, b_pub);
    unsigned char shared[32];
    dlen = 32;
    EVP_PKEY_derive(ctx, shared, &dlen);
    hex_dump("Calculated Shared secret (Alice x Bob)             ", shared, 32);
    printf("Expected   Shared secret                            : 6a7b2f29cf08c93585c0099481c7f5157b92d797ffd2e9fec35ad28fa3ff463b\n");
    EVP_PKEY_CTX_free(ctx);
    EVP_PKEY_free(b_pub);
    EVP_PKEY_free(a_priv);

    return 0;
}
