#!/bin/sh
set -e
mkdir -p /tmp/fonttest
cp /shared/updates-irix/Inconsolata-Regular.pfa /tmp/fonttest/
cat << 'EOF' > /tmp/fonttest/fonts.scale
1
Inconsolata-Regular.pfa -misc-inconsolata-medium-r-normal--0-0-0-0-m-0-iso8859-1
EOF

/usr/bin/X11/mkfontdir /tmp/fonttest
cat /tmp/fonttest/fonts.dir

export DISPLAY=:0.0
xset +fp /tmp/fonttest
xset fp rehash
xlsfonts -fn '*-inconsolata-*'
echo "FONT_TEST_SUCCESS"
