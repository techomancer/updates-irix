# SGI IRIX 6.5 Modern Typography (`Xfonts`)

## 1. Overview
The stock SGI IRIX 6.5 font subsystem in `/usr/lib/X11/fonts/` provides legacy bitmap fonts and classic 1990s PostScript Type 1 outlines (such as Adobe Utopia, Charter, Helvetica, Times, Courier, and Avant Garde). Stock `Xsgi` and SGI `xfs` do not natively render TrueType (`.ttf`) or OpenType (`.otf`) outline formats without an external rasterizer.

This subsystem introduces high-quality, modern, open-source typography to IRIX 6.5:
1. **Curated Vector Outlines (`/usr/lib/X11/fonts/Type1/` and `/usr/lib/DPS/AFM/`)**: Modern TrueType/OpenType outlines converted into Adobe Type 1 ASCII outlines (`.pfa`) with accompanying Adobe Font Metrics (`.afm`).
2. **Pixel-Perfect Bitmap Typography (`/usr/lib/X11/fonts/misc/`)**: Native compressed PCF fonts (`.pcf.Z`) for Terminus in 9 tailored sizes (12, 14, 16, 18, 20, 22, 24, 28, 32 pixels in Regular and Bold).
3. **Native 8-bit Powerline Glyphs**: In monospaced coding fonts (JetBrains Mono NL, Hack, Inconsolata), Powerline symbols (`uniE0B0..uniE0B3`, `uniE0A0..uniE0A2`) are mapped into the unused ISO8859-1 C1 control range (slots 128..134 / `0x80..0x86`). This allows standard IRIX terminal tools, `tcsh` prompts, `tmux`, and `vim` to render Powerline status bars natively without requiring UTF-8 terminal emulators.
4. **Developer & Icon Typography**: `SymbolsNerdFontMono.pfa` provides over 4,000 developer and terminal glyphs.

Both `/usr/lib/X11/fonts/Type1/` and `/usr/lib/X11/fonts/misc/` are part of the compiled-in default font search path of `Xsgi`. All standard X11, Motif, and desktop applications (`winterm`, `xterm`, `jot`, `4Dwm`, Showcase) can immediately use these fonts.

## 2. Curated Font Matrix

| Category | Font Family | Styles Available | Spacing / Characteristics | Primary Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **Bitmap Monospace** | **Terminus** | 9 sizes (12–32px), Regular & Bold | Crisp bitmap PCF (`.pcf.Z`) | High-speed, crystal-clear terminal typography |
| **Monospaced** | **JetBrains Mono NL** | Regular, Bold, Italic, BoldItalic | Fixed (`m`), Powerline (`0x80..0x86`), no ligatures | Premier coding font for terminals and editors |
| **Monospaced** | **Hack** | Regular, Bold, Italic, BoldItalic | Fixed (`m`), Powerline (`0x80..0x86`), wide apertures | Low-resolution screen readability |
| **Monospaced** | **Inconsolata** | Regular, Bold | Fixed (`m`), Powerline (`0x80..0x86`), cubic Bézier | Clean terminal & code display (`winterm`, `jot`) |
| **Monospaced** | **Droid Sans Mono** | Regular, Dotted Zero, Slashed Zero | Fixed (`m`), clear distinction for coding | Clean Android system monospace |
| **Monospaced** | **Source Code Pro** | Regular, Bold, Italic, BoldItalic | Fixed (`m`), native CFF/Type 1 metrics | High-legibility developer font |
| **Monospaced** | **Liberation Mono** | Regular, Bold, Italic, BoldItalic | Fixed (`m`), Courier metric-compatible | Drop-in modernization for Courier |
| **Developer Icons** | **Symbols Nerd Font** | Regular Mono | Unicode (`iso10646-1`), 4,000+ developer icons | File type icons, Git indicators, UI glyphs |
| **Proportional** | **Roboto** | Regular, Bold, Italic, BoldItalic | Proportional (`p`), geometric neo-grotesque | Clean, modern desktop UI and Motif dialogs |
| **Proportional** | **Droid Sans & Serif** | Regular, Bold, Italic, BoldItalic | Proportional (`p`), high contrast | Compact screen legibility |
| **Proportional** | **Source Sans 3** | Regular, Bold, Italic, BoldItalic | Proportional (`p`), clean neo-grotesque | Desktop dialogs, Motif menus, 4Dwm |
| **Proportional** | **Liberation Sans** | Regular, Bold, Italic, BoldItalic | Proportional (`p`), Helvetica metric-compatible | Drop-in modernization for Helvetica |
| **Proportional** | **Liberation Serif** | Regular, Bold, Italic, BoldItalic | Proportional (`p`), Times metric-compatible | Drop-in modernization for Times |

## 3. Technical Conversion Pipeline
The conversion is performed via [`convert_fonts.py`](file:///home/dbehr/gits/iris/shared/updates-irix/fonts/convert_fonts.py):
1. **Re-encoding to ISO8859-1:** Core X11 on IRIX relies on 8-bit character sets. Unicode outlines are re-encoded to `iso8859-1` (Latin-1 Western European).
2. **Powerline Glyph Preservation:** For coding fonts, `uniE0B0..uniE0B3` (triangles) and `uniE0A0..uniE0A2` (branch, line, lock) are preserved in C1 slots 128..134 before pruning.
3. **Glyph Pruning:** Unencoded glyphs are stripped, reducing file footprint from ~500 KB to ~60–80 KB per font.
4. **Em Square Normalization:** Rescaled to standard Adobe Type 1 geometry (1000 units per em).
5. **Curve Optimization & Hinting:** Outlines are simplified, direction-corrected, and autohinted for crisp un-antialiased rasterization under SGI's Type 1 rasterizer.
6. **AFM Extraction:** Generates exact Adobe Font Metrics for DPS and PostScript tools.
7. **Bitmap PCF Compression:** Terminus fonts are decompressed from host `.pcf.gz` and recompressed with standard UNIX LZW `compress` to generate native `.pcf.Z` files acceptable to `Xsgi`.

## 4. Integration & Packaging
- **Target Subsystem:** `patchSG002026.x_eoe_sw.Xfonts`
- **Follows:** `x_eoe.sw.Xfonts 1280000000 1289999999`
- **Replaces:** `patchSG0005785.x_eoe_sw.Xfonts 0 maxint` (supersedes Adobe Replacement Patch; carries forward all Courier AFM metrics)
- **Install-time Activation (`exitop` via `.fonts_rollup.sh`):**
  - Appends font definitions to `/usr/lib/X11/fonts/Type1/fonts.scale`.
  - Configures convenient short aliases in `/usr/lib/X11/fonts/Type1/fonts.alias` (e.g. `jetbrains-14`, `hack-14`, `droidsansmono-14`, `roboto-14`, `nerdfont-14`).
  - Configures Terminus aliases in `/usr/lib/X11/fonts/misc/fonts.alias` (e.g. `terminus-14`, `terminus-bold-14`).
  - Executes `/usr/bin/X11/mkfontdir` on both `/usr/lib/X11/fonts/Type1` and `/usr/lib/X11/fonts/misc`.
  - Rehashes font server and X server caches (`xset fp rehash`).
- **Clean Removal (`removeop`):**
  - Unregisters rollup font entries from `fonts.scale` and `fonts.alias` in both directories.
  - Recompiles `fonts.dir` via `mkfontdir`.
  - Rehashes active X server font paths.

## 5. Usage in IRIX Applications
```sh
# Launch winterm with Terminus bitmap font:
winterm -fn terminus-14 &
winterm -fn terminus-bold-16 &

# Launch winterm with JetBrains Mono NL:
winterm -fn jetbrains-14 &
winterm -fn jetbrains-bold-14 &

# Launch winterm with Droid Sans Mono:
winterm -fn droidsansmono-14 &

# Launch winterm with Hack:
winterm -fn hack-14 &

# Launch jot with Roboto:
jot -fn roboto-14 &
```
