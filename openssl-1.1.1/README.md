# OpenSSL 1.1.1w Modernization for SGI IRIX 6.5.22m

## 1. Overview & Modernization Role
While **OpenSSL 0.9.7** must be retained and hardened for backward compatibility with existing IRIX 6.5.22m system binaries (`/usr/lib32/libcrypto.so.0.9.7` for OpenLDAP and legacy OpenSSH 3.6.1p2), modern cryptographic algorithms and protocols (such as TLS 1.3, SHA-256/512, ChaCha20-Poly1305, Ed25519, and X25519) are essential for modern network connectivity and modern OpenSSH (9.x).

This package delivers **OpenSSL 1.1.1w** (`libcrypto.so.1.1` and `libssl.so.1.1`), built natively with MIPSpro C99 (`cc -c99`) in pure C (`no-asm`) mode with `-O2` loop unrolling for bit-exact NIST correctness on big-endian MIPS architectures.

## 2. Key Architecture & Features
1. **Side-by-Side Coexistence:**
   - Uses SONAME `libcrypto.so.1.1` and `libssl.so.1.1`.
   - Coexists peacefully with `libcrypto.so.0.9.7` without any symbol or file collisions.
2. **Pure C Bit-Exact NIST Correctness (`no-asm`):**
   - The upstream Perl assembly generators (`sha512-mips.pl`, `aes-mips.pl`) contain host-dependent endianness heuristics that mistakenly generate little-endian loads when run on x86_64 cross-environments.
   - Built with `no-asm` and MIPSpro `-O2`, producing 100% bit-for-bit exact NIST test vectors for SHA-256, SHA-512, SHA3-256, AES-256-GCM, and ChaCha20-Poly1305.
3. **Multi-ABI Support:**
   - N32 (`-n32 -mips3`) for standard IRIX userland (`/usr/lib32` or `/usr/local/lib32`).
   - N64 (`-64 -mips4`) for 64-bit execution (`/usr/lib64` or `/usr/local/lib64`).
4. **Protocols & Primitives:**
   - TLS 1.3 protocol engine.
   - SHA-2 (SHA-224, SHA-256, SHA-384, SHA-512) and FIPS 202 SHA-3.
   - Authenticated AEAD ciphers: AES-256-GCM, AES-128-GCM, ChaCha20-Poly1305.
   - RFC 7748 X25519 ECDH key exchange.
   - RSA up to 4096 bits.

## 3. Directory Layout
- `openssl/`: Upstream submodule tracking tag `OpenSSL_1_1_1w`.
- `build/`: Built artifacts:
  - `32/`: N32 libraries (`libcrypto.so.1.1`, `libssl.so.1.1`, `libcrypto.a`, `libssl.a`) and `openssl` CLI binary.
  - `64/`: N64 libraries.
  - `include/`: Multi-ABI headers (`openssl/`).
- `test_crypto111.c`: Comprehensive cryptographic verification test suite.
- `generate_build.py`: Host-side header and pure C configuration + guest build generator.
- `build_irix.sh`: Full build and verification orchestrator.

## 4. Verification Results
Both N32 and N64 builds pass the complete cryptographic verification test suite:
- Message digests (SHA-256, SHA-512, SHA3-256): PASS (100% bit-for-bit exact NIST vectors).
- Authenticated AEAD ciphers (AES-256-GCM, ChaCha20-Poly1305): PASS.
- Key exchange (RFC 7748 X25519 ECDH): PASS.
- RSA-2048 key generation & SHA-256 signature verification: PASS.
- TLS 1.3 context configuration & ciphersuites: PASS.
- CLI binary (`openssl version -a`, `openssl dgst -sha256`): PASS.
- QuickStart ELF metadata audit: PASS (0 unresolved symbols, valid DT_SONAME, clean `.quickstart_info`).
