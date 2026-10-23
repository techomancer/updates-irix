#!/usr/bin/env python3
"""generate_terminfo.py - Generate modern terminfo sources for SGI IRIX."""

import os
import subprocess
import sys

TERMS = [
    "xterm-256color", "xterm-color", "xterm-16color", "xterm-direct",
    "screen-256color", "screen",
    "tmux-256color", "tmux", "tmux-direct",
    "alacritty", "alacritty-direct",
    "kitty", "kitty-direct",
    "foot", "foot-direct",
    "rxvt-256color", "rxvt-unicode", "rxvt-unicode-256color", "rxvt",
    "gnome-256color", "gnome",
    "putty-256color", "putty",
    "linux"
]

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_file = os.path.join(script_dir, "modern_terms.ti")
    
    with open(out_file, "w") as out:
        out.write("# Modern Terminal Definitions for SGI IRIX 6.5\n")
        out.write("# Generated from Linux ncurses terminfo database\n")
        out.write("# Includes 256-color and direct-color modern terminal support\n\n")
        
        for t in TERMS:
            res = subprocess.run(["infocmp", "-I", "-1", t], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode != 0:
                print(f"Warning: could not dump terminfo for {t}: {res.stderr.strip()}", file=sys.stderr)
                continue
            out.write(f"# === Terminal: {t} ===\n")
            out.write(res.stdout)
            out.write("\n")
            
    print(f"Generated {out_file} with {len(TERMS)} terminal profiles.")

if __name__ == "__main__":
    main()
