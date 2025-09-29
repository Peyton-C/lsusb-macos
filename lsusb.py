import json
import subprocess
import platform
import sys
import plistlib
from pathlib import Path
import os

VERBOSE = False
DEBUG = False
DEBUG_TYPE = None
filt_vid = None
filt_pid = None

if platform.system() == "Darwin":
    mv_unclean = platform.mac_ver()[0]
    mv_unclean = mv_unclean.split(".")
    if mv_unclean[0] == "10" and int(mv_unclean[1]) < 10:
        macos_version = float((f"{mv_unclean[0]}.0{mv_unclean[1]}"))
    else:
        macos_version = float((f"{mv_unclean[0]}.{mv_unclean[1]}"))
    
else:
    sys.exit("This script is only supported on macOS") 

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

def filter_vid_pid(lines, type, filt_vid, filt_pid, l_id, vid, pid, mfr, name):
    # VID / PID Filter
    if type == "USB":
        if filt_vid == None and filt_pid == None:
            lines.append(f"Location: {l_id}: ID {vid}:{pid} {mfr} {name}")
        else:
            if vid == filt_vid and pid == filt_pid:
                lines.append(f"Location: {l_id}: ID {vid}:{pid} {mfr} {name}")
    else:
        if filt_vid == None and filt_pid == None:
                lines.append(f"ID: {vid}:{pid} {mfr} {name}")
        else:
            if vid == filt_vid and pid == filt_pid:
                lines.append(f"ID: {vid}:{pid} {mfr} {name}")

def SPUSBHostDataType(): # Tahoe and Newer USB
    if DEBUG == True and DEBUG_TYPE == "USB":
        f = open(DEBUG_FILE)
        data = json.load(f)
    else:
        result = subprocess.run(
            ["system_profiler", "SPUSBHostDataType", "-json"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)

    lines = []
    def process_devices(items, depth=0):
        for dev in items or []:
            l_id, vid, pid, mfr, name = extract_features(dev, "USBKeyLocationID", "USBDeviceKeyVendorID", "USBDeviceKeyProductID", "USBDeviceKeyVendorName", "_name", 4)
            filter_vid_pid(lines, "USB", filt_vid, filt_pid, l_id, vid, pid, mfr, name)
            child_items = dev.get("_items")
            if isinstance(child_items, list) and child_items:
                process_devices(child_items, depth + 1)

    for top in data.get("SPUSBHostDataType", []):
        process_devices(top.get("_items", []), depth=0)

    return lines

def SPUSBDataType(VERSION): # Yosemite - Sequoia USB
    # Catalina - Sequoia
    if VERSION == 3:
        if DEBUG == True and DEBUG_TYPE == "USB":
            f = open(DEBUG_FILE)
            data = json.load(f)
        else:
            result = subprocess.run(
                ["system_profiler", "SPUSBDataType", "-json"],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout)
    # Yosemite - Mojave
    else:
        if os.path.exists("/tmp/lsusb.plist"):
            os.remove("/tmp/lsusb.plist")
        if os.path.exists("/tmp/lsusb.json"):
            os.remove("/tmp/lsusb.json")
            
        if DEBUG == True and DEBUG_TYPE == "USB":
            plist_to_json(DEBUG_FILE)
        else:
            result = subprocess.run(
                ["system_profiler", "SPUSBDataType", "-xml"],
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
            l_id, vid, pid, mfr, name = extract_features(dev, "location_id", "vendor_id", "product_id", "manufacturer", "_name", VERSION)

            filter_vid_pid(lines, "USB", filt_vid, filt_pid, l_id, vid, pid, mfr, name)

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
    if os.path.exists("/tmp/lsusb.plist"):
        os.remove("/tmp/lsusb.plist")
    if os.path.exists("/tmp/lsusb.json"):
        os.remove("/tmp/lsusb.json")

    if DEBUG == True and DEBUG_TYPE == "USB":
        plist_to_json(DEBUG_FILE)
    else:
        result = subprocess.run(
            ["system_profiler", "SPUSBDataType", "-xml"],
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
            l_id, vid, pid, mfr, name = extract_features(dev, "g_location_id", "b_vendor_id", "a_product_id", "f_manufacturer", "_name", 1)

            filter_vid_pid(lines, "USB", filt_vid, filt_pid, l_id, vid, pid, mfr, name)

            child_items = dev.get("_items")
            if isinstance(child_items, list) and child_items:
                process_devices(child_items, depth + 1)

    hubs = data[0].get("_items", []) or []
    for top in hubs:
        process_devices(top.get("_items", []), depth=0)

    return lines

def SPThunderboltDataType(FORMAT): # Yosemite and newer
    if FORMAT == "JSON":
        if DEBUG == True and DEBUG_TYPE == "TB":
            f = open(DEBUG_FILE)
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
        if DEBUG == True and DEBUG_TYPE == "TB":
            plist_to_json(DEBUG_FILE)
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

            filter_vid_pid(lines, "TB", filt_vid, filt_pid, None, vid, pid, mfr, name)

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

# Command Line Arguments
if len(sys.argv) > 1:
    if sys.argv[1] == "-v" or sys.argv[1] == "--verbose":
        VERBOSE = True
    elif sys.argv[1] == "-d":
        filt_vid, filt_pid = sys.argv[2].split(":")
    
    # -D USB /exaple/example.json 26.0
    # Lets you test with a pre-saved json file
    elif sys.argv[1] == "-D" or sys.argv[1] == "--debug":
        DEBUG = True

        # Allows for testing either USB or TB
        if len(sys.argv) > 2:
            if sys.argv[2] == "USB" or sys.argv[2] == "usb":
                DEBUG_TYPE = "USB"
            else:
                DEBUG_TYPE = "TB"
        
        # system_profiler json output
        if len(sys.argv) > 3:
            DEBUG_FILE = sys.argv[3]
        else:
            sys.exit("Missing JSON file!")
        
        # lets you test both USB handelers regardless of OS version
        if len(sys.argv) > 4:
            macos_version = float(sys.argv[4])

if VERBOSE == False:
    if macos_version >= 26.0:
        usb = SPUSBHostDataType() # Tahoe and Newer
        tb = SPThunderboltDataType("JSON")
    elif macos_version >= 10.15 and macos_version < 26.0:
        usb = SPUSBDataType("JSON") # Catalina - Sequoia
        tb = SPThunderboltDataType(3)
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