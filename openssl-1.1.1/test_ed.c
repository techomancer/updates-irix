#include <stdio.h>
#include <string.h>
#include <openssl/evp.h>
#include <openssl/err.h>

int main() {
    EVP_PKEY_CTX *pctx = EVP_PKEY_CTX_new_id(EVP_PKEY_ED25519, NULL);
    EVP_PKEY *pkey = NULL;
    int rc;

    rc = EVP_PKEY_keygen_init(pctx);
    printf("keygen_init: %d\n", rc);
    rc = EVP_PKEY_keygen(pctx, &pkey);
    printf("keygen: %d\n", rc);
    EVP_PKEY_CTX_free(pctx);

    size_t publen = 32;
    unsigned char pub[32];
    EVP_PKEY_get_raw_public_key(pkey, pub, &publen);
    printf("pubkey: ");
    for (int i = 0; i < 32; i++) printf("%02x", pub[i]);
    printf("\n");

    unsigned char sig[64];
    size_t siglen = sizeof(sig);
    const char *msg = "Authenticate OpenSSH 9.x Client with Ed25519";

    EVP_MD_CTX *mctx = EVP_MD_CTX_new();
    rc = EVP_DigestSignInit(mctx, NULL, NULL, NULL, pkey);
    printf("DigestSignInit: %d\n", rc);
    rc = EVP_DigestSign(mctx, sig, &siglen, (const unsigned char *)msg, strlen(msg));
    printf("DigestSign: %d, siglen=%lu\n", rc, (unsigned long)siglen);
    printf("sig: ");
    for (int i = 0; i < 64; i++) printf("%02x", sig[i]);
    printf("\n");
    EVP_MD_CTX_free(mctx);

    mctx = EVP_MD_CTX_new();
    rc = EVP_DigestVerifyInit(mctx, NULL, NULL, NULL, pkey);
    printf("DigestVerifyInit: %d\n", rc);
    rc = EVP_DigestVerify(mctx, sig, siglen, (const unsigned char *)msg, strlen(msg));
    printf("DigestVerify: %d\n", rc);
    if (rc != 1) {
        ERR_print_errors_fp(stdout);
    }
    EVP_MD_CTX_free(mctx);

    /* Test X25519 */
    EVP_PKEY *my_key = NULL, *peer_key = NULL;
    pctx = EVP_PKEY_CTX_new_id(EVP_PKEY_X25519, NULL);
    EVP_PKEY_keygen_init(pctx);
    EVP_PKEY_keygen(pctx, &my_key);
    EVP_PKEY_CTX_free(pctx);

    pctx = EVP_PKEY_CTX_new_id(EVP_PKEY_X25519, NULL);
    EVP_PKEY_keygen_init(pctx);
    EVP_PKEY_keygen(pctx, &peer_key);
    EVP_PKEY_CTX_free(pctx);

    unsigned char sec1[32], sec2[32];
    size_t sec1_len = 32, sec2_len = 32;

    pctx = EVP_PKEY_CTX_new(my_key, NULL);
    EVP_PKEY_derive_init(pctx);
    EVP_PKEY_derive_set_peer(pctx, peer_key);
    EVP_PKEY_derive(pctx, sec1, &sec1_len);
    EVP_PKEY_CTX_free(pctx);

    pctx = EVP_PKEY_CTX_new(peer_key, NULL);
    EVP_PKEY_derive_init(pctx);
    EVP_PKEY_derive_set_peer(pctx, my_key);
    EVP_PKEY_derive(pctx, sec2, &sec2_len);
    EVP_PKEY_CTX_free(pctx);

    printf("X25519 derive sec1_len=%lu sec2_len=%lu\n", (unsigned long)sec1_len, (unsigned long)sec2_len);
    if (memcmp(sec1, sec2, 32) == 0) {
        printf("X25519 shared secret match: [OK]\n");
    } else {
        printf("X25519 shared secret MISMATCH!\n");
    }
    EVP_PKEY_free(my_key);
    EVP_PKEY_free(peer_key);

    return 0;
}
