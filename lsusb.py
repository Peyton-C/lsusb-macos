#!/usr/bin/env python3

import json, plistlib, platform, os, sys, subprocess, argparse
from pathlib import Path

VERBOSE = False
EXTRA_INFO = False
DEBUG_TYPE = [False, False]
DEBUG_FILE = ["", ""]
INDENT = "     "
filt_vid = None
filt_pid = None

USB_DATA_PROPERTIES = {
                  # 10.7 - 10.9      10.10 - 10.14     10.15 - 15.X.    26.0+
    "ARG1":       ["SPUSBDataType",   "SPUSBDataType", "SPUSBDataType", "SPUSBHostDataType"],
    "ARG2":       ["-xml",            "-xml",          "-json",         "-json"],
    "LID":        ["g_location_id",   "location_id",   "location_id",   "USBKeyLocationID"],
    "RLID":       ["usb_bus_number",  "location_id",   "location_id",   "USBKeyLocationID"],
    "VID":        ["b_vendor_id",     "vendor_id",     "vendor_id",     "USBDeviceKeyVendorID"],
    "PID":        ["a_product_id",    "product_id",    "product_id",    "USBDeviceKeyProductID"],
    "MFR":        ["f_manufacturer",  "manufacturer",  "manufacturer",  "USBDeviceKeyVendorName"],
    "SPEED":      ["e_device_speed",  "device_speed",  "device_speed",  "USBDeviceKeyLinkSpeed"],
    "NAME":       ["_name",           "_name",         "_name",         "_name"],
    "HEAD":       ["_items",          "_items",        "SPUSBDataType", "SPUSBHostDataType"],
    "SERIAL":     ["d_serial_num",    "serial_num",    "serial_num",    "USBDeviceKeySerialNumber"],
    "APPL_SERIAL":[None,              None,            None,            None]
}

TB_DATA_PROPERTIES = {
                  # Unsupported.  10.15 - 15.X              26.0+
    "ARG1":       [None, None,    "SPThunderboltDataType",  "SPThunderboltDataType"],
    "ARG2":       [None, None,    "-json",                  "-json"],
    "LID":        [None, None,    None,                     None], # This is kinda still a janky workaround becasue i want to share as much as i can between USB and TB as i can but i dont wanna make it overly complex either
    "RLID":       [None, None,    None,                     None],
    "VID":        [None, None,    "vendor_id_key",          "vendor_id_key"],
    "PID":        [None, None,    "device_id_key",          "device_id_key"],
    "MFR":        [None, None,    "vendor_name_key",        "vendor_name_key"],
    "SPEED":      [None, None,    "mode_key",               "mode_key"],
    "NAME":       [None, None,    "_name",                  "_name"],
    "HEAD":       [None, None,    "SPThunderboltDataType",  "SPThunderboltDataType"],
    "SERIAL":     [None, None,    None,                     None],
    "APPL_SERIAL":[None, None,    "aapl_serial_number_key", None]
}

SPEED_NAME = {
    "usb1_ls": "USB 1.1 LS - 1.5 Mb/s",
    "usb1_fs": "USB 1.1 HS - 12 Mb/s",
    "usb2": "USB 2.0 - 480 Mb/s",
    "usb30": "USB 3.0 - 5 Gb/s",
    "usb31": "USB 3.1 - 10 Gb/s",
    "usb32": "USB 3.2x2 - 10 Gb/s",
    "usb4": "USB 4.0 - 40 Gb/s",
    "usb?": "Unknown USB",
    "tb1": "Thunderbolt 1 - 10 Gb/s",
    "tb2": "Thunderbolt 2 - 20 Gb/s",
    "tb3": "Thunderbolt 3 - 40 Gb/s",
    "tb4": "Thunderbolt 4 - 40 Gb/s",
    "tb5": "Thunderbolt 5 - 120 Gb/s",
    "tb?": "Unknown Thunderbolt"
}

SPEED_INDEX = {
    "1.5 Mb/s":          SPEED_NAME["usb1_ls"],
    "full_speed":        SPEED_NAME["usb1_fs"],
    "12 Mb/s":           SPEED_NAME["usb1_fs"],
    "high_speed":        SPEED_NAME["usb2"],
    "480 Mb/s":          SPEED_NAME["usb2"],
    "super_speed":       SPEED_NAME["usb30"],
    "5 Gb/s":            SPEED_NAME["usb30"],
    "10 Gb/s":           SPEED_NAME["usb31"],
    "usb_four":          SPEED_NAME["usb4"],
    "thunderbolt_one":   SPEED_NAME["tb1"],
    "thunderbolt_two":   SPEED_NAME["tb2"],
    "thunderbolt_three": SPEED_NAME["tb3"],
    "thunderbolt_four":  SPEED_NAME["tb4"],
    "thunderbolt_five":  SPEED_NAME["tb5"]
}

# Apple is stupid and wont just directly give us info on certain devices like root hubs and bluetooth controllers
DEVICE_OVERRIDE = {
    # _name output                    MFR                Speed                     Fancy Name                  VID     PID
    "Generic":                        ["Generic",        SPEED_NAME["usb?"],     "Unknown Bus",              "05ac", "0000"],
    "USBBus":                         ["Apple Inc.",     SPEED_NAME["usb1_fs"],  "USB 1.1 Bus",              "05ac", "0000"],
    "USB20Bus":                       ["Apple Inc.",     SPEED_NAME["usb2"],     "USB 2.0 Bus",              "05ac", "0000"],
    "USB30Bus":                       ["Apple Inc.",     SPEED_NAME["usb30"],    "USB 3.0 Bus",              "05ac", "0000"],
    "USB 3.1 Bus":                    ["Apple Inc.",     SPEED_NAME["usb31"],    "USB 3.1 Bus",              "05ac", "0000"],
    "thunderbolt_bus":                ["Apple Inc.",     SPEED_NAME["tb?"],      "Thunderbolt 1 / 2 Bus",    "0001", "0000"],
    "thunderboltusb4_bus_":           ["Apple Inc.",     SPEED_NAME["tb4"],      "Thunderbolt / USB 4 Bus",  "0001", "0000"],
    "OHCI Root Hub Simulation":       ["Apple Inc.",     SPEED_NAME["usb1_fs"],  "Virtual USB 1.1 Bus",      "05ac", "8005"],
    "UHCI Root Hub Simulation":       ["Apple Inc.",     SPEED_NAME["usb1_fs"],  "Virtual USB 1.1 Bus",      "05ac", "0000"],
    "EHCI Root Hub Simulation":       ["Apple Inc.",     SPEED_NAME["usb2"],     "Virtual USB 2.0 Bus",      "05ac", "8006"],
    "XHCI Root Hub Simulation":       ["Apple Inc.",     SPEED_NAME["usb30"],    "Virtual USB 3.0 Bus",      "05ac", "8007"],
    "Bluetooth USB Host Controller":  ["Broadcom Corp.", SPEED_NAME["usb1_fs"],  "Bluetooth USB Controller", "05ac", "8290"] # MacbookPro12,1 + Others
}

def clean_macos_version(raw):
    parts = raw.split(".")
    major = int(parts[0])
    minor = int(parts[1])
    if len(parts) > 2:
        patch = (int(parts[2]))
    else:
        patch = 0
    
    ver = (major * 10000) + (minor * 100) + (patch)
    
    if ver >= 260000:
        VERSION = 4
    elif 101500 <= ver <= 260000:
        VERSION = 3
    elif 101000 <= ver <= 101400:
        VERSION = 2
    else:
        VERSION = 1
    
    # 10.6 and 10.9 are untested
    if (ver >= 100900 and ver <= 100999) or (ver >= 100600 and ver <= 100699):
        print("Your version is untested, please make an issue on Github with info \n" \
        "about if it worked along with the output of the following command: \n" \
        "system_profiler SPUSBDataType -xml \n")
    
    return VERSION, ver

def arguments():
    global DEBUG_FILE, DEBUG_TYPE, VERSION, filt_pid, filt_vid, VERBOSE, macos_version, EXTRA_INFO
    parser = argparse.ArgumentParser(
        prog="lsusb-macos",
        description="Display connected USB and Thunderbolt Devices on macOS / Mac OS X"
    )

    parser.add_argument("-v", "--verbose", help="Output the raw information from system_profiler", action='store_true')
    parser.add_argument("-d", nargs=1, metavar=("Vendor:Product"), help="Show only devices with the specified vendor and product ID numbers (in Hexadecimal) ")
    parser.add_argument("-e", "--extra", help="Include extra information about the device, including Speed and serial", action='store_true')
    parser.add_argument("-D", "--debug", nargs=2, metavar=("Type", "File"), action="append", help="Simulate Connected Devices, Type (USB|TB) and File (JSON or XML)")
    parser.add_argument("-os", "--osver", help="Debug OS Version (ie 10.7, 10.13, 15.5, 26.1, etc)")

    args = parser.parse_args()
    if args.debug:
        if not args.osver:
            sys.exit("OS Version required for debugging")
        for t, f in args.debug:
            if t == "USB":
                DEBUG_TYPE[0] = True
                DEBUG_FILE[0] = f
            if t == "TB":
                DEBUG_TYPE[1] = True
                DEBUG_FILE[1] = f
        
        VERSION, macos_version = clean_macos_version(args.osver)

    if args.d:
        filt_vid, filt_pid = args.d[0].split(":")
    
    VERBOSE = args.verbose
    EXTRA_INFO = args.extra

def clean_hex(h):
    if h in (None, "-"):
        return "-"
    s = str(h).lower().strip()
    if s.startswith("0x"):
        s = s[2:]
    return s.zfill(4)

def plist_to_json(path):
    plist_file = Path(path)
    with plist_file.open("rb") as f:
        data = plistlib.load(f)  # handles XML and binary plists

    # plistlib returns Python types; convert to JSON
    # Default encoder can’t handle datetime/bytes—handle them below.
    def default(o):
        if isinstance(o, bytes):
            # represent bytes as base64 to preserve data
            import base64
            return {"__type__": "bytes", "base64": base64.b64encode(o).decode("ascii")}
        if hasattr(o, "isoformat"):
            return o.isoformat()
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    with open("/tmp/lsusb.json", "w", encoding="utf-8") as out:
        json.dump(data, out, ensure_ascii=False, indent=2, sort_keys=True, default=default)

def extract_features(dev, DATA_PROPERTIES, VERSION, RH):
    # The only parts that are 100% consistent among versions
    name = dev.get(DATA_PROPERTIES["NAME"][VERSION - 1]) or "-"

    if RH == False:
        LID_TYPE = "LID"
    else:
        LID_TYPE = "RLID"
    
    if DATA_PROPERTIES[LID_TYPE][VERSION - 1] != None:
        if RH == True and (VERSION == 2 or VERSION == 3):
            rh_bus = dev.get("_items", [])
            if len(rh_bus) > 0:
                for rh_dev in rh_bus or []:
                    l_id = clean_hex(rh_dev.get(DATA_PROPERTIES["LID"][VERSION - 1])) or "-"
                    if l_id != "-":
                        l_id = l_id.split(" / ")[0]
                        l_id = l_id[:-6] + "000000"
                        break
            else:
                l_id = "00000000"
        else:
            l_id = clean_hex(dev.get(DATA_PROPERTIES[LID_TYPE][VERSION - 1])) or "-"
            if VERSION != 4:
                if VERSION == 1 and RH == True:
                    l_id = l_id + "0000"
                l_id = l_id.split(" / ")[0]
    else:
        l_id = None
    
    if RH == False:
        raw_speed = dev.get(DATA_PROPERTIES["SPEED"][VERSION - 1]) or "-"
        pid = clean_hex(dev.get(DATA_PROPERTIES["PID"][VERSION - 1])) or "-"
        # it seems like in V2 apple sometimes includes the manufacturer in the VID but not always so the previous patch for V3 wont work
        # V2 and V3 are so messy compared to V1 and V4, it is actually insane how many patches i have to make for each of them
        if len(dev.get(DATA_PROPERTIES["VID"][VERSION - 1])) > 6 or (VERSION == 3 and l_id != None):
            # VID includes both the manufacturer and the VID for some reason
            vid = dev.get(DATA_PROPERTIES["VID"][VERSION - 1]) or "-"

            # V3: Apple is actually fucking insane, instead of you know, putting down their actual USB VID they just supply "apple_vendor_id"
            if vid != "apple_vendor_id":
                vid, mfr = vid.split("  ") # "vendor_id" : "0x154b  (PNY Technologies Inc.)"
                vid = clean_hex(vid)
                mfr = mfr.strip("()")
            else:
                vid = "05ac" # Pretty sure this is apple's VID
                # Apple doesnt add on the company name to the VID so we get it from the feild thats usally less detailed, execpt for themselves
                mfr = dev.get(DATA_PROPERTIES["MFR"][VERSION - 1]) or "-"
        elif VERSION != 3 or (VERSION == 3 and l_id == None):
            mfr = dev.get(DATA_PROPERTIES["MFR"][VERSION - 1]) or "-"
            vid = clean_hex(dev.get(DATA_PROPERTIES["VID"][VERSION - 1]) or "-")
        
        try:
            speed = SPEED_INDEX[raw_speed]
        except:
            speed = None
            pass
        
    # Root hubs and certain devices need to get their data manually 
    try:
        if "thunderboltusb4_bus_" in name:
            mfr, speed, name, vid, pid = DEVICE_OVERRIDE["thunderboltusb4_bus_"]
        else:
            mfr, speed, name, vid, pid = DEVICE_OVERRIDE[name]
    except:
        pass

    if DATA_PROPERTIES["SERIAL"][VERSION - 1] != None:
        serial = dev.get(DATA_PROPERTIES["SERIAL"][VERSION - 1])
        if serial == "Not Provided":
            serial = None
    # Apple seems to be the only one that can do serial numbers with Thunderbolt
    elif DATA_PROPERTIES["APPL_SERIAL"][VERSION - 1] != None:
        serial = dev.get(DATA_PROPERTIES["APPL_SERIAL"][VERSION - 1])
    else:
        serial = None

    # Collapse whitespace in name/manufacturer so it's clean on one line
    mfr = " ".join(str(mfr).split())
    name = " ".join(str(name).split())

    # Name, LID, VID, PID, MFR, 
    info = [name, l_id, vid, pid, mfr]
    # Speed, Serial
    ext_info = [speed, serial]
    
    return info, ext_info

def get_json(VERSION, TYPE):
    if TYPE == "USB":
        command = USB_DATA_PROPERTIES
        DEBUG_INDEX = 0
    else:
        command = TB_DATA_PROPERTIES
        DEBUG_INDEX = 1

    if DEBUG_TYPE[DEBUG_INDEX] == True:
        if VERSION >= 3:
            f = open(DEBUG_FILE[DEBUG_INDEX])
        elif VERSION <= 2:
            plist_to_json(DEBUG_FILE[DEBUG_INDEX])
            f = open("/tmp/lsusb.json")
        data = json.load(f)
    else:
        result = subprocess.run(
            ["system_profiler", command["ARG1"][VERSION - 1], command["ARG2"][VERSION - 1]],
            capture_output=True,
            text=True,
            check=True,
        )
        if VERSION >= 3:
            data = json.loads(result.stdout)
        elif VERSION <= 2:
            with open("/tmp/lsusb.plist", "w", encoding="utf-8") as f:
                f.write(result.stdout)

            plist_to_json("/tmp/lsusb.plist")

            f = open("/tmp/lsusb.json")
            data = json.load(f)
    
    return data

def SPDataType(VERSION, TYPE):
    data = get_json(VERSION, TYPE)
    if TYPE == "USB":
        DATA_PROPERTIES = USB_DATA_PROPERTIES
    else:
        DATA_PROPERTIES = TB_DATA_PROPERTIES
    lines = []

    def filter_vid_pid(filt_vid, vid, filt_pid, pid):
        if filt_vid == None and filt_pid == None:
            return True
        else:
            if vid == filt_vid and pid == filt_pid:
                return True
            else:
                return False

    def output(device, ext):
        lines = []
        if filter_vid_pid(filt_vid, device[2], filt_pid, device[3]) == True:
            if device[1] != None:
                lines.append(f"Location: {device[1]}: ID {device[2]}:{device[3]} {device[4]} {device[0]}")
            else:
                lines.append(f"ID {device[2]}:{device[3]} {device[4]} {device[0]}")
            
            if EXTRA_INFO == True:
                if ext[0] != None:
                    lines.append(f"{INDENT}Speed: {ext[0]}")
                if ext[1] != None:
                    lines.append(f"{INDENT}Serial: {ext[1]}")
        return lines
        
    def process_devices(items, depth=0):
        for dev in items or []:
            device, ext = extract_features(dev, DATA_PROPERTIES, VERSION, False)
            for line in output(device, ext):
                lines.append(line)
            
            child_items = dev.get("_items")
            if isinstance(child_items, list) and child_items:
                process_devices(child_items, depth + 1)
    
    if VERSION > 2:
        dev = data
    else:
        dev = data[0]
    
    for top in dev.get(DATA_PROPERTIES["HEAD"][VERSION - 1], []):
        device, ext = extract_features(top, DATA_PROPERTIES, VERSION, True)
        for line in output(device, ext):
            lines.append(line)
        
        process_devices(top.get("_items", []), depth=0)
    
    return lines

if sys.version_info[0] < 3:
    sys.exit('This script requires Python 3')

if platform.system() == "Darwin":
    VERSION, macos_version = clean_macos_version(platform.mac_ver()[0])
    arguments()
else:
    sys.exit("This script is only supported on macOS") 

if VERBOSE == False:
    usb = SPDataType(VERSION, "USB")
    # Temporary fix because i dont have any testing for TB on VERSION 1 or 2
    if VERSION > 2:
        tb = SPDataType(VERSION, "TB")
    else:
        tb = []
    
    # 10.6.5 is the first version with Thunderbolt support
    # if macos_version > 100604:
    #     tb = SPDataType(VERSION, "TB")

    if usb != []:
        print("USB Devies:")
        for line in usb:
            print(line)
    if tb != []:
        print("\nThunderbolt / USB 4 Devices:")
        for line in tb:
            print(line)

    if usb == [] and tb == []:
        print("No Devices Connected / Detected!")
    
    # Cleanup temp files
    if os.path.exists("/tmp/lsusb.plist"):
       os.remove("/tmp/lsusb.plist")
    if os.path.exists("/tmp/lsusb.json"):
       os.remove("/tmp/lsusb.json")
else:
    result = subprocess.run(
            ["system_profiler", USB_DATA_PROPERTIES["ARG1"][VERSION - 1]],
            capture_output=True,
            text=True,
            check=True,
        )
    print(result.stdout)

    # Thunderbolt
    if VERSION > 2:
        result = subprocess.run(
            ["system_profiler", TB_DATA_PROPERTIES["ARG1"][VERSION - 1]],
            capture_output=True,
            text=True,
            check=True,
        )
        print(result.stdout)