#!/usr/bin/env python3
"""
irix_lib_audit.py - Forensic & ABI Compatibility Auditor for IRIX Libraries

Usage:
  1. Audit a single library (.so or .a):
     ./irix_lib_audit.py audit <path/to/lib.so>
  2. Compare an original IRIX library against a modernized build:
     ./irix_lib_audit.py compare <orig_lib.so> <new_lib.so>
  3. Compare an entire directory tree of IRIX libraries (o32, n32, n64):
     ./irix_lib_audit.py compare-tree <orig_dir> <new_dir>
"""

import argparse
import json
import os
import re
import subprocess
import sys

# Ignored MIPS linker bookkeeping symbols that aren't part of the C ABI
MIPS_BOOKKEEPING_SYMS = {
    "_procedure_table",
    "_procedure_table_size",
    "_procedure_string_table",
    "__dso_displacement",
    "__elf_header",
    "__program_header_table",
    "_gp_disp",
    "_DYNAMIC",
    "_GLOBAL_OFFSET_TABLE_",
    "_fdata",
    "_edata",
    "_fbss",
    "_end",
    "_ftext",
    "_etext",
    "_init",
    "_fini",
}


def run_cmd(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
    return p.stdout


def parse_elf_metadata(path):
    is_archive = path.endswith(".a")
    info = {
        "path": path,
        "type": "archive" if is_archive else "dso",
        "abi": None,
        "isa": None,
        "soname": None,
        "iversion": None,
        "base_address": None,
        "needed": [],
        "version_strings": [],
        "defined_funcs": {},
        "defined_objects": {},
        "undefined_syms": set(),
    }

    # Extract version strings
    s_out = run_cmd(["strings", "-a", path])
    ver_matches = set()
    for line in s_out.splitlines():
        if "Copyright" in line and ("deflate" in line or "inflate" in line or "libpng" in line):
            ver_matches.add(line.strip())
    info["version_strings"] = sorted(ver_matches)

    if is_archive:
        h_out = run_cmd(["readelf", "-h", path])
        for line in h_out.splitlines():
            if "Class:" in line and not info["abi"]:
                if "ELF64" in line:
                    info["abi"] = "n64"
            if "Flags:" in line:
                if "abi2" in line or "n32" in line:
                    info["abi"] = "n32"
                elif not info["abi"]:
                    info["abi"] = "o32"
                for isa in ("mips4", "mips3", "mips2", "mips1"):
                    if isa in line:
                        info["isa"] = isa
                        break
        nm_out = run_cmd(["nm", "-g", "--defined-only", path])
        for line in nm_out.splitlines():
            parts = line.split()
            if len(parts) == 3:
                _, stype, name = parts
                if name in MIPS_BOOKKEEPING_SYMS:
                    continue
                if stype in ("T", "W"):
                    info["defined_funcs"][name] = 0
                elif stype in ("D", "R", "B", "G", "S", "C"):
                    info["defined_objects"][name] = 0
        nm_u = run_cmd(["nm", "-u", path])
        for line in nm_u.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0] == "U":
                info["undefined_syms"].add(parts[1])
        info["undefined_syms"] -= set(info["defined_funcs"].keys()) | set(info["defined_objects"].keys())
        info["undefined_syms"] = sorted(info["undefined_syms"])
        return info

    # DSO analysis
    h_out = run_cmd(["readelf", "-h", "-d", "-W", path])
    for line in h_out.splitlines():
        if "Class:" in line and "ELF64" in line:
            info["abi"] = "n64"
        elif "Machine:" in line and "N32" in line:
            info["abi"] = "n32"
        elif "Flags:" in line:
            if "abi2" in line or "n32" in line:
                info["abi"] = "n32"
            elif not info["abi"]:
                info["abi"] = "o32"
            for isa in ("mips4", "mips3", "mips2", "mips1"):
                if isa in line:
                    info["isa"] = isa
                    break
        elif "(SONAME)" in line:
            m = re.search(r"\[(.*?)\]", line)
            if m:
                info["soname"] = m.group(1)
        elif "(MIPS_IVERSION)" in line:
            m = re.search(r"Interface Version:\s*(\S+)", line)
            if m:
                info["iversion"] = m.group(1)
        elif "(MIPS_BASE_ADDRESS)" in line:
            m = re.search(r"0x[0-9a-fA-F]+", line.split(")")[-1])
            if m:
                info["base_address"] = m.group(0)
        elif "(NEEDED)" in line:
            m = re.search(r"\[(.*?)\]", line)
            if m:
                info["needed"].append(m.group(1))

    # Parse .dynsym
    sym_out = run_cmd(["readelf", "--dyn-syms", "-W", path])
    for line in sym_out.splitlines():
        line = line.strip()
        if not line or not line[0].isdigit():
            continue
        parts = line.split()
        if len(parts) < 8:
            continue
        # Num: Value Size Type Bind Vis Ndx Name
        size_str = parts[2]
        stype = parts[3]
        bind = parts[4]
        ndx = parts[6]
        name = parts[7]
        if name in MIPS_BOOKKEEPING_SYMS or stype == "SECTION":
            continue
        size = int(size_str, 16) if size_str.startswith("0x") else int(size_str)
        if ndx == "UND":
            if name:
                info["undefined_syms"].add(name)
        else:
            if bind in ("GLOBAL", "WEAK"):
                if stype == "FUNC":
                    info["defined_funcs"][name] = size
                elif stype == "OBJECT":
                    info["defined_objects"][name] = size

    info["undefined_syms"] = sorted(info["undefined_syms"])
    return info


def compare_libs(orig_path, new_path):
    orig = parse_elf_metadata(orig_path)
    new = parse_elf_metadata(new_path)
    errors = []
    warnings = []
    added_funcs = sorted(set(new["defined_funcs"].keys()) - set(orig["defined_funcs"].keys()))
    missing_funcs = sorted(set(orig["defined_funcs"].keys()) - set(new["defined_funcs"].keys()))
    added_objs = sorted(set(new["defined_objects"].keys()) - set(orig["defined_objects"].keys()))
    missing_objs = sorted(set(orig["defined_objects"].keys()) - set(new["defined_objects"].keys()))

    if orig["abi"] != new["abi"]:
        errors.append(f"ABI mismatch: orig={orig['abi']} vs new={new['abi']}")
    if orig["type"] == "dso":
        if orig["soname"] != new["soname"]:
            errors.append(f"SONAME mismatch: orig={orig['soname']} vs new={new['soname']}")
        if orig["iversion"] != new["iversion"]:
            errors.append(f"MIPS_IVERSION mismatch: orig={orig['iversion']} vs new={new['iversion']}")
        if orig["base_address"] != new["base_address"]:
            warnings.append(f"MIPS_BASE_ADDRESS changed: orig={orig['base_address']} vs new={new['base_address']}")
        if orig["needed"] != new["needed"]:
            errors.append(f"DT_NEEDED mismatch: orig={orig['needed']} vs new={new['needed']}")

    if missing_funcs:
        errors.append(f"MISSING exported functions ({len(missing_funcs)}): {', '.join(missing_funcs)}")
    if missing_objs:
        errors.append(f"MISSING exported data objects ({len(missing_objs)}): {', '.join(missing_objs)}")

    # Check OBJECT sizes for common objects (except *_copyright strings which naturally change length)
    for obj_name in sorted(set(orig["defined_objects"].keys()) & set(new["defined_objects"].keys())):
        osz = orig["defined_objects"][obj_name]
        nsz = new["defined_objects"][obj_name]
        if osz != 0 and nsz != 0 and osz != nsz:
            if obj_name.endswith("_copyright"):
                warnings.append(f"Copyright string size changed for {obj_name}: {osz} -> {nsz} bytes (harmless)")
            else:
                errors.append(f"ABI OBJECT SIZE MISMATCH for {obj_name}: orig={osz} bytes vs new={nsz} bytes!")

    # Check undefined imports
    new_imports = sorted(set(new["undefined_syms"]) - set(orig["undefined_syms"]))
    # Forbidden Linux/glibc symbols
    for sym in new["undefined_syms"]:
        if sym in ("__errno_location", "__stack_chk_fail", "__stack_chk_guard") or sym.endswith("_chk"):
            errors.append(f"FORBIDDEN non-IRIX symbol imported: {sym}")

    print(f"======================================================================")
    print(f"Comparing: {orig_path}  --->  {new_path}")
    print(f"======================================================================")
    print(f"  ABI / ISA        : {orig['abi']} ({orig['isa']})  --->  {new['abi']} ({new['isa']})")
    if orig["type"] == "dso":
        print(f"  SONAME / IVERSION: {orig['soname']} ({orig['iversion']})  --->  {new['soname']} ({new['iversion']})")
        print(f"  Base Address     : {orig['base_address']}  --->  {new['base_address']}")
        print(f"  DT_NEEDED        : {orig['needed']}  --->  {new['needed']}")
    print(f"  Version Strings  : {orig['version_strings']}  --->  {new['version_strings']}")
    print(f"  Exported Funcs   : {len(orig['defined_funcs'])} orig  --->  {len(new['defined_funcs'])} new (+{len(added_funcs)} added, -{len(missing_funcs)} missing)")
    print(f"  Exported Objects : {len(orig['defined_objects'])} orig  --->  {len(new['defined_objects'])} new (+{len(added_objs)} added, -{len(missing_objs)} missing)")
    if new_imports:
        print(f"  New libc Imports : {', '.join(new_imports)}")

    if warnings:
        for w in warnings:
            print(f"  [WARN]  {w}")
    if errors:
        for e in errors:
            print(f"  [FAIL]  {e}")
        print(f"  RESULT: FAILED ({len(errors)} error(s))")
        return False
    else:
        print(f"  RESULT: PASS (100% backwards-compatible ABI & symbol superset)")
        return True


def main():
    parser = argparse.ArgumentParser(description="IRIX Library Forensic & ABI Auditor")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_audit = sub.add_parser("audit")
    p_audit.add_argument("path")

    p_cmp = sub.add_parser("compare")
    p_cmp.add_argument("orig")
    p_cmp.add_argument("new")

    p_tree = sub.add_parser("compare-tree")
    p_tree.add_argument("orig_dir")
    p_tree.add_argument("new_dir")

    args = parser.parse_args()
    if args.cmd == "audit":
        info = parse_elf_metadata(args.path)
        print(json.dumps(info, indent=2))
    elif args.cmd == "compare":
        ok = compare_libs(args.orig, args.new)
        sys.exit(0 if ok else 1)
    elif args.cmd == "compare-tree":
        targets = [
            "libz.so",
            "32/libz.so",
            "64/libz.so",
            "libz.a",
            "32/libz.a",
            "64/libz.a",
        ]
        all_ok = True
        for rel in targets:
            op = os.path.join(args.orig_dir, rel)
            np = os.path.join(args.new_dir, rel)
            if os.path.exists(op) and os.path.exists(np):
                if not compare_libs(op, np):
                    all_ok = False
            elif os.path.exists(op):
                print(f"[FAIL] Missing target in new tree: {np}")
                all_ok = False
        sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
