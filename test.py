def clean_macos_version(raw):
    parts = raw.split(".")
    major = int(parts[0])
    minor = int(parts[1])
    
    if len(parts) > 2:
        fix = (int(parts[2]))
    else:
        fix = 0

    ver = (major * 10000) + (minor * 100) + (fix)
    
    if ver >= 260000:
        VERSION = 4
    elif 101500 <= ver <= 260000:
        VERSION = 3
    elif 101000 <= ver <= 101400:
        VERSION = 2
    else:
        VERSION = 1
    
    return VERSION

print(clean_macos_version("10.16.4"))