# IRIX 6.5.22m `libtiff` Modernization (`3.4beta037` -> `3.9.7` + ABI Preservation + CVE Backports)

## 1. Original IRIX 6.5.22m Baseline

SGI shipped `libtiff` as part of the Image Format Library (`ifl_eoe` / `ifl_dev`) and desktop graphics subsystems. The original system binaries were compiled from Sam Leffler's `v3.4beta037` (circa 1997) using MIPSpro:

| Path | ABI / ISA | Base Address | IVERSION | Original Symbols | DT_NEEDED |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/usr/lib/libtiff.so` | `o32` (`mips2`) | `0x0dc00000` | `sgi1.1` | 137 funcs, 9 objects | `libjpeg.so, libm.so, libc.so.1` |
| `/usr/lib32/libtiff.so` | `n32` (`mips3`) | `0x0dc00000` | `sgi1.1` | 137 funcs, 9 objects | `libjpeg.so, libm.so, libc.so.1` |
| `/usr/lib64/libtiff.so` | `n64` (`mips3`) | `0x02130000` | `sgi1.1` | 137 funcs, 9 objects | `libjpeg.so, libm.so, libc.so.1` |

These DSOs are dynamically loaded by `/usr/lib*/libiflTIFF.so`, `/usr/lib*/libxtiff.so`, `/usr/sbin/imgcopy`, `/usr/sbin/imginfo`, `/usr/sbin/imgview`, and third-party imaging packages.

---

## 2. Architecture & Version Selection: Why `v3.9.7`

While `libtiff 4.x` introduced BigTIFF, it broke binary compatibility by changing `toff_t` from 32-bit to 64-bit, altering struct layouts, and modifying internal tag handling. Existing IRIX binaries (`libiflTIFF.so`, `libxtiff.so`) do not treat `TIFF*` as opaque pointers and directly access structure internals.

We chose **`libtiff v3.9.7`** (the final release of the 3.x branch) as the base because:
1. It retains the standard 32-bit `toff_t` classic TIFF ABI.
2. It incorporates 15 years of upstream bug fixes, LZW improvements, Deflate/ZIP support, and security hardening over `3.4beta037`.
3. Through surgical ABI patches based on SGI DWARF forensics, it can be made **100% byte-for-byte ABI-compatible** with existing IRIX binaries.

---

## 3. Deep DWARF Forensics & ABI Corrections

Using DWARF symbol information extracted from IRIX system libraries (`libiflTIFF.so`, `libxtiff.so`) and SGI headers, we identified critical ABI breaks introduced between `3.4beta037` and `3.9.7`. All of these were resolved in `patches/irix-abi-and-cves.patch`:

### A. Directory Struct Offset Alignment (`FIELD_SETLONGS 3` vs `4`)
In upstream `3.5+`, `FIELD_SETLONGS` was increased from 3 to 4 to expand the field bitmask, adding 4 bytes before `td_imagewidth`.
- SGI's `libiflTIFF.so` directly reads `tif->tif_dir.td_imagewidth` at offset 12 (+36 from `struct tiff`).
- With `FIELD_SETLONGS 4`, `td_imagewidth` shifted by 4 bytes, causing `libiflTIFF.so` to read zero and fail with `iflBADATTRIBUTES`.
- **Fix:** Restored `FIELD_SETLONGS 3` and inserted ABI padding so `sizeof(TIFFDirectory)` matches the exact SGI size of **264 bytes** (32-bit) and **392 bytes** (64-bit).

### B. `TIFFFaxTabEnt` Table Dimensions
In upstream `3.5+`, `Param` in `TIFFFaxTabEnt` was widened from `uint16` to `uint32`, doubling `sizeof(TIFFFaxTabEnt)` from 4 to 8 bytes.
- This doubled the exported table sizes (`TIFFFaxMainTable` from 512 to 1024 bytes, `TIFFFaxWhiteTable` from 16 KB to 32 KB, `TIFFFaxBlackTable` from 32 KB to 64 KB).
- **Fix:** Restored `uint16 Param` in `tif_fax3.h` so all three tables match the exact original symbol sizes.

### C. `_TIFFRGBAImage` Structure Size
Upstream `3.5+` added four fields (`req_orientation`, `cielab`, `row_offset`, `col_offset`) to `_TIFFRGBAImage`, increasing its size from 68 to 84 bytes on 32-bit. Applications allocating this structure on the stack or in heap structures suffered buffer overruns.
- **Fix:** Restored `sizeof(_TIFFRGBAImage)` to **68 bytes** (32-bit) / **112 bytes** (64-bit) and relocated new state fields into `struct tiff`.

### D. `struct tiff` Member Offsets for `libxtiff.so`
SGI's `libxtiff.so` directly accesses internal members of `struct tiff`:
- `tif_name` at offset 0
- `tif_flags` at offset 12 (`o32`/`n32`) / 16 (`n64`)
- `tif_dir` at offset 24 (`o32`/`n32`) / 32 (`n64`)
- `tif_clientdir` at offset 296 (`o32`/`n32`) / 432 (`n64`)
- `tif_tagmethods` at offset 492 (`o32`/`n32`) / 776 (`n64`)
Our patch preserves these exact offsets while retaining `3.9.7` functionality.

### E. Endianness & Codec Symbol Table
- Autoconf header defaults assumed little-endian when unconfigured; we explicitly defined `WORDS_BIGENDIAN 1` to prevent byte-swapping errors on MIPS (`"Not a TIFF file, bad version number 10752"`).
- `_TIFFBuiltinCODECS` table was adjusted to exclude dynamic codecs so its size matches the original **204 bytes** (32-bit) / **408 bytes** (64-bit).
- Exported `const int tiffDataWidth[13]` (52 bytes) and provided backward-compatible wrappers for `_TIFFSetupFieldInfo`, `TIFFFindFieldInfo`, and `TIFFFieldWithTag`.

---

## 4. Backported Post-3.9.7 CVE Security Fixes

We backported critical security patches addressing vulnerabilities discovered after the 3.9.7 release:

| CVE / Fix | Affected Source | Description |
| :--- | :--- | :--- |
| **CVE-2011-0192** | `tif_fax3.c` | Follow-up bounds check for Fax3 `EXPAND2D` buffer overruns on corrupt CCITT images. |
| **CVE-2014-8129** | `tif_next.c` | Validate `BitsPerSample == 2` in `NeXTPreDecode` before processing scanlines. |
| **CVE-2015-8665** / **CVE-2015-8683** | `tif_getimage.c` | Check `td_samplesperpixel` and color channels to prevent out-of-bounds heap reads. |
| **CVE-2016-3990** | `tif_pixarlog.c` | Heap buffer overflow check in `PixarLogEncode` on excessive row sizes. |
| **CVE-2016-5875** | `tif_luv.c` | Enforce `td_samplesperpixel == 1` in `LogL16InitState` to prevent heap corruption. |
| **CVE-2018-8905** | `tif_lzw.c` | Prevent heap buffer overrun in `LZWDecodeCompat` on corrupt LZW streams. |
| **CVE-2019-14973** | `tif_aux.c` | Prevent integer overflow leading to heap buffer overflow in `_TIFFCheckMalloc`. |

---

## 5. Verification & Audit Results

### A. Symbol & ABI Compatibility Audit (`irix_lib_audit.py compare-tree`)
All 3 ABIs pass 100% backwards-compatibility verification against the original IRIX 6.5.22m DSOs:
- **`o32` (`mips2`)**: 137/137 original functions preserved, 9/9 objects preserved, 0 missing symbols. Result: **PASS**
- **`n32` (`mips3`)**: 137/137 original functions preserved, 9/9 objects preserved, 0 missing symbols. Result: **PASS**
- **`n64` (`mips3`)**: 137/137 original functions preserved, 9/9 objects preserved, 0 missing symbols. Result: **PASS**

### B. Struct Layout Verification (`test_abi_compat`)
Compiled and executed natively under IRIX across all 3 ABIs (`o32`, `n32`, `n64`):
- `sizeof(TIFF)`: 580 bytes (32-bit), 920 bytes (64-bit) — **MATCH**
- `sizeof(TIFFDirectory)`: 264 bytes (32-bit), 392 bytes (64-bit) — **MATCH**
- `sizeof(TIFFFaxTabEnt)`: 4 bytes — **MATCH**
- `sizeof(TIFFRGBAImage)`: 68 bytes (32-bit), 112 bytes (64-bit) — **MATCH**
- `sizeof(TIFFCodec)`: 12 bytes (32-bit), 24 bytes (64-bit) — **MATCH**
- `_TIFFBuiltinCODECS`: 204 bytes (32-bit), 408 bytes (64-bit) — **MATCH**

### C. Live System Binary Integration Tests
Tested against IRIX system binaries linked to `libiflTIFF.so` and `libxtiff.so`:
- `/usr/sbin/imgcopy /usr/share/data/images/TestPattern.rgb /tmp/sample.tif` -> **SUCCESS**
- `/usr/sbin/imginfo /tmp/sample.tif` -> **SUCCESS** (verifies dimensional and photometric tags read correctly)

---

## 6. How to Build

Run the automated build script on the host or inside the guest environment:
```bash
./build_irix.sh
```
This script stages the upstream `libtiff` submodule (`v3.9.7`), applies `patches/irix-abi-and-cves.patch`, compiles `o32`, `n32`, and `n64` shared and static libraries using native MIPSpro 7.4.4m inside the running IRIX guest, and runs `rqs32`/`rqs64` quickstart.
