# lsusb-macos
A simple python script that outputs connected USB and Thunderbolt devices in a format similar to lsusb using `system_profiler` on Mac OS X 10.6 and newer with Python 3.7+.

## Sample Output
```
USB Devies:
Location: 00000000: ID 05ac:0000 Apple Inc. USB 3.1 Bus
Location: 01000000: ID 05ac:0000 Apple Inc. USB 3.1 Bus
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
Location: 02000000: ID 05ac:0000 Apple Inc. USB 3.1 Bus

Thunderbolt / USB 4 Devices:
ID 0001:0000 Apple Inc. Thunderbolt / USB 4 Bus
ID 0001:0000 Apple Inc. Thunderbolt / USB 4 Bus
ID 0001:0000 Apple Inc. Thunderbolt / USB 4 Bus
ID 2b89:0708 Ugreen Group Limited Thunderbolt 4 Docking Station (8-in-1)
```

## Copatability
| macOS Version | Python Version | USB | USB Root Hubs  | TB | Format            |
| :-----------: | :------------: | :-: | :------------: | -- | ----------------- |
| 10.6          | 3.7            |  ?  |  ?             | X  | 1 - Legacy        |
| 10.7          | 3.7            |  Y  |  Y             | X  | 1 - Legacy        |
| 10.8          | 3.7            |  Y  |  Y             | X  | 1 - Legacy        |
| 10.9          | 3.11           |  ?  |  ?             | X  | 1 - Legacy        |
| 10.10         | 3.11           |  Y  |  ~             | X  | 2 - Modern - XML  |
| 10.11         | 3.11           |  Y  |  ~             | X  | 2 - Modern - XML  |
| 10.12         | 3.11           |  Y  |  ~             | X  | 2 - Modern - XML  |
| 10.13         | 3.13           |  Y  |  ~             | X  | 2 - Modern - XML  |
| 10.14         | 3.13           |  Y  |  ~             | X  | 2 - Modern - XML  |
| 10.15         | 3.13           |  Y  |  ~             | Y  | 3 - Modern - JSON |
| 11            | 3.13           |  Y  |  ~             | Y  | 3 - Modern - JSON |
| 12            | 3.13           |  Y  |  ~             | Y  | 3 - Modern - JSON |
| 13            | 3.13           |  Y  |  ~             | Y  | 3 - Modern - JSON |
| 14            | 3.13           |  Y  |  ~             | Y  | 3 - Modern - JSON |
| 15            | 3.13           |  Y  |  ~             | Y  | 3 - Modern - JSON |
| 26            | 3.13           |  Y  |  Y             | Y  | 4 - Host - JSON   |

### Copatability Notes
- Thunderbolt support is disabled for 10.14 and lower because I don't have a way to properly test Format 1 and Format 2 TB, although Format 2 TB should work with minor modications.
- Root hubs lack the location ID on 10.10-15.X because apple doesnt give you any form of location ID outside of a device itself.
- 10.6 should work without any modifacations

## Credit
Thank you to the following people for their contributions:
- [@kirb]("https://github.com/kirb") - [macOS Tahoe Thunderbolt 3 Output](./json_examples/tahoe_tb_kirb.json)
- [@jlhonora]("https://github.com/jlhonora") - [Information about older macOS system_profiler outputs ]("https://github.com/jlhonora/lsusb")