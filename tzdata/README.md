# SGI IRIX 6.5 Timezone Database Modernization (`tzdata2026e`)

## 1. Overview
The stock timezone database on SGI IRIX 6.5 systems was last updated in 2007 via official SGI patch `patchSG0007204`. Consequently, stock IRIX cannot correctly compute local times or daylight-saving transitions enacted worldwide over the last 19 years (e.g. US Energy Policy Act changes, Europe/London transitions, Russian permanent time shifts, Middle East adjustments, etc.).

This subsystem delivers:
- **`tzdata2026e`**: Upstream IANA Timezone Database (release 2026e, September 2026).
- **`zic` & `zdump` 2026e**: Built with native MIPSpro C99 (`-n32 -mips3 -O2`), replacing the legacy 1990s binaries in `/usr/bin/zic` and `/usr/bin/zdump`.
- **Backward-Compatible Fat Binary Format (`-b fat`)**: Compiles 32-bit and 64-bit transition tables so that stock IRIX `libc.so.1` (`ctime`, `localtime`, `mktime`, `strftime`) correctly handles all modern timezones without requiring any libc modification.

## 2. Directory Layout & Subsystem Mapping
- **System Location:** `/usr/lib/locale/TZ/`
- **Compiler Binaries:** `/usr/bin/zic`, `/usr/bin/zdump`
- **Subsystem:** `patchSG002026.eoe_sw.base` (follows `eoe.sw.base`, replacing `patchSG0007204`).

## 3. Install-time Generation
During installation of `patchSG002026`, an `exitop` invokes the modernized `zic` compiler:
```sh
if [ -x $rbase/usr/bin/zic ]; then
    cd $rbase/usr/lib/locale/TZ
    $rbase/usr/bin/zic -b fat -d $rbase/usr/lib/locale/TZ \
        africa antarctica asia australasia europe northamerica southamerica etcetera factory backward
fi
```
This automatically updates every timezone file in `/usr/lib/locale/TZ/` to the 2026e standard.
