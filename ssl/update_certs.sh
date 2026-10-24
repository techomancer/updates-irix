#!/bin/sh
# update_certs.sh - Update Mozilla Root CA bundle from curl.se and verify
# exclusions for compromised/distrusted roots (e.g. eMudhra weak keys incident).
set -e

SSL_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$SSL_DIR/ca-certificates.crt"
URL="https://curl.se/ca/cacert.pem"

echo ">>> Fetching latest Mozilla CA bundle from $URL..."
curl -s -f -o "$TARGET.tmp" "$URL"

# Sanity check: ensure the file contains valid certificates
CERT_COUNT=$(grep -c "BEGIN CERTIFICATE" "$TARGET.tmp" || true)
if [ "$CERT_COUNT" -lt 50 ]; then
    echo "Error: Downloaded CA bundle has too few certificates ($CERT_COUNT)" >&2
    rm -f "$TARGET.tmp"
    exit 1
fi

# Verify that compromised roots are NOT present:
# 1. emSign ECC Root CA - G3 (used to sign compromised eMudhra intermediates)
# 2. AAA Certificate Services (Sectigo cross-sign for compromised eMudhra intermediates)
python3 -c "
import sys, re, subprocess
with open('$TARGET.tmp') as f:
    data = f.read()
certs = re.findall(r'(-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----)', data, re.DOTALL)
for c in certs:
    p = subprocess.run(['openssl', 'x509', '-noout', '-subject'], input=c.encode(), capture_output=True)
    subj = p.stdout.decode().strip()
    if 'emSign ECC Root CA - G3' in subj:
        sys.exit('Error: Found compromised root: emSign ECC Root CA - G3')
    if 'AAA Certificate Services' in subj:
        sys.exit('Error: Found compromised root: AAA Certificate Services')
print(f'Verification passed: {len(certs)} trusted roots, compromised roots excluded.')
"

mv "$TARGET.tmp" "$TARGET"
echo ">>> Successfully updated $TARGET ($CERT_COUNT root certificates)."
