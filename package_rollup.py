#!/usr/bin/env python3
"""
package_rollup.py - Package "Security Rollup 2026, the Year of the IRIX Desktop"
into an SGI inst/swmgr compatible .tardist patch distribution (patchSG002026).
"""

import gzip
import os
import shutil
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GUEST_SHARED = "/shared/updates-irix"
DIST_DIR = os.path.join(BASE_DIR, "dist")
ROOT_DIR = os.path.join(DIST_DIR, "root")
OUT_DIR = os.path.join(DIST_DIR, "out")

PRODUCT_NAME = "patchSG002026-1"
PRODUCT_DESC = "Security Rollup 2026 for SGI IRIX 6.5 (Beta 1)"

# Subsystems and their versions
VERS_IFL = 1319999926
VERS_SSL = 1279999926
VERS_SSL11 = 1119999926
VERS_SSH = 1279999926
VERS_EOE = 1289999926
VERS_XFONTS = 1289999926

def copy_file(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.islink(src):
        linkto = os.readlink(src)
        if os.path.lexists(dst):
            os.remove(dst)
        os.symlink(linkto, dst)
    else:
        shutil.copy2(src, dst)

def run_guest_script(script_path):
    cmd = ["/home/dbehr/gits/iris/tools/irix-sh.py", "run", f"sh {script_path}"]
    env = dict(os.environ)
    if "IRIS_ROOT_PASSWORD" not in env or not env["IRIS_ROOT_PASSWORD"]:
        env["IRIS_ROOT_PASSWORD"] = "p00pp00p"
    res = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"Error running guest script: {script_path}\nOutput: {res.stdout}\nError: {res.stderr}")
        sys.exit(1)
    return res.stdout

def main():
    print("=== Step 1: Cleaning and preparing staging tree ===")
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    os.makedirs(ROOT_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)

    for d in [
        "usr/bin", "usr/sbin", "usr/libexec", "usr/lib", "usr/lib32", "usr/lib64",
        "usr/include", "etc/openssh", "etc/init.d", "etc/config", "etc/rc2.d", "etc/rc0.d", "var/empty",
        "usr/lib/X11/fonts/Type1", "usr/lib/DPS/AFM", "usr/lib/X11/fonts/misc", "usr/lib/locale/TZ",
        "usr/share/lib/terminfo", "usr/share/tcsh", "usr/share/tcsh/examples", "etc/ssl/certs", "usr/local/ssl",
        "usr/share/catman/u_man/cat1", "usr/share/catman/u_man/cat1/openssh", "usr/share/catman/u_man/cat1/openssl",
        "usr/share/catman/p_man/cat5/openssh", "usr/share/catman/p_man/cat5/openssl",
        "usr/share/catman/a_man/cat7/openssl", "usr/share/catman/a_man/cat8/openssh"
    ]:
        os.makedirs(os.path.join(ROOT_DIR, d), exist_ok=True)

    idb_entries = []

    def add_idb(ftype, mode, owner, group, path, exp_tag, attrs=""):
        src_path = path
        attr_str = f" {attrs}" if attrs else ""
        idb_entries.append((path, f"{ftype} {mode} {owner} {group} {path} {src_path} {exp_tag}{attr_str}"))

    print("=== Step 2: Staging Media & Compression Libraries ===")
    TAG_IFL = "patchSG002026_1_ifl_eoe_sw_c"
    TAG_IFL64 = "patchSG002026_1_ifl_eoe_sw64_c"
    TAG_IFLDEV = "patchSG002026_1_ifl_dev_sw_c"
    TAG_SSL_LIB32 = "patchSG002026_1_openssl_sw_lib32"
    TAG_SSL_BASE = "patchSG002026_1_openssl_sw_base"
    TAG_SSL11_LIB32 = "patchSG002026_1_openssl11_sw_lib32"
    TAG_SSL11_LIB64 = "patchSG002026_1_openssl11_sw_lib64"
    TAG_SSL11_DEV = "patchSG002026_1_openssl11_sw_dev"
    TAG_SSH_CLIENT = "patchSG002026_1_openssh_sw_client"
    TAG_SSH_COMMON = "patchSG002026_1_openssh_sw_common"
    TAG_SSH_SERVER = "patchSG002026_1_openssh_sw_server"
    TAG_EOE_BASE = "patchSG002026_1_eoe_sw_base"
    TAG_EOE_TERM = "patchSG002026_1_eoe_sw_termbase"
    TAG_EOE_TCSH = "patchSG002026_1_eoe_sw_tcsh"
    TAG_EOE_MAN_BASE = "patchSG002026_1_eoe_man_base"
    TAG_SSH_MAN = "patchSG002026_1_openssh_man_manpages"
    TAG_SSL_MAN = "patchSG002026_1_openssl_man_manpages"

    # 2.1 Modernized O32 / N32 DSOs
    copy_file(os.path.join(BASE_DIR, "zlib/build/libz.so"), os.path.join(ROOT_DIR, "usr/lib/libz.so"))
    add_idb("f", "0755", "root", "sys", "usr/lib/libz.so", TAG_IFL, "needrqs")
    copy_file(os.path.join(BASE_DIR, "zlib/build/32/libz.so"), os.path.join(ROOT_DIR, "usr/lib32/libz.so"))
    add_idb("f", "0755", "root", "sys", "usr/lib32/libz.so", TAG_IFL, "needrqs")

    copy_file(os.path.join(BASE_DIR, "libpng/build/libpng.so"), os.path.join(ROOT_DIR, "usr/lib/libpng.so"))
    add_idb("f", "0755", "root", "sys", "usr/lib/libpng.so", TAG_IFL, "needrqs")
    copy_file(os.path.join(BASE_DIR, "libpng/build/32/libpng.so"), os.path.join(ROOT_DIR, "usr/lib32/libpng.so"))
    add_idb("f", "0755", "root", "sys", "usr/lib32/libpng.so", TAG_IFL, "needrqs")

    copy_file(os.path.join(BASE_DIR, "libtiff/build/libtiff.so"), os.path.join(ROOT_DIR, "usr/lib/libtiff.so"))
    add_idb("f", "0755", "root", "sys", "usr/lib/libtiff.so", TAG_IFL, "needrqs")
    copy_file(os.path.join(BASE_DIR, "libtiff/build/32/libtiff.so"), os.path.join(ROOT_DIR, "usr/lib32/libtiff.so"))
    add_idb("f", "0755", "root", "sys", "usr/lib32/libtiff.so", TAG_IFL, "needrqs")

    copy_file(os.path.join(BASE_DIR, "libjpeg/build/libjpeg.so"), os.path.join(ROOT_DIR, "usr/lib/libjpeg.so"))
    add_idb("f", "0755", "root", "sys", "usr/lib/libjpeg.so", TAG_IFL, "needrqs")
    copy_file(os.path.join(BASE_DIR, "libjpeg/build/32/libjpeg.so"), os.path.join(ROOT_DIR, "usr/lib32/libjpeg.so"))
    add_idb("f", "0755", "root", "sys", "usr/lib32/libjpeg.so", TAG_IFL, "needrqs")

    # 2.3 Modernized N64 DSOs (ifl_eoe_sw64.c++)
    copy_file(os.path.join(BASE_DIR, "zlib/build/64/libz.so"), os.path.join(ROOT_DIR, "usr/lib64/libz.so"))
    add_idb("f", "0755", "root", "sys", "usr/lib64/libz.so", TAG_IFL64, "needrqs")

    copy_file(os.path.join(BASE_DIR, "libpng/build/64/libpng.so"), os.path.join(ROOT_DIR, "usr/lib64/libpng.so"))
    add_idb("f", "0755", "root", "sys", "usr/lib64/libpng.so", TAG_IFL64, "needrqs")

    copy_file(os.path.join(BASE_DIR, "libtiff/build/64/libtiff.so"), os.path.join(ROOT_DIR, "usr/lib64/libtiff.so"))
    add_idb("f", "0755", "root", "sys", "usr/lib64/libtiff.so", TAG_IFL64, "needrqs")

    copy_file(os.path.join(BASE_DIR, "libjpeg/build/64/libjpeg.so"), os.path.join(ROOT_DIR, "usr/lib64/libjpeg.so"))
    add_idb("f", "0755", "root", "sys", "usr/lib64/libjpeg.so", TAG_IFL64, "needrqs")

    # 2.4 Headers & Archives (ifl_dev_sw.c++)
    dev_headers = [
        ("zlib/build/zlib.h", "usr/include/zlib.h"),
        ("zlib/build/zconf.h", "usr/include/zconf.h"),
        ("libpng/build/png.h", "usr/include/png.h"),
        ("libpng/build/pngconf.h", "usr/include/pngconf.h"),
        ("libtiff/build/tiff.h", "usr/include/tiff.h"),
        ("libtiff/build/tiffio.h", "usr/include/tiffio.h"),
        ("libtiff/build/tiffconf.h", "usr/include/tiffconf.h"),
        ("libtiff/build/tiffvers.h", "usr/include/tiffvers.h"),
        ("libjpeg/build/jpeglib.h", "usr/include/jpeglib.h"),
        ("libjpeg/build/jconfig.h", "usr/include/jconfig.h"),
        ("libjpeg/build/jerror.h", "usr/include/jerror.h"),
        ("libjpeg/build/jmorecfg.h", "usr/include/jmorecfg.h"),
    ]
    for src, dst in dev_headers:
        copy_file(os.path.join(BASE_DIR, src), os.path.join(ROOT_DIR, dst))
        add_idb("f", "0644", "root", "sys", dst, TAG_IFLDEV)

    dev_archives = [
        ("zlib/build/libz.a", "usr/lib/libz.a"),
        ("zlib/build/32/libz.a", "usr/lib32/libz.a"),
        ("zlib/build/64/libz.a", "usr/lib64/libz.a"),
        ("libpng/build/libpng.a", "usr/lib/libpng.a"),
        ("libpng/build/32/libpng.a", "usr/lib32/libpng.a"),
        ("libpng/build/64/libpng.a", "usr/lib64/libpng.a"),
        ("libtiff/build/libtiff.a", "usr/lib/libtiff.a"),
        ("libtiff/build/32/libtiff.a", "usr/lib32/libtiff.a"),
        ("libtiff/build/64/libtiff.a", "usr/lib64/libtiff.a"),
        ("libjpeg/build/libjpeg.a", "usr/lib/libjpeg.a"),
        ("libjpeg/build/32/libjpeg.a", "usr/lib32/libjpeg.a"),
        ("libjpeg/build/64/libjpeg.a", "usr/lib64/libjpeg.a"),
    ]
    for src, dst in dev_archives:
        copy_file(os.path.join(BASE_DIR, src), os.path.join(ROOT_DIR, dst))
        add_idb("f", "0644", "root", "sys", dst, TAG_IFLDEV)

    print("=== Step 3: Staging OpenSSL 0.9.7 (openssl_sw.lib32, openssl_sw.base) ===")
    copy_file(os.path.join(BASE_DIR, "openssl-0.9.7/build/32/libcrypto.so.0.9.7"), os.path.join(ROOT_DIR, "usr/lib32/libcrypto.so.0.9.7"))
    add_idb("f", "0755", "root", "sys", "usr/lib32/libcrypto.so.0.9.7", TAG_SSL_LIB32, "needrqs")

    copy_file(os.path.join(BASE_DIR, "openssl-0.9.7/build/32/libssl.so.0.9.7"), os.path.join(ROOT_DIR, "usr/lib32/libssl.so.0.9.7"))
    add_idb("f", "0755", "root", "sys", "usr/lib32/libssl.so.0.9.7", TAG_SSL_LIB32, "needrqs")

    add_idb("l", "0777", "root", "sys", "usr/lib32/libcrypto.so.0", TAG_SSL_LIB32, "symval(libcrypto.so.0.9.7)")
    add_idb("l", "0777", "root", "sys", "usr/lib32/libcrypto.so", TAG_SSL_LIB32, "symval(libcrypto.so.0)")
    add_idb("l", "0777", "root", "sys", "usr/lib32/libssl.so.0", TAG_SSL_LIB32, "symval(libssl.so.0.9.7)")
    add_idb("l", "0777", "root", "sys", "usr/lib32/libssl.so", TAG_SSL_LIB32, "symval(libssl.so.0)")

    copy_file(os.path.join(BASE_DIR, "openssl-0.9.7/build/32/libcrypto.a"), os.path.join(ROOT_DIR, "usr/lib32/libcrypto.a"))
    add_idb("f", "0644", "root", "sys", "usr/lib32/libcrypto.a", TAG_SSL_LIB32)

    copy_file(os.path.join(BASE_DIR, "openssl-0.9.7/build/32/libssl.a"), os.path.join(ROOT_DIR, "usr/lib32/libssl.a"))
    add_idb("f", "0644", "root", "sys", "usr/lib32/libssl.a", TAG_SSL_LIB32)

    # OpenSSL base CLI (0.9.7 & 1.1.1 updating openssl.sw.base)
    copy_file(os.path.join(BASE_DIR, "openssl-0.9.7/build/32/openssl"), os.path.join(ROOT_DIR, "usr/bin/openssl.097"))
    add_idb("f", "0755", "root", "sys", "usr/bin/openssl.097", TAG_SSL_BASE, "tag(0x53534c30)")

    copy_file(os.path.join(BASE_DIR, "openssl-1.1.1/build/32/openssl"), os.path.join(ROOT_DIR, "usr/bin/openssl"))
    add_idb("f", "0755", "root", "sys", "usr/bin/openssl", TAG_SSL_BASE, "tag(0x53534c31)")

    copy_file(os.path.join(BASE_DIR, "openssl-1.1.1/openssl/apps/openssl.cnf"), os.path.join(ROOT_DIR, "usr/openssl/openssl.cnf"))
    add_idb("f", "0644", "root", "sys", "usr/openssl/openssl.cnf", TAG_SSL_BASE, "config(suggest)")

    # OpenSSL Root CA Certificates Bundle & Symlinks
    copy_file(os.path.join(BASE_DIR, "ssl/ca-certificates.crt"), os.path.join(ROOT_DIR, "etc/ssl/certs/ca-certificates.crt"))
    add_idb("f", "0644", "root", "sys", "etc/ssl/certs/ca-certificates.crt", TAG_SSL_BASE, "config(suggest)")
    add_idb("l", "0777", "root", "sys", "etc/ssl/cert.pem", TAG_SSL_BASE, "symval(certs/ca-certificates.crt)")
    add_idb("l", "0777", "root", "sys", "usr/local/ssl/cert.pem", TAG_SSL_BASE, "symval(/etc/ssl/certs/ca-certificates.crt)")
    add_idb("l", "0777", "root", "sys", "usr/local/ssl/certs", TAG_SSL_BASE, "symval(/etc/ssl/certs)")
    add_idb("l", "0777", "root", "sys", "usr/share/ssl/cert.pem", TAG_SSL_BASE, "symval(/etc/ssl/certs/ca-certificates.crt)")
    add_idb("l", "0777", "root", "sys", "usr/openssl/cert.pem", TAG_SSL_BASE, "symval(/etc/ssl/certs/ca-certificates.crt)")

    print("=== Step 4: Staging OpenSSL 1.1.1 (openssl11_sw.lib32, lib64, dev) ===")
    copy_file(os.path.join(BASE_DIR, "openssl-1.1.1/build/32/libcrypto.so.1.1"), os.path.join(ROOT_DIR, "usr/lib32/libcrypto.so.1.1"))
    add_idb("f", "0755", "root", "sys", "usr/lib32/libcrypto.so.1.1", TAG_SSL11_LIB32, "needrqs")

    copy_file(os.path.join(BASE_DIR, "openssl-1.1.1/build/32/libssl.so.1.1"), os.path.join(ROOT_DIR, "usr/lib32/libssl.so.1.1"))
    add_idb("f", "0755", "root", "sys", "usr/lib32/libssl.so.1.1", TAG_SSL11_LIB32, "needrqs")

    copy_file(os.path.join(BASE_DIR, "openssl-1.1.1/build/32/libcrypto.a"), os.path.join(ROOT_DIR, "usr/lib32/libcrypto-1.1.a"))
    add_idb("f", "0644", "root", "sys", "usr/lib32/libcrypto-1.1.a", TAG_SSL11_LIB32)

    copy_file(os.path.join(BASE_DIR, "openssl-1.1.1/build/32/libssl.a"), os.path.join(ROOT_DIR, "usr/lib32/libssl-1.1.a"))
    add_idb("f", "0644", "root", "sys", "usr/lib32/libssl-1.1.a", TAG_SSL11_LIB32)

    copy_file(os.path.join(BASE_DIR, "openssl-1.1.1/build/64/libcrypto.so.1.1"), os.path.join(ROOT_DIR, "usr/lib64/libcrypto.so.1.1"))
    add_idb("f", "0755", "root", "sys", "usr/lib64/libcrypto.so.1.1", TAG_SSL11_LIB64, "needrqs")

    copy_file(os.path.join(BASE_DIR, "openssl-1.1.1/build/64/libssl.so.1.1"), os.path.join(ROOT_DIR, "usr/lib64/libssl.so.1.1"))
    add_idb("f", "0755", "root", "sys", "usr/lib64/libssl.so.1.1", TAG_SSL11_LIB64, "needrqs")

    copy_file(os.path.join(BASE_DIR, "openssl-1.1.1/build/64/libcrypto.a"), os.path.join(ROOT_DIR, "usr/lib64/libcrypto-1.1.a"))
    add_idb("f", "0644", "root", "sys", "usr/lib64/libcrypto-1.1.a", TAG_SSL11_LIB64)

    copy_file(os.path.join(BASE_DIR, "openssl-1.1.1/build/64/libssl.a"), os.path.join(ROOT_DIR, "usr/lib64/libssl-1.1.a"))
    add_idb("f", "0644", "root", "sys", "usr/lib64/libssl-1.1.a", TAG_SSL11_LIB64)

    copy_file(os.path.join(BASE_DIR, "openssl-1.1.1/build/32/openssl"), os.path.join(ROOT_DIR, "usr/bin/openssl11"))
    add_idb("f", "0755", "root", "sys", "usr/bin/openssl11", TAG_SSL11_DEV, "tag(0x53534c31)")

    ssl_inc_dir = os.path.join(BASE_DIR, "openssl-1.1.1/build/include/openssl")
    for f in os.listdir(ssl_inc_dir):
        src_h = os.path.join(ssl_inc_dir, f)
        if os.path.isfile(src_h):
            dst_h = os.path.join(ROOT_DIR, "usr/include/openssl-1.1/openssl", f)
            copy_file(src_h, dst_h)
            add_idb("f", "0644", "root", "sys", f"usr/include/openssl-1.1/openssl/{f}", TAG_SSL11_DEV)
            dst_local = os.path.join(ROOT_DIR, "usr/local/ssl/include/openssl", f)
            copy_file(src_h, dst_local)
            add_idb("f", "0644", "root", "sys", f"usr/local/ssl/include/openssl/{f}", TAG_SSL11_DEV)

    print("=== Step 5: Staging OpenSSH 9.9p2 (openssh_sw.client, common, server) ===")
    ssh_clients = [
        ("openssh/build/bin/ssh", "usr/bin/ssh"),
        ("openssh/build/bin/scp", "usr/bin/scp"),
        ("openssh/build/bin/sftp", "usr/bin/sftp"),
        ("openssh/build/bin/ssh-add", "usr/bin/ssh-add"),
        ("openssh/build/bin/ssh-agent", "usr/bin/ssh-agent"),
        ("openssh/build/bin/ssh-keyscan", "usr/bin/ssh-keyscan"),
    ]
    for src, dst in ssh_clients:
        copy_file(os.path.join(BASE_DIR, src), os.path.join(ROOT_DIR, dst))
        add_idb("f", "0755", "root", "sys", dst, TAG_SSH_CLIENT, "tag(0x53534832)")
    add_idb("l", "0777", "root", "sys", "usr/bin/slogin", TAG_SSH_CLIENT, "symval(ssh)")

    with open(os.path.join(ROOT_DIR, "etc/openssh/ssh_config"), "w") as f:
        f.write("# OpenSSH 9.9p2 Client Configuration (Security Rollup 2026)\n"
                "Host *\n"
                "    SendEnv LANG LC_*\n"
                "    HashKnownHosts yes\n")
    add_idb("f", "0644", "root", "sys", "etc/openssh/ssh_config", TAG_SSH_CLIENT, "config(suggest)")

    ssh_commons = [
        ("openssh/build/bin/ssh-keygen", "usr/bin/ssh-keygen"),
        ("openssh/build/libexec/ssh-keysign", "usr/bin/ssh-keysign"),
    ]
    for src, dst in ssh_commons:
        copy_file(os.path.join(BASE_DIR, src), os.path.join(ROOT_DIR, dst))
        add_idb("f", "4711" if "keysign" in src else "0755", "root", "sys", dst, TAG_SSH_COMMON, "tag(0x53534832)")



    ssh_servers = [
        ("openssh/build/sbin/sshd", "usr/sbin/sshd"),
        ("openssh/build/libexec/sshd-session", "usr/libexec/sshd-session"),
        ("openssh/build/libexec/sftp-server", "usr/libexec/sftp-server"),
        ("openssh/build/libexec/ssh-pkcs11-helper", "usr/libexec/ssh-pkcs11-helper"),
        ("openssh/build/libexec/ssh-sk-helper", "usr/libexec/ssh-sk-helper"),
    ]
    for src, dst in ssh_servers:
        copy_file(os.path.join(BASE_DIR, src), os.path.join(ROOT_DIR, dst))
        add_idb("f", "0755", "root", "sys", dst, TAG_SSH_SERVER, "tag(0x53534832)")

    with open(os.path.join(ROOT_DIR, "etc/openssh/sshd_config"), "w") as f:
        f.write("# OpenSSH 9.9p2 Server Configuration (Security Rollup 2026)\n"
                "Port 22\n"
                "Protocol 2\n"
                "HostKey /etc/openssh/ssh_host_rsa_key\n"
                "HostKey /etc/openssh/ssh_host_ecdsa_key\n"
                "HostKey /etc/openssh/ssh_host_ed25519_key\n"
                "SyslogFacility AUTH\n"
                "LogLevel INFO\n"
                "PermitRootLogin yes\n"
                "AuthorizedKeysFile .ssh/authorized_keys\n"
                "PasswordAuthentication yes\n"
                "PermitEmptyPasswords no\n"
                "KbdInteractiveAuthentication no\n"
                "X11Forwarding yes\n"
                "Subsystem sftp /usr/libexec/sftp-server\n")
    add_idb("f", "0600", "root", "sys", "etc/openssh/sshd_config", TAG_SSH_SERVER, "config(suggest)")

    copy_file(os.path.join(BASE_DIR, "openssh/openssh/moduli"), os.path.join(ROOT_DIR, "etc/openssh/moduli"))
    add_idb("f", "0644", "root", "sys", "etc/openssh/moduli", TAG_SSH_SERVER, "config(suggest)")

    with open(os.path.join(ROOT_DIR, "etc/init.d/sshd"), "w") as f:
        f.write("#! /sbin/sh\n"
                "# OpenSSH sshd startup script for IRIX (Security Rollup 2026)\n"
                "case $1 in\n"
                "'start')\n"
                "    if test ! -d /var/empty; then\n"
                "        mkdir -p /var/empty\n"
                "        chmod 0755 /var/empty\n"
                "        chown root:sys /var/empty\n"
                "    fi\n"
                "    if test ! -f /etc/openssh/ssh_host_rsa_key; then\n"
                "        /usr/bin/ssh-keygen -t rsa -N '' -f /etc/openssh/ssh_host_rsa_key\n"
                "    fi\n"
                "    if test ! -f /etc/openssh/ssh_host_ecdsa_key; then\n"
                "        /usr/bin/ssh-keygen -t ecdsa -N '' -f /etc/openssh/ssh_host_ecdsa_key\n"
                "    fi\n"
                "    if test ! -f /etc/openssh/ssh_host_ed25519_key; then\n"
                "        /usr/bin/ssh-keygen -t ed25519 -N '' -f /etc/openssh/ssh_host_ed25519_key\n"
                "    fi\n"
                "    if /sbin/chkconfig sshd; then\n"
                "        if test -x /usr/sbin/sshd; then\n"
                "            /usr/sbin/sshd\n"
                "        fi\n"
                "    fi\n"
                "    ;;\n"
                "'stop')\n"
                "    /sbin/killall 15 sshd 2>/dev/null\n"
                "    ;;\n"
                "*)\n"
                "    echo 'usage: /etc/init.d/sshd {start|stop}'\n"
                "    ;;\n"
                "esac\n")
    add_idb("f", "0755", "root", "sys", "etc/init.d/sshd", TAG_SSH_SERVER, "config(suggest)")

    with open(os.path.join(ROOT_DIR, "etc/config/sshd"), "w") as f:
        f.write("on\n")
    add_idb("f", "0644", "root", "sys", "etc/config/sshd", TAG_SSH_SERVER, "config(suggest)")

    add_idb("l", "0755", "root", "sys", "etc/rc2.d/S30sshd", TAG_SSH_SERVER, "symval(../init.d/sshd)")
    add_idb("l", "0755", "root", "sys", "etc/rc0.d/K30sshd", TAG_SSH_SERVER, "symval(../init.d/sshd)")

    server_exitop = ('exitop("if ! id sshd >/dev/null 2>&1; then /usr/sbin/useradd -c \'OpenSSH PrivSep\' -d /var/empty -s /bin/false -u 130 sshd; fi; '
                     'mkdir -p /var/empty && chmod 0755 /var/empty && chown root:sys /var/empty; '
                     'if test ! -f /etc/openssh/ssh_host_rsa_key; then /usr/bin/ssh-keygen -t rsa -N \'\' -f /etc/openssh/ssh_host_rsa_key; fi; '
                     'if test ! -f /etc/openssh/ssh_host_ecdsa_key; then /usr/bin/ssh-keygen -t ecdsa -N \'\' -f /etc/openssh/ssh_host_ecdsa_key; fi; '
                     'if test ! -f /etc/openssh/ssh_host_ed25519_key; then /usr/bin/ssh-keygen -t ed25519 -N \'\' -f /etc/openssh/ssh_host_ed25519_key; fi")')
    add_idb("d", "0755", "root", "sys", "var/empty", TAG_SSH_SERVER, server_exitop)

    print("=== Step 6: Staging Modern Terminal Database (eoe_sw.termbase) ===")
    copy_file(os.path.join(BASE_DIR, "terminfo/modern_terms.ti"), os.path.join(ROOT_DIR, "usr/share/lib/terminfo/modern_terms.ti"))
    term_exitop = 'exitop("TERMINFO=$rbase/usr/share/lib/terminfo tic $rbase/usr/share/lib/terminfo/modern_terms.ti")'
    term_removeop = ('removeop("for t in xterm-256color xterm-color xterm-16color xterm-direct screen-256color screen tmux-256color tmux tmux-direct '
                     'alacritty alacritty-direct kitty kitty-direct foot foot-direct rxvt-256color rxvt-unicode rxvt-unicode-256color rxvt gnome-256color '
                     'gnome putty-256color putty linux; do rm -f $rbase/usr/share/lib/terminfo/?/$t; done")')
    add_idb("f", "0644", "root", "sys", "usr/share/lib/terminfo/modern_terms.ti", TAG_EOE_TERM, f"{term_exitop} {term_removeop}")

    print("=== Step 7: Staging TimeZone Database and Shells (eoe_sw.base) ===")
    copy_file(os.path.join(BASE_DIR, "tzdata/build/bin/zic"), os.path.join(ROOT_DIR, "usr/bin/zic"))
    add_idb("f", "0755", "root", "sys", "usr/bin/zic", TAG_EOE_BASE, "tag(0x545A4943)")

    copy_file(os.path.join(BASE_DIR, "tzdata/build/bin/zdump"), os.path.join(ROOT_DIR, "usr/bin/zdump"))
    add_idb("f", "0755", "root", "sys", "usr/bin/zdump", TAG_EOE_BASE, "tag(0x545A4450)")

    copy_file(os.path.join(BASE_DIR, "tcsh/build/tcsh"), os.path.join(ROOT_DIR, "usr/bin/tcsh"))
    add_idb("f", "0755", "root", "sys", "usr/bin/tcsh", TAG_EOE_TCSH, "tag(0x54435348)")

    copy_file(os.path.join(BASE_DIR, "tcsh/tcsh/complete.tcsh"), os.path.join(ROOT_DIR, "usr/share/tcsh/complete.tcsh"))
    add_idb("f", "0644", "root", "sys", "usr/share/tcsh/complete.tcsh", TAG_EOE_TCSH)

    copy_file(os.path.join(BASE_DIR, "tcsh/tcsh/dot.tcshrc"), os.path.join(ROOT_DIR, "usr/share/tcsh/examples/dot.tcshrc"))
    add_idb("f", "0644", "root", "sys", "usr/share/tcsh/examples/dot.tcshrc", TAG_EOE_TCSH)
    copy_file(os.path.join(BASE_DIR, "tcsh/tcsh/dot.login"), os.path.join(ROOT_DIR, "usr/share/tcsh/examples/dot.login"))
    add_idb("f", "0644", "root", "sys", "usr/share/tcsh/examples/dot.login", TAG_EOE_TCSH)

    with open(os.path.join(ROOT_DIR, "etc/csh.cshrc"), "w") as f:
        f.write("# /etc/csh.cshrc - System-wide settings for modern tcsh (Security Rollup 2026)\n"
                "if ( -f /usr/share/tcsh/complete.tcsh && $?prompt ) then\n"
                "    source /usr/share/tcsh/complete.tcsh\n"
                "endif\n")
    add_idb("f", "0644", "root", "sys", "etc/csh.cshrc", TAG_EOE_TCSH, "config(suggest)")

    tz_src_files = [
        "africa", "antarctica", "asia", "australasia", "backward", "etcetera", "europe", "factory",
        "northamerica", "southamerica", "iso3166.tab", "zone.tab", "zone1970.tab", "zonenow.tab", "leapseconds"
    ]
    tz_exitop = ('exitop("if [ -x $rbase/usr/bin/zic ]; then cd $rbase/usr/lib/locale/TZ && '
                 '$rbase/usr/bin/zic -b fat -d $rbase/usr/lib/locale/TZ africa antarctica asia australasia europe northamerica southamerica etcetera factory backward; fi")')
    for z in tz_src_files:
        copy_file(os.path.join(BASE_DIR, f"tzdata/src/{z}"), os.path.join(ROOT_DIR, f"usr/lib/locale/TZ/{z}"))
        if z == "northamerica":
            add_idb("f", "0644", "root", "sys", f"usr/lib/locale/TZ/{z}", TAG_EOE_BASE, tz_exitop)
        else:
            add_idb("f", "0644", "root", "sys", f"usr/lib/locale/TZ/{z}", TAG_EOE_BASE)

    print("=== Step 8: Staging Modern Type 1 Fonts and DPS Metrics (x_eoe_sw.Xfonts) ===")
    TAG_XFONTS = "patchSG002026_1_x_eoe_sw_Xfonts"

    # Ensure fonts are converted
    subprocess.run([sys.executable, os.path.join(BASE_DIR, "fonts/convert_fonts.py")], check=True)

    font_pfa_dir = os.path.join(BASE_DIR, "fonts/pfa")
    for f in sorted(os.listdir(font_pfa_dir)):
        src = os.path.join(font_pfa_dir, f)
        if f.endswith(".pfa"):
            copy_file(src, os.path.join(ROOT_DIR, "usr/lib/X11/fonts/Type1", f))
            add_idb("f", "0644", "root", "sys", f"usr/lib/X11/fonts/Type1/{f}", TAG_XFONTS)
        elif f.endswith(".afm"):
            afm_name = f[:-4]
            copy_file(src, os.path.join(ROOT_DIR, "usr/lib/DPS/AFM", afm_name))
            add_idb("f", "0644", "root", "sys", f"usr/lib/DPS/AFM/{afm_name}", TAG_XFONTS)

    # Copy Courier AFMs carried forward from patchSG0005785
    font_afm_dir = os.path.join(BASE_DIR, "fonts/afm")
    for f in sorted(os.listdir(font_afm_dir)):
        src = os.path.join(font_afm_dir, f)
        if os.path.isfile(src):
            copy_file(src, os.path.join(ROOT_DIR, "usr/lib/DPS/AFM", f))
            add_idb("f", "0644", "root", "sys", f"usr/lib/DPS/AFM/{f}", TAG_XFONTS)

    # Stage Terminus PCF.Z bitmap fonts into misc/
    font_pcf_dir = os.path.join(BASE_DIR, "fonts/pcf")
    for f in sorted(os.listdir(font_pcf_dir)):
        if f.endswith(".pcf.Z"):
            src = os.path.join(font_pcf_dir, f)
            copy_file(src, os.path.join(ROOT_DIR, "usr/lib/X11/fonts/misc", f))
            add_idb("f", "0644", "root", "sys", f"usr/lib/X11/fonts/misc/{f}", TAG_XFONTS)

    # Rollup scale, alias, and helper script
    copy_file(os.path.join(BASE_DIR, "fonts/fonts.scale.rollup"), os.path.join(ROOT_DIR, "usr/lib/X11/fonts/Type1/.fonts.scale.rollup2026"))
    copy_file(os.path.join(BASE_DIR, "fonts/fonts.alias.rollup"), os.path.join(ROOT_DIR, "usr/lib/X11/fonts/Type1/.fonts.alias.rollup2026"))
    copy_file(os.path.join(BASE_DIR, "fonts/fonts.alias.misc.rollup"), os.path.join(ROOT_DIR, "usr/lib/X11/fonts/misc/.fonts.alias.misc.rollup2026"))
    copy_file(os.path.join(BASE_DIR, "fonts/fonts_rollup.sh"), os.path.join(ROOT_DIR, "usr/lib/X11/fonts/Type1/.fonts_rollup.sh"))
    add_idb("f", "0644", "root", "sys", "usr/lib/X11/fonts/Type1/.fonts.alias.rollup2026", TAG_XFONTS)
    add_idb("f", "0644", "root", "sys", "usr/lib/X11/fonts/misc/.fonts.alias.misc.rollup2026", TAG_XFONTS)
    add_idb("f", "0755", "root", "sys", "usr/lib/X11/fonts/Type1/.fonts_rollup.sh", TAG_XFONTS)

    font_exitop = 'exitop("sh $rbase/usr/lib/X11/fonts/Type1/.fonts_rollup.sh install")'
    font_removeop = 'removeop("sh $rbase/usr/lib/X11/fonts/Type1/.fonts_rollup.sh remove")'
    add_idb("f", "0644", "root", "sys", "usr/lib/X11/fonts/Type1/.fonts.scale.rollup2026", TAG_XFONTS, f"{font_exitop} {font_removeop}")

    print("=== Step 9: Staging Formatted Manual Pages (eoe_man, openssh_man, openssl_man) ===")
    def format_man_page(src_file, dst_gz, is_pod=False, section=1, center="Manual", release="", substitutions=None):
        os.makedirs(os.path.dirname(dst_gz), exist_ok=True)
        if is_pod:
            cmd_pod = ["pod2man", f"--section={section}", f"--center={center}"]
            if release:
                cmd_pod.append(f"--release={release}")
            cmd_pod.append(src_file)
            p_pod = subprocess.Popen(cmd_pod, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            p_groff = subprocess.Popen(["groff", "-t", "-e", "-mandoc", "-Tascii", "-P-c"],
                                       stdin=p_pod.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            p_pod.stdout.close()
            out, _ = p_groff.communicate()
        else:
            with open(src_file, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            if substitutions:
                for k, v in substitutions.items():
                    content = content.replace(k, v)
            p_groff = subprocess.Popen(["groff", "-t", "-e", "-mandoc", "-Tascii", "-P-c"],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            out, _ = p_groff.communicate(input=content.encode("utf-8"))
        with gzip.open(dst_gz, "wb", compresslevel=9) as gz:
            gz.write(out)

    # 9.1 tcsh man page
    tcsh_sub = {
        "@PACKAGE_ENGLISH_DATE@": "April 12, 2024",
        "@PACKAGE_ORIGIN@": "Astron",
        "@PACKAGE_VERSION@": "6.24.16",
        "@PACKAGE_DATE@": "2024-04-12",
        "@PACKAGE_BUGREPORT@": "https://bugs.astron.com/",
        "@PACKAGE_MAILLIST@": "https://mailman.astron.com/mailman/listinfo/tcsh"
    }
    tcsh_dst = os.path.join(ROOT_DIR, "usr/share/catman/u_man/cat1/tcsh.z")
    format_man_page(os.path.join(BASE_DIR, "tcsh/tcsh/tcsh.man.in"), tcsh_dst, substitutions=tcsh_sub)
    add_idb("f", "0644", "root", "sys", "usr/share/catman/u_man/cat1/tcsh.z", TAG_EOE_MAN_BASE)

    # 9.2 OpenSSH man pages
    ssh_man_files = [
        ("ssh.1", "u_man/cat1/openssh", "ssh.z"),
        ("scp.1", "u_man/cat1/openssh", "scp.z"),
        ("sftp.1", "u_man/cat1/openssh", "sftp.z"),
        ("ssh-add.1", "u_man/cat1/openssh", "ssh-add.z"),
        ("ssh-agent.1", "u_man/cat1/openssh", "ssh-agent.z"),
        ("ssh-keygen.1", "u_man/cat1/openssh", "ssh-keygen.z"),
        ("ssh-keyscan.1", "u_man/cat1/openssh", "ssh-keyscan.z"),
        ("ssh_config.5", "p_man/cat5/openssh", "ssh_config.z"),
        ("sshd_config.5", "p_man/cat5/openssh", "sshd_config.z"),
        ("moduli.5", "p_man/cat5/openssh", "moduli.z"),
        ("sshd.8", "a_man/cat8/openssh", "sshd.z"),
        ("sftp-server.8", "a_man/cat8/openssh", "sftp-server.z"),
        ("ssh-keysign.8", "a_man/cat8/openssh", "ssh-keysign.z"),
        ("ssh-pkcs11-helper.8", "a_man/cat8/openssh", "ssh-pkcs11-helper.z"),
        ("ssh-sk-helper.8", "a_man/cat8/openssh", "ssh-sk-helper.z"),
    ]
    for src, sdir, dst in ssh_man_files:
        src_path = os.path.join(BASE_DIR, f"openssh/openssh/{src}")
        dst_path = os.path.join(ROOT_DIR, f"usr/share/catman/{sdir}/{dst}")
        format_man_page(src_path, dst_path)
        add_idb("f", "0644", "root", "sys", f"usr/share/catman/{sdir}/{dst}", TAG_SSH_MAN)

    add_idb("l", "0777", "root", "sys", "usr/share/catman/u_man/cat1/openssh/slogin.z", TAG_SSH_MAN, "symval(ssh.z)")

    # 9.3 OpenSSL man pages
    ssl_doc_dir = os.path.join(BASE_DIR, "openssl-1.1.1/openssl/doc")
    for f in sorted(os.listdir(os.path.join(ssl_doc_dir, "man1"))):
        if f.endswith(".pod"):
            base = f[:-4]
            src_path = os.path.join(ssl_doc_dir, f"man1/{f}")
            dst_path = os.path.join(ROOT_DIR, f"usr/share/catman/u_man/cat1/openssl/{base}.z")
            format_man_page(src_path, dst_path, is_pod=True, section=1, center="OpenSSL", release="1.1.1w")
            add_idb("f", "0644", "root", "sys", f"usr/share/catman/u_man/cat1/openssl/{base}.z", TAG_SSL_MAN)

    for dgst in ["md2", "md4", "md5", "mdc2", "ripemd160", "sha", "sha1", "sha224", "sha256", "sha384", "sha512"]:
        add_idb("l", "0777", "root", "sys", f"usr/share/catman/u_man/cat1/openssl/{dgst}.z", TAG_SSL_MAN, "symval(dgst.z)")

    for f in sorted(os.listdir(os.path.join(ssl_doc_dir, "man5"))):
        if f.endswith(".pod"):
            base = f[:-4]
            src_path = os.path.join(ssl_doc_dir, f"man5/{f}")
            dst_path = os.path.join(ROOT_DIR, f"usr/share/catman/p_man/cat5/openssl/{base}.z")
            format_man_page(src_path, dst_path, is_pod=True, section=5, center="OpenSSL", release="1.1.1w")
            add_idb("f", "0644", "root", "sys", f"usr/share/catman/p_man/cat5/openssl/{base}.z", TAG_SSL_MAN)

    for f in sorted(os.listdir(os.path.join(ssl_doc_dir, "man7"))):
        if f.endswith(".pod"):
            base = f[:-4]
            src_path = os.path.join(ssl_doc_dir, f"man7/{f}")
            dst_path = os.path.join(ROOT_DIR, f"usr/share/catman/a_man/cat7/openssl/{base}.z")
            format_man_page(src_path, dst_path, is_pod=True, section=7, center="OpenSSL", release="1.1.1w")
            add_idb("f", "0644", "root", "sys", f"usr/share/catman/a_man/cat7/openssl/{base}.z", TAG_SSL_MAN)

    for a in ["DES", "Modes", "of"]:
        add_idb("l", "0777", "root", "sys", f"usr/share/catman/a_man/cat7/openssl/{a}.z", TAG_SSL_MAN, "symval(des_modes.z)")

    print("=== Step 10: Generating Spec and IDB ===")
    idb_entries.sort(key=lambda x: (x[0], x[1]))
    idb_path = os.path.join(DIST_DIR, f"{PRODUCT_NAME}.idb")
    with open(idb_path, "w") as f:
        for _, entry in idb_entries:
            f.write(entry + "\n")
    print(f"Wrote {len(idb_entries)} records to {idb_path}")

    spec_content = f"""product {PRODUCT_NAME}
    id "{PRODUCT_DESC}"

    image ifl_eoe_sw
        id "Image Format Executable Software (32-bit o32 & n32)"
        version {VERS_IFL}
        subsys c++ default patch
            id "Modernized 32-bit Shared Libraries (zlib, libpng, libtiff, libjpeg)"
            follows ifl_eoe.sw.c++ 1314000000 1319999999
            replaces patchSG0005734.ifl_eoe_sw.c++ 0 maxint
            replaces patchSG002026.ifl_eoe_sw.c++ 0 maxint
            replaces {PRODUCT_NAME}.ifl_eoe_sw.c++ 0 maxint
            exp {TAG_IFL}
        endsubsys
    endimage

    image ifl_eoe_sw64
        id "Image Format Executable Software (64-bit n64)"
        version {VERS_IFL}
        subsys c++ default patch
            id "Modernized 64-bit Media & Compression Libraries (n64)"
            follows eoe.sw64.lib 1280000000 1289999999
            replaces patchSG0005734.ifl_eoe_sw64.c++ 0 maxint
            replaces patchSG002026.ifl_eoe_sw64.c++ 0 maxint
            replaces {PRODUCT_NAME}.ifl_eoe_sw64.c++ 0 maxint
            exp {TAG_IFL64}
        endsubsys
    endimage

    image ifl_dev_sw
        id "Image Format Development Software"
        version {VERS_IFL}
        subsys c++ default patch
            id "Modernized Media & Compression Headers and Archives"
            follows ifl_dev.sw.c++ 1314000000 1319999999
            replaces patchSG002026.ifl_dev_sw.c++ 0 maxint
            replaces {PRODUCT_NAME}.ifl_dev_sw.c++ 0 maxint
            exp {TAG_IFLDEV}
        endsubsys
    endimage

    image openssl_sw
        id "OpenSSL 0.9.7 Execution Environment (32-bit n32)"
        version {VERS_SSL}
        subsys lib32 default patch
            id "OpenSSL 0.9.7 n32 Modernized Shared & Static Libraries"
            follows openssl.sw.lib32 1270000000 1279999999
            replaces patchSG0005533.openssl_sw.lib32 0 maxint
            replaces patchSG002026.openssl_sw.lib32 0 maxint
            replaces {PRODUCT_NAME}.openssl_sw.lib32 0 maxint
            exp {TAG_SSL_LIB32}
        endsubsys
        subsys base default patch
            id "OpenSSL 0.9.7 Tool"
            follows openssl.sw.base 1270000000 1279999999
            replaces patchSG0005533.openssl_sw.base 0 maxint
            replaces patchSG002026.openssl_sw.base 0 maxint
            replaces {PRODUCT_NAME}.openssl_sw.base 0 maxint
            exp {TAG_SSL_BASE}
        endsubsys
    endimage

    image openssl11_sw
        id "OpenSSL 1.1.1 Modern Cryptographic Engine"
        version {VERS_SSL11}
        subsys lib32 default
            id "OpenSSL 1.1.1w n32 Shared Libraries (32-bit)"
            replaces patchSG002026.openssl11_sw.lib32 0 maxint
            replaces {PRODUCT_NAME}.openssl11_sw.lib32 0 maxint
            exp {TAG_SSL11_LIB32}
        endsubsys
        subsys lib64 default patch
            id "OpenSSL 1.1.1w 64-bit Shared Libraries (n64)"
            follows eoe.sw64.lib 1280000000 1289999999
            replaces patchSG002026.openssl11_sw.lib64 0 maxint
            replaces {PRODUCT_NAME}.openssl11_sw.lib64 0 maxint
            exp {TAG_SSL11_LIB64}
        endsubsys
        subsys dev default
            id "OpenSSL 1.1.1w Development Headers and CLI"
            replaces patchSG002026.openssl11_sw.dev 0 maxint
            replaces {PRODUCT_NAME}.openssl11_sw.dev 0 maxint
            exp {TAG_SSL11_DEV}
        endsubsys
    endimage

    image openssh_sw
        id "OpenSSH 9.9p2 Modern Secure Shell Suite"
        version {VERS_SSH}
        subsys client default patch
            id "OpenSSH 9.9p2 Client Utilities"
            follows openssh.sw.client 1270000000 1279999999
            replaces patchSG002026.openssh_sw.client 0 maxint
            replaces {PRODUCT_NAME}.openssh_sw.client 0 maxint
            exp {TAG_SSH_CLIENT}
        endsubsys
        subsys common default patch
            id "OpenSSH 9.9p2 Common Key and Configuration Tools"
            follows openssh.sw.common 1270000000 1279999999
            replaces patchSG002026.openssh_sw.common 0 maxint
            replaces {PRODUCT_NAME}.openssh_sw.common 0 maxint
            exp {TAG_SSH_COMMON}
        endsubsys
        subsys server default patch
            id "OpenSSH 9.9p2 PrivSep Server and Daemons"
            follows openssh.sw.common 1270000000 1279999999
            replaces openssh.sw.server 0 maxint
            replaces patchSG002026.openssh_sw.server 0 maxint
            replaces {PRODUCT_NAME}.openssh_sw.server 0 maxint
            exp {TAG_SSH_SERVER}
        endsubsys
    endimage

    image eoe_sw
        id "IRIX Execution Environment Software"
        version {VERS_EOE}
        subsys termbase default patch
            id "Modernized Terminal Database (256-color & modern terminal profiles)"
            follows eoe.sw.termbase 1280000000 1289999999
            replaces patchSG002026.eoe_sw.termbase 0 maxint
            replaces {PRODUCT_NAME}.eoe_sw.termbase 0 maxint
            exp {TAG_EOE_TERM}
        endsubsys
        subsys base default patch
            id "Modernized TimeZone Processing and tzdata2026e Database"
            follows eoe.sw.base 1280000000 1289999999
            replaces patchSG0007204.eoe_sw.base 0 maxint
            replaces patchSG002026.eoe_sw.base 0 maxint
            replaces {PRODUCT_NAME}.eoe_sw.base 0 maxint
            exp {TAG_EOE_BASE}
        endsubsys
        subsys tcsh default patch
            id "tcsh 6.24.16 Modern C Shell"
            follows eoe.sw.base 1280000000 1289999999
            replaces patchSG002026.eoe_sw.tcsh 0 maxint
            replaces {PRODUCT_NAME}.eoe_sw.tcsh 0 maxint
            exp {TAG_EOE_TCSH}
        endsubsys
    endimage

    image x_eoe_sw
        id "X11 Execution Environment Software"
        version {VERS_XFONTS}
        subsys Xfonts default patch
            id "Modernized Scalable & Terminal Typography (Inconsolata, Hack, JetBrains Mono, Droid, Roboto, Terminus, Nerd Font Symbols) & AFM Metrics"
            follows x_eoe.sw.Xfonts 1280000000 1289999999
            replaces patchSG0005785.x_eoe_sw.Xfonts 0 maxint
            replaces patchSG002026.x_eoe_sw.Xfonts 0 maxint
            replaces {PRODUCT_NAME}.x_eoe_sw.Xfonts 0 maxint
            exp {TAG_XFONTS}
        endsubsys
    endimage

    image eoe_man
        id "IRIX Execution Environment Online Manual Pages"
        version {VERS_EOE}
        subsys base default patch
            id "tcsh 6.24.16 Modern C Shell Man Page"
            follows eoe.man.base 1280000000 1289999999
            replaces patchSG002026.eoe_man.base 0 maxint
            replaces {PRODUCT_NAME}.eoe_man.base 0 maxint
            exp {TAG_EOE_MAN_BASE}
        endsubsys
    endimage

    image openssh_man
        id "OpenSSH Online Manual Pages"
        version {VERS_SSH}
        subsys manpages default patch
            id "OpenSSH 9.9p2 Manual Pages"
            follows openssh.man.manpages 1270000000 1279999999
            replaces patchSG002026.openssh_man.manpages 0 maxint
            replaces {PRODUCT_NAME}.openssh_man.manpages 0 maxint
            exp {TAG_SSH_MAN}
        endsubsys
    endimage

    image openssl_man
        id "OpenSSL Online Manual Pages"
        version {VERS_SSL}
        subsys manpages default patch
            id "OpenSSL 1.1.1w Manual Pages"
            follows openssl.man.manpages 1270000000 1279999999
            replaces patchSG002026.openssl_man.manpages 0 maxint
            replaces {PRODUCT_NAME}.openssl_man.manpages 0 maxint
            exp {TAG_SSL_MAN}
        endsubsys
    endimage
endproduct
"""
    spec_path = os.path.join(DIST_DIR, f"{PRODUCT_NAME}.spec")
    with open(spec_path, "w") as f:
        f.write(spec_content)
    print(f"Wrote spec to {spec_path}")

    print("=== Step 11: Generating build_dist.sh for Guest execution ===")
    build_script_path = os.path.join(DIST_DIR, "build_dist.sh")
    with open(build_script_path, "w") as f:
        f.write(f"""#!/bin/sh
set -e
STAGE=/tmp/patchSG002026_root
DIST=/shared/updates-irix/dist
OUT=/shared/updates-irix/dist/out

rm -rf "$STAGE"
mkdir -p "$STAGE"

echo "--- Copying staged tree to local XFS /tmp ---"
cp -r /shared/updates-irix/dist/root/* "$STAGE/"

echo "--- Stripping & tagging binaries on local XFS ---"
cd "$STAGE"
for bin in usr/bin/openssl.097 usr/bin/openssl usr/bin/openssl11 \\
           usr/bin/zic usr/bin/zdump usr/bin/tcsh \\
           usr/bin/ssh usr/bin/scp usr/bin/sftp usr/bin/ssh-add usr/bin/ssh-agent \\
           usr/bin/ssh-keyscan usr/bin/ssh-keygen usr/bin/ssh-keysign \\
           usr/sbin/sshd usr/libexec/sshd-session usr/libexec/sftp-server \\
           usr/libexec/ssh-pkcs11-helper usr/libexec/ssh-sk-helper; do
    if test -f "$bin"; then
        strip "$bin"
    fi
done

if test -f usr/bin/openssl.097; then /usr/sbin/tag 0x53534c30 usr/bin/openssl.097; fi
if test -f usr/bin/openssl; then /usr/sbin/tag 0x53534c31 usr/bin/openssl; fi
if test -f usr/bin/openssl11; then /usr/sbin/tag 0x53534c31 usr/bin/openssl11; fi
if test -f usr/bin/zic; then /usr/sbin/tag 0x545A4943 usr/bin/zic; fi
if test -f usr/bin/zdump; then /usr/sbin/tag 0x545A4450 usr/bin/zdump; fi
if test -f usr/bin/tcsh; then /usr/sbin/tag 0x54435348 usr/bin/tcsh; fi

for bin in usr/bin/ssh usr/bin/scp usr/bin/sftp usr/bin/ssh-add usr/bin/ssh-agent usr/bin/ssh-keyscan usr/bin/ssh-keygen usr/bin/ssh-keysign \\
           usr/sbin/sshd usr/libexec/sshd-session usr/libexec/sftp-server usr/libexec/ssh-pkcs11-helper usr/libexec/ssh-sk-helper; do
    if test -f "$bin"; then
        /usr/sbin/tag 0x53534832 "$bin"
    fi
done

echo "--- Sorting IDB ---"
cd "$DIST"
sort -k 5,6 {PRODUCT_NAME}.idb -o {PRODUCT_NAME}.sorted.idb

echo "--- Running gendist ---"
/usr/sbin/gendist -verbose -sbase "$STAGE" -idb {PRODUCT_NAME}.sorted.idb -spec {PRODUCT_NAME}.spec -dist "$OUT"

echo "--- Building tardist archive ---"
cd "$OUT"
tar cf "/tmp/{PRODUCT_NAME}.tardist" *
cp "/tmp/{PRODUCT_NAME}.tardist" "/shared/updates-irix/{PRODUCT_NAME}.tardist"
rm -f "/tmp/{PRODUCT_NAME}.tardist"
rm -rf "$STAGE"
echo "TARDIST_BUILD_SUCCESS"
""")
    os.chmod(build_script_path, 0o755)

    print("=== Step 12: Executing build_dist.sh in Guest ===")
    out = run_guest_script(f"{GUEST_SHARED}/dist/build_dist.sh")
    print(out)

    links = [
        os.path.join(BASE_DIR, "security_rollup_2026-beta1.tardist"),
        os.path.join(BASE_DIR, "security_rollup_2026.tardist"),
        os.path.join(BASE_DIR, "patchSG002026.tardist"),
    ]
    for link_target in links:
        if os.path.islink(link_target) or os.path.exists(link_target):
            os.remove(link_target)
        os.symlink(f"{PRODUCT_NAME}.tardist", link_target)
    print(f"Successfully generated {BASE_DIR}/{PRODUCT_NAME}.tardist and tardist symlinks!")

if __name__ == "__main__":
    main()
