# SGI IRIX 6.5 TCSH Shell Modernization (`tcsh 6.24.16`)

## 1. Overview
Stock SGI IRIX 6.5 systems ship with `tcsh 6.04.00 (Cornell) 93/07/03`, last maintained by SGI in 1993/1994. While functional for basic interactive use, stock `tcsh 6.04` lacks three decades of modern shell features, security hardening, bug fixes, terminal enhancements, and extended syntax capabilities.

This subproject ports and delivers **tcsh 6.24.16** (official release tag `TCSH6_24_16`, Astron, 2025/2026) natively compiled for SGI IRIX 6.5.22m.

Key features of modern `tcsh 6.24.16` on IRIX:
- Full color ls / completion highlighting (`color`, `colorcat`).
- Wide character / multibyte UTF-8 input and display (`wide`, `nls`).
- Modern history editing, search, and spell-checking algorithms.
- Configurable auto-completion, directory stacks, and prompt formats.
- Seamless compatibility with stock IRIX `/bin/csh` and `/bin/tcsh` environment.

## 2. Technical Details & IRIX Porting Fixes
The shell is compiled using native MIPSpro C99 (`cc -n32 -mips4 -O3 -c99`) linking against stock `/usr/lib32/libcurses.so` (`-ltermlib`) and `/usr/lib32/libc.so.1`.

Two targeted patches were engineered for IRIX:
1. **`01_tcsh_irix_strcasestr.patch`**:
   - IRIX `libc.so.1` does not export `strcasestr()`.
   - Provides an inline static implementation using `strncasecmp` in `sh.set.c`.
2. **`02_tcsh_irix_doprnt_overflow.patch`**:
   - In `tc.printf.c`, `doprnt()` defines `INF` as `INT_MAX` (`0x7fffffff`).
   - MIPSpro loop induction optimization converted `for (i = 0; *bp && i < prec; i++)` into a pointer comparison `bp < bp_start + prec`. Because user memory starts around `0x10000000`, `bp_start + 0x7fffffff` overflowed to `0x8fffffff` (signed negative), causing signed comparison `slt` to terminate after exactly 1 character for `%s` and `%S`.
   - Fixed by bypassing the precision loop when `prec == INF`, ensuring full string rendering across all builtins, version reports, and editor keybindings.

## 3. Subsystem Mapping
- **Binary Location:** `/usr/bin/tcsh`
- **Subsystem:** `eoe.sw.base` (`1289434520`)
- **Rollup Subsystem:** `patchSG002026.eoe_sw.base`
- **Patch Binary Tag:** `0x54435348` (`TCSH`)

## 4. Verification
Run inside IRIX:
```csh
/usr/bin/tcsh -c 'echo $version'
```
Expected output:
```
tcsh 6.24.16 (Astron) 2025-07-09 (mipseb-sgi-irix) options wide,nls,dl,al,kan,rh,color,filec
```
