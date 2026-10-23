# zlib 1.3.2 Modernization for SGI IRIX 6.5.22m

## 1. Overview & Modernization Role
`zlib` is one of the most foundational shared libraries on SGI IRIX, sitting at the base of the userland dependency graph. It is used directly by the Image Format Library (`ifl_eoe`), OpenSSL, OpenSSH, X11 utilities, PNG/TIFF format decoders, and countless third-party applications.

IRIX 6.5.22m originally shipped with an ancient zlib 1.1.x / 1.2.3 build, vulnerable to numerous critical memory corruption vulnerabilities discovered over the past two decades.

This package provides a modernized **zlib 1.3.2** drop-in replacement across all three MIPS ELF ABIs (**O32**, **N32**, and **N64**), fully patched against all known CVEs while maintaining 100% binary ABI compatibility with existing IRIX binaries.

## 2. ABI Compatibility & Engineering Details
1. **ABI Drop-in Invariant:**
   - Exact symbol export matching: exports all public zlib symbols (`deflate`, `inflate`, `deflateInit_`, `inflateInit_`, `compress`, `uncompress`, `crc32`, `adler32`, etc.) with identical undecorated names and calling conventions.
   - Preserves `z_stream` struct layout and alignment across O32 (32-bit pointers), N32 (32-bit pointers with 64-bit registers), and N64 (64-bit pointers and registers).
   - SONAME matching: delivers `libz.so.1` with `libz.so` symlink matching original IRIX dynamic tag expectations.
2. **Tri-ABI Delivery:**
   - **O32 (`-32 -mips2`):** Installed to `/usr/lib/libz.so` (and `/usr/lib/libz.a`) for legacy IRIX 5.3 and early 6.x binaries.
   - **N32 (`-n32 -mips3`):** Installed to `/usr/lib32/libz.so` (and `/usr/lib32/libz.a`) for standard IRIX 6.5 applications.
   - **N64 (`-64 -mips4`):** Installed to `/usr/lib64/libz.so` (and `/usr/lib64/libz.a`) for 64-bit applications.
3. **Hardened Against All Known Vulnerabilities:**
   - **CVE-2016-9840:** Out-of-bounds pointer arithmetic in `inftrees.c`.
   - **CVE-2016-9841:** Out-of-bounds pointer arithmetic in `inffast.c`.
   - **CVE-2016-9842:** Undefined left shift of negative values in `inflate.c`.
   - **CVE-2016-9843:** Big-endian CRC32 calculation undefined behaviour in `crc32.c`.
   - **CVE-2018-25032:** Out-of-bounds write / heap corruption in `deflate.c` during arbitrary window manipulation.
   - **CVE-2022-37434:** Heap buffer overflow in `inflate.c` (`inflateGetHeader`) via excessive extra fields.

## 3. Directory Layout
- `zlib/`: Upstream submodule tracking `v1.3.2`.
- `orig/`: Pristine original IRIX 6.5.22m DSOs extracted for binary comparison:
  - `32/libz.so` (O32)
  - `n32/libz.so` (N32)
  - `64/libz.so` (N64)
- `patches/`: Applied patches for IRIX build and ABI constraints.
- `build/`: Built artifacts:
  - `32/`: Modernized O32 DSO and static archive.
  - `n32/`: Modernized N32 DSO and static archive.
  - `64/`: Modernized N64 DSO and static archive.
- `test_abi_compat.c`: Multi-ABI validation test suite testing compression, decompression, Adler32, CRC32, and struct alignment.
- `build_irix.sh`: Native guest compilation and test orchestrator.

## 4. Verification Results
- **O32, N32, and N64 ABI Suites:** All compression levels, dictionary inflates, Adler-32, and CRC-32 checksums verified bit-exact on live IRIX guest.
- **QuickStart ELF Audit:** PASS (DT_SONAME matches, `.quickstart_info` verified clean, no symbol preemption hazards).
