# IRIX 6.5.22m `libpng` Modernization (`1.2.5`/`1.2.6` -> `1.2.59` + 2025–2026 CVE Backports)

## 1. Original IRIX 6.5.22m & `patchSG0005734` Baseline

SGI shipped `libpng` as part of the Image Format Library (`ifl_eoe` / `ifl_dev`) and updated the runtime DSOs in `patchSG0005734` (November 2004) without updating `/usr/include`:

| Path | Subsystem | Version | Details |
| :--- | :--- | :--- | :--- |
| `/usr/include/png.h`, `/usr/include/pngconf.h` | `ifl_dev.sw.c++` | **1.2.5** (Oct 3, 2002) | Byte-for-byte identical to upstream `v1.2.5` (0 SGI edits) |
| `/usr/lib/libpng.so` (`o32`, `mips2`) | `patchSG0005734.ifl_eoe_sw.c++` | **1.2.6** (Aug 15, 2004) | `SONAME: libpng.so`, `IVERSION: sgi1.0`, base `0x0dc00000`, 330 funcs + 29 objects |
| `/usr/lib32/libpng.so` (`n32`, `mips3`) | `patchSG0005734.ifl_eoe_sw.c++` | **1.2.6** (Aug 15, 2004) | `SONAME: libpng.so`, `IVERSION: sgi1.0`, base `0x0dc00000`, 330 funcs + 29 objects |
| `/usr/lib64/libpng.so` (`n64`, `mips3`) | `patchSG0005734.ifl_eoe_sw64.c++` | **1.2.6** (Aug 15, 2004) | `SONAME: libpng.so`, `IVERSION: sgi1.0`, base `0x02130000`, 330 funcs + 29 objects |

All three DSOs declare `DT_NEEDED: libz.so, libm.so, libc.so.1` and are dynamically loaded by `/usr/lib*/libiflPNG.so` (`imginfo`, `imgcopy`, `imgview`, desktop file typing) and third-party binaries.

---

## 2. Why `/usr/lib*/libpng.so` Must Stay on the `1.2.x` Series (`v1.2.59`)

Unlike `zlib` (which maintained a single backwards-compatible ABI from `1.1.x` through `1.3.2`), `libpng` broke ABI compatibility across major series (`1.2` -> `1.4` -> `1.5` -> `1.6`):

1. **Hard Runtime Version Check in `png_create_read_struct` / `png_create_write_struct`:**
   Applications compiled against `/usr/include/png.h` pass `PNG_LIBPNG_VER_STRING` (`"1.2.5"`) as `user_png_ver`. `libpng` enforces:
   ```c
   if (user_png_ver == NULL || user_png_ver[0] != png_libpng_ver[0] ||
       (user_png_ver[0] == '1' && user_png_ver[2] != png_libpng_ver[2]) || ...)
       png_error(png_ptr, "Incompatible libpng version in application and library");
   ```
   Any `1.4.x`, `1.5.x`, or `1.6.x` library immediately aborts when called by an existing `1.2.x` binary.
2. **Publicly Exposed `png_struct` (`struct png_struct_def`) and `png_info` (`struct png_info_struct`):**
   - In `1.2.x`, both structures are publicly defined in `png.h`. `png_jmpbuf(png_ptr)` expands directly to `((png_ptr)->jmpbuf)` (offset 0), and applications directly access `info_ptr->width`, `info_ptr->height`, `info_ptr->bit_depth`, `png_ptr->io_ptr`, etc.
   - In `1.4.x`, deprecated functions (`png_check_sig`, `png_info_init`) were removed and `png_struct` fields were reorganized.
   - In `1.5.0+` and `1.6.x`, `png_struct` and `png_info` were made completely opaque and over 40 internal `png_push_*` / `png_read_*` / `png_write_*` symbols exported by SGI's `libpng.so` were removed.

Upstream maintained the `libpng12` branch with security backports for 13 years after IRIX's `1.2.6`, culminating in **`v1.2.59` (September 28, 2017)**, which includes over 30 CVE fixes (`CVE-2004-0597` through `CVE-2017-12652`).

---

## 3. ABI Fixes & Post-2017 CVE Backports in `patches/irix-abi-and-cves.patch`

### A. Restoring Exact `1.2.5`/`1.2.6` ABI & Symbol Compatibility in `1.2.59`
Our automated struct-offset and symbol audit between `v1.2.5`/`v1.2.6` and `v1.2.59` caught two upstream changes inside `libpng12` that we fix in `patches/irix-abi-and-cves.patch`:
1. **`struct png_struct_def` middle-field deletion in `1.2.54` (`commit d5b51a49a`):**
   In July 2015 (`1.2.54beta01`), upstream deleted 7 unused `PNG_WRITE_WEIGHTED_FILTER_SUPPORTED` fields (`heuristic_method`, `num_prev_filters`, `prev_filters`, `filter_weights`, `inv_filter_weights`, `filter_costs`, `inv_filter_costs`) from the middle of `struct png_struct_def`. That shifted every subsequent member of `png_struct` (`time_buffer`, `free_me`, `user_chunk_ptr`, `mem_ptr`, `malloc_fn`, `free_fn`, `big_row_buf`, etc.) by **24 bytes on `o32`/`n32` and 48 bytes on `n64`**. Restoring those 7 struct members in `png.h` keeps every single `1.2.5`/`1.2.6` member offset in `png_struct` and `png_info` **100% identical**.
2. **6 internal functions removed from `.dynsym` between `1.2.20` and `1.2.48`:**
   SGI's `libpng.so` (`1.2.6`) exported `png_init_mmx_flags`, `png_push_handle_tEXt`, `png_push_read_tEXt`, `png_push_handle_zTXt`, `png_push_read_zTXt`, and `png_push_handle_unknown` (whose prototypes remained in `png.h`). We restore thin compatibility wrappers in `png.c` and `pngpread.c` so all **330 functions and 29 global objects** match SGI's `.dynsym` table with zero missing symbols.

### B. Backported 2025–2026 CVEs from `libpng 1.6.51`–`1.6.59`
We audited all security fixes in `libpng 1.6.33` through `1.6.59` (2017–2026). While many recent `1.6` CVEs only affect the `1.6`-only Simplified API (`png_image_*`) or ARM NEON intrinsics, **5 post-2017 vulnerabilities hit core `1.2.59` code** and are backported in `patches/irix-abi-and-cves.patch`:

| Vulnerability | Upstream `1.6` Commit | Description & Backport in `1.2.59` |
| :--- | :--- | :--- |
| **CVE-2025-64505** (Moderate) | `6a528eb5f` (`1.6.51`) | Heap buffer overflow in `png_do_dither` / `png_set_dither` (`pngrtran.c`): allocate `dither_index` to `PNG_MAX_PALETTE_LENGTH` (256 bytes) instead of `num_palette` bytes so malformed PNGs with out-of-range palette indices cannot read/write out of bounds. |
| **CVE-2026-25646** (High) | `01d03b845` (`1.6.55`) | Heap buffer overflow in `png_set_dither` (`pngrtran.c`): store original palette indices (`png_ptr->palette_to_index[i]` / `[j]`) in the color-distance hash table so color pruning cannot drive `max_d` past the 769-element `hash` array. |
| **CVE-2026-33416** (High) | `230192697`, `7ea9eea88`, `d4c4e49eb` (`1.6.56`–`1.6.58`) | Use-after-free via pointer aliasing in `png_set_PLTE`, `png_set_tRNS`, `png_set_hIST`, and `png_set_dither` (`pngset.c`, `pngrtran.c`, `pngwrite.c`): allocate independent buffers for `png_ptr` and `info_ptr` (and sync `info_ptr->palette` in `png_read_transform_info`) so freeing `info_ptr` data via `png_free_data()` never leaves dangling pointers in `png_ptr`. |
| **CVE-2026-34757** (Medium) | `398cbe3df`, `55d20aaa3` (`1.6.57`) | Use-after-free in `png_set_PLTE`, `png_set_tRNS`, `png_set_hIST`, `png_set_text_2`, `png_set_sPLT`, and `png_set_unknown_chunks` (`pngset.c`) when a caller passes a pointer obtained from `png_get_*` back into `png_set_*` (getter-to-setter self-aliasing). |
| **64-bit rowbytes & double-free hardening** | `2c974860c`, `cae474558`, `aa77ef38c` (`1.6.57`–`1.6.59`) | Prevent 32-bit overflow before `(png_size_t)` cast in `png_do_expand_palette` (`pngrtran.c`) on 64-bit (`n64`), clear `big_row_buf`/`prev_row` pointers immediately after `png_free` before `png_malloc` in `png_read_start_row` (`pngrutil.c`), and clear `zstream.next_in` on `png_inflate` exit. |
