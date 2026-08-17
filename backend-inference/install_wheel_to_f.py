import urllib.request
import json
import zipfile
import io
import os
import sys

TARGET_DIR = r"F:\FoodSense\python_packages"
os.makedirs(TARGET_DIR, exist_ok=True)

def install_pkg(pkg_name):
    print(f"Fetching PyPI metadata for '{pkg_name}'...")
    url = f"https://pypi.org/pypi/{pkg_name}/json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        data = json.load(resp)
        
    urls = data["urls"]
    wheel_url = None
    # Find matching wheel for win_amd64 specifically
    for u in urls:
        fn = u["filename"]
        if fn.endswith(".whl") and "win_amd64" in fn and ("cp3" in fn or "abi3" in fn or "py3" in fn):
            wheel_url = u["url"]
            wheel_name = fn
            break
            
    if not wheel_url:
        for u in urls:
            if u["filename"].endswith(".whl") and "win_amd64" in u["filename"]:
                wheel_url = u["url"]
                wheel_name = u["filename"]
                break
                
    if not wheel_url:
        print(f"No suitable wheel found for {pkg_name}")
        return False
        
    print(f"Downloading {wheel_name} from {wheel_url}...")
    req = urllib.request.Request(wheel_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        wheel_bytes = resp.read()
        
    print(f"Extracting {len(wheel_bytes)/(1024*1024):.1f} MB into {TARGET_DIR}...")
    with zipfile.ZipFile(io.BytesIO(wheel_bytes)) as z:
        z.extractall(TARGET_DIR)
        
    print(f"Successfully installed {pkg_name} to {TARGET_DIR}!")
    return True

if __name__ == "__main__":
    for pkg in sys.argv[1:]:
        install_pkg(pkg)
