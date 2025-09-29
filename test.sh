#!/bin/bash
# Automatically try every supported combination

# Tahoe and Newer
printf "\nTahoe - USB\n"
python3 ./lsusb.py -D USB ./json_examples/tahoe_usb_full.json 26.1

printf "\nTahoe - Thunderbolt / USB 4"
python3 ./lsusb.py -D TB ./json_examples/tahoe_tb.json 26.1

# Sequoia - Catalina
printf "\nSequoia - USB\n"
python3 ./lsusb.py -D USB ./json_examples/sequoia_intel_usb_full.json 15

printf "\nSequoia - Thunderbolt / USB 4"
python3 ./lsusb.py -D TB ./json_examples/sequoia_intel_tb.json 26.1

# Mojave - Yosemite
printf "\nMojave - USB\n" 
python3 ./lsusb.py -D USB ./json_examples/hs_xml_usb_basic.plist 10.13 

# Mavricks and Older
printf "\nMavricks - USB\n"
python3 ./lsusb.py -D USB ./json_examples/lion_xml_usb_basic.plist 10.07