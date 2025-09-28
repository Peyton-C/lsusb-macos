# lsusb-macos
A simple python script that outputs connected USB and Thunderbolt devices in a format similar to lsusb using `system_profiler` on Mac OS X 10.7 and newer with Python 3.7+.

## Sample Output
```
USB Devies:
Location: 01100000: ID 1d5c:5801 Fresco Logic, Inc. USB2.0 Hub
Location: 01150000: ID 3188:5335 XFANIC Thunderbolt 4 Docking Station
Location: 01140000: ID 2109:2822 VIA Labs, Inc. USB2.0 Hub
Location: 01142000: ID 046d:0ab5 Logitech G733 Gaming Headset
Location: 01145000: ID 2109:8822 VIA Labs, Inc. USB Billboard Device
Location: 01130000: ID 35d6:2510 Bridgesil USB2.1 Hub
Location: 01131000: ID 05e3:0610 GenesysLogic USB2.1 Hub
Location: 01131100: ID 05ac:0324 Apple Inc. Magic Trackpad
Location: 01133000: ID 046d:c545 Logitech USB Receiver
Location: 01134000: ID 046d:c539 Logitech USB Receiver
Location: 01110000: ID 1d5c:7112 - Unnamed Device
Location: 01200000: ID 8087:0b40 Intel Corporation. USB3.0 Hub
Location: 01240000: ID 2109:0822 VIA Labs, Inc. USB3.1 Hub
Location: 01244000: ID 0bda:8153 Realtek USB 10/100/1000 LAN
Location: 01230000: ID 35d6:3510 Bridgesil USB3.2 Hub
Location: 01220000: ID 0bda:8157 Realtek USB 10/100/1G/2.5G/5G LAN

Thunderbolt / USB 4 Devices:
ID: 2b89:0708 Ugreen Group Limited Thunderbolt 4 Docking Station (8-in-1)
```