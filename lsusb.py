import json
import subprocess
import platform
import sys
import plistlib
from pathlib import Path
import os
import argparse

VERBOSE = False
DEBUG_TYPE = [False, False]
DEBUG_FILE = ["", ""]
filt_vid = None
filt_pid = None

def clean_macos_version(raw):
    raw = raw.split(".")
    if raw[0] == "10" and int(raw[1]) < 10:
        macos_version = float((f"{raw[0]}.0{raw[1]}"))
    else:
        macos_version = float((f"{raw[0]}.{raw[1]}"))
    
    return macos_version

def arguments():
    global DEBUG_FILE, DEBUG_TYPE, macos_version, filt_pid, filt_vid, VERBOSE
    parser = argparse.ArgumentParser(
        prog="lsusb-macos",
        description="Display connected USB and Thunderbolt Devices on macOS / Mac OS X"
    )

    parser.add_argument("-v", "--verbose", help="Output the raw information from system_profiler")
    parser.add_argument("-d", nargs=1, metavar=("Vendor:Product"), help="Show only devices with the specified vendor and product ID numbers (in Hexadecimal) ")
    parser.add_argument("-D", "--debug", nargs=2, metavar=("Type", "File"), action="append", help="Simulate Connected Devices, Type (USB|TB) and File (JSON or XML)")
    parser.add_argument("-os", "--osver", help="Debug OS Version (ie 10.7, 10.13, 15.5, 26.1, etc)")

    args = parser.parse_args()

    if args.verbose:
        VERBOSE == True
    if args.debug:
        if not args.osver:
            sys.exit("OS Version required for debugging")
        for t, f in args.debug:
            if t == "USB":
                DEBUG_TYPE[0] = True
                DEBUG_FILE[0] = f
            elif t == "TB":
                DEBUG_TYPE[1] = True
                DEBUG_FILE[1] = f
        
        macos_version = clean_macos_version(args.osver)

    if args.d:
        filt_vid, filt_pid = args.d.split(":")

def clean_hex(h):
    if h in (None, "-"):
        return "-"
    s = str(h).lower().strip()
    if s.startswith("0x"):
        s = s[2:]
    return s.zfill(4)

def plist_to_json(path) -> None:
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
            # e.g., datetime.datetime from plist "Date" type
            return o.isoformat()
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    with open("/tmp/lsusb.json", "w", encoding="utf-8") as out:
        json.dump(data, out, ensure_ascii=False, indent=2, sort_keys=True, default=default)

def extract_features(dev, location_id, VID, PID, MFR, NAME, VERSION):
    # The only parts that are 100% consistent among versions
    l_id = clean_hex(dev.get(location_id)) or "-"
    name = dev.get(NAME) or "-"
    pid = clean_hex(dev.get(PID)) or "-"

    # 4 - Tahoe and Newer
    # 3 - Catalina - Sequoia
    # 2 - Yosmite - Mojave
    # 1 - Mavricks and Older
    if VERSION != 3:
        mfr = dev.get(MFR) or "-"
        vid = clean_hex(dev.get(VID) or "-")
    elif VERSION == 3:
        # VID includes both the manufacturer and the VID for some reason
        vid = dev.get("vendor_id") or "-"

        # Apple is actually fucking insane, instead of you know, putting down their actual USB VID they just supply "apple_vendor_id"
        if vid != "apple_vendor_id":
            vid, mfr = vid.split("  ") # "vendor_id" : "0x154b  (PNY Technologies Inc.)"
            vid = clean_hex(vid)
            mfr = mfr.strip("()")
        else:
            vid = "05ac" # Pretty sure this is apple's VID
            # Apple doesnt add on the company name to the VID so we get it from the feild thats usally less detailed, execpt for themselves
            mfr = dev.get("manufacturer") or "-"
    
    if VERSION != 4:
        l_id = l_id.split(" / ")[0]

    # Collapse whitespace in name/manufacturer so it's clean on one line
    mfr = " ".join(str(mfr).split())
    name = " ".join(str(name).split())
    
    return l_id, vid, pid, mfr, name

def filter_vid_pid(filt_vid, vid, filt_pid, pid):
    if filt_vid == None and filt_pid == None:
        return True
    else:
        if vid == filt_vid and pid == filt_pid:
            return True
        else:
            return False

def get_json(VERSION):
    command = {
        1: ["SPUSBDataType", "-xml"],
        2: ["SPUSBDataType", "-xml"],
        3: ["SPUSBDataType", "-json"],
        4: ["SPUSBHostDataType", "-json"]
    }
    
    if DEBUG_TYPE[0] == True:
        if VERSION >= 3:
            f = open(DEBUG_FILE[0])
        elif VERSION <= 2:
            plist_to_json(DEBUG_FILE[0])
            f = open("/tmp/lsusb.json")
        data = json.load(f)
    else:
        result = subprocess.run(
            ["system_profiler", command[VERSION][0], command[VERSION][1]],
            capture_output=True,
            text=True,
            check=True,
        )
        if VERSION >= 3:
            data = json.loads(result.stdout)
        elif VERSION <= 2:
            if os.path.exists("/tmp/lsusb.plist"):
                os.remove("/tmp/lsusb.plist")
            if os.path.exists("/tmp/lsusb.json"):
                os.remove("/tmp/lsusb.json")

            with open("/tmp/lsusb.plist", "w", encoding="utf-8") as f:
                f.write(result.stdout)

            plist_to_json("/tmp/lsusb.plist")

            f = open("/tmp/lsusb.json")
            data = json.load(f)
    
    return data

def SPUSBHostDataType(): # Tahoe and Newer USB
    data = get_json(4)
    lines = []
    def process_devices(items, depth=0):
        for dev in items or []:
            l_id, vid, pid, mfr, name = extract_features(dev, "USBKeyLocationID", "USBDeviceKeyVendorID", "USBDeviceKeyProductID", "USBDeviceKeyVendorName", "_name", 4)
            if filter_vid_pid(filt_vid, vid, filt_pid, pid) == True:
                lines.append(f"Location: {l_id}: ID {vid}:{pid} {mfr} {name}")
            
            child_items = dev.get("_items")
            if isinstance(child_items, list) and child_items:
                process_devices(child_items, depth + 1)

    for top in data.get("SPUSBHostDataType", []):
        process_devices(top.get("_items", []), depth=0)

    return lines

def SPUSBDataType(VERSION): # Yosemite - Sequoia USB
    data = get_json(VERSION)
    lines = []

    def process_devices(items, depth=0):
        for dev in items or []:
            l_id, vid, pid, mfr, name = extract_features(dev, "location_id", "vendor_id", "product_id", "manufacturer", "_name", VERSION)

            if filter_vid_pid(filt_vid, vid, filt_pid, pid) == True:
                lines.append(f"Location: {l_id}: ID {vid}:{pid} {mfr} {name}")

            child_items = dev.get("_items")
            if isinstance(child_items, list) and child_items:
                process_devices(child_items, depth + 1)

    if VERSION == 3:
        hubs = data.get("SPUSBDataType", [])
    else:
        hubs = data[0].get("_items", []) or []

    for top in hubs:
        process_devices(top.get("_items", []), depth=0)

    return lines

def SPUSBDataType_legacy(): # Snow Leopard - Mavericks
    data = get_json(1)
    lines = []

    def process_devices(items, depth=0):
        for dev in items or []:
            l_id, vid, pid, mfr, name = extract_features(dev, "g_location_id", "b_vendor_id", "a_product_id", "f_manufacturer", "_name", 1)

            if filter_vid_pid(filt_vid, vid, filt_pid, pid) == True:
                lines.append(f"Location: {l_id}: ID {vid}:{pid} {mfr} {name}")

            child_items = dev.get("_items")
            if isinstance(child_items, list) and child_items:
                process_devices(child_items, depth + 1)

    hubs = data[0].get("_items", []) or []
    for top in hubs:
        process_devices(top.get("_items", []), depth=0)

    return lines

def SPThunderboltDataType(FORMAT): # Yosemite and newer
    if FORMAT == "JSON":
        if DEBUG_TYPE[1] == True:
            f = open(DEBUG_FILE[1])
            data = json.load(f)
        else:
            result = subprocess.run(
                ["system_profiler", "SPThunderboltDataType", "-json"],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout)
    else:
        if DEBUG_TYPE[1] == True:
            plist_to_json(DEBUG_FILE[1])
        else:
            if os.path.exists("/tmp/lsusb.plist"):
                os.remove("/tmp/lsusb.plist")
            if os.path.exists("/tmp/lsusb.json"):
                os.remove("/tmp/lsusb.json")

            result = subprocess.run(
                ["system_profiler", "SPThunderboltDataType", "-xml"],
                capture_output=True,
                text=True,
                check=True,
            )

            with open("/tmp/lsusb.plist", "w", encoding="utf-8") as f:
                f.write(result.stdout)

            plist_to_json("/tmp/lsusb.plist")

        f = open("/tmp/lsusb.json")
        data = json.load(f)
        
    lines = []

    def process_devices(items, depth=0):
        for dev in items or []:
            # Note: These arent a direct eqivilant to normal USB VID and PIDs
            vid = clean_hex(dev.get("vendor_id_key") or "-")
            pid = clean_hex(dev.get("device_id_key") or "-")
            mfr = dev.get("vendor_name_key") or "-"
            name = dev.get("_name") or "-"

            # Collapse whitespace in name/manufacturer so it's clean on one line
            mfr = " ".join(str(mfr).split())
            name = " ".join(str(name).split())

            if filter_vid_pid(filt_vid, vid, filt_pid, pid) == True:
                lines.append(f"ID {vid}:{pid} {mfr} {name}")

            # I dont have another TB / USB 4 device to test with but this should work? 
            child_items = dev.get("_items")
            if isinstance(child_items, list) and child_items:
                process_devices(child_items, depth + 1)
    
    if FORMAT == "JSON":
        hubs = data.get("SPThunderboltDataType", [])
    else:
        hubs = data[0].get("_items", []) or []
    for top in hubs:
        process_devices(top.get("_items", []), depth=0)

    return lines

if platform.system() == "Darwin":
    macos_version = clean_macos_version(platform.mac_ver()[0])
    arguments()
else:
    sys.exit("This script is only supported on macOS") 

if VERBOSE == False:
    if macos_version >= 26.0:
        usb = SPUSBHostDataType() # Tahoe and Newer
        tb = SPThunderboltDataType("JSON")
    elif macos_version >= 10.15 and macos_version < 26.0:
        usb = SPUSBDataType(3) # Catalina - Sequoia
        tb = SPThunderboltDataType("JSON")
    elif macos_version >= 10.10 and macos_version < 10.15:
        usb = SPUSBDataType(2) # Yosemite - Mojave
        tb = []
        #tb = SPThunderboltDataType("XML")
    else:
        usb = SPUSBDataType_legacy()
        tb = []

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
else:
    if macos_version >= 26.0:
        # Tahoe and Newer
        result = subprocess.run(
            ["system_profiler", "SPUSBHostDataType"],
            capture_output=True,
            text=True,
            check=True,
        )
        print(result.stdout)
    else:
        # Pre Tahoe
        result = subprocess.run(
            ["system_profiler", "SPUSBDataType"],
            capture_output=True,
            text=True,
            check=True,
        )
        print(result.stdout)
    
    # Thunderbolt
    result = subprocess.run(
        ["system_profiler", "SPThunderboltDataType"],
        capture_output=True,
        text=True,
        check=True,
    )
    print(result.stdout)