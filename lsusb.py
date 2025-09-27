import json
import subprocess
import platform

def clean_hex(h):
    if h in (None, "-"):
        return "-"
    s = str(h).lower().strip()
    if s.startswith("0x"):
        s = s[2:]
    return s.zfill(4)

def tahoe_usb_fmt():
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

            lines.append(f"Location: {l_id}: ID {vid}:{pid} {mfr} {name}")

            child_items = dev.get("_items")
            if isinstance(child_items, list) and child_items:
                process_devices(child_items, depth + 1)
    
    for top in data.get("SPUSBHostDataType", []):
        process_devices(top.get("_items", []), depth=0)

    return lines

def tbolt_usb4_fmt():
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

            lines.append(f"ID: {vid}:{pid} {mfr} {name}")

            # I dont have another TB / USB 4 device to test with but this should work? 
            child_items = dev.get("_items")
            if isinstance(child_items, list) and child_items:
                process_devices(child_items, depth + 1)
    
    for top in data.get("SPThunderboltDataType", []):
        process_devices(top.get("_items", []), depth=0)

    return lines


if platform.system() == "Darwin":
    if float(platform.mac_ver()[0]) >= 26.0:
        usb = tahoe_usb_fmt()
        tb = tbolt_usb4_fmt()
        
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
        print("Unsupported Version")        
else:
    print("This script is only meant for use on macOS")