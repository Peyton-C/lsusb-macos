#!/bin/bash
# Automatically try every supported combination

EXTRA_ARGS=""

# Tahoe and Newer
printf "Tahoe\n"
python3 ./lsusb.py -D USB ./tests/Version4/tahoe_usb_full.json -D TB ./tests/Version4/tahoe_tb.json -os 26.1 $EXTRA_ARGS

# Sequoia - Catalina
printf "\n\nSequoia\n"
python3 ./lsusb.py -D USB ./tests/Version3/sequoia_intel_usb_full.json -D TB ./tests/Version3/sequoia_intel_tb.json -os  15.5 $EXTRA_ARGS

# Mojave - Yosemite
printf "\n\nMojave\n" 
python3 ./lsusb.py -D USB ./tests/Version2/hs_xml_usb_basic.plist -os 10.13 $EXTRA_ARGS

# Mavricks and Older
printf "\n\nMavricks\n"
python3 ./lsusb.py -D USB ./tests/Version1/lion_xml_usb_basic.plist -os 10.7 $EXTRA_ARGS