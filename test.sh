#!/bin/bash
# Automatically try every supported combination

# Tahoe and Newer
printf "Tahoe"
python3 ./lsusb.py -D USB ./json_examples/tahoe_usb_full.json -D TB ./json_examples/tahoe_tb.json -os 26.1

# Sequoia - Catalina
printf "\nSequoia - USB\n"
python3 ./lsusb.py -D USB ./json_examples/sequoia_intel_usb_full.json -D TB ./json_examples/sequoia_intel_tb.json -os  15.5

# Mojave - Yosemite
printf "\nMojave - USB\n" 
python3 ./lsusb.py -D USB ./json_examples/hs_xml_usb_basic.plist -os  10.13 

# Mavricks and Older
printf "\nMavricks - USB\n"
python3 ./lsusb.py -D USB ./json_examples/lion_xml_usb_basic.plist -os 10.7