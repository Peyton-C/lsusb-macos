import json
import subprocess
import platform
import sys

VERBOSE = False

if platform.system() == "Darwin":
    macos_version = float(platform.mac_ver()[0])
else:
    sys.exit("This script is only supported on macOS") 

filt_vid = None
filt_pid = None

def clean_hex(h):
    if h in (None, "-"):
        return "-"
    s = str(h).lower().strip()
    if s.startswith("0x"):
        s = s[2:]
    return s.zfill(4)

def SPUSBHostDataType(): # Tahoe and Newer USB
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
    result = subprocess.run(
        ["system_profiler", "SPUSBDataType", "-json"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)

    lines = []
    # def process_devices(items, depth=0):
    #     for dev in items or []:
    #         l_id = clean_hex(dev.get("USBKeyLocationID")) or "-"
    #         vid = clean_hex(dev.get("USBDeviceKeyVendorID")) or "-"
    #         pid = clean_hex(dev.get("USBDeviceKeyProductID")) or "-"
    #         mfr = dev.get("USBDeviceKeyVendorName") or "-"
    #         name = dev.get("_name") or "-"    

    #         # Collapse whitespace in name/manufacturer so it's clean on one line
    #         mfr = " ".join(str(mfr).split())
    #         name = " ".join(str(name).split())

    #         lines.append(f"Location: {l_id}: ID {vid}:{pid} {mfr} {name}")

    #         child_items = dev.get("_items")
    #         if isinstance(child_items, list) and child_items:
    #             process_devices(child_items, depth + 1)
    
    # for top in data.get("SPUSBHostDataType", []):
    #     process_devices(top.get("_items", []), depth=0)

    return lines

def SPThunderboltDataType(): # Shared with both Tahoe and Pre-Tahoe
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

if VERBOSE == False:
    if float(platform.mac_ver()[0]) >= 26.0:
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