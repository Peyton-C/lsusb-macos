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
    for hub in data.get("SPUSBHostDataType", []):
        for dev in hub.get("_items", []) or []:
            l_id = clean_hex(dev.get("USBKeyLocationID")) or "-"
            vid = clean_hex(dev.get("USBDeviceKeyVendorID")) or "-"
            pid = clean_hex(dev.get("USBDeviceKeyProductID")) or "-"
            mfr = dev.get("USBDeviceKeyVendorName") or "-"
            name = dev.get("_name") or "-"

            # Collapse whitespace in name/manufacturer so it's clean on one line
            mfr = " ".join(str(mfr).split())
            name = " ".join(str(name).split())

            lines.append(f"Location: {l_id}: ID {vid}:{pid} {mfr} {name}")

    return lines

if platform.system() == "Darwin":
    if float(platform.mac_ver()[0]) >= 26.0:
        for line in tahoe_usb_fmt():
            print(line)
    else:
        print("Unsupported Version")        
else:
    print("This script is only meant for use on macOS")