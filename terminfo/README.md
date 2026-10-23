# SGI IRIX 6.5 Modern Terminal Database (`terminfo`)

## 1. Overview
On stock SGI IRIX 6.5 systems, the terminal database in `/usr/share/lib/terminfo/` contains legacy terminal descriptions from the 1980s and 1990s (such as `iris-ansi`, `vt100`, `vt220`, and basic monochrome `xterm`).

Connecting to an IRIX system from modern Linux or macOS environments via SSH or Telnet almost invariably exports modern terminal types like `xterm-256color`, `tmux-256color`, `screen-256color`, `alacritty`, `kitty`, or `foot`. On stock IRIX, curses applications (`vi`, `top`, `less`, `nano`) fail immediately with:
```
tput: unknown terminal "xterm-256color"
Sorry, I don't know anything about your "xterm-256color" terminal.
```

This subsystem generates authentic, compiled terminfo definitions for 24 contemporary terminal environments and compiles them directly into `/usr/share/lib/terminfo/` using IRIX's native `/usr/bin/tic`.

## 2. Supported Terminal Profiles

| Category | Terminal Type (`$TERM`) | Color Capability |
| :--- | :--- | :--- |
| **Standard XTerm** | `xterm-256color`, `xterm-color`, `xterm-16color`, `xterm-direct` | 256 colors / Direct RGB |
| **Multiplexers** | `screen-256color`, `screen`, `tmux-256color`, `tmux`, `tmux-direct` | 256 colors / Direct RGB |
| **Modern GPU Terminals** | `alacritty`, `alacritty-direct`, `kitty`, `kitty-direct`, `foot`, `foot-direct` | 256 colors / Direct RGB |
| **Desktop Terminals** | `gnome-256color`, `gnome`, `putty-256color`, `putty`, `linux` | 256 colors |
| **Unicode Virtual Terminals** | `rxvt-256color`, `rxvt-unicode`, `rxvt-unicode-256color`, `rxvt` | 256 colors |

## 3. Architecture & Packaging
- **Source Generation:** [`generate_terminfo.py`](file:///home/dbehr/gits/iris/shared/updates-irix/terminfo/generate_terminfo.py) extracts definitions using `infocmp -I -1`.
- **Target Subsystem:** `patchSG002026.eoe_sw.termbase` (follows `eoe.sw.termbase`).
- **Install-time Execution:** Staged at `/usr/share/lib/terminfo/modern_terms.ti`. During package installation, an `exitop` runs:
  ```sh
  TERMINFO=$rbase/usr/share/lib/terminfo tic $rbase/usr/share/lib/terminfo/modern_terms.ti
  ```
  This guarantees that all terminal binaries are compiled according to the exact endianness, bit-fields, and format expected by IRIX curses `libcurses.so.1`.
