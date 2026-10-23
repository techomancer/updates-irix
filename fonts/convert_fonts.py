#!/usr/bin/env python3
"""
Convert curated modern TrueType / OpenType fonts to Adobe Type 1 (.pfa)
and package Terminus bitmap fonts for SGI IRIX 6.5 X11 / Xsgi display environment.

Pipeline:
1. Re-encode font to ISO8859-1 (Western European 8-bit) and preserve Powerline glyphs
   in C1 control slots 128..134 (0x80..0x86) for terminal/statusline usage.
2. Prune unencoded glyphs (reduces footprint from ~500KB to ~70KB per font).
3. Normalize em-square to standard Type 1 (1000 units).
4. Simplify Bézier splines, correct contour direction, and autohint.
5. Generate Adobe Type 1 ASCII outline (.pfa) and AFM metrics (.afm).
6. Emit fonts.scale and fonts.alias fragments for IRIX Type 1 and misc font directories.
"""

import os
import subprocess
import sys
import tempfile

FONT_CONFIGS = [
    # Monospaced (Coding, Terminals, winterm, jot)
    {
        "src": "/usr/share/fonts/inconsolata/Inconsolata-Regular.ttf",
        "pfa": "Inconsolata-Regular.pfa",
        "powerline": True,
        "xlfd": [
            "-misc-inconsolata-medium-r-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/inconsolata/Inconsolata-Bold.ttf",
        "pfa": "Inconsolata-Bold.pfa",
        "powerline": True,
        "xlfd": [
            "-misc-inconsolata-bold-r-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/hack/Hack-Regular.ttf",
        "pfa": "Hack-Regular.pfa",
        "powerline": True,
        "xlfd": [
            "-source foundry-hack-medium-r-normal--0-0-0-0-m-0-iso8859-1",
            "-misc-hack-medium-r-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/hack/Hack-Bold.ttf",
        "pfa": "Hack-Bold.pfa",
        "powerline": True,
        "xlfd": [
            "-source foundry-hack-bold-r-normal--0-0-0-0-m-0-iso8859-1",
            "-misc-hack-bold-r-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/hack/Hack-Italic.ttf",
        "pfa": "Hack-Italic.pfa",
        "powerline": True,
        "xlfd": [
            "-source foundry-hack-medium-i-normal--0-0-0-0-m-0-iso8859-1",
            "-misc-hack-medium-i-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/hack/Hack-BoldItalic.ttf",
        "pfa": "Hack-BoldItalic.pfa",
        "powerline": True,
        "xlfd": [
            "-source foundry-hack-bold-i-normal--0-0-0-0-m-0-iso8859-1",
            "-misc-hack-bold-i-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/jetbrains-mono/JetBrainsMonoNL-Regular.ttf",
        "pfa": "JetBrainsMonoNL-Regular.pfa",
        "powerline": True,
        "xlfd": [
            "-jetbrains-jetbrains mono nl-medium-r-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/jetbrains-mono/JetBrainsMonoNL-Bold.ttf",
        "pfa": "JetBrainsMonoNL-Bold.pfa",
        "powerline": True,
        "xlfd": [
            "-jetbrains-jetbrains mono nl-bold-r-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/jetbrains-mono/JetBrainsMonoNL-Italic.ttf",
        "pfa": "JetBrainsMonoNL-Italic.pfa",
        "powerline": True,
        "xlfd": [
            "-jetbrains-jetbrains mono nl-medium-i-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/jetbrains-mono/JetBrainsMonoNL-BoldItalic.ttf",
        "pfa": "JetBrainsMonoNL-BoldItalic.pfa",
        "powerline": True,
        "xlfd": [
            "-jetbrains-jetbrains mono nl-bold-i-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/droid/DroidSansMono.ttf",
        "pfa": "DroidSansMono.pfa",
        "xlfd": [
            "-google-droid sans mono-medium-r-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/droid/DroidSansMonoDotted.ttf",
        "pfa": "DroidSansMonoDotted.pfa",
        "xlfd": [
            "-google-droid sans mono dotted-medium-r-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/droid/DroidSansMonoSlashed.ttf",
        "pfa": "DroidSansMonoSlashed.pfa",
        "xlfd": [
            "-google-droid sans mono slashed-medium-r-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/source-code-pro/SourceCodePro-Regular.otf",
        "pfa": "SourceCodePro-Regular.pfa",
        "xlfd": [
            "-adobe-source code pro-medium-r-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/source-code-pro/SourceCodePro-Bold.otf",
        "pfa": "SourceCodePro-Bold.pfa",
        "xlfd": [
            "-adobe-source code pro-bold-r-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/source-code-pro/SourceCodePro-It.otf",
        "pfa": "SourceCodePro-It.pfa",
        "xlfd": [
            "-adobe-source code pro-medium-i-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/source-code-pro/SourceCodePro-BoldIt.otf",
        "pfa": "SourceCodePro-BoldIt.pfa",
        "xlfd": [
            "-adobe-source code pro-bold-i-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/liberation-fonts/LiberationMono-Regular.ttf",
        "pfa": "LiberationMono-Regular.pfa",
        "xlfd": [
            "-liberation-liberation mono-medium-r-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/liberation-fonts/LiberationMono-Bold.ttf",
        "pfa": "LiberationMono-Bold.pfa",
        "xlfd": [
            "-liberation-liberation mono-bold-r-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/liberation-fonts/LiberationMono-Italic.ttf",
        "pfa": "LiberationMono-Italic.pfa",
        "xlfd": [
            "-liberation-liberation mono-medium-i-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/liberation-fonts/LiberationMono-BoldItalic.ttf",
        "pfa": "LiberationMono-BoldItalic.pfa",
        "xlfd": [
            "-liberation-liberation mono-bold-i-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },

    # Proportional / Variable-Width (Motif, 4Dwm, Desktop GUI)
    {
        "src": "/usr/share/fonts/roboto/Roboto-Regular.ttf",
        "pfa": "Roboto-Regular.pfa",
        "xlfd": [
            "-google-roboto-medium-r-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/roboto/Roboto-Bold.ttf",
        "pfa": "Roboto-Bold.pfa",
        "xlfd": [
            "-google-roboto-bold-r-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/roboto/Roboto-Italic.ttf",
        "pfa": "Roboto-Italic.pfa",
        "xlfd": [
            "-google-roboto-medium-i-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/roboto/Roboto-BoldItalic.ttf",
        "pfa": "Roboto-BoldItalic.pfa",
        "xlfd": [
            "-google-roboto-bold-i-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/droid/DroidSans.ttf",
        "pfa": "DroidSans-Regular.pfa",
        "xlfd": [
            "-google-droid sans-medium-r-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/droid/DroidSans-Bold.ttf",
        "pfa": "DroidSans-Bold.pfa",
        "xlfd": [
            "-google-droid sans-bold-r-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/droid/DroidSerif-Regular.ttf",
        "pfa": "DroidSerif-Regular.pfa",
        "xlfd": [
            "-google-droid serif-medium-r-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/droid/DroidSerif-Bold.ttf",
        "pfa": "DroidSerif-Bold.pfa",
        "xlfd": [
            "-google-droid serif-bold-r-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/droid/DroidSerif-Italic.ttf",
        "pfa": "DroidSerif-Italic.pfa",
        "xlfd": [
            "-google-droid serif-medium-i-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/droid/DroidSerif-BoldItalic.ttf",
        "pfa": "DroidSerif-BoldItalic.pfa",
        "xlfd": [
            "-google-droid serif-bold-i-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/source-sans-3/SourceSans3-Regular.otf",
        "pfa": "SourceSans3-Regular.pfa",
        "xlfd": [
            "-adobe-source sans 3-medium-r-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/source-sans-3/SourceSans3-Bold.otf",
        "pfa": "SourceSans3-Bold.pfa",
        "xlfd": [
            "-adobe-source sans 3-bold-r-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/source-sans-3/SourceSans3-It.otf",
        "pfa": "SourceSans3-It.pfa",
        "xlfd": [
            "-adobe-source sans 3-medium-i-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/source-sans-3/SourceSans3-BoldIt.otf",
        "pfa": "SourceSans3-BoldIt.pfa",
        "xlfd": [
            "-adobe-source sans 3-bold-i-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/liberation-fonts/LiberationSans-Regular.ttf",
        "pfa": "LiberationSans-Regular.pfa",
        "xlfd": [
            "-liberation-liberation sans-medium-r-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/liberation-fonts/LiberationSans-Bold.ttf",
        "pfa": "LiberationSans-Bold.pfa",
        "xlfd": [
            "-liberation-liberation sans-bold-r-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/liberation-fonts/LiberationSans-Italic.ttf",
        "pfa": "LiberationSans-Italic.pfa",
        "xlfd": [
            "-liberation-liberation sans-medium-i-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/liberation-fonts/LiberationSans-BoldItalic.ttf",
        "pfa": "LiberationSans-BoldItalic.pfa",
        "xlfd": [
            "-liberation-liberation sans-bold-i-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/liberation-fonts/LiberationSerif-Regular.ttf",
        "pfa": "LiberationSerif-Regular.pfa",
        "xlfd": [
            "-liberation-liberation serif-medium-r-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/liberation-fonts/LiberationSerif-Bold.ttf",
        "pfa": "LiberationSerif-Bold.pfa",
        "xlfd": [
            "-liberation-liberation serif-bold-r-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/liberation-fonts/LiberationSerif-Italic.ttf",
        "pfa": "LiberationSerif-Italic.pfa",
        "xlfd": [
            "-liberation-liberation serif-medium-i-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },
    {
        "src": "/usr/share/fonts/liberation-fonts/LiberationSerif-BoldItalic.ttf",
        "pfa": "LiberationSerif-BoldItalic.pfa",
        "xlfd": [
            "-liberation-liberation serif-bold-i-normal--0-0-0-0-p-0-iso8859-1",
        ],
    },

    # Developer & Symbol Fonts
    {
        "src": "/usr/share/fonts/symbols-nerd-font/SymbolsNerdFontMono-Regular.ttf",
        "pfa": "SymbolsNerdFontMono.pfa",
        "reencode_iso": False,
        "xlfd": [
            "-nerd-symbols nerd font mono-medium-r-normal--0-0-0-0-m-0-iso10646-1",
            "-nerd-symbols nerd font mono-medium-r-normal--0-0-0-0-m-0-iso8859-1",
        ],
    },
]

ALIASES_TYPE1 = [
    # Inconsolata
    ("inconsolata", "-misc-inconsolata-medium-r-normal--14-135-100-75-m-0-iso8859-1"),
    ("inconsolata-bold", "-misc-inconsolata-bold-r-normal--14-135-100-75-m-0-iso8859-1"),
    ("inconsolata-12", "-misc-inconsolata-medium-r-normal--12-116-100-75-m-0-iso8859-1"),
    ("inconsolata-14", "-misc-inconsolata-medium-r-normal--14-135-100-75-m-0-iso8859-1"),
    ("inconsolata-16", "-misc-inconsolata-medium-r-normal--16-154-100-75-m-0-iso8859-1"),
    ("inconsolata-18", "-misc-inconsolata-medium-r-normal--18-174-100-75-m-0-iso8859-1"),

    # Hack
    ("hack", "-misc-hack-medium-r-normal--14-135-100-75-m-0-iso8859-1"),
    ("hack-bold", "-misc-hack-bold-r-normal--14-135-100-75-m-0-iso8859-1"),
    ("hack-12", "-misc-hack-medium-r-normal--12-116-100-75-m-0-iso8859-1"),
    ("hack-14", "-misc-hack-medium-r-normal--14-135-100-75-m-0-iso8859-1"),
    ("hack-16", "-misc-hack-medium-r-normal--16-154-100-75-m-0-iso8859-1"),
    ("hack-18", "-misc-hack-medium-r-normal--18-174-100-75-m-0-iso8859-1"),

    # JetBrains Mono NL
    ("jetbrains", "-jetbrains-jetbrains mono nl-medium-r-normal--14-135-100-75-m-0-iso8859-1"),
    ("jetbrains-bold", "-jetbrains-jetbrains mono nl-bold-r-normal--14-135-100-75-m-0-iso8859-1"),
    ("jetbrains-italic", "-jetbrains-jetbrains mono nl-medium-i-normal--14-135-100-75-m-0-iso8859-1"),
    ("jetbrains-bolditalic", "-jetbrains-jetbrains mono nl-bold-i-normal--14-135-100-75-m-0-iso8859-1"),
    ("jetbrains-12", "-jetbrains-jetbrains mono nl-medium-r-normal--12-116-100-75-m-0-iso8859-1"),
    ("jetbrains-14", "-jetbrains-jetbrains mono nl-medium-r-normal--14-135-100-75-m-0-iso8859-1"),
    ("jetbrains-16", "-jetbrains-jetbrains mono nl-medium-r-normal--16-154-100-75-m-0-iso8859-1"),
    ("jetbrains-18", "-jetbrains-jetbrains mono nl-medium-r-normal--18-174-100-75-m-0-iso8859-1"),
    ("jetbrainsmono", "-jetbrains-jetbrains mono nl-medium-r-normal--14-135-100-75-m-0-iso8859-1"),
    ("jetbrainsmono-bold", "-jetbrains-jetbrains mono nl-bold-r-normal--14-135-100-75-m-0-iso8859-1"),

    # Droid Family
    ("droidsansmono", "-google-droid sans mono-medium-r-normal--14-135-100-75-m-0-iso8859-1"),
    ("droidsansmono-12", "-google-droid sans mono-medium-r-normal--12-116-100-75-m-0-iso8859-1"),
    ("droidsansmono-14", "-google-droid sans mono-medium-r-normal--14-135-100-75-m-0-iso8859-1"),
    ("droidsansmono-16", "-google-droid sans mono-medium-r-normal--16-154-100-75-m-0-iso8859-1"),
    ("droidsansmono-18", "-google-droid sans mono-medium-r-normal--18-174-100-75-m-0-iso8859-1"),
    ("droidsansmonodotted", "-google-droid sans mono dotted-medium-r-normal--14-135-100-75-m-0-iso8859-1"),
    ("droidsansmonoslashed", "-google-droid sans mono slashed-medium-r-normal--14-135-100-75-m-0-iso8859-1"),
    ("droidsans", "-google-droid sans-medium-r-normal--14-135-100-75-p-0-iso8859-1"),
    ("droidsans-bold", "-google-droid sans-bold-r-normal--14-135-100-75-p-0-iso8859-1"),
    ("droidserif", "-google-droid serif-medium-r-normal--14-135-100-75-p-0-iso8859-1"),

    # Roboto
    ("roboto", "-google-roboto-medium-r-normal--14-135-100-75-p-0-iso8859-1"),
    ("roboto-bold", "-google-roboto-bold-r-normal--14-135-100-75-p-0-iso8859-1"),
    ("roboto-italic", "-google-roboto-medium-i-normal--14-135-100-75-p-0-iso8859-1"),
    ("roboto-bolditalic", "-google-roboto-bold-i-normal--14-135-100-75-p-0-iso8859-1"),
    ("roboto-12", "-google-roboto-medium-r-normal--12-116-100-75-p-0-iso8859-1"),
    ("roboto-14", "-google-roboto-medium-r-normal--14-135-100-75-p-0-iso8859-1"),
    ("roboto-16", "-google-roboto-medium-r-normal--16-154-100-75-p-0-iso8859-1"),
    ("roboto-18", "-google-roboto-medium-r-normal--18-174-100-75-p-0-iso8859-1"),

    # Source Code Pro
    ("sourcecodepro", "-adobe-source code pro-medium-r-normal--14-135-100-75-m-0-iso8859-1"),
    ("sourcecodepro-bold", "-adobe-source code pro-bold-r-normal--14-135-100-75-m-0-iso8859-1"),
    ("sourcecodepro-12", "-adobe-source code pro-medium-r-normal--12-116-100-75-m-0-iso8859-1"),
    ("sourcecodepro-14", "-adobe-source code pro-medium-r-normal--14-135-100-75-m-0-iso8859-1"),
    ("sourcecodepro-16", "-adobe-source code pro-medium-r-normal--16-154-100-75-m-0-iso8859-1"),
    ("sourcecodepro-18", "-adobe-source code pro-medium-r-normal--18-174-100-75-m-0-iso8859-1"),

    # Liberation
    ("liberationmono", "-liberation-liberation mono-medium-r-normal--14-135-100-75-m-0-iso8859-1"),
    ("liberationmono-bold", "-liberation-liberation mono-bold-r-normal--14-135-100-75-m-0-iso8859-1"),
    ("liberationsans", "-liberation-liberation sans-medium-r-normal--14-135-100-75-p-0-iso8859-1"),
    ("liberationserif", "-liberation-liberation serif-medium-r-normal--14-135-100-75-p-0-iso8859-1"),
    ("sourcesans", "-adobe-source sans 3-medium-r-normal--14-135-100-75-p-0-iso8859-1"),

    # Nerd Font
    ("nerdfont", "-nerd-symbols nerd font mono-medium-r-normal--14-135-100-75-m-0-iso10646-1"),
    ("nerdfont-12", "-nerd-symbols nerd font mono-medium-r-normal--12-116-100-75-m-0-iso10646-1"),
    ("nerdfont-14", "-nerd-symbols nerd font mono-medium-r-normal--14-135-100-75-m-0-iso10646-1"),
    ("nerdfont-16", "-nerd-symbols nerd font mono-medium-r-normal--16-154-100-75-m-0-iso10646-1"),
    ("nerdfont-18", "-nerd-symbols nerd font mono-medium-r-normal--18-174-100-75-m-0-iso10646-1"),
    ("nerdsymbols", "-nerd-symbols nerd font mono-medium-r-normal--14-135-100-75-m-0-iso10646-1"),
]

# Terminus specifications for bitmap fonts (/usr/lib/X11/fonts/misc/)
TERMINUS_SPECS = [
    # (pixel_size, point_size, avg_width)
    (12, 120, 60),
    (14, 140, 80),
    (16, 160, 80),
    (18, 180, 100),
    (20, 200, 100),
    (22, 220, 110),
    (24, 240, 120),
    (28, 280, 140),
    (32, 320, 160),
]

def generate_terminus_misc_aliases():
    aliases = []
    # Default aliases
    aliases.append(('terminus', '-xos4-terminus-medium-r-normal--14-140-72-72-c-80-iso10646-1'))
    aliases.append(('terminus-bold', '-xos4-terminus-bold-r-normal--14-140-72-72-c-80-iso10646-1'))

    for px, pt, w in TERMINUS_SPECS:
        med_10646 = f"-xos4-terminus-medium-r-normal--{px}-{pt}-72-72-c-{w}-iso10646-1"
        bld_10646 = f"-xos4-terminus-bold-r-normal--{px}-{pt}-72-72-c-{w}-iso10646-1"

        med_8859 = f"-xos4-terminus-medium-r-normal--{px}-{pt}-72-72-c-{w}-iso8859-1"
        bld_8859 = f"-xos4-terminus-bold-r-normal--{px}-{pt}-72-72-c-{w}-iso8859-1"

        aliases.append((f"terminus-{px}", med_10646))
        aliases.append((f"terminus-bold-{px}", bld_10646))
        aliases.append((med_8859, med_10646))
        aliases.append((bld_8859, bld_10646))

    return aliases

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pfa_dir = os.path.join(script_dir, "pfa")
    pcf_dir = os.path.join(script_dir, "pcf")
    os.makedirs(pfa_dir, exist_ok=True)
    os.makedirs(pcf_dir, exist_ok=True)

    # Standard ISO8859-1 conversion with optional Powerline copying
    ff_script_iso = """Open($1)
Reencode("iso8859-1")
if ($3 == "1")
    i = 0
    powerline_glyphs = ["uniE0B0", "uniE0B1", "uniE0B2", "uniE0B3", "uniE0A0", "uniE0A1", "uniE0A2"]
    while (i < 7)
        gname = powerline_glyphs[i]
        if (InFont(gname))
            Select(gname)
            Copy()
            Select(128 + i)
            Paste()
            SetGlyphName(gname)
        endif
        i = i + 1
    endloop
endif
Select(0, 255)
SelectInvert()
Clear()
ScaleToEm(1000)
Simplify()
CorrectDirection()
AutoHint()
Generate($2)
Close()
"""

    # Full unicode conversion (for icon/symbol fonts like Nerd Font)
    ff_script_full = """Open($1)
ScaleToEm(1000)
Simplify()
CorrectDirection()
AutoHint()
Generate($2)
Close()
"""

    with tempfile.NamedTemporaryFile("w", suffix=".ff", delete=False) as f1:
        f1.write(ff_script_iso)
        ff_iso_path = f1.name

    with tempfile.NamedTemporaryFile("w", suffix=".ff", delete=False) as f2:
        f2.write(ff_script_full)
        ff_full_path = f2.name

    try:
        scale_lines = []
        for item in FONT_CONFIGS:
            src = item["src"]
            pfa_name = item["pfa"]
            reencode = item.get("reencode_iso", True)
            pw = "1" if item.get("powerline", False) else "0"
            dst = os.path.join(pfa_dir, pfa_name)

            if not os.path.exists(src):
                print(f"Warning: Source font {src} not found, skipping...")
                continue

            if not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst):
                print(f"Converting: {os.path.basename(src)} -> {pfa_name}...")
                ff_tool = ff_iso_path if reencode else ff_full_path
                cmd = ["fontforge", "-script", ff_tool, src, dst, pw] if reencode else ["fontforge", "-script", ff_tool, src, dst]
                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
                if res.returncode != 0:
                    print(f"Error converting {src}: {res.stderr}", file=sys.stderr)
                    sys.exit(1)
            else:
                print(f"Up to date: {pfa_name}")

            for xlfd in item["xlfd"]:
                scale_lines.append(f"{pfa_name} {xlfd}")

        # Ensure Terminus PCF files are prepared in pcf/
        host_terminus_dir = "/usr/share/fonts/terminus"
        if os.path.exists(host_terminus_dir):
            for px, _, _ in TERMINUS_SPECS:
                for style, suffix in [("n", "n"), ("b", "b")]:
                    pcf_name = f"ter-x{px}{suffix}.pcf.Z"
                    dst_pcf = os.path.join(pcf_dir, pcf_name)
                    src_gz = os.path.join(host_terminus_dir, f"ter-x{px}{suffix}.pcf.gz")
                    if os.path.exists(src_gz):
                        if not os.path.exists(dst_pcf) or os.path.getmtime(src_gz) > os.path.getmtime(dst_pcf):
                            print(f"Compressing Terminus: {src_gz} -> {pcf_name}")
                            p1 = subprocess.Popen(["gzip", "-dc", src_gz], stdout=subprocess.PIPE)
                            with open(dst_pcf, "wb") as out_f:
                                subprocess.run(["compress", "-c"], stdin=p1.stdout, stdout=out_f, check=True)
                            p1.wait()

        # Write fonts.scale.rollup for Type1
        scale_rollup_path = os.path.join(script_dir, "fonts.scale.rollup")
        with open(scale_rollup_path, "w") as f:
            for line in scale_lines:
                f.write(f"{line}\n")
        print(f"Wrote {len(scale_lines)} scale entries to {scale_rollup_path}")

        # Write fonts.alias.rollup for Type1
        alias_rollup_path = os.path.join(script_dir, "fonts.alias.rollup")
        with open(alias_rollup_path, "w") as f:
            for alias, target in ALIASES_TYPE1:
                f.write(f'{alias} "{target}"\n')
        print(f"Wrote {len(ALIASES_TYPE1)} Type 1 alias entries to {alias_rollup_path}")

        # Write fonts.alias.misc.rollup for Terminus in misc/
        terminus_aliases = generate_terminus_misc_aliases()
        misc_alias_path = os.path.join(script_dir, "fonts.alias.misc.rollup")
        with open(misc_alias_path, "w") as f:
            for alias, target in terminus_aliases:
                f.write(f'{alias} "{target}"\n')
        print(f"Wrote {len(terminus_aliases)} misc alias entries to {misc_alias_path}")

    finally:
        if os.path.exists(ff_iso_path):
            os.remove(ff_iso_path)
        if os.path.exists(ff_full_path):
            os.remove(ff_full_path)

if __name__ == "__main__":
    main()
