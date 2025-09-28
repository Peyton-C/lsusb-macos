import json
import subprocess
import platform
import sys

VERBOSE = False
DEBUG = False
DEBUG_TYPE = None
filt_vid = None
filt_pid = None

if platform.system() == "Darwin":
    mv_unclean = platform.mac_ver()[0]
    mv_unclean = mv_unclean.split(".")
    macos_version = float((f"{mv_unclean[0]}.{mv_unclean[1]}"))
    if macos_version < 10.15:
        sys.exit("This script cannot be ran on your version of Mac OS X")
else:
    sys.exit("This script is only supported on macOS") 

def clean_hex(h):
    if h in (None, "-"):
        return "-"
    s = str(h).lower().strip()
    if s.startswith("0x"):
        s = s[2:]
    return s.zfill(4)

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
            l_id = clean_hex(dev.get("USBKeyLocationID")) or "-"
            vid = clean_hex(dev.get("USBDeviceKeyVendorID")) or "-"
            pid = clean_hex(dev.get("USBDeviceKeyProductID")) or "-"
            mfr = dev.get("USBDeviceKeyVendorName") or "-"
            name = dev.get("_name") or "-"    

            # Collapse whitespace in name/manufacturer so it's clean on one line
            mfr = " ".join(str(mfr).split())
            name = " ".join(str(name).split())

            # VID / PID Filter
            if filt_vid == None and filt_pid == None:
                lines.append(f"Location: {l_id}: ID {vid}:{pid} {mfr} {name}")
            else:
                if vid == filt_vid and pid == filt_pid:
                    lines.append(f"Location: {l_id}: ID {vid}:{pid} {mfr} {name}")

            child_items = dev.get("_items")
            if isinstance(child_items, list) and child_items:
                process_devices(child_items, depth + 1)
    
    for top in data.get("SPUSBHostDataType", []):
        process_devices(top.get("_items", []), depth=0)

    return lines

def SPUSBDataType(): # Pre Tahoe USB
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

    lines = []
    def process_devices(items, depth=0):
        for dev in items or []:
            l_id = clean_hex(dev.get("location_id")) or "-"
            pid = clean_hex(dev.get("product_id")) or "-"
            name = dev.get("_name") or "-"    

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

            # The / # at the end of location IDs looks kinda ugly and is only sometimes there so im removing it
            l_id = l_id.split(" / ")[0]

            # Collapse whitespace in name/manufacturer so it's clean on one line
            mfr = " ".join(str(mfr).split())
            name = " ".join(str(name).split())

            lines.append(f"Location: {l_id}: ID {vid}:{pid} {mfr} {name}")

            child_items = dev.get("_items")
            if isinstance(child_items, list) and child_items:
                process_devices(child_items, depth + 1)
    
    for top in data.get("SPUSBDataType", []):
        process_devices(top.get("_items", []), depth=0)

    return lines

def SPThunderboltDataType(): # Shared with both Tahoe and Pre-Tahoe
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

            # VID / PID Filter
            if filt_vid == None and filt_pid == None:
                lines.append(f"ID: {vid}:{pid} {mfr} {name}")
            else:
                if vid == filt_vid and pid == filt_pid:
                    lines.append(f"ID: {vid}:{pid} {mfr} {name}")

            # I dont have another TB / USB 4 device to test with but this should work? 
            child_items = dev.get("_items")
            if isinstance(child_items, list) and child_items:
                process_devices(child_items, depth + 1)
    
    for top in data.get("SPThunderboltDataType", []):
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
        usb = SPUSBHostDataType()
    else:
        usb = SPUSBDataType()

    tb = SPThunderboltDataType()

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
        # Tahoe+
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