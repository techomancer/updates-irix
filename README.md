# SGI IRIX 6.5.22m Modernization & Security Rollup 2026

> "2026: The Year of the IRIX Desktop"

## 1. Overview
This project provides a comprehensive, production-grade security and modernization update for Silicon Graphics systems running **IRIX 6.5.22m** (MIPS architectures R4x00 through R16000 on IP22, IP24, IP28, IP30, and IP32).

Over the past two decades, foundational IRIX userland libraries and networking protocols fell drastically behind modern standards, leaving systems vulnerable to numerous remote exploits and unable to communicate with modern TLS 1.3 web services or modern OpenSSH servers.

This rollup modernizes the entire core stack from the bottom up—preserving 100% binary ABI compatibility for legacy IRIX software while introducing modern cryptography, contemporary networking, and hardened image format libraries.

## 2. Rollup Components

| Component | Upstream Version | Delivered ABIs | Subsystem / Role |
| :--- | :--- | :--- | :--- |
| **`zlib`** | 1.3.2 | O32, N32, N64 | Core compression library; fixes CVE-2016-9840..43, CVE-2018-25032, CVE-2022-37434 |
| **`libpng`** | 1.2.59 + CVE backports | N32 | Drop-in PNG decoder preserving IRIX 6.5 ABI; fixes all libpng 1.2 CVEs |
| **`libtiff`** | 3.9.7 + CVE backports | N32 | Drop-in TIFF decoder preserving IRIX 6.5 ABI; fixes all post-3.9.7 vulnerabilities |
| **`libjpeg`** | libjpeg-turbo 2.1.5.1 | N32 | IJG v6b drop-in replacement with loop unrolling; dual v6a/v6b ABI compatibility |
| **`openssl-0.9.7`** | 0.9.7m + post-0.9.7m CVEs | O32, N32, N64 | Drop-in hardened OpenSSL for existing system daemons (`/usr/lib32/libcrypto.so.0.9.7`) |
| **`openssl-1.1.1`** | 1.1.1w | N32, N64 | Modern side-by-side OpenSSL (`libcrypto.so.1.1` / `libssl.so.1.1`) with TLS 1.3 & AEAD |
| **`openssh`** | 9.9p2 | N32 | Modern OpenSSH suite (all 13 utilities: `ssh`, `sshd`, `scp`, `sftp`, `ssh-keygen`, etc.) |
| **`terminfo`** | Modern (ncurses 6.x) | Data (`.ti`) | 24 modern terminal definitions (`xterm-256color`, `tmux-256color`, `alacritty`, `kitty`, etc.) |
| **`tzdata`** | 2026e (Sep 2026) | N32 / Fat TZ | Modern IANA timezone database + MIPSpro C99 `zic` and `zdump` compilers |
| **`tcsh`** | 6.24.16 (2025/2026) | N32 MIPS4 | Modern C shell (`/usr/bin/tcsh`), wide characters, UTF-8, color completion |
| **`fonts`** | Modern Open-Source (Type 1) | Data (`.pfa`, `.afm`) | 26 modernized scalable outline fonts (Inconsolata, Hack, Source Code Pro, Liberation, Source Sans) |

## 3. Architecture & Invariants
- **Endianness & Bit-Containers:** All cryptographic algorithms are compiled with pure C routines (`no-asm`) and loop unrolling, preventing host-endianness generator corruption and ensuring 100% bit-exact NIST test vector compliance on big-endian MIPS.
- **ABI Coexistence:**
  - `libcrypto.so.0.9.7` remains intact for OpenLDAP and system tools.
  - `libcrypto.so.1.1` is installed side-by-side for modern software.
- **Thread Safety:** Uniform use of `_SGI_MP_SOURCE` / `(*__oserror())` across all translation units.
- **Patch Semantics:** Packaged into SGI `inst` / `swmgr` format using proper patch attributes (`follows`, `replaces`, `patch`) so installation automatically creates backups in `/var/inst/patchbase/` and enables complete rollback.

## 4. Building & Verification
To build any component individually:
```sh
./build.sh <component> all
```
To run the full rollup packaging and verification:
```sh
./package_rollup.sh
```
