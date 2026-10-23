#!/bin/sh
# fonts_rollup.sh - Helper script for patchSG002026 Type 1 and misc font registration
ACTION="${1:-install}"
T1DIR="${rbase}/usr/lib/X11/fonts/Type1"
MISCDIR="${rbase}/usr/lib/X11/fonts/misc"

case "$ACTION" in
install)
    # 1. Update Type1 fonts.scale
    if [ -f "$T1DIR/fonts.scale" ]; then
        tail +2 "$T1DIR/fonts.scale" | egrep -v 'Inconsolata|Hack|SourceCodePro|Liberation|SourceSans3|JetBrainsMono|Droid|Roboto|SymbolsNFM' > "$T1DIR/scale.tmp"
        cat "$T1DIR/.fonts.scale.rollup2026" >> "$T1DIR/scale.tmp"
        COUNT=`wc -l < "$T1DIR/scale.tmp" | tr -d ' '`
        echo "$COUNT" > "$T1DIR/fonts.scale"
        cat "$T1DIR/scale.tmp" >> "$T1DIR/fonts.scale"
        rm -f "$T1DIR/scale.tmp"
    fi

    # 2. Update Type1 fonts.alias
    if [ -f "$T1DIR/.fonts.alias.rollup2026" ]; then
        touch "$T1DIR/fonts.alias"
        egrep -v 'inconsolata|hack|sourcecodepro|liberation|sourcesans|jetbrains|droid|roboto|nerd' "$T1DIR/fonts.alias" > "$T1DIR/alias.tmp"
        cat "$T1DIR/.fonts.alias.rollup2026" >> "$T1DIR/alias.tmp"
        mv "$T1DIR/alias.tmp" "$T1DIR/fonts.alias"
    fi

    # 3. Update misc fonts.alias (Terminus aliases)
    if [ -f "$MISCDIR/.fonts.alias.misc.rollup2026" ]; then
        touch "$MISCDIR/fonts.alias"
        egrep -v 'terminus' "$MISCDIR/fonts.alias" > "$MISCDIR/alias.tmp"
        cat "$MISCDIR/.fonts.alias.misc.rollup2026" >> "$MISCDIR/alias.tmp"
        mv "$MISCDIR/alias.tmp" "$MISCDIR/fonts.alias"
    fi

    # 4. Run mkfontdir on both directories
    if [ -x "${rbase}/usr/bin/X11/mkfontdir" ]; then
        "${rbase}/usr/bin/X11/mkfontdir" "$T1DIR"
        "${rbase}/usr/bin/X11/mkfontdir" "$MISCDIR"
    fi

    # 5. Rehash font cache in active X server if running
    if [ -x "${rbase}/usr/bin/X11/xset" ]; then
        DISPLAY=:0 "${rbase}/usr/bin/X11/xset" fp rehash 2>/dev/null || true
    fi
    ;;

remove)
    # 1. Clean Type1 fonts.scale
    if [ -f "$T1DIR/fonts.scale" ]; then
        tail +2 "$T1DIR/fonts.scale" | egrep -v 'Inconsolata|Hack|SourceCodePro|Liberation|SourceSans3|JetBrainsMono|Droid|Roboto|SymbolsNFM' > "$T1DIR/scale.tmp"
        COUNT=`wc -l < "$T1DIR/scale.tmp" | tr -d ' '`
        echo "$COUNT" > "$T1DIR/fonts.scale"
        cat "$T1DIR/scale.tmp" >> "$T1DIR/fonts.scale"
        rm -f "$T1DIR/scale.tmp"
    fi

    # 2. Clean Type1 fonts.alias
    if [ -f "$T1DIR/fonts.alias" ]; then
        egrep -v 'inconsolata|hack|sourcecodepro|liberation|sourcesans|jetbrains|droid|roboto|nerd' "$T1DIR/fonts.alias" > "$T1DIR/alias.tmp"
        if [ -s "$T1DIR/alias.tmp" ]; then
            mv "$T1DIR/alias.tmp" "$T1DIR/fonts.alias"
        else
            rm -f "$T1DIR/fonts.alias" "$T1DIR/alias.tmp"
        fi
    fi

    # 3. Clean misc fonts.alias
    if [ -f "$MISCDIR/fonts.alias" ]; then
        egrep -v 'terminus' "$MISCDIR/fonts.alias" > "$MISCDIR/alias.tmp"
        if [ -s "$MISCDIR/alias.tmp" ]; then
            mv "$MISCDIR/alias.tmp" "$MISCDIR/fonts.alias"
        else
            rm -f "$MISCDIR/fonts.alias" "$MISCDIR/alias.tmp"
        fi
    fi

    rm -f "$T1DIR/.fonts.scale.rollup2026" "$T1DIR/.fonts.alias.rollup2026" "$T1DIR/.fonts_rollup.sh"
    rm -f "$MISCDIR/.fonts.alias.misc.rollup2026"

    # 4. Re-run mkfontdir on both directories
    if [ -x "${rbase}/usr/bin/X11/mkfontdir" ]; then
        "${rbase}/usr/bin/X11/mkfontdir" "$T1DIR"
        "${rbase}/usr/bin/X11/mkfontdir" "$MISCDIR"
    fi

    # 5. Rehash font cache in active X server
    if [ -x "${rbase}/usr/bin/X11/xset" ]; then
        DISPLAY=:0 "${rbase}/usr/bin/X11/xset" fp rehash 2>/dev/null || true
    fi
    ;;
esac
