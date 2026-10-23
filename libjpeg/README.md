# IRIX 6.5.22m `libjpeg` Modernization (IJG `v6a` -> `libjpeg-turbo 2.1.5.1` + Dual `v6a`/`v6b` ABI)

## 1. Original IRIX 6.5.22m Baseline

SGI shipped `libjpeg` as part of the standard execution environment and Image Format Library (`ifl_eoe`). The original system binaries were compiled from IJG **v6a** (circa February 1996) with SGI-specific ICC profile extensions:

| Path | ABI / ISA | Base Address | IVERSION | Original Symbols | DT_NEEDED |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/usr/lib/libjpeg.so` | `o32` (`mips2`) | `0x0dc00000` / `0x098d0000` | `sgi1.0` | 100 funcs, 2 objects | `libc.so.1` |
| `/usr/lib32/libjpeg.so` | `n32` (`mips3`) | `0x0dc00000` / `0x09ab0000` | `sgi1.0` | 100 funcs, 2 objects | `libc.so.1` |
| `/usr/lib64/libjpeg.so` | `n64` (`mips3`) | `0x02130000` | `sgi1.0` | *(Missing from stock IRIX!)* | `libc.so.1` |

These DSOs are dynamically linked by core IRIX imaging components including `/usr/lib32/libiflJFIF.so`, `/usr/lib32/libiflNITF.so`, `/usr/lib32/libtiff.so`, and `/usr/sbin/cocojpeg`.

> [!NOTE]
> Stock IRIX 6.5.22m never shipped `/usr/lib64/libjpeg.so`, even though `/usr/lib64/libtiff.so` had a DT_NEEDED entry referencing it! Our modernization delivers a complete 64-bit `libjpeg.so` and `libjpeg.a`, resolving this longstanding omission.

---

## 2. Architecture & Engine Selection: Why `libjpeg-turbo 2.1.5.1`

We selected **`libjpeg-turbo 2.1.5.1`** as the modernization engine because:
1. **Plain-C Architecture:** Tag 2.1.5.1 provides clean, high-performance plain-C implementations without the C++ and build complexity introduced in 3.x.
2. **SIMD Considerations on SGI MIPS:** SGI MIPS processors (R4000 through R16000) do not implement MIPS DSPr2 or Ingenic MSA SIMD extensions. The build is configured with plain C (`-DWITH_SIMD=OFF`, `jsimd_none.c`). Under MIPSpro `-O2`, the heavily unrolled, cache-conscious C algorithms significantly outperform stock IJG v6a/v6b.
3. **ABI Adaptability:** libjpeg-turbo can be surgically adjusted to preserve SGI's exact structure offsets while retaining arithmetic coding, memory sources/destinations (`jpeg_mem_src`, `jpeg_mem_dest`), and modern bug fixes.

---

## 3. Forensic Discovery: SGI Shipped `v6a` (`61`), NOT `v6b` (`62`)

A common assumption among IRIX developers was that SGI userland targeted IJG v6b (`JPEG_LIB_VERSION 62`). Detailed forensic analysis of `/usr/lib32/libiflJFIF.so`, `/usr/lib32/libtiff.so`, and `/usr/sbin/cocojpeg` revealed the truth:

```c
/* Disassembly of libiflJFIF.so at initialization: */
li      $a1, 61          /* version = JPEG_LIB_VERSION 61 (v6a!) */
li      $a2, 360         /* structsize = 360 bytes (32-bit v6a compress struct) */
jal     jpeg_CreateCompress
```

Stock SGI binaries call:
- `jpeg_CreateCompress(cinfo, 61, 360)`
- `jpeg_CreateDecompress(cinfo, 61, 464)`

### The Struct Layout Trap in `v6b`
Between v6a and v6b, IJG made subtle ABI-breaking changes:
1. **`client_data` Insertion:** IJG v6b added `void *client_data;` into `jpeg_common_fields`. This shifted every single subsequent member in `jpeg_compress_struct` and `jpeg_decompress_struct` by 4 bytes (32-bit) / 8 bytes (64-bit). In `libiflJFIF.so`, accessing `cinfo->dest` at offset 20 read garbage instead of the destination manager, causing an immediate crash.
2. **`script_space` Addition:** In `jpeg_compress_struct`, v6b added an internal array `jpeg_scan_info script_space[16]`, inflating `sizeof(jpeg_compress_struct)` from 360 to 372 bytes.
3. **`marker_list` Addition:** In `jpeg_decompress_struct`, v6b added `jpeg_saved_marker_ptr marker_list`, inflating `sizeof(jpeg_decompress_struct)` from 464 to 472 bytes.
4. **SGI ICC Profile Extensions:** SGI added `prof_info` (an internal `read_icc_profile_data` struct) at offset 460 in `jpeg_decompress_struct`, and exported `write_icc_profile` and `add_chunk`.

---

## 4. Dual-Version Compatibility & ABI Restoration

In `patches/irix-abi.patch`, we achieved simultaneous **100% byte-for-byte binary compatibility with SGI v6a** and **functional compatibility with modern v6b** applications:

### A. Exact SGI v6a Structure Offsets
- Removed `client_data` from `jpeg_common_fields`, restoring `dest` to offset 20 (32-bit) / 32 (64-bit), `image_width` to offset 24 (32-bit) / 40 (64-bit), and all subsequent fields to their exact original offsets.
- Removed `script_space` from `jpeg_compress_struct`; `jpeg_simple_progression` now allocates scan space dynamically via `alloc_small`.
- Relocated `marker_list` from `jpeg_decompress_struct` into internal `struct jpeg_marker_reader` in `jpegint.h`.
- Restored `cinfo->prof_info` in `jpeg_decompress_struct` at offset 460 (32-bit) / 616 (64-bit).
- Resulting sizes:
  - `sizeof(struct jpeg_compress_struct)` = **360 bytes** (32-bit) / **496 bytes** (64-bit)
  - `sizeof(struct jpeg_decompress_struct)` = **464 bytes** (32-bit) / **624 bytes** (64-bit)

### B. Dual Version & Struct Size Acceptance
In `jcapimin.c` and `jdapimin.c`, `jpeg_CreateCompress` and `jpeg_CreateDecompress` were updated to accept:
- **Version 61** (IRIX 6.5.22m stock) and **Version 62** (v6b).
- Struct sizes 360 / 372 (32-bit) and 496 / 520 (64-bit).
- Zeroing is clamped to `min(structsize, sizeof(*cinfo))` to ensure stack buffers allocated by v6a callers (360 bytes) are never overwritten.

### C. SGI ICC Profile Functions
- Re-exported `write_icc_profile` as a binary-compatible wrapper to libjpeg-turbo's `jpeg_write_icc_profile`.
- Re-exported `add_chunk` matching SGI's original signature and behavior.
- Provided modern standard ICC functions (`jpeg_read_icc_profile`, `jpeg_write_icc_profile`).

---

## 5. Verification & Audit Results

### A. Struct Layout & ABI Smoke Tests (`test_abi_compat.c`)
Compiled and executed natively under IRIX across all 3 ABIs (`o32`, `n32`, `n64`):
```text
=========================================
  IRIX 6.5.22m libjpeg ABI & Smoke Test  
=========================================
--- Checking Structure Sizes and Member Offsets ---
  -> Struct sizes and all 31 critical offsets MATCH SGI 6.5 ABI perfectly!
--- Checking Dual-Version Acceptance (61 and 62) ---
  -> Both JPEG_LIB_VERSION 61 and 62 accepted successfully!
--- Checking Exported Global Objects ---
  -> Global objects jpeg_natural_order and jpeg_std_message_table verified!
--- Testing End-to-End Compression and Decompression ---
  -> Compressed 64x64 RGB to 1142 bytes JPEG
  -> Decompression verified successfully!

=== ALL ABI TESTS PASSED ===
```

### B. Live System Integration Tests
Tested against existing SGI IRIX system binaries linked to `libiflJFIF.so`:
- `/usr/sbin/imgcopy /usr/share/data/images/TestPattern.rgb /tmp/test_pattern.jpg` -> **SUCCESS**
- `/usr/sbin/imginfo -v /tmp/test_pattern.jpg` -> **SUCCESS** (correctly reports JFIF format and 4 sub-image resolutions: 40x30, 80x60, 160x120, 320x240)

### C. Symbol & ABI Compatibility Audit (`irix_lib_audit.py compare-tree`)
Comparison of modernized DSOs against original IRIX 6.5.22m system libraries:
- **`o32` (`mips2`)**: 100/100 original functions preserved, 2/2 objects preserved, 0 missing symbols. Result: **PASS**
- **`n32` (`mips3`)**: 100/100 original functions preserved, 2/2 objects preserved, 0 missing symbols. Result: **PASS**
- **`n64` (`mips3`)**: 189 functions exported, full QuickStart registry alignment, 0 glibc/non-IRIX symbols. Result: **PASS**

---

## 6. Build Instructions

To rebuild inside the IRIX guest from the host repository:
```bash
cd shared/updates-irix/libjpeg
./build_irix.sh
```
This automatically stages the source tree, applies `irix-abi.patch`, compiles `o32`, `n32`, and `n64` targets with MIPSpro 7.4.4m, runs `rqs32`/`rqs64`, executes the native verification suite, and performs the ELF ABI audit.
