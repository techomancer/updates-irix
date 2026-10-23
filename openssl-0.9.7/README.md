# OpenSSL 0.9.7 Modernization & Hardening for SGI IRIX 6.5.22m

## 1. Overview & Motivation
IRIX 6.5.22m originally shipped OpenSSL 0.9.7d in `/usr/lib32/libcrypto.so.0.9.7` and `/usr/lib32/libssl.so.0.9.7`.
Key system components on IRIX depend directly on these specific library names:
- **OpenSSH 3.6.1p2** (`ssh`, `scp`, `sftp`, `sshd`, `ssh-keygen`, `ssh-agent`) dynamically links `libcrypto.so.0.9.7`.
- **OpenLDAP subsystem** (`/usr/lib32/libldap.so.3`, `/usr/lib32/libldap_r.so.3`, `ldapsearch`, `slapd`) links both `libcrypto.so.0.9.7` and `libssl.so.0.9.7`.
- **OpenSSL CLI** (`/usr/bin/openssl`) links both DSOs.

Because these system binaries hardcode `DT_NEEDED: libcrypto.so.0.9.7` and `libssl.so.0.9.7` (not unversioned `libcrypto.so`), upgrading or replacing OpenSSL with an incompatible ABI would break core system utilities.

This project delivers a drop-in, 100% ABI-compatible, security-hardened OpenSSL 0.9.7 implementation for IRIX 6.5.22m.

## 2. Key Technical Improvements & Hardening
1. **Security Vulnerability Fixes:**
   - Backported fix for **CVE-2008-5077** (`EVP_VerifyFinal` return value <= 0 check in SSL client/server handshakes).
   - Backported fix for **CVE-2009-0590** (multi-byte ASN.1 string length validation in `a_strex.c`).
2. **KSSL Decoupling & ABI Preservation:**
   - SGI's original `libssl.so.0.9.7` was dynamically linked against `/usr/lib32/libkrb5.so.3` because Kerberos support was enabled, exporting 19 `kssl_*` entry points.
   - We implemented ABI preservation stubs for all 19 `kssl_*` symbols inside `libssl.so.0.9.7`. This eliminates the runtime dependency on `libkrb5.so.3` while preserving 100% symbol compatibility for any binary expecting them.
3. **Tri-ABI Architecture (O32, N32, N64):**
   - SGI only shipped N32 libraries (`/usr/lib32`).
   - We build and deliver all three MIPS ELF ABIs:
     - `O32` (`mips2`, `/usr/lib`) for legacy IRIX 5.3/6.2 binaries.
     - `N32` (`mips3`, `/usr/lib32`) for standard IRIX 6.5 userland.
     - `N64` (`mips3`, `/usr/lib64`) for 64-bit applications.
4. **MIPS III/IV Assembly Optimization:**
   - Native handwritten MIPS3 assembly (`crypto/bn/asm/mips3.s` by Andy Polyakov) is assembled for both N32 and N64.
   - Provides accelerated 64-bit arithmetic (`bn_add_words`, `bn_sub_words`, `bn_mul_words`, `bn_div_words`, `bn_div_3_words`, `bn_sqr_words`, `bn_mul_comba*`, `bn_sqr_comba*`).
   - Pure C fallback (`bn_asm.c`) is retained for O32 (MIPS2).
5. **Exact QuickStart Base Address Matching:**
   - Base addresses aligned with SGI `/usr/lib32/so_locations`:
     - `libcrypto.so.0.9.7`: `0xbf0000`
     - `libssl.so.0.9.7`: `0x6540000`

## 3. Directory Layout
- `openssl/`: Upstream OpenSSL submodule tracking `OpenSSL_0_9_7-stable`.
- `patches/`:
  - `cve-fixes-and-stubs.patch`: Backported security patches and `kssl_*` ABI stubs.
  - `opensslconf.h`: Tri-ABI header with proper ABI-specific bignum definitions.
- `orig/32/`: Original SGI IRIX 6.5.22m N32 libraries for byte and ABI audits.
- `build/`: Built artifacts:
  - `libcrypto.so.0.9.7`, `libssl.so.0.9.7`, `libcrypto.a`, `libssl.a` (O32)
  - `32/` (N32 libraries and `openssl` CLI)
  - `64/` (N64 libraries)
  - `include/` (Multi-ABI headers)
- `generate_build.py`: Source staging and guest script generator.
- `build_irix.sh`: Full orchestration script.
- `test_abi_compat.c`: Comprehensive ABI verification test suite.

## 4. Verification Suite
1. **Structure Size & Offset Validation:**
   - Validates `sizeof(BIGNUM)`, `sizeof(EVP_MD_CTX)`, `sizeof(EVP_CIPHER_CTX)`, `sizeof(RSA)` and exact member offsets across 32-bit and 64-bit ABIs.
2. **Cryptographic Algorithm Functional Tests:**
   - SHA-1 and MD5 NIST test vector verification.
   - AES-128-CBC encryption and decryption round-trip.
   - RSA 1024-bit key generation, SHA-1 signing, signature verification, and tamper detection.
3. **Live System Binary Compatibility:**
   - `/usr/bin/ldapsearch -V` loads modernized `libssl.so.0.9.7` and `libcrypto.so.0.9.7` without errors.
   - `/usr/bin/openssl` (original SGI binary) dynamically loads modernized libraries.
4. **ELF Metadata & Export Audit:**
   - Validated with `irix_lib_audit.py compare-tree` against original SGI binaries.
