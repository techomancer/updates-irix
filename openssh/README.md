# OpenSSH 9.9p2 Modernization for SGI IRIX 6.5.22m

## 1. Overview & Modernization Role
IRIX 6.5.22m ships with OpenSSH 3.6.1p2 (circa 2003), linked against OpenSSL 0.9.7. This legacy daemon is deprecated and unsafe on modern networks: it lacks support for modern ciphers (ChaCha20-Poly1305, AES-GCM), modern MACs (UMAC-128, HMAC-SHA2), modern key exchanges (Curve25519, SNTRUP761 post-quantum hybrid), and modern public key formats (Ed25519, ECDSA). Modern SSH clients reject connections to OpenSSH 3.6.1p2 by default due to deprecated ssh-dss / diffie-hellman-group1-sha1.

This package delivers **OpenSSH Portable 9.9p2** built natively on SGI IRIX 6.5.22m with MIPSpro C99 (`cc -c99 -n32 -mips3 -O2`), linked dynamically against modernized **OpenSSL 1.1.1w** (`libcrypto.so.1.1`) and modernized **zlib 1.3.2** (`libz.so`).

## 2. Delivered Utilities
All 13 OpenSSH utilities are compiled in MIPS-3 N32 ELF format:
- **Client Binaries (`build/bin/`):**
  - `ssh`: OpenSSH SSH client
  - `scp`: Secure copy client (SFTP protocol backend)
  - `sftp`: Interactive SFTP file transfer client
  - `ssh-add`: Private key addition to authentication agent
  - `ssh-agent`: Authentication agent daemon
  - `ssh-keygen`: Public/private key generation, signature signing & verification
  - `ssh-keyscan`: Remote SSH public host key collector
- **Server Binaries (`build/sbin/`):**
  - `sshd`: OpenSSH SSH master listening daemon
- **Privsep & Helper Binaries (`build/libexec/`):**
  - `sshd-session`: Privilege-separated session daemon (OpenSSH 9.8+ architecture)
  - `sftp-server`: SFTP server subsystem
  - `ssh-keysign`: Hostbased authentication helper
  - `ssh-pkcs11-helper`: PKCS#11 smartcard helper
  - `ssh-sk-helper`: FIDO/U2F security key helper

## 3. Key Technical Challenges & Solutions
1. **Thread-Safe `errno` Divergence & `atomicio` Broken Pipe:**
   - *Problem:* Loading private keys via `sshkey_load_private` failed with `SSH_ERR_SYSTEM_ERROR (-24)` reporting `Broken pipe` on EOF. `atomicio.c` wrote to the global `extern int errno = EPIPE`, but `sshbuf-io.c` checked `(*__oserror())` (activated transitively via `<pthread.h>` in OpenSSL headers), seeing `0` instead of `EPIPE`.
   - *Solution:* Added `#define _SGI_MP_SOURCE 1` to `includes.h` and `config.h`, ensuring that all translation units uniformly use thread-local `errno` via `(*__oserror())`.
2. **Ed25519 Constant-Time Sign Extraction vs. MIPSpro C99 Optimizer:**
   - *Problem:* In the bundled SUPERCOP `ed25519.c` reference implementation, `negative(signed char b)` was implemented as `unsigned long long x = b; x >>= 63; return x;`. MIPSpro C99's optimizer reasoned that an 8-bit `char` cannot have bit 63 set, and dead-code eliminated `negative()` to return constant `0`. Consequently, negative window digits in `sc25519_window3` were never negated, causing all Ed25519 keypair generation and signing calculations to diverge from NIST/RFC 8032 vectors.
   - *Solution:* Replaced `negative(b)` with `((unsigned char)b) >> 7`, which cleanly and portably extracts bit 7 (the sign bit) in constant time without branches or 64-bit integer conversion warnings. Verified bit-for-bit against OpenSSL 1.1.1 and Linux host `ssh-keygen`.
3. **ML-KEM768 Frontend Incompatibility:**
   - *Problem:* The Eurydice-generated ML-KEM768 C code triggers a fatal compiler bug in MIPSpro C99 (`fec: eok_lvalue_from_struct_rvalue not implemented`).
   - *Solution:* Disabled ML-KEM768 on `__sgi` in `defines.h`, while keeping post-quantum hybrid `sntrup761x25519-sha512` active, which compiles cleanly and passes all tests.
4. **Anonymous Memory Mapping (`MAP_ANON`):**
   - *Problem:* `sshkey_prekey_alloc` failed when `MAP_ANON` was missing on IRIX.
   - *Solution:* Added fallback to map `/dev/zero` via `open("/dev/zero", O_RDWR)` with `MAP_PRIVATE`.
5. **SGI Make Continuation Bug:**
   - *Problem:* In `Makefile.in`, `FIXALGORITHMSCMD= $(SHELL) $(srcdir)/fixalgorithms $(SED) \ @UNSUPPORTED_ALGORITHMS@` left a trailing backslash when `@UNSUPPORTED_ALGORITHMS@` was empty. SGI `/bin/make` treated the following `all:` target as part of the variable assignment.
   - *Solution:* Collapsed `FIXALGORITHMSCMD` to a single line.

## 4. Verification & Testing
The automated test suite in `build_irix.sh` executes the following checks on the live IRIX guest:
- **Key Generation & Digital Signatures:**
  - RSA (2048-bit / 3072-bit): PASS (`Good "file" signature`)
  - ECDSA (`ecdsa-sha2-nistp256`): PASS (`Good "file" signature`)
  - ED25519 (`ssh-ed25519`): PASS (`Good "file" signature`)
  - Cross-platform verification: Signatures generated on IRIX verify identically on Linux x86_64 and vice versa.
- **Daemon & Protocol Negotiation:**
  - `sshd` runs cleanly in daemon mode with privilege separation (`/var/empty` and user `sshd`).
  - `ssh-keyscan` negotiates `SSH-2.0-OpenSSH_9.9` and retrieves RSA, ECDSA, and ED25519 host keys.
- **End-to-End Sessions:**
  - Loopback SSH login authenticated with ED25519 user key: PASS (`IRIX64 purple 6.5 IP28`).
  - SCP file transfer with SHA/cmp verification: PASS.
  - SFTP subsystem session and directory listing: PASS.
- **ELF DSO Audit:**
  - All 13 binaries are verified MIPS-3 N32 ELF binaries with clean QuickStart metadata, resolving `libcrypto.so.1.1`, `libz.so`, and `libc.so.1`.
